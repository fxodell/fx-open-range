"""
Improved directional filtering using price action and momentum indicators.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from src.data_loader import load_eurusd_data
from src.core_analysis import calculate_daily_metrics, calculate_adr
from src.regime import calculate_moving_averages, calculate_momentum, classify_regime
from src.backtest_no_sl import backtest_strategy_no_sl
from src.strategies import strategy_always_buy, strategy_always_sell


def strategy_price_trend_directional(df: pd.DataFrame) -> pd.Series:
    """
    Use price trend: buy if price above recent MA (uptrend), sell if below (downtrend).
    """
    signals = pd.Series('flat', index=df.index)
    
    # Use SMA20 as short-term trend filter
    if 'SMA20' in df.columns:
        # Buy when price above SMA20 (uptrend)
        signals.loc[df['Close'].shift(1) > df['SMA20']] = 'long'
        # Sell when price below SMA20 (downtrend)
        signals.loc[df['Close'].shift(1) < df['SMA20']] = 'short'
    else:
        # Fallback: use simple moving average
        ma = df['Close'].rolling(window=5).mean()
        signals.loc[df['Close'].shift(1) > ma] = 'long'
        signals.loc[df['Close'].shift(1) < ma] = 'short'
    
    return signals


def strategy_momentum_directional(df: pd.DataFrame, window: int = 5) -> pd.Series:
    """
    Use momentum: buy if recent moves are positive, sell if negative.
    """
    signals = pd.Series('flat', index=df.index)
    
    if 'net_from_open_pips' in df.columns:
        # Average of recent net moves
        momentum = df['net_from_open_pips'].rolling(window=window, min_periods=1).mean()
        signals.loc[momentum > 2] = 'long'  # Buy if positive momentum
        signals.loc[momentum < -2] = 'short'  # Sell if negative momentum
    else:
        # Fallback: use close-to-close momentum
        momentum = df['Close'].pct_change(window) * 10000
        signals.loc[momentum > 2] = 'long'
        signals.loc[momentum < -2] = 'short'
    
    return signals


def strategy_recent_high_low(df: pd.DataFrame, lookback: int = 5) -> pd.Series:
    """
    Buy if open is near recent low, sell if near recent high.
    Based on mean reversion / range trading logic.
    """
    signals = pd.Series('flat', index=df.index)
    
    # Calculate recent high and low
    recent_high = df['High'].rolling(window=lookback, min_periods=1).max()
    recent_low = df['Low'].rolling(window=lookback, min_periods=1).min()
    recent_range = recent_high - recent_low
    
    # Buy if open is in lower 30% of recent range (bounce from low)
    buy_threshold = recent_low + 0.3 * recent_range
    signals.loc[df['Open'] <= buy_threshold] = 'long'
    
    # Sell if open is in upper 30% of recent range (reject from high)
    sell_threshold = recent_high - 0.3 * recent_range
    signals.loc[df['Open'] >= sell_threshold] = 'short'
    
    return signals


def strategy_up_move_vs_down_move(df: pd.DataFrame) -> pd.Series:
    """
    Compare up_move vs down_move potential from open.
    Buy if up_move typically larger, sell if down_move typically larger.
    """
    signals = pd.Series('flat', index=df.index)
    
    if 'up_from_open_pips' in df.columns and 'down_from_open_pips' in df.columns:
        # Use recent average to predict direction
        avg_up = df['up_from_open_pips'].rolling(window=5, min_periods=1).mean()
        avg_down = df['down_from_open_pips'].rolling(window=5, min_periods=1).mean()
        
        # Buy if up moves are typically larger (bullish)
        signals.loc[avg_up > avg_down + 5] = 'long'
        # Sell if down moves are typically larger (bearish)
        signals.loc[avg_down > avg_up + 5] = 'short'
    
    return signals


def strategy_combined_directional(df: pd.DataFrame) -> pd.Series:
    """
    Combine multiple signals: price trend + momentum.
    """
    signals = pd.Series('flat', index=df.index)
    
    # Get individual signals
    trend_signals = strategy_price_trend_directional(df)
    momentum_signals = strategy_momentum_directional(df)
    
    # Combine: need agreement (both say same direction)
    long_mask = (trend_signals == 'long') & (momentum_signals == 'long')
    short_mask = (trend_signals == 'short') & (momentum_signals == 'short')
    
    signals.loc[long_mask] = 'long'
    signals.loc[short_mask] = 'short'
    
    return signals


def strategy_regime_with_momentum_fallback(df: pd.DataFrame) -> pd.Series:
    """
    Use regime when available, fall back to momentum for chop.
    """
    signals = pd.Series('flat', index=df.index)
    
    # Regime signals
    signals.loc[df['regime'] == 'bull'] = 'long'
    signals.loc[df['regime'] == 'bear'] = 'short'
    
    # For chop, use momentum
    chop_mask = df['regime'] == 'chop'
    if 'net_from_open_pips' in df.columns:
        momentum = df['net_from_open_pips'].rolling(window=5, min_periods=1).mean()
        signals.loc[chop_mask & (momentum > 1)] = 'long'
        signals.loc[chop_mask & (momentum < -1)] = 'short'
    
    return signals


def test_improved_directional():
    """Test improved directional strategies."""
    
    print("=" * 80)
    print("IMPROVED DIRECTIONAL FILTERING (10 pip TP, no SL, exit at EOD)")
    print("=" * 80)
    
    # Load and prepare data
    data_file = project_root / "data" / "eur_usd.csv"
    print(f"\nLoading data from: {data_file}")
    
    df = load_eurusd_data(str(data_file))
    df = calculate_daily_metrics(df)
    df = calculate_moving_averages(df, periods=[20, 50, 100, 200])
    df = calculate_momentum(df, periods=[1, 3, 6])
    df = classify_regime(df)
    
    print(f"Loaded {len(df)} days of data")
    print(f"Date range: {df['Date'].min()} to {df['Date'].max()}\n")
    
    # Strategy parameters
    tp_pips = 10.0
    cost_per_trade = 2.0
    
    # Define strategies to test
    strategies_to_test = {
        'Baseline: Always Buy': strategy_always_buy,
        'Baseline: Always Sell': strategy_always_sell,
        'Price Trend (SMA20 filter)': strategy_price_trend_directional,
        'Momentum (5-day avg net move)': strategy_momentum_directional,
        'Combined (Trend + Momentum)': strategy_combined_directional,
        'Regime + Momentum Fallback': strategy_regime_with_momentum_fallback,
    }
    
    results = {}
    
    for strategy_name, strategy_func in strategies_to_test.items():
        print("\n" + "=" * 80)
        print(f"Strategy: {strategy_name}")
        print("=" * 80)
        
        try:
            # Generate signals
            signals = strategy_func(df)
            
            # Count signals
            signal_counts = signals.value_counts()
            print(f"\nSignal Distribution:")
            for sig, count in signal_counts.items():
                print(f"  {sig}: {count}")
            
            # Skip if no trades
            if len(signals[signals.isin(['long', 'short'])]) == 0:
                print("No signals generated - skipping backtest")
                continue
            
            # Run backtest
            result = backtest_strategy_no_sl(
                df,
                signals,
                take_profit_pips=tp_pips,
                cost_per_trade_pips=cost_per_trade,
            )
            
            # Print summary
            result.print_summary()
            
            # Additional stats
            trades = result.trades
            if len(trades) > 0:
                tp_hit_rate = (trades['tp_hit']).sum() / len(trades) * 100
                eod_exits = trades[~trades['tp_hit']]
                
                long_trades = trades[trades['direction'] == 'long']
                short_trades = trades[trades['direction'] == 'short']
                
                print(f"\nAdditional Stats:")
                print(f"  TP Hit Rate:     {tp_hit_rate:.2f}%")
                print(f"  EOD Exits:       {len(eod_exits)} ({len(eod_exits)/len(trades)*100:.1f}%)")
                
                if len(long_trades) > 0:
                    long_tp = (long_trades['tp_hit']).sum() / len(long_trades) * 100
                    print(f"  Long: {len(long_trades)} trades | TP: {long_tp:.1f}% | Avg: {long_trades['pips'].mean():.2f} pips")
                
                if len(short_trades) > 0:
                    short_tp = (short_trades['tp_hit']).sum() / len(short_trades) * 100
                    print(f"  Short: {len(short_trades)} trades | TP: {short_tp:.1f}% | Avg: {short_trades['pips'].mean():.2f} pips")
                
                if len(eod_exits) > 0:
                    eod_avg = eod_exits['pips'].mean()
                    eod_wins = (eod_exits['pips'] > 0).sum()
                    eod_losses = (eod_exits['pips'] <= 0).sum()
                    print(f"  EOD Avg: {eod_avg:.2f} pips ({eod_wins}W/{eod_losses}L)")
            
            results[strategy_name] = result
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Comparison table
    print("\n" + "=" * 80)
    print("STRATEGY COMPARISON")
    print("=" * 80)
    
    comparison_data = []
    for name, result in results.items():
        stats = result.get_summary_stats()
        trades = result.trades
        
        if len(trades) > 0:
            tp_hit_rate = (trades['tp_hit']).sum() / len(trades) * 100
            eod_exits = trades[~trades['tp_hit']]
            eod_avg_loss = eod_exits[eod_exits['pips'] <= 0]['pips'].mean() if len(eod_exits[eod_exits['pips'] <= 0]) > 0 else 0.0
        else:
            tp_hit_rate = 0.0
            eod_avg_loss = 0.0
        
        comparison_data.append({
            'Strategy': name[:40],
            'Total Pips': f"{stats['total_pips']:+.2f}",
            'Trades': stats['total_trades'],
            'TP Hit %': f"{tp_hit_rate:.1f}",
            'Win Rate %': f"{stats['win_rate']:.2f}",
            'Avg Win': f"{stats['avg_win']:.2f}",
            'Avg Loss': f"{stats['avg_loss']:.2f}",
            'Profit Factor': f"{stats['profit_factor']:.2f}",
            'Max DD': f"{stats['max_drawdown_pips']:.0f}",
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    print("\n" + comparison_df.to_string(index=False))
    
    # Find best strategy
    if results:
        best = max(results.items(), key=lambda x: x[1].get_summary_stats()['total_pips'])
        best_stats = best[1].get_summary_stats()
        print(f"\n{'=' * 80}")
        print(f"BEST STRATEGY: {best[0]}")
        print(f"{'=' * 80}")
        print(f"Total Pips: {best_stats['total_pips']:+.2f}")
        print(f"Trades: {best_stats['total_trades']}")
        print(f"Win Rate: {best_stats['win_rate']:.2f}%")
        print(f"Profit Factor: {best_stats['profit_factor']:.2f}")
        print(f"Max Drawdown: {best_stats['max_drawdown_pips']:.2f} pips")
    
    print("\n" + "=" * 80)
    print("DIRECTIONAL FILTERING ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_improved_directional()

