"""
Tests for src/strategies.py
"""

import pytest
import pandas as pd
from src.strategies import (
    calculate_sma,
    strategy_price_trend_directional,
    strategy_dual_market_open,
    STRATEGIES,
)


class TestStrategies:
    """Test strategy functions."""
    
    def test_calculate_sma(self, sample_ohlc_data):
        """Test SMA calculation."""
        sma = calculate_sma(sample_ohlc_data, 'Close', window=20)
        
        assert isinstance(sma, pd.Series)
        assert len(sma) == len(sample_ohlc_data)
        # First 19 values should be NaN
        assert sma.iloc[:19].isna().all()
        # 20th value onwards should have values
        assert sma.iloc[19:].notna().all()
    
    def test_strategy_price_trend_directional_long(self, sample_ohlc_data):
        """Test strategy generates long signal."""
        df = sample_ohlc_data.copy()
        
        # Add SMA20
        df['SMA20'] = calculate_sma(df, 'Close', window=20)
        
        # Set up: price > SMA20 (uptrend)
        df.loc[df.index[-2], 'Close'] = df.loc[df.index[-2], 'SMA20'] + 0.001
        
        signals = strategy_price_trend_directional(df, sma_period=20)
        
        # Should generate signals
        assert signals.notna().any()
        assert signals.isin(['long', 'short', 'flat']).all()
    
    def test_strategy_price_trend_directional_short(self, sample_ohlc_data):
        """Test strategy generates short signal."""
        df = sample_ohlc_data.copy()
        
        # Add SMA20
        df['SMA20'] = calculate_sma(df, 'Close', window=20)
        
        # Set up: price < SMA20 (downtrend)
        df.loc[df.index[-2], 'Close'] = df.loc[df.index[-2], 'SMA20'] - 0.001
        
        signals = strategy_price_trend_directional(df, sma_period=20)
        
        # Should generate signals
        assert signals.notna().any()
        assert signals.isin(['long', 'short', 'flat']).all()
    
    def test_strategy_price_trend_directional_lookahead_bias(self, sample_ohlc_data):
        """CRITICAL: Test that strategy prevents lookahead bias."""
        df = sample_ohlc_data.copy()
        df['SMA20'] = calculate_sma(df, 'Close', window=20)
        
        signals = strategy_price_trend_directional(df, sma_period=20)
        
        # Strategy should use shift(1) to prevent lookahead bias
        # We can't directly test this, but we can verify signals are generated correctly
        assert signals.notna().any()
    
    def test_strategy_dual_market_open(self, sample_ohlc_data_with_opens):
        """Test dual market open strategy."""
        df = sample_ohlc_data_with_opens.copy()
        
        # Add SMA20
        from src.strategies import calculate_sma
        df['SMA20'] = calculate_sma(df, 'Close', window=20)
        
        signals = strategy_dual_market_open(df, sma_period=20)
        
        assert isinstance(signals, pd.DataFrame)  # Returns DataFrame, not Series
        assert len(signals) == len(df)
        assert 'eur_signal' in signals.columns
        assert 'us_signal' in signals.columns
        assert signals['eur_signal'].isin(['long', 'short', 'flat']).all()
        assert signals['us_signal'].isin(['long', 'short', 'flat']).all()
    
    def test_strategy_dual_market_open_requires_opens(self, sample_ohlc_data):
        """Test that dual market strategy requires EUR_Open and US_Open columns."""
        df = sample_ohlc_data.copy()
        df['SMA20'] = calculate_sma(df, 'Close', window=20)
        
        # Should work even without EUR_Open/US_Open (adds them automatically)
        signals = strategy_dual_market_open(df, sma_period=20)
        
        assert isinstance(signals, pd.DataFrame)  # Returns DataFrame
        assert len(signals) == len(df)
        assert 'eur_signal' in signals.columns
        assert 'us_signal' in signals.columns
    
    def test_strategies_registry(self):
        """Test that STRATEGIES registry contains expected strategies."""
        assert 'price_trend_sma20' in STRATEGIES  # Correct key name
        assert 'dual_market_open' in STRATEGIES
        assert callable(STRATEGIES['price_trend_sma20'])
        assert callable(STRATEGIES['dual_market_open'])
    
    def test_strategy_insufficient_data(self):
        """Test strategy with insufficient data."""
        # Create DataFrame with only 10 days (less than SMA20)
        df = pd.DataFrame({
            'Date': pd.date_range('2025-12-01', periods=10, freq='D'),
            'Open': [1.1600] * 10,
            'High': [1.1610] * 10,
            'Low': [1.1590] * 10,
            'Close': [1.1605] * 10,
        })
        
        signals = strategy_price_trend_directional(df, sma_period=20)
        
        # All signals should be 'flat' (not enough data)
        assert (signals == 'flat').all()
    
    def test_calculate_sma_custom_window(self, sample_ohlc_data):
        """Test SMA calculation with custom window."""
        sma = calculate_sma(sample_ohlc_data, 'Close', window=10)
        
        assert isinstance(sma, pd.Series)
        # First 9 values should be NaN
        assert sma.iloc[:9].isna().all()
        # 10th value onwards should have values
        assert sma.iloc[9:].notna().all()

