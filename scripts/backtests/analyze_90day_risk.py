"""
90-Day Risk Analysis: Drawdown and Adverse Pips

This script analyzes the last 90 days to calculate:
- Max drawdown
- Average pips that go against open trades
- Max and average pips per day that go against open trades
- Required account size for micro account to avoid blowing out
"""

import pandas as pd
import numpy as np
from datetime import timedelta
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data_loader import load_eurusd_data, add_market_open_prices, price_to_pips, pips_to_price
from src.backtest_dual_market import backtest_dual_market_open, analyze_dual_market_results
from src.strategies import STRATEGIES


def calculate_adverse_pips(df: pd.DataFrame, trades_df: pd.DataFrame) -> dict:
    """
    Calculate adverse pips (pips that go against open trades).
    
    For each trade, track the maximum adverse move while the trade is open:
    - Long trades: max(entry_price - low_price_during_trade)
    - Short trades: max(high_price_during_trade - entry_price)
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with Date, Open, High, Low, Close columns
    trades_df : pd.DataFrame
        DataFrame with trade results (date, direction, entry_price, exit_price, etc.)
        
    Returns:
    --------
    dict with adverse pip metrics
    """
    if len(trades_df) == 0:
        return {
            'max_adverse_pips': 0.0,
            'avg_adverse_pips': 0.0,
            'max_adverse_pips_per_day': 0.0,
            'avg_adverse_pips_per_day': 0.0,
            'adverse_pips_by_trade': [],
        }
    
    adverse_pips_by_trade = []
    adverse_pips_per_day = []
    
    # Create date index for quick lookup
    df_indexed = df.set_index('Date')
    
    for _, trade in trades_df.iterrows():
        entry_date = pd.Timestamp(trade['date'])
        entry_price = trade['entry_price']
        direction = trade['direction']
        exit_date = entry_date  # For daily data, trades close same day
        
        # Find the row in df for this trade
        trade_row = df[df['Date'] == entry_date]
        if len(trade_row) == 0:
            continue
        
        trade_row = trade_row.iloc[0]
        
        # Calculate adverse pips
        if direction == 'long':
            # For long: adverse move is when price goes below entry
            # Maximum adverse = entry_price - lowest_price_during_trade
            lowest_price = trade_row['Low']
            adverse_pips = price_to_pips(entry_price - lowest_price) if entry_price > lowest_price else 0.0
        else:  # short
            # For short: adverse move is when price goes above entry
            # Maximum adverse = highest_price_during_trade - entry_price
            highest_price = trade_row['High']
            adverse_pips = price_to_pips(highest_price - entry_price) if highest_price > entry_price else 0.0
        
        adverse_pips_by_trade.append({
            'date': entry_date,
            'direction': direction,
            'adverse_pips': adverse_pips,
        })
        
        # For daily data, adverse pips per day = adverse pips (since trade is open for 1 day)
        adverse_pips_per_day.append(adverse_pips)
    
    adverse_df = pd.DataFrame(adverse_pips_by_trade)
    
    if len(adverse_df) == 0:
        return {
            'max_adverse_pips': 0.0,
            'avg_adverse_pips': 0.0,
            'max_adverse_pips_per_day': 0.0,
            'avg_adverse_pips_per_day': 0.0,
            'adverse_pips_by_trade': [],
        }
    
    max_adverse_pips = adverse_df['adverse_pips'].max()
    avg_adverse_pips = adverse_df['adverse_pips'].mean()
    max_adverse_pips_per_day = max(adverse_pips_per_day) if adverse_pips_per_day else 0.0
    avg_adverse_pips_per_day = np.mean(adverse_pips_per_day) if adverse_pips_per_day else 0.0
    
    return {
        'max_adverse_pips': max_adverse_pips,
        'avg_adverse_pips': avg_adverse_pips,
        'max_adverse_pips_per_day': max_adverse_pips_per_day,
        'avg_adverse_pips_per_day': avg_adverse_pips_per_day,
        'adverse_pips_by_trade': adverse_pips_by_trade,
    }


