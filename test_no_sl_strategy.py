"""
Test strategies with TP only (no stop loss, exit at EOD).
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pandas as pd
from src.data_loader import load_eurusd_data
from src.core_analysis import calculate_daily_metrics, calculate_adr
from src.regime import calculate_moving_averages, classify_regime
from src.backtest_no_sl import backtest_strategy_no_sl
from src.strategies import (
    strategy_always_buy,
    strategy_always_sell,
    strategy_regime_aligned_directional,
    strategy_regime_aligned,
)


def test_no_sl_strategies():
    """Test strategies with 10 pip TP, no stop loss, exit at EOD."""
    
    print("=" * 80)
    print("TESTING: 10 PIP TP, NO STOP LOSS, EXIT AT END OF DAY")
    print("=" * 80)
    
    # Load data
    data_file = project_root / "data" / "eur_usd.csv"
    print(f"\nLoading data from: {data_file}")
    
    df = load_eurusd_data(str(data_file))
    print(f"Loaded {len(df)} days of data")
    print(f"Date range: {df['Date'].min()} to {df['Date'].max()}\n")
    
    # Calculate features
    df = calculate_daily_metrics(df)
    df = calculate_moving_averages(df, periods=[20, 50, 100, 200])
    df = classify_regime(df)
    
    # Strategy parameters
    tp_pips = 10.0  # 10 pip take profit
    cost_per_trade = 2.0  # 2 pips cost
    
    strategies_to_test = {
        'Always Buy': strategy_always_buy,
        'Always Sell': strategy_always_sell,
        'Regime Aligned (with chop filter)': strategy_regime_aligned,
        'Regime Directional (always trade)': strategy_regime_aligned_directional,
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
            
            # Run backtest with NO STOP LOSS
            result = backtest_strategy_no_sl(
                df,
                signals,
                take_profit_pips=tp_pips,
                cost_per_trade_pips=cost_per_trade,
            )
            
            # Print summary
            result.print_summary()
            
            # Additional stats for TP-only strategy
            trades = result.trades
            if len(trades) > 0:
                tp_hit_rate = (trades['tp_hit']).sum() / len(trades) * 100
                eod_exits = len(trades[~trades['tp_hit']])
                eod_avg_pips = trades[~trades['tp_hit']]['pips'].mean() if eod_exits > 0 else 0.0
                
                print(f"\nAdditional Stats (TP-only strategy):")
                print(f"  TP Hit Rate:     {tp_hit_rate:.2f}%")
                print(f"  EOD Exits:       {eod_exits} trades")
                print(f"  Avg Pips (EOD):  {eod_avg_pips:.2f} pips")
                
                # Show distribution of EOD exit results
                if eod_exits > 0:
                    eod_trades = trades[~trades['tp_hit']]
                    wins = (eod_trades['pips'] > 0).sum()
                    losses = (eod_trades['pips'] <= 0).sum()
                    print(f"  EOD Wins:        {wins} ({wins/eod_exits*100:.1f}%)")
                    print(f"  EOD Losses:      {losses} ({losses/eod_exits*100:.1f}%)")
            
            results[strategy_name] = result
            
        except Exception as e:
            print(f"Error running strategy {strategy_name}: {e}")
            import traceback
            traceback.print_exc()
    
    # Comparison table
    print("\n" + "=" * 80)
    print("STRATEGY COMPARISON (10 pip TP, no SL, EOD exit)")
    print("=" * 80)
    
    comparison_data = []
    for name, result in results.items():
        stats = result.get_summary_stats()
        trades = result.trades
        tp_hit_rate = (trades['tp_hit']).sum() / len(trades) * 100 if len(trades) > 0 else 0.0
        
        comparison_data.append({
            'Strategy': name,
            'Total Pips': f"{stats['total_pips']:.2f}",
            'Trades': stats['total_trades'],
            'Win Rate %': f"{stats['win_rate']:.2f}",
            'TP Hit Rate %': f"{tp_hit_rate:.2f}",
            'Avg Win': f"{stats['avg_win']:.2f}",
            'Avg Loss': f"{stats['avg_loss']:.2f}",
            'Profit Factor': f"{stats['profit_factor']:.2f}",
            'Max DD (pips)': f"{stats['max_drawdown_pips']:.2f}",
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    print("\n" + comparison_df.to_string(index=False))
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print("\nKey Insights:")
    print("- TP Hit Rate shows % of trades that hit 10 pip target before EOD")
    print("- EOD Exits are trades closed at end of day (may be winning or losing)")
    print("- No stop loss means trades can lose more than TP size")
    print("- This approach aims to capture small moves in the daily range")
    print("=" * 80)


if __name__ == "__main__":
    test_no_sl_strategies()

