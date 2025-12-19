"""
Data loading and cleaning for EUR/USD OHLC data.
"""

import pandas as pd
import numpy as np
from pathlib import Path


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

