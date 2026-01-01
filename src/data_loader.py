"""
Data loading and cleaning for EUR/USD OHLC data.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional
from .market_sessions import get_market_open_prices, get_eur_open_time, get_us_open_time


def load_eurusd_data(filepath: str) -> pd.DataFrame:
    """
    Load and clean EUR/USD OHLC data from CSV.
    
    Parameters:
    -----------
    filepath : str
        Path to the CSV file
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with columns: Date, Open, High, Low, Close
        Sorted chronologically (oldest first)
    """
    df = pd.read_csv(filepath)
    
    # The CSV has "Price" which appears to be Close price
    # Rename and clean columns
    df = df.rename(columns={
        'Price': 'Close',
        'Date': 'Date'
    })
    
    # Parse dates
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
    
    # Convert OHLC to float (handle any string formatting)
    for col in ['Open', 'High', 'Low', 'Close']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Sort chronologically (oldest first)
    df = df.sort_values('Date').reset_index(drop=True)
    
    # Keep only essential columns
    df = df[['Date', 'Open', 'High', 'Low', 'Close']].copy()
    
    # Remove any rows with missing data
    df = df.dropna().reset_index(drop=True)
    
    return df


def price_to_pips(price_diff: float) -> float:
    """
    Convert price difference to pips.
    For EUR/USD: 1 pip = 0.0001
    
    Parameters:
    -----------
    price_diff : float
        Price difference (e.g., High - Low)
        
    Returns:
    --------
    float
        Difference in pips
    """
    return price_diff * 10000


def pips_to_price(pips: float) -> float:
    """
    Convert pips to price difference.
    
    Parameters:
    -----------
    pips : float
        Number of pips
        
    Returns:
    --------
    float
        Price difference
    """
    return pips / 10000


def load_intraday_data(filepath: str, granularity: str = 'H1') -> Optional[pd.DataFrame]:
    """
    Load intraday OHLC data from CSV (if available).
    
    Parameters:
    -----------
    filepath : str
        Path to the CSV file
    granularity : str
        Data granularity ('H1', 'M15', etc.)
        
    Returns:
    --------
    pd.DataFrame or None
        DataFrame with intraday OHLC data, or None if file doesn't exist
    """
    path = Path(filepath)
    if not path.exists():
        return None
    
    try:
        df = pd.read_csv(filepath)
        
        # Try to parse timestamp/date column
        date_cols = ['Date', 'Time', 'Timestamp', 'datetime']
        date_col = None
        for col in date_cols:
            if col in df.columns:
                date_col = col
                break
        
        if date_col is None:
            return None
        
        # Parse dates
        df['Date'] = pd.to_datetime(df[date_col])
        
        # Ensure OHLC columns exist
        required_cols = ['Open', 'High', 'Low', 'Close']
        if not all(col in df.columns for col in required_cols):
            return None
        
        # Convert OHLC to float
        for col in required_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Sort chronologically
        df = df.sort_values('Date').reset_index(drop=True)
        
        # Remove missing data
        df = df.dropna(subset=required_cols).reset_index(drop=True)
        
        return df[['Date', 'Open', 'High', 'Low', 'Close']].copy()
        
    except Exception:
        return None


def add_market_open_prices(daily_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add EUR and US market open price columns to daily DataFrame.
    
    This function approximates market open prices from daily OHLC data
    and adds them as new columns: 'EUR_Open' and 'US_Open'.
    
    Parameters:
    -----------
    daily_df : pd.DataFrame
        DataFrame with Date, Open, High, Low, Close columns
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with added 'EUR_Open' and 'US_Open' columns
    """
    df = daily_df.copy()
    
    eur_opens = []
    us_opens = []
    
    for idx, row in df.iterrows():
        date = pd.Timestamp(row['Date'])
        eur_open, us_open = get_market_open_prices(df, date)
        eur_opens.append(eur_open)
        us_opens.append(us_open)
    
    df['EUR_Open'] = eur_opens
    df['US_Open'] = us_opens
    
    return df

