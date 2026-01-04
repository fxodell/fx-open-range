"""
Signal Service - Handles signal generation for trading strategies.
"""

import pandas as pd
from typing import Dict, Optional, Tuple
from app.strategies.sma20_strategy import get_current_signal
from app.strategies.dual_market_open_strategy import get_dual_market_signals, get_market_open_signal
from app.config.settings import Settings


class SignalService:
    """Service for generating trading signals."""
    
    def get_signal(self, df: pd.DataFrame, sma_period: int = None) -> Tuple[str, Optional[float], Optional[float]]:
        """
        Get current trading signal.
        
        Parameters:
        -----------
        df : pd.DataFrame
            Market data with SMA calculated
        sma_period : int, optional
            SMA period (default: from Settings)
            
        Returns:
        --------
        tuple (signal, price, sma)
            signal: 'long', 'short', or 'flat'
            price: Current close price
            sma: Current SMA value
        """
        sma_period = sma_period or Settings.SMA_PERIOD
        return get_current_signal(df, sma_period)
    
    def get_dual_market_signals(self, df: pd.DataFrame, sma_period: int = None) -> Dict:
        """
        Get signals for both EUR and US market opens.
        
        Parameters:
        -----------
        df : pd.DataFrame
            Market data with SMA calculated
        sma_period : int, optional
            SMA period (default: from Settings)
            
        Returns:
        --------
        dict
            Dictionary with 'eur' and 'us' keys, each containing (signal, price, sma) tuple
        """
        sma_period = sma_period or Settings.SMA_PERIOD
        return get_dual_market_signals(df, sma_period)
    
    def get_market_open_signal(self, df: pd.DataFrame, market: str, sma_period: int = None) -> Tuple[str, Optional[float], Optional[float]]:
        """
        Get signal for a specific market open.
        
        Parameters:
        -----------
        df : pd.DataFrame
            Market data with SMA calculated
        market : str
            'eur' or 'us'
        sma_period : int, optional
            SMA period (default: from Settings)
            
        Returns:
        --------
        tuple (signal, price, sma)
            signal: 'long', 'short', or 'flat'
            price: Market open price
            sma: Current SMA value
        """
        sma_period = sma_period or Settings.SMA_PERIOD
        return get_market_open_signal(df, market, sma_period)


