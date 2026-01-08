"""
Metrics tracking for trading operations.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Optional
from collections import defaultdict
from threading import Lock

logger = logging.getLogger(__name__)


class TradingMetrics:
    """Tracks trading metrics and statistics."""
    
    def __init__(self):
        """Initialize metrics tracker."""
        self._lock = Lock()
        self.reset()
    
    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self.trades_executed = 0
            self.trades_successful = 0
            self.trades_failed = 0
            self.api_calls = 0
            self.api_errors = 0
            self.total_pips = 0.0
            self.daily_pnl = 0.0
            self.last_reset_date = datetime.now(timezone.utc).date()
            self.api_call_times = []  # Track latencies
            self.trade_history = []  # Track trade details
    
    def record_trade(self, success: bool, pips: Optional[float] = None) -> None:
        """
        Record a trade execution.
        
        Parameters:
        -----------
        success : bool
            Whether trade was successful
        pips : float, optional
            Pips gained/lost from trade
        """
        with self._lock:
            self.trades_executed += 1
            if success:
                self.trades_successful += 1
            else:
                self.trades_failed += 1
            
            if pips is not None:
                self.total_pips += pips
                self.daily_pnl += pips
                self.trade_history.append({
                    'timestamp': datetime.now(timezone.utc),
                    'success': success,
                    'pips': pips
                })
    
    def record_api_call(self, duration_seconds: Optional[float] = None, error: bool = False) -> None:
        """
        Record an API call.
        
        Parameters:
        -----------
        duration_seconds : float, optional
            Duration of API call in seconds
        error : bool
            Whether the API call resulted in an error
        """
        with self._lock:
            self.api_calls += 1
            if error:
                self.api_errors += 1
            if duration_seconds is not None:
                self.api_call_times.append(duration_seconds)
    
    def get_summary(self) -> Dict:
        """
        Get metrics summary.
        
        Returns:
        --------
        dict
            Dictionary with current metrics
        """
        with self._lock:
            # Check if we need to reset daily metrics
            today = datetime.now(timezone.utc).date()
            if self.last_reset_date != today:
                self.daily_pnl = 0.0
                self.last_reset_date = today
            
            avg_api_latency = (
                sum(self.api_call_times) / len(self.api_call_times)
                if self.api_call_times else 0.0
            )
            
            win_rate = (
                (self.trades_successful / self.trades_executed * 100)
                if self.trades_executed > 0 else 0.0
            )
            
            return {
                'trades_executed': self.trades_executed,
                'trades_successful': self.trades_successful,
                'trades_failed': self.trades_failed,
                'win_rate': win_rate,
                'total_pips': self.total_pips,
                'daily_pnl': self.daily_pnl,
                'api_calls': self.api_calls,
                'api_errors': self.api_errors,
                'api_error_rate': (
                    (self.api_errors / self.api_calls * 100)
                    if self.api_calls > 0 else 0.0
                ),
                'avg_api_latency_seconds': avg_api_latency,
            }
    
    def log_summary(self) -> None:
        """Log metrics summary."""
        summary = self.get_summary()
        logger.info("Trading Metrics Summary:")
        logger.info(f"  Trades Executed: {summary['trades_executed']}")
        logger.info(f"  Win Rate: {summary['win_rate']:.2f}%")
        logger.info(f"  Total Pips: {summary['total_pips']:.2f}")
        logger.info(f"  Daily P/L: {summary['daily_pnl']:.2f} pips")
        logger.info(f"  API Calls: {summary['api_calls']}")
        logger.info(f"  API Error Rate: {summary['api_error_rate']:.2f}%")
        logger.info(f"  Avg API Latency: {summary['avg_api_latency_seconds']:.3f}s")


# Global metrics instance
_metrics_instance: Optional[TradingMetrics] = None


def get_metrics() -> TradingMetrics:
    """Get global metrics instance."""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = TradingMetrics()
    return _metrics_instance





