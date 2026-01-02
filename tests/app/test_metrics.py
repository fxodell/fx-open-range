"""
Tests for app/utils/metrics.py
"""

import pytest
import time
from app.utils.metrics import TradingMetrics, get_metrics


class TestTradingMetrics:
    """Test TradingMetrics class."""
    
    def test_metrics_initialization(self):
        """Test metrics initialization."""
        metrics = TradingMetrics()
        
        assert metrics.trades_executed == 0
        assert metrics.trades_successful == 0
        assert metrics.trades_failed == 0
        assert metrics.api_calls == 0
        assert metrics.api_errors == 0
    
    def test_record_trade_success(self):
        """Test recording successful trade."""
        metrics = TradingMetrics()
        
        metrics.record_trade(success=True, pips=10.0)
        
        assert metrics.trades_executed == 1
        assert metrics.trades_successful == 1
        assert metrics.trades_failed == 0
        assert metrics.total_pips == 10.0
    
    def test_record_trade_failure(self):
        """Test recording failed trade."""
        metrics = TradingMetrics()
        
        metrics.record_trade(success=False, pips=-5.0)
        
        assert metrics.trades_executed == 1
        assert metrics.trades_successful == 0
        assert metrics.trades_failed == 1
        assert metrics.total_pips == -5.0
    
    def test_record_api_call(self):
        """Test recording API call."""
        metrics = TradingMetrics()
        
        metrics.record_api_call(duration_seconds=0.5, error=False)
        
        assert metrics.api_calls == 1
        assert metrics.api_errors == 0
        assert len(metrics.api_call_times) == 1
        assert metrics.api_call_times[0] == 0.5
    
    def test_record_api_call_error(self):
        """Test recording API call error."""
        metrics = TradingMetrics()
        
        metrics.record_api_call(duration_seconds=0.3, error=True)
        
        assert metrics.api_calls == 1
        assert metrics.api_errors == 1
    
    def test_get_summary(self):
        """Test getting metrics summary."""
        metrics = TradingMetrics()
        
        metrics.record_trade(success=True, pips=10.0)
        metrics.record_trade(success=False, pips=-5.0)
        metrics.record_api_call(duration_seconds=0.5, error=False)
        metrics.record_api_call(duration_seconds=0.3, error=True)
        
        summary = metrics.get_summary()
        
        assert summary['trades_executed'] == 2
        assert summary['trades_successful'] == 1
        assert summary['trades_failed'] == 1
        assert summary['win_rate'] == 50.0
        assert summary['total_pips'] == 5.0
        assert summary['api_calls'] == 2
        assert summary['api_errors'] == 1
        assert summary['api_error_rate'] == 50.0
        assert summary['avg_api_latency_seconds'] == 0.4
    
    def test_get_summary_win_rate_calculation(self):
        """Test win rate calculation."""
        metrics = TradingMetrics()
        
        # 3 wins, 1 loss
        metrics.record_trade(success=True, pips=10.0)
        metrics.record_trade(success=True, pips=8.0)
        metrics.record_trade(success=True, pips=12.0)
        metrics.record_trade(success=False, pips=-5.0)
        
        summary = metrics.get_summary()
        
        assert summary['win_rate'] == 75.0
    
    def test_reset(self):
        """Test resetting metrics."""
        metrics = TradingMetrics()
        
        metrics.record_trade(success=True, pips=10.0)
        metrics.record_api_call(duration_seconds=0.5, error=False)
        
        metrics.reset()
        
        assert metrics.trades_executed == 0
        assert metrics.api_calls == 0
    
    def test_get_metrics_singleton(self):
        """Test that get_metrics returns singleton."""
        metrics1 = get_metrics()
        metrics2 = get_metrics()
        
        assert metrics1 is metrics2
    
    def test_log_summary(self, caplog):
        """Test logging metrics summary."""
        import logging
        caplog.set_level(logging.INFO)
        
        metrics = TradingMetrics()
        
        metrics.record_trade(success=True, pips=10.0)
        metrics.log_summary()
        
        # Check that summary was logged
        assert len(caplog.records) > 0
        log_messages = " ".join([record.message for record in caplog.records])
        assert "Trading Metrics Summary" in log_messages or "Trades Executed" in log_messages

