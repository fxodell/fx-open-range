"""
Market Data Service - Handles fetching and preparing market data.
"""

import pandas as pd
from datetime import datetime, timezone, timedelta
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
        Fetch market data for specified number of days.
        
        Parameters:
        -----------
        days : int
            Number of days of data to fetch
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with Date, Open, High, Low, Close columns
        """
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)
        
        df = self.client.fetch_candles(
            instrument=self.instrument,
            granularity="D",
            from_time=start_time,
            to_time=end_time
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


