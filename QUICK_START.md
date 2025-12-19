# Quick Start Guide

## Running the Analysis

```bash
# Install dependencies
pip install -r requirements.txt

# Run full analysis
python run_analysis.py
```

## Example: Custom Strategy

```python
from src.data_loader import load_eurusd_data
from src.core_analysis import calculate_daily_metrics, calculate_adr
from src.regime import calculate_moving_averages, classify_regime
from src.backtest import backtest_strategy

# Load data
df = load_eurusd_data('data/eur_usd.csv')

# Calculate features
df = calculate_daily_metrics(df)
df = calculate_moving_averages(df)
df = classify_regime(df)

# Create custom signals
def my_strategy(df):
    signals = pd.Series('flat', index=df.index)
    adr = calculate_adr(df, window=20)
    
    # Buy when regime is bull and ADR > 40 pips
    signals.loc[(df['regime'] == 'bull') & (adr > 40)] = 'long'
    
    return signals

# Run backtest
signals = my_strategy(df)
result = backtest_strategy(
    df, signals,
    take_profit_pips=25.0,
    stop_loss_pips=15.0,
    cost_per_trade_pips=2.0
)

# View results
result.print_summary()
stats = result.get_summary_stats()
print(f"Win Rate: {stats['win_rate']:.2f}%")
```

## Key Functions Reference

### Data Loading
- `load_eurusd_data(filepath)` - Load and clean OHLC data

### Core Analysis
- `calculate_daily_metrics(df)` - Add range_pips, up_from_open_pips, etc.
- `calculate_distribution_stats(df, col)` - Get stats (mean, median, percentiles)
- `analyze_range_distribution(df)` - Frequency of pip thresholds
- `calculate_adr(df, window=20)` - Average Daily Range
- `calculate_mfe_mae(df, direction='long')` - MFE/MAE analysis

### Regime Detection
- `calculate_moving_averages(df, periods=[20,50,100,200])` - Add SMA columns
- `calculate_momentum(df, periods=[1,3,6])` - Add momentum columns
- `classify_regime(df, sma_short=50, sma_long=200)` - Add 'regime' column
- `analyze_regime_performance(df)` - Compare metrics by regime

### Backtesting
- `backtest_strategy(df, signals, take_profit_pips, stop_loss_pips, ...)` - Run backtest
- `result.get_summary_stats()` - Get performance dictionary
- `result.print_summary()` - Print formatted report

## Common Parameter Choices

### Take Profit / Stop Loss
- Conservative: TP=15, SL=15 pips
- Moderate: TP=20, SL=20 pips
- Aggressive: TP=30, SL=15 pips

### ADR Filters
- Low volatility skip: ADR < 30-35 pips
- High volatility target: ADR > 50-60 pips

### Transaction Costs
- Tight spread broker: 1.5-2.0 pips
- Standard broker: 2.0-3.0 pips
- Conservative: 3.0+ pips

