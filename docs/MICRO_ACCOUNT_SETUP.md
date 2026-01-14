# Micro Account Setup Guide

This guide explains how to configure the trading system for micro account trading ($0.10 per pip) and switch to live account trading.

## Position Size Configuration

### Current Configuration (Micro Account)

The position size has been set to **1,000 units (1 micro lot)** which equals **$0.10 per pip** for EUR/USD trading.

**Configuration Location:** `app/config/settings.py`
```python
POSITION_SIZE: int = 1000  # Units (1 micro lot = $0.10 per pip for EUR/USD)
```

### Position Size Reference

For EUR/USD trading:
- **1 micro lot** = 1,000 units = **$0.10 per pip** ✓ (Current setting)
- **1 mini lot** = 10,000 units = $1.00 per pip
- **1 standard lot** = 100,000 units = $10.00 per pip

### Changing Position Size

To change the position size, edit `app/config/settings.py`:

```python
# For micro account ($0.10 per pip):
POSITION_SIZE: int = 1000

# For mini account ($1.00 per pip):
POSITION_SIZE: int = 10000

# For standard account ($10.00 per pip):
POSITION_SIZE: int = 100000
```

**⚠️ Warning:** Only change position size if you understand the risk implications. Larger positions = larger potential profits AND losses.

---

## Switching to Live Account

You have two options to switch from practice to live trading:

### Option 1: Use Command Line Flag (Recommended for Testing)

```bash
# Run in live mode with confirmation prompt
python -m app.main --mode live
```

**Safety Features:**
- Prompts for confirmation before connecting to live account
- You must type "yes" to proceed
- Easy to switch back to practice mode

### Option 2: Set Environment Variable in `.env` File (Permanent)

Edit your `.env` file in the project root:

```bash
# Practice mode (default, safe)
OANDA_PRACTICE_MODE=true

# Live mode (real money!)
OANDA_PRACTICE_MODE=false
```

**⚠️ Important Notes:**
- Once set to `false` in `.env`, the application will default to live mode
- You can still override with `--mode practice` command line flag
- Make sure your live API token is in `.env` as `OANDA_API_TOKEN`
- Always test thoroughly in practice mode first!

---

## Complete `.env` File Example

```bash
# OANDA API Configuration
OANDA_API_TOKEN=your-live-api-token-here
OANDA_PRACTICE_MODE=false
OANDA_ACCOUNT_ID=your-account-id-here  # Optional, will auto-detect if not set
```

---

## Verification Steps

### 1. Verify Position Size

Run the status command to see current settings:

```bash
python -m app.main --status
```

Look for:
```
Position Size: 1000 units
✓ Micro account: 1000 units = $0.10 per pip
```

### 2. Verify Account Mode

Check the settings output:
```
API Mode: LIVE  (or PRACTICE)
```

### 3. Test Connection

```bash
# Test practice mode
python -m app.main --mode practice --status

# Test live mode (with confirmation)
python -m app.main --mode live --status
```

---

## Example: Full Live Trading Setup

### Step 1: Configure `.env` file

```bash
cd /opt/fx-open-range
nano .env  # or your preferred editor
```

Add:
```bash
OANDA_API_TOKEN=your-live-token-here
OANDA_PRACTICE_MODE=false
```

### Step 2: Verify Configuration

```bash
python -m app.main --status
```

Expected output:
```
API Mode: LIVE
Position Size: 1000 units
✓ Micro account: 1000 units = $0.10 per pip
⚠️  LIVE MODE ENABLED - Real money trading!
```

### Step 3: Test Run (Live Mode)

```bash
python -m app.main --mode live --once
```

You'll be prompted:
```
⚠️  LIVE MODE - This will trade with REAL MONEY! Continue? (yes/no):
```

Type `yes` to proceed (or `no` to cancel).

### Step 4: Start Continuous Trading

```bash
python -m app.main --mode live
```

---

## Risk Management Reminders

When trading with real money:

1. **Position Size**: Current setting is 1,000 units ($0.10 per pip) - suitable for micro accounts
2. **Take Profit**: 10 pips = $1.00 profit per winning trade
3. **Stop Loss**: None (EOD exit only) - positions exit at end of day if TP not hit
4. **Max Trades**: 2 per day (one at EUR market open 8:00 UTC, one at US market open 13:00 UTC)
5. **Monitor**: Check account regularly, monitor logs

---

## Switching Back to Practice Mode

### If Using Command Line Flag:
```bash
python -m app.main --mode practice
```

### If Using `.env` File:
Change `.env`:
```bash
OANDA_PRACTICE_MODE=true
```

---

## Troubleshooting

### "LIVE MODE ENABLED" Warning

This is normal when `OANDA_PRACTICE_MODE=false`. Verify you're ready before trading.

### Position Size Not Showing Correctly

Check that `app/config/settings.py` has:
```python
POSITION_SIZE: int = 1000
```

### Cannot Connect to Live Account

1. Verify `OANDA_API_TOKEN` in `.env` is your **live** token (not practice token)
2. Live tokens start with different prefixes than practice tokens
3. Check OANDA account status and API access

---

## Summary

✅ **Position Size**: Set to 1,000 units ($0.10 per pip) - **COMPLETE**
✅ **Live Mode**: Use `--mode live` or set `OANDA_PRACTICE_MODE=false` in `.env`

**Next Steps:**
1. Verify position size with `--status` command
2. Test in practice mode first: `python -m app.main --mode practice --once`
3. When ready, switch to live: `python -m app.main --mode live`
4. Monitor logs and account balance
