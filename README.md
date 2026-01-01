# FX Open-Range Lab

Quantitative research and backtesting framework for EUR/USD "trade at the open" strategies.

## Overview

This project provides a comprehensive Python framework for:
- Analyzing EUR/USD daily ranges and open-based movements
- Detecting market regimes (bull/bear/chop)
- Designing and backtesting systematic trade-at-open strategies
- Automated trading on OANDA with the best-performing strategies
- Exploring additional factors (macro events, volatility patterns, etc.)

The project consists of two main components:
1. **Backtesting Framework** (`src/`): Research and test trading strategies on historical data
2. **Trading Application** (`app/`): Automated trading on OANDA using Price Trend (SMA20) Directional strategies
   - **Single Daily Open Strategy**: Trades at 22:00 UTC (daily candle open)
   - **Dual Market Open Strategy**: Trades at EUR (8:00 UTC) and US (13:00 UTC) market opens

## Project Structure

```
fx-open-range-project/
├── app/                     # Automated OANDA trading application
│   ├── main.py             # Trading application entry point
│   ├── trading_engine.py   # Core trading logic
│   ├── config/             # Configuration (API tokens, settings)
│   │   └── settings.py     # Trading settings and configuration
│   ├── strategies/         # Strategy implementations
│   │   ├── sma20_strategy.py
│   │   └── dual_market_open_strategy.py
│   ├── utils/              # OANDA API client
│   │   └── oanda_client.py
│   ├── README.md           # Trading app documentation
│   ├── HOW_TO_RUN.md       # Detailed run instructions
│   ├── QUICK_START.md      # Quick start guide
│   └── TRADE_TIMING.md     # Trading hours and timing details
├── src/                    # Backtesting framework
│   ├── data_loader.py      # Data loading and cleaning
│   ├── core_analysis.py    # Range calculations, distributions, MFE/MAE
│   ├── regime.py           # Market regime detection
│   ├── backtest.py         # Backtesting engine
│   ├── backtest_no_sl.py   # No-stop-loss backtesting engine
│   ├── backtest_dual_market.py  # Dual market open backtesting engine
│   ├── market_sessions.py  # Market session utilities
│   ├── strategies.py       # Strategy definitions
│   ├── oanda_api.py        # OANDA API utilities
│   └── main.py             # Main analysis (module)
├── data/                   # Historical EUR/USD OHLC data
│   ├── eur_usd.csv
│   ├── eur_usd_long_term.csv
│   └── eur_usd_oanda.csv
├── docs/                   # Additional documentation
│   ├── CONTEXT.md          # Project context
│   ├── TASKS.md            # Task tracking
│   └── *.md                # Other documentation files
├── logs/                   # Trading application logs
│   └── trading_YYYYMMDD.log
├── requirements.txt        # Python dependencies
├── STRATEGY_EXPLANATION.md # Detailed strategy documentation
└── README.md
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. **For Trading Application (OANDA):**
   - Set up OANDA API credentials:
     ```bash
     # Create .env file in project root (or set environment variables)
     export OANDA_API_TOKEN="your-api-token-here"
     export OANDA_PRACTICE_MODE="true"  # Use practice account (default)
     export OANDA_ACCOUNT_ID="your-account-id"  # Optional, will auto-detect if not set
     ```
   - See `app/README.md` for detailed setup instructions

3. **For Backtesting Framework:**
   - Ensure your EUR/USD data is in `data/eur_usd.csv` with columns:
     - Date (MM/DD/YYYY format)
     - Price (Close price)
     - Open
     - High
     - Low

## Usage

### Backtesting Framework

**Run full backtesting analysis:**
```bash
python -m src.main
```

This will:
1. Load and clean the EUR/USD data
2. Calculate daily range metrics and distributions
3. Detect market regimes (bull/bear/chop)
4. Backtest multiple strategies
5. Display comprehensive performance metrics
6. **Compare single vs dual market open strategies**

**Run 12-month backtest comparison:**
```bash
python backtest_12month.py
```

This compares single daily open vs dual market open strategies over the past 12 months.

### Automated Trading Application

For automated trading on OANDA, see the [Trading Application documentation](app/README.md).

**Quick start:**
```bash
# Check account status (tests connection)
python -m app.main --status

# Run once (practice mode - check signal and execute if needed)
python -m app.main --once

