"""
Main analysis script for EUR/USD open-range strategies.
"""

import pandas as pd
import numpy as np
from pathlib import Path

from .data_loader import load_eurusd_data
from .core_analysis import (
    calculate_daily_metrics,
    calculate_distribution_stats,
    analyze_range_distribution,
    calculate_adr,
    calculate_mfe_mae,
)
from .regime import (
    calculate_moving_averages,
    calculate_momentum,
    classify_regime,
    analyze_regime_performance,
)
from .backtest import backtest_strategy, BacktestResult
from .backtest_no_sl import backtest_strategy_no_sl
from .backtest_dual_market import backtest_dual_market_open, analyze_dual_market_results
from .strategies import STRATEGIES
from .data_loader import add_market_open_prices


def run_core_analysis(df: pd.DataFrame):
    """Run and display core range and distribution analysis."""
    print("\n" + "=" * 80)
    print("CORE ANALYSIS: Daily Range and Open-Based Moves")
    print("=" * 80)
    
    # Calculate daily metrics
    df = calculate_daily_metrics(df)
    
    # Distribution statistics
    metrics_to_analyze = [
        'range_pips',
        'up_from_open_pips',
        'down_from_open_pips',
        'net_from_open_pips',
    ]
    
    print("\nDistribution Statistics:")
    print("-" * 80)
    for metric in metrics_to_analyze:
        stats = calculate_distribution_stats(df, metric)
        print(f"\n{metric.replace('_', ' ').title()}:")
        print(f"  Count:    {stats['count']}")
        print(f"  Mean:     {stats['mean']:.2f} pips")
        print(f"  Median:   {stats['median']:.2f} pips")
        print(f"  Std:      {stats['std']:.2f} pips")
        print(f"  Min:      {stats['min']:.2f} pips")
        print(f"  Max:      {stats['max']:.2f} pips")
        print(f"  P25:      {stats['p25']:.2f} pips")
        print(f"  P50:      {stats['p50']:.2f} pips")
        print(f"  P75:      {stats['p75']:.2f} pips")
        print(f"  P90:      {stats['p90']:.2f} pips")
    
    # Pip threshold analysis
    print("\n" + "-" * 80)
    print("Frequency of Pip Moves from Open:")
    print("-" * 80)
    threshold_df = analyze_range_distribution(df)
    print(threshold_df.to_string(index=False))
    
    # MFE/MAE analysis
    print("\n" + "-" * 80)
    print("Maximum Favorable/Adverse Excursion from Open:")
    print("-" * 80)
    mfe_long, mae_long = calculate_mfe_mae(df, direction='long')
    mfe_short, mae_short = calculate_mfe_mae(df, direction='short')
    
    print(f"\nLong trades (assuming buy at open):")
    print(f"  MFE mean:  {mfe_long.mean():.2f} pips")
    print(f"  MFE median: {mfe_long.median():.2f} pips")
    print(f"  MAE mean:  {mae_long.mean():.2f} pips")
    print(f"  MAE median: {mae_long.median():.2f} pips")
    
    print(f"\nShort trades (assuming sell at open):")
    print(f"  MFE mean:  {mfe_short.mean():.2f} pips")
    print(f"  MFE median: {mfe_short.median():.2f} pips")
    print(f"  MAE mean:  {mae_short.mean():.2f} pips")
    print(f"  MAE median: {mae_short.median():.2f} pips")
    
    return df


def run_regime_analysis(df: pd.DataFrame):
    """Run and display regime detection and analysis."""
    print("\n" + "=" * 80)
    print("MARKET REGIME ANALYSIS")
    print("=" * 80)
    
    # Calculate moving averages and momentum
    df = calculate_moving_averages(df, periods=[20, 50, 100, 200])
    df = calculate_momentum(df, periods=[1, 3, 6])
    
    # Classify regime
    df = classify_regime(df, sma_short=50, sma_long=200)
    
    # Regime distribution
    regime_counts = df['regime'].value_counts()
    print("\nRegime Distribution:")
    print("-" * 80)
    for regime, count in regime_counts.items():
        pct = 100 * count / len(df)
        print(f"{regime.upper()}: {count} days ({pct:.1f}%)")
    
    # Regime performance analysis
    print("\n" + "-" * 80)
    print("Performance Metrics by Regime:")
    print("-" * 80)
    regime_perf = analyze_regime_performance(df)
    print(regime_perf.to_string(index=False))
    
    return df


