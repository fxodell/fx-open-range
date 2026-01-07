"""
Trading Engine - Main logic for automated trading.
"""

import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Tuple
import pandas as pd

from app.config.settings import Settings
from app.utils.oanda_client import OandaTradingClient
from app.utils.metrics import get_metrics
from app.strategies.sma20_strategy import get_current_signal, prepare_data_for_strategy
from app.strategies.dual_market_open_strategy import (
    get_dual_market_signals,
    check_eur_market_open,
    check_us_market_open,
    get_market_open_signal,
)


class TradingEngine:
    """Main trading engine that executes the strategy."""
    
    def __init__(self, client: OandaTradingClient):
        """
        Initialize trading engine.
        
        Parameters:
        -----------
        client : OandaTradingClient
            OANDA API client
        """
        self.client = client
        self.instrument = Settings.INSTRUMENT
        self.logger = self._setup_logger()
        self.trades_today = 0
        self.last_trade_date = None
        self.eur_trade_today = False
        self.us_trade_today = False
        self.metrics = get_metrics()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger."""
        logger = logging.getLogger("TradingEngine")
        logger.setLevel(getattr(logging, Settings.LOG_LEVEL))
        
        # Create logs directory
        Settings.LOG_DIR.mkdir(exist_ok=True)
        
        # File handler
        log_file = Settings.LOG_DIR / f"trading_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def check_trading_hours(self) -> bool:
        """Check if current time is within trading hours."""
        now = datetime.now(timezone.utc)
        current_hour = now.hour
        
        if Settings.TRADING_START_HOUR <= Settings.TRADING_END_HOUR:
            return Settings.TRADING_START_HOUR <= current_hour <= Settings.TRADING_END_HOUR
        else:
            # Handles case where trading hours cross midnight
            return current_hour >= Settings.TRADING_START_HOUR or current_hour <= Settings.TRADING_END_HOUR
    
    def has_traded_today(self) -> bool:
        """Check if we've already traded today."""
        today = datetime.now(timezone.utc).date()
        
        # Reset counter if new day
        if self.last_trade_date != today:
            self.trades_today = 0
            self.last_trade_date = today
            self.eur_trade_today = False
            self.us_trade_today = False
            return False
        
        # For dual market open, check if we've hit the max trades
        if Settings.DUAL_MARKET_OPEN_ENABLED:
            return self.trades_today >= Settings.MAX_DAILY_TRADES
        else:
            return self.trades_today >= Settings.MAX_DAILY_TRADES
    
    def check_eur_market_open(self) -> bool:
        """Check if current time is within EUR market open window."""
        return check_eur_market_open()
    
    def check_us_market_open(self) -> bool:
        """Check if current time is within US market open window."""
        return check_us_market_open()
    
    def get_market_data(self, days: int = 30) -> pd.DataFrame:
        """
        Fetch market data for strategy analysis.
        
        Uses count-based fetching (more reliable than date-based) with a buffer
        to ensure we get enough complete candles for indicator calculations.
        
        Parameters:
        -----------
        days : int
            Number of days to request (deprecated - kept for compatibility).
            Actual count is calculated based on SMA_PERIOD with buffer.
            
        Returns:
        --------
        pd.DataFrame with Date, Open, High, Low, Close columns
        """
        # Use count-based fetching with buffer: request 50% more candles than needed
        # This ensures we have enough complete candles even after filtering incomplete ones
        # For SMA20, request 30 candles to ensure we get at least 20 complete ones
        requested_count = int(Settings.SMA_PERIOD * 1.5)  # 50% buffer
        
        import time
        start_time_api = time.time()
        try:
            df = self.client.fetch_candles(
                instrument=self.instrument,
                granularity="D",
                count=requested_count  # Use count instead of date range for reliability
            )
            duration = time.time() - start_time_api
            self.metrics.record_api_call(duration_seconds=duration, error=False)
            return df
        except Exception as e:
            duration = time.time() - start_time_api
            self.metrics.record_api_call(duration_seconds=duration, error=True)
            raise
    
    def get_signal(self) -> Tuple[str, Optional[float], Optional[float], Optional[Dict]]:
        """
        Get current trading signal.
        
        Returns:
        --------
        tuple (signal, price, sma, price_info)
            signal: 'long', 'short', or 'flat'
            price: Current close price
            sma: Current SMA value
            price_info: Current market pricing
        """
        try:
            # Get historical data
            df = self.get_market_data()
            
            if len(df) < Settings.SMA_PERIOD:
                self.logger.warning(f"Insufficient data: {len(df)} candles (need {Settings.SMA_PERIOD})")
                return 'flat', None, None, None
            
            # Prepare data
            df = prepare_data_for_strategy(df, Settings.SMA_PERIOD)
            
            # Get signal
            signal, price, sma = get_current_signal(df, Settings.SMA_PERIOD)
            
            # Get current market pricing
            import time
            start_time_api = time.time()
            try:
                price_info = self.client.get_current_price(self.instrument)
                duration = time.time() - start_time_api
                self.metrics.record_api_call(duration_seconds=duration, error=False)
            except Exception as e:
                duration = time.time() - start_time_api
                self.metrics.record_api_call(duration_seconds=duration, error=True)
                self.logger.warning(f"Could not get current pricing: {e}")
                price_info = None
            
            return signal, price, sma, price_info
            
        except Exception as e:
            self.logger.error(f"Error getting signal: {e}", exc_info=True)
            return 'flat', None, None, None
    
    def check_open_positions(self) -> List[Dict]:
        """
        Check for open positions in our instrument.
        
        Uses both open_trades (individual trades) and open_positions (aggregated)
        to ensure we catch all open positions even if OANDA aggregates them.
        """
        try:
            # Check individual trades
            open_trades = self.client.get_open_trades()
            our_trades = [t for t in open_trades if t['instrument'] == self.instrument]
            
            # Also check aggregated positions (defensive check)
            try:
                open_positions = self.client.get_open_positions()
                our_positions = [p for p in open_positions if p['instrument'] == self.instrument]
                
                # If positions exist but trades don't (shouldn't happen, but defensive)
                if our_positions and not our_trades:
                    self.logger.warning(
                        f"Position detected via aggregated positions but not trades: {our_positions}"
                    )
                
                # Log total position units if we have positions
                for pos in our_positions:
                    long_units = int(pos.get('long', {}).get('units', 0))
                    short_units = abs(int(pos.get('short', {}).get('units', 0)))
                    net_units = long_units - short_units
                    if net_units != 0:
                        self.logger.debug(
                            f"Aggregated position: {net_units} net units "
                            f"(Long: {long_units}, Short: {short_units})"
                        )
            except Exception as e:
                self.logger.debug(f"Could not check aggregated positions: {e}")
            
            return our_trades
        except Exception as e:
            self.logger.error(f"Error checking open positions: {e}")
            return []
    
    def log_position_status(self, context: str = "") -> None:
        """
        Log detailed information about current positions.
        
        Parameters:
        -----------
        context : str
            Context message (e.g., "EUR Market Open")
        """
        try:
            open_trades = self.check_open_positions()
            
            if context:
                self.logger.info(f"=== Position Status at {context} ===")
            
            if not open_trades:
                self.logger.info(f"  No open positions ({self.instrument})")
            else:
                self.logger.info(f"  Open Positions: {len(open_trades)} trade(s)")
                total_units = 0
                for i, trade in enumerate(open_trades, 1):
                    units = int(trade.get('currentUnits', 0))
                    unrealized_pl = float(trade.get('unrealizedPL', 0))
                    trade_id = trade.get('id', 'N/A')
                    price = float(trade.get('price', 0))
                    total_units += units
                    
                    direction = "LONG" if units > 0 else "SHORT"
                    self.logger.info(
                        f"    Trade {i}: ID={trade_id}, {direction} {abs(units)} units, "
                        f"Entry Price={price:.5f}, Unrealized P/L={unrealized_pl:.2f} {trade.get('financing', 'USD')}"
                    )
                
                self.logger.info(f"  Total Position: {total_units} units ({'LONG' if total_units > 0 else 'SHORT' if total_units < 0 else 'FLAT'})")
                self.logger.info(f"  Trades Today: {self.trades_today}/{Settings.MAX_DAILY_TRADES} (EUR: {self.eur_trade_today}, US: {self.us_trade_today})")
            
            if context:
                self.logger.info("=" * 60)
                
        except Exception as e:
            self.logger.error(f"Error logging position status: {e}")
    
    def close_eod_positions(self) -> None:
        """Close all open positions at end of day (EOD exit strategy)."""
        open_trades = self.check_open_positions()
        
        if not open_trades:
            return
        
        self.logger.info(f"Closing {len(open_trades)} EOD positions...")
        
        for trade in open_trades:
            try:
                result = self.client.close_trade(trade['id'])
                self.logger.info(f"Closed trade {trade['id']}: {result}")
            except Exception as e:
                self.logger.error(f"Error closing trade {trade['id']}: {e}")
    
    def execute_trade(self, signal: str, price_info: Dict) -> Optional[Dict]:
        """
        Execute a trade based on signal.
        
        Parameters:
        -----------
        signal : str
            'long', 'short', or 'flat'
        price_info : Dict
            Current market pricing information
            
        Returns:
        --------
        Dict with order result or None if failed
        """
        if signal == 'flat':
            self.logger.info("No signal - staying flat")
            return None
        
        # Check if we should trade
        if self.has_traded_today():
            self.logger.info(f"Already traded today ({self.trades_today} trades)")
            return None
        
        # Check for existing positions (safeguard against overlapping positions)
        open_trades = self.check_open_positions()
        if open_trades:
            self.logger.warning(
                f"SAFEGUARD: Already have {len(open_trades)} open position(s) - skipping trade execution"
            )
            self.log_position_status("Pre-Execution Safeguard")
            return None
        
        # Determine order size
        if signal == 'long':
            units = Settings.POSITION_SIZE
        elif signal == 'short':
            units = -Settings.POSITION_SIZE
        else:
            return None
        
        # Safety check: validate position size
        if Settings.MAX_POSITION_SIZE and abs(units) > Settings.MAX_POSITION_SIZE:
            self.logger.warning(
                f"Position size {abs(units)} exceeds maximum {Settings.MAX_POSITION_SIZE} - rejecting trade"
            )
            return None
        
        # Place order
        try:
            # Log expected fill price (bid for shorts, ask for longs)
            if signal == 'short':
                expected_fill_price = price_info['bid']
            else:  # long
                expected_fill_price = price_info['ask']
            
            self.logger.info(
                f"Placing {signal} order: {units} units, "
                f"Expected Fill: {expected_fill_price:.5f} ({'BID' if signal == 'short' else 'ASK'}), "
                f"TP={Settings.TAKE_PROFIT_PIPS} pips"
            )
            
            order_result = self.client.place_market_order(
                instrument=self.instrument,
                units=units,
                take_profit_pips=Settings.TAKE_PROFIT_PIPS if Settings.TAKE_PROFIT_PIPS else None,
                stop_loss_pips=Settings.STOP_LOSS_PIPS if Settings.STOP_LOSS_PIPS else None
            )
            
            # Extract and log actual fill price and verify TP calculation
            actual_fill_price = None
            tp_price_set = None
            
            if order_result:
                # Get fill price from order fill transaction
                if 'orderFillTransaction' in order_result:
                    fill_transaction = order_result['orderFillTransaction']
                    actual_fill_price = float(fill_transaction.get('price', 0))
                
                # Get TP price that was set
                if 'orderCreateTransaction' in order_result:
                    create_transaction = order_result['orderCreateTransaction']
                    if 'takeProfitOnFill' in create_transaction:
                        tp_price_set = float(create_transaction['takeProfitOnFill'].get('price', 0))
                
                # Verify TP calculation
                if actual_fill_price and tp_price_set and Settings.TAKE_PROFIT_PIPS:
                    if signal == 'short':
                        expected_tp = actual_fill_price - (Settings.TAKE_PROFIT_PIPS * 0.0001)
                        tp_delta_actual = actual_fill_price - tp_price_set
                    else:  # long
                        expected_tp = actual_fill_price + (Settings.TAKE_PROFIT_PIPS * 0.0001)
                        tp_delta_actual = tp_price_set - actual_fill_price
                    
                    tp_delta_pips = tp_delta_actual * 10000  # Convert to pips
                    expected_tp_pips = Settings.TAKE_PROFIT_PIPS
                    
                    self.logger.info(
                        f"✓ Order Filled - Actual Fill Price: {actual_fill_price:.5f}, "
                        f"TP Set: {tp_price_set:.5f}, "
                        f"TP Delta: {tp_delta_actual:.5f} ({tp_delta_pips:.2f} pips, expected {expected_tp_pips:.2f} pips)"
                    )
                    
                    # Warn if TP delta is significantly off (more than 0.5 pip difference)
                    if abs(tp_delta_pips - expected_tp_pips) > 0.5:
                        self.logger.warning(
                            f"⚠️ TP CALCULATION WARNING: TP delta ({tp_delta_pips:.2f} pips) differs from "
                            f"expected ({expected_tp_pips:.2f} pips) by {abs(tp_delta_pips - expected_tp_pips):.2f} pips"
                        )
                elif actual_fill_price:
                    self.logger.info(f"✓ Order Filled - Actual Fill Price: {actual_fill_price:.5f}")
            
            self.logger.info(f"Order placed successfully: {order_result}")
            self.trades_today += 1
            self.last_trade_date = datetime.now(timezone.utc).date()
            
            # Record metrics
            self.metrics.record_trade(success=True, pips=None)  # Pips will be known later
            
            return order_result
            
        except Exception as e:
            self.logger.error(f"Error placing order: {e}", exc_info=True)
            # Record failed trade
            self.metrics.record_trade(success=False, pips=None)
            return None
    
    def run_once(self) -> None:
        """Run trading logic once (check signal and execute if needed)."""
        try:
            # Check if dual market open is enabled
            if Settings.DUAL_MARKET_OPEN_ENABLED:
                self._run_dual_market_open()
            else:
                self._run_single_daily_open()
                
        except Exception as e:
            self.logger.error(f"Error in run_once: {e}", exc_info=True)
    
    def _run_single_daily_open(self) -> None:
        """Run single daily open trading logic (original behavior)."""
        # Check trading hours
        if not self.check_trading_hours():
            self.logger.debug("Outside trading hours")
            return
        
        # Get signal
        signal, price, sma, price_info = self.get_signal()
        
        if price_info is None:
            self.logger.warning("Could not get price info - skipping")
            return
        
        # Format price and SMA safely (handle None values)
        price_str = f"{price:.5f}" if price is not None else "N/A"
        sma_str = f"{sma:.5f}" if sma is not None else "N/A"
        self.logger.info(f"Signal: {signal}, Price: {price_str}, SMA20: {sma_str}")
        
        # Check for existing positions
        open_trades = self.check_open_positions()
        if open_trades:
            self.logger.debug(f"Monitoring {len(open_trades)} open position(s)")
            return
        
        # Execute trade if signal is not flat
        if signal != 'flat':
            self.execute_trade(signal, price_info)
        else:
            self.logger.debug("No signal - staying flat")
    
    def _run_dual_market_open(self) -> None:
        """Run dual market open trading logic with position checks at each market open."""
        # Check EUR market open
        if self.check_eur_market_open():
            # Check positions at EUR market open time (not at function start)
            open_trades = self.check_open_positions()
            self.log_position_status("EUR Market Open (8:00 UTC)")
            
            if self.eur_trade_today:
                self.logger.info("EUR market already traded today - skipping")
            elif open_trades:
                self.logger.warning(
                    f"EUR market open but {len(open_trades)} position(s) already open - "
                    f"SAFEGUARD: Skipping EUR trade to prevent position overlap"
                )
                self.logger.info("  This can happen if a previous trade is still open or if trades closed and reopened")
            else:
                self.logger.info("EUR market open detected (8:00 UTC) - No open positions, proceeding with trade evaluation")
                self._try_market_open_trade('eur')
        
        # Check US market open (independent check with fresh position check)
        if self.check_us_market_open():
            # Check positions at US market open time (not at function start or EUR check time)
            open_trades = self.check_open_positions()
            self.log_position_status("US Market Open (13:00 UTC)")
            
            if self.us_trade_today:
                self.logger.info("US market already traded today - skipping")
            elif open_trades:
                self.logger.warning(
                    f"US market open but {len(open_trades)} position(s) already open - "
                    f"SAFEGUARD: Skipping US trade to prevent position overlap"
                )
                self.logger.info("  This typically means the EUR trade (from 8:00 UTC) is still open")
                # Log details of open trades for debugging
                for trade in open_trades:
                    units = int(trade.get('currentUnits', 0))
                    trade_id = trade.get('id', 'N/A')
                    price = float(trade.get('price', 0))
                    direction = "LONG" if units > 0 else "SHORT"
                    self.logger.info(
                        f"  Open trade: ID={trade_id}, {direction} {abs(units)} units, Entry={price:.5f}"
                    )
            else:
                self.logger.info("US market open detected (13:00 UTC) - No open positions, proceeding with trade evaluation")
                self._try_market_open_trade('us')
    
    def _try_market_open_trade(self, market: str) -> None:
        """
        Try to execute a trade at a market open.
        
        Parameters:
        -----------
        market : str
            'eur' or 'us'
        """
        try:
            # Get market data
            df = self.get_market_data()
            
            if len(df) < Settings.SMA_PERIOD:
                self.logger.warning(f"Insufficient data: {len(df)} candles (need {Settings.SMA_PERIOD})")
                return
            
            # Prepare data
            df = prepare_data_for_strategy(df, Settings.SMA_PERIOD)
            
            # Get signal for this market
            signal, price, sma = get_market_open_signal(df, market, Settings.SMA_PERIOD)
            
            # Get current market pricing (LIVE prices)
            try:
                price_info = self.client.get_current_price(self.instrument)
                price_timestamp = price_info.get('time', 'N/A')
            except Exception as e:
                self.logger.warning(f"Could not get current pricing: {e}")
                return
            
            # Format price and SMA safely (handle None values)
            price_str = f"{price:.5f}" if price is not None else "N/A"
            sma_str = f"{sma:.5f}" if sma is not None else "N/A"
            
            # Log both historical (signal) and live prices with timestamp
            self.logger.info(
                f"{market.upper()} Market Open - Signal: {signal}, "
                f"Historical Close: {price_str}, SMA20: {sma_str}, "
                f"Live Bid: {price_info['bid']:.5f}, Live Ask: {price_info['ask']:.5f}, "
                f"Live Mid: {price_info['mid']:.5f}, Spread: {(price_info['ask'] - price_info['bid']):.5f}, "
                f"Quote Timestamp: {price_timestamp}"
            )
            
            # SAFEGUARD 1: Check if we've hit max daily trades
            if self.has_traded_today():
                self.logger.warning(
                    f"SAFEGUARD TRIGGERED: Already traded today ({self.trades_today}/{Settings.MAX_DAILY_TRADES} trades) - skipping {market.upper()} trade"
                )
                return
            
            # SAFEGUARD 2: Final position check before executing (critical safeguard)
            # This is the last check before we execute - must pass to proceed
            open_trades = self.check_open_positions()
            if open_trades:
                self.logger.warning(
                    f"🚫 SAFEGUARD TRIGGERED: {len(open_trades)} position(s) detected before {market.upper()} trade execution - "
                    f"ABORTING to prevent position overlap"
                )
                self.log_position_status(f"Pre-Execution Check ({market.upper()} Market)")
                
                # Log detailed info about why we're blocking
                for trade in open_trades:
                    trade_id = trade.get('id', 'N/A')
                    units = int(trade.get('currentUnits', 0))
                    entry_price = float(trade.get('price', 0))
                    direction = "LONG" if units > 0 else "SHORT"
                    self.logger.warning(
                        f"  Blocking trade due to existing: Trade ID={trade_id}, "
                        f"{direction} {abs(units)} units at {entry_price:.5f}"
                    )
                return
            
            # Additional defensive log when no positions found
            self.logger.debug(
                f"✓ Position check passed: No open positions found before {market.upper()} trade execution"
            )
            
            # Execute trade if signal is not flat
            if signal != 'flat':
                self.logger.info(f"All safeguards passed - executing {market.upper()} market trade")
                result = self.execute_trade(signal, price_info)
                if result:
                    # Mark this market as traded
                    if market == 'eur':
                        self.eur_trade_today = True
                        self.logger.info(f"EUR market trade completed. Trades today: {self.trades_today}/{Settings.MAX_DAILY_TRADES}")
                    elif market == 'us':
                        self.us_trade_today = True
                        self.logger.info(f"US market trade completed. Trades today: {self.trades_today}/{Settings.MAX_DAILY_TRADES}")
                    
                    # Log position status after trade execution
                    self.log_position_status(f"Post-Execution ({market.upper()} Market)")
                else:
                    self.logger.warning(f"Trade execution returned None for {market.upper()} market")
            else:
                self.logger.info(f"No signal at {market.upper()} market open - staying flat")
                
        except Exception as e:
            self.logger.error(f"Error in _try_market_open_trade ({market}): {e}", exc_info=True)
    
    def run_continuous(self, check_interval_seconds: int = 60) -> None:
        """
        Run trading engine continuously.
        
        Parameters:
        -----------
        check_interval_seconds : int
            Seconds between checks
        """
        self.logger.info("Starting continuous trading loop...")
        self.logger.info(f"Check interval: {check_interval_seconds} seconds")
        
        try:
            while True:
                self.run_once()
                time.sleep(check_interval_seconds)
                
        except KeyboardInterrupt:
            self.logger.info("Trading loop interrupted by user")
        except Exception as e:
            self.logger.error(f"Error in trading loop: {e}", exc_info=True)
            raise

