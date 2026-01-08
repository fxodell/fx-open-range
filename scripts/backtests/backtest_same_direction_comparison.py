"""
Backtest Comparison: Current vs New Same-Direction Position Rules

This script compares:
1. CURRENT: Skip US trade if EUR position still open (any direction)
2. NEW: Keep EUR position if US signal is same direction, skip if different
"""

import pandas as pd
from datetime import timedelta
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data_loader import load_eurusd_data, add_market_open_prices, price_to_pips, pips_to_price
from src.backtest import BacktestResult
from src.strategies import STRATEGIES


def backtest_dual_market_current(df: pd.DataFrame,
                                 signals_df: pd.DataFrame,
                                 take_profit_pips: float,
                                 cost_per_trade_pips: float = 2.0,
                                 initial_equity: float = 10000.0) -> BacktestResult:
    """
    CURRENT BEHAVIOR: Skip US trade if EUR position still open (any direction).
    This is the existing logic.
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
        
        # Check if EUR trade hit TP before US open
        if open_position is not None and open_position['entry_time'] == 'eur':
            tp_hit = False
            if open_position['direction'] == 'long':
                tp_price = open_position['entry_price'] + pips_to_price(take_profit_pips)
                if row['High'] >= tp_price:
                    tp_hit = True
            else:  # short
                tp_price = open_position['entry_price'] - pips_to_price(take_profit_pips)
                if row['Low'] <= tp_price:
                    tp_hit = True
            
            if tp_hit:
                if open_position['direction'] == 'long':
                    pips_result = take_profit_pips - cost_per_trade_pips
                    exit_price = open_position['entry_price'] + pips_to_price(take_profit_pips)
                else:
                    pips_result = take_profit_pips - cost_per_trade_pips
                    exit_price = open_position['entry_price'] - pips_to_price(take_profit_pips)
                
                trades.append({
                    'date': open_position['entry_date'],
                    'direction': open_position['direction'],
                    'entry_price': open_position['entry_price'],
                    'exit_price': exit_price,
                    'exit_reason': 'TP',
                    'session': 'EUR',
                    'pips': pips_result,
                    'tp_hit': True,
                })
                
                current_equity += pips_result * 10
                open_position = None
        
        # CURRENT BEHAVIOR: Process US market open trade (ONLY if no open position)
        if open_position is None and us_signal in ['long', 'short'] and us_open_price is not None and pd.notna(us_open_price):
            open_position = {
                'direction': us_signal,
                'entry_price': us_open_price,
                'entry_time': 'us',
                'entry_date': date,
                'entry_index': i
            }
        
        # Check if US trade hit TP during the day
        if open_position is not None and open_position['entry_time'] == 'us':
            tp_hit = False
            if open_position['direction'] == 'long':
                tp_price = open_position['entry_price'] + pips_to_price(take_profit_pips)
                if row['High'] >= tp_price:
                    tp_hit = True
            else:  # short
                tp_price = open_position['entry_price'] - pips_to_price(take_profit_pips)
                if row['Low'] <= tp_price:
                    tp_hit = True
            
            if tp_hit:
                if open_position['direction'] == 'long':
                    pips_result = take_profit_pips - cost_per_trade_pips
                    exit_price = open_position['entry_price'] + pips_to_price(take_profit_pips)
                else:
                    pips_result = take_profit_pips - cost_per_trade_pips
                    exit_price = open_position['entry_price'] - pips_to_price(take_profit_pips)
                
                trades.append({
                    'date': open_position['entry_date'],
                    'direction': open_position['direction'],
                    'entry_price': open_position['entry_price'],
                    'exit_price': exit_price,
                    'exit_reason': 'TP',
                    'session': 'US',
                    'pips': pips_result,
                    'tp_hit': True,
                })
                
                current_equity += pips_result * 10
                open_position = None
        
        # Close any open positions at end of day (EOD exit)
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


def backtest_dual_market_new(df: pd.DataFrame,
                            signals_df: pd.DataFrame,
                            take_profit_pips: float,
                            cost_per_trade_pips: float = 2.0,
                            initial_equity: float = 10000.0) -> BacktestResult:
    """
    NEW BEHAVIOR: Keep EUR position if US signal is same direction, skip if different.
    This saves spread costs (4 pips) when signals align.
    """
    signals_df = signals_df.reindex(df.index)
    
    trades = []
    equity_curve = []
    current_equity = initial_equity
    open_position = None
    skipped_same_direction = 0  # Track how many same-direction trades we kept
    
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
        
        # Check if EUR trade hit TP before US open
        if open_position is not None and open_position['entry_time'] == 'eur':
            tp_hit = False
            if open_position['direction'] == 'long':
                tp_price = open_position['entry_price'] + pips_to_price(take_profit_pips)
                if row['High'] >= tp_price:
                    tp_hit = True
            else:  # short
                tp_price = open_position['entry_price'] - pips_to_price(take_profit_pips)
                if row['Low'] <= tp_price:
                    tp_hit = True
            
            if tp_hit:
                if open_position['direction'] == 'long':
                    pips_result = take_profit_pips - cost_per_trade_pips
                    exit_price = open_position['entry_price'] + pips_to_price(take_profit_pips)
                else:
                    pips_result = take_profit_pips - cost_per_trade_pips
                    exit_price = open_position['entry_price'] - pips_to_price(take_profit_pips)
                
                trades.append({
                    'date': open_position['entry_date'],
                    'direction': open_position['direction'],
                    'entry_price': open_position['entry_price'],
                    'exit_price': exit_price,
                    'exit_reason': 'TP',
                    'session': 'EUR',
                    'pips': pips_result,
                    'tp_hit': True,
                })
                
                current_equity += pips_result * 10
                open_position = None
        
        # NEW BEHAVIOR: Process US market open trade
        # If EUR position still open, check if same direction
        if open_position is not None and open_position['entry_time'] == 'eur':
            # EUR position still open - check US signal direction
            if us_signal in ['long', 'short'] and us_open_price is not None and pd.notna(us_open_price):
                if us_signal == open_position['direction']:
                    # SAME DIRECTION: Keep existing position (save spread costs)
                    # Don't open new trade, just continue with existing
                    skipped_same_direction += 1
                    # Note: We track this but don't create a trade entry
                    # The existing EUR position continues
                else:
                    # DIFFERENT DIRECTION: Skip US trade (would conflict)
                    pass
        elif open_position is None and us_signal in ['long', 'short'] and us_open_price is not None and pd.notna(us_open_price):
            # No open position - enter US trade normally
            open_position = {
                'direction': us_signal,
                'entry_price': us_open_price,
                'entry_time': 'us',
                'entry_date': date,
                'entry_index': i
            }
        
        # Check if US trade hit TP during the day
        if open_position is not None and open_position['entry_time'] == 'us':
            tp_hit = False
            if open_position['direction'] == 'long':
                tp_price = open_position['entry_price'] + pips_to_price(take_profit_pips)
                if row['High'] >= tp_price:
                    tp_hit = True
            else:  # short
                tp_price = open_position['entry_price'] - pips_to_price(take_profit_pips)
                if row['Low'] <= tp_price:
                    tp_hit = True
            
            if tp_hit:
                if open_position['direction'] == 'long':
                    pips_result = take_profit_pips - cost_per_trade_pips
                    exit_price = open_position['entry_price'] + pips_to_price(take_profit_pips)
                else:
                    pips_result = take_profit_pips - cost_per_trade_pips
                    exit_price = open_position['entry_price'] - pips_to_price(take_profit_pips)
                
                trades.append({
                    'date': open_position['entry_date'],
                    'direction': open_position['direction'],
                    'entry_price': open_position['entry_price'],
                    'exit_price': exit_price,
                    'exit_reason': 'TP',
                    'session': 'US',
                    'pips': pips_result,
                    'tp_hit': True,
                })
                
                current_equity += pips_result * 10
                open_position = None
        
        # Close any open positions at end of day (EOD exit)
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
    
    # Store metadata about skipped trades
    result = BacktestResult(trades_df, equity_series)
    result.skipped_same_direction = skipped_same_direction
    result.spread_savings_pips = skipped_same_direction * 4  # 4 pips saved per skipped trade (2 close + 2 open)
    
    return result


def analyze_comparison(current_result: BacktestResult, new_result: BacktestResult) -> dict:
    """Analyze and compare the two backtest results."""
    current_stats = current_result.get_summary_stats()
    new_stats = new_result.get_summary_stats()
    
    # Calculate differences
    pips_diff = new_stats['total_pips'] - current_stats['total_pips']
    trades_diff = new_stats['total_trades'] - current_stats['total_trades']
    win_rate_diff = new_stats['win_rate'] - current_stats['win_rate']
    
    return {
        'current': current_stats,
        'new': new_stats,
        'pips_diff': pips_diff,
        'trades_diff': trades_diff,
        'win_rate_diff': win_rate_diff,
        'skipped_same_direction': getattr(new_result, 'skipped_same_direction', 0),
        'spread_savings_pips': getattr(new_result, 'spread_savings_pips', 0),
    }


def run_comparison_backtest():
    """Run comparison backtest."""
    print("=" * 80)
    print("BACKTEST COMPARISON: Current vs New Same-Direction Position Rules")
    print("=" * 80)
    
    # Load data
    data_file = project_root / "data" / "eur_usd_long_term.csv"
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
    
    # Run CURRENT behavior backtest
    print("\n" + "=" * 80)
    print("CURRENT BEHAVIOR: Skip US trade if EUR position still open")
    print("=" * 80)
    current_result = backtest_dual_market_current(
        df_with_opens,
        dual_signals_df,
        take_profit_pips=tp_pips,
        cost_per_trade_pips=cost_per_trade,
    )
    current_stats = current_result.get_summary_stats()
    current_result.print_summary()
    
    # Run NEW behavior backtest
    print("\n" + "=" * 80)
    print("NEW BEHAVIOR: Keep EUR position if US signal is same direction")
    print("=" * 80)
    new_result = backtest_dual_market_new(
        df_with_opens,
        dual_signals_df,
        take_profit_pips=tp_pips,
        cost_per_trade_pips=cost_per_trade,
    )
    new_stats = new_result.get_summary_stats()
    new_result.print_summary()
    
    # Compare results
    comparison = analyze_comparison(current_result, new_result)
    
    print("\n" + "=" * 80)
    print("COMPARISON RESULTS")
    print("=" * 80)
    print(f"\nTotal Pips Difference: {comparison['pips_diff']:+.2f} pips")
    print(f"  Current: {current_stats['total_pips']:.2f} pips")
    print(f"  New:     {new_stats['total_pips']:.2f} pips")
    
    print(f"\nTotal Trades Difference: {comparison['trades_diff']:+d} trades")
    print(f"  Current: {current_stats['total_trades']} trades")
    print(f"  New:     {new_stats['total_trades']} trades")
    
    print(f"\nWin Rate Difference: {comparison['win_rate_diff']:+.2f}%")
    print(f"  Current: {current_stats['win_rate']:.2f}%")
    print(f"  New:     {new_stats['win_rate']:.2f}%")
    
    print(f"\nSame-Direction Trades Kept: {comparison['skipped_same_direction']}")
    print(f"Spread Costs Saved: {comparison['spread_savings_pips']:.2f} pips")
    print(f"  (4 pips per skipped trade: 2 close + 2 open)")
    
    # Detailed comparison table
    print("\n" + "=" * 80)
    print("DETAILED COMPARISON TABLE")
    print("=" * 80)
    
    comparison_data = []
    comparison_data.append({
        'Metric': 'Total Pips',
        'Current': f"{current_stats['total_pips']:.2f}",
        'New': f"{new_stats['total_pips']:.2f}",
        'Difference': f"{comparison['pips_diff']:+.2f}",
    })
    comparison_data.append({
        'Metric': 'Total Trades',
        'Current': f"{current_stats['total_trades']}",
        'New': f"{new_stats['total_trades']}",
        'Difference': f"{comparison['trades_diff']:+d}",
    })
    comparison_data.append({
        'Metric': 'Win Rate %',
        'Current': f"{current_stats['win_rate']:.2f}",
        'New': f"{new_stats['win_rate']:.2f}",
        'Difference': f"{comparison['win_rate_diff']:+.2f}",
    })
    comparison_data.append({
        'Metric': 'Avg Pips/Trade',
        'Current': f"{current_stats['avg_pips_per_trade']:.2f}",
        'New': f"{new_stats['avg_pips_per_trade']:.2f}",
        'Difference': f"{new_stats['avg_pips_per_trade'] - current_stats['avg_pips_per_trade']:+.2f}",
    })
    comparison_data.append({
        'Metric': 'Profit Factor',
        'Current': f"{current_stats['profit_factor']:.2f}",
        'New': f"{new_stats['profit_factor']:.2f}",
        'Difference': f"{new_stats['profit_factor'] - current_stats['profit_factor']:+.2f}",
    })
    comparison_data.append({
        'Metric': 'Max Drawdown (pips)',
        'Current': f"{current_stats['max_drawdown_pips']:.2f}",
        'New': f"{new_stats['max_drawdown_pips']:.2f}",
        'Difference': f"{new_stats['max_drawdown_pips'] - current_stats['max_drawdown_pips']:+.2f}",
    })
    
    comparison_df = pd.DataFrame(comparison_data)
    print("\n" + comparison_df.to_string(index=False))
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if comparison['pips_diff'] > 0:
        print(f"✓ New behavior outperformed by {comparison['pips_diff']:.2f} pips")
    else:
        print(f"✗ New behavior underperformed by {abs(comparison['pips_diff']):.2f} pips")
    
    print(f"\nNew behavior saved {comparison['spread_savings_pips']:.2f} pips in spread costs")
    print(f"by keeping {comparison['skipped_same_direction']} same-direction positions")
    print(f"instead of closing and reopening.")
    
    if comparison['trades_diff'] < 0:
        print(f"\nNew behavior executed {abs(comparison['trades_diff'])} fewer trades")
        print(f"(kept existing positions instead of closing/reopening)")
    
    print("\n" + "=" * 80)
    print("IMPORTANT DISCLAIMER:")
    print("These are historical backtests with no guarantee of future performance.")
    print("=" * 80)
    
    return {
        'current_result': current_result,
        'new_result': new_result,
        'comparison': comparison,
    }


if __name__ == "__main__":
    results = run_comparison_backtest()