def calculate_drawdown_90day(equity_curve: pd.Series) -> dict:
    """
    Calculate drawdown metrics for 90-day period.
    
    Parameters:
    -----------
    equity_curve : pd.Series
        Equity curve over time
        
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
    
    # Convert drawdown from dollars to pips
    # Backtest uses mini lot (1,000 units) where 1 pip = $10
    # So drawdown in pips = drawdown in dollars / $10 per pip
    max_drawdown_pips = max_drawdown / 10.0  # $10 per pip per mini lot
    
    return {
        'max_drawdown_dollars': max_drawdown,
        'max_drawdown_pips': max_drawdown_pips,
        'max_drawdown_pct': max_drawdown_pct,
        'initial_equity': initial_equity,
        'final_equity': equity_values[-1],
    }


def calculate_required_account_size(adverse_metrics: dict, drawdown_metrics: dict, micro_lot_size: int = 1000) -> dict:
    """
    Calculate required account size for micro account to avoid blowing out.
    
    For micro account:
    - 1 micro lot = 1,000 units
    - 1 pip = $0.10 per micro lot for EUR/USD
    
    Parameters:
    -----------
    adverse_metrics : dict
        Metrics from calculate_adverse_pips
    drawdown_metrics : dict
        Metrics from calculate_drawdown_90day
    micro_lot_size : int
        Units per micro lot (default: 1000)
        
    Returns:
    --------
    dict with required account size calculations
    """
    # Cost per pip for micro lot
    cost_per_pip_micro = 0.10  # $0.10 per pip per micro lot
    
    # Maximum adverse pips (worst case while trade is open)
    max_adverse_pips = adverse_metrics['max_adverse_pips']
    max_adverse_loss = max_adverse_pips * cost_per_pip_micro
    
    # Max drawdown in pips (worst case equity drawdown)
    max_drawdown_pips = drawdown_metrics['max_drawdown_pips']
    max_drawdown_loss = max_drawdown_pips * cost_per_pip_micro
    
    # Use the larger of the two as worst case
    worst_case_pips = max(max_adverse_pips, max_drawdown_pips)
    worst_case_loss = worst_case_pips * cost_per_pip_micro
    
    # Required account size = worst case loss (to avoid blowing out)
    # This is the minimum needed, but we'll show it clearly
    required_account_size = worst_case_loss
    
    return {
        'max_adverse_loss_micro': max_adverse_loss,
        'max_drawdown_loss_micro': max_drawdown_loss,
        'worst_case_pips': worst_case_pips,
        'worst_case_loss_micro': worst_case_loss,
        'required_account_size_micro': required_account_size,
        'cost_per_pip_micro': cost_per_pip_micro,
    }


def analyze_90day_risk():
    """Run 90-day risk analysis."""
    print("=" * 80)
    print("90-DAY RISK ANALYSIS")
    print("=" * 80)
    
    # Load data
    data_file = project_root / "data" / "eur_usd_long_term.csv"
    print(f"\nLoading data from: {data_file}")
    
    df = load_eurusd_data(str(data_file))
    
    # Filter to last 90 days
    end_date = df['Date'].max()
    start_date = end_date - timedelta(days=90)
    
    df_90day = df[df['Date'] >= start_date].copy()
    df_90day = df_90day.reset_index(drop=True)
    
    print(f"\n90-Day Period: {df_90day['Date'].min()} to {df_90day['Date'].max()}")
    print(f"Trading days: {len(df_90day)}")
    
    # Parameters matching live trading (10 pips TP, no SL, EOD exit)
    tp_pips = 10.0
    cost_per_trade = 2.0
    
    # Prepare data with market open prices
    print("\nPreparing data with market open prices...")
    df_with_opens = add_market_open_prices(df_90day.copy())
    
    # Generate signals
    print("Generating signals...")
    dual_signals_df = STRATEGIES['dual_market_open'](df_with_opens)
    
    # Run backtest
    print("Running backtest...")
    result = backtest_dual_market_open(
        df_with_opens,
        dual_signals_df,
        take_profit_pips=tp_pips,
        cost_per_trade_pips=cost_per_trade,
    )
    
    # Get standard stats
    stats = analyze_dual_market_results(result)
    
    # Calculate drawdown metrics
    print("\nCalculating drawdown metrics...")
    dd_metrics = calculate_drawdown_90day(result.equity_curve)
    
    # Calculate adverse pips
    print("Calculating adverse pips...")
    adverse_metrics = calculate_adverse_pips(df_with_opens, result.trades)
    
    # Calculate required account size
    print("Calculating required account size...")
    account_metrics = calculate_required_account_size(adverse_metrics, dd_metrics)
    
    # Print results
    print("\n" + "=" * 80)
    print("90-DAY RISK ANALYSIS RESULTS")
    print("=" * 80)
    
    print(f"\nPeriod: {df_90day['Date'].min().strftime('%Y-%m-%d')} to {df_90day['Date'].max().strftime('%Y-%m-%d')}")
    print(f"Trading days: {len(df_90day)}")
    print(f"Total trades: {stats['total_trades']}")
    
    print(f"\n" + "-" * 80)
    print("MAX DRAWDOWN (Last 90 Days)")
    print("-" * 80)
    print(f"Max Drawdown: {dd_metrics['max_drawdown_pips']:.2f} pips")
    print(f"Max Drawdown: ${dd_metrics['max_drawdown_dollars']:.2f} (mini lot basis)")
    print(f"Max Drawdown: {dd_metrics['max_drawdown_pct']:.2f}%")
    
    print(f"\n" + "-" * 80)
    print("ADVERSE PIPS (Pips Against Open Trades)")
    print("-" * 80)
    print(f"Max Adverse Pips (single trade): {adverse_metrics['max_adverse_pips']:.2f} pips")
    print(f"Average Adverse Pips (per trade): {adverse_metrics['avg_adverse_pips']:.2f} pips")
    print(f"Max Adverse Pips Per Day: {adverse_metrics['max_adverse_pips_per_day']:.2f} pips")
    print(f"Average Adverse Pips Per Day: {adverse_metrics['avg_adverse_pips_per_day']:.2f} pips")
    
    print(f"\n" + "-" * 80)
    print("REQUIRED ACCOUNT SIZE (Micro Account)")
    print("-" * 80)
    print(f"Micro Lot Size: 1,000 units")
    print(f"Cost Per Pip (micro lot): ${account_metrics['cost_per_pip_micro']:.2f}")
    print(f"\nMax Adverse Loss (micro lot): ${account_metrics['max_adverse_loss_micro']:.2f}")
    print(f"Max Drawdown Loss (micro lot): ${account_metrics['max_drawdown_loss_micro']:.2f}")
    print(f"\nWorst Case (max of above): {account_metrics['worst_case_pips']:.2f} pips")
    print(f"Worst Case Loss: ${account_metrics['worst_case_loss_micro']:.2f}")
    print(f"\n{'='*80}")
    print(f"REQUIRED ACCOUNT SIZE: ${account_metrics['required_account_size_micro']:.2f}")
    print(f"{'='*80}")
    print(f"\nNote: This is the minimum account size needed to cover the worst case")
    print(f"      scenario in the last 90 days. This does not include best practices")
    print(f"      for position sizing or risk management.")
    
    print(f"\n" + "-" * 80)
    print("TRADE STATISTICS (Reference)")
    print("-" * 80)
    print(f"Total Pips: {stats['total_pips']:.2f}")
    print(f"Win Rate: {stats['win_rate']:.2f}%")
    print(f"Avg Pips/Trade: {stats['avg_pips_per_trade']:.2f}")
    print(f"EUR Trades: {stats['eur_trades']}")
    print(f"US Trades: {stats['us_trades']}")
    
    return {
        'drawdown_metrics': dd_metrics,
        'adverse_metrics': adverse_metrics,
        'account_metrics': account_metrics,
        'stats': stats,
    }


if __name__ == "__main__":
    results = analyze_90day_risk()
