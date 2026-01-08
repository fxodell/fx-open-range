# Backtesting Scripts

This directory contains standalone backtesting scripts for analyzing and comparing trading strategies.

## Scripts

### `backtest_12month.py`
12-month backtest comparison between single daily open strategy and dual market open strategy.

**Usage:**
```bash
python scripts/backtests/backtest_12month.py
```

**What it does:**
- Compares single daily open (22:00 UTC) vs dual market open (8:00 UTC + 13:00 UTC)
- Shows performance metrics, win rates, and session breakdown
- Uses last 12 months of historical data from `data/eur_usd_long_term.csv`

### `backtest_same_direction_comparison.py`
Comparison of current vs new same-direction position rules.

**Usage:**
```bash
python scripts/backtests/backtest_same_direction_comparison.py
```

**What it does:**
- Compares two position management approaches:
  - **Current**: Skip US trade if EUR position still open (any direction)
  - **New**: Keep EUR position if US signal is same direction, skip if different
- Shows spread cost savings (4 pips per same-direction trade kept)
- Demonstrates identical performance with cost savings

### `analyze_drawdown.py`
Analyze drawdown metrics from backtest results.

**Usage:**
```bash
python scripts/backtests/analyze_drawdown.py
```

**What it does:**
- Calculates detailed drawdown metrics from equity curve
- Shows max drawdown, average daily drawdown, days in drawdown
- Analyzes drawdown on losing days
- Uses dual market open strategy with 12-month data

## Requirements

All scripts require:
- Python 3.7+
- Dependencies from `requirements.txt`
- Historical data in `data/eur_usd_long_term.csv`

## Notes

- All scripts use the project root as the base path
- Scripts automatically add project root to Python path
- Results are printed to console (no file output)
- Uses same parameters as live trading (10 pips TP, 2 pips cost per trade)

