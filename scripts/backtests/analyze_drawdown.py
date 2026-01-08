"""
Analyze drawdown metrics from backtest results.
Calculates average daily drawdown and max drawdown.
"""

import pandas as pd
import numpy as np
from datetime import timedelta
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data_loader import load_eurusd_data, add_market_open_prices
from src.backtest_dual_market import backtest_dual_market_open, analyze_dual_market_results
from src.strategies import STRATEGIES


def calculate_drawdown_metrics(equity_curve: pd.Series, trades_df: pd.DataFrame) -> dict:
    """
    Calculate detailed drawdown metrics from equity curve.
    
    Parameters:
    -----------
    equity_curve : pd.Series
        Equity curve over time
    trades_df : pd.DataFrame
        DataFrame with trade results
        
    Returns:
    --------
    dict with drawdown metrics
    """
    equity_values = equity_curve.values
    initial_equity = equity_values[0]
    
    # Calculate running maximum (peak equity)
    running_max = np.maximum.accumulate(equity_values)
    
    # Calculate drawdown (current equity - peak equity)
    drawdown = equity_values - running_max
    
    # Calculate drawdown as percentage
    drawdown_pct = (drawdown / running_max) * 100
    drawdown_pct = np.where(running_max > 0, drawdown_pct, 0)
    
    # Max drawdown (most negative value)
    max_drawdown = abs(drawdown.min()) if drawdown.min() < 0 else 0.0
    max_drawdown_pct = abs(drawdown_pct.min()) if drawdown_pct.min() < 0 else 0.0
    
    # Average daily drawdown (only negative values)
    negative_dd = drawdown[drawdown < 0]
    avg_daily_drawdown = abs(negative_dd.mean()) if len(negative_dd) > 0 else 0.0
    
    # Average daily drawdown percentage
    negative_dd_pct = drawdown_pct[drawdown_pct < 0]
    avg_daily_drawdown_pct = abs(negative_dd_pct.mean()) if len(negative_dd_pct) > 0 else 0.0
    
    # Count days in drawdown
    days_in_drawdown = (drawdown < 0).sum()
    days_in_drawdown_pct = (days_in_drawdown / len(drawdown)) * 100 if len(drawdown) > 0 else 0.0
    
    # Calculate drawdown per trade
    # Create a DataFrame with equity and drawdown
    equity_df = pd.DataFrame({
        'equity': equity_values,
        'running_max': running_max,
        'drawdown': drawdown,
        'drawdown_pct': drawdown_pct
    })
    
    # Average drawdown on losing days (days with negative equity change)
    daily_equity_change = np.diff(equity_values)
    losing_days = daily_equity_change < 0
    if losing_days.sum() > 0:
        # Drawdown on losing days (next day's drawdown after a loss)
        avg_drawdown_on_losing_days = abs(drawdown[1:][losing_days].mean()) if len(drawdown[1:][losing_days]) > 0 else 0.0
    else:
        avg_drawdown_on_losing_days = 0.0
    
    return {
        'max_drawdown': max_drawdown,
        'max_drawdown_pct': max_drawdown_pct,
        'avg_daily_drawdown': avg_daily_drawdown,
        'avg_daily_drawdown_pct': avg_daily_drawdown_pct,
        'days_in_drawdown': days_in_drawdown,
        'days_in_drawdown_pct': days_in_drawdown_pct,
        'avg_drawdown_on_losing_days': avg_drawdown_on_losing_days,
        'initial_equity': initial_equity,
        'final_equity': equity_values[-1],
        'total_return_pct': ((equity_values[-1] - initial_equity) / initial_equity) * 100,
    }