# Run continuously (checks every 60 seconds)
python -m app.main
```

**Available Strategies:**

1. **Single Daily Open Strategy** (Default when dual market disabled):
   - **Trading window:** 22:00-23:00 UTC (EUR/USD daily candle open)
   - **12-Month Performance:** +1,399 pips, 78% win rate, 240 trades
   - **Max trades:** 1 per day

2. **Dual Market Open Strategy** (Recommended - enabled by default):
   - **Trading windows:** 8:00 UTC (EUR open) and 13:00 UTC (US open)
   - **12-Month Performance:** +2,900 pips, 87% win rate, 428 trades
   - **Improvement:** +107% more pips vs single daily open
   - **Max trades:** 2 per day (one per session, but only if first trade closed)
   - See [Dual Market Open Guide](docs/DUAL_MARKET_OPEN_GUIDE.md) for setup

**Common Features:**
- **Practice mode by default** (safe for testing)
- **Strategy:** Price Trend (SMA20) Directional
- **Take Profit:** 10 pips
- **Stop Loss:** None (EOD exit if TP not hit)
- **Position size:** 1 unit (micro lot)

See `app/HOW_TO_RUN.md` for detailed instructions and `app/TRADE_TIMING.md` for timing details.

## Core Analysis

The framework calculates:

- **Daily Range Metrics:**
  - `range_pips`: High - Low in pips
  - `up_from_open_pips`: High - Open in pips
  - `down_from_open_pips`: Open - Low in pips
  - `net_from_open_pips`: Close - Open in pips

- **Distribution Statistics:**
  - Mean, median, std, percentiles (10/25/50/75/90/95/99)
  - Frequency of pip movements (5, 10, 15, 20+ pips)
  - Maximum Favorable/Adverse Excursion (MFE/MAE)

- **Average Daily Range (ADR):**
  - Rolling ADR calculation (default 20-day window)

## Market Regime Detection

Regimes are classified using:
- Moving averages (SMA20, SMA50, SMA100, SMA200)
- Momentum indicators (1/3/6 month returns)
- Trend direction (MA slopes)

**Classification Rules:**
- **Bull**: Price > SMA50 > SMA200 AND SMA50 trending up
- **Bear**: Price < SMA50 < SMA200 AND SMA50 trending down
- **Chop**: Everything else

## Strategies

The framework includes two production-ready strategies based on comprehensive backtesting:

### 1. Single Daily Open Strategy

**Price Trend (SMA20) Directional:**
- **Logic:** Buy when yesterday's Close > SMA20 (uptrend), Sell when yesterday's Close < SMA20 (downtrend)
- **Backtest Performance (5 years):** 82.06% win rate, +7,945.95 pips, 83.88 pips max drawdown
- **12-Month Performance:** +1,399 pips, 78% win rate, 240 trades
- **Live Trading Parameters:**
  - Take Profit: 10 pips
  - Stop Loss: None (exit at end-of-day if TP not hit)
  - Entry: At daily open (22:00 UTC)
  - Max 1 trade per day

### 2. Dual Market Open Strategy (Recommended)

**Price Trend (SMA20) Directional - Dual Market:**
- **Logic:** Same SMA20 logic, trades at both EUR and US market opens
- **12-Month Performance:** +2,900 pips, 87% win rate, 428 trades
- **Improvement:** +107% more pips vs single daily open
- **Live Trading Parameters:**
  - Take Profit: 10 pips
  - Stop Loss: None (exit at end-of-day if TP not hit)
  - Entry: EUR market open (8:00 UTC) and/or US market open (13:00 UTC)
  - Max 2 trades per day (one per session, but only if first trade closed)
  - Only one position open at a time
- **Session Performance:**
  - EUR Market: +1,399 pips, 78% win rate, 240 trades
  - US Market: +1,501 pips, 100% win rate, 188 trades
- **See:** [Dual Market Open Guide](docs/DUAL_MARKET_OPEN_GUIDE.md) for setup and [Dual Market Open Strategy](docs/DUAL_MARKET_OPEN_STRATEGY.md) for details

**See:** [Strategy Documentation](STRATEGY_EXPLANATION.md) for full details

### Adding Custom Strategies

**For Backtesting:**

Create a function in `src/strategies.py` that takes `df` and returns a `pd.Series` with signals ('long', 'short', 'flat'):

```python
def my_custom_strategy(df: pd.DataFrame, **kwargs) -> pd.Series:
    signals = pd.Series('flat', index=df.index)
    # Your logic here
    return signals