def run_backtests(df: pd.DataFrame):
    """Run backtests for different strategies."""
    print("\n" + "=" * 80)
    print("STRATEGY BACKTESTS")
    print("=" * 80)
    
    # Standard TP/SL parameters (in pips)
    tp_pips = 20.0
    sl_pips = 20.0
    cost_per_trade = 2.0  # 2 pips per trade (spread + commission)
    
    results = {}
    
    # Test each strategy
    for strategy_name, strategy_func in STRATEGIES.items():
        print(f"\n{'=' * 60}")
        print(f"Strategy: {strategy_name.replace('_', ' ').title()}")
        print(f"{'=' * 60}")
        
        try:
            # Generate signals
            signals = strategy_func(df)
            
            # Count signals
            signal_counts = signals.value_counts()
            print(f"\nSignal Distribution:")
            for sig, count in signal_counts.items():
                print(f"  {sig}: {count}")
            
            # Run backtest
            result = backtest_strategy(
                df,
                signals,
                take_profit_pips=tp_pips,
                stop_loss_pips=sl_pips,
                cost_per_trade_pips=cost_per_trade,
            )
            
            result.print_summary()
            results[strategy_name] = result
            
        except Exception as e:
            print(f"Error running strategy {strategy_name}: {e}")
            import traceback
            traceback.print_exc()
    
    # Compare strategies
    print("\n" + "=" * 80)
    print("STRATEGY COMPARISON")
    print("=" * 80)
    
    comparison_data = []
    for name, result in results.items():
        stats = result.get_summary_stats()
        comparison_data.append({
            'Strategy': name.replace('_', ' ').title(),
            'Total Pips': f"{stats['total_pips']:.2f}",
            'Trades': stats['total_trades'],
            'Win Rate %': f"{stats['win_rate']:.2f}",
            'Profit Factor': f"{stats['profit_factor']:.2f}",
            'Max DD (pips)': f"{stats['max_drawdown_pips']:.2f}",
            'Sharpe': f"{stats['sharpe']:.2f}",
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    print("\n" + comparison_df.to_string(index=False))
    
    return results


def run_dual_market_comparison(df: pd.DataFrame):
    """
    Compare single daily open strategy vs dual market open strategy.
    
    This function runs both strategies with the same parameters and compares
    their performance metrics.
    """
    print("\n" + "=" * 80)
    print("DUAL MARKET OPEN STRATEGY COMPARISON")
    print("=" * 80)
    
    # Parameters matching live trading (10 pips TP, no SL, EOD exit)
    tp_pips = 10.0
    cost_per_trade = 2.0  # 2 pips per trade (spread + commission)
    
    # Prepare data with market open prices
    print("\nPreparing data with market open prices...")
    df_with_opens = add_market_open_prices(df.copy())
    
    # Run single daily open strategy (baseline)
    print("\n" + "-" * 80)
    print("BASELINE: Single Daily Open Strategy (22:00 UTC)")
    print("-" * 80)
    
    single_signals = STRATEGIES['price_trend_sma20'](df_with_opens)
    single_result = backtest_strategy_no_sl(
        df_with_opens,
        single_signals,
        take_profit_pips=tp_pips,
        cost_per_trade_pips=cost_per_trade,
    )
    
    single_stats = single_result.get_summary_stats()
    single_result.print_summary()
    
    # Run dual market open strategy
    print("\n" + "-" * 80)
    print("DUAL MARKET OPEN STRATEGY (EUR 8:00 UTC + US 13:00 UTC)")
    print("-" * 80)
    
    dual_signals_df = STRATEGIES['dual_market_open'](df_with_opens)
    dual_result = backtest_dual_market_open(
        df_with_opens,
        dual_signals_df,
        take_profit_pips=tp_pips,
        cost_per_trade_pips=cost_per_trade,
    )
    
    dual_stats = analyze_dual_market_results(dual_result)
    dual_result.print_summary()
    
    # Print session-specific metrics
    print("\n" + "-" * 80)
    print("Session-Specific Metrics:")
    print("-" * 80)
    print(f"EUR Market Trades: {dual_stats['eur_trades']}")
    print(f"EUR Market Pips: {dual_stats['eur_pips']:.2f}")
    print(f"EUR Market Win Rate: {dual_stats['eur_win_rate']:.2f}%")
    print(f"\nUS Market Trades: {dual_stats['us_trades']}")
    print(f"US Market Pips: {dual_stats['us_pips']:.2f}")
    print(f"US Market Win Rate: {dual_stats['us_win_rate']:.2f}%")
    print(f"\nDays with 2 trades: {dual_stats['days_with_2_trades']}")
    print(f"Days with 1 trade: {dual_stats['days_with_1_trade']}")
    print(f"Days with 0 trades: {dual_stats['days_with_0_trades']}")
    
    # Comparison table
    print("\n" + "=" * 80)
    print("STRATEGY COMPARISON")
    print("=" * 80)
    
    comparison_data = []
    comparison_data.append({
        'Strategy': 'Single Daily Open',
        'Total Pips': f"{single_stats['total_pips']:.2f}",
        'Trades': single_stats['total_trades'],
        'Win Rate %': f"{single_stats['win_rate']:.2f}",
        'Avg Pips/Trade': f"{single_stats['avg_pips_per_trade']:.2f}",
        'Profit Factor': f"{single_stats['profit_factor']:.2f}",
        'Max DD (pips)': f"{single_stats['max_drawdown_pips']:.2f}",
        'Sharpe': f"{single_stats['sharpe']:.2f}",
    })
    comparison_data.append({
        'Strategy': 'Dual Market Open',
        'Total Pips': f"{dual_stats['total_pips']:.2f}",
        'Trades': dual_stats['total_trades'],
        'Win Rate %': f"{dual_stats['win_rate']:.2f}",
        'Avg Pips/Trade': f"{dual_stats['avg_pips_per_trade']:.2f}",
        'Profit Factor': f"{dual_stats['profit_factor']:.2f}",
        'Max DD (pips)': f"{dual_stats['max_drawdown_pips']:.2f}",
        'Sharpe': f"{dual_stats['sharpe']:.2f}",
    })
    
    comparison_df = pd.DataFrame(comparison_data)
    print("\n" + comparison_df.to_string(index=False))
    
    # Calculate improvement
    print("\n" + "-" * 80)
    print("Performance Improvement:")
    print("-" * 80)
    pips_improvement = dual_stats['total_pips'] - single_stats['total_pips']
    pips_improvement_pct = (pips_improvement / abs(single_stats['total_pips'])) * 100 if single_stats['total_pips'] != 0 else 0
    print(f"Total Pips Improvement: {pips_improvement:+.2f} pips ({pips_improvement_pct:+.2f}%)")
    print(f"Additional Trades: {dual_stats['total_trades'] - single_stats['total_trades']}")
    
    return {
        'single': single_result,
        'dual': dual_result,
        'single_stats': single_stats,
        'dual_stats': dual_stats,
    }


def main():
    """Main execution function."""
    print("FX Open-Range Lab")
    print("EUR/USD Trade-at-Open Strategy Analysis")
    print("=" * 80)
    
    # Load data
    data_file = Path(__file__).parent.parent / "data" / "eur_usd.csv"
    print(f"\nLoading data from: {data_file}")
    
    df = load_eurusd_data(str(data_file))
    print(f"Loaded {len(df)} days of data")
    print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
    
    # Run core analysis
    df = run_core_analysis(df)
    
    # Run regime analysis
    df = run_regime_analysis(df)
    
    # Run backtests
    results = run_backtests(df)
    
    # Run dual market open comparison
    comparison_results = run_dual_market_comparison(df)
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print("\nIMPORTANT DISCLAIMER:")
    print("These are historical backtests with no guarantee of future performance.")
    print("Risk management is critical. Consider sizing positions conservatively")
    print("(e.g., well under 1% risk per trade).")
    print("=" * 80)


if __name__ == "__main__":
    main()

