# Architectural Decisions (ADR)

This document records architectural decisions made for the FX Open-Range Lab project.

## ADR-001 - Separation of Backtesting and Trading Applications
- **Date**: Initial project setup
- **Decision**: Split project into `src/` (backtesting framework) and `app/` (trading application)
- **Why**: 
  - Clear separation of research/analysis vs production code
  - Allows independent development and testing
  - Backtesting framework can be used without trading dependencies
- **Alternatives considered**: 
  - Single monolithic application
  - Trading app with embedded backtesting
- **Consequences**: 
  - Some code duplication possible
  - Need to maintain consistency between frameworks
  - Clearer project structure and easier maintenance

## ADR-002 - Practice Mode by Default
- **Date**: Trading application implementation
- **Decision**: Trading application defaults to practice mode, requires explicit `--mode live` flag
- **Why**: 
  - Prevents accidental live trading
  - Safety-first approach for financial applications
  - Allows testing without risk
- **Alternatives considered**: 
  - Live mode by default with confirmation
  - Environment variable only
- **Consequences**: 
  - Extra step required for live trading
  - Reduces risk of accidental real-money trades
  - May require documentation updates if users expect different default

## ADR-003 - No Stop Loss in SMA20 Strategy
- **Date**: Strategy implementation
- **Decision**: Current SMA20 strategy uses EOD (end-of-day) exit instead of stop loss
- **Why**: 
  - Based on backtesting results showing better performance
  - Reduces whipsaw from intraday volatility
  - Aligns with "trade at the open" philosophy
- **Alternatives considered**: 
  - Fixed stop loss (e.g., 20 pips)
  - Adaptive stop loss based on ADR
  - Trailing stop loss
- **Consequences**: 
  - Higher risk per trade (no hard stop)
  - Relies on EOD exit for risk management
  - May need review if market conditions change

## ADR-004 - Daily OHLC Data for Backtesting
- **Date**: Initial backtesting implementation
- **Decision**: Use daily OHLC (Open, High, Low, Close) data for backtesting
- **Why**: 
  - Matches "trade at the open" strategy timing
  - Simpler data requirements
  - Faster backtesting execution
- **Alternatives considered**: 
  - Intraday data (M5, M15, H1)
  - Tick data
- **Consequences**: 
  - Less precision for TP/SL execution
  - Conservative assumption: SL hit first if both possible
  - May need intraday data for more precise backtesting in future

## ADR-005 - Transaction Cost Modeling
- **Date**: Backtesting framework implementation
- **Decision**: Include 2 pips transaction cost per trade by default
- **Why**: 
  - Realistic cost modeling for EUR/USD
  - Accounts for spread and potential slippage
  - Conservative approach to performance estimates
- **Alternatives considered**: 
  - No transaction costs
  - Variable costs based on volatility
  - Separate spread and slippage modeling
- **Consequences**: 
  - More realistic backtest results
  - May underestimate costs in volatile conditions
  - Configurable for different assumptions

## ADR-006 - CSV Data Storage
- **Date**: Initial data handling
- **Decision**: Store historical data as CSV files in `data/` directory
- **Why**: 
  - Simple and portable
  - Easy to inspect and modify
  - No database dependencies
- **Alternatives considered**: 
  - SQLite database
  - Parquet files
  - Direct API-only approach
- **Consequences**: 
  - Easy to work with but may not scale
  - File-based approach limits concurrent access
  - May need migration for larger datasets

## ADR-007 - Cursor AI as Primary Development Tool
- **Date**: 2025-01-XX
- **Decision**: Use Cursor's built-in AI features for development (no external API keys)
- **Why**: 
  - Integrated development experience
  - No API key management needed
  - Consistent with team workflow
- **Alternatives considered**: 
  - External AI APIs (Claude, Gemini)
  - Multiple AI tools
- **Consequences**: 
  - Simplified setup
  - Relies on Cursor subscription
  - Documentation focuses on Cursor features

## ADR-008 - Daily Logging with File and Console Handlers
- **Date**: Trading application implementation
- **Decision**: Implement dual logging system: daily rotating log files (DEBUG level) and console output (INFO level)
- **Why**: 
  - DEBUG-level file logs provide detailed debugging information
  - INFO-level console output reduces noise for users
  - Daily log files (`logs/trading_YYYYMMDD.log`) enable historical analysis
  - Structured logging format with timestamps for audit trail
- **Alternatives considered**: 
  - Single log file (all levels)
  - Console-only logging
  - External logging services
- **Consequences**: 
  - Better debugging capabilities with detailed file logs
  - Cleaner user experience with filtered console output
  - Log files require disk space management
  - Historical analysis possible through log file review

