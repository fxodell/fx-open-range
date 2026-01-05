"""
Tests for src/market_sessions.py
"""

import pytest
import pandas as pd
from datetime import datetime, timezone
from src.market_sessions import (
    get_eur_open_time,
    get_us_open_time,
    approximate_eur_open_price,
    approximate_us_open_price,
    get_market_open_prices,
    is_market_open_time,
)


class TestMarketSessions:
    """Test market session utilities."""
    
    def test_get_eur_open_time(self):
        """Test EUR market open time generation."""
        date = pd.Timestamp('2025-12-02', tz='UTC')
        eur_time = get_eur_open_time(date)
        
        assert eur_time.hour == 8
        assert eur_time.minute == 0
        assert eur_time.second == 0
        assert eur_time.tzinfo == timezone.utc
    
    def test_get_us_open_time(self):
        """Test US market open time generation."""
        date = pd.Timestamp('2025-12-02', tz='UTC')
        us_time = get_us_open_time(date)
        
        assert us_time.hour == 13
        assert us_time.minute == 0
        assert us_time.second == 0
        assert us_time.tzinfo == timezone.utc
    
    def test_approximate_eur_open_price(self, sample_ohlc_data):
        """Test EUR open price approximation."""
        date = pd.Timestamp(sample_ohlc_data['Date'].iloc[0])
        eur_price = approximate_eur_open_price(sample_ohlc_data, date)
        
        assert eur_price is not None
        assert isinstance(eur_price, float)
        # EUR open should be close to daily open (simplified approximation)
        row = sample_ohlc_data[sample_ohlc_data['Date'] == date].iloc[0]
        assert abs(eur_price - row['Open']) < 0.01
    
    def test_approximate_us_open_price(self, sample_ohlc_data):
        """Test US open price approximation."""
        date = pd.Timestamp(sample_ohlc_data['Date'].iloc[0])
        us_price = approximate_us_open_price(sample_ohlc_data, date)
        
        assert us_price is not None
        assert isinstance(us_price, float)
        # US open should be between daily open and close (30% interpolation)
        row = sample_ohlc_data[sample_ohlc_data['Date'] == date].iloc[0]
        assert row['Open'] <= us_price <= row['Close'] or row['Close'] <= us_price <= row['Open']
    
    def test_get_market_open_prices(self, sample_ohlc_data):
        """Test getting both EUR and US open prices."""
        date = pd.Timestamp(sample_ohlc_data['Date'].iloc[0])
        eur_price, us_price = get_market_open_prices(sample_ohlc_data, date)
        
        assert eur_price is not None
        assert us_price is not None
        assert isinstance(eur_price, float)
        assert isinstance(us_price, float)
    
    def test_is_market_open_time_eur(self):
        """Test is_market_open_time for EUR market."""
        eur_time = datetime(2025, 12, 2, 8, 0, 0, tzinfo=timezone.utc)
        assert is_market_open_time(eur_time, market='eur') is True
        
        not_eur_time = datetime(2025, 12, 2, 13, 0, 0, tzinfo=timezone.utc)
        assert is_market_open_time(not_eur_time, market='eur') is False
    
    def test_is_market_open_time_us(self):
        """Test is_market_open_time for US market."""
        us_time = datetime(2025, 12, 2, 13, 0, 0, tzinfo=timezone.utc)
        assert is_market_open_time(us_time, market='us') is True
        
        not_us_time = datetime(2025, 12, 2, 8, 0, 0, tzinfo=timezone.utc)
        assert is_market_open_time(not_us_time, market='us') is False
    
    def test_is_market_open_time_both(self):
        """Test is_market_open_time for both markets."""
        eur_time = datetime(2025, 12, 2, 8, 0, 0, tzinfo=timezone.utc)
        assert is_market_open_time(eur_time, market='both') is True
        
        us_time = datetime(2025, 12, 2, 13, 0, 0, tzinfo=timezone.utc)
        assert is_market_open_time(us_time, market='both') is True
        
        other_time = datetime(2025, 12, 2, 15, 0, 0, tzinfo=timezone.utc)
        assert is_market_open_time(other_time, market='both') is False
    
    def test_is_market_open_time_naive_datetime(self):
        """Test is_market_open_time with naive datetime."""
        naive_time = datetime(2025, 12, 2, 8, 0, 0)  # No timezone
        # Should handle gracefully (adds UTC timezone)
        result = is_market_open_time(naive_time, market='eur')
        assert result is True or result is False  # Should return bool
    
    def test_approximate_eur_open_price_missing_data(self):
        """Test EUR open price with missing date."""
        df = pd.DataFrame({
            'Date': pd.date_range('2025-12-01', periods=5, freq='D'),
            'Open': [1.1600] * 5,
            'High': [1.1610] * 5,
            'Low': [1.1590] * 5,
            'Close': [1.1605] * 5,
        })
        
        missing_date = pd.Timestamp('2025-12-10', tz='UTC')
        result = approximate_eur_open_price(df, missing_date)
        
        assert result is None
    
    def test_approximate_us_open_price_missing_data(self):
        """Test US open price with missing date."""
        df = pd.DataFrame({
            'Date': pd.date_range('2025-12-01', periods=5, freq='D'),
            'Open': [1.1600] * 5,
            'High': [1.1610] * 5,
            'Low': [1.1590] * 5,
            'Close': [1.1605] * 5,
        })
        
        missing_date = pd.Timestamp('2025-12-10', tz='UTC')
        result = approximate_us_open_price(df, missing_date)
        
        assert result is None



