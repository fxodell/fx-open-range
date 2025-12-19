# Trade Duration Analysis

## Summary

Since we trade at the daily open and exit either when TP is hit (intraday) or at end of day (EOD), trade duration varies.

---

## Trade Exit Types

### TP Hits (Intraday Exits)

- **Count:** 1,054 trades (81.1%)
- **Duration:** Less than full trading day (intraday exit)
- **Average Pips:** +8.00 pips
- **Win Rate:** 100.0%
- **Note:** Exact timing unknown (would need intraday data)

### EOD Exits (Full Day)

- **Count:** 245 trades (18.9%)
- **Duration:** Full trading day (~24 hours)
- **Average Pips:** -1.98 pips
- **Win Rate:** 4.9% (most are small losses)
- **Entry:** Daily open
- **Exit:** Daily close

---

## Duration Statistics

### Overall Average Duration

**Estimated Average: ~59.4% of trading day (~14.3 hours)**

Breakdown:
- **TP Hits (81.1%):** ~50% of trading day (estimate - exact time unknown)
- **EOD Exits (18.9%):** 100% of trading day (full 24 hours)

### By Direction

**Long Trades:**
- TP Hits: 501 (80.7% of long trades) - Intraday exit
- EOD Exits: 120 (19.3% of long trades) - Full day

**Short Trades:**
- TP Hits: 553 (81.6% of short trades) - Intraday exit
- EOD Exits: 125 (18.4% of short trades) - Full day

---

## Key Insights

### Most Trades Exit Intraday (81.1%)

- **1,054 out of 1,299 trades** hit the 10 pip TP target during the day
- These trades exit before the end of day
- All TP hits are winners (+8.00 pips each)
- Exact timing varies (could be minutes or hours after open)

### Some Trades Held Full Day (18.9%)

- **245 out of 1,299 trades** don't hit TP and exit at EOD
- Held for full trading day (~24 hours)
- Most EOD exits are small losses (-1.98 pips average)
- Only 4.9% of EOD exits are winners

### Duration Distribution

```
81.1% of trades: Intraday exit (TP hit)
                  ↓
                  Average: ~50% of day (~12 hours estimated)
                  
18.9% of trades: Full day exit (EOD)
                  ↓
                  Duration: 100% of day (~24 hours)
```

---

## Limitations

### Daily OHLC Data Limitation

Since we only have **daily OHLC data** (not intraday):
- We know TP was hit, but not exactly when
- Can't determine precise entry/exit times
- Estimated duration for TP hits is approximate

### What We Know

✅ **TP Hits:** Exited before end of day (intraday)
✅ **EOD Exits:** Exited at end of day (full day)
❌ **Exact Timing:** Unknown for TP hits (would need M5/M15/H1 data)

---

## Typical Trade Lifecycle

### TP Hit Scenario (81.1% of trades)

```
Day Start (Open)
    ↓
Enter Trade (at Open price)
    ↓
Price moves toward TP target
    ↓
TP Hit (10 pips) ← Exact time unknown, but before close
    ↓
Exit Trade (+8 pips after costs)
    ↓
Duration: Less than full day (estimated ~12 hours average)
```

### EOD Exit Scenario (18.9% of trades)

```
Day Start (Open)
    ↓
Enter Trade (at Open price)
    ↓
Price doesn't reach TP target
    ↓
Market Closes
    ↓
Exit Trade at Close price (could be + or -)
    ↓
Duration: Full trading day (~24 hours)
```

---

## Performance by Duration

### Intraday Exits (TP Hits)

- **1,054 trades**
- **Average:** +8.00 pips
- **Win Rate:** 100% (all winners)
- **Duration:** Less than full day

### Full Day Exits (EOD)

- **245 trades**
- **Average:** -1.98 pips
- **Win Rate:** 4.9% (mostly small losses)
- **Duration:** Full day (~24 hours)

---

## Conclusion

**Trade Duration Summary:**

1. **Most trades (81.1%)** exit intraday when TP is hit
   - Estimated duration: ~50% of trading day (~12 hours)
   - All are winners
   
2. **Some trades (18.9%)** are held full day (EOD exit)
   - Duration: Full trading day (~24 hours)
   - Mostly small losses
   
3. **Overall average:** ~59.4% of trading day (~14.3 hours)

**Key Takeaway:**
Most trades hit TP and exit intraday, but the exact timing requires intraday data. The 18.9% that exit at EOD are mostly small losses, showing the importance of hitting TP quickly.

