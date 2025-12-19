"""
Test adding stop losses to directional filtering strategies.
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
from src.backtest import backtest_strategy
# Strategy functions
def strategy_price_trend_directional(df: pd.DataFrame) -> pd.Series:
    """Buy when price above SMA20, sell when below."""
    signals = pd.Series('flat', index=df.index)
    if 'SMA20' in df.columns:
        signals.loc[df['Close'].shift(1) > df['SMA20']] = 'long'
        signals.loc[df['Close'].shift(1) < df['SMA20']] = 'short'
    return signals

def strategy_momentum_directional(df: pd.DataFrame, window: int = 5) -> pd.Series:
    """Buy if recent moves positive, sell if negative."""
    signals = pd.Series('flat', index=df.index)
    if 'net_from_open_pips' in df.columns:
        momentum = df['net_from_open_pips'].rolling(window=window, min_periods=1).mean()
        signals.loc[momentum > 2] = 'long'
        signals.loc[momentum < -2] = 'short'
    return signals

def strategy_combined_directional(df: pd.DataFrame) -> pd.Series:
    """Requires both trend AND momentum to agree."""
    signals = pd.Series('flat', index=df.index)
    trend_signals = strategy_price_trend_directional(df)
    momentum_signals = strategy_momentum_directional(df)
    long_mask = (trend_signals == 'long') & (momentum_signals == 'long')
    short_mask = (trend_signals == 'short') & (momentum_signals == 'short')
    signals.loc[long_mask] = 'long'
    signals.loc[short_mask] = 'short'
    return signals

def strategy_regime_with_momentum_fallback(df: pd.DataFrame) -> pd.Series:
    """Use regime when clear, fall back to momentum for chop."""
    signals = pd.Series('flat', index=df.index)
    signals.loc[df['regime'] == 'bull'] = 'long'
    signals.loc[df['regime'] == 'bear'] = 'short'
    chop_mask = df['regime'] == 'chop'
    if 'net_from_open_pips' in df.columns:
        momentum = df['net_from_open_pips'].rolling(window=5, min_periods=1).mean()
        signals.loc[chop_mask & (momentum > 1)] = 'long'
        signals.loc[chop_mask & (momentum < -1)] = 'short'
    return signals


def test_sl_with_directional():
    """Test various stop loss levels with directional strategies."""
    
    print("=" * 80)
    print("TESTING STOP LOSSES WITH DIRECTIONAL STRATEGIES")
    print("=" * 80)
    
    # Load and prepare data
    data_file = project_root / "data" / "eur_usd.csv"
    df = load_eurusd_data(str(data_file))
    df = calculate_daily_metrics(df)
    df = calculate_moving_averages(df, periods=[20, 50, 200])
    df = calculate_momentum(df)
    df = classify_regime(df)
    
    print(f"\nLoaded {len(df)} days of data\n")
    
    tp_pips = 10.0
    cost_per_trade = 2.0
    
    # Test different SL levels
    sl_levels = [15, 20, 25, 30, 40, 50]
    
    strategies_to_test = {
        'Price Trend (SMA20)': strategy_price_trend_directional,
        'Momentum': strategy_momentum_directional,
        'Combined': strategy_combined_directional,
        'Regime + Momentum': strategy_regime_with_momentum_fallback,
    }
    
    results_summary = []
    
    for strategy_name, strategy_func in strategies_to_test.items():
        print("\n" + "=" * 80)
        print(f"Strategy: {strategy_name}")
        print("=" * 80)
        
        signals = strategy_func(df)
        
        # Test without SL (baseline)
        from src.backtest_no_sl import backtest_strategy_no_sl
        result_no_sl = backtest_strategy_no_sl(df, signals, tp_pips, cost_per_trade)
        stats_no_sl = result_no_sl.get_summary_stats()
        trades_no_sl = result_no_sl.trades
        
        print(f"\nBaseline (No SL):")
        print(f"  Total Pips: {stats_no_sl['total_pips']:+.2f}")
        print(f"  Trades: {stats_no_sl['total_trades']}")
        print(f"  TP Hit Rate: {(trades_no_sl['tp_hit'].sum() / len(trades_no_sl) * 100) if len(trades_no_sl) > 0 else 0:.1f}%")
        print(f"  Win Rate: {stats_no_sl['win_rate']:.2f}%")
        print(f"  Max Drawdown: {stats_no_sl['max_drawdown_pips']:.2f} pips")
        
        results_summary.append({
            'Strategy': strategy_name,
            'SL (pips)': 'No SL',
            'Total Pips': stats_no_sl['total_pips'],
            'Trades': stats_no_sl['total_trades'],
            'Win Rate %': stats_no_sl['win_rate'],
            'TP Hit %': (trades_no_sl['tp_hit'].sum() / len(trades_no_sl) * 100) if len(trades_no_sl) > 0 else 0,
            'Max DD (pips)': stats_no_sl['max_drawdown_pips'],
            'SL Hits': 0,
        })
        
        # Test with different SL levels
        print(f"\nWith Stop Loss:")
        for sl_pips in sl_levels:
            result = backtest_strategy(df, signals, tp_pips, sl_pips, cost_per_trade)
            stats = result.get_summary_stats()
            trades = result.trades
            
            # Count SL hits
            sl_hits = 0
            if 'exit_reason' in trades.columns:
                sl_hits = len(trades[trades['exit_reason'] == 'SL'])
            else:
                # Estimate: trades that lost exactly -SL amount
                expected_sl_loss = -(sl_pips + cost_per_trade)
                sl_hits = len(trades[trades['pips'] <= expected_sl_loss * 0.95])  # Allow small tolerance
            
            tp_hits = len(trades[trades['pips'] >= (tp_pips - cost_per_trade) * 0.95])
            tp_hit_rate = (tp_hits / len(trades) * 100) if len(trades) > 0 else 0
            
            print(f"  SL {sl_pips:2d} pips: Total={stats['total_pips']:+.2f} | "
                  f"Win Rate={stats['win_rate']:.1f}% | TP Hit={tp_hit_rate:.1f}% | "
                  f"SL Hits={sl_hits} | Max DD={stats['max_drawdown_pips']:.2f}")
            
            results_summary.append({
                'Strategy': strategy_name,
                'SL (pips)': f'{sl_pips}',
                'Total Pips': stats['total_pips'],
                'Trades': stats['total_trades'],
                'Win Rate %': stats['win_rate'],
                'TP Hit %': tp_hit_rate,
                'Max DD (pips)': stats['max_drawdown_pips'],
                'SL Hits': sl_hits,
            })
    
    # Summary comparison
    print("\n" + "=" * 80)
    print("SUMMARY COMPARISON")
    print("=" * 80)
    
    summary_df = pd.DataFrame(results_summary)
    
    # Group by strategy and show best SL
    print("\nBest Stop Loss per Strategy:")
    print("-" * 80)
    
    for strategy in strategies_to_test.keys():
        strategy_results = summary_df[summary_df['Strategy'] == strategy]
        best = strategy_results.loc[strategy_results['Total Pips'].idxmax()]
        
        print(f"\n{strategy}:")
        print(f"  Best SL: {best['SL (pips)']} pips")
        print(f"  Total Pips: {best['Total Pips']:+.2f}")
        print(f"  Win Rate: {best['Win Rate %']:.2f}%")
        print(f"  TP Hit Rate: {best['TP Hit %']:.1f}%")
        print(f"  Max Drawdown: {best['Max DD (pips)']:.2f} pips")
        print(f"  SL Hits: {best['SL Hits']}")
    
    # Show full comparison table
    print("\n" + "=" * 80)
    print("FULL COMPARISON TABLE")
    print("=" * 80)
    print(summary_df.to_string(index=False))
    
    print("\n" + "=" * 80)
    print("KEY INSIGHTS:")
    print("=" * 80)
    print("1. Compare No SL vs With SL performance")
    print("2. Check if SL prevents losses or stops out winning trades")
    print("3. Look for optimal SL that protects without reducing wins")
    print("4. Consider: If strategy already has 0 drawdown, SL may not add value")
    print("=" * 80)


if __name__ == "__main__":
    test_sl_with_directional()

