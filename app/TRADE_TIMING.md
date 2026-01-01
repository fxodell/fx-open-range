# Trade Timing Explanation

## Current Behavior

The application will execute trades **whenever it checks and finds a valid signal**, within the configured trading hours.

**Default Settings:**
- **Trading Hours**: 0-23 UTC (all day, 24 hours)
- **Check Interval**: 60 seconds (when running continuously)
- **Max Daily Trades**: 1 per day

This means:
- If you run `python -m app.main` (continuous mode), it checks every 60 seconds
- If a valid signal exists and conditions are met, it trades immediately
- Once it trades once, it won't trade again until the next day

## EUR/USD Daily Candle Schedule

For EUR/USD, OANDA uses **New York close** (22:00 UTC) as the daily candle boundary:

- **Daily Candle CLOSE**: 22:00 UTC (5:00 PM EST / 6:00 PM EDT)
- **Daily Candle OPEN**: 22:00 UTC (new trading day starts)
- **Daily Candle includes**: Price action from 22:00 UTC to 22:00 UTC next day

## Optimal Timing for "Trade at the Open" Strategy

Since the strategy is designed to trade **at the daily open**, optimal timing is:

1. **Wait for daily close**: After 22:00 UTC, the previous day's candle is complete
2. **Check signal**: Use yesterday's close vs SMA20 to determine direction
3. **Execute trade**: Shortly after 22:00 UTC (at the daily open)

### Recommended Configuration

To trade optimally "at the open", modify `app/config/settings.py`:

```python
# Trading Hours (UTC)
TRADING_START_HOUR: int = 22  # 22:00 UTC = daily open
TRADING_END_HOUR: int = 23    # Give 1 hour window to execute
```

This ensures:
- Trades only execute between 22:00-23:00 UTC (at daily open)
- Signal is based on the completed previous day's candle
- You're trading at the actual daily open price

## Example Schedule

**Current Day (e.g., December 18):**
- 22:00 UTC: Daily candle closes for December 18
- Signal calculated using December 18's close vs SMA20
- Trade executes at 22:00 UTC (December 19 candle opens)

**Next Day (December 19):**
- Trade is active throughout December 19
- If TP hits → Trade closes automatically
- If TP doesn't hit → Trade closes at 22:00 UTC (EOD exit)

## Time Zone Conversions

**22:00 UTC = Daily Open:**
- **EST (Winter)**: 5:00 PM
- **EDT (Summer)**: 6:00 PM
- **GMT**: 10:00 PM
- **CET**: 11:00 PM (23:00)

## Configuration Options

### Option 1: Trade Only at Daily Open (Recommended)

```python
TRADING_START_HOUR: int = 22  # 22:00 UTC
TRADING_END_HOUR: int = 23    # 23:00 UTC
```

**Pros:**
- ✅ Trades at actual daily open
- ✅ Signal based on completed candle
- ✅ Matches backtested strategy timing

**Cons:**
- ⚠️ Narrow window (only 1 hour)
- ⚠️ If app is down at 22:00 UTC, might miss trade

### Option 2: Wider Window (Current Default)

```python
TRADING_START_HOUR: int = 0   # 00:00 UTC
TRADING_END_HOUR: int = 23    # 23:00 UTC
```

**Pros:**
- ✅ More flexibility (anytime during day)
- ✅ Won't miss trades if app runs all day
- ✅ Can catch up if app restarts

**Cons:**
- ⚠️ Might trade later than daily open
- ⚠️ Entry price might differ from backtest

### Option 3: Extended Window (Conservative)

```python
TRADING_START_HOUR: int = 22  # 22:00 UTC
TRADING_END_HOUR: int = 1     # 01:00 UTC (next day)
```

**Pros:**
- ✅ Captures daily open
- ✅ 3-hour window for reliability

**Cons:**
- ⚠️ Handles midnight crossing (code supports this)

## How to Check Current Settings

```bash
python -c "from app.config.settings import Settings; print(f'Trading Hours: {Settings.TRADING_START_HOUR:02d}:00 - {Settings.TRADING_END_HOUR:02d}:00 UTC')"
```

## Testing Trade Timing

To test when trades would execute:

```bash
# Run once and check logs
python -m app.main --once

# Check logs
tail -f logs/trading_$(date +%Y%m%d).log
```

## Recommended Configuration

**Option 1** (22:00-23:00 UTC) is recommended for the **Price Trend (SMA20) Directional** strategy:

1. Matches the backtested strategy (trades at open)
2. Signal is based on completed daily candle
3. Entry price matches backtest assumptions

Configure in `app/config/settings.py`:

```python
TRADING_START_HOUR: int = 22
TRADING_END_HOUR: int = 23
```

Then restart the application.

