> This file is the single source of truth for humans and AI agents.
> All agents must read this before making changes.

# Project Context

## What we're building
- **Product**: FX Open-Range Lab - Quantitative research and backtesting framework for EUR/USD trading strategies
- **Users**: Quantitative researchers, traders, and developers working on forex strategies
- **Primary goal**: Develop, backtest, and deploy systematic "trade at the open" strategies for EUR/USD

## Current status
- **Working**: 
  - Backtesting framework (`src/`) with comprehensive metrics and dual market open support
  - Automated trading application (`app/`) with SMA20 strategy
  - **Dual Market Open Strategy (DEFAULT, ENABLED)** - trades at both EUR (8:00 UTC) and US (13:00 UTC) market opens
    - Shows +107% improvement over single daily open (12-month backtest: +2,900 pips vs +1,399 pips)
    - Default configuration in `app/config/settings.py`
    - **Same-Direction Position Logic**: Keeps existing position if new signal is same direction (saves 4 pips spread costs per trade)
  - Single Daily Open Strategy (still available, can be enabled by setting `DUAL_MARKET_OPEN_ENABLED = False`)
  - Market regime detection (bull/bear/chop)
  - OANDA API integration with full trading operations (practice and live modes)
  - Fixed OANDA API datetime formatting to prevent 400 Bad Request errors (RFC3339 format with microseconds stripped)
  - Historical data analysis and range calculations
  - Comprehensive CLI interface with multiple commands (`--once`, `--status`, `--close-all`, `--mode`, `--interval`)
  - Daily logging system with file (DEBUG) and console (INFO) handlers (`logs/trading_YYYYMMDD.log`)
  - Comprehensive error handling and graceful error recovery throughout
  - Account monitoring and status reporting
  - Trading hours configuration: Dual market opens (8:00 and 13:00 UTC) by default, or single daily open (22:00-23:00 UTC) when disabled

- **Broken**: 
  - None currently known

- **In progress**: 
  - Strategy research and optimization
  - Additional strategy development

## Architecture snapshot
- **Frontend**: None (CLI-based application)
- **Backend**: Python-based trading engine and backtesting framework
  - **Trading Application** (`app/`):
    - Trading Engine (`app/trading_engine.py`): Core trading logic, signal generation, trade execution, dual/single mode routing
    - OANDA Client (`app/utils/oanda_client.py`): OANDA API wrapper for all trading operations (orders, positions, pricing, candles)
    - Strategy Modules:
      - `app/strategies/sma20_strategy.py`: Core SMA20 strategy implementation (used by both modes)
      - `app/strategies/dual_market_open_strategy.py`: Dual market open strategy wrapper and market open time checks
    - Settings (`app/config/settings.py`): Centralized configuration management (DUAL_MARKET_OPEN_ENABLED defaults to True)
    - Main Entry (`app/main.py`): CLI interface with arguments (--once, --status, --close-all, --mode, --interval)
  - **Backtesting Framework** (`src/`):
    - Data Loading (`src/data_loader.py`): CSV loading, market open price approximation
    - Core Analysis (`src/core_analysis.py`): Range calculations, distributions, MFE/MAE, ADR
    - Regime Detection (`src/regime.py`): Market regime classification (bull/bear/chop)
    - Backtesting Engines:
      - `src/backtest.py`: Standard backtesting engine (with TP/SL)
      - `src/backtest_no_sl.py`: No-stop-loss backtesting engine (EOD exit)
      - `src/backtest_dual_market.py`: Dual market open backtesting engine
    - Strategies (`src/strategies.py`): Strategy definitions for backtesting (price_trend_sma20, dual_market_open)
    - Market Sessions (`src/market_sessions.py`): Market open time utilities and price approximation
    - OANDA API (`src/oanda_api.py`): OANDA API utilities for data fetching
    - Main Analysis (`src/main.py`): Main backtesting entry point with regime analysis and strategy comparison
  - **Backtesting Scripts** (`scripts/backtests/`):
    - `backtest_12month.py`: 12-month backtest comparison (single vs dual market open)
    - `backtest_same_direction_comparison.py`: Comparison of current vs new same-direction position rules
    - `analyze_drawdown.py`: Drawdown metrics analysis from backtest results
