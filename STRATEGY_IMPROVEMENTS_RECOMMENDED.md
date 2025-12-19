# Strategy Improvement Recommendations

## Current Performance (Baseline)

- **Total Pips:** +7,945.95 (5 years)
- **Win Rate:** 82.06%
- **TP Hit Rate:** 81.14%
- **Max Drawdown:** 83.88 pips
- **EOD Exit Win Rate:** 4.9% (the weak point)

---

## Tested Improvements: Results

| Strategy | Trades | Total Pips | Win Rate | TP Hit % | EOD Win % | vs Baseline |
|----------|--------|------------|----------|----------|-----------|-------------|
| **Baseline** | 1,299 | **+7,945.95** | 82.06% | 81.14% | 4.90% | - |
| ADR Filter (40) | 1,295 | +7,933.95 | 82.16% | 81.24% | 4.94% | -12 pips |
| ADR Filter (50) | 1,131 | +7,046.52 | 83.11% | 82.23% | 4.98% | -899 pips |
| Skip Wednesday | 1,039 | +6,471.49 | 83.06% | 82.19% | 4.86% | -1,474 pips |
| ADR + Day Filter | 1,036 | +6,457.49 | 83.11% | 82.24% | 4.89% | -1,488 pips |
| High Vol Only (60+) | 865 | +5,413.41 | 83.24% | 82.54% | 3.97% | -2,533 pips |

**Key Finding:** Filters improve win rate but reduce total pips (fewer trades = less total profit)

---

## Recommended Improvements

### 1. Focus on EOD Exit Problem ✅ **HIGH PRIORITY**

**The Real Issue:**
- EOD exits have only 4.9% win rate
- 233 losing EOD exits averaging -2.14 pips
- This is where most losses come from

**Solutions to Test:**

#### A. Adaptive TP Based on ADR
- **Idea:** Scale TP based on volatility
- **Logic:** TP = ADR × 0.25 (25% of average range)
- **Why:** More realistic targets for each day's volatility
- **Expected:** Higher TP hit rate, fewer EOD exits

#### B. Multiple TP Levels (Partial Profits)
- **Idea:** Take 50% profit at 5 pips, let remainder run to 10 pips or EOD
- **Why:** Secures some profit even if full TP doesn't hit
- **Expected:** Reduces EOD losses, improves overall performance

#### C. Trailing Stop (Alternative Approach)
- **Idea:** No fixed SL, but trailing stop that moves with price
- **Why:** Protects profits without stopping out too early
- **Expected:** Better handling of trades that don't hit TP

---

### 2. Better Entry Conditions

**Current:** Simple SMA20 crossover

**Improvements:**

#### A. Add Trend Strength Filter
```python
# Only trade when trend is strong (price well above/below SMA)
distance_from_sma = abs(price - SMA20) * 10000  # in pips
signals.loc[(signals == 'long') & (distance_from_sma < 10)] = 'flat'  # Too close to SMA
```

#### B. Add Momentum Confirmation
```python
# Require momentum to agree with trend
momentum = (close - close.shift(5)) * 10000  # 5-day momentum
signals.loc[(signals == 'long') & (momentum < 5)] = 'flat'  # Weak momentum
```

#### C. Multiple Timeframe Confirmation
- Use longer timeframe (SMA50 or SMA100) to confirm trend
- Only trade when both short and long-term trends agree

---

### 3. Volatility-Based Adjustments

**Analysis Shows:**
- Higher ADR = Better performance (85.7% win rate on 80+ ADR)
- Medium ADR (40-60) still good (80% win rate)
- Low ADR (<40) has only 4 trades, hard to evaluate

**Recommendation:**
- **Don't filter out low ADR** (removes trades, reduces total pips)
- **Instead:** Adjust TP based on ADR
- High ADR days: Use larger TP (capture more)
- Low ADR days: Use smaller TP (easier to hit)

---

### 4. Day-of-Week Optimization

**Analysis Shows:**
- Tuesday: Best (6.69 avg pips)
- Thursday: Good (6.28 avg pips)
- Wednesday: Weakest (5.67 avg pips)

**Recommendation:**
- **Don't skip Wednesday** (reduces total pips by -1,474)
- **Instead:** Size positions differently by day
- Wednesday: Smaller position size
- Tuesday/Thursday: Normal position size

---

### 5. Risk Management Enhancements

#### A. Maximum Daily Loss Limit
```python
# Stop trading after X pips lost in a day
daily_loss_limit = 50  # pips
if daily_loss >= daily_loss_limit:
    signals.loc[remaining_days] = 'flat'
```

