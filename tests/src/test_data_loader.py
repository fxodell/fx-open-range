"""
Tests for src/data_loader.py
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from src.data_loader import (
    load_eurusd_data,
    price_to_pips,
    pips_to_price,
    load_intraday_data,
    add_market_open_prices,
)


class TestDataLoader:
    """Test data loading functions."""
    
    def test_load_eurusd_data_valid_csv(self, sample_csv_file):
        """Test loading valid CSV file."""
        df = load_eurusd_data(sample_csv_file)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert 'Date' in df.columns
        assert 'Open' in df.columns
        assert 'High' in df.columns
        assert 'Low' in df.columns
        assert 'Close' in df.columns
    
    def test_load_eurusd_data_date_parsing(self, sample_csv_file):
        """Test that dates are parsed correctly."""
        df = load_eurusd_data(sample_csv_file)
        
        assert pd.api.types.is_datetime64_any_dtype(df['Date'])
        assert df['Date'].is_monotonic_increasing  # Should be sorted chronologically
    
    def test_load_eurusd_data_column_renaming(self, sample_csv_file):
        """Test that Price column is renamed to Close."""
        df = load_eurusd_data(sample_csv_file)
        
        assert 'Close' in df.columns
        assert 'Price' not in df.columns or df['Price'].equals(df['Close'])
    
    def test_load_eurusd_data_nan_removal(self, tmp_path):
        """Test that NaN values are removed."""
        # Create CSV with NaN values
        csv_file = tmp_path / "test_with_nan.csv"
        data = {
            'Date': ['12/01/2025', '12/02/2025', '12/03/2025'],
            'Price': [1.1600, np.nan, 1.1620],
            'Open': [1.1595, 1.1605, 1.1615],
            'High': [1.1610, 1.1615, 1.1630],
            'Low': [1.1590, 1.1600, 1.1610],
        }
        df_test = pd.DataFrame(data)
        df_test.to_csv(csv_file, index=False)
        
        df = load_eurusd_data(str(csv_file))
        
        # Should have fewer rows (NaN row removed)
        assert len(df) < len(df_test)
        assert df['Close'].notna().all()
    
    def test_price_to_pips(self):
        """Test price to pips conversion."""
        # For EUR/USD: 1 pip = 0.0001
        assert abs(price_to_pips(0.0001) - 1.0) < 0.01
        assert abs(price_to_pips(0.0010) - 10.0) < 0.01
        assert abs(price_to_pips(0.0100) - 100.0) < 0.01
        assert abs(price_to_pips(1.1600 - 1.1500) - 100.0) < 0.01  # 0.01 = 100 pips
    
    def test_pips_to_price(self):
        """Test pips to price conversion."""
        assert pips_to_price(1.0) == 0.0001
        assert pips_to_price(10.0) == 0.0010
        assert pips_to_price(100.0) == 0.0100
        assert pips_to_price(1000.0) == 0.1000
    
    def test_price_pips_roundtrip(self):
        """Test that price_to_pips and pips_to_price are inverse."""
        test_prices = [0.0001, 0.0010, 0.0100, 0.1000]
        
        for price in test_prices:
            pips = price_to_pips(price)
            converted_back = pips_to_price(pips)
            assert abs(price - converted_back) < 1e-10
    
    def test_add_market_open_prices(self, sample_ohlc_data):
        """Test adding market open prices."""
        df = add_market_open_prices(sample_ohlc_data)
        
        assert 'EUR_Open' in df.columns
        assert 'US_Open' in df.columns
        assert len(df) == len(sample_ohlc_data)
        assert df['EUR_Open'].notna().all()
        assert df['US_Open'].notna().all()
    
    def test_add_market_open_prices_eur_approximation(self, sample_ohlc_data):
        """Test that EUR open prices are reasonable."""
        df = add_market_open_prices(sample_ohlc_data)
        
        # EUR open should be close to daily open (simplified approximation)
        for idx, row in df.iterrows():
            # EUR open should be within reasonable range of daily open
            diff = abs(row['EUR_Open'] - row['Open'])
            assert diff < 0.01  # Should be very close
    
    def test_add_market_open_prices_us_approximation(self, sample_ohlc_data):
        """Test that US open prices are reasonable."""
        df = add_market_open_prices(sample_ohlc_data)
        
        # US open should be between daily open and close (30% interpolation)
        for idx, row in df.iterrows():
            daily_range = abs(row['Close'] - row['Open'])
            us_open_diff = abs(row['US_Open'] - row['Open'])
            # US open should be roughly 30% through the range
            assert us_open_diff <= daily_range * 1.1  # Allow some tolerance
    
    def test_load_intraday_data_nonexistent_file(self):
        """Test loading non-existent intraday file."""
        result = load_intraday_data("nonexistent_file.csv")
        assert result is None
    
    def test_load_intraday_data_missing_columns(self, tmp_path):
        """Test loading intraday file with missing columns."""
        csv_file = tmp_path / "test_invalid.csv"
        data = {'Date': ['2025-12-01'], 'Price': [1.1600]}  # Missing OHLC
        df_test = pd.DataFrame(data)
        df_test.to_csv(csv_file, index=False)
        
        result = load_intraday_data(str(csv_file))
        assert result is None