```

Then add it to the `STRATEGIES` dictionary in `src/strategies.py`.

**For Live Trading:**

Implement your strategy in `app/strategies/` following the pattern in `sma20_strategy.py`, then integrate it into `app/trading_engine.py`.

## Backtesting

The backtesting engine:

- Simulates trades at the daily open
- Handles take-profit and stop-loss orders
- Assumes conservative execution (SL hit first if both TP/SL possible)
- Includes transaction costs (default 2 pips per trade)
- Calculates comprehensive metrics:
  - Total pips, win rate, profit factor
  - Max drawdown (pips and %)
  - Sharpe-like metrics
  - Average win/loss

### Backtest Parameters

**Note:** Backtesting uses different parameters than live trading for research purposes.

**Backtesting defaults:**
- `take_profit_pips`: 20.0 pips
- `stop_loss_pips`: 20.0 pips
- `cost_per_trade_pips`: 2.0 pips (spread + commission)
- `initial_equity`: 10000.0

**Live trading parameters** (configured in `app/config/settings.py`):
- `take_profit_pips`: 10.0 pips
- `stop_loss_pips`: None (EOD exit)
- `position_size`: 1 unit (micro lot)
- `dual_market_open_enabled`: True (default, recommended)
- `eur_market_open_hour`: 8 (8:00 UTC)
- `us_market_open_hour`: 13 (13:00 UTC)
- `max_daily_trades`: 2 (when dual market enabled)
- `trading_hours`: 22:00-23:00 UTC (used only when dual market disabled)

These differences reflect the strategy optimization: the 10-pip TP with EOD exit has shown better risk-adjusted returns in testing.

## Performance Metrics

Each backtest reports:

- **Absolute Performance:**
  - Total pips
  - Average pips per trade/day

- **Win Rate & Profitability:**
  - Win rate (%)
  - Average win/loss
  - Profit factor (gross profit / gross loss)

- **Risk Metrics:**
  - Maximum drawdown (pips and %)
  - Sharpe ratio (pips and annualized)

- **Trade Statistics:**
  - Total trades (long vs short)

## Important Notes

### Data Requirements

**For Backtesting:**
- The framework expects daily OHLC data in `data/eur_usd.csv`
- Dates should be in chronological order (oldest first)
- Missing data is automatically removed
- Required columns: Date, Open, High, Low, Close

**For Live Trading:**
- Data is fetched automatically from OANDA API
- Requires 20+ days of historical data for SMA20 calculation
- Uses daily candles (granularity "D")

### Lookahead Bias Prevention

All calculations use only information available at the time:
- Regime classification uses only prior closes
- ADR uses rolling windows (no future data)
- Signals are generated before trade execution
- Strategy uses `shift(1)` to ensure yesterday's close is used (not today's)

### Transaction Costs

**Backtesting:** Default assumption is 2 pips per trade (spread + commission). Adjust in backtest functions if needed.

**Live Trading:** Actual spread costs are handled by OANDA. The strategy accounts for spread in take-profit calculations.

### Trading Hours

**Single Daily Open Strategy:**
- Trades during 1-hour window (22:00-23:00 UTC) at daily candle open
- Configuration: `TRADING_START_HOUR: 22`, `TRADING_END_HOUR: 23`

**Dual Market Open Strategy (Default):**
- Trades at EUR market open: 8:00 UTC (London session)
- Trades at US market open: 13:00 UTC (New York session, 8:00 AM EST)
- Configuration: `DUAL_MARKET_OPEN_ENABLED: True` in `app/config/settings.py`

**Configuration:** Trading settings can be adjusted in `app/config/settings.py`

### Limitations

- Daily OHLC data limits precision for intraday TP/SL hits in backtesting
- Conservative assumption: if both TP and SL could be hit, SL is assumed
- For more precise execution analysis, intraday data is recommended
- Live trading requires stable internet connection and OANDA API access

## Logging and Monitoring

**Trading Application:**
- Logs are written to `logs/trading_YYYYMMDD.log`
- Includes signal generation, trade execution, errors, and account status
- View logs: `tail -f logs/trading_$(date +%Y%m%d).log`

**Monitoring Commands:**
```bash
# Check account status and open positions
python -m app.main --status

# View recent logs
tail -20 logs/trading_$(date +%Y%m%d).log
```

## Disclaimer

**This is research software for historical analysis and automated trading.**

- Historical backtests do NOT guarantee future performance
- All strategies should be tested with out-of-sample data
- Risk management is critical - size positions conservatively
- Consider well under 1% risk per trade
- Results are subject to overfitting and market regime changes
- **Live trading uses real money** - always test in practice mode first
- The application defaults to practice mode for safety

## Future Enhancements

Potential areas for extension:

- **Macro Event Integration:**
  - Tag ECB, FOMC, NFP, CPI release dates
  - Compare volatility on event vs normal days
  - Skip trading near major releases

- **Inter-Market Analysis:**
  - DXY, equity indices, bond yields
  - Risk-on/risk-off regimes
  - Volatility indices (VIX)

- **Advanced Features:**
  - Session-specific signal optimization (different logic for EUR vs US opens)
  - Adaptive TP/SL based on ADR or session
  - Day-of-week patterns
  - Calendar effects (month-end, quarter-end)
  - Intraday refinement with M5/M15/H1 data for accurate market open prices

## License

This project is for research purposes only.

