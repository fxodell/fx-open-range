"""
Backtesting engine for dual market open strategies.

This module provides backtesting functionality for strategies that trade
at both EUR market open (8:00 UTC) and US market open (13:00 UTC).
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from .data_loader import price_to_pips, pips_to_price
from .backtest import BacktestResult
from .market_sessions import get_eur_open_time, get_us_open_time


def backtest_dual_market_open(df: pd.DataFrame,
                             signals_df: pd.DataFrame,  # DataFrame with eur_signal, us_signal, eur_open_price, us_open_price
                             take_profit_pips: float,
                             cost_per_trade_pips: float = 2.0,
                             initial_equity: float = 10000.0) -> BacktestResult:
    """
    Backtest a dual market open strategy.
    
    Logic:
    - Check EUR market open (8:00 UTC) for signal
    - If signal exists and no open position → Enter trade at EUR open price
    - Monitor if TP hit before US open
    - At US market open (13:00 UTC):
      - If EUR trade still open → Skip US trade
      - If no open position → Check signal and enter if valid
    - Close any open positions at EOD (daily close) if TP not hit
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with Date, Open, High, Low, Close columns
    signals_df : pd.DataFrame
        DataFrame with columns:
        - 'eur_signal': Signal for EUR open ('long', 'short', 'flat')
        - 'us_signal': Signal for US open ('long', 'short', 'flat')
        - 'eur_open_price': EUR market open price
        - 'us_open_price': US market open price
    take_profit_pips : float
        Take profit in pips
    cost_per_trade_pips : float
        Transaction cost per trade in pips (default 2.0)
    initial_equity : float
        Initial equity (default 10000.0)
        
    Returns:
    --------
    BacktestResult
        BacktestResult object with trades and equity curve
    """
    # Ensure signals are aligned with df
    signals_df = signals_df.reindex(df.index)
    
    trades = []
    equity_curve = []
    current_equity = initial_equity
    
    # Track open position
    open_position = None  # {'direction': 'long'/'short', 'entry_price': float, 'entry_time': 'eur'/'us', 'entry_date': date}
    
    for i in df.index:
        if i == 0:
            equity_curve.append(current_equity)
            continue
        
        row = df.loc[i]
        date = pd.Timestamp(row['Date'])
        signal_row = signals_df.loc[i]
        
        # Check EUR market open (8:00 UTC)
        eur_signal = signal_row['eur_signal']
        eur_open_price = signal_row['eur_open_price']
        
        # Check US market open (13:00 UTC)
        us_signal = signal_row['us_signal']
        us_open_price = signal_row['us_open_price']
        
        # Process EUR market open trade
        if eur_signal in ['long', 'short'] and eur_open_price is not None and pd.notna(eur_open_price):
            if open_position is None:
                # Enter trade at EUR open
                open_position = {
                    'direction': eur_signal,
                    'entry_price': eur_open_price,
                    'entry_time': 'eur',
                    'entry_date': date,
                    'entry_index': i
                }
        
        # Check if EUR trade hit TP before US open
        # We approximate this by checking if TP would have been hit by mid-day
        # (between EUR open and US open)
        if open_position is not None and open_position['entry_time'] == 'eur':
            # Check if TP was hit during the day (before or at US open)
            # We use the daily High/Low to approximate
            tp_hit = False
            if open_position['direction'] == 'long':
                tp_price = open_position['entry_price'] + pips_to_price(take_profit_pips)
                if row['High'] >= tp_price:
                    tp_hit = True
            else:  # short
                tp_price = open_position['entry_price'] - pips_to_price(take_profit_pips)
                if row['Low'] <= tp_price:
                    tp_hit = True
            
            if tp_hit:
                # TP hit - close EUR trade
                if open_position['direction'] == 'long':
                    pips_result = take_profit_pips - cost_per_trade_pips
                    exit_price = open_position['entry_price'] + pips_to_price(take_profit_pips)
                else:  # short
                    pips_result = take_profit_pips - cost_per_trade_pips
                    exit_price = open_position['entry_price'] - pips_to_price(take_profit_pips)
                
                trades.append({
                    'date': open_position['entry_date'],
                    'direction': open_position['direction'],
                    'entry_price': open_position['entry_price'],
                    'exit_price': exit_price,
                    'exit_reason': 'TP',
                    'session': open_position['entry_time'].upper(),
                    'pips': pips_result,
                    'tp_hit': True,
                })
                
                current_equity += pips_result * 10  # $10 per pip per mini lot
                open_position = None
        
        # Process US market open trade (only if no open position)
        if open_position is None and us_signal in ['long', 'short'] and us_open_price is not None and pd.notna(us_open_price):
            # Enter trade at US open
            open_position = {
                'direction': us_signal,
                'entry_price': us_open_price,
                'entry_time': 'us',
                'entry_date': date,
                'entry_index': i
            }
        
        # Check if US trade hit TP during the day
        if open_position is not None and open_position['entry_time'] == 'us':
            tp_hit = False
            if open_position['direction'] == 'long':
                tp_price = open_position['entry_price'] + pips_to_price(take_profit_pips)
                if row['High'] >= tp_price:
                    tp_hit = True
            else:  # short
                tp_price = open_position['entry_price'] - pips_to_price(take_profit_pips)
                if row['Low'] <= tp_price:
                    tp_hit = True
            
            if tp_hit:
                # TP hit - close US trade
                if open_position['direction'] == 'long':
                    pips_result = take_profit_pips - cost_per_trade_pips
                    exit_price = open_position['entry_price'] + pips_to_price(take_profit_pips)
                else:  # short
                    pips_result = take_profit_pips - cost_per_trade_pips
                    exit_price = open_position['entry_price'] - pips_to_price(take_profit_pips)
                
                trades.append({
                    'date': open_position['entry_date'],
                    'direction': open_position['direction'],
                    'entry_price': open_position['entry_price'],
                    'exit_price': exit_price,
                    'exit_reason': 'TP',
                    'session': open_position['entry_time'].upper(),
                    'pips': pips_result,
                    'tp_hit': True,
                })
                
                current_equity += pips_result * 10
                open_position = None
        
        # Close any open positions at end of day (EOD exit)
        if open_position is not None:
            # Check if this is the end of the trading day
            # For daily data, we close at the daily close
            close_price = row['Close']
            
            if open_position['direction'] == 'long':
                pips_result = price_to_pips(close_price - open_position['entry_price']) - cost_per_trade_pips
            else:  # short
                pips_result = price_to_pips(open_position['entry_price'] - close_price) - cost_per_trade_pips
            
            trades.append({
                'date': open_position['entry_date'],
                'direction': open_position['direction'],
                'entry_price': open_position['entry_price'],
                'exit_price': close_price,
                'exit_reason': 'EOD',
                'session': open_position['entry_time'].upper(),
                'pips': pips_result,
                'tp_hit': False,
            })
            
            current_equity += pips_result * 10
            open_position = None
        
        equity_curve.append(current_equity)
    
    # Close any remaining open position at the end
    if open_position is not None:
        last_row = df.iloc[-1]
        close_price = last_row['Close']
        
        if open_position['direction'] == 'long':
            pips_result = price_to_pips(close_price - open_position['entry_price']) - cost_per_trade_pips
        else:  # short
            pips_result = price_to_pips(open_position['entry_price'] - close_price) - cost_per_trade_pips
        
        trades.append({
            'date': open_position['entry_date'],
            'direction': open_position['direction'],
            'entry_price': open_position['entry_price'],
            'exit_price': close_price,
            'exit_reason': 'EOD',
            'session': open_position['entry_time'].upper(),
            'pips': pips_result,
            'tp_hit': False,
        })
        
        current_equity += pips_result * 10
        equity_curve[-1] = current_equity
    
    trades_df = pd.DataFrame(trades)
    equity_series = pd.Series(equity_curve, index=df.index)
    
    return BacktestResult(trades_df, equity_series)


def analyze_dual_market_results(result: BacktestResult) -> Dict:
    """
    Analyze dual market open backtest results with session-specific metrics.
    
    Parameters:
    -----------
    result : BacktestResult
        Backtest result from backtest_dual_market_open
        
    Returns:
    --------
    Dict
        Dictionary with comprehensive metrics including session breakdown
    """
    stats = result.get_summary_stats()
    trades = result.trades
    
    if len(trades) == 0:
        return {
            **stats,
            'eur_trades': 0,
            'us_trades': 0,
            'eur_pips': 0.0,
            'us_pips': 0.0,
            'eur_win_rate': 0.0,
            'us_win_rate': 0.0,
            'days_with_2_trades': 0,
            'days_with_1_trade': 0,
            'days_with_0_trades': 0,
        }
    
    # Session-specific analysis
    eur_trades = trades[trades['session'] == 'EUR']
    us_trades = trades[trades['session'] == 'US']
    
    eur_pips = eur_trades['pips'].sum() if len(eur_trades) > 0 else 0.0
    us_pips = us_trades['pips'].sum() if len(us_trades) > 0 else 0.0
    
    eur_win_rate = (eur_trades['pips'] > 0).sum() / len(eur_trades) * 100 if len(eur_trades) > 0 else 0.0
    us_win_rate = (us_trades['pips'] > 0).sum() / len(us_trades) * 100 if len(us_trades) > 0 else 0.0
    
    # Count trades per day
    trades_by_date = trades.groupby('date').size()
    days_with_2_trades = (trades_by_date >= 2).sum()
    days_with_1_trade = (trades_by_date == 1).sum()
    days_with_0_trades = len(result.equity_curve) - len(trades_by_date)
    
    return {
        **stats,
        'eur_trades': len(eur_trades),
        'us_trades': len(us_trades),
        'eur_pips': eur_pips,
        'us_pips': us_pips,
        'eur_win_rate': eur_win_rate,
        'us_win_rate': us_win_rate,
        'days_with_2_trades': days_with_2_trades,
        'days_with_1_trade': days_with_1_trade,
        'days_with_0_trades': days_with_0_trades,
    }

