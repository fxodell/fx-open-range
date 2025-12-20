# How to Run the Trading Application

## Quick Start (3 Steps)

### Step 1: Check Connection and Account Status
```bash
python -m app.main --status
```

This shows:
- Account balance
- Open positions
- Account summary

### Step 2: Run Trading

**Option A: Run Once (Test)**
```bash
python -m app.main --once
```
- Checks signal once
- Executes trade if valid
- Exits immediately

**Option B: Run Continuously (Live Trading)**
```bash
python -m app.main
```
- Checks every 60 seconds
- Executes trades when signals are valid
- Runs until you press Ctrl+C

---

## Full Command Reference

### Basic Commands

```bash
# Show account status (also tests connection)
python -m app.main --status

# Run once (check and exit)
python -m app.main --once

# Run continuously (default: checks every 60 seconds)
python -m app.main

# Run with custom check interval (5 minutes)
python -m app.main --interval 300

# Close all open positions
python -m app.main --close-all

# Show help
python -m app.main --help
```

### Practice vs Live Mode

**Practice Mode (Default - Safe for Testing):**
```bash
python -m app.main --mode practice
# or just
python -m app.main
```

**Live Mode (Real Money - Requires Confirmation):**
```bash
python -m app.main --mode live
```
⚠️ **WARNING**: This uses real money!

---

## Example Session

### 1. Check Your Account

```bash
python -m app.main --status
```

**Expected Output:**
```
Account Status:
Balance: 100000.00 USD
Unrealized P/L: 0.00 USD
Open Trades: 0
```

### 2. Run a Test (Practice Mode)

```bash
python -m app.main --once
```

**Expected Output:**
```
✓ Connected successfully
Signal: long, Price: 1.17236, SMA20: 1.16497
Placing long order: 1 units, TP=10.0 pips
Order placed successfully
Done.
```

### 3. Run Continuously

```bash
python -m app.main
```

**What Happens:**
- App starts and connects to OANDA
- Checks for signals every 60 seconds
- Executes trades during trading hours (22:00-23:00 UTC)
- Logs all activity to console and log file
- Press **Ctrl+C** to stop

---

## What Happens When It Runs

### Continuous Mode (`python -m app.main`)

1. **Connects** to OANDA API
2. **Checks every 60 seconds**:
   - Is it trading hours? (22:00-23:00 UTC)
   - Get signal (long/short/flat)
   - Already traded today? (max 1/day)
   - Open positions exist?
   - Execute trade if all conditions met
3. **Monitors** open positions
4. **Logs** everything to console and file
5. **Runs until** you press Ctrl+C

### Run Once Mode (`python -m app.main --once`)

1. **Connects** to OANDA API
2. **Checks once**:
   - Trading hours?
   - Get signal
   - Execute if valid
3. **Exits immediately**

---

## Monitoring

### View Logs in Real-Time

```bash
# Watch log file
tail -f logs/trading_$(date +%Y%m%d).log

# Or if on Windows
type logs\trading_YYYYMMDD.log
```

### Check Account Anytime

```bash
python -m app.main --status
```

### Check Open Positions

The status command shows open positions, or check in OANDA platform.

---

## Troubleshooting

### "Connection failed"
- Check internet connection
- Verify API token in `.env` file (create from `.env.example` if needed)
- Check OANDA API status

### "Insufficient data"
- App needs 20+ days of historical data
- Wait a few minutes and try again
- Check OANDA account has access

### "Already traded today"
- Normal - max 1 trade per day
- Will reset tomorrow
- Check `--status` to see today's trade

### "Outside trading hours"
- Trading hours: 22:00-23:00 UTC
- App only trades during this window
- Use `--once` to test anytime

### App won't start
- Make sure you're in project directory
- Check Python version: `python --version` (needs 3.7+)
- Install dependencies: `pip install requests pandas numpy`

---

## Recommended Workflow

### For Testing (Practice Mode)

1. **Check account status (tests connection):**
   ```bash
   python -m app.main --status
   ```

2. **Run once to test:**
   ```bash
   python -m app.main --once
   ```

3. **Check what happened:**
   ```bash
   python -m app.main --status
   ```

4. **If satisfied, run continuously:**
   ```bash
   python -m app.main
   ```

### For Live Trading

1. **Test thoroughly in practice mode first!**

2. **Switch to live mode:**
   ```bash
   python -m app.main --mode live
   ```
   (It will ask for confirmation)

3. **Monitor closely:**
   - Watch logs
   - Check account regularly
   - Monitor for issues

4. **Have exit strategy:**
   - Know how to stop: Ctrl+C
   - Know how to close positions: `--close-all`
   - Monitor account balance

---

## Running in Background (Linux/Mac)

### Using `nohup`:
```bash
nohup python -m app.main > trading_output.log 2>&1 &
```

### Using `screen`:
```bash
screen -S trading
python -m app.main
# Press Ctrl+A then D to detach
# Reattach: screen -r trading
```

### Using `tmux`:
```bash
tmux new -s trading
python -m app.main
# Press Ctrl+B then D to detach
# Reattach: tmux attach -t trading
```

---

## Next Steps

1. ✅ Read `app/README.md` for full documentation
2. ✅ Read `app/TRADE_TIMING.md` for timing details
3. ✅ Read `app/QUICK_START.md` for quick reference
4. ✅ Test in practice mode first!
5. ✅ Monitor logs and account

---

## Summary

**Most Common Commands:**
```bash
# Check status (tests connection)
python -m app.main --status

# Run once (test)
python -m app.main --once

# Run continuously
python -m app.main
```

That's it! Start with testing, then run once, then go continuous.