## ADR-009 - Comprehensive Error Handling Strategy
- **Date**: Trading application implementation
- **Decision**: Implement comprehensive error handling with try/except blocks, error logging, and graceful degradation
- **Why**: 
  - Financial applications require robust error handling
  - Prevents application crashes from stopping trading operations
  - Error logging enables post-mortem analysis
  - Graceful degradation allows partial functionality to continue
- **Alternatives considered**: 
  - Fail-fast approach (crash on error)
  - Minimal error handling
  - External error tracking services
- **Consequences**: 
  - More resilient application
  - Better debugging through error logs
  - Requires careful error handling design to avoid masking critical issues
  - May continue operating with degraded functionality

## ADR-010 - CLI Interface with Multiple Commands
- **Date**: Trading application implementation
- **Decision**: Implement comprehensive CLI interface with multiple commands (`--once`, `--status`, `--close-all`, `--mode`, `--interval`)
- **Why**: 
  - Flexible usage patterns (one-time checks, continuous operation, status monitoring)
  - Safety features (`--close-all` for emergency exits, `--status` for monitoring)
  - Testing capability (`--once` for single execution)
  - Configurable operation (`--interval` for custom check frequency)
- **Alternatives considered**: 
  - Single mode of operation
  - Configuration file only
  - Web interface
- **Consequences**: 
  - More user-friendly and flexible
  - Supports multiple use cases (testing, monitoring, production)
  - Requires maintaining CLI argument parsing
  - May need documentation updates as features grow

## ADR-011 - Trading Hours Window Configuration
- **Date**: Trading application implementation
- **Decision**: Configure trading hours window (22:00-23:00 UTC) for daily open trading, aligned with EUR/USD daily candle boundary
- **Why**: 
  - EUR/USD daily candle closes at 22:00 UTC (New York close)
  - Trading at daily open matches backtested strategy timing
  - 1-hour window provides execution flexibility while maintaining strategy alignment
  - Prevents trading outside optimal time window
- **Alternatives considered**: 
  - 24-hour trading window
  - Fixed execution time (22:00 UTC exactly)
  - No time restrictions
- **Consequences**: 
  - Strategy execution matches backtest assumptions
  - Reduced flexibility (only 1-hour window per day)
  - Requires application to be running during window
  - May miss trades if application is down during window

## ADR-012 - Dual Market Open Strategy Implementation
- **Date**: 2025-01-XX
- **Decision**: Implement dual market open strategy that trades at both EUR market open (8:00 UTC) and US market open (13:00 UTC) using the same SMA20 directional logic
- **Why**: 
  - 12-month backtest showed +107% improvement over single daily open strategy
  - Provides more trading opportunities (up to 2 trades per day)
  - US session showed exceptional performance (100% win rate, +1,501 pips from 188 trades)
  - Reuses proven SMA20 logic, reducing complexity
  - Only one position open at a time maintains risk control
- **Alternatives considered**: 
  - Different signal logic for EUR vs US opens
  - Allowing multiple positions simultaneously
  - Trading only at EUR or only at US open
- **Consequences**: 
  - Significantly improved performance metrics (+2,900 pips vs +1,399 pips in 12-month period)
  - Higher win rate (87.85% vs 78.33%)
  - More trades (428 vs 240), providing more opportunities
  - Requires application to be running at both market open times (8:00 and 13:00 UTC)
  - More complex position tracking and session management
  - Market open price approximation needed for backtesting (uses daily open for EUR, interpolated for US)

## ADR-013 - Market Open Price Approximation from Daily Data
- **Date**: 2025-01-XX
- **Decision**: Approximate market open prices from daily OHLC data for backtesting dual market open strategy
- **Why**: 
  - Daily OHLC data is readily available and simpler to work with
  - Intraday data (H1, M15) not always available for historical backtesting
  - Approximation provides reasonable estimates for strategy evaluation
  - EUR open uses current day's open (price at 22:00 UTC previous day, which is when EUR opens at 8:00 UTC)
  - US open interpolates between daily open and close (30% through day)
- **Alternatives considered**: 
  - Require intraday data (H1, M15) for all backtests
  - Use previous day's close for EUR open (incorrect - tested and fixed)
  - Use daily open for US open (less accurate)
- **Consequences**: 
  - Enables backtesting with commonly available daily data
  - Approximation may introduce some inaccuracy
  - For production use, intraday data recommended for more precise execution
  - EUR open approximation (using daily open) proved accurate in testing
  - US open approximation (30% interpolation) provides reasonable estimate
