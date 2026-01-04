"""
Pytest configuration and shared fixtures for FX Open-Range Lab tests.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import Mock, MagicMock
from typing import Dict, List, Optional

# Add project root to path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ============================================================================
# Helper Functions
# ============================================================================

def create_sample_dataframe(
    days: int = 30,
    start_date: Optional[datetime] = None,
    base_price: float = 1.1600,
    volatility: float = 0.002
) -> pd.DataFrame:
    """
    Create a sample EUR/USD OHLC DataFrame for testing.
    
    Parameters:
    -----------
    days : int
        Number of days of data to generate
    start_date : datetime, optional
        Start date (default: 30 days ago)
    base_price : float
        Base price level (default: 1.1600)
    volatility : float
        Price volatility (default: 0.002)
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with Date, Open, High, Low, Close columns
    """
    if start_date is None:
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    dates = pd.date_range(start=start_date, periods=days, freq='D', tz='UTC')
    
    # Generate realistic price movements
    np.random.seed(42)  # For reproducible tests
    price_changes = np.random.normal(0, volatility, days)
    prices = base_price + np.cumsum(price_changes)
    
    data = []
    for i, date in enumerate(dates):
        open_price = prices[i]
        # Generate realistic daily range (typically 0.5-1.5% of price)
        daily_range = np.random.uniform(0.005, 0.015) * open_price
        high = open_price + np.random.uniform(0, daily_range)
        low = open_price - np.random.uniform(0, daily_range)
        close = open_price + np.random.uniform(-daily_range/2, daily_range/2)
        
        # Ensure High >= max(Open, Close) and Low <= min(Open, Close)
        high = max(high, open_price, close)
        low = min(low, open_price, close)
        
        data.append({
            'Date': date,
            'Open': round(open_price, 5),
            'High': round(high, 5),
            'Low': round(low, 5),
            'Close': round(close, 5),
        })
    
    df = pd.DataFrame(data)
    return df


def assert_dataframe_structure(df: pd.DataFrame, required_cols: List[str] = None):
    """
    Assert that DataFrame has required structure.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame to check
    required_cols : list, optional
        Required columns (default: Date, Open, High, Low, Close)
    """
    if required_cols is None:
        required_cols = ['Date', 'Open', 'High', 'Low', 'Close']
    
    assert isinstance(df, pd.DataFrame), "Must be a DataFrame"
    assert len(df) > 0, "DataFrame must not be empty"
    
    for col in required_cols:
        assert col in df.columns, f"Missing required column: {col}"
        assert not df[col].isna().all(), f"Column {col} must have some non-null values"


def assert_backtest_result(result):
    """
    Assert that backtest result has required structure.
    
    Parameters:
    -----------
    result
        BacktestResult object to check
    """
    assert hasattr(result, 'trades'), "BacktestResult must have 'trades' attribute"
    assert hasattr(result, 'equity_curve'), "BacktestResult must have 'equity_curve' attribute"
    assert hasattr(result, 'get_summary_stats'), "BacktestResult must have 'get_summary_stats' method"
    
    assert isinstance(result.trades, pd.DataFrame), "trades must be a DataFrame"
    assert isinstance(result.equity_curve, pd.Series), "equity_curve must be a Series"


# ============================================================================
# Data Fixtures
# ============================================================================

@pytest.fixture
def sample_ohlc_data():
    """Sample EUR/USD OHLC DataFrame (30 days)."""
    return create_sample_dataframe(days=30)


@pytest.fixture
def sample_ohlc_data_60days():
    """Sample EUR/USD OHLC DataFrame (60 days)."""
    return create_sample_dataframe(days=60)


@pytest.fixture
def sample_ohlc_data_with_sma(sample_ohlc_data):
    """Sample OHLC data with SMA20 calculated."""
    df = sample_ohlc_data.copy()
    df['SMA20'] = df['Close'].rolling(window=20, min_periods=20).mean()
    return df


@pytest.fixture
def sample_ohlc_data_with_opens(sample_ohlc_data):
    """Sample OHLC data with EUR_Open and US_Open columns."""
    df = sample_ohlc_data.copy()
    
    # Add market open prices (simplified approximation)
    eur_opens = []
    us_opens = []
    
    for idx, row in df.iterrows():
        # EUR open: use daily open (simplified)
        eur_opens.append(row['Open'])
        # US open: interpolate between open and close (30% through day)
        us_open = row['Open'] + (row['Close'] - row['Open']) * 0.3
        us_opens.append(us_open)
    
    df['EUR_Open'] = eur_opens
    df['US_Open'] = us_opens
    
    return df


@pytest.fixture
def sample_csv_file(tmp_path):
    """Create a temporary CSV file with sample data."""
    csv_file = tmp_path / "sample_eur_usd.csv"
    df = create_sample_dataframe(days=30)
    
    # Format for CSV (MM/DD/YYYY)
    df_csv = df.copy()
    df_csv['Date'] = df_csv['Date'].dt.strftime('%m/%d/%Y')
    df_csv['Price'] = df_csv['Close']  # Add Price column (same as Close)
    df_csv = df_csv[['Date', 'Price', 'Open', 'High', 'Low']]
    
    df_csv.to_csv(csv_file, index=False)
    return str(csv_file)


# ============================================================================
# OANDA Client Mocks
# ============================================================================

@pytest.fixture
def mock_oanda_client():
    """Mock OandaTradingClient for testing."""
    from app.utils.oanda_client import OandaTradingClient
    
    client = Mock(spec=OandaTradingClient)
    client.api_token = "test-token"
    client.practice = True
    client.account_id = "test-account-123"
    client.base_url = "https://api-fxpractice.oanda.com"
    
    # Mock methods
    client.get_account_info.return_value = {
        'id': 'test-account-123',
        'currency': 'USD',
        'tags': [{'name': 'Practice Account'}]
    }
    
    client.get_account_summary.return_value = {
        'balance': '10000.00',
        'currency': 'USD',
        'unrealizedPL': '0.00',
        'marginUsed': '0.00',
        'marginAvailable': '10000.00'
    }
    
    client.get_open_positions.return_value = []
    client.get_open_trades.return_value = []
    
    client.get_current_price.return_value = {
        'bid': 1.1600,
        'ask': 1.1602,
        'mid': 1.1601,
        'time': datetime.now(timezone.utc).isoformat()
    }
    
    # Mock fetch_candles to return sample data
    def mock_fetch_candles(*args, **kwargs):
        return create_sample_dataframe(days=30)
    
    client.fetch_candles = Mock(side_effect=mock_fetch_candles)
    
    client.place_market_order.return_value = {
        'orderFillTransaction': {
            'id': 'test-order-123',
            'instrument': 'EUR_USD',
            'units': '1',
            'price': '1.1601'
        }
    }
    
    client.close_trade.return_value = {'id': 'test-trade-123'}
    client.close_all_trades.return_value = {'ids': ['test-trade-123']}
    
    return client


@pytest.fixture
def mock_oanda_api():
    """Mock OandaAPI for testing."""
    from src.oanda_api import OandaAPI
    
    api = Mock(spec=OandaAPI)
    api.api_token = "test-token"
    api.practice = True
    api.base_url = "https://api-fxpractice.oanda.com"
    
    # Mock methods
    api.get_instruments.return_value = ['EUR_USD', 'GBP_USD', 'USD_JPY']
    
    api.get_account_info.return_value = {
        'id': 'test-account-123',
        'currency': 'USD'
    }
    
    # Mock fetch_candles to return sample data
    def mock_fetch_candles(*args, **kwargs):
        return create_sample_dataframe(days=30)
    
    api.fetch_candles = Mock(side_effect=mock_fetch_candles)
    api.fetch_daily_data = Mock(side_effect=mock_fetch_candles)
    
    return api


# ============================================================================
# Sample Trade Data
# ============================================================================

@pytest.fixture
def sample_trade_data():
    """Sample trade execution result."""
    return {
        'orderFillTransaction': {
            'id': 'test-order-123',
            'instrument': 'EUR_USD',
            'units': '1',
            'price': '1.1601',
            'time': datetime.now(timezone.utc).isoformat()
        }
    }


@pytest.fixture
def sample_account_info():
    """Sample OANDA account information."""
    return {
        'id': 'test-account-123',
        'currency': 'USD',
        'balance': '10000.00',
        'unrealizedPL': '0.00',
        'marginUsed': '0.00',
        'marginAvailable': '10000.00',
        'tags': [{'name': 'Practice Account'}]
    }


# ============================================================================
# Datetime Fixtures
# ============================================================================

@pytest.fixture
def sample_datetime_naive():
    """Sample naive datetime (no timezone)."""
    return datetime(2025, 12, 2, 13, 59, 27)


@pytest.fixture
def sample_datetime_utc():
    """Sample UTC timezone-aware datetime."""
    return datetime(2025, 12, 2, 13, 59, 27, tzinfo=timezone.utc)


@pytest.fixture
def sample_datetime_with_microseconds():
    """Sample datetime with microseconds (the problematic case)."""
    return datetime(2025, 12, 2, 13, 59, 27, 990721, tzinfo=timezone.utc)


@pytest.fixture
def sample_datetime_with_offset():
    """Sample datetime with timezone offset."""
    return datetime(2025, 12, 2, 13, 59, 27, tzinfo=timezone(timedelta(hours=-5)))


# ============================================================================
# Settings Fixtures
# ============================================================================

@pytest.fixture
def mock_settings(monkeypatch):
    """Mock Settings for testing."""
    import app.config.settings as settings_module
    
    # Save original values
    original_values = {
        'OANDA_API_TOKEN': settings_module.Settings.OANDA_API_TOKEN,
        'OANDA_PRACTICE_MODE': settings_module.Settings.OANDA_PRACTICE_MODE,
        'DUAL_MARKET_OPEN_ENABLED': settings_module.Settings.DUAL_MARKET_OPEN_ENABLED,
    }
    
    # Set test values
    monkeypatch.setattr(settings_module.Settings, 'OANDA_API_TOKEN', 'test-token')
    monkeypatch.setattr(settings_module.Settings, 'OANDA_PRACTICE_MODE', True)
    monkeypatch.setattr(settings_module.Settings, 'DUAL_MARKET_OPEN_ENABLED', True)
    
    yield settings_module.Settings
    
    # Restore original values
    for key, value in original_values.items():
        monkeypatch.setattr(settings_module.Settings, key, value)


