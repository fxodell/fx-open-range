> This file is the single source of truth for humans and AI agents.
> All agents must read this before making changes.

# Project Context

## What we're building
- **Product**: FX Open-Range Lab - Quantitative research and backtesting framework for EUR/USD trading strategies
- **Users**: Quantitative researchers, traders, and developers working on forex strategies
- **Primary goal**: Develop, backtest, and deploy systematic "trade at the open" strategies for EUR/USD

## Current status
- **Working**: 
  - Backtesting framework (`src/`) with comprehensive metrics
  - Automated trading application (`app/`) with SMA20 strategy
  - Market regime detection (bull/bear/chop)
  - OANDA API integration with full trading operations
  - Historical data analysis and range calculations
  - Comprehensive CLI interface with multiple commands (`--once`, `--status`, `--close-all`, `--mode`, `--interval`)
  - Daily logging system with file and console handlers (`logs/trading_YYYYMMDD.log`)
  - Error handling and graceful error recovery throughout
  - Account monitoring and status reporting
  - Trading hours configuration (22:00-23:00 UTC window for daily open)

- **Broken**: 
  - None currently known

- **In progress**: 
  - Strategy research and optimization
  - Additional strategy development

## Architecture snapshot
- **Frontend**: None (CLI-based application)
- **Backend**: Python-based trading engine and backtesting framework
  - Trading Engine (`app/trading_engine.py`): Core trading logic, signal generation, trade execution
  - OANDA Client (`app/utils/oanda_client.py`): OANDA API wrapper for all trading operations
  - Strategy Module (`app/strategies/sma20_strategy.py`): SMA20 strategy implementation
  - Settings (`app/config/settings.py`): Centralized configuration management
- **Data store**: CSV files for historical data, OANDA API for live data
- **Auth**: OANDA API token (stored in environment variables or `.env` via python-dotenv)
- **Integrations**: 
  - OANDA API for live trading and data (practice and live modes)
  - Historical CSV data files for backtesting
- **Logging**: Daily rotating log files (`logs/trading_YYYYMMDD.log`) with file and console handlers
- **Deployment**: Local/remote Python execution (CLI-based, can run in background with screen/tmux/nohup)

## How to run
- **Dev**: 
  ```bash
  # Backtesting
  python -m src.main
  
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
  - Trading hours: 22:00-23:00 UTC (daily open window)

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
  - Trading hours window: 22:00-23:00 UTC (configurable in settings)

## Trading-Specific Notes
- **Instrument**: EUR_USD (primary focus)
- **Strategy**: Price Trend (SMA20) Directional
  - BUY when yesterday's Close > SMA20 (uptrend)
  - SELL when yesterday's Close < SMA20 (downtrend)
  - Signal uses previous day's close to avoid lookahead bias
  - Take Profit: 10 pips
  - Stop Loss: None (positions exit at end-of-day if TP not hit)
- **Trading Hours**: 22:00-23:00 UTC (1-hour window at daily open, New York close)
- **Position Sizing**: 1 unit (micro lot) by default
- **Risk Management**: Max 1 trade per day
- **Data Requirements**: Minimum 20 days of historical data for SMA20 (fetches 30 days)
- **Logging**: Daily log files with DEBUG level to file, INFO level to console

## Known risks / sharp edges
- **Historical backtests don't guarantee future performance**
- **Daily OHLC data limits precision for intraday TP/SL hits**
- **Conservative assumption**: If both TP and SL could be hit, SL is assumed
- **No stop loss** in current strategy (EOD exit only)
- **Market regime changes** can affect strategy performance
- **API rate limits** from OANDA must be respected

## Changelog (newest first)
- 2025-01-XX: Added comprehensive error handling and logging improvements
- 2025-01-XX: Implemented full CLI interface with --status, --close-all, --once, --interval, --mode commands
- 2025-01-XX: Configured trading hours window (22:00-23:00 UTC) for daily open trading
- 2025-01-XX: Removed API key requirements from AI documentation, focused on Cursor built-in features
- 2025-01-XX: Updated project documentation structure
- 2025-01-XX: Initial project setup with backtesting framework and trading application
