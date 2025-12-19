# Strategy Improvement Recommendations

## Current Strategy Performance (5-Year Test)

- **Win Rate:** 82.06%
- **TP Hit Rate:** 81.14%
- **Total Pips:** +7,946 pips
- **Max Drawdown:** 83.88 pips
- **Profit Factor:** 16.97

**Weak Point:** EOD exits have only 4.9% win rate (mostly small losses)

---

## Improvement Opportunities

### 1. Filter Low Volatility Days ✅ **HIGH PRIORITY**

**Problem:**
- EOD exits often occur on low-volatility days
- When ADR is too low, there's not enough range to hit 10 pip TP

**Solution:**
- Only trade when ADR20 > threshold (e.g., 40-50 pips)
- Skip days with insufficient volatility
- This should improve TP hit rate

**Expected Impact:**
- Reduce EOD exits
- Increase TP hit rate from 81% to 85%+
- Reduce losing EOD exits

**Implementation:**
```python
def strategy_with_adr_filter(df, min_adr=40):
    signals = strategy_price_trend_directional(df)
    adr = calculate_adr(df, window=20)
    signals.loc[adr < min_adr] = 'flat'  # Skip low volatility
    return signals
```

---

### 2. Adaptive TP Based on Volatility

**Problem:**
- Fixed 10 pip TP may be too large for low-volatility days
- Fixed 10 pip TP may be too small for high-volatility days

**Solution:**
- Scale TP based on ADR: TP = ADR × multiplier (e.g., 0.3 = 30% of ADR)
- Low volatility → smaller TP (easier to hit)
- High volatility → larger TP (capture more)

**Expected Impact:**
- Better TP hit rates across volatility regimes
- Capture more profit on high-volatility days
- More realistic targets on low-volatility days

**Implementation:**
```python
def adaptive_tp_from_adr(df, adr_multiplier=0.3):
    adr = calculate_adr(df, window=20)
    # For each trade, use ADR-based TP instead of fixed 10 pips
    # Would require modifying backtest engine
```

---

### 3. Multiple TP Levels (Partial Profits)

**Problem:**
- All-or-nothing: either hit 10 pip TP or exit at EOD (possibly losing)

**Solution:**
- Take partial profit at 5 pips (secure some gain)
- Let remainder run to 10 pips or EOD
- Reduces impact of EOD losses

**Expected Impact:**
- Secure profits on trades that don't reach full TP
- Reduce average loss on EOD exits
- Better risk management

**Implementation:**
```python
# Take 50% at 5 pips, 50% at 10 pips or EOD
# Would require position sizing modifications
```

---

### 4. Day-of-Week Filters

**Problem:**
- Some days of week may have better/worse performance
- Monday/Friday patterns, mid-week patterns

**Solution:**
- Analyze performance by day of week
- Filter out weak days
- Focus on best-performing days

**Expected Impact:**
- Improve win rate by avoiding weak days
- May reduce trade count but improve quality

---

### 5. Better Trend Detection

**Problem:**
- Simple SMA20 crossover may miss nuanced trends
- Could improve entry timing

**Solution:**
- Add momentum confirmation (e.g., SMA20 slope)
- Use multiple timeframes
- Add RSI or other momentum indicators

**Expected Impact:**
- Better entry timing
- Reduced false signals
- Higher TP hit rate

---

### 6. Time-of-Day Filters (with Intraday Data)

**Problem:**
- Trading at open may not be optimal
- Some hours have better volatility/movement

**Solution:**
- Analyze intraday patterns
- Trade during highest-probability hours
- Skip low-volatility periods

**Expected Impact:**
- Better entry timing
- Higher TP hit rate
- Requires intraday data

---

### 7. Trend Strength Confirmation

**Problem:**
- Trading in weak trends may lead to EOD exits

**Solution:**
- Only trade when trend is strong (e.g., price well above/below SMA)
- Add distance filter (e.g., price must be X pips from SMA)
- Add momentum confirmation

**Expected Impact:**
- Higher quality setups
- Better TP hit rate
- Fewer trades but better quality

---

### 8. Gap Analysis

**Problem:**
- Large gaps may indicate news/events → unpredictable

**Solution:**
- Filter out days with large gaps (>X pips from previous close)
- Avoid trading around major news events
- Skip gap days

**Expected Impact:**
- Avoid unpredictable days
- Improve win rate
- Reduce volatility in results

---

### 9. Range Position Filter

**Problem:**
- Opening at extremes may reduce TP hit probability

**Solution:**
- Only trade when open is in middle 50% of recent range
- Avoid opening at yesterday's high/low
- Better entry position

**Expected Impact:**
- Higher TP hit rate
- Better entry prices
- More consistent results

---

### 10. Position Sizing Based on Volatility

**Problem:**
- Fixed position size doesn't account for volatility

**Solution:**
- Size positions based on ADR
- Higher volatility → smaller position (risk control)
- Lower volatility → normal position

**Expected Impact:**
- Better risk management
- More consistent drawdown
- Better risk-adjusted returns

---

## Recommended Priority Improvements

### Tier 1: Quick Wins (Implement First)

1. **ADR Filter** - Skip low-volatility days
   - Easy to implement
   - Should improve TP hit rate
   - Reduces losing EOD exits

2. **Day-of-Week Filter** - Avoid weak days
   - Easy to analyze and implement
   - Can improve win rate
   - May reduce trade count but improve quality

### Tier 2: Medium Impact (Next Steps)

3. **Better Trend Detection** - Add momentum/strength filters
   - Moderate complexity
   - Should improve entry quality
   - Higher TP hit rate

4. **Gap Filter** - Avoid large gap days
   - Easy to implement
   - Avoids unpredictable days
   - Reduces volatility

### Tier 3: Advanced (Future Enhancement)

5. **Adaptive TP** - Scale TP with volatility
   - Requires backtest engine modifications
   - Higher complexity
   - Better capture of opportunities

6. **Multiple TP Levels** - Partial profits
   - Requires position sizing changes
   - More complex execution
   - Better risk management

---

## Testing Approach

1. **Start with ADR Filter**
   - Test different thresholds (30, 40, 50 pips)
   - Measure impact on TP hit rate and total pips
   - Find optimal threshold

2. **Add Day-of-Week Analysis**
   - Identify weak days
   - Test filtering them out
   - Measure improvement

3. **Combine Filters**
   - ADR + Day-of-Week
   - Test combination
   - Measure cumulative impact

4. **Iterate and Optimize**
   - Test one improvement at a time
   - Measure before/after
   - Only keep improvements that help

---

## Expected Results After Improvements

**Target Metrics:**
- TP Hit Rate: 81% → 85-90%
- Win Rate: 82% → 85-88%
- EOD Exit Win Rate: 4.9% → 20%+
- Max Drawdown: Keep below 100 pips
- Total Pips: Increase by 10-20%

---

## Key Principles

1. **Don't Over-Optimize**
   - Test on out-of-sample data
   - Prefer simple, robust rules
   - Avoid curve-fitting

2. **Focus on Weak Points**
   - EOD exits are the problem
   - Focus improvements there
   - Measure impact carefully

3. **Maintain Simplicity**
   - More filters ≠ better
   - Simple rules are more robust
   - Prefer quality over complexity

---

## Conclusion

The strategy is already strong (82% win rate, +7,946 pips over 5 years). The main improvement opportunity is **reducing EOD exits** by:

1. **Filtering low-volatility days** (ADR filter)
2. **Better entry timing** (trend strength)
3. **Day-of-week filters** (avoid weak days)

Start with ADR filter as it's the easiest and likely most impactful improvement.

