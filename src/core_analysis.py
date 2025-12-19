"""
Core analysis functions for daily range and open-based moves.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
from .data_loader import price_to_pips


def calculate_daily_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate daily range, open-based moves, and related metrics.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with columns: Date, Open, High, Low, Close
        
    Returns:
    --------
    pd.DataFrame
        Original DataFrame with added columns:
        - range_pips: Daily range (High - Low) in pips
        - up_from_open_pips: High - Open in pips
        - down_from_open_pips: Open - Low in pips
        - net_from_open_pips: Close - Open in pips
        - body_pips: |Close - Open| in pips
        - upper_shadow_pips: High - max(Open, Close) in pips
        - lower_shadow_pips: min(Open, Close) - Low in pips
    """
    df = df.copy()
    
    # Calculate in price terms first
    df['range'] = df['High'] - df['Low']
    df['up_from_open'] = df['High'] - df['Open']
    df['down_from_open'] = df['Open'] - df['Low']
    df['net_from_open'] = df['Close'] - df['Open']
    df['body'] = np.abs(df['Close'] - df['Open'])
    df['upper_shadow'] = df['High'] - np.maximum(df['Open'], df['Close'])
    df['lower_shadow'] = np.minimum(df['Open'], df['Close']) - df['Low']
    
    # Convert to pips
    df['range_pips'] = price_to_pips(df['range'])
    df['up_from_open_pips'] = price_to_pips(df['up_from_open'])
    df['down_from_open_pips'] = price_to_pips(df['down_from_open'])
    df['net_from_open_pips'] = price_to_pips(df['net_from_open'])
    df['body_pips'] = price_to_pips(df['body'])
    df['upper_shadow_pips'] = price_to_pips(df['upper_shadow'])
    df['lower_shadow_pips'] = price_to_pips(df['lower_shadow'])
    
    # Drop intermediate columns (keep only pips versions)
    df = df.drop(columns=['range', 'up_from_open', 'down_from_open', 'net_from_open', 
                          'body', 'upper_shadow', 'lower_shadow'])
    
    return df


def calculate_distribution_stats(df: pd.DataFrame, col: str) -> Dict[str, float]:
    """
    Calculate comprehensive distribution statistics for a column.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with the column of interest
    col : str
        Column name to analyze
        
    Returns:
    --------
    dict
        Dictionary with mean, median, std, min, max, and percentiles
    """
    data = df[col].dropna()
    
    stats = {
        'count': len(data),
        'mean': data.mean(),
        'median': data.median(),
        'std': data.std(),
        'min': data.min(),
        'max': data.max(),
        'p10': data.quantile(0.10),
        'p25': data.quantile(0.25),
        'p50': data.quantile(0.50),
        'p75': data.quantile(0.75),
        'p90': data.quantile(0.90),
        'p95': data.quantile(0.95),
        'p99': data.quantile(0.99),
    }
    
    return stats


def analyze_range_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze how often certain pip moves from the open occur.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with range metrics (from calculate_daily_metrics)
        
    Returns:
    --------
    pd.DataFrame
        Summary DataFrame showing frequency of pip thresholds
    """
    thresholds = [5, 10, 15, 20, 25, 30, 40, 50, 60, 75, 100]
    
    results = []
    for threshold in thresholds:
        up_count = (df['up_from_open_pips'] >= threshold).sum()
        down_count = (df['down_from_open_pips'] >= threshold).sum()
        range_count = (df['range_pips'] >= threshold).sum()
        
        results.append({
            'threshold_pips': threshold,
            'up_from_open_count': up_count,
            'up_from_open_pct': 100 * up_count / len(df),
            'down_from_open_count': down_count,
            'down_from_open_pct': 100 * down_count / len(df),
            'range_count': range_count,
            'range_pct': 100 * range_count / len(df),
        })
    
    return pd.DataFrame(results)


def calculate_adr(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """
    Calculate Average Daily Range (ADR) over a rolling window.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with 'range_pips' column
    window : int
        Rolling window size (default 20)
        
    Returns:
    --------
    pd.Series
        ADR series (indexed same as df)
    """
    return df['range_pips'].rolling(window=window, min_periods=1).mean()


def calculate_mfe_mae(df: pd.DataFrame, entry_price_col: str = 'Open', 
                     direction: str = 'long') -> Tuple[pd.Series, pd.Series]:
    """
    Calculate Maximum Favorable Excursion (MFE) and Maximum Adverse Excursion (MAE)
    from the open, assuming a trade in the specified direction.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with OHLC data
    entry_price_col : str
        Column name for entry price (default 'Open')
    direction : str
        'long' or 'short'
        
    Returns:
    --------
    Tuple[pd.Series, pd.Series]
        (MFE in pips, MAE in pips)
    """
    if direction == 'long':
        # For long: MFE = High - Entry, MAE = Entry - Low
        mfe_price = df['High'] - df[entry_price_col]
        mae_price = df[entry_price_col] - df['Low']
    else:  # short
        # For short: MFE = Entry - Low, MAE = High - Entry
        mfe_price = df[entry_price_col] - df['Low']
        mae_price = df['High'] - df[entry_price_col]
    
    mfe_pips = price_to_pips(mfe_price)
    mae_pips = price_to_pips(mae_price)
    
    return mfe_pips, mae_pips

