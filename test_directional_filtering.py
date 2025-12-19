"""
Test directional filtering with no-SL strategy (10 pip TP, exit at EOD).
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
from src.strategies import (
    strategy_always_buy,
    strategy_always_sell,
    strategy_regime_aligned,
    strategy_regime_aligned_directional,
)


def create_directional_strategy(df: pd.DataFrame) -> pd.Series:
    """
    Create a directional strategy: buy in bull, sell in bear, skip chop.
    This is essentially regime_aligned but with clear directional intent.
    """
    signals = pd.Series('flat', index=df.index)
    
    # Buy in bull regimes
    signals.loc[df['regime'] == 'bull'] = 'long'
    
    # Sell in bear regimes
    signals.loc[df['regime'] == 'bear'] = 'short'
    
    # Skip chop (no trade)
    signals.loc[df['regime'] == 'chop'] = 'flat'
    
    return signals


def create_directional_with_momentum(df: pd.DataFrame) -> pd.Series:
    """
    Directional strategy: use regime when clear, otherwise use short-term momentum.
    """
    signals = pd.Series('flat', index=df.index)
    
    # Clear regime signals
    signals.loc[df['regime'] == 'bull'] = 'long'
    signals.loc[df['regime'] == 'bear'] = 'short'
    
    # For chop, use recent momentum (5-day average of net moves)
    chop_mask = df['regime'] == 'chop'
    if 'net_from_open_pips' in df.columns:
        recent_momentum = df['net_from_open_pips'].rolling(window=5, min_periods=1).mean()
        signals.loc[chop_mask & (recent_momentum > 2)] = 'long'  # Buy if positive momentum
        signals.loc[chop_mask & (recent_momentum < -2)] = 'short'  # Sell if negative momentum
        # Otherwise stay flat
    
    return signals


def create_directional_with_adr_filter(df: pd.DataFrame, min_adr: float = 30.0) -> pd.Series:
    """
    Directional strategy with ADR filter to skip low-volatility days.
    """
    signals = create_directional_strategy(df)
    
    # Calculate ADR
    adr = calculate_adr(df, window=20)
    
    # Filter out low volatility days
    signals.loc[adr < min_adr] = 'flat'
    
    return signals


def test_directional_filtering():
    """Test various directional filtering approaches."""
    
    print("=" * 80)
    print("DIRECTIONAL FILTERING WITH NO-SL STRATEGY (10 pip TP, exit at EOD)")
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
    
    # Show regime distribution
    regime_counts = df['regime'].value_counts()
    print("Regime Distribution:")
    for regime, count in regime_counts.items():
        pct = 100 * count / len(df)
        print(f"  {regime.upper()}: {count} days ({pct:.1f}%)")
    print()
    
    # Strategy parameters
    tp_pips = 10.0
    cost_per_trade = 2.0
    
    # Define strategies to test
    strategies_to_test = {
        'Baseline: Always Buy': strategy_always_buy,
        'Baseline: Always Sell': strategy_always_sell,
        'Directional: Buy Bull / Sell Bear / Skip Chop': create_directional_strategy,
        'Directional + Momentum (fill chop)': create_directional_with_momentum,
        'Directional + ADR Filter (min 30 pips)': lambda df: create_directional_with_adr_filter(df, min_adr=30.0),
        'Directional + ADR Filter (min 40 pips)': lambda df: create_directional_with_adr_filter(df, min_adr=40.0),
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
                eod_exits = len(trades[~trades['tp_hit']])
                
                # Analyze by direction
                long_trades = trades[trades['direction'] == 'long']
                short_trades = trades[trades['direction'] == 'short']
                
                print(f"\nAdditional Stats:")
                print(f"  TP Hit Rate:     {tp_hit_rate:.2f}%")
                print(f"  EOD Exits:       {eod_exits} trades")
                
                if len(long_trades) > 0:
                    long_tp_rate = (long_trades['tp_hit']).sum() / len(long_trades) * 100
                    long_avg = long_trades['pips'].mean()
                    print(f"  Long Trades:     {len(long_trades)} | TP Rate: {long_tp_rate:.1f}% | Avg: {long_avg:.2f} pips")
                
                if len(short_trades) > 0:
                    short_tp_rate = (short_trades['tp_hit']).sum() / len(short_trades) * 100
                    short_avg = short_trades['pips'].mean()
                    print(f"  Short Trades:    {len(short_trades)} | TP Rate: {short_tp_rate:.1f}% | Avg: {short_avg:.2f} pips")
                
                # EOD exit analysis
                if eod_exits > 0:
                    eod_trades = trades[~trades['tp_hit']]
                    eod_avg = eod_trades['pips'].mean()
                    eod_wins = (eod_trades['pips'] > 0).sum()
                    eod_losses = (eod_trades['pips'] <= 0).sum()
                    print(f"  EOD Exit Avg:   {eod_avg:.2f} pips ({eod_wins} wins, {eod_losses} losses)")
            
            results[strategy_name] = result
            
        except Exception as e:
            print(f"Error running strategy {strategy_name}: {e}")
            import traceback
            traceback.print_exc()
    
    # Comprehensive comparison
    print("\n" + "=" * 80)
    print("STRATEGY COMPARISON: Directional Filtering")
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
            'Strategy': name[:50],  # Truncate long names
            'Total Pips': f"{stats['total_pips']:+.2f}",
            'Trades': stats['total_trades'],
            'TP Hit %': f"{tp_hit_rate:.1f}",
            'Win Rate %': f"{stats['win_rate']:.2f}",
            'Avg Win': f"{stats['avg_win']:.2f}",
            'Avg Loss': f"{stats['avg_loss']:.2f}",
            'Profit Factor': f"{stats['profit_factor']:.2f}",
            'Max DD (pips)': f"{stats['max_drawdown_pips']:.2f}",
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    print("\n" + comparison_df.to_string(index=False))
    
    # Highlight improvements
    print("\n" + "=" * 80)
    print("KEY IMPROVEMENTS FROM DIRECTIONAL FILTERING:")
    print("=" * 80)
    
    if 'Baseline: Always Buy' in results and 'Directional: Buy Bull / Sell Bear / Skip Chop' in results:
        baseline = results['Baseline: Always Buy'].get_summary_stats()
        directional = results['Directional: Buy Bull / Sell Bear / Skip Chop'].get_summary_stats()
        
        print(f"\nAlways Buy → Directional Filtering:")
        print(f"  Total Pips:    {baseline['total_pips']:+.2f} → {directional['total_pips']:+.2f} "
              f"({directional['total_pips'] - baseline['total_pips']:+.2f})")
        print(f"  Max Drawdown:  {baseline['max_drawdown_pips']:.2f} → {directional['max_drawdown_pips']:.2f}")
        print(f"  Trades:        {baseline['total_trades']} → {directional['total_trades']}")
    
    if 'Baseline: Always Sell' in results and 'Directional: Buy Bull / Sell Bear / Skip Chop' in results:
        baseline_sell = results['Baseline: Always Sell'].get_summary_stats()
        directional = results['Directional: Buy Bull / Sell Bear / Skip Chop'].get_summary_stats()
        
        print(f"\nAlways Sell → Directional Filtering:")
        print(f"  Total Pips:    {baseline_sell['total_pips']:+.2f} → {directional['total_pips']:+.2f} "
              f"({directional['total_pips'] - baseline_sell['total_pips']:+.2f})")
        print(f"  Max Drawdown:  {baseline_sell['max_drawdown_pips']:.2f} → {directional['max_drawdown_pips']:.2f}")
        print(f"  Profit Factor: {baseline_sell['profit_factor']:.2f} → {directional['profit_factor']:.2f}")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print("\nRecommendations:")
    print("- Compare TP hit rates between strategies")
    print("- Look for strategies that reduce EOD losses")
    print("- Higher win rate and profit factor are key")
    print("- Fewer trades but better quality is often better")
    print("=" * 80)


if __name__ == "__main__":
    test_directional_filtering()

