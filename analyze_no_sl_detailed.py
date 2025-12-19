"""
Detailed analysis of no-SL strategy with trade-by-trade breakdown.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pandas as pd
from src.data_loader import load_eurusd_data
from src.core_analysis import calculate_daily_metrics
from src.regime import calculate_moving_averages, classify_regime
from src.backtest_no_sl import backtest_strategy_no_sl
from src.strategies import strategy_always_buy, strategy_always_sell


def analyze_detailed():
    """Detailed trade-by-trade analysis."""
    
    print("=" * 80)
    print("DETAILED ANALYSIS: 10 PIP TP, NO SL, EXIT AT EOD")
    print("=" * 80)
    
    # Load and prepare data
    data_file = project_root / "data" / "eur_usd.csv"
    df = load_eurusd_data(str(data_file))
    df = calculate_daily_metrics(df)
    df = calculate_moving_averages(df)
    df = classify_regime(df)
    
    # Test both buy and sell strategies
    for strategy_name, strategy_func in [('Always Buy', strategy_always_buy), 
                                         ('Always Sell', strategy_always_sell)]:
        print(f"\n{'=' * 80}")
        print(f"{strategy_name} - Trade Details")
        print(f"{'=' * 80}\n")
        
        signals = strategy_func(df)
        result = backtest_strategy_no_sl(df, signals, take_profit_pips=10.0, cost_per_trade_pips=2.0)
        
        trades = result.trades
        
        if len(trades) == 0:
            print("No trades generated.")
            continue
        
        # Merge with original data to show OHLC info
        trades_with_data = trades.merge(
            df[['Date', 'Open', 'High', 'Low', 'Close', 'range_pips', 'up_from_open_pips', 
                'down_from_open_pips', 'net_from_open_pips']],
            left_on='date',
            right_on='Date',
            how='left'
        )
        
        # Display first 10 trades in detail
        print("First 10 Trades:")
        print("-" * 80)
        
        for idx, trade in trades_with_data.head(10).iterrows():
            direction = trade['direction'].upper()
            entry = trade['entry_price']
            exit_p = trade['exit_price']
            exit_reason = trade['exit_reason']
            pips = trade['pips']
            tp_hit = trade['tp_hit']
            
            high = trade['High']
            low = trade['Low']
            close = trade['Close']
            
            if direction == 'LONG':
                up_move = trade['up_from_open_pips']
                max_loss = trade['down_from_open_pips']
            else:
                up_move = trade['down_from_open_pips']
                max_loss = trade['up_from_open_pips']
            
            print(f"\nTrade {idx + 1} ({trade['date'].strftime('%Y-%m-%d')}):")
            print(f"  Direction:     {direction}")
            print(f"  Entry:         {entry:.5f} (Open)")
            print(f"  Exit:          {exit_p:.5f} ({exit_reason})")
            print(f"  Result:        {pips:+.2f} pips {'✓' if pips > 0 else '✗'}")
            print(f"  TP Hit:        {'Yes' if tp_hit else 'No (EOD exit)'}")
            print(f"  Daily Range:   {trade['range_pips']:.1f} pips")
            if direction == 'LONG':
                print(f"  Up Move:       {up_move:.1f} pips available")
                print(f"  Down Move:     {max_loss:.1f} pips (max loss if EOD)")
            else:
                print(f"  Down Move:     {up_move:.1f} pips available")
                print(f"  Up Move:       {max_loss:.1f} pips (max loss if EOD)")
            print(f"  Net Move:      {trade['net_from_open_pips']:+.1f} pips (open to close)")
        
        # Summary statistics
        print(f"\n{'=' * 80}")
        print(f"{strategy_name} - Summary Statistics")
        print(f"{'=' * 80}")
        
        tp_hits = trades[trades['tp_hit']]
        eod_exits = trades[~trades['tp_hit']]
        
        print(f"\nTotal Trades: {len(trades)}")
        print(f"  TP Hits: {len(tp_hits)} ({len(tp_hits)/len(trades)*100:.1f}%)")
        print(f"  EOD Exits: {len(eod_exits)} ({len(eod_exits)/len(trades)*100:.1f}%)")
        
        if len(tp_hits) > 0:
            print(f"\nTP Hits:")
            print(f"  Avg Pips: {tp_hits['pips'].mean():.2f}")
            print(f"  All winners: {len(tp_hits[tp_hits['pips'] > 0])} / {len(tp_hits)}")
        
        if len(eod_exits) > 0:
            print(f"\nEOD Exits:")
            print(f"  Avg Pips: {eod_exits['pips'].mean():.2f}")
            print(f"  Winners: {len(eod_exits[eod_exits['pips'] > 0])} ({len(eod_exits[eod_exits['pips'] > 0])/len(eod_exits)*100:.1f}%)")
            print(f"  Losers: {len(eod_exits[eod_exits['pips'] <= 0])} ({len(eod_exits[eod_exits['pips'] <= 0])/len(eod_exits)*100:.1f}%)")
            print(f"  Largest Win: {eod_exits['pips'].max():.2f} pips")
            print(f"  Largest Loss: {eod_exits['pips'].min():.2f} pips")
            print(f"  Avg Loss (losing trades): {eod_exits[eod_exits['pips'] <= 0]['pips'].mean():.2f} pips")
        
        # Show losing EOD trades in detail
        if len(eod_exits) > 0 and len(eod_exits[eod_exits['pips'] <= 0]) > 0:
            print(f"\n{'=' * 80}")
            print("Losing EOD Exits (TP not hit, closed at loss):")
            print(f"{'=' * 80}")
            
            losing_eod = eod_exits[eod_exits['pips'] <= 0].merge(
                df[['Date', 'Open', 'High', 'Low', 'Close', 'range_pips']],
                left_on='date',
                right_on='Date',
                how='left'
            )
            
            for idx, trade in losing_eod.iterrows():
                print(f"\n{trade['date'].strftime('%Y-%m-%d')}: {trade['direction'].upper()}")
                print(f"  Entry: {trade['entry_price']:.5f}, Exit: {trade['exit_price']:.5f} (Close)")
                print(f"  Loss: {trade['pips']:.2f} pips")
                print(f"  Daily Range: {trade['range_pips']:.1f} pips")
                if trade['direction'] == 'long':
                    print(f"  High was {trade['High']:.5f} (TP would be {trade['entry_price'] + 0.0010:.5f})")
                    print(f"  TP missed by: {((trade['entry_price'] + 0.0010) - trade['High']) * 10000:.1f} pips")
                else:
                    print(f"  Low was {trade['Low']:.5f} (TP would be {trade['entry_price'] - 0.0010:.5f})")
                    print(f"  TP missed by: {(trade['Low'] - (trade['entry_price'] - 0.0010)) * 10000:.1f} pips")


if __name__ == "__main__":
    analyze_detailed()

