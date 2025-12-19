"""
Test strategies to improve drawdown, including wide stop loss and filters.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from src.data_loader import load_eurusd_data
from src.core_analysis import calculate_daily_metrics, calculate_adr
from src.regime import calculate_moving_averages, classify_regime
from src.backtest import backtest_strategy
from src.backtest_no_sl import backtest_strategy_no_sl
from src.strategies import strategy_always_sell


def backtest_with_wide_sl(df: pd.DataFrame, signals: pd.Series, 
                          take_profit_pips: float, stop_loss_pips: float,
                          cost_per_trade_pips: float = 2.0) -> object:
    """
    Backtest with a wide stop loss as safety net.
    Still exits at EOD if TP not hit, but SL protects from extreme moves.
    """
    from src.backtest import BacktestResult
    from src.data_loader import price_to_pips, pips_to_price
    
    signals = signals.reindex(df.index)
    trades = []
    equity_curve = []
    current_equity = 10000.0
    
    for i in df.index:
        if i == 0:
            equity_curve.append(current_equity)
            continue
        
        signal = signals.loc[i]
        if signal not in ['long', 'short']:
            equity_curve.append(current_equity)
            continue
        
        row = df.loc[i]
        open_price = row['Open']
        close_price = row['Close']
        
        # Calculate TP and SL prices
        if signal == 'long':
            tp_price = open_price + pips_to_price(take_profit_pips)
            sl_price = open_price - pips_to_price(stop_loss_pips)
        else:  # short
            tp_price = open_price - pips_to_price(take_profit_pips)
            sl_price = open_price + pips_to_price(stop_loss_pips)
        
        # Check execution (conservative: SL first if both possible)
        pips_result = None
        exit_reason = None
        
        if signal == 'long':
            if row['Low'] <= sl_price:
                pips_result = -stop_loss_pips - cost_per_trade_pips
                exit_reason = 'SL'
            elif row['High'] >= tp_price:
                pips_result = take_profit_pips - cost_per_trade_pips
                exit_reason = 'TP'
            else:
                pips_result = price_to_pips(close_price - open_price) - cost_per_trade_pips
                exit_reason = 'EOD'
        else:  # short
            if row['High'] >= sl_price:
                pips_result = -stop_loss_pips - cost_per_trade_pips
                exit_reason = 'SL'
            elif row['Low'] <= tp_price:
                pips_result = take_profit_pips - cost_per_trade_pips
                exit_reason = 'TP'
            else:
                pips_result = price_to_pips(open_price - close_price) - cost_per_trade_pips
                exit_reason = 'EOD'
        
        trades.append({
            'date': row['Date'],
            'direction': signal,
            'entry_price': open_price,
            'exit_price': close_price,
            'exit_reason': exit_reason,
            'pips': pips_result,
        })
        
        current_equity += pips_result * 10
        equity_curve.append(current_equity)
    
    trades_df = pd.DataFrame(trades)
    equity_series = pd.Series(equity_curve, index=df.index)
    
    from src.backtest import BacktestResult
    return BacktestResult(trades_df, equity_series)


def strategy_filter_low_adr(df: pd.DataFrame, min_adr: float = 30.0) -> pd.Series:
    """Filter out low volatility days."""
    signals = strategy_always_sell(df)
    adr = calculate_adr(df, window=20)
    signals.loc[adr < min_adr] = 'flat'
    return signals


def strategy_filter_exhaustion(df: pd.DataFrame) -> pd.Series:
    """Avoid selling after strong down days when opening at/below yesterday's low."""
    signals = strategy_always_sell(df)
    
    prev_low = df['Low'].shift(1)
    prev_close = df['Close'].shift(1)
    prev_open = df['Open'].shift(1)
    
    # Avoid selling if open is at/below yesterday's low after a down day
    exhaustion_short = (
        (signals == 'short') & 
        (df['Open'] <= prev_low) &
        (prev_close < prev_open)  # Yesterday was down day
    )
    
    signals.loc[exhaustion_short] = 'flat'
    return signals


def strategy_filter_directional(df: pd.DataFrame) -> pd.Series:
    """Only sell when in downtrend (price below SMA20)."""
    signals = pd.Series('flat', index=df.index)
    df = calculate_moving_averages(df, periods=[20])
    
    # Only sell when price below SMA20 (downtrend)
    signals.loc[df['Close'].shift(1) < df['SMA20']] = 'short'
    
    return signals


