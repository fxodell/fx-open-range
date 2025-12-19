"""
Show each day's trade results for directional strategies.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pandas as pd
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


def show_daily_trades():
    """Show each day's trade in detail."""
    
    print("=" * 100)
    print("DAILY TRADE BREAKDOWN - DIRECTIONAL STRATEGIES")
    print("=" * 100)
    
    # Load and prepare data
    data_file = project_root / "data" / "eur_usd.csv"
    df = load_eurusd_data(str(data_file))
    df = calculate_daily_metrics(df)
    df = calculate_moving_averages(df, periods=[20, 50, 200])
    df = calculate_momentum(df)
    df = classify_regime(df)
    
    print(f"\nTotal Days in Data: {len(df)}")
    print(f"Date Range: {df['Date'].min()} to {df['Date'].max()}\n")
    
    # Test Price Trend strategy
    signals = strategy_price_trend_directional(df)
    result = backtest_strategy_no_sl(df, signals, 10.0, 2.0)
    trades = result.trades
    
    # Merge with original data for full context
    trades_detailed = trades.merge(
        df[['Date', 'Open', 'High', 'Low', 'Close', 'range_pips', 
            'up_from_open_pips', 'down_from_open_pips', 'net_from_open_pips', 'SMA20']],
        left_on='date',
        right_on='Date',
        how='left'
    )
    
    trades_detailed = trades_detailed.sort_values('date')
    
    print("=" * 100)
    print("PRICE TREND (SMA20) STRATEGY - DAILY TRADES")
    print("=" * 100)
    print(f"\nTotal Trading Days: {len(trades_detailed)}")
    print(f"Trading Days: {len(trades_detailed)} / Total Days: {len(df)} ({len(trades_detailed)/len(df)*100:.1f}%)\n")
    
    print("-" * 100)
    print(f"{'Date':<12} {'Dir':<6} {'Entry':<10} {'High':<10} {'Low':<10} {'Close':<10} {'TP Hit':<8} {'Result':<10} {'Range':<8}")
    print("-" * 100)
    
    for idx, trade in trades_detailed.iterrows():
        date_str = trade['date'].strftime('%Y-%m-%d')
        direction = trade['direction'].upper()
        entry = trade['entry_price']
        high = trade['High']
        low = trade['Low']
        close = trade['Close']
        tp_hit = 'Yes' if trade['tp_hit'] else 'No'
        result_pips = trade['pips']
        daily_range = trade['range_pips']
        
        # Determine if TP was hit
        if direction == 'LONG':
            tp_target = entry + 0.0010  # 10 pips
            tp_hit_actual = 'Yes' if high >= tp_target else 'No'
        else:
            tp_target = entry - 0.0010  # 10 pips
            tp_hit_actual = 'Yes' if low <= tp_target else 'No'
        
        result_str = f"{result_pips:+.2f}"
        
        print(f"{date_str:<12} {direction:<6} {entry:.5f}  {high:.5f}  {low:.5f}  {close:.5f}  {tp_hit_actual:<8} {result_str:<10} {daily_range:.1f}")
    
    print("-" * 100)
    
    # Summary statistics
    print("\n" + "=" * 100)
    print("SUMMARY STATISTICS")
    print("=" * 100)
    
    total_pips = trades_detailed['pips'].sum()
    avg_pips = trades_detailed['pips'].mean()
    wins = (trades_detailed['pips'] > 0).sum()
    losses = (trades_detailed['pips'] <= 0).sum()
    tp_hits = trades_detailed['tp_hit'].sum()
    
    long_trades = trades_detailed[trades_detailed['direction'] == 'long']
    short_trades = trades_detailed[trades_detailed['direction'] == 'short']
    
    print(f"\nTotal Trading Days: {len(trades_detailed)}")
    print(f"  Long Trades: {len(long_trades)}")
    print(f"  Short Trades: {len(short_trades)}")
    print(f"\nResults:")
    print(f"  Total Pips: {total_pips:+.2f}")
    print(f"  Average Pips/Trade: {avg_pips:.2f}")
    print(f"  Wins: {wins} ({wins/len(trades_detailed)*100:.1f}%)")
    print(f"  Losses: {losses} ({losses/len(trades_detailed)*100:.1f}%)")
    print(f"  TP Hits: {tp_hits} ({tp_hits/len(trades_detailed)*100:.1f}%)")
    
    print(f"\nLong Trade Performance:")
    if len(long_trades) > 0:
        print(f"  Count: {len(long_trades)}")
        print(f"  Total: {long_trades['pips'].sum():+.2f} pips")
        print(f"  Avg: {long_trades['pips'].mean():.2f} pips")
        print(f"  TP Hits: {(long_trades['tp_hit']).sum()} ({long_trades['tp_hit'].sum()/len(long_trades)*100:.1f}%)")
    
    print(f"\nShort Trade Performance:")
    if len(short_trades) > 0:
        print(f"  Count: {len(short_trades)}")
        print(f"  Total: {short_trades['pips'].sum():+.2f} pips")
        print(f"  Avg: {short_trades['pips'].mean():.2f} pips")
        print(f"  TP Hits: {(short_trades['tp_hit']).sum()} ({short_trades['tp_hit'].sum()/len(short_trades)*100:.1f}%)")
    
    # Show days with no trade
    trading_dates = set(trades_detailed['date'])
    all_dates = set(df['Date'])
    no_trade_dates = sorted(all_dates - trading_dates)
    
    if len(no_trade_dates) > 0:
        print(f"\nDays with NO TRADE ({len(no_trade_dates)} days):")
        for date in no_trade_dates:
            date_row = df[df['Date'] == date].iloc[0]
            if 'SMA20' in df.columns:
                above_ma = date_row['Close'] > date_row['SMA20']
                ma_status = f"Price {'above' if above_ma else 'below'} SMA20"
                print(f"  {date.strftime('%Y-%m-%d')}: {ma_status}")
            else:
                print(f"  {date.strftime('%Y-%m-%d')}")
    
    print("\n" + "=" * 100)


if __name__ == "__main__":
    show_daily_trades()

