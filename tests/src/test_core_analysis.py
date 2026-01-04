"""
Tests for src/core_analysis.py
"""

import pytest
import pandas as pd
import numpy as np
from src.core_analysis import (
    calculate_daily_metrics,
    calculate_distribution_stats,
    analyze_range_distribution,
    calculate_adr,
    calculate_mfe_mae,
)


class TestCoreAnalysis:
    """Test core analysis functions."""
    
    def test_calculate_daily_metrics(self, sample_ohlc_data):
        """Test daily metrics calculation."""
        df = calculate_daily_metrics(sample_ohlc_data)
        
        # Check that new columns are added
        assert 'range_pips' in df.columns
        assert 'up_from_open_pips' in df.columns
        assert 'down_from_open_pips' in df.columns
        assert 'net_from_open_pips' in df.columns
        assert 'body_pips' in df.columns
        assert 'upper_shadow_pips' in df.columns
        assert 'lower_shadow_pips' in df.columns
    
    def test_calculate_daily_metrics_range_pips(self, sample_ohlc_data):
        """Test that range_pips is calculated correctly."""
        df = calculate_daily_metrics(sample_ohlc_data)
        
        for idx, row in df.iterrows():
            # Range should be High - Low in pips
            expected_range = (row['High'] - row['Low']) * 10000
            assert abs(row['range_pips'] - expected_range) < 0.01
    
    def test_calculate_daily_metrics_up_from_open(self, sample_ohlc_data):
        """Test up_from_open_pips calculation."""
        df = calculate_daily_metrics(sample_ohlc_data)
        
        for idx, row in df.iterrows():
            # Up from open should be High - Open in pips
            expected = (row['High'] - row['Open']) * 10000
            assert abs(row['up_from_open_pips'] - expected) < 0.01
    
    def test_calculate_daily_metrics_down_from_open(self, sample_ohlc_data):
        """Test down_from_open_pips calculation."""
        df = calculate_daily_metrics(sample_ohlc_data)
        
        for idx, row in df.iterrows():
            # Down from open should be Open - Low in pips
            expected = (row['Open'] - row['Low']) * 10000
            assert abs(row['down_from_open_pips'] - expected) < 0.01
    
    def test_calculate_distribution_stats(self, sample_ohlc_data):
        """Test distribution statistics calculation."""
        df = calculate_daily_metrics(sample_ohlc_data)
        stats = calculate_distribution_stats(df, 'range_pips')
        
        assert 'count' in stats
        assert 'mean' in stats
        assert 'median' in stats
        assert 'std' in stats
        assert 'min' in stats
        assert 'max' in stats
        assert 'p25' in stats
        assert 'p50' in stats
        assert 'p75' in stats
        assert 'p90' in stats
    
    def test_calculate_distribution_stats_values(self, sample_ohlc_data):
        """Test that distribution stats values are correct."""
        df = calculate_daily_metrics(sample_ohlc_data)
        stats = calculate_distribution_stats(df, 'range_pips')
        
        # Mean should match DataFrame mean
        assert abs(stats['mean'] - df['range_pips'].mean()) < 0.01
        # Median should match DataFrame median
        assert abs(stats['median'] - df['range_pips'].median()) < 0.01
        # Min should match DataFrame min
        assert abs(stats['min'] - df['range_pips'].min()) < 0.01
        # Max should match DataFrame max
        assert abs(stats['max'] - df['range_pips'].max()) < 0.01
    
    def test_analyze_range_distribution(self, sample_ohlc_data):
        """Test range distribution analysis."""
        df = calculate_daily_metrics(sample_ohlc_data)
        result_df = analyze_range_distribution(df)
        
        assert isinstance(result_df, pd.DataFrame)
        assert 'threshold_pips' in result_df.columns
        assert 'up_from_open_count' in result_df.columns
        assert 'down_from_open_count' in result_df.columns
        assert 'range_count' in result_df.columns
        assert len(result_df) > 0
    
    def test_calculate_adr(self, sample_ohlc_data):
        """Test ADR calculation."""
        df = calculate_daily_metrics(sample_ohlc_data)
        adr = calculate_adr(df, window=20)
        
        assert isinstance(adr, pd.Series)
        assert len(adr) == len(df)
        # ADR should be positive
        assert (adr >= 0).all()
    
    def test_calculate_adr_rolling_window(self, sample_ohlc_data):
        """Test that ADR uses rolling window correctly."""
        df = calculate_daily_metrics(sample_ohlc_data)
        adr = calculate_adr(df, window=20)
        
        # For row 20+, ADR should be mean of last 20 range_pips
        if len(df) >= 20:
            for i in range(19, len(df)):
                expected_adr = df['range_pips'].iloc[i-19:i+1].mean()
                assert abs(adr.iloc[i] - expected_adr) < 0.01
    
    def test_calculate_mfe_mae_long(self, sample_ohlc_data):
        """Test MFE/MAE calculation for long trades."""
        mfe, mae = calculate_mfe_mae(sample_ohlc_data, entry_price_col='Open', direction='long')
        
        assert isinstance(mfe, pd.Series)
        assert isinstance(mae, pd.Series)
        assert len(mfe) == len(sample_ohlc_data)
        assert len(mae) == len(sample_ohlc_data)
        
        # MFE should be >= 0 (favorable excursion)
        assert (mfe >= 0).all()
        # MAE should be >= 0 (adverse excursion)
        assert (mae >= 0).all()
    
    def test_calculate_mfe_mae_short(self, sample_ohlc_data):
        """Test MFE/MAE calculation for short trades."""
        mfe, mae = calculate_mfe_mae(sample_ohlc_data, entry_price_col='Open', direction='short')
        
        assert isinstance(mfe, pd.Series)
        assert isinstance(mae, pd.Series)
        assert len(mfe) == len(sample_ohlc_data)
        assert len(mae) == len(sample_ohlc_data)
        
        # MFE should be >= 0
        assert (mfe >= 0).all()
        # MAE should be >= 0
        assert (mae >= 0).all()
    
    def test_calculate_mfe_mae_long_values(self, sample_ohlc_data):
        """Test that MFE/MAE values are correct for long trades."""
        mfe, mae = calculate_mfe_mae(sample_ohlc_data, entry_price_col='Open', direction='long')
        
        for idx, row in sample_ohlc_data.iterrows():
            # For long: MFE = High - Entry, MAE = Entry - Low
            expected_mfe = (row['High'] - row['Open']) * 10000
            expected_mae = (row['Open'] - row['Low']) * 10000
            
            assert abs(mfe.loc[idx] - expected_mfe) < 0.01
            assert abs(mae.loc[idx] - expected_mae) < 0.01
    
    def test_calculate_mfe_mae_short_values(self, sample_ohlc_data):
        """Test that MFE/MAE values are correct for short trades."""
        mfe, mae = calculate_mfe_mae(sample_ohlc_data, entry_price_col='Open', direction='short')
        
        for idx, row in sample_ohlc_data.iterrows():
            # For short: MFE = Entry - Low, MAE = High - Entry
            expected_mfe = (row['Open'] - row['Low']) * 10000
            expected_mae = (row['High'] - row['Open']) * 10000
            
            assert abs(mfe.loc[idx] - expected_mfe) < 0.01
            assert abs(mae.loc[idx] - expected_mae) < 0.01


