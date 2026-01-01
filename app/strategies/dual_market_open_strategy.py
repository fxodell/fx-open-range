"""
Dual Market Open Strategy Implementation for Live Trading.

This strategy trades at both EUR market open (8:00 UTC) and US market open (13:00 UTC)
using the same SMA20 directional logic as the single daily open strategy.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Literal, Optional, Tuple, Dict
from .sma20_strategy import (
    calculate_sma,
    prepare_data_for_strategy,
    get_current_signal,
    TradeSignal,
)


def get_dual_market_signals(candles_df: pd.DataFrame, sma_period: int = 20) -> Dict[str, Tuple[TradeSignal, Optional[float], Optional[float]]]:
    """
    Get trading signals for both EUR and US market opens.
    
    Both signals use the same SMA20 directional logic:
    - BUY (LONG) when: Yesterday's Close > SMA20 (uptrend)
    - SELL (SHORT) when: Yesterday's Close < SMA20 (downtrend)
    
    Parameters:
    -----------
    candles_df : pd.DataFrame
        DataFrame with Date, Open, High, Low, Close columns
    sma_period : int
        SMA period (default: 20)
        
    Returns:
    --------
    Dict with keys:
        'eur': tuple (signal, current_price, sma_value) for EUR market open
        'us': tuple (signal, current_price, sma_value) for US market open
    """
    # Both EUR and US opens use the same signal logic
    # (based on previous day's close vs SMA20)
    eur_signal, price, sma = get_current_signal(candles_df, sma_period)
    us_signal, _, _ = get_current_signal(candles_df, sma_period)
    
    return {
        'eur': (eur_signal, price, sma),
        'us': (us_signal, price, sma),
    }


def check_eur_market_open(current_time: Optional[datetime] = None) -> bool:
    """
    Check if current time is within EUR market open window (8:00 UTC).
    
    Parameters:
    -----------
    current_time : datetime, optional
        Current time (default: now in UTC)
        
    Returns:
    --------
    bool
        True if within EUR market open window
    """
    if current_time is None:
        current_time = datetime.now(timezone.utc)
    
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    
    # EUR market open: 8:00-9:00 UTC
    return current_time.hour == 8


def check_us_market_open(current_time: Optional[datetime] = None) -> bool:
    """
    Check if current time is within US market open window (13:00 UTC).
    
    Parameters:
    -----------
    current_time : datetime, optional
        Current time (default: now in UTC)
        
    Returns:
    --------
    bool
        True if within US market open window
    """
    if current_time is None:
        current_time = datetime.now(timezone.utc)
    
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    
    # US market open: 13:00-14:00 UTC
    return current_time.hour == 13


def get_market_open_signal(candles_df: pd.DataFrame, 
                          market: str,
                          sma_period: int = 20) -> Tuple[TradeSignal, Optional[float], Optional[float]]:
    """
    Get trading signal for a specific market open.
    
    Parameters:
    -----------
    candles_df : pd.DataFrame
        DataFrame with Date, Open, High, Low, Close columns
    market : str
        'eur' or 'us'
    sma_period : int
        SMA period (default: 20)
        
    Returns:
    --------
    tuple (signal, current_price, sma_value)
        signal: 'long', 'short', or 'flat'
        current_price: Latest close price
        sma_value: Current SMA value
    """
    if market.lower() not in ['eur', 'us']:
        raise ValueError("market must be 'eur' or 'us'")
    
    signals = get_dual_market_signals(candles_df, sma_period)
    return signals[market.lower()]

