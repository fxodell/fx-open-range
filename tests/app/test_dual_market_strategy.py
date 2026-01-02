"""
Tests for app/strategies/dual_market_open_strategy.py
"""

import pytest
import pandas as pd
from datetime import datetime, timezone
from app.strategies.dual_market_open_strategy import (
    get_dual_market_signals,
    check_eur_market_open,
    check_us_market_open,
    get_market_open_signal,
)


class TestDualMarketStrategy:
    """Test dual market open strategy functions."""
    
    def test_get_dual_market_signals(self, sample_ohlc_data):
        """Test get_dual_market_signals returns both EUR and US signals."""
        signals = get_dual_market_signals(sample_ohlc_data, sma_period=20)
        
        assert isinstance(signals, dict)
        assert 'eur' in signals
        assert 'us' in signals
        
        eur_signal, eur_price, eur_sma = signals['eur']
        us_signal, us_price, us_sma = signals['us']
        
        assert eur_signal in ['long', 'short', 'flat']
        assert us_signal in ['long', 'short', 'flat']
        assert eur_price is not None or eur_signal == 'flat'
        assert us_price is not None or us_signal == 'flat'
    
    def test_get_dual_market_signals_same_signal(self, sample_ohlc_data):
        """Test that EUR and US signals use the same logic (both based on previous day's close)."""
        signals = get_dual_market_signals(sample_ohlc_data, sma_period=20)
        
        # Both should use the same signal logic
        eur_signal, _, _ = signals['eur']
        us_signal, _, _ = signals['us']
        
        # They should be the same (both based on previous day's close vs SMA20)
        assert eur_signal == us_signal
    
    @pytest.mark.parametrize("hour,expected", [
        (7, False),  # Before EUR open
        (8, True),   # EUR open hour
        (9, False),  # After EUR open window
        (12, False), # Before US open (not EUR)
        (13, False), # US open hour (not EUR)
        (14, False), # After US open window
    ])
    def test_check_eur_market_open(self, hour, expected):
        """Test EUR market open detection."""
        test_time = datetime(2025, 12, 2, hour, 0, 0, tzinfo=timezone.utc)
        result = check_eur_market_open(test_time)
        assert result == expected
    
    @pytest.mark.parametrize("hour,expected", [
        (12, False), # Before US open
        (13, True),  # US open hour
        (14, False), # After US open window
        (7, False),  # Before US open
        (8, False),  # EUR open, not US
    ])
    def test_check_us_market_open(self, hour, expected):
        """Test US market open detection."""
        test_time = datetime(2025, 12, 2, hour, 0, 0, tzinfo=timezone.utc)
        result = check_us_market_open(test_time)
        assert result == expected
    
    def test_check_eur_market_open_naive_datetime(self):
        """Test EUR market open with naive datetime (should handle gracefully)."""
        naive_time = datetime(2025, 12, 2, 8, 0, 0)  # No timezone
        result = check_eur_market_open(naive_time)
        # Should still work (function adds UTC timezone)
        assert result is True or result is False  # Should return bool
    
    def test_check_us_market_open_naive_datetime(self):
        """Test US market open with naive datetime."""
        naive_time = datetime(2025, 12, 2, 13, 0, 0)  # No timezone
        result = check_us_market_open(naive_time)
        # Should still work
        assert result is True or result is False
    
    def test_get_market_open_signal_eur(self, sample_ohlc_data):
        """Test get_market_open_signal for EUR market."""
        signal, price, sma = get_market_open_signal(sample_ohlc_data, 'eur', sma_period=20)
        
        assert signal in ['long', 'short', 'flat']
        assert price is not None or signal == 'flat'
        assert sma is not None or signal == 'flat'
    
    def test_get_market_open_signal_us(self, sample_ohlc_data):
        """Test get_market_open_signal for US market."""
        signal, price, sma = get_market_open_signal(sample_ohlc_data, 'us', sma_period=20)
        
        assert signal in ['long', 'short', 'flat']
        assert price is not None or signal == 'flat'
        assert sma is not None or signal == 'flat'
    
    def test_get_market_open_signal_invalid_market(self, sample_ohlc_data):
        """Test get_market_open_signal with invalid market name."""
        with pytest.raises(ValueError, match="market must be 'eur' or 'us'"):
            get_market_open_signal(sample_ohlc_data, 'invalid', sma_period=20)
    
    def test_get_market_open_signal_insufficient_data(self):
        """Test get_market_open_signal with insufficient data."""
        # Create DataFrame with only 10 days (less than SMA20)
        df = pd.DataFrame({
            'Date': pd.date_range('2025-12-01', periods=10, freq='D'),
            'Open': [1.1600] * 10,
            'High': [1.1610] * 10,
            'Low': [1.1590] * 10,
            'Close': [1.1605] * 10,
        })
        
        signal, price, sma = get_market_open_signal(df, 'eur', sma_period=20)
        
        # Should return 'flat' with None values
        assert signal == 'flat'
        assert price is None
        assert sma is None

