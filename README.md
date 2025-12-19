# FX Open-Range Lab

Quantitative research and backtesting framework for EUR/USD "trade at the open" strategies.

## Overview

This project provides a comprehensive Python framework for:
- Analyzing EUR/USD daily ranges and open-based movements
- Detecting market regimes (bull/bear/chop)
- Designing and backtesting systematic trade-at-open strategies
- Exploring additional factors (macro events, volatility patterns, etc.)

## Project Structure

```
fx-open-range-project/
├── data/
│   └── eur_usd.csv          # Historical EUR/USD OHLC data
├── src/
│   ├── __init__.py
│   ├── data_loader.py       # Data loading and cleaning
│   ├── core_analysis.py     # Range calculations, distributions, MFE/MAE
│   ├── regime.py            # Market regime detection
│   ├── backtest.py          # Backtesting engine
│   ├── strategies.py        # Strategy definitions
│   └── main.py              # Main analysis (module)
├── run_analysis.py          # Entry point script
├── requirements.txt         # Python dependencies
└── README.md
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure your EUR/USD data is in `data/eur_usd.csv` with columns:
   - Date (MM/DD/YYYY format)
   - Price (Close price)
   - Open
   - High
   - Low

## Usage

Run the full analysis:

```bash
python run_analysis.py
```

This will:
1. Load and clean the EUR/USD data
2. Calculate daily range metrics and distributions
3. Detect market regimes (bull/bear/chop)
4. Backtest multiple strategies
5. Display comprehensive performance metrics

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

The framework includes several pre-built strategies:

1. **always_buy**: Baseline - always buy at open
2. **always_sell**: Baseline - always sell at open
3. **regime_aligned**: Trade only in direction of regime
4. **regime_adr_filter**: Regime-aligned with ADR filter (skip low volatility)
5. **regime_gap_filter**: Regime-aligned with gap/exhaustion filters

### Adding Custom Strategies

Create a function in `src/strategies.py` that takes `df` and returns a `pd.Series` with signals ('long', 'short', 'flat'):

```python
def my_custom_strategy(df: pd.DataFrame, **kwargs) -> pd.Series:
    signals = pd.Series('flat', index=df.index)
    # Your logic here
    return signals
```

Then add it to the `STRATEGIES` dictionary.

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

You can customize:
- `take_profit_pips`: Take profit in pips (default 20.0)
- `stop_loss_pips`: Stop loss in pips (default 20.0)
- `cost_per_trade_pips`: Transaction cost (default 2.0)
- `initial_equity`: Starting equity (default 10000.0)

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

- The framework expects daily OHLC data
- Dates should be in chronological order (oldest first)
- Missing data is automatically removed

### Lookahead Bias Prevention

All calculations use only information available at the time:
- Regime classification uses only prior closes
- ADR uses rolling windows (no future data)
- Signals are generated before trade execution

### Transaction Costs

Default assumption: 2 pips per trade (spread + commission). Adjust in `run_backtests()` if needed.

### Limitations

- Daily OHLC data limits precision for intraday TP/SL hits
- Conservative assumption: if both TP and SL could be hit, SL is assumed
- For more precise execution, intraday data is recommended

## Disclaimer

**This is research software for historical analysis only.**

- Historical backtests do NOT guarantee future performance
- All strategies should be tested with out-of-sample data
- Risk management is critical - size positions conservatively
- Consider well under 1% risk per trade
- Results are subject to overfitting and market regime changes

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
  - Adaptive TP/SL based on ADR
  - Day-of-week patterns
  - Calendar effects (month-end, quarter-end)
  - Intraday refinement with M5/M15/H1 data

## License

This project is for research purposes only.

