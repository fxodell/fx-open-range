"""
Stop Loss Optimization Test

Tests different stop loss values to find the optimal one that doesn't hurt profitability.
Compares against baseline (no stop loss).
"""

import pandas as pd
from datetime import timedelta
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.data_loader import load_eurusd_data, add_market_open_prices, price_to_pips, pips_to_price
from src.backtest_dual_market import BacktestResult, analyze_dual_market_results
from src.strategies import STRATEGIES


def backtest_dual_market_with_sl(df: pd.DataFrame,
                                 signals_df: pd.DataFrame,
                                 take_profit_pips: float,
                                 stop_loss_pips: float,
                                 cost_per_trade_pips: float = 2.0,
                                 initial_equity: float = 10000.0) -> BacktestResult:
    """
    Backtest dual market open strategy WITH stop loss support.
    
    Modified version of backtest_dual_market_open that includes stop loss.
    """
    signals_df = signals_df.reindex(df.index)
    
    trades = []
    equity_curve = []
    current_equity = initial_equity
    
    open_position = None
    
    for i in df.index:
        if i == 0:
            equity_curve.append(current_equity)
            continue
        
        row = df.loc[i]
        date = pd.Timestamp(row['Date'])
        signal_row = signals_df.loc[i]
        
        eur_signal = signal_row['eur_signal']
        eur_open_price = signal_row['eur_open_price']
        us_signal = signal_row['us_signal']
        us_open_price = signal_row['us_open_price']
        
        # Process EUR market open trade
        if eur_signal in ['long', 'short'] and eur_open_price is not None and pd.notna(eur_open_price):
            if open_position is None:
                open_position = {
                    'direction': eur_signal,
                    'entry_price': eur_open_price,
                    'entry_time': 'eur',
                    'entry_date': date,
                    'entry_index': i
                }
        
        # Check if EUR trade hit TP or SL before US open
        if open_position is not None and open_position['entry_time'] == 'eur':
            tp_hit = False
            sl_hit = False
            
            if open_position['direction'] == 'long':
                tp_price = open_position['entry_price'] + pips_to_price(take_profit_pips)
                sl_price = open_position['entry_price'] - pips_to_price(stop_loss_pips)
                
                # Conservative: check SL first if both possible
                if row['Low'] <= sl_price:
                    sl_hit = True
                elif row['High'] >= tp_price:
                    tp_hit = True
            else:  # short
                tp_price = open_position['entry_price'] - pips_to_price(take_profit_pips)
                sl_price = open_position['entry_price'] + pips_to_price(stop_loss_pips)
                
                if row['High'] >= sl_price:
                    sl_hit = True
                elif row['Low'] <= tp_price:
                    tp_hit = True
            
            if tp_hit or sl_hit:
                if tp_hit:
                    pips_result = take_profit_pips - cost_per_trade_pips
                    exit_reason = 'TP'
                else:
                    pips_result = -stop_loss_pips - cost_per_trade_pips
                    exit_reason = 'SL'
                
                trades.append({
                    'date': open_position['entry_date'],
                    'direction': open_position['direction'],
                    'entry_price': open_position['entry_price'],
                    'exit_price': open_position['entry_price'],  # Approximate
                    'exit_reason': exit_reason,
                    'session': open_position['entry_time'].upper(),
                    'pips': pips_result,
                    'tp_hit': tp_hit,
                })
                
                current_equity += pips_result * 10
                open_position = None
        
        # Process US market open trade (only if no open position)
        if open_position is None and us_signal in ['long', 'short'] and us_open_price is not None and pd.notna(us_open_price):
            open_position = {
                'direction': us_signal,
                'entry_price': us_open_price,
                'entry_time': 'us',
                'entry_date': date,
                'entry_index': i
            }
        
        # Check if US trade hit TP or SL during the day
        if open_position is not None and open_position['entry_time'] == 'us':
            tp_hit = False
            sl_hit = False
            
            if open_position['direction'] == 'long':
                tp_price = open_position['entry_price'] + pips_to_price(take_profit_pips)
                sl_price = open_position['entry_price'] - pips_to_price(stop_loss_pips)
                
                if row['Low'] <= sl_price:
                    sl_hit = True
                elif row['High'] >= tp_price:
                    tp_hit = True
            else:  # short
                tp_price = open_position['entry_price'] - pips_to_price(take_profit_pips)
                sl_price = open_position['entry_price'] + pips_to_price(stop_loss_pips)
                
                if row['High'] >= sl_price:
                    sl_hit = True
                elif row['Low'] <= tp_price:
                    tp_hit = True
            
            if tp_hit or sl_hit:
                if tp_hit:
                    pips_result = take_profit_pips - cost_per_trade_pips
                    exit_reason = 'TP'
                    if open_position['direction'] == 'long':
                        exit_price = open_position['entry_price'] + pips_to_price(take_profit_pips)
                    else:
                        exit_price = open_position['entry_price'] - pips_to_price(take_profit_pips)
                else:
                    pips_result = -stop_loss_pips - cost_per_trade_pips
                    exit_reason = 'SL'
                    if open_position['direction'] == 'long':
                        exit_price = open_position['entry_price'] - pips_to_price(stop_loss_pips)
                    else:
                        exit_price = open_position['entry_price'] + pips_to_price(stop_loss_pips)
                
                trades.append({
                    'date': open_position['entry_date'],
                    'direction': open_position['direction'],
                    'entry_price': open_position['entry_price'],
                    'exit_price': exit_price,
                    'exit_reason': exit_reason,
                    'session': open_position['entry_time'].upper(),
                    'pips': pips_result,
                    'tp_hit': tp_hit,
                })
                
                current_equity += pips_result * 10
                open_position = None
        
        # Close any open positions at end of day (EOD exit) if TP/SL not hit
        if open_position is not None:
            close_price = row['Close']
            
            if open_position['direction'] == 'long':
                pips_result = price_to_pips(close_price - open_position['entry_price']) - cost_per_trade_pips
            else:  # short
                pips_result = price_to_pips(open_position['entry_price'] - close_price) - cost_per_trade_pips
            
            trades.append({
                'date': open_position['entry_date'],
                'direction': open_position['direction'],
                'entry_price': open_position['entry_price'],
                'exit_price': close_price,
                'exit_reason': 'EOD',
                'session': open_position['entry_time'].upper(),
                'pips': pips_result,
                'tp_hit': False,
            })
            
            current_equity += pips_result * 10
            open_position = None
        
        equity_curve.append(current_equity)
    
    # Close any remaining open position at the end
    if open_position is not None:
        last_row = df.iloc[-1]
        close_price = last_row['Close']
        
        if open_position['direction'] == 'long':
            pips_result = price_to_pips(close_price - open_position['entry_price']) - cost_per_trade_pips
        else:
            pips_result = price_to_pips(open_position['entry_price'] - close_price) - cost_per_trade_pips
        
        trades.append({
            'date': open_position['entry_date'],
            'direction': open_position['direction'],
            'entry_price': open_position['entry_price'],
            'exit_price': close_price,
            'exit_reason': 'EOD',
            'session': open_position['entry_time'].upper(),
            'pips': pips_result,
            'tp_hit': False,
        })
        
        current_equity += pips_result * 10
        equity_curve[-1] = current_equity
    
    trades_df = pd.DataFrame(trades)
    equity_series = pd.Series(equity_curve, index=df.index)
    
    return BacktestResult(trades_df, equity_series)


