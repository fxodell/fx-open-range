"""
Market session utilities for EUR and US market opens.

This module provides functions to determine market open times and approximate
market open prices from daily OHLC data.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
import pandas as pd


# Market open times in UTC
EUR_MARKET_OPEN_HOUR = 8  # 8:00 AM UTC (London session open)
US_MARKET_OPEN_HOUR = 13  # 1:00 PM UTC (New York session open, EST = UTC-5)


def get_eur_open_time(date: pd.Timestamp) -> pd.Timestamp:
    """
    Get EUR market open timestamp for a given date.
    
    EUR market (London session) opens at 8:00 AM UTC.
    
    Parameters:
    -----------
    date : pd.Timestamp
        Trading date
        
    Returns:
    --------
    pd.Timestamp
        EUR market open timestamp (8:00 UTC on the given date)
    """
    return pd.Timestamp(
        year=date.year,
        month=date.month,
        day=date.day,
        hour=EUR_MARKET_OPEN_HOUR,
        minute=0,
        second=0,
        tz='UTC'
    )


def get_us_open_time(date: pd.Timestamp) -> pd.Timestamp:
    """
    Get US market open timestamp for a given date.
    
    US market (New York session) opens at 8:00 AM EST = 13:00 UTC (winter)
    or 8:00 AM EDT = 12:00 UTC (summer). For simplicity, we use 13:00 UTC.
    
    Parameters:
    -----------
    date : pd.Timestamp
        Trading date
        
    Returns:
    --------
    pd.Timestamp
        US market open timestamp (13:00 UTC on the given date)
    """
    return pd.Timestamp(
        year=date.year,
        month=date.month,
        day=date.day,
        hour=US_MARKET_OPEN_HOUR,
        minute=0,
        second=0,
        tz='UTC'
    )


def approximate_eur_open_price(daily_df: pd.DataFrame, date: pd.Timestamp) -> Optional[float]:
    """
    Approximate EUR market open price from daily OHLC data.
    
    EUR market opens at 8:00 UTC, which is approximately 10 hours into the
    daily candle (which starts at 22:00 UTC the previous day).
    We approximate by using the current day's open price, which represents
    the price at 22:00 UTC (when the daily candle starts).
    
    Parameters:
    -----------
    daily_df : pd.DataFrame
        DataFrame with Date, Open, High, Low, Close columns
    date : pd.Timestamp
        Date to get EUR open price for
        
    Returns:
    --------
    float or None
        Approximated EUR open price, or None if data not available
    """
    # Find the row for the current trading day
    # The daily candle for "date" starts at 22:00 UTC the previous day
    # EUR opens at 8:00 UTC on "date", which is part of this daily candle
    day_rows = daily_df[daily_df['Date'] == date]
    if len(day_rows) == 0:
        return None
    
    # Use the current day's open (price at 22:00 UTC previous day)
    # This is a reasonable approximation for EUR open at 8:00 UTC
    row = day_rows.iloc[0]
    return row['Open']


def approximate_us_open_price(daily_df: pd.DataFrame, date: pd.Timestamp) -> Optional[float]:
    """
    Approximate US market open price from daily OHLC data.
    
    US market opens at 13:00 UTC, which is approximately 30% through
    the trading day (assuming daily candle spans 22:00 UTC to 22:00 UTC next day).
    We interpolate between daily open and close.
    
    Parameters:
    -----------
    daily_df : pd.DataFrame
        DataFrame with Date, Open, High, Low, Close columns
    date : pd.Timestamp
        Date to get US open price for
        
    Returns:
    --------
    float or None
        Approximated US open price, or None if data not available
    """
    # Find the row for the current trading day
    day_rows = daily_df[daily_df['Date'] == date]
    if len(day_rows) == 0:
        return None
    
    row = day_rows.iloc[0]
    
    # US open is approximately 30% through the trading day
    # Interpolate between daily open and close
    daily_range = row['Close'] - row['Open']
    us_open_price = row['Open'] + (daily_range * 0.3)
    
    return us_open_price


def get_market_open_prices(daily_df: pd.DataFrame, date: pd.Timestamp) -> Tuple[Optional[float], Optional[float]]:
    """
    Get both EUR and US market open prices for a given date.
    
    Parameters:
    -----------
    daily_df : pd.DataFrame
        DataFrame with Date, Open, High, Low, Close columns
    date : pd.Timestamp
        Trading date
        
    Returns:
    --------
    tuple (eur_open_price, us_open_price)
        EUR and US market open prices, or None if not available
    """
    eur_open = approximate_eur_open_price(daily_df, date)
    us_open = approximate_us_open_price(daily_df, date)
    
    return eur_open, us_open


def is_market_open_time(current_time: datetime, market: str = 'both') -> bool:
    """
    Check if current time is within a market open window.
    
    Parameters:
    -----------
    current_time : datetime
        Current time (should be timezone-aware UTC)
    market : str
        'eur', 'us', or 'both' (default: 'both')
        
    Returns:
    --------
    bool
        True if within market open window
    """
    if not isinstance(current_time, datetime):
        return False
    
    # Ensure timezone-aware
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    
    hour = current_time.hour
    
    if market == 'eur':
        # EUR market open window: 8:00-9:00 UTC
        return hour == EUR_MARKET_OPEN_HOUR
    elif market == 'us':
        # US market open window: 13:00-14:00 UTC
        return hour == US_MARKET_OPEN_HOUR
    elif market == 'both':
        # Either market open
        return hour == EUR_MARKET_OPEN_HOUR or hour == US_MARKET_OPEN_HOUR
    else:
        return False

