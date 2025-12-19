"""
Calculate daily drawdown for directional strategies.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from src.data_loader import load_eurusd_data
from src.core_analysis import calculate_daily_metrics
from src.regime import calculate_moving_averages, calculate_momentum, classify_regime
from src.backtest_no_sl import backtest_strategy_no_sl


def strategy_price_trend_directional(df: pd.DataFrame) -> pd.Series:
    """Buy when price above SMA20, sell when below."""
    signals = pd.Series('flat', index=df.index)
    if 'SMA20' in df.columns:
        signals.loc[df['Close'].shift(1) > df['SMA20']] = 'long'
        signals.loc[df['Close'].shift(1) < df['SMA20']] = 'short'
    return signals


def calculate_daily_drawdown():
    """Calculate drawdown for each day."""
    
    print("=" * 100)
    print("DRAWDOWN ANALYSIS - DIRECTIONAL STRATEGIES")
    print("=" * 100)
    
    # Load and prepare data
    data_file = project_root / "data" / "eur_usd.csv"
    df = load_eurusd_data(str(data_file))
    df = calculate_daily_metrics(df)
    df = calculate_moving_averages(df, periods=[20, 50, 200])
    df = calculate_momentum(df)
    df = classify_regime(df)
    
    # Test Price Trend strategy
    signals = strategy_price_trend_directional(df)
    result = backtest_strategy_no_sl(df, signals, 10.0, 2.0)
    
    # Get equity curve
    equity_curve = result.equity_curve
    trades = result.trades
    
    # Merge with dates
    equity_df = pd.DataFrame({
        'Date': df['Date'],
        'Equity': equity_curve.values,
    })
    
    # Calculate running maximum (peak equity)
    equity_df['RunningMax'] = equity_df['Equity'].cummax()
    
    # Calculate drawdown
    equity_df['Drawdown'] = equity_df['Equity'] - equity_df['RunningMax']
    equity_df['Drawdown_Pips'] = equity_df['Drawdown'] / 10.0  # Convert to pips ($10 per pip)
    equity_df['Drawdown_Pct'] = (equity_df['Drawdown'] / equity_df['RunningMax'] * 100).fillna(0)
    
    # Merge with trade results
    if len(trades) > 0:
        trades_with_dd = trades.merge(
            equity_df[['Date', 'Equity', 'RunningMax', 'Drawdown', 'Drawdown_Pips', 'Drawdown_Pct']],
            left_on='date',
            right_on='Date',
            how='left'
        )
    else:
        trades_with_dd = pd.DataFrame()
    
    # Show daily drawdown
    print("\n" + "=" * 100)
    print("DAILY DRAWDOWN BREAKDOWN")
    print("=" * 100)
    
    print(f"\n{'Date':<12} {'Equity':<12} {'Peak':<12} {'Drawdown (pips)':<18} {'Drawdown (%)':<15} {'Trade Result':<15}")
    print("-" * 100)
    
    for idx, row in equity_df.iterrows():
        date_str = row['Date'].strftime('%Y-%m-%d')
        equity = row['Equity']
        peak = row['RunningMax']
        dd_pips = row['Drawdown_Pips']
        dd_pct = row['Drawdown_Pct']
        
        # Get trade result for this day if exists
        trade_row = trades[trades['date'] == row['Date']]
        if len(trade_row) > 0:
            trade_result = f"{trade_row.iloc[0]['pips']:+.2f} pips"
        else:
            trade_result = "No trade"
        
        print(f"{date_str:<12} {equity:>10.2f}  {peak:>10.2f}  {dd_pips:>15.2f}  {dd_pct:>12.2f}%  {trade_result:<15}")
    
    print("-" * 100)
    
    # Summary statistics
    max_dd_pips = equity_df['Drawdown_Pips'].min()
    max_dd_pct = equity_df['Drawdown_Pct'].min()
    max_dd_date = equity_df.loc[equity_df['Drawdown_Pips'].idxmin(), 'Date']
    
    print("\n" + "=" * 100)
    print("DRAWDOWN SUMMARY")
    print("=" * 100)
    
    print(f"\nMaximum Drawdown:")
    print(f"  Value: {abs(max_dd_pips):.2f} pips ({abs(max_dd_pct):.2f}%)")
    print(f"  Date: {max_dd_date.strftime('%Y-%m-%d')}")
    print(f"  Equity at Max DD: ${equity_df.loc[equity_df['Drawdown_Pips'].idxmin(), 'Equity']:.2f}")
    print(f"  Peak Equity before: ${equity_df.loc[equity_df['Drawdown_Pips'].idxmin(), 'RunningMax']:.2f}")
    
    # Count days with drawdown
    days_with_dd = (equity_df['Drawdown_Pips'] < 0).sum()
    days_at_peak = (equity_df['Drawdown_Pips'] == 0).sum()
    
    print(f"\nDrawdown Statistics:")
    print(f"  Days with Drawdown: {days_with_dd} / {len(equity_df)} ({days_with_dd/len(equity_df)*100:.1f}%)")
    print(f"  Days at Peak: {days_at_peak} / {len(equity_df)} ({days_at_peak/len(equity_df)*100:.1f}%)")
    print(f"  Average Drawdown (on days with DD): {equity_df[equity_df['Drawdown_Pips'] < 0]['Drawdown_Pips'].mean():.2f} pips")
    
    # Show equity progression
    print(f"\nEquity Progression:")
    print(f"  Starting Equity: ${equity_df.iloc[0]['Equity']:.2f}")
    print(f"  Ending Equity: ${equity_df.iloc[-1]['Equity']:.2f}")
    print(f"  Total Gain: ${equity_df.iloc[-1]['Equity'] - equity_df.iloc[0]['Equity']:.2f}")
    print(f"  Total Gain (pips): {(equity_df.iloc[-1]['Equity'] - equity_df.iloc[0]['Equity']) / 10.0:.2f}")
    
    # Show drawdown periods if any
    if days_with_dd > 0:
        print(f"\nDrawdown Periods:")
        in_dd = False
        dd_start = None
        for idx, row in equity_df.iterrows():
            if row['Drawdown_Pips'] < 0 and not in_dd:
                in_dd = True
                dd_start = row['Date']
            elif row['Drawdown_Pips'] == 0 and in_dd:
                in_dd = False
                dd_end = equity_df.iloc[idx-1]['Date']
                max_dd_in_period = equity_df.iloc[dd_start:idx]['Drawdown_Pips'].min()
                print(f"  {dd_start.strftime('%Y-%m-%d')} to {dd_end.strftime('%Y-%m-%d')}: {abs(max_dd_in_period):.2f} pips")
    else:
        print(f"\nNo Drawdown Periods: Equity always at or above previous peak!")
    
    print("\n" + "=" * 100)
    
    return equity_df, max_dd_pips, max_dd_pct


if __name__ == "__main__":
    equity_df, max_dd, max_dd_pct = calculate_daily_drawdown()

