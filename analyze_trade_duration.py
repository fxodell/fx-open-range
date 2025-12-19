"""
Analyze how long trades were held.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from src.data_loader import load_eurusd_data
from src.core_analysis import calculate_daily_metrics
from src.regime import calculate_moving_averages
from src.backtest_no_sl import backtest_strategy_no_sl


def strategy_price_trend_directional(df: pd.DataFrame) -> pd.Series:
    """Buy when price above SMA20, sell when below."""
    signals = pd.Series('flat', index=df.index)
    if 'SMA20' in df.columns:
        signals.loc[df['Close'].shift(1) > df['SMA20']] = 'long'
        signals.loc[df['Close'].shift(1) < df['SMA20']] = 'short'
    return signals


def analyze_trade_duration():
    """Analyze how long trades were held."""
    
    print("=" * 80)
    print("TRADE DURATION ANALYSIS")
    print("=" * 80)
    
    # Load data (use long-term for more realistic analysis)
    data_file = project_root / "data" / "eur_usd_long_term.csv"
    print(f"\nLoading data from: {data_file}")
    
    df = load_eurusd_data(str(data_file))
    df = calculate_daily_metrics(df)
    df = calculate_moving_averages(df)
    
    print(f"Loaded {len(df)} days of data")
    print(f"Date range: {df['Date'].min()} to {df['Date'].max()}\n")
    
    # Run strategy
    signals = strategy_price_trend_directional(df)
    result = backtest_strategy_no_sl(df, signals, 10.0, 2.0)
    trades = result.trades
    
    # Merge with OHLC data for analysis
    trades_detailed = trades.merge(
        df[['Date', 'Open', 'High', 'Low', 'Close']],
        left_on='date',
        right_on='Date',
        how='left'
    )
    
    print("=" * 80)
    print("TRADE EXIT ANALYSIS")
    print("=" * 80)
    
    # Count TP hits vs EOD exits
    tp_hits = trades_detailed[trades_detailed['tp_hit'] == True]
    eod_exits = trades_detailed[trades_detailed['tp_hit'] == False]
    
    print(f"\nExit Types:")
    print(f"  TP Hits (intraday exit): {len(tp_hits)} trades ({len(tp_hits)/len(trades)*100:.1f}%)")
    print(f"  EOD Exits (full day): {len(eod_exits)} trades ({len(eod_exits)/len(trades)*100:.1f}%)")
    
    # Trade duration information
    print(f"\n" + "=" * 80)
    print("TRADE DURATION SUMMARY")
    print("=" * 80)
    
    print(f"\nSince we use daily OHLC data, we can estimate:")
    print(f"  • TP Hits: Exited intraday (before market close)")
    print(f"    - These trades hit 10 pip target during the day")
    print(f"    - Duration: Less than full trading day (intraday)")
    print(f"    - Exact time unknown (would need intraday data)")
    
    print(f"\n  • EOD Exits: Held full trading day")
    print(f"    - TP not hit, exited at end of day")
    print(f"    - Duration: Full trading day (~24 hours for FX)")
    print(f"    - Entry: Daily open")
    print(f"    - Exit: Daily close")
    
    # Analyze TP hits
    if len(tp_hits) > 0:
        print(f"\n" + "=" * 80)
        print("TP HITS (Intraday Exits) Analysis")
        print("=" * 80)
        print(f"Count: {len(tp_hits)} trades")
        print(f"Avg Pips: {tp_hits['pips'].mean():.2f}")
        print(f"Win Rate: {(tp_hits['pips'] > 0).sum() / len(tp_hits) * 100:.1f}%")
        print(f"\nNote: TP hits occur intraday, but exact timing requires intraday data")
        print(f"      Based on daily OHLC, we know TP was hit but not when")
        
    # Analyze EOD exits
    if len(eod_exits) > 0:
        print(f"\n" + "=" * 80)
        print("EOD EXITS (Full Day) Analysis")
        print("=" * 80)
        print(f"Count: {len(eod_exits)} trades")
        print(f"Avg Pips: {eod_exits['pips'].mean():.2f}")
        print(f"Win Rate: {(eod_exits['pips'] > 0).sum() / len(eod_exits) * 100:.1f}%")
        print(f"Duration: Full trading day (entry at open, exit at close)")
        print(f"          Approximately 24 hours for FX markets")
        
        # Show some EOD exit examples
        print(f"\nSample EOD Exits (first 10):")
        print(f"{'Date':<12} {'Dir':<6} {'Entry':<10} {'Close':<10} {'Result':<10}")
        print("-" * 60)
        for idx, trade in eod_exits.head(10).iterrows():
            print(f"{trade['date'].strftime('%Y-%m-%d'):<12} {trade['direction'].upper():<6} {trade['entry_price']:.5f}  {trade['Close']:.5f}  {trade['pips']:+.2f}")
    
    # Duration statistics
    print(f"\n" + "=" * 80)
    print("DURATION STATISTICS")
    print("=" * 80)
    
    # For TP hits: estimate as "intraday" (less than full day)
    # For EOD: full day
    # Since we don't have exact intraday timing, we estimate:
    # - TP hits: average of 50% through the day (approximation)
    # - EOD: 100% of the day (full day)
    
    estimated_duration_tp = 0.5  # Estimate: TP hits average 50% through the day
    estimated_duration_eod = 1.0  # EOD = full day
    
    avg_duration = (len(tp_hits) * estimated_duration_tp + len(eod_exits) * estimated_duration_eod) / len(trades)
    
    print(f"\nEstimated Average Trade Duration:")
    print(f"  TP Hits ({len(tp_hits)} trades): ~50% of trading day (estimate)")
    print(f"  EOD Exits ({len(eod_exits)} trades): 100% of trading day (full day)")
    print(f"  Overall Average: ~{avg_duration*100:.1f}% of trading day")
    print(f"                     (~{avg_duration*24:.1f} hours, assuming 24h FX market)")
    
    print(f"\nNote: Exact intraday timing requires minute/hourly data")
    print(f"      Current analysis uses daily OHLC, so exact duration is estimated")
    
    # Show breakdown by direction
    print(f"\n" + "=" * 80)
    print("DURATION BY DIRECTION")
    print("=" * 80)
    
    long_tp = tp_hits[tp_hits['direction'] == 'long']
    long_eod = eod_exits[eod_exits['direction'] == 'long']
    short_tp = tp_hits[tp_hits['direction'] == 'short']
    short_eod = eod_exits[eod_exits['direction'] == 'short']
    
    print(f"\nLong Trades:")
    print(f"  TP Hits: {len(long_tp)} ({len(long_tp)/(len(long_tp)+len(long_eod))*100:.1f}% of long trades)")
    print(f"  EOD Exits: {len(long_eod)} ({len(long_eod)/(len(long_tp)+len(long_eod))*100:.1f}% of long trades)")
    
    print(f"\nShort Trades:")
    print(f"  TP Hits: {len(short_tp)} ({len(short_tp)/(len(short_tp)+len(short_eod))*100:.1f}% of short trades)")
    print(f"  EOD Exits: {len(short_eod)} ({len(short_eod)/(len(short_tp)+len(short_eod))*100:.1f}% of short trades)")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    analyze_trade_duration()

