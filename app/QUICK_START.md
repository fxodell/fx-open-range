# Quick Start Guide

## 🚀 Quick Start (2 Steps)

### 1. Check Status (Tests Connection)
```bash
python -m app.main --status
```

### 2. Run Trading (Practice Mode)
```bash
# Run once (check and execute if needed)
python -m app.main --once

# Run continuously (check every 60 seconds)
python -m app.main
```

## 📋 Common Commands

```bash
# Show account status
python -m app.main --status

# Run once (no loop)
python -m app.main --once

# Run with custom check interval (5 minutes)
python -m app.main --interval 300

# Close all open positions
python -m app.main --close-all

# Live mode (WARNING: Real money!)
python -m app.main --mode live
```

## ⚙️ Configuration

Edit `app/config/settings.py`:

```python
# Trading settings
INSTRUMENT = "EUR_USD"
TAKE_PROFIT_PIPS = 10.0
STOP_LOSS_PIPS = None  # None = EOD exit
POSITION_SIZE = 1  # Units (1 = micro lot)

# Strategy settings
SMA_PERIOD = 20

# Risk management
MAX_DAILY_TRADES = 1
```

## 📊 How It Works

1. **Fetches** last 30 days of EUR/USD daily candles
2. **Calculates** SMA20 moving average
3. **Determines** signal:
   - **LONG** if Close > SMA20
   - **SHORT** if Close < SMA20
   - **FLAT** otherwise
4. **Executes** trade if signal is valid:
   - Checks if already traded today (max 1/day)
   - Checks for open positions
   - Places market order with 10 pip TP
5. **Monitors** open positions
6. **Exits** at end of day if TP not hit (no stop loss)

## 🔍 Monitoring

**Logs**: Check `logs/trading_YYYYMMDD.log`

**Account**: Run `python -m app.main --status`

**Live**: Run `python -m app.main` and watch console output

## ⚠️ Safety Features

- ✅ **Practice mode by default**
- ✅ **Max 1 trade per day**
- ✅ **Position checking** (won't double up)
- ✅ **Error handling** and logging
- ✅ **Trading hours** check

## 📈 Expected Behavior

- **Trades once per day** (at most)
- **Closes positions** at end of day if TP not hit
- **No stop loss** (EOD exit handles risk)
- **Only trades** when signal is clear (long/short)

## 🐛 Troubleshooting

**"Insufficient data"**: Wait for more historical data to accumulate (needs 20+ days)

**"Already traded today"**: Normal - max 1 trade per day limit

**"Already have open position"**: Normal - won't open duplicate position

**Connection errors**: Check API token and internet connection

## 📚 Full Documentation

See `app/README.md` for complete documentation.

