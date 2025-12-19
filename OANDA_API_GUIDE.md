# OANDA API Integration Guide

## Overview

This module provides integration with OANDA API to fetch EUR/USD historical data for backtesting.

---

## Setup

### 1. API Token

Your OANDA API token is configured in the code:
```
965884e308ff2a75fcf9a5011a2cc39a-616820942fc0746b78b04062b603c20d
```

**⚠️ Security Note:** This token is hardcoded in the files. For production, consider:
- Using environment variables
- Using a config file (not committed to git)
- Storing in secure credential manager

### 2. Practice vs Live Account

The code uses **practice API** by default. To switch to live:
```python
api = OandaAPI(API_TOKEN, practice=False)  # Use live account
```

---

## Usage

### Quick Start

```python
from src.oanda_api import OandaAPI, save_oanda_data

# Your API token
API_TOKEN = "your-token-here"

# Initialize API
api = OandaAPI(API_TOKEN, practice=True)

# Fetch 1 year of daily data
df = api.fetch_daily_data("EUR_USD", days=365)

# Save to CSV
save_oanda_data(df, "eur_usd_oanda.csv")
```

### Command Line

Run the fetch script:
```bash
python fetch_oanda_data.py
```

Or use the module directly:
```bash
python -m src.oanda_api
```

---

## API Methods

### `fetch_daily_data()`

Fetch daily EUR/USD data (convenience method).

```python
df = api.fetch_daily_data(
    instrument="EUR_USD",
    days=365,  # Number of days
    end_date=None  # End date (default: today)
)
```

**Returns:** DataFrame with columns: Date, Price, Open, High, Low, Close

### `fetch_candles()`

Fetch candles with custom granularity.

```python
from datetime import datetime, timedelta

# Fetch last 500 candles
df = api.fetch_candles("EUR_USD", granularity="D", count=500)

# Fetch specific date range
from_time = datetime(2020, 1, 1)
to_time = datetime(2024, 1, 1)
df = api.fetch_candles("EUR_USD", granularity="D", from_time=from_time, to_time=to_time)
```

**Granularity Options:**
- `"D"` - Daily
- `"H12"` - 12 hours
- `"H4"` - 4 hours
- `"H1"` - 1 hour
- `"M30"` - 30 minutes
- `"M15"` - 15 minutes
- `"M5"` - 5 minutes
- See OANDA docs for full list

**Returns:** DataFrame with columns: Date, Open, High, Low, Close, Volume

---

## Examples

### Example 1: Fetch Last Year of Data

```python
from src.oanda_api import OandaAPI

api = OandaAPI(API_TOKEN)
df = api.fetch_daily_data("EUR_USD", days=365)
print(f"Fetched {len(df)} days")
```

### Example 2: Fetch Specific Date Range

```python
from datetime import datetime

api = OandaAPI(API_TOKEN)
from_date = datetime(2023, 1, 1)
to_date = datetime(2024, 1, 1)

df = api.fetch_candles("EUR_USD", "D", from_time=from_date, to_time=to_date)
```

### Example 3: Fetch Intraday Data

```python
# Fetch 4-hour candles for last 30 days
api = OandaAPI(API_TOKEN)
df = api.fetch_candles("EUR_USD", granularity="H4", count=180)  # 30 days * 6 candles/day
```

### Example 4: Use with Backtesting

```python
from src.oanda_api import OandaAPI, save_oanda_data
from src.data_loader import load_eurusd_data

# Fetch from OANDA
api = OandaAPI(API_TOKEN)
df = api.fetch_daily_data("EUR_USD", days=1825)  # 5 years

# Save to CSV
save_oanda_data(df, "eur_usd_oanda.csv")

# Use in backtesting
df = load_eurusd_data("data/eur_usd_oanda.csv")
# ... continue with backtesting ...
```

---

## Data Format

The OANDA API returns data in this format:

```python
DataFrame:
  Date    - datetime (converted to pandas datetime)
  Price   - float (same as Close)
  Open    - float
  High    - float
  Low     - float
  Close   - float
  Volume  - int (if available)
```

Saved CSV format matches existing data:
```
Date,Price,Open,High,Low,Vol.,Change %
12/18/2025,1.1725,1.1742,1.1763,1.1713,,-0.13%
```

---

## Error Handling

Common errors and solutions:

### 1. Authentication Error
```
HTTPError: 401 Unauthorized
```
**Solution:** Check API token is correct

### 2. Account Not Found
```
ValueError: No accounts found
```
**Solution:** Token may not have account access, or wrong API endpoint (practice vs live)

### 3. Rate Limit
```
HTTPError: 429 Too Many Requests
```
**Solution:** OANDA has rate limits, add delays between requests

### 4. Invalid Instrument
```
HTTPError: 400 Bad Request
```
**Solution:** Check instrument name (use "EUR_USD" not "EURUSD")

---

## Rate Limits

OANDA API has rate limits:
- **Practice API:** ~120 requests per minute
- **Live API:** Varies by account type

For large data fetches, the code automatically chunks requests (max 5000 candles per request).

---

## Security Best Practices

### ⚠️ Current Implementation (Token in Code)

The token is currently hardcoded in `src/oanda_api.py` and `fetch_oanda_data.py`. This works but is not secure.

### ✅ Recommended: Environment Variables

```python
import os

API_TOKEN = os.getenv('OANDA_API_TOKEN')
if not API_TOKEN:
    raise ValueError("OANDA_API_TOKEN environment variable not set")

api = OandaAPI(API_TOKEN)
```

Set environment variable:
```bash
export OANDA_API_TOKEN="your-token-here"
python fetch_oanda_data.py
```

### ✅ Alternative: Config File (Not in Git)

Create `config.py` (add to `.gitignore`):
```python
OANDA_API_TOKEN = "your-token-here"
```

Use in code:
```python
from config import OANDA_API_TOKEN
api = OandaAPI(OANDA_API_TOKEN)
```

---

## Integration with Existing Code

The OANDA data format is compatible with existing backtesting code:

```python
# Fetch from OANDA
from src.oanda_api import OandaAPI, save_oanda_data
api = OandaAPI(API_TOKEN)
df_oanda = api.fetch_daily_data("EUR_USD", days=1825)
save_oanda_data(df_oanda, "data/eur_usd_oanda.csv")

# Use in existing backtesting
from src.data_loader import load_eurusd_data
df = load_eurusd_data("data/eur_usd_oanda.csv")

# Continue with normal backtesting
from src.core_analysis import calculate_daily_metrics
df = calculate_daily_metrics(df)
# ... rest of backtesting ...
```

---

## Testing

Test the API connection:

```bash
python -c "from src.oanda_api import OandaAPI; api = OandaAPI('your-token'); print('Connected:', api.get_account_info())"
```

---

## References

- OANDA API Documentation: https://developer.oanda.com/rest-live-v20/introduction/
- OANDA Practice API: https://api-fxpractice.oanda.com
- OANDA Live API: https://api-fxtrade.oanda.com

---

## Notes

- The code uses **mid prices** (average of bid/ask)
- Only **complete candles** are returned (incomplete candles at end of day are excluded)
- Maximum **5000 candles per request** (code handles chunking automatically)
- Default is **practice API** (set `practice=False` for live)