- **Data store**: CSV files for historical data (`data/`), OANDA API for live data
- **Auth**: OANDA API token (stored in environment variables or `.env` via python-dotenv)
- **Integrations**: 
  - OANDA API for live trading and data (practice and live modes)
  - Historical CSV data files for backtesting (`data/eur_usd.csv`, `data/eur_usd_long_term.csv`)
- **Logging**: Daily rotating log files (`logs/trading_YYYYMMDD.log`) with file handler (DEBUG) and console handler (INFO)
- **Deployment**: Local/remote Python execution (CLI-based, can run in background with screen/tmux/nohup)

## How to run
- **Dev**: 
  ```bash
  # Backtesting
  python -m src.main
  
  # Standalone backtest scripts
  python scripts/backtests/backtest_12month.py
  python scripts/backtests/backtest_same_direction_comparison.py
  python scripts/backtests/analyze_drawdown.py
  
  # Trading app - check account status
  python -m app.main --status
  
  # Trading app - run once (practice mode)
  python -m app.main --once
  
  # Trading app - run continuously (practice mode)
  python -m app.main
  
  # Trading app - close all positions
  python -m app.main --close-all
  ```

- **Trading App CLI Options**:
  - `--once`: Run once and exit (test mode)
  - `--status`: Show account status and exit
  - `--close-all`: Close all open positions and exit
  - `--mode practice|live`: Set trading mode (default: practice)
  - `--interval SECONDS`: Check interval for continuous mode (default: 60)

- **Tests**: 
  ```bash
  # Run tests (when implemented)
  pytest tests/
  ```

- **Build**: 
  ```bash
  # Install dependencies
  pip install -r requirements.txt
  ```

- **Deploy**: 
  - Trading app runs continuously or on schedule
  - Practice mode by default (use `--mode live` for production)
  - Logs saved to `logs/trading_YYYYMMDD.log`
  - Trading hours: 
    - **Default (Dual Market Open)**: 8:00 UTC (EUR) and 13:00 UTC (US) market opens
    - **Alternative (Single Daily Open)**: 22:00-23:00 UTC window when dual market disabled
  - Application must be running at market open times for execution

## Constraints
- **Must**: 
  - Prevent lookahead bias in backtesting
  - Use only information available at trade time
  - Include transaction costs in backtests
  - Default to practice mode for safety
  - Log all trading activity (file and console logging implemented)
  - Handle errors gracefully with comprehensive error handling

- **Must not**: 
  - Use future data in signal generation
  - Trade with real money without explicit confirmation
  - Commit API keys or sensitive data
  - Create files in repo root (use scratch/ or sandbox/)

- **Performance/SLA**: 
  - Backtests should complete in reasonable time
  - Trading app checks every 60 seconds (configurable via `--interval`)
  - OANDA API rate limits must be respected
  - Trading hours: 
    - **Dual Market Open (default)**: EUR 8:00 UTC, US 13:00 UTC (configurable in settings)
    - **Single Daily Open**: 22:00-23:00 UTC window (when dual market disabled)

## Trading-Specific Notes
- **Instrument**: EUR_USD (primary focus)
- **Default Strategy**: **Dual Market Open** (enabled by default in `app/config/settings.py`)
- **Strategies**:
  - **Dual Market Open (DEFAULT, RECOMMENDED)**: Price Trend (SMA20) Directional
    - Same SMA20 logic, trades at both market opens
    - EUR Market Open: 8:00 UTC (London session)
    - US Market Open: 13:00 UTC (New York session)
    - Only one position open at a time (skips US if EUR trade still open)
    - **12-Month Performance**: +2,900 pips, 87% win rate, 428 trades
    - **Improvement**: +107% more pips vs single daily open
    - Session breakdown: EUR +1,399 pips (78% win rate), US +1,501 pips (100% win rate)
  - **Single Daily Open** (available when `DUAL_MARKET_OPEN_ENABLED = False`): Price Trend (SMA20) Directional
    - BUY when yesterday's Close > SMA20 (uptrend)
    - SELL when yesterday's Close < SMA20 (downtrend)
    - Entry: 22:00 UTC (daily candle open)
    - **12-Month Performance**: +1,399 pips, 78% win rate, 240 trades
