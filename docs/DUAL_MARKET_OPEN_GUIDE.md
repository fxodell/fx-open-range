# Dual Market Open Strategy - Quick Start Guide

## Overview

The Dual Market Open Strategy trades at both EUR market open (8:00 UTC) and US market open (13:00 UTC), allowing up to 2 trades per day. Only one position can be open at a time.

**12-Month Performance:**
- Total Pips: +2,900 pips (vs +1,399 for single daily open)
- Win Rate: 87.85%
- Trades: 428 (vs 240 for single daily open)
- Improvement: +107% more pips

## Quick Commands

### Start the Strategy

**Option 1: systemd Service (Recommended for Production)**
```bash
# Install and start the service (runs in background, auto-restarts, starts on boot)
sudo /opt/fx-open-range/setup-service.sh
sudo systemctl start fx-open-range

# Check status
sudo systemctl status fx-open-range

# View logs
sudo journalctl -u fx-open-range -f
```

**Option 2: Run Continuously (Manual)**
```bash
# Start in background (runs continuously, checks every 60 seconds)
nohup python -m app.main > /dev/null 2>&1 &

# Or run in foreground (press Ctrl+C to stop)
python -m app.main
```

**Option 3: Run in Screen/Tmux (For Remote Servers)**
```bash
# Using screen
screen -S trading
python -m app.main
# Press Ctrl+A then D to detach

# Using tmux
tmux new-session -s trading
python -m app.main
# Press Ctrl+B then D to detach
```

**Option 4: Run Once (Testing)**
```bash
# Check signal and execute if needed (exits after one check)
python -m app.main --once
```

### Check Status

```bash
# Check account status, open positions, and settings
python -m app.main --status
```

### Monitor Logs

```bash
# View live logs (follow mode)
tail -f logs/trading_$(date +%Y%m%d).log

# View last 50 lines
tail -50 logs/trading_$(date +%Y%m%d).log

# View today's log file
cat logs/trading_$(date +%Y%m%d).log
```

### Stop the Strategy

**If running in foreground:**
- Press `Ctrl+C`

**If running in background:**
```bash
# Find the process
ps aux | grep "python -m app.main"

# Kill the process (replace PID with actual process ID)
kill <PID>

# Or kill all Python trading processes
pkill -f "python -m app.main"
```

**If running in screen:**
```bash
# Reattach to screen
screen -r trading

# Then press Ctrl+C to stop
```

**If running in tmux:**
```bash
# Reattach to tmux
tmux attach-session -t trading

# Then press Ctrl+C to stop
```

### Close All Positions (Emergency)

```bash
# Close all open positions immediately
python -m app.main --close-all
```

## Step-by-Step Setup

### 1. Verify Configuration

```bash
# Check current settings
python -c "from app.config.settings import Settings; Settings.print_settings()"
```

**Expected Output:**
- Dual Market Open: **ENABLED**
- EUR Market Open: 08:00 UTC
- US Market Open: 13:00 UTC
- Max Daily Trades: 2

### 2. Test Connection

```bash
# Test OANDA API connection
python -m app.main --status
```

**Expected Output:**
- Account status
- Open positions (if any)
- Settings confirmation

### 3. Start the Strategy

```bash
# Start continuously (recommended)
python -m app.main
```

The application will:
- Check every 60 seconds
- Trade at EUR market open (8:00 UTC)
- Trade at US market open (13:00 UTC) if no open position
- Log all activity to `logs/trading_YYYYMMDD.log`

### 4. Monitor Activity

**Watch for these log messages:**
- `"EUR market open detected (8:00 UTC)"` - EUR session check
- `"US market open detected (13:00 UTC)"` - US session check
- `"Signal: long/short"` - Signal generated
- `"Order placed successfully"` - Trade executed
- `"EUR trade still open - skipping"` - US trade skipped (EUR still open)

## Market Open Times (UTC)

- **EUR Market Open**: 8:00 UTC (London session)
- **US Market Open**: 13:00 UTC (New York session, 8:00 AM EST)

**Convert to your timezone:**
- 8:00 UTC = 3:00 AM EST / 4:00 AM EDT
- 13:00 UTC = 8:00 AM EST / 9:00 AM EDT

## Strategy Behavior

1. **EUR Market Open (8:00 UTC)**:
   - Checks SMA20 signal
   - If signal valid and no open position → Enters trade
   - Monitors for 10 pip take-profit or end-of-day exit

2. **US Market Open (13:00 UTC)**:
   - Checks SMA20 signal
   - **Only trades if no open position** (skips if EUR trade still open)
   - If signal valid and no open position → Enters trade
   - Monitors for 10 pip take-profit or end-of-day exit

3. **Position Management**:
   - Only one position open at a time
   - Positions close at end-of-day (22:00 UTC) if TP not hit
   - No stop loss (EOD exit handles risk)

## Troubleshooting

### Strategy Not Trading

**Check:**
1. Is dual market open enabled?
   ```bash
   python -c "from app.config.settings import Settings; print(f'Dual Market Open: {Settings.DUAL_MARKET_OPEN_ENABLED}')"
   ```

2. Is application running at market open times?
   - EUR: 8:00 UTC
   - US: 13:00 UTC

3. Check logs for errors:
   ```bash
   tail -100 logs/trading_$(date +%Y%m%d).log | grep -i error
   ```

### No Trades Executing

**Possible reasons:**
- No valid signal (price not clearly above/below SMA20)
- Already traded today (max 2 trades per day)
- Open position exists (only one position at a time)
- Outside market open windows

**Check:**
```bash
# View recent log entries
tail -50 logs/trading_$(date +%Y%m%d).log

# Check for signal generation
grep -i "signal" logs/trading_$(date +%Y%m%d).log | tail -10
```

### Application Crashed

**Restart:**
```bash
# Check if still running
ps aux | grep "python -m app.main"

# If not running, restart
python -m app.main
```

## Best Practices

1. **Start Before Market Opens**: Start the application at least 5 minutes before 8:00 UTC (EUR open)

2. **Monitor First Few Days**: Watch logs closely for the first few days to ensure proper operation

3. **Use Practice Mode First**: Always test in practice mode before live trading

4. **Check Daily**: Review logs daily to ensure strategy is working correctly

5. **Keep Application Running**: The application must be running at both market open times (8:00 and 13:00 UTC)

## Configuration

Edit `app/config/settings.py` to adjust:

```python
DUAL_MARKET_OPEN_ENABLED: bool = True  # Enable/disable dual market open
EUR_MARKET_OPEN_HOUR: int = 8  # EUR market open hour (UTC)
US_MARKET_OPEN_HOUR: int = 13  # US market open hour (UTC)
MAX_DAILY_TRADES: int = 2  # Max trades per day
TAKE_PROFIT_PIPS: float = 10.0  # Take profit in pips
```

## Time Zone Reference

**Market Open Times:**
- **EUR Open**: 8:00 UTC = 3:00 AM EST / 4:00 AM EDT
- **US Open**: 13:00 UTC = 8:00 AM EST / 9:00 AM EDT

**Daily Candle Close**: 22:00 UTC = 5:00 PM EST / 6:00 PM EDT

## Support

For more information:
- See [DUAL_MARKET_OPEN_STRATEGY.md](./DUAL_MARKET_OPEN_STRATEGY.md) for detailed strategy documentation
- See [CONTEXT.md](./CONTEXT.md) for project context
- Check logs in `logs/trading_YYYYMMDD.log` for detailed activity





