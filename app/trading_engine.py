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
from app.strategies.sma20_strategy import get_current_signal, prepare_data_for_strategy


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
            return False
        
        return self.trades_today >= Settings.MAX_DAILY_TRADES
    
    def get_market_data(self, days: int = 30) -> pd.DataFrame:
        """Fetch market data for strategy analysis."""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)
        
        df = self.client.fetch_candles(
            instrument=self.instrument,
            granularity="D",
            from_time=start_time,
            to_time=end_time
        )
        
        return df
    
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
            try:
                price_info = self.client.get_current_price(self.instrument)
            except Exception as e:
                self.logger.warning(f"Could not get current pricing: {e}")
                price_info = None
            
            return signal, price, sma, price_info
            
        except Exception as e:
            self.logger.error(f"Error getting signal: {e}", exc_info=True)
            return 'flat', None, None, None
    
    def check_open_positions(self) -> List[Dict]:
        """Check for open positions in our instrument."""
        try:
            open_trades = self.client.get_open_trades()
            our_trades = [t for t in open_trades if t['instrument'] == self.instrument]
            return our_trades
        except Exception as e:
            self.logger.error(f"Error checking open positions: {e}")
            return []
    
    def close_eod_positions(self):
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
        
        # Check for existing positions
        open_trades = self.check_open_positions()
        if open_trades:
            self.logger.info(f"Already have {len(open_trades)} open position(s) - skipping")
            return None
        
        # Determine order size
        if signal == 'long':
            units = Settings.POSITION_SIZE
        elif signal == 'short':
            units = -Settings.POSITION_SIZE
        else:
            return None
        
        # Place order
        try:
            self.logger.info(f"Placing {signal} order: {units} units, TP={Settings.TAKE_PROFIT_PIPS} pips")
            
            order_result = self.client.place_market_order(
                instrument=self.instrument,
                units=units,
                take_profit_pips=Settings.TAKE_PROFIT_PIPS if Settings.TAKE_PROFIT_PIPS else None,
                stop_loss_pips=Settings.STOP_LOSS_PIPS if Settings.STOP_LOSS_PIPS else None
            )
            
            self.logger.info(f"Order placed successfully: {order_result}")
            self.trades_today += 1
            self.last_trade_date = datetime.now(timezone.utc).date()
            
            return order_result
            
        except Exception as e:
            self.logger.error(f"Error placing order: {e}", exc_info=True)
            return None
    
    def run_once(self):
        """Run trading logic once (check signal and execute if needed)."""
        try:
            # Check trading hours
            if not self.check_trading_hours():
                self.logger.debug("Outside trading hours")
                return
            
            # Get signal
            signal, price, sma, price_info = self.get_signal()
            
            if price_info is None:
                self.logger.warning("Could not get price info - skipping")
                return
            
            self.logger.info(f"Signal: {signal}, Price: {price:.5f}, SMA20: {sma:.5f if sma else 'N/A'}")
            
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
                
        except Exception as e:
            self.logger.error(f"Error in run_once: {e}", exc_info=True)
    
    def run_continuous(self, check_interval_seconds: int = 60):
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

