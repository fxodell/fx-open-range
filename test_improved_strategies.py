"""
Test improved strategies based on analysis.
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
    """Baseline: Buy when price above SMA20, sell when below."""
    signals = pd.Series('flat', index=df.index)
    if 'SMA20' in df.columns:
        signals.loc[df['Close'].shift(1) > df['SMA20']] = 'long'
        signals.loc[df['Close'].shift(1) < df['SMA20']] = 'short'
    return signals


def strategy_with_adr_filter(df: pd.DataFrame, min_adr: float = 40.0) -> pd.Series:
    """Add ADR filter to skip low-volatility days."""
    signals = strategy_price_trend_directional(df)
    adr = calculate_adr(df, window=20)
    signals.loc[adr < min_adr] = 'flat'
    return signals


def strategy_with_day_filter(df: pd.DataFrame) -> pd.Series:
    """Skip Wednesday (weakest day)."""
    signals = strategy_price_trend_directional(df)
    trades_df = pd.DataFrame({'date': df['Date'], 'signal': signals})
    trades_df['DayOfWeek'] = pd.to_datetime(trades_df['date']).dt.day_name()
    trades_df.loc[trades_df['DayOfWeek'] == 'Wednesday', 'signal'] = 'flat'
    
    return pd.Series(trades_df['signal'].values, index=df.index)


def strategy_with_adr_and_day_filter(df: pd.DataFrame, min_adr: float = 40.0) -> pd.Series:
    """Combine ADR and day-of-week filters."""
    signals = strategy_price_trend_directional(df)
    adr = calculate_adr(df, window=20)
    signals.loc[adr < min_adr] = 'flat'
    
    # Skip Wednesday
    trades_df = pd.DataFrame({'date': df['Date'], 'signal': signals})
    trades_df['DayOfWeek'] = pd.to_datetime(trades_df['date']).dt.day_name()
    trades_df.loc[trades_df['DayOfWeek'] == 'Wednesday', 'signal'] = 'flat'
    
    return pd.Series(trades_df['signal'].values, index=df.index)


def strategy_high_volatility_only(df: pd.DataFrame, min_adr: float = 60.0) -> pd.Series:
    """Only trade on high-volatility days."""
    signals = strategy_price_trend_directional(df)
    adr = calculate_adr(df, window=20)
    signals.loc[adr < min_adr] = 'flat'
    return signals


def test_improvements():
    """Test improved strategies."""
    
    print("=" * 80)
    print("TESTING STRATEGY IMPROVEMENTS")
    print("=" * 80)
    
    # Load data
    df = load_eurusd_data('data/eur_usd_long_term.csv')
    df = calculate_daily_metrics(df)
    df = calculate_moving_averages(df)
    
    strategies_to_test = {
        'Baseline (SMA20)': strategy_price_trend_directional,
        'ADR Filter (min 40)': lambda df: strategy_with_adr_filter(df, min_adr=40.0),
        'ADR Filter (min 50)': lambda df: strategy_with_adr_filter(df, min_adr=50.0),
        'Skip Wednesday': strategy_with_day_filter,
        'ADR + Day Filter': lambda df: strategy_with_adr_and_day_filter(df, min_adr=40.0),
        'High Vol Only (ADR 60+)': lambda df: strategy_high_volatility_only(df, min_adr=60.0),
    }
    
    results = {}
    
    for name, strategy_func in strategies_to_test.items():
        print(f"\n{'=' * 80}")
        print(f"Testing: {name}")
        print(f"{'=' * 80}")
        
        signals = strategy_func(df)
        result = backtest_strategy_no_sl(df, signals, 10.0, 2.0)
        
        trades = result.trades
        if len(trades) > 0:
            tp_hit_rate = (trades['tp_hit']).sum() / len(trades) * 100
            eod_exits = trades[~trades['tp_hit']]
            eod_win_rate = (eod_exits['pips'] > 0).sum() / len(eod_exits) * 100 if len(eod_exits) > 0 else 0
            
            stats = result.get_summary_stats()
            
            print(f"  Trades: {stats['total_trades']}")
            print(f"  Total Pips: {stats['total_pips']:+.2f}")
            print(f"  Win Rate: {stats['win_rate']:.2f}%")
            print(f"  TP Hit Rate: {tp_hit_rate:.2f}%")
            print(f"  EOD Exit Win Rate: {eod_win_rate:.2f}%")
            print(f"  Max Drawdown: {stats['max_drawdown_pips']:.2f} pips")
            
            results[name] = {
                'trades': stats['total_trades'],
                'total_pips': stats['total_pips'],
                'win_rate': stats['win_rate'],
                'tp_hit_rate': tp_hit_rate,
                'eod_win_rate': eod_win_rate,
                'max_dd': stats['max_drawdown_pips'],
            }
        else:
            print("  No trades generated")
    
    # Comparison
    print(f"\n{'=' * 80}")
    print("IMPROVEMENT COMPARISON")
    print(f"{'=' * 80}")
    
    comparison_data = []
    baseline = results.get('Baseline (SMA20)', {})
    
    for name, stats in results.items():
        comparison_data.append({
            'Strategy': name,
            'Trades': stats['trades'],
            'Total Pips': f"{stats['total_pips']:+.2f}",
            'Win Rate %': f"{stats['win_rate']:.2f}",
            'TP Hit %': f"{stats['tp_hit_rate']:.2f}",
            'EOD Win %': f"{stats['eod_win_rate']:.2f}",
            'Max DD': f"{stats['max_dd']:.2f}",
            'Pips vs Baseline': f"{stats['total_pips'] - baseline.get('total_pips', 0):+.2f}",
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    print("\n" + comparison_df.to_string(index=False))
    
    print(f"\n{'=' * 80}")
    print("RECOMMENDATIONS:")
    print(f"{'=' * 80}")
    
    # Find best improvements
    best_pips = max(results.items(), key=lambda x: x[1]['total_pips'])
    best_tp_hit = max(results.items(), key=lambda x: x[1]['tp_hit_rate'])
    best_eod = max(results.items(), key=lambda x: x[1]['eod_win_rate'])
    
    print(f"\nBest Total Pips: {best_pips[0]} ({best_pips[1]['total_pips']:+.2f})")
    print(f"Best TP Hit Rate: {best_tp_hit[0]} ({best_tp_hit[1]['tp_hit_rate']:.2f}%)")
    print(f"Best EOD Win Rate: {best_eod[0]} ({best_eod[1]['eod_win_rate']:.2f}%)")


if __name__ == "__main__":
    test_improvements()