def run_stop_loss_optimization():
    """Test different stop loss values and compare to baseline."""
    print("=" * 80)
    print("STOP LOSS OPTIMIZATION TEST")
    print("=" * 80)
    
    # Load data
    data_file = Path(__file__).parent / "data" / "eur_usd_long_term.csv"
    print(f"\nLoading data from: {data_file}")
    
    df = load_eurusd_data(str(data_file))
    
    # Filter to last 12 months
    end_date = df['Date'].max()
    start_date = end_date - timedelta(days=365)
    df_12month = df[df['Date'] >= start_date].copy()
    df_12month = df_12month.reset_index(drop=True)
    
    print(f"12-Month Period: {df_12month['Date'].min()} to {df_12month['Date'].max()}")
    print(f"Trading days: {len(df_12month)}")
    
    # Parameters
    tp_pips = 10.0
    cost_per_trade = 2.0
    
    # Prepare data
    print("\nPreparing data with market open prices...")
    df_with_opens = add_market_open_prices(df_12month.copy())
    
    # Generate signals
    dual_signals_df = STRATEGIES['dual_market_open'](df_with_opens)
    
    # Test stop loss values (including None for baseline)
    stop_loss_values = [None, 5, 10, 15, 20, 25, 30, 40, 50, 60, 80, 100]
    
    results = []
    
    # Import baseline backtest function
    from src.backtest_dual_market import backtest_dual_market_open
    
    print("\n" + "=" * 80)
    print("RUNNING TESTS...")
    print("=" * 80)
    
    for sl_pips in stop_loss_values:
        sl_label = "None (EOD)" if sl_pips is None else f"{sl_pips}"
        print(f"\nTesting Stop Loss: {sl_label} pips...")
        
        if sl_pips is None:
            # Baseline: no stop loss
            result = backtest_dual_market_open(
                df_with_opens,
                dual_signals_df,
                take_profit_pips=tp_pips,
                cost_per_trade_pips=cost_per_trade,
            )
        else:
            # With stop loss
            result = backtest_dual_market_with_sl(
                df_with_opens,
                dual_signals_df,
                take_profit_pips=tp_pips,
                stop_loss_pips=sl_pips,
                cost_per_trade_pips=cost_per_trade,
            )
        
        stats = analyze_dual_market_results(result)
        
        # Count exit reasons
        trades_df = result.trades
        tp_exits = len(trades_df[trades_df.get('exit_reason') == 'TP']) if 'exit_reason' in trades_df.columns else 0
        sl_exits = len(trades_df[trades_df.get('exit_reason') == 'SL']) if 'exit_reason' in trades_df.columns else 0
        eod_exits = len(trades_df[trades_df.get('exit_reason') == 'EOD']) if 'exit_reason' in trades_df.columns else len(trades_df)
        
        results.append({
            'Stop Loss (pips)': sl_label,
            'Total Pips': stats['total_pips'],
            'Total Trades': stats['total_trades'],
            'Win Rate %': stats['win_rate'],
            'Avg Pips/Trade': stats['avg_pips_per_trade'],
            'Profit Factor': stats['profit_factor'],
            'Max DD (pips)': stats['max_drawdown_pips'],
            'Sharpe': stats['sharpe'],
            'TP Exits': tp_exits,
            'SL Exits': sl_exits,
            'EOD Exits': eod_exits,
        })
    
    # Create comparison DataFrame
    results_df = pd.DataFrame(results)
    
    print("\n" + "=" * 80)
    print("STOP LOSS OPTIMIZATION RESULTS")
    print("=" * 80)
    print("\nComparison Table:")
    print(results_df.to_string(index=False))
    
    # Find baseline (no stop loss)
    baseline = results_df[results_df['Stop Loss (pips)'] == 'None (EOD)'].iloc[0]
    baseline_pips = baseline['Total Pips']
    
    print("\n" + "=" * 80)
    print("ANALYSIS: Stop Loss vs Baseline (No SL)")
    print("=" * 80)
    
    # Filter to stop loss results (exclude baseline)
    sl_results = results_df[results_df['Stop Loss (pips)'] != 'None (EOD)'].copy()
    sl_results['Pips Diff'] = sl_results['Total Pips'] - baseline_pips
    sl_results['Pips Diff %'] = (sl_results['Pips Diff'] / abs(baseline_pips)) * 100
    sl_results['Better?'] = sl_results['Total Pips'] >= baseline_pips * 0.95  # Within 5% considered acceptable
    
    print("\nStop Loss Impact on Profitability:")
    print(sl_results[['Stop Loss (pips)', 'Total Pips', 'Pips Diff', 'Pips Diff %', 
                     'Win Rate %', 'SL Exits', 'Better?']].to_string(index=False))
    
    # Find optimal stop loss
    # Criteria: at least 95% of baseline profit (or at least still profitable if that's not possible)
    acceptable = sl_results[sl_results['Total Pips'] >= baseline_pips * 0.95]
    
    # If no stop loss meets 95% criteria, find the best one that's still profitable
    if len(acceptable) == 0:
        acceptable = sl_results[sl_results['Total Pips'] > 0]
    
    if len(acceptable) > 0:
        # Sort by total pips (descending), then by win rate, then by lower max drawdown
        optimal = acceptable.sort_values(
            ['Total Pips', 'Win Rate %', 'Max DD (pips)'],
            ascending=[False, False, True]
        ).iloc[0]
        
        print("\n" + "=" * 80)
        print("RECOMMENDED STOP LOSS")
        print("=" * 80)
        print(f"\nOptimal Stop Loss: {optimal['Stop Loss (pips)']} pips")
        print(f"\nPerformance:")
        print(f"  Total Pips: {optimal['Total Pips']:.2f} (vs {baseline_pips:.2f} baseline, {optimal['Pips Diff']:+.2f} diff)")
        print(f"  Win Rate: {optimal['Win Rate %']:.2f}% (vs {baseline['Win Rate %']:.2f}% baseline)")
        print(f"  Avg Pips/Trade: {optimal['Avg Pips/Trade']:.2f} (vs {baseline['Avg Pips/Trade']:.2f} baseline)")
        print(f"  Max Drawdown: {optimal['Max DD (pips)']:.2f} pips (vs {baseline['Max DD (pips)']:.2f} baseline)")
        print(f"  Total Trades: {optimal['Total Trades']} (vs {baseline['Total Trades']} baseline)")
        print(f"  SL Exits: {optimal['SL Exits']} trades")
        print(f"  TP Exits: {optimal['TP Exits']} trades")
        print(f"  EOD Exits: {optimal['EOD Exits']} trades")
    else:
        print("\n" + "=" * 80)
        print("RECOMMENDATION")
        print("=" * 80)
        print("\nNo stop loss value maintains at least 95% of baseline profitability.")
        print("Recommendation: Keep current EOD exit strategy (no stop loss).")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nBaseline (No Stop Loss):")
    print(f"  Total Pips: {baseline_pips:.2f}")
    print(f"  Win Rate: {baseline['Win Rate %']:.2f}%")
    print(f"  Avg Pips/Trade: {baseline['Avg Pips/Trade']:.2f}")
    print(f"  Max Drawdown: {baseline['Max DD (pips)']:.2f} pips")
    
    return results_df, baseline


if __name__ == "__main__":
    results_df, baseline = run_stop_loss_optimization()

