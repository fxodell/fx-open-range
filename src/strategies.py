"""
Strategy definitions for trade-at-open strategies.
"""

import pandas as pd
import numpy as np
from typing import Literal
from .core_analysis import calculate_adr
from .regime import RegimeType


TradeSignal = Literal['long', 'short', 'flat']


def strategy_always_buy(df: pd.DataFrame, **kwargs) -> pd.Series:
    """
    Baseline strategy: Always buy at open.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with OHLC data
        
    Returns:
    --------
    pd.Series
        Signals: 'long' for all days
    """
    return pd.Series('long', index=df.index)


def strategy_always_sell(df: pd.DataFrame, **kwargs) -> pd.Series:
    """
    Baseline strategy: Always sell at open.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with OHLC data
        
    Returns:
    --------
    pd.Series
        Signals: 'short' for all days
    """
    return pd.Series('short', index=df.index)


def strategy_regime_aligned(df: pd.DataFrame, **kwargs) -> pd.Series:
    """
    Strategy: Trade only in direction of regime.
    - Bull regime → buy at open
    - Bear regime → sell at open
    - Chop → no trade
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with 'regime' column
        
    Returns:
    --------
    pd.Series
        Signals based on regime
    """
    signals = pd.Series('flat', index=df.index)
    
    signals.loc[df['regime'] == 'bull'] = 'long'
    signals.loc[df['regime'] == 'bear'] = 'short'
    
    return signals


def strategy_regime_aligned_with_adr_filter(df: pd.DataFrame, 
                                           adr_window: int = 20,
                                           min_adr_pips: float = 30.0,
                                           **kwargs) -> pd.Series:
    """
    Strategy: Regime-aligned with ADR filter to avoid low-volatility days.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with 'regime' and 'range_pips' columns
    adr_window : int
        Window for ADR calculation (default 20)
    min_adr_pips : float
        Minimum ADR to trade (default 30.0 pips)
        
    Returns:
    --------
    pd.Series
        Signals based on regime and ADR filter
    """
    signals = strategy_regime_aligned(df)
    
    # Calculate ADR
    adr = calculate_adr(df, window=adr_window)
    
    # Filter out low volatility days
    signals.loc[adr < min_adr_pips] = 'flat'
    
    return signals


def strategy_regime_aligned_with_gap_filter(df: pd.DataFrame,
                                           max_gap_pips: float = 20.0,
                                           **kwargs) -> pd.Series:
    """
    Strategy: Regime-aligned with gap filter to avoid exhaustion setups.
    
    Avoids:
    - Buying after huge up days when open is at/above yesterday's high
    - Selling after huge down days when open is at/below yesterday's low
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with OHLC and 'regime' columns
    max_gap_pips : float
        Maximum gap from yesterday's close to today's open (default 20.0)
        
    Returns:
    --------
    pd.Series
        Signals based on regime and gap filter
    """
    signals = strategy_regime_aligned(df)
    
    # Calculate gap from yesterday's close to today's open
    gap = (df['Open'] - df['Close'].shift(1)).abs() * 10000  # Convert to pips
    
    # Avoid trades when gap is too large
    signals.loc[gap > max_gap_pips] = 'flat'
    
    # Additional filters: avoid exhaustion setups
    prev_high = df['High'].shift(1)
    prev_low = df['Low'].shift(1)
    prev_close = df['Close'].shift(1)
    prev_open = df['Open'].shift(1)
    
    # Avoid buying if open is at/above yesterday's high (exhaustion risk)
    exhaustion_long = (
        (signals == 'long') & 
        (df['Open'] >= prev_high) &
        (prev_close > prev_open)  # Yesterday was up day
    )
    
    # Avoid selling if open is at/below yesterday's low (exhaustion risk)
    exhaustion_short = (
        (signals == 'short') & 
        (df['Open'] <= prev_low) &
        (prev_close < prev_open)  # Yesterday was down day
    )
    
    signals.loc[exhaustion_long] = 'flat'
    signals.loc[exhaustion_short] = 'flat'
    
    return signals


def strategy_adaptive_tp_sl_from_adr(df: pd.DataFrame,
                                    adr_window: int = 20,
                                    tp_adr_multiplier: float = 0.3,
                                    sl_adr_multiplier: float = 0.3,
                                    min_adr_pips: float = 30.0,
                                    **kwargs) -> tuple:
    """
    Strategy: Regime-aligned with adaptive TP/SL based on ADR.
    
    This is a meta-strategy that modifies TP/SL based on volatility.
    Returns both signals and a function to get TP/SL for each trade.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with OHLC and 'regime' columns
    adr_window : int
        Window for ADR calculation
    tp_adr_multiplier : float
        TP = ADR * tp_adr_multiplier (default 0.3)
    sl_adr_multiplier : float
        SL = ADR * sl_adr_multiplier (default 0.3)
    min_adr_pips : float
        Minimum ADR to trade
        
    Returns:
    --------
    tuple
        (signals: pd.Series, tp_sl_func: callable)
        tp_sl_func takes (date, direction) and returns (tp_pips, sl_pips)
    """
    signals = strategy_regime_aligned_with_adr_filter(df, adr_window, min_adr_pips)
    adr = calculate_adr(df, window=adr_window)
    
    def get_tp_sl(date, direction):
        """Get TP/SL for a given date based on ADR."""
        idx = df[df['Date'] == date].index
        if len(idx) == 0:
            return 20.0, 20.0  # Default
        adr_val = adr.loc[idx[0]]
        tp = adr_val * tp_adr_multiplier
        sl = adr_val * sl_adr_multiplier
        return tp, sl
    
    return signals, get_tp_sl


def strategy_regime_aligned_directional(df: pd.DataFrame, **kwargs) -> pd.Series:
    """
    Strategy: Trade in direction of net move expectation.
    Uses regime to determine direction, but always trades (no chop filter).
    
    - Bull regime → Buy (expect up move)
    - Bear regime → Sell (expect down move)
    - Chop → Use momentum (if positive momentum, buy; if negative, sell)
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with 'regime' column
        
    Returns:
    --------
    pd.Series
        Signals based on regime and momentum
    """
    signals = pd.Series('flat', index=df.index)
    
    # Bull regime -> buy
    signals.loc[df['regime'] == 'bull'] = 'long'
    
    # Bear regime -> sell
    signals.loc[df['regime'] == 'bear'] = 'short'
    
    # For chop, use net move from open trend (simple momentum)
    chop_mask = df['regime'] == 'chop'
    if 'net_from_open_pips' in df.columns:
        # Buy if average net move is positive, sell if negative
        # Simple: use recent average of net moves
        recent_avg = df['net_from_open_pips'].rolling(window=5, min_periods=1).mean()
        signals.loc[chop_mask & (recent_avg > 0)] = 'long'
        signals.loc[chop_mask & (recent_avg < 0)] = 'short'
    else:
        # Fallback: buy in chop (neutral bias)
        signals.loc[chop_mask] = 'long'
    
    return signals


# Strategy registry for easy access
STRATEGIES = {
    'always_buy': strategy_always_buy,
    'always_sell': strategy_always_sell,
    'regime_aligned': strategy_regime_aligned,
    'regime_adr_filter': strategy_regime_aligned_with_adr_filter,
    'regime_gap_filter': strategy_regime_aligned_with_gap_filter,
    'regime_directional': strategy_regime_aligned_directional,
}

