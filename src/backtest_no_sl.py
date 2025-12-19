"""
Backtesting engine for strategies with TP only (no stop loss, exit at EOD).
"""

import pandas as pd
import numpy as np
from typing import Dict
from .data_loader import price_to_pips, pips_to_price
from .backtest import BacktestResult


def backtest_strategy_no_sl(df: pd.DataFrame,
                            signals: pd.Series,  # 'long', 'short', or 'flat' for each day
                            take_profit_pips: float,
                            cost_per_trade_pips: float = 2.0,
                            initial_equity: float = 10000.0) -> BacktestResult:
    """
    Backtest a strategy that trades at the open with TP only (no stop loss).
    
    Logic:
    - Trade enters at the Open price
    - If TP is hit during the day, exit with profit
    - If TP is NOT hit, close at end of day at Close price (even if losing)
    - No stop loss - always holds until EOD if TP not hit
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with OHLC data and any necessary indicators
    signals : pd.Series
        Trading signals: 'long', 'short', or 'flat' (index must match df)
    take_profit_pips : float
        Take profit in pips
    cost_per_trade_pips : float
        Transaction cost per trade in pips (default 2.0 = spread + commission)
    initial_equity : float
        Initial equity (default 10000.0)
        
    Returns:
    --------
    BacktestResult
        BacktestResult object with trades and equity curve
    """
    # Ensure signals are aligned with df
    signals = signals.reindex(df.index)
    
    trades = []
    equity_curve = []
    current_equity = initial_equity
    
    for i in df.index:
        if i == 0:
            equity_curve.append(current_equity)
            continue
        
        signal = signals.loc[i]
        
        # Skip if no signal
        if signal not in ['long', 'short']:
            equity_curve.append(current_equity)
            continue
        
        row = df.loc[i]
        open_price = row['Open']
        close_price = row['Close']
        
        # Calculate TP price
        if signal == 'long':
            tp_price = open_price + pips_to_price(take_profit_pips)
            
            # Check if TP was hit during the day
            if row['High'] >= tp_price:
                # TP hit - exit with profit
                pips_result = take_profit_pips - cost_per_trade_pips
                exit_price = tp_price
                exit_reason = 'TP'
            else:
                # TP not hit - close at end of day
                pips_result = price_to_pips(close_price - open_price) - cost_per_trade_pips
                exit_price = close_price
                exit_reason = 'EOD'
                
        else:  # short
            tp_price = open_price - pips_to_price(take_profit_pips)
            
            # Check if TP was hit during the day
            if row['Low'] <= tp_price:
                # TP hit - exit with profit
                pips_result = take_profit_pips - cost_per_trade_pips
                exit_price = tp_price
                exit_reason = 'TP'
            else:
                # TP not hit - close at end of day
                pips_result = price_to_pips(open_price - close_price) - cost_per_trade_pips
                exit_price = close_price
                exit_reason = 'EOD'
        
        # Record trade
        trades.append({
            'date': row['Date'],
            'direction': signal,
            'entry_price': open_price,
            'exit_price': exit_price,
            'exit_reason': exit_reason,
            'pips': pips_result,
            'tp_hit': (exit_reason == 'TP'),
        })
        
        # Update equity (simple: assume 1 lot = 1 pip = $10 for mini lot)
        current_equity += pips_result * 10  # $10 per pip per mini lot
        
        equity_curve.append(current_equity)
    
    trades_df = pd.DataFrame(trades)
    equity_series = pd.Series(equity_curve, index=df.index)
    
    return BacktestResult(trades_df, equity_series)

