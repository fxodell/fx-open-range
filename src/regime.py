"""
Market regime detection: bull, bear, or choppy markets.
"""

import pandas as pd
import numpy as np
from typing import Literal


RegimeType = Literal['bull', 'bear', 'chop']


def calculate_moving_averages(df: pd.DataFrame, 
                             periods: list = [20, 50, 100, 200]) -> pd.DataFrame:
    """
    Calculate moving averages for Close prices.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with 'Close' column
    periods : list
        List of periods for moving averages
        
    Returns:
    --------
    pd.DataFrame
        Original DataFrame with added SMA columns (e.g., 'SMA20', 'SMA50')
    """
    df = df.copy()
    
    for period in periods:
        df[f'SMA{period}'] = df['Close'].rolling(window=period, min_periods=1).mean()
    
    return df


def calculate_momentum(df: pd.DataFrame, periods: list = [1, 3, 6]) -> pd.DataFrame:
    """
    Calculate momentum (returns) over different periods (in months, approximated as ~20 trading days).
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with 'Close' column
    periods : list
        List of periods in months (each month ≈ 20 trading days)
        
    Returns:
    --------
    pd.DataFrame
        Original DataFrame with added momentum columns
    """
    df = df.copy()
    
    for period_months in periods:
        period_days = period_months * 20
        df[f'momentum_{period_months}m'] = df['Close'].pct_change(periods=period_days) * 100
    
    return df


def classify_regime(df: pd.DataFrame, 
                   price_col: str = 'Close',
                   sma_short: int = 50,
                   sma_long: int = 200) -> pd.DataFrame:
    """
    Classify market regime as bull, bear, or chop based on price vs MAs.
    
    Classification rules (using only data available up to that day):
    - Bull: Price > SMA_short > SMA_long AND SMA_short trending up
    - Bear: Price < SMA_short < SMA_long AND SMA_short trending down
    - Chop: Everything else
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with Close and SMA columns
    price_col : str
        Column name for price (default 'Close')
    sma_short : int
        Short MA period (default 50)
    sma_long : int
        Long MA period (default 200)
        
    Returns:
    --------
    pd.DataFrame
        Original DataFrame with added 'regime' column ('bull', 'bear', or 'chop')
    """
    df = df.copy()
    
    sma_short_col = f'SMA{sma_short}'
    sma_long_col = f'SMA{sma_long}'
    
    # Calculate MA slopes (using 5-day change as proxy for trend)
    df[f'{sma_short_col}_slope'] = df[sma_short_col].diff(5)
    
    # Initialize regime column
    df['regime'] = 'chop'
    
    # Bull conditions
    bull_mask = (
        (df[price_col] > df[sma_short_col]) &
        (df[sma_short_col] > df[sma_long_col]) &
        (df[f'{sma_short_col}_slope'] > 0)
    )
    
    # Bear conditions
    bear_mask = (
        (df[price_col] < df[sma_short_col]) &
        (df[sma_short_col] < df[sma_long_col]) &
        (df[f'{sma_short_col}_slope'] < 0)
    )
    
    df.loc[bull_mask, 'regime'] = 'bull'
    df.loc[bear_mask, 'regime'] = 'bear'
    
    # Clean up temporary column
    df = df.drop(columns=[f'{sma_short_col}_slope'])
    
    return df


def analyze_regime_performance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze how daily range and open-based moves differ by regime.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with 'regime' and range metrics
        
    Returns:
    --------
    pd.DataFrame
        Summary statistics by regime
    """
    regime_cols = ['range_pips', 'up_from_open_pips', 'down_from_open_pips', 
                   'net_from_open_pips']
    
    results = []
    for regime in ['bull', 'bear', 'chop']:
        regime_df = df[df['regime'] == regime]
        if len(regime_df) == 0:
            continue
            
        row = {'regime': regime, 'count': len(regime_df)}
        for col in regime_cols:
            row[f'{col}_mean'] = regime_df[col].mean()
            row[f'{col}_median'] = regime_df[col].median()
            row[f'{col}_std'] = regime_df[col].std()
        
        results.append(row)
    
    return pd.DataFrame(results)

