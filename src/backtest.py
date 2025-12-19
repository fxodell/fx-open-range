"""
Backtesting engine for trade-at-open strategies.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Literal
from .data_loader import price_to_pips, pips_to_price


TradeSignal = Literal['long', 'short', 'flat']


class BacktestResult:
    """Container for backtest results."""
    
    def __init__(self, trades: pd.DataFrame, equity_curve: pd.Series):
        self.trades = trades
        self.equity_curve = equity_curve
    
    def get_summary_stats(self) -> Dict:
        """Calculate comprehensive performance statistics."""
        trades = self.trades
        
        if len(trades) == 0:
            # Drawdown calculation even with no trades
            equity = self.equity_curve.values
            running_max = np.maximum.accumulate(equity)
            drawdown = equity - running_max
            max_drawdown_pips = abs(drawdown.min()) if len(drawdown) > 0 and drawdown.min() < 0 else 0.0
            max_drawdown_pct = (max_drawdown_pips / running_max[np.argmin(drawdown)]) * 100 if len(drawdown) > 0 and drawdown.min() < 0 and running_max[np.argmin(drawdown)] > 0 else 0.0
            
            return {
                'total_trades': 0,
                'long_trades': 0,
                'short_trades': 0,
                'total_pips': 0.0,
                'avg_pips_per_trade': 0.0,
                'avg_pips_per_day': 0.0,
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0,
                'max_drawdown_pips': max_drawdown_pips,
                'max_drawdown_pct': max_drawdown_pct,
                'sharpe': 0.0,
                'sharpe_annualized': 0.0,
            }
        
        total_pips = trades['pips'].sum()
        avg_pips_per_trade = trades['pips'].mean()
        win_rate = (trades['pips'] > 0).sum() / len(trades) * 100
        
        winning_trades = trades[trades['pips'] > 0]
        losing_trades = trades[trades['pips'] <= 0]
        
        avg_win = winning_trades['pips'].mean() if len(winning_trades) > 0 else 0.0
        avg_loss = losing_trades['pips'].mean() if len(losing_trades) > 0 else 0.0
        profit_factor = abs(winning_trades['pips'].sum() / losing_trades['pips'].sum()) if len(losing_trades) > 0 and losing_trades['pips'].sum() != 0 else np.inf
        
        # Drawdown calculation
        equity = self.equity_curve.values
        running_max = np.maximum.accumulate(equity)
        drawdown = equity - running_max
        max_drawdown_pips = abs(drawdown.min())
        max_drawdown_pct = (max_drawdown_pips / running_max[np.argmin(drawdown)]) * 100 if running_max[np.argmin(drawdown)] > 0 else 0
        
        # Sharpe-like metric (mean / std * sqrt(n))
        if len(trades) > 1:
            sharpe = (avg_pips_per_trade / trades['pips'].std()) * np.sqrt(len(trades)) if trades['pips'].std() > 0 else 0.0
        else:
            sharpe = 0.0
        
        # Annualized Sharpe (approximate, assuming ~252 trading days per year)
        trades_per_year = len(trades) / (len(self.equity_curve) / 252) if len(self.equity_curve) > 0 else 0
        sharpe_annualized = sharpe * np.sqrt(252 / len(self.equity_curve)) if len(self.equity_curve) > 0 else 0.0
        
        long_trades = trades[trades['direction'] == 'long']
        short_trades = trades[trades['direction'] == 'short']
        
        return {
            'total_trades': len(trades),
            'long_trades': len(long_trades),
            'short_trades': len(short_trades),
            'total_pips': total_pips,
            'avg_pips_per_trade': avg_pips_per_trade,
            'avg_pips_per_day': total_pips / len(self.equity_curve) if len(self.equity_curve) > 0 else 0.0,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_drawdown_pips': max_drawdown_pips,
            'max_drawdown_pct': max_drawdown_pct,
            'sharpe': sharpe,
            'sharpe_annualized': sharpe_annualized,
        }
    
    def print_summary(self):
        """Print formatted summary statistics."""
        stats = self.get_summary_stats()
        
        print("=" * 60)
        print("BACKTEST SUMMARY")
        print("=" * 60)
        print(f"Total Trades:        {stats['total_trades']} ({stats['long_trades']} long, {stats['short_trades']} short)")
        print(f"Total Pips:          {stats['total_pips']:.2f}")
        print(f"Avg Pips/Trade:      {stats['avg_pips_per_trade']:.2f}")
        print(f"Avg Pips/Day:        {stats['avg_pips_per_day']:.2f}")
        print(f"Win Rate:            {stats['win_rate']:.2f}%")
        print(f"Avg Win:             {stats['avg_win']:.2f} pips")
        print(f"Avg Loss:            {stats['avg_loss']:.2f} pips")
        print(f"Profit Factor:       {stats['profit_factor']:.2f}")
        print(f"Max Drawdown:        {stats['max_drawdown_pips']:.2f} pips ({stats['max_drawdown_pct']:.2f}%)")
        print(f"Sharpe (pips):       {stats['sharpe']:.2f}")
        print(f"Sharpe (annualized): {stats['sharpe_annualized']:.2f}")
        print("=" * 60)


def backtest_strategy(df: pd.DataFrame,
                     signals: pd.Series,  # 'long', 'short', or 'flat' for each day
                     take_profit_pips: float,
                     stop_loss_pips: float,
                     cost_per_trade_pips: float = 2.0,
                     initial_equity: float = 10000.0) -> BacktestResult:
    """
    Backtest a strategy that trades at the open.
    
    Assumptions:
    - Trade enters at the Open price
    - If both TP and SL can be hit in the same day, we conservatively assume SL is hit first
    - Positions are closed at end of day if TP/SL not hit (close at Close price)
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with OHLC data and any necessary indicators
    signals : pd.Series
        Trading signals: 'long', 'short', or 'flat' (index must match df)
    take_profit_pips : float
        Take profit in pips
    stop_loss_pips : float
        Stop loss in pips
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
        
        # Calculate TP and SL prices
        if signal == 'long':
            tp_price = open_price + pips_to_price(take_profit_pips)
            sl_price = open_price - pips_to_price(stop_loss_pips)
        else:  # short
            tp_price = open_price - pips_to_price(take_profit_pips)
            sl_price = open_price + pips_to_price(stop_loss_pips)
        
        # Check if TP or SL was hit (conservative: check SL first if both possible)
        pips_result = None
        
        # Conservative assumption: if both could be hit, SL wins
        if signal == 'long':
            # Check if SL hit before TP
            if row['Low'] <= sl_price:
                # SL hit
                pips_result = -stop_loss_pips - cost_per_trade_pips
            elif row['High'] >= tp_price:
                # TP hit
                pips_result = take_profit_pips - cost_per_trade_pips
            else:
                # Close at end of day
                close_price = row['Close']
                pips_result = price_to_pips(close_price - open_price) - cost_per_trade_pips
        else:  # short
            # Check if SL hit before TP
            if row['High'] >= sl_price:
                # SL hit
                pips_result = -stop_loss_pips - cost_per_trade_pips
            elif row['Low'] <= tp_price:
                # TP hit
                pips_result = take_profit_pips - cost_per_trade_pips
            else:
                # Close at end of day
                close_price = row['Close']
                pips_result = price_to_pips(open_price - close_price) - cost_per_trade_pips
        
        # Record trade
        trades.append({
            'date': row['Date'],
            'direction': signal,
            'entry_price': open_price,
            'exit_price': row['Close'],  # Approximate, actual depends on TP/SL
            'pips': pips_result,
        })
        
        # Update equity (simple: assume 1 lot = 1 pip = $10 for mini lot)
        # For simplicity, we'll track in "pip units" and assume constant position size
        current_equity += pips_result * 10  # $10 per pip per mini lot
        
        equity_curve.append(current_equity)
    
    trades_df = pd.DataFrame(trades)
    equity_series = pd.Series(equity_curve, index=df.index)
    
    return BacktestResult(trades_df, equity_series)

