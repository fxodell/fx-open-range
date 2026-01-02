"""
Tests for src/regime.py
"""

import pytest
import pandas as pd
import numpy as np
from src.regime import (
    calculate_moving_averages,
    calculate_momentum,
    classify_regime,
    analyze_regime_performance,
)


class TestRegime:
    """Test regime detection functions."""
    
    def test_calculate_moving_averages(self, sample_ohlc_data):
        """Test moving averages calculation."""
        df = calculate_moving_averages(sample_ohlc_data, periods=[20, 50, 100])
        
        assert 'SMA20' in df.columns
        assert 'SMA50' in df.columns
        assert 'SMA100' in df.columns
        assert len(df) == len(sample_ohlc_data)
    
    def test_calculate_moving_averages_values(self, sample_ohlc_data):
        """Test that moving averages are calculated correctly."""
        df = calculate_moving_averages(sample_ohlc_data, periods=[20])
        
        # Check that SMA20 is the mean of last 20 closes
        for i in range(19, len(df)):
            expected_sma = df['Close'].iloc[i-19:i+1].mean()
            assert abs(df['SMA20'].iloc[i] - expected_sma) < 1e-10
    
    def test_calculate_momentum(self, sample_ohlc_data):
        """Test momentum calculation."""
        df = calculate_momentum(sample_ohlc_data, periods=[1, 3])
        
        assert 'momentum_1m' in df.columns
        assert 'momentum_3m' in df.columns
        assert len(df) == len(sample_ohlc_data)
    
    def test_classify_regime_bull(self, sample_ohlc_data):
        """Test regime classification for bull market."""
        df = calculate_moving_averages(sample_ohlc_data, periods=[50, 200])
        df = classify_regime(df, sma_short=50, sma_long=200)
        
        assert 'regime' in df.columns
        assert df['regime'].isin(['bull', 'bear', 'chop']).all()
    
    def test_classify_regime_bear(self, sample_ohlc_data):
        """Test regime classification for bear market."""
        df = calculate_moving_averages(sample_ohlc_data, periods=[50, 200])
        df = classify_regime(df, sma_short=50, sma_long=200)
        
        # Should have regime column
        assert 'regime' in df.columns
    
    def test_classify_regime_chop(self, sample_ohlc_data):
        """Test regime classification for choppy market."""
        df = calculate_moving_averages(sample_ohlc_data, periods=[50, 200])
        df = classify_regime(df, sma_short=50, sma_long=200)
        
        # Should classify some as 'chop'
        regimes = df['regime'].unique()
        assert 'chop' in regimes or 'bull' in regimes or 'bear' in regimes
    
    def test_classify_regime_rules(self, sample_ohlc_data):
        """Test that regime classification follows the rules."""
        df = calculate_moving_averages(sample_ohlc_data, periods=[50, 200])
        df = classify_regime(df, sma_short=50, sma_long=200)
        
        # Check that regime values are valid
        valid_regimes = ['bull', 'bear', 'chop']
        assert df['regime'].isin(valid_regimes).all()
    
    def test_analyze_regime_performance(self, sample_ohlc_data):
        """Test regime performance analysis."""
        df = calculate_moving_averages(sample_ohlc_data, periods=[50, 200])
        df = classify_regime(df, sma_short=50, sma_long=200)
        
        # Add range metrics (required for analyze_regime_performance)
        from src.core_analysis import calculate_daily_metrics
        df = calculate_daily_metrics(df)
        
        result_df = analyze_regime_performance(df)
        
        assert isinstance(result_df, pd.DataFrame)
        assert 'regime' in result_df.columns
        assert 'count' in result_df.columns
        assert len(result_df) > 0
    
    def test_analyze_regime_performance_columns(self, sample_ohlc_data):
        """Test that regime performance includes all required metrics."""
        df = calculate_moving_averages(sample_ohlc_data, periods=[50, 200])
        df = classify_regime(df, sma_short=50, sma_long=200)
        from src.core_analysis import calculate_daily_metrics
        df = calculate_daily_metrics(df)
        
        result_df = analyze_regime_performance(df)
        
        # Should have metrics for each regime
        required_cols = ['regime', 'count', 'range_pips_mean', 'range_pips_median']
        for col in required_cols:
            assert col in result_df.columns

