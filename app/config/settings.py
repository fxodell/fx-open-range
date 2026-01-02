"""
Configuration settings for the trading application.
"""

import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings and configuration."""
    
    # OANDA API Configuration
    OANDA_API_TOKEN: Optional[str] = os.getenv("OANDA_API_TOKEN")
    OANDA_PRACTICE_MODE: bool = os.getenv("OANDA_PRACTICE_MODE", "true").lower() == "true"
    OANDA_ACCOUNT_ID: Optional[str] = os.getenv("OANDA_ACCOUNT_ID", None)
    
    # Trading Configuration
    INSTRUMENT: str = "EUR_USD"
    TAKE_PROFIT_PIPS: float = 10.0
    STOP_LOSS_PIPS: Optional[float] = None  # None = EOD exit (no stop loss)
    POSITION_SIZE: int = 1000  # Units (1 mini lot = $1 per pip for EUR/USD)
    SPREAD_COST_PIPS: float = 2.0  # Estimated spread cost
    
    # Strategy Configuration (Price Trend SMA20)
    SMA_PERIOD: int = 20
    STRATEGY_NAME: str = "Price Trend (SMA20) Directional"
    
    # Trading Hours (UTC)
    # EUR/USD daily candle opens at 22:00 UTC (New York close)
    # Set to 22-23 UTC to trade at the daily open (matches backtest strategy)
    TRADING_START_HOUR: int = 22  # Start of trading day (UTC) - 22:00 = daily open
    TRADING_END_HOUR: int = 23  # End of trading window (UTC) - gives 1 hour window
    
    # Dual Market Open Configuration
    DUAL_MARKET_OPEN_ENABLED: bool = True  # Enable dual market open trading
    EUR_MARKET_OPEN_HOUR: int = 8  # EUR market open (London session) - 8:00 UTC
    US_MARKET_OPEN_HOUR: int = 13  # US market open (New York session) - 13:00 UTC
    
    # Risk Management
    MAX_DAILY_TRADES: int = 2  # Allow 2 trades per day (one per session) when dual market enabled
    MAX_DAILY_LOSS_PIPS: Optional[float] = None  # Optional: stop trading after X pips loss
    MAX_DRAWDOWN_PIPS: Optional[float] = None  # Optional: stop trading after X pips drawdown
    MAX_POSITION_SIZE: Optional[int] = None  # Optional: maximum position size in units
    
    # Logging
    LOG_DIR: Path = Path(__file__).parent.parent.parent / "logs"
    LOG_LEVEL: str = "INFO"
    
    # Data Storage
    DATA_DIR: Path = Path(__file__).parent.parent.parent / "data"
    
    @classmethod
    def validate(cls) -> list[str]:
        """Validate settings and return list of warnings/issues."""
        warnings = []
        
        if not cls.OANDA_API_TOKEN:
            warnings.append("ERROR: OANDA_API_TOKEN not set! Please set it in .env file or environment variable.")
        
        if not cls.OANDA_PRACTICE_MODE:
            warnings.append("⚠️  LIVE MODE ENABLED - Real money trading!")
        else:
            warnings.append("✓ Practice mode enabled (safe for testing)")
        
        if cls.STOP_LOSS_PIPS is None:
            warnings.append("⚠️  No stop loss set - trades will exit at end-of-day")
        
        if cls.POSITION_SIZE > 10000:
            warnings.append(f"⚠️  Large position size: {cls.POSITION_SIZE} units")
        
        return warnings
    
    @classmethod
    def print_settings(cls):
        """Print current settings."""
        print("=" * 80)
        print("TRADING APPLICATION SETTINGS")
        print("=" * 80)
        print(f"API Mode: {'PRACTICE' if cls.OANDA_PRACTICE_MODE else 'LIVE'}")
        print(f"Instrument: {cls.INSTRUMENT}")
        print(f"Strategy: {cls.STRATEGY_NAME}")
        print(f"Take Profit: {cls.TAKE_PROFIT_PIPS} pips")
        print(f"Stop Loss: {cls.STOP_LOSS_PIPS if cls.STOP_LOSS_PIPS else 'EOD Exit'}")
        print(f"Position Size: {cls.POSITION_SIZE} units")
        print(f"SMA Period: {cls.SMA_PERIOD}")
        print(f"Max Daily Trades: {cls.MAX_DAILY_TRADES}")
        print(f"Dual Market Open: {'ENABLED' if cls.DUAL_MARKET_OPEN_ENABLED else 'DISABLED'}")
        if cls.DUAL_MARKET_OPEN_ENABLED:
            print(f"EUR Market Open: {cls.EUR_MARKET_OPEN_HOUR:02d}:00 UTC")
            print(f"US Market Open: {cls.US_MARKET_OPEN_HOUR:02d}:00 UTC")
        print("=" * 80)
        
        warnings = cls.validate()
        for warning in warnings:
            print(warning)
        print("=" * 80)