def test_drawdown_improvements():
    """Test various methods to reduce drawdown."""
    
    print("=" * 80)
    print("DRAWDOWN IMPROVEMENT STRATEGIES")
    print("=" * 80)
    
    # Load data
    data_file = project_root / "data" / "eur_usd.csv"
    df = load_eurusd_data(str(data_file))
    df = calculate_daily_metrics(df)
    df = calculate_moving_averages(df, periods=[20, 50, 200])
    df = classify_regime(df, sma_short=50, sma_long=200)
    
    print(f"\nLoaded {len(df)} days of data\n")
    
    tp_pips = 10.0
    cost_per_trade = 2.0
    
    strategies_to_test = {
        '1. Baseline: Always Sell (no SL)': {
            'func': strategy_always_sell,
            'backtest_func': backtest_strategy_no_sl,
            'params': {'take_profit_pips': tp_pips, 'cost_per_trade_pips': cost_per_trade}
        },
        '2. Always Sell + Wide SL (30 pips)': {
            'func': strategy_always_sell,
            'backtest_func': backtest_with_wide_sl,
            'params': {'take_profit_pips': tp_pips, 'stop_loss_pips': 30.0, 'cost_per_trade_pips': cost_per_trade}
        },
        '3. Always Sell + Wide SL (50 pips)': {
            'func': strategy_always_sell,
            'backtest_func': backtest_with_wide_sl,
            'params': {'take_profit_pips': tp_pips, 'stop_loss_pips': 50.0, 'cost_per_trade_pips': cost_per_trade}
        },
        '4. Always Sell + ADR Filter (min 40 pips)': {
            'func': lambda df: strategy_filter_low_adr(df, min_adr=40.0),
            'backtest_func': backtest_strategy_no_sl,
            'params': {'take_profit_pips': tp_pips, 'cost_per_trade_pips': cost_per_trade}
        },
        '5. Always Sell + Exhaustion Filter': {
            'func': strategy_filter_exhaustion,
            'backtest_func': backtest_strategy_no_sl,
            'params': {'take_profit_pips': tp_pips, 'cost_per_trade_pips': cost_per_trade}
        },
        '6. Directional Filter (Sell only in downtrend)': {
            'func': strategy_filter_directional,
            'backtest_func': backtest_strategy_no_sl,
            'params': {'take_profit_pips': tp_pips, 'cost_per_trade_pips': cost_per_trade}
        },
    }
    
    results = {}
    
    for strategy_name, config in strategies_to_test.items():
        print("\n" + "=" * 80)
        print(f"Strategy: {strategy_name}")
        print("=" * 80)
        
        try:
            signals = config['func'](df)
            signal_counts = signals.value_counts()
            print(f"\nSignal Distribution:")
            for sig, count in signal_counts.items():
                print(f"  {sig}: {count}")
            
            if len(signals[signals.isin(['long', 'short'])]) == 0:
                print("No signals - skipping")
                continue
            
            result = config['backtest_func'](df, signals, **config['params'])
            result.print_summary()
            
            # Show drawdown breakdown
            stats = result.get_summary_stats()
            trades = result.trades
            if len(trades) > 0:
                eod_exits = trades[trades['exit_reason'] == 'EOD'] if 'exit_reason' in trades.columns else trades[~trades.get('tp_hit', pd.Series([False]*len(trades)))]
                sl_exits = trades[trades['exit_reason'] == 'SL'] if 'exit_reason' in trades.columns else pd.DataFrame()
                
                print(f"\nExit Breakdown:")
                if 'exit_reason' in trades.columns:
                    exit_counts = trades['exit_reason'].value_counts()
                    for reason, count in exit_counts.items():
                        print(f"  {reason}: {count}")
                
                if len(eod_exits) > 0:
                    eod_losses = eod_exits[eod_exits['pips'] <= 0]
                    if len(eod_losses) > 0:
                        print(f"  EOD Losses: {len(eod_losses)} trades, avg: {eod_losses['pips'].mean():.2f} pips")
                        print(f"  Largest EOD Loss: {eod_losses['pips'].min():.2f} pips")
            
            results[strategy_name] = result
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Comparison
    print("\n" + "=" * 80)
    print("DRAWDOWN COMPARISON")
    print("=" * 80)
    
    comparison_data = []
    for name, result in results.items():
        stats = result.get_summary_stats()
        trades = result.trades
        
        if len(trades) > 0:
            eod_exits = trades[trades.get('exit_reason', 'EOD') == 'EOD'] if 'exit_reason' in trades.columns else pd.DataFrame()
            sl_exits = trades[trades.get('exit_reason', '') == 'SL'] if 'exit_reason' in trades.columns else pd.DataFrame()
            largest_loss = trades['pips'].min()
        else:
            largest_loss = 0.0
            eod_exits = pd.DataFrame()
            sl_exits = pd.DataFrame()
        
        comparison_data.append({
            'Strategy': name[:45],
            'Total Pips': f"{stats['total_pips']:+.2f}",
            'Trades': stats['total_trades'],
            'Win Rate %': f"{stats['win_rate']:.2f}",
            'Max DD (pips)': f"{stats['max_drawdown_pips']:.2f}",
            'Max DD %': f"{stats['max_drawdown_pct']:.2f}",
            'Largest Loss': f"{largest_loss:.2f}",
            'SL Hits': len(sl_exits),
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    print("\n" + comparison_df.to_string(index=False))
    
    print("\n" + "=" * 80)
    print("KEY INSIGHTS:")
    print("=" * 80)
    print("1. Wide SL: Limits maximum loss per trade (e.g., 30-50 pips)")
    print("2. ADR Filter: Skips low-volatility days (reduces weak setups)")
    print("3. Exhaustion Filter: Avoids selling at extremes after strong moves")
    print("4. Directional Filter: Only sells in downtrends (avoids counter-trend)")
    print("=" * 80)


if __name__ == "__main__":
    test_drawdown_improvements()