- **Signal Generation**: Uses previous day's close vs SMA20 to avoid lookahead bias (same logic for both strategies)
- **Take Profit**: 10 pips (live trading) / 20 pips (backtesting defaults)
- **Stop Loss**: None (positions exit at end-of-day if TP not hit)
- **Trading Hours**: 
  - **Dual mode (default)**: 8:00 UTC (EUR) and 13:00 UTC (US) market opens
  - **Single mode**: 22:00-23:00 UTC (daily open window)
- **Position Sizing**: 1,000 units (1 mini lot = $1 per pip for EUR/USD) by default
- **Risk Management**: 
  - Single mode: Max 1 trade per day
  - Dual mode: Max 2 trades per day (one per session, but only if first trade closed)
  - Only one position open at a time
  - **Same-Direction Position Logic**: If EUR position still open at US market open and US signal is same direction, keeps existing position (saves 4 pips spread costs: 2 close + 2 open)
- **Configuration**: 
  - `DUAL_MARKET_OPEN_ENABLED`: True by default (enables dual market open strategy)
  - `EUR_MARKET_OPEN_HOUR`: 8 (8:00 UTC) by default
  - `US_MARKET_OPEN_HOUR`: 13 (13:00 UTC) by default
  - `MAX_DAILY_TRADES`: 2 when dual market enabled, 1 when disabled
- **Data Requirements**: Minimum 20 days of historical data for SMA20 (fetches 30 days from OANDA)
- **Logging**: Daily log files (`logs/trading_YYYYMMDD.log`) with DEBUG level to file, INFO level to console

## Known risks / sharp edges
- **Historical backtests don't guarantee future performance**
- **Daily OHLC data limits precision for intraday TP/SL hits**
- **Conservative assumption**: If both TP and SL could be hit, SL is assumed
- **No stop loss** in current strategy (EOD exit only)
- **Market regime changes** can affect strategy performance
- **API rate limits** from OANDA must be respected

## Changelog (newest first)
- 2026-01-08: Implemented same-direction position logic - keeps existing position if new signal is same direction (saves 4 pips spread costs per trade)
- 2026-01-08: Reorganized backtesting scripts to `scripts/backtests/` directory for better organization
- 2026-01-08: Fixed currency display in position status logs (was showing financing cost instead of currency)
- 2026-01-02: Updated position size from 1 unit (micro lot) to 1,000 units (mini lot = $1 per pip)
- 2026-01-02: Fixed OANDA API datetime formatting issue (400 Bad Request errors) - now uses RFC3339 format with microseconds stripped
- 2026-01-01: Updated CONTEXT.md and documentation to reflect current codebase state
- 2025-01-XX: Dual Market Open Strategy set as default (DUAL_MARKET_OPEN_ENABLED = True)
- 2025-01-XX: Implemented Dual Market Open Strategy with 12-month backtest showing +107% improvement
- 2025-01-XX: Added market session utilities and dual market open backtesting engine
- 2025-01-XX: Added comprehensive error handling and logging improvements
- 2025-01-XX: Implemented full CLI interface with --status, --close-all, --once, --interval, --mode commands
- 2025-01-XX: Configured trading hours: dual market opens (8:00 and 13:00 UTC) and single daily open (22:00-23:00 UTC)
- 2025-01-XX: Removed API key requirements from AI documentation, focused on Cursor built-in features
- 2025-01-XX: Updated project documentation structure
- 2025-01-XX: Initial project setup with backtesting framework and trading application
