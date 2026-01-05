"""
Integration tests for backtest workflows.
"""

import pytest
import pandas as pd
from pathlib import Path
from src.data_loader import load_eurusd_data, add_market_open_prices
from src.core_analysis import calculate_daily_metrics, calculate_adr
from src.regime import calculate_moving_averages, classify_regime, analyze_regime_performance
from src.strategies import strategy_price_trend_directional, strategy_dual_market_open
from src.backtest import backtest_strategy
from src.backtest_no_sl import backtest_strategy_no_sl
from src.backtest_dual_market import backtest_dual_market_open


class TestBacktestWorkflow:
    """Test full backtest workflows."""
    
    def test_single_daily_open_strategy_workflow(self, sample_ohlc_data):
        """Test complete workflow for single daily open strategy."""
        df = sample_ohlc_data.copy()
        
        # Step 1: Prepare data
        from src.strategies import calculate_sma
        df['SMA20'] = calculate_sma(df, 'Close', window=20)
        
        # Step 2: Generate signals
        signals = strategy_price_trend_directional(df, sma_period=20)
        
        # Step 3: Run backtest
        result = backtest_strategy(
            df,
            signals,
            take_profit_pips=10.0,
            stop_loss_pips=10.0,
            cost_per_trade_pips=2.0
        )
        
        # Step 4: Verify results
        assert len(result.trades) >= 0  # May have trades or not
        assert len(result.equity_curve) == len(df)
        assert result.equity_curve.iloc[0] == 10000.0  # Initial equity
        
        # Step 5: Get summary stats
        stats = result.get_summary_stats()
        assert 'total_trades' in stats
        assert 'total_pips' in stats
        assert 'win_rate' in stats
    
    def test_dual_market_open_strategy_workflow(self, sample_ohlc_data_with_opens):
        """Test complete workflow for dual market open strategy."""
        df = sample_ohlc_data_with_opens.copy()
        
        # Step 1: Prepare data
        from src.strategies import calculate_sma
        df['SMA20'] = calculate_sma(df, 'Close', window=20)
        
        # Step 2: Generate signals
        signals_df = strategy_dual_market_open(df, sma_period=20)
        
        # Step 3: Run backtest
        result = backtest_dual_market_open(
            df,
            signals_df,
            take_profit_pips=10.0,
            cost_per_trade_pips=2.0
        )
        
        # Step 4: Verify results
        assert len(result.trades) >= 0
        assert len(result.equity_curve) == len(df)
        
        # Step 5: Analyze results
        from src.backtest_dual_market import analyze_dual_market_results
        analysis = analyze_dual_market_results(result)
        assert isinstance(analysis, dict)
    
    def test_regime_analysis_workflow(self, sample_ohlc_data):
        """Test complete regime analysis workflow."""
        df = sample_ohlc_data.copy()
        
        # Step 1: Calculate daily metrics
        df = calculate_daily_metrics(df)
        
        # Step 2: Calculate moving averages
        df = calculate_moving_averages(df, periods=[50, 200])
        
        # Step 3: Classify regime
        df = classify_regime(df, sma_short=50, sma_long=200)
        
        # Step 4: Analyze performance by regime
        performance = analyze_regime_performance(df)
        
        # Step 5: Verify results
        assert isinstance(performance, pd.DataFrame)
        assert 'regime' in performance.columns
        assert len(performance) > 0
    
    def test_core_analysis_workflow(self, sample_ohlc_data):
        """Test complete core analysis workflow."""
        df = sample_ohlc_data.copy()
        
        # Step 1: Calculate daily metrics
        df = calculate_daily_metrics(df)
        
        # Step 2: Calculate ADR
        df['ADR'] = calculate_adr(df, window=20)
        
        # Step 3: Verify metrics
        assert 'range_pips' in df.columns
        assert 'up_from_open_pips' in df.columns
        assert 'down_from_open_pips' in df.columns
        assert 'ADR' in df.columns
        
        # Step 4: Verify ADR calculation
        assert df['ADR'].notna().sum() > 0  # Should have some ADR values
    
    def test_data_loading_to_backtest_workflow(self, sample_csv_file):
        """Test complete workflow from data loading to backtest."""
        # Step 1: Load data
        df = load_eurusd_data(sample_csv_file)
        
        # Step 2: Add market open prices
        df = add_market_open_prices(df)
        
        # Step 3: Prepare for strategy
        from src.strategies import calculate_sma
        df['SMA20'] = calculate_sma(df, 'Close', window=20)
        
        # Step 4: Generate signals
        signals = strategy_price_trend_directional(df, sma_period=20)
        
        # Step 5: Run backtest
        result = backtest_strategy(
            df,
            signals,
            take_profit_pips=10.0,
            stop_loss_pips=10.0
        )
        
        # Step 6: Verify end-to-end
        assert len(result.trades) >= 0
        assert len(result.equity_curve) == len(df)
    
    def test_no_sl_backtest_workflow(self, sample_ohlc_data):
        """Test complete workflow for no-SL backtest."""
        df = sample_ohlc_data.copy()
        
        # Step 1: Prepare data
        from src.strategies import calculate_sma
        df['SMA20'] = calculate_sma(df, 'Close', window=20)
        
        # Step 2: Generate signals
        signals = strategy_price_trend_directional(df, sma_period=20)
        
        # Step 3: Run no-SL backtest
        result = backtest_strategy_no_sl(
            df,
            signals,
            take_profit_pips=10.0,
            cost_per_trade_pips=2.0
        )
        
        # Step 4: Verify results
        assert len(result.trades) >= 0
        assert len(result.equity_curve) == len(df)
        
        # Step 5: Check that trades have exit_reason
        if len(result.trades) > 0:
            assert 'exit_reason' in result.trades.columns
            assert 'tp_hit' in result.trades.columns