def analyze_backtest_drawdown():
    """Run backtest and analyze drawdown metrics."""
    print("=" * 80)
    print("BACKTEST DRAWDOWN ANALYSIS")
    print("=" * 80)
    
    # Load data
    data_file = project_root / "data" / "eur_usd_long_term.csv"
    print(f"\nLoading data from: {data_file}")
    
    df = load_eurusd_data(str(data_file))
    
    # Filter to last 12 months
    end_date = df['Date'].max()
    start_date = end_date - timedelta(days=365)
    df_12month = df[df['Date'] >= start_date].copy()
    df_12month = df_12month.reset_index(drop=True)
    
    print(f"12-Month Period: {df_12month['Date'].min()} to {df_12month['Date'].max()}")
    print(f"Trading days: {len(df_12month)}")
    
    # Parameters
    tp_pips = 10.0
    cost_per_trade = 2.0
    
    # Prepare data
    print("\nPreparing data with market open prices...")
    df_with_opens = add_market_open_prices(df_12month.copy())
    
    # Generate signals
    dual_signals_df = STRATEGIES['dual_market_open'](df_with_opens)
    
    # Run backtest
    print("\nRunning backtest...")
    result = backtest_dual_market_open(
        df_with_opens,
        dual_signals_df,
        take_profit_pips=tp_pips,
        cost_per_trade_pips=cost_per_trade,
    )
    
    # Get standard stats
    stats = analyze_dual_market_results(result)
    
    # Calculate detailed drawdown metrics
    print("\nCalculating drawdown metrics...")
    dd_metrics = calculate_drawdown_metrics(result.equity_curve, result.trades)
    
    # Print results
    print("\n" + "=" * 80)
    print("DRAWDOWN METRICS")
    print("=" * 80)
    
    print(f"\nEquity Metrics:")
    print(f"  Initial Equity: ${dd_metrics['initial_equity']:,.2f}")
    print(f"  Final Equity: ${dd_metrics['final_equity']:,.2f}")
    print(f"  Total Return: {dd_metrics['total_return_pct']:.2f}%")
    
    print(f"\nMax Drawdown (Full Backtest):")
    print(f"  Max Drawdown: {dd_metrics['max_drawdown']:.2f} pips")
    print(f"  Max Drawdown: {dd_metrics['max_drawdown_pct']:.2f}%")
    
    print(f"\nAverage Daily Drawdown:")
    print(f"  Avg Daily Drawdown: {dd_metrics['avg_daily_drawdown']:.2f} pips")
    print(f"  Avg Daily Drawdown: {dd_metrics['avg_daily_drawdown_pct']:.4f}%")
    
    print(f"\nDrawdown Statistics:")
    print(f"  Days in Drawdown: {dd_metrics['days_in_drawdown']} days ({dd_metrics['days_in_drawdown_pct']:.2f}% of trading days)")
    print(f"  Avg Drawdown on Losing Days: {dd_metrics['avg_drawdown_on_losing_days']:.2f} pips")
    
    print(f"\nTrade Statistics (for reference):")
    print(f"  Total Trades: {stats['total_trades']}")
    print(f"  Total Pips: {stats['total_pips']:.2f}")
    print(f"  Win Rate: {stats['win_rate']:.2f}%")
    print(f"  Avg Pips/Trade: {stats['avg_pips_per_trade']:.2f}")
    
    # Calculate drawdown per trade (approximate)
    # Drawdown is measured from equity, but we can relate it to trades
    avg_loss_pips = stats.get('avg_loss', 0)
    if avg_loss_pips < 0:
        print(f"\nLoss Metrics:")
        print(f"  Avg Loss per Trade: {avg_loss_pips:.2f} pips")
        print(f"  (Note: Daily drawdown may be lower than avg loss due to winning trades)")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nMaximum Drawdown (Full Backtest): {dd_metrics['max_drawdown']:.2f} pips ({dd_metrics['max_drawdown_pct']:.2f}%)")
    print(f"Average Daily Drawdown: {dd_metrics['avg_daily_drawdown']:.2f} pips ({dd_metrics['avg_daily_drawdown_pct']:.4f}%)")
    print(f"Days in Drawdown: {dd_metrics['days_in_drawdown']} out of {len(result.equity_curve)} trading days ({dd_metrics['days_in_drawdown_pct']:.2f}%)")
    
    return dd_metrics, stats


if __name__ == "__main__":
    dd_metrics, stats = analyze_backtest_drawdown()



