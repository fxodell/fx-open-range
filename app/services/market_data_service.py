"""
Market Data Service - Handles fetching and preparing market data.
"""

import pandas as pd
from typing import Optional
from app.utils.oanda_client import OandaTradingClient
from app.strategies.sma20_strategy import prepare_data_for_strategy
from app.config.settings import Settings


class MarketDataService:
    """Service for fetching and preparing market data."""
    
    def __init__(self, client: OandaTradingClient, instrument: str = None):
        """
        Initialize market data service.
        
        Parameters:
        -----------
        client : OandaTradingClient
            OANDA API client
        instrument : str, optional
            Trading instrument (default: from Settings)
        """
        self.client = client
        self.instrument = instrument or Settings.INSTRUMENT
    
    def fetch_market_data(self, days: int = 30) -> pd.DataFrame:
        """
        Fetch market data using count-based fetching for reliability.
        
        Uses count-based fetching (more reliable than date-based) with a buffer
        to ensure we get enough complete candles for indicator calculations.
        
        Parameters:
        -----------
        days : int
            Number of days (deprecated - kept for compatibility).
            Actual count is calculated based on SMA_PERIOD with buffer.
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with Date, Open, High, Low, Close columns
        """
        # Use count-based fetching with buffer: request 50% more candles than needed
        # This ensures we have enough complete candles even after filtering incomplete ones
        # For SMA20, request 30 candles to ensure we get at least 20 complete ones
        requested_count = int(Settings.SMA_PERIOD * 1.5)  # 50% buffer
        
        df = self.client.fetch_candles(
            instrument=self.instrument,
            granularity="D",
            count=requested_count  # Use count instead of date range for reliability
        )
        
        return df
    
    def prepare_data_for_strategy(self, df: pd.DataFrame, sma_period: int = None) -> pd.DataFrame:
        """
        Prepare market data for strategy analysis.
        
        Parameters:
        -----------
        df : pd.DataFrame
            Raw market data
        sma_period : int, optional
            SMA period (default: from Settings)
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with SMA column added
        """
        sma_period = sma_period or Settings.SMA_PERIOD
        return prepare_data_for_strategy(df, sma_period)
    
    def get_data_with_sma(self, days: int = 30, sma_period: int = None) -> pd.DataFrame:
        """
        Fetch and prepare market data with SMA calculated.
        
        Parameters:
        -----------
        days : int
            Number of days of data to fetch
        sma_period : int, optional
            SMA period (default: from Settings)
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with Date, Open, High, Low, Close, SMA columns
        """
        df = self.fetch_market_data(days)
        return self.prepare_data_for_strategy(df, sma_period)



