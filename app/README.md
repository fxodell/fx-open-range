# Automated OANDA Trading Application

Automated trading application that implements **Price Trend (SMA20) Directional** strategies on OANDA:
- **Single Daily Open Strategy**: Trades at 22:00 UTC (daily candle open)
- **Dual Market Open Strategy**: Trades at EUR (8:00 UTC) and US (13:00 UTC) market opens (default, recommended)

## ⚠️ IMPORTANT WARNINGS

1. **Practice Mode by Default**: The application defaults to practice mode. Use `--mode live` to enable live trading.
2. **Real Money Risk**: Live trading uses real money. Use at your own risk.
3. **No Guarantees**: Past performance does not guarantee future results.
4. **Test First**: Always test thoroughly in practice mode before considering live trading.

## Strategy Overview

### Single Daily Open Strategy

**Price Trend (SMA20) Directional Strategy:**
- **BUY** when: Yesterday's Close > SMA20 (uptrend)
- **SELL** when: Yesterday's Close < SMA20 (downtrend)
- **Take Profit**: 10 pips
- **Stop Loss**: None (EOD exit if TP not hit)
- **Trades**: 1 trade per day maximum
- **Entry**: 22:00 UTC (daily candle open)

**Backtested Performance:**
- 5 years: Win Rate 82.06%, +7,945.95 pips, 83.88 pips max drawdown
- 12 months: +1,399 pips, 78% win rate, 240 trades

### Dual Market Open Strategy (Default, Recommended)

**Price Trend (SMA20) Directional - Dual Market:**
- **Same signal logic** as single daily open
- **EUR Market Open**: 8:00 UTC (London session)
- **US Market Open**: 13:00 UTC (New York session)
- **Take Profit**: 10 pips
- **Stop Loss**: None (EOD exit if TP not hit)
- **Trades**: Up to 2 trades per day (one per session, but only if first trade closed)
- **Position Limit**: Only one position open at a time

**12-Month Performance:**
- Total Pips: +2,900 pips (vs +1,399 for single daily open)
- Win Rate: 87.85% (vs 78.33% for single daily open)
- Trades: 428 (vs 240 for single daily open)
- **Improvement**: +107% more pips vs single daily open
- **Session Breakdown**:
  - EUR Market: +1,399 pips, 78% win rate, 240 trades
  - US Market: +1,501 pips, 100% win rate, 188 trades

**See:** [Dual Market Open Guide](../docs/DUAL_MARKET_OPEN_GUIDE.md) for setup instructions

## Installation

### Prerequisites

```bash
pip install -r requirements.txt
```

### Configuration

1. **API Token**: Create a `.env` file in the project root with your OANDA API token:
   ```bash
   cp .env.example .env
   # Edit .env and add your token:
   # OANDA_API_TOKEN=your-token-here
   ```
   
   Or set as an environment variable:
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
- `DUAL_MARKET_OPEN_ENABLED`: Enable dual market open trading (default: True)
- `EUR_MARKET_OPEN_HOUR`: EUR market open hour UTC (default: 8)
- `US_MARKET_OPEN_HOUR`: US market open hour UTC (default: 13)
- `MAX_DAILY_TRADES`: Maximum trades per day (default: 2 when dual market enabled, 1 otherwise)
- `TRADING_START_HOUR`: Start of trading day UTC (default: 22, used for single daily open)
- `TRADING_END_HOUR`: End of trading day UTC (default: 23, used for single daily open)

## How It Works

### Single Daily Open Mode (when DUAL_MARKET_OPEN_ENABLED = False)

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

### Dual Market Open Mode (Default, when DUAL_MARKET_OPEN_ENABLED = True)

1. **Data Collection**: Fetches last 30 days of daily candles from OANDA
2. **EUR Market Open (8:00 UTC)**:
   - Checks SMA20 signal
   - If signal valid and no open position → Enters trade
   - Monitors for 10 pip take-profit or end-of-day exit
3. **US Market Open (13:00 UTC)**:
   - Checks SMA20 signal
   - **Only trades if no open position** (skips if EUR trade still open)
   - If signal valid and no open position → Enters trade
   - Monitors for 10 pip take-profit or end-of-day exit
4. **Position Management**:
   - Only one position open at a time
   - Positions close at end-of-day (22:00 UTC) if TP not hit
   - No stop loss (EOD exit handles risk)

## Logging

Logs are saved to `logs/trading_YYYYMMDD.log` with:
- Signal generation
- Trade execution
- Errors and warnings
- Account status

## Safety Features

1. **Practice Mode Default**: Prevents accidental live trading
2. **Max Daily Trades**: Limits to 1 trade per day (single mode) or 2 trades per day (dual mode)
3. **Position Check**: Won't open new position if one already exists (only one position at a time)
4. **Trading Hours**: Respects configured trading hours or market open times
5. **Error Handling**: Comprehensive error handling and logging
6. **Session Tracking**: Tracks which session (EUR or US) opened each trade

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
Max Daily Trades: 2
Dual Market Open: ENABLED
EUR Market Open: 08:00 UTC
US Market Open: 13:00 UTC
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

2025-12-18 08:00:00 - TradingEngine - INFO - EUR market open detected (8:00 UTC)
2025-12-18 08:00:01 - TradingEngine - INFO - EUR Market Open - Signal: long, Price: 1.17250, SMA20: 1.17120
2025-12-18 08:00:02 - TradingEngine - INFO - Placing long order: 1 units, TP=10.0 pips
2025-12-18 08:00:03 - TradingEngine - INFO - Order placed successfully: {...}
2025-12-18 13:00:00 - TradingEngine - INFO - US market open detected (13:00 UTC)
2025-12-18 13:00:01 - TradingEngine - INFO - Already have 1 open position(s) - skipping
```

## Troubleshooting

### API Token Not Set

If you see an error about `OANDA_API_TOKEN` not being set:
1. Make sure you have created a `.env` file in the project root
2. Copy `.env.example` to `.env` if needed: `cp .env.example .env`
3. Add your token to `.env`: `OANDA_API_TOKEN=your-token-here`
4. Verify the `.env` file is in the project root (same directory as `requirements.txt`)

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

