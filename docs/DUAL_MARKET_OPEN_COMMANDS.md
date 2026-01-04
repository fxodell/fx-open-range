# Dual Market Open Strategy - Command Reference

Quick reference guide for starting, stopping, and monitoring the Dual Market Open Strategy.

## Quick Commands

### Start Strategy

```bash
# Start in background (recommended)
nohup python -m app.main > /dev/null 2>&1 &

# Start in foreground (press Ctrl+C to stop)
python -m app.main

# Start in screen (for remote servers)
screen -S trading
python -m app.main
# Press Ctrl+A then D to detach

# Start in tmux (for remote servers)
tmux new-session -s trading
python -m app.main
# Press Ctrl+B then D to detach
```

### Check Status

```bash
# Check account status, settings, and open positions
python -m app.main --status
```

### Monitor Logs

```bash
# View live logs (follow mode)
tail -f logs/trading_$(date +%Y%m%d).log

# View last 50 lines
tail -50 logs/trading_$(date +%Y%m%d).log

# Search for specific events
grep -i "EUR market open" logs/trading_$(date +%Y%m%d).log
grep -i "US market open" logs/trading_$(date +%Y%m%d).log
grep -i "signal" logs/trading_$(date +%Y%m%d).log
```

### Stop Strategy

```bash
# Find running process
ps aux | grep "python -m app.main"

# Stop by PID (replace <PID> with actual process ID)
kill <PID>

# Stop all Python trading processes
pkill -f "python -m app.main"

# If in screen: screen -r trading, then Ctrl+C
# If in tmux: tmux attach-session -t trading, then Ctrl+C
```

### Emergency Commands

```bash
# Close all open positions immediately
python -m app.main --close-all

# Run once (test mode, exits after one check)
python -m app.main --once
```

## Step-by-Step Checklist

### Before Starting

- [ ] Verify dual market open is enabled: `python -m app.main --status`
- [ ] Check OANDA API connection: `python -m app.main --status`
- [ ] Verify practice mode (unless ready for live): Check settings output
- [ ] Ensure application will run at market open times (8:00 and 13:00 UTC)

### Starting the Strategy

1. **Start the application:**
   ```bash
   python -m app.main
   ```

2. **Verify it's running:**
   ```bash
   ps aux | grep "python -m app.main"
   ```

3. **Check initial logs:**
   ```bash
   tail -20 logs/trading_$(date +%Y%m%d).log
   ```

### Daily Monitoring

- [ ] Check logs after EUR market open (8:00 UTC)
- [ ] Check logs after US market open (13:00 UTC)
- [ ] Verify trades executed correctly
- [ ] Monitor open positions: `python -m app.main --status`

### Stopping the Strategy

1. **Find the process:**
   ```bash
   ps aux | grep "python -m app.main"
   ```

2. **Stop gracefully:**
   ```bash
   kill <PID>
   ```

3. **Verify stopped:**
   ```bash
   ps aux | grep "python -m app.main"
   ```

## Market Open Times Reference

| Market | UTC Time | EST (Winter) | EDT (Summer) |
|--------|----------|--------------|--------------|
| EUR Open | 8:00 UTC | 3:00 AM | 4:00 AM |
| US Open | 13:00 UTC | 8:00 AM | 9:00 AM |
| Daily Close | 22:00 UTC | 5:00 PM | 6:00 PM |

## Common Issues

### Strategy Not Trading

**Check:**
1. Is dual market open enabled? `python -m app.main --status`
2. Is application running? `ps aux | grep "python -m app.main"`
3. Check logs for errors: `tail -100 logs/trading_$(date +%Y%m%d).log | grep -i error`

### Application Crashed

**Restart:**
```bash
# Check if running
ps aux | grep "python -m app.main"

# If not, restart
python -m app.main
```

### Need to Check What Happened

**Review logs:**
```bash
# View today's full log
cat logs/trading_$(date +%Y%m%d).log

# Search for specific events
grep -i "trade" logs/trading_$(date +%Y%m%d).log
grep -i "signal" logs/trading_$(date +%Y%m%d).log
grep -i "error" logs/trading_$(date +%Y%m%d).log
```

## See Also

- [Dual Market Open Guide](./DUAL_MARKET_OPEN_GUIDE.md) - Detailed setup and usage
- [Dual Market Open Strategy](./DUAL_MARKET_OPEN_STRATEGY.md) - Strategy documentation
- [app/README.md](../app/README.md) - Trading application documentation


