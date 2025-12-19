# Automated OANDA Trading Application

Automated trading application that implements the **Price Trend (SMA20) Directional** strategy on OANDA.

## ⚠️ IMPORTANT WARNINGS

1. **Practice Mode by Default**: The application defaults to practice mode. Use `--mode live` to enable live trading.
2. **Real Money Risk**: Live trading uses real money. Use at your own risk.
3. **No Guarantees**: Past performance does not guarantee future results.
4. **Test First**: Always test thoroughly in practice mode before considering live trading.

## Strategy Overview

**Price Trend (SMA20) Directional Strategy:**
- **BUY** when: Yesterday's Close > SMA20 (uptrend)
- **SELL** when: Yesterday's Close < SMA20 (downtrend)
- **Take Profit**: 10 pips
- **Stop Loss**: None (EOD exit if TP not hit)
- **Trades**: 1 trade per day maximum

**Backtested Performance (5 years):**
- Win Rate: 82.06%
- Total Pips: +7,945.95 pips
- Max Drawdown: 83.88 pips

## Installation

### Prerequisites

```bash
pip install requests pandas numpy
```

### Configuration

1. **API Token**: Set your OANDA API token in `app/config/settings.py` or use environment variable:
   ```bash
   export OANDA_API_TOKEN="your-token-here"
   ```

2. **Practice vs Live**: Default is practice mode. To enable live:
   ```bash
   export OANDA_PRACTICE_MODE="false"
   ```
   Or use `--mode live` command line argument.

## Usage

### Basic Usage

**Run once (check signal and execute if needed):**
```bash
python -m app.main --once
```

**Run continuously (check every 60 seconds):**
```bash
python -m app.main
```

**Run with custom check interval:**
```bash
python -m app.main --interval 300  # Check every 5 minutes
```

### Advanced Usage

**Check account status:**
```bash
python -m app.main --status
```

**Close all open positions:**
```bash
python -m app.main --close-all
```

**Force live mode (with confirmation):**
```bash
python -m app.main --mode live
```

**Run in practice mode explicitly:**
```bash
python -m app.main --mode practice
```

## Configuration

Edit `app/config/settings.py` to customize:

- `INSTRUMENT`: Trading pair (default: "EUR_USD")
- `TAKE_PROFIT_PIPS`: Take profit in pips (default: 10.0)
- `STOP_LOSS_PIPS`: Stop loss in pips (default: None = EOD exit)
- `POSITION_SIZE`: Position size in units (default: 1)
- `SMA_PERIOD`: SMA period for strategy (default: 20)
- `MAX_DAILY_TRADES`: Maximum trades per day (default: 1)
- `TRADING_START_HOUR`: Start of trading day UTC (default: 0)
- `TRADING_END_HOUR`: End of trading day UTC (default: 23)

## How It Works

1. **Data Collection**: Fetches last 30 days of daily candles from OANDA
2. **Signal Generation**: Calculates SMA20 and determines if price is above/below
3. **Signal Check**: 
   - BUY if Close > SMA20
   - SELL if Close < SMA20
   - FLAT otherwise
4. **Trade Execution**: 
   - Checks if already traded today (max 1 trade/day)
   - Checks for open positions
   - Places market order with TP if signal is valid
5. **Monitoring**: Continuously monitors open positions
6. **EOD Exit**: Positions close at end of day if TP not hit (no stop loss)

## Logging

Logs are saved to `logs/trading_YYYYMMDD.log` with:
- Signal generation
- Trade execution
- Errors and warnings
- Account status

## Safety Features

1. **Practice Mode Default**: Prevents accidental live trading
2. **Max Daily Trades**: Limits to 1 trade per day
3. **Position Check**: Won't open new position if one already exists
4. **Trading Hours**: Respects configured trading hours
5. **Error Handling**: Comprehensive error handling and logging

## Example Output

```
================================================================================
AUTOMATED OANDA TRADING APPLICATION
Strategy: Price Trend (SMA20) Directional
================================================================================

================================================================================
TRADING APPLICATION SETTINGS
================================================================================
API Mode: PRACTICE
Instrument: EUR_USD
Strategy: Price Trend (SMA20) Directional
Take Profit: 10.0 pips
Stop Loss: EOD Exit
Position Size: 1 units
SMA Period: 20
Max Daily Trades: 1
================================================================================
✓ Practice mode enabled (safe for testing)
⚠️  No stop loss set - trades will exit at end-of-day
================================================================================

Connecting to OANDA API...
✓ Connected successfully
  Account ID: 101-001-30925981-001
  Currency: USD
  Account Name: Practice Account

Starting continuous trading (check every 60 seconds)...
Press Ctrl+C to stop

2025-12-18 10:00:00 - TradingEngine - INFO - Signal: long, Price: 1.17250, SMA20: 1.17120
2025-12-18 10:00:01 - TradingEngine - INFO - Placing long order: 1 units, TP=10.0 pips
2025-12-18 10:00:02 - TradingEngine - INFO - Order placed successfully: {...}
```

## Troubleshooting

### Connection Errors
- Check API token is correct
- Verify internet connection
- Check OANDA API status

### Insufficient Data
- Strategy needs at least 20 days of data
- Wait for more historical data to accumulate

### Order Rejected
- Check account balance
- Verify instrument is available
- Check margin requirements

### No Signal Generated
- Price may be exactly at SMA20 (flat signal)
- Not enough historical data
- Check logs for details

## Risk Management

- **Position Sizing**: Start with smallest position size (1 unit = micro lot)
- **Testing**: Always test in practice mode first
- **Monitoring**: Monitor logs and account regularly
- **Stop Loss**: Consider adding stop loss if desired (modify settings)
- **Drawdown Limits**: Consider implementing max drawdown limits

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review OANDA API documentation
3. Test in practice mode first

## License

Use at your own risk. This is for educational purposes.

