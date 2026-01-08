# Project Tasks

This document tracks current tasks, improvements, and future work for the FX Open-Range Lab project.

## Current Tasks

### High Priority
- [ ] Add comprehensive test suite for backtesting framework
- [ ] Add tests for trading engine

### Medium Priority
- [ ] Research additional trading strategies
- [ ] Implement adaptive TP/SL based on ADR
- [ ] Add day-of-week pattern analysis
- [ ] Implement calendar effects (month-end, quarter-end)

### Low Priority
- [ ] Add visualization for backtest results
- [ ] Create web dashboard for monitoring
- [ ] Implement strategy comparison tools
- [ ] Add performance attribution analysis

## Future Enhancements

### Strategy Development
- [ ] Session-specific signal optimization (different logic for EUR vs US opens)
- [ ] Adaptive TP/SL based on session (different levels for EUR vs US)
- [ ] Macro event integration (ECB, FOMC, NFP, CPI)
- [ ] Inter-market analysis (DXY, equity indices, bond yields)
- [ ] Volatility-based strategies
- [ ] Multi-timeframe strategies
- [ ] Regime-adaptive strategies

### Data & Analysis
- [ ] Intraday data support (M5, M15, H1) for accurate market open prices
- [ ] Real-time data streaming
- [ ] Advanced regime detection
- [ ] Correlation analysis with other instruments
- [ ] Volatility clustering analysis
- [ ] Session-specific performance attribution analysis

### Infrastructure
- [ ] Database migration for large datasets
- [ ] API rate limiting improvements
- [ ] Automated testing pipeline
- [ ] CI/CD setup
- [ ] Docker containerization

### Risk Management
- [ ] Position sizing algorithms
- [ ] Portfolio-level risk management
- [ ] Drawdown protection mechanisms
- [ ] Correlation-based position limits

### Documentation
- [ ] API documentation
- [ ] Strategy development guide
- [ ] Deployment guide
- [ ] Troubleshooting guide
- [ ] Performance tuning guide

## Completed Tasks

- [x] Implemented same-direction position logic - keeps existing position if new signal is same direction (saves 4 pips spread costs)
- [x] Created backtest comparison script for same-direction position rules (`scripts/backtests/backtest_same_direction_comparison.py`)
- [x] Reorganized backtesting scripts to `scripts/backtests/` directory for better organization
- [x] Fixed currency display in position status logs (was showing financing cost instead of currency)
- [x] Fixed OANDA API datetime formatting to prevent 400 Bad Request errors (RFC3339 format)
- [x] Updated position sizing from 1 unit (micro lot) to 1,000 units (mini lot = $1 per pip)
- [x] Dual Market Open Strategy implementation (EUR 8:00 UTC + US 13:00 UTC)
- [x] Dual market open backtesting engine with session-specific analysis
- [x] 12-month backtest comparison showing +107% improvement over single daily open
- [x] Market session utilities for EUR and US market open times
- [x] Market open price approximation from daily OHLC data
- [x] Live trading integration for dual market open strategy
- [x] Initial backtesting framework
- [x] SMA20 strategy implementation
- [x] OANDA API integration
- [x] Trading application with practice mode
- [x] Market regime detection
- [x] Comprehensive backtest metrics
- [x] Documentation structure
- [x] AI tool usage documentation (Cursor-focused)
- [x] Implement error handling improvements
- [x] Add logging improvements for better debugging

## Notes

- Tasks should be moved to "Completed" when finished
- Add new tasks as they arise
- Prioritize based on project goals and user needs
- Break down large tasks into smaller, actionable items