#### B. Position Sizing Based on Volatility
```python
# Size positions smaller on high-volatility days
position_size = base_size * (normal_adr / current_adr)
```

#### C. Correlation with Market Regime
- Reduce position size in chop/uncertain regimes
- Increase in strong trend regimes

---

### 6. Advanced Techniques (Requires Intraday Data)

#### A. Time-of-Day Entry
- Analyze which hours have best TP hit rates
- Enter during optimal hours instead of always at open

#### B. Price Action Filters
- Wait for pullback before entering
- Enter on retests of key levels
- Use candlestick patterns for confirmation

#### C. Volatility Expansion
- Trade when volatility is expanding (not contracting)
- Use Bollinger Bands or ATR expansion signals

---

## Top 3 Recommendations (Priority Order)

### 1. Adaptive TP Based on ADR ✅ **HIGHEST PRIORITY**

**Why:**
- Directly addresses EOD exit problem
- More realistic targets for each day
- Should increase TP hit rate

**Implementation:**
```python
adr = calculate_adr(df, window=20)
tp_pips = adr * 0.25  # 25% of ADR as TP
# Would need to modify backtest engine to use variable TP
```

**Expected Impact:**
- TP Hit Rate: 81% → 85-88%
- EOD Exits: 18.9% → 12-15%
- Total Pips: Increase by 5-10%

---

### 2. Multiple TP Levels (Partial Profits) ✅ **HIGH PRIORITY**

**Why:**
- Secures profit even if full TP doesn't hit
- Reduces impact of EOD losses
- Better risk management

**Implementation:**
```python
# Take 50% at 5 pips, 50% at 10 pips or EOD
# Requires position sizing modifications
```

**Expected Impact:**
- EOD Exit Win Rate: 4.9% → 15-25%
- Average Loss: -2.14 → -1.0 to -1.5 pips
- Total Pips: Increase by 3-7%

---

### 3. Trend Strength Filter ✅ **MEDIUM PRIORITY**

**Why:**
- Improves entry quality
- Avoids weak trend setups
- Should improve TP hit rate

**Implementation:**
```python
# Only trade when price is X pips away from SMA20
distance = abs(df['Close'] - df['SMA20']) * 10000
signals.loc[(signals != 'flat') & (distance < 15)] = 'flat'  # Too close
```

**Expected Impact:**
- Win Rate: 82% → 84-85%
- TP Hit Rate: 81% → 83-84%
- Fewer trades but better quality

---

## What NOT to Do (Based on Testing)

### ❌ Don't Filter Out Low ADR Days
- Reduces total pips significantly
- Even low-volatility days can be profitable
- Better to adjust TP instead

### ❌ Don't Skip Days of Week
- Reduces total pips (e.g., -1,474 pips for skipping Wednesday)
- Win rate improvement doesn't compensate
- Better to adjust position sizing

### ❌ Don't Add Fixed Stop Losses
- Already tested: Made performance worse
- Stops out winning trades
- Directional filtering is the protection

---

## Implementation Roadmap

### Phase 1: Quick Wins (This Week)
1. ✅ Test adaptive TP (ADR-based)
2. ✅ Measure impact on TP hit rate and EOD exits
3. ✅ Optimize TP multiplier (test 0.2, 0.25, 0.3)

### Phase 2: Medium-Term (Next 2 Weeks)
1. ✅ Implement multiple TP levels
2. ✅ Test partial profit approach
3. ✅ Measure impact on EOD win rate

### Phase 3: Advanced (Next Month)
1. ✅ Add trend strength filters
2. ✅ Test momentum confirmation
3. ✅ Optimize entry conditions

---

## Success Metrics

**Target Improvements:**
- TP Hit Rate: 81% → **85-88%** (+4-7%)
- EOD Exit Win Rate: 4.9% → **15-25%** (+10-20%)
- Win Rate: 82% → **84-86%** (+2-4%)
- Total Pips: +7,946 → **+8,500 to +9,000** (+7-13%)
- Max Drawdown: Keep below **100 pips**

---

## Conclusion

The baseline strategy is already strong (+7,946 pips, 82% win rate). The main improvement opportunity is **addressing the EOD exit problem** (4.9% win rate).

**Best approach:**
1. **Adaptive TP** based on ADR (most impactful)
2. **Multiple TP levels** for partial profits (reduces losses)
3. **Trend strength filters** (improves entry quality)

**Avoid:**
- Simple filters that just reduce trade count
- Fixed stop losses (already tested - doesn't work)
- Over-optimization

Focus on improving the **EOD exit performance** rather than filtering out trades - this is where the real opportunity lies.

