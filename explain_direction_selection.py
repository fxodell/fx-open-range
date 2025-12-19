"""
Explain how trade direction is selected.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pandas as pd
from src.data_loader import load_eurusd_data
from src.regime import calculate_moving_averages


def explain_direction_selection():
    """Explain how the strategy selects trade direction."""
    
    print("=" * 80)
    print("HOW TRADE DIRECTION IS SELECTED")
    print("=" * 80)
    
    # Load data
    df = load_eurusd_data('data/eur_usd_long_term.csv')
    df = calculate_moving_averages(df, periods=[20])
    
    print("\nStrategy: Price Trend (SMA20) Directional")
    print("-" * 80)
    
    print("\nDirection Selection Rule:")
    print("  • BUY (LONG) when: Yesterday's Close > SMA20")
    print("     → Price is above the 20-day moving average = UPTREND")
    print()
    print("  • SELL (SHORT) when: Yesterday's Close < SMA20")
    print("     → Price is below the 20-day moving average = DOWNTREND")
    print()
    print("  • NO TRADE (FLAT) when: No signal generated")
    
    print("\n" + "=" * 80)
    print("DETAILED EXPLANATION")
    print("=" * 80)
    
    print("\n1. Calculate SMA20 (Simple Moving Average of last 20 closes)")
    print("   - SMA20 = Average of last 20 day's closing prices")
    print("   - This represents the recent trend")
    
    print("\n2. Compare Yesterday's Close to SMA20")
    print("   - Use YESTERDAY's close (not today's) to avoid lookahead bias")
    print("   - This is information available at today's open")
    
    print("\n3. Generate Signal:")
    print("   - If Close(yesterday) > SMA20 → Trend is UP → BUY")
    print("   - If Close(yesterday) < SMA20 → Trend is DOWN → SELL")
    
    print("\n" + "=" * 80)
    print("VISUAL EXAMPLE")
    print("=" * 80)
    
    # Calculate signals
    df['PrevClose'] = df['Close'].shift(1)
    signals = pd.Series('flat', index=df.index)
    signals.loc[df['PrevClose'] > df['SMA20']] = 'long'
    signals.loc[df['PrevClose'] < df['SMA20']] = 'short'
    
    # Show examples with explanation
    print("\nExample Trades (showing direction selection):")
    print()
    print(f"{'Date':<12} {'Prev Close':<12} {'SMA20':<12} {'Difference':<12} {'Direction':<12} {'Reason'}")
    print("-" * 80)
    
    # Show 15 examples
    for i in range(50, 65):
        row = df.iloc[i]
        prev_close = df.iloc[i-1]['Close'] if i > 0 else None
        
        if prev_close and pd.notna(row['SMA20']):
            signal = signals.iloc[i]
            diff = prev_close - row['SMA20']
            diff_pips = diff * 10000
            
            if signal == 'long':
                reason = f"Price {diff_pips:+.1f} pips above MA → UPTREND → BUY"
            elif signal == 'short':
                reason = f"Price {abs(diff_pips):+.1f} pips below MA → DOWNTREND → SELL"
            else:
                reason = "No signal"
            
            print(f"{row['Date'].strftime('%Y-%m-%d'):<12} {prev_close:.5f}    {row['SMA20']:.5f}    {diff_pips:+8.1f}     {signal.upper():<12} {reason}")
    
    print("\n" + "=" * 80)
    print("WHY THIS WORKS")
    print("=" * 80)
    
    print("\nThe logic behind this approach:")
    print("  1. Moving averages smooth out price noise")
    print("  2. Price above MA suggests uptrend (momentum up)")
    print("  3. Price below MA suggests downtrend (momentum down)")
    print("  4. Trading with the trend improves win probability")
    print("  5. SMA20 represents medium-term trend (~1 month)")
    
    print("\n" + "=" * 80)
    print("STATISTICS (5-Year Data)")
    print("=" * 80)
    
    # Show distribution
    signal_counts = signals.value_counts()
    total_signals = signals[signals.isin(['long', 'short'])].count()
    
    print(f"\nDirection Distribution:")
    print(f"  Long Signals: {signal_counts.get('long', 0)} ({signal_counts.get('long', 0)/total_signals*100:.1f}%)")
    print(f"  Short Signals: {signal_counts.get('short', 0)} ({signal_counts.get('short', 0)/total_signals*100:.1f}%)")
    print(f"  Flat: {signal_counts.get('flat', 0)}")
    print(f"  Total Trading Signals: {total_signals}")
    
    print("\n" + "=" * 80)
    print("ALTERNATIVE DIRECTION SELECTION METHODS")
    print("=" * 80)
    
    print("\nOther methods we could use:")
    print()
    print("1. Momentum-Based:")
    print("   - Buy if recent net moves are positive (upward momentum)")
    print("   - Sell if recent net moves are negative (downward momentum)")
    print()
    print("2. Multiple Moving Averages:")
    print("   - Buy when SMA20 > SMA50 (short-term > long-term = uptrend)")
    print("   - Sell when SMA20 < SMA50 (short-term < long-term = downtrend)")
    print()
    print("3. Regime-Based:")
    print("   - Buy in bull regime (price > SMA50 > SMA200, MAs trending up)")
    print("   - Sell in bear regime (price < SMA50 < SMA200, MAs trending down)")
    print("   - No trade in chop regime")
    print()
    print("4. Combined (Trend + Momentum):")
    print("   - Require both price trend AND momentum to agree")
    print("   - More selective, fewer but higher-quality trades")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    explain_direction_selection()

