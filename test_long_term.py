"""
Test directional strategies on long-term data to see realistic performance.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pandas as pd
from src.data_loader import load_eurusd_data
from src.core_analysis import calculate_daily_metrics, calculate_adr
from src.regime import calculate_moving_averages, calculate_momentum, classify_regime
from src.backtest_no_sl import backtest_strategy_no_sl


def strategy_price_trend_directional(df: pd.DataFrame) -> pd.Series:
    """Buy when price above SMA20, sell when below."""
    signals = pd.Series('flat', index=df.index)
    if 'SMA20' in df.columns:
        signals.loc[df['Close'].shift(1) > df['SMA20']] = 'long'
        signals.loc[df['Close'].shift(1) < df['SMA20']] = 'short'
    return signals


def test_long_term_strategy():
    """Test strategy on long-term data."""
    
    print("=" * 80)
    print("LONG-TERM STRATEGY TEST (5 Years of Data)")
    print("=" * 80)
    
    # Load long-term data
    data_file = project_root / "data" / "eur_usd_long_term.csv"
    print(f"\nLoading data from: {data_file}")
    
    df = load_eurusd_data(str(data_file))
    print(f"Loaded {len(df)} days of data")
    print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
    print(f"Years: {(df['Date'].max() - df['Date'].min()).days / 365.25:.1f} years\n")
    
    # Calculate features
    df = calculate_daily_metrics(df)
    df = calculate_moving_averages(df, periods=[20, 50, 100, 200])
    df = calculate_momentum(df, periods=[1, 3, 6])
    df = classify_regime(df)
    
    # Test strategy
    signals = strategy_price_trend_directional(df)
    result = backtest_strategy_no_sl(df, signals, 10.0, 2.0)
    
    # Print results
    result.print_summary()
    
    # Additional analysis
    trades = result.trades
    if len(trades) > 0:
        tp_hit_rate = (trades['tp_hit']).sum() / len(trades) * 100
        wins = (trades['pips'] > 0).sum()
        losses = (trades['pips'] <= 0).sum()
        
        print(f"\nAdditional Stats:")
        print(f"  TP Hit Rate: {tp_hit_rate:.2f}%")
        print(f"  Wins: {wins} ({wins/len(trades)*100:.1f}%)")
        print(f"  Losses: {losses} ({losses/len(trades)*100:.1f}%)")
        
        if losses > 0:
            losing_trades = trades[trades['pips'] <= 0]
            print(f"  Average Loss: {losing_trades['pips'].mean():.2f} pips")
            print(f"  Largest Loss: {losing_trades['pips'].min():.2f} pips")
        
        # Drawdown analysis
        equity = result.equity_curve.values
        running_max = np.maximum.accumulate(equity)
        drawdown = equity - running_max
        max_dd_pips = abs(drawdown.min()) / 10.0  # Convert to pips
        
        print(f"\nDrawdown Analysis:")
        print(f"  Max Drawdown: {max_dd_pips:.2f} pips")
        if drawdown.min() < 0:
            max_dd_idx = np.argmin(drawdown)
            max_dd_pct = (abs(drawdown.min()) / running_max[max_dd_idx] * 100) if running_max[max_dd_idx] > 0 else 0
            print(f"  Max DD %: {max_dd_pct:.2f}%")
    
    print("\n" + "=" * 80)
    print("Compare these results to the 23-day sample to see the difference!")
    print("=" * 80)


if __name__ == "__main__":
    import numpy as np
    test_long_term_strategy()

