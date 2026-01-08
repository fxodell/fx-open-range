"""
12-Month Backtest for Dual Market Open Strategy

This script runs a 12-month backtest comparison between the single daily open
strategy and the dual market open strategy.
"""

import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data_loader import load_eurusd_data, add_market_open_prices
from src.backtest_no_sl import backtest_strategy_no_sl
from src.backtest_dual_market import backtest_dual_market_open, analyze_dual_market_results
from src.strategies import STRATEGIES


def run_12month_backtest():
    """Run 12-month backtest comparison."""
    print("=" * 80)
    print("12-MONTH BACKTEST: Dual Market Open Strategy Comparison")
    print("=" * 80)
    
    # Load data from long-term file
    data_file = project_root / "data" / "eur_usd_long_term.csv"
    print(f"\nLoading data from: {data_file}")
    
    df = load_eurusd_data(str(data_file))
    print(f"Loaded {len(df)} days of data")
    print(f"Full date range: {df['Date'].min()} to {df['Date'].max()}")
    
    # Filter to last 12 months
    end_date = df['Date'].max()
    start_date = end_date - timedelta(days=365)
    
    df_12month = df[df['Date'] >= start_date].copy()
    df_12month = df_12month.reset_index(drop=True)
    
    print(f"\n12-Month Period: {df_12month['Date'].min()} to {df_12month['Date'].max()}")
    print(f"Trading days: {len(df_12month)}")
    
    # Parameters matching live trading (10 pips TP, no SL, EOD exit)
    tp_pips = 10.0
    cost_per_trade = 2.0  # 2 pips per trade (spread + commission)
    
    # Prepare data with market open prices
    print("\nPreparing data with market open prices...")
    df_with_opens = add_market_open_prices(df_12month.copy())
    
    # Run single daily open strategy (baseline)
    print("\n" + "=" * 80)
    print("BASELINE: Single Daily Open Strategy (22:00 UTC)")
    print("=" * 80)
    
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
    print("\n" + "=" * 80)
    print("DUAL MARKET OPEN STRATEGY (EUR 8:00 UTC + US 13:00 UTC)")
    print("=" * 80)
    
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
    print("\n" + "=" * 80)
    print("SESSION-SPECIFIC METRICS")
    print("=" * 80)
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
    print("STRATEGY COMPARISON (12-Month Period)")
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
    print("\n" + "=" * 80)
    print("PERFORMANCE IMPROVEMENT")
    print("=" * 80)
    pips_improvement = dual_stats['total_pips'] - single_stats['total_pips']
    pips_improvement_pct = (pips_improvement / abs(single_stats['total_pips'])) * 100 if single_stats['total_pips'] != 0 else 0
    trades_improvement = dual_stats['total_trades'] - single_stats['total_trades']
    
    print(f"Total Pips Improvement: {pips_improvement:+.2f} pips ({pips_improvement_pct:+.2f}%)")
    print(f"Additional Trades: {trades_improvement:+d}")
    print(f"Win Rate Change: {dual_stats['win_rate'] - single_stats['win_rate']:+.2f}%")
    print(f"Avg Pips/Trade Change: {dual_stats['avg_pips_per_trade'] - single_stats['avg_pips_per_trade']:+.2f} pips")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    if pips_improvement > 0:
        print(f"✓ Dual Market Open strategy outperformed by {pips_improvement:.2f} pips")
    else:
        print(f"✗ Dual Market Open strategy underperformed by {abs(pips_improvement):.2f} pips")
    
    print(f"\nDual Market Open generated {trades_improvement} additional trades")
    print(f"EUR session contributed {dual_stats['eur_pips']:.2f} pips ({dual_stats['eur_trades']} trades)")
    print(f"US session contributed {dual_stats['us_pips']:.2f} pips ({dual_stats['us_trades']} trades)")
    
    print("\n" + "=" * 80)
    print("IMPORTANT DISCLAIMER:")
    print("These are historical backtests with no guarantee of future performance.")
    print("Risk management is critical. Consider sizing positions conservatively")
    print("(e.g., well under 1% risk per trade).")
    print("=" * 80)
    
    return {
        'single': single_result,
        'dual': dual_result,
        'single_stats': single_stats,
        'dual_stats': dual_stats,
    }


if __name__ == "__main__":
    results = run_12month_backtest()

