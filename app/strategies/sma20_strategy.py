"""
Price Trend (SMA20) Directional Strategy Implementation.
"""

import pandas as pd
import numpy as np
from typing import Literal, Optional, Tuple


TradeSignal = Literal['long', 'short', 'flat']


def calculate_sma(df: pd.DataFrame, price_col: str = 'Close', window: int = 20) -> pd.Series:
    """Calculate Simple Moving Average."""
    return df[price_col].rolling(window=window, min_periods=window).mean()


def strategy_price_trend_directional(df: pd.DataFrame, sma_period: int = 20) -> pd.Series:
    """
    Price Trend (SMA20) Directional Strategy.
    
    Logic:
    - BUY (LONG) when: Yesterday's Close > SMA20 (uptrend)
    - SELL (SHORT) when: Yesterday's Close < SMA20 (downtrend)
    - FLAT when: Signal unclear or insufficient data
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with Date, Open, High, Low, Close columns
    sma_period : int
        Period for SMA calculation (default: 20)
        
    Returns:
    --------
    pd.Series
        Trading signals: 'long', 'short', or 'flat'
    """
    signals = pd.Series('flat', index=df.index)
    
    # Calculate SMA if not already present
    sma_col = f'SMA{sma_period}'
    if sma_col not in df.columns:
        df[sma_col] = calculate_sma(df, 'Close', sma_period)
    
    # Get yesterday's close (shifted by 1 to avoid lookahead bias)
    prev_close = df['Close'].shift(1)
    sma = df[sma_col]
    
    # Generate signals
    # Buy when price above SMA20 (uptrend)
    signals.loc[prev_close > sma] = 'long'
    
    # Sell when price below SMA20 (downtrend)
    signals.loc[prev_close < sma] = 'short'
    
    # Set to flat if SMA not available (not enough data)
    signals.loc[sma.isna()] = 'flat'
    
    return signals


def prepare_data_for_strategy(candles_df: pd.DataFrame, sma_period: int = 20) -> pd.DataFrame:
    """
    Prepare historical data for strategy analysis.
    
    Parameters:
    -----------
    candles_df : pd.DataFrame
        DataFrame with Date, Open, High, Low, Close columns
    sma_period : int
        SMA period
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with SMA column added
    """
    df = candles_df.copy()
    df['SMA20'] = calculate_sma(df, 'Close', sma_period)
    return df


def get_current_signal(candles_df: pd.DataFrame, sma_period: int = 20) -> Tuple[TradeSignal, Optional[float], Optional[float]]:
    """
    Get the current trading signal based on latest data.
    
    Parameters:
    -----------
    candles_df : pd.DataFrame
        DataFrame with Date, Open, High, Low, Close columns
    sma_period : int
        SMA period
        
    Returns:
    --------
    tuple (signal, current_price, sma_value)
        signal: 'long', 'short', or 'flat'
        current_price: Latest close price
        sma_value: Current SMA value
    """
    if len(candles_df) < sma_period:
        return 'flat', None, None
    
    df = prepare_data_for_strategy(candles_df, sma_period)
    
    # Get signals
    signals = strategy_price_trend_directional(df, sma_period)
    
    # Get latest values
    latest_signal = signals.iloc[-1]
    latest_close = df['Close'].iloc[-1]
    latest_sma = df['SMA20'].iloc[-1]
    
    return latest_signal, latest_close, latest_sma

