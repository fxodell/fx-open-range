"""
Analyze current strategy performance and suggest improvements.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from src.data_loader import load_eurusd_data
from src.core_analysis import calculate_daily_metrics, calculate_adr
from src.regime import calculate_moving_averages
from src.backtest_no_sl import backtest_strategy_no_sl


def strategy_price_trend_directional(df: pd.DataFrame) -> pd.Series:
    """Buy when price above SMA20, sell when below."""
    signals = pd.Series('flat', index=df.index)
    if 'SMA20' in df.columns:
        signals.loc[df['Close'].shift(1) > df['SMA20']] = 'long'
        signals.loc[df['Close'].shift(1) < df['SMA20']] = 'short'
    return signals


def analyze_weak_points():
    """Identify weak points in current strategy."""
    
    print("=" * 80)
    print("STRATEGY IMPROVEMENT ANALYSIS")
    print("=" * 80)
    
    # Load long-term data
    df = load_eurusd_data('data/eur_usd_long_term.csv')
    df = calculate_daily_metrics(df)
    df = calculate_moving_averages(df)
    
    signals = strategy_price_trend_directional(df)
    result = backtest_strategy_no_sl(df, signals, 10.0, 2.0)
    trades = result.trades
    
    # Merge with market data
    trades_detailed = trades.merge(
        df[['Date', 'Open', 'High', 'Low', 'Close', 'range_pips', 
            'up_from_open_pips', 'down_from_open_pips', 'net_from_open_pips']],
        left_on='date',
        right_on='Date',
        how='left'
    )
    
    print(f"\nTotal Trades: {len(trades)}")
    
    # Analyze EOD exits (the weak point)
    eod_exits = trades_detailed[~trades_detailed['tp_hit']]
    
    print(f"\n{'=' * 80}")
    print("EOD EXITS ANALYSIS (The Weak Point)")
    print(f"{'=' * 80}")
    print(f"Count: {len(eod_exits)} trades (18.9% of all trades)")
    print(f"Win Rate: {(eod_exits['pips'] > 0).sum() / len(eod_exits) * 100:.1f}%")
    print(f"Average: {eod_exits['pips'].mean():.2f} pips")
    print(f"\nThis is where we can improve!")
    
    # Analyze characteristics of losing EOD exits
    losing_eod = eod_exits[eod_exits['pips'] <= 0]
    
    if len(losing_eod) > 0:
        print(f"\nLosing EOD Exits ({len(losing_eod)} trades):")
        print(f"  Average Range: {losing_eod['range_pips'].mean():.1f} pips")
        print(f"  Average Loss: {losing_eod['pips'].mean():.2f} pips")
        
        # Check if low volatility days
        adr = calculate_adr(df, window=20)
        losing_eod_with_adr = losing_eod.merge(
            df[['Date']].assign(ADR=adr),
            left_on='date',
            right_on='Date',
            how='left'
        )
        print(f"  Average ADR: {losing_eod_with_adr['ADR'].mean():.1f} pips")
        
        # Check direction
        print(f"  Long trades: {len(losing_eod[losing_eod['direction'] == 'long'])}")
        print(f"  Short trades: {len(losing_eod[losing_eod['direction'] == 'short'])}")
    
    # Analyze day-of-week patterns
    trades_detailed['DayOfWeek'] = pd.to_datetime(trades_detailed['date']).dt.day_name()
    print(f"\n{'=' * 80}")
    print("DAY-OF-WEEK PATTERNS")
    print(f"{'=' * 80}")
    day_perf = trades_detailed.groupby('DayOfWeek')['pips'].agg(['mean', 'count'])
    day_perf = day_perf.sort_values('mean', ascending=False)
    print(day_perf)
    
    # Analyze by ADR
    adr = calculate_adr(df, window=20)
    trades_with_adr = trades_detailed.merge(
        df[['Date']].assign(ADR=adr),
        left_on='date',
        right_on='Date',
        how='left'
    )
    
    print(f"\n{'=' * 80}")
    print("VOLATILITY (ADR) ANALYSIS")
    print(f"{'=' * 80}")
    print(f"Average ADR: {trades_with_adr['ADR'].mean():.1f} pips")
    
    # Performance by ADR buckets
    trades_with_adr['ADR_Bucket'] = pd.cut(trades_with_adr['ADR'], 
                                           bins=[0, 40, 60, 80, 1000], 
                                           labels=['Low (<40)', 'Medium (40-60)', 'High (60-80)', 'Very High (80+)'])
    
    adr_perf = trades_with_adr.groupby('ADR_Bucket')['pips'].agg(['mean', 'count', lambda x: (x > 0).sum() / len(x) * 100])
    adr_perf.columns = ['Avg Pips', 'Count', 'Win Rate %']
    print(f"\nPerformance by ADR:")
    print(adr_perf)
    
    print(f"\n{'=' * 80}")


if __name__ == "__main__":
    analyze_weak_points()

