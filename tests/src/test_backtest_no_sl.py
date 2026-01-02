"""
Tests for src/backtest_no_sl.py
"""

import pytest
import pandas as pd
from src.backtest_no_sl import backtest_strategy_no_sl


class TestBacktestNoSL:
    """Test backtest_no_sl functions."""
    
    def test_backtest_strategy_no_sl_tp_hit(self, sample_ohlc_data):
        """Test backtest with TP hit (no stop loss)."""
        df = sample_ohlc_data.copy()
        
        signals = pd.Series('flat', index=df.index)
        signals.iloc[-1] = 'long'
        
        # Modify last row so TP is hit
        last_idx = df.index[-1]
        entry_price = df.loc[last_idx, 'Open']
        tp_price = entry_price + 0.0020  # 20 pips TP
        df.loc[last_idx, 'High'] = tp_price + 0.0001  # TP hit
        
        result = backtest_strategy_no_sl(
            df,
            signals,
            take_profit_pips=20.0,
            cost_per_trade_pips=2.0
        )
        
        assert len(result.trades) == 1
        assert result.trades.iloc[0]['direction'] == 'long'
        assert result.trades.iloc[0]['tp_hit'] == True  # Use == instead of is for numpy bool
        assert result.trades.iloc[0]['exit_reason'] == 'TP'
        assert abs(result.trades.iloc[0]['pips'] - (20.0 - 2.0)) < 0.1  # TP - cost
    
    def test_backtest_strategy_no_sl_eod_exit(self, sample_ohlc_data):
        """Test backtest with EOD exit (no TP hit, no stop loss)."""
        df = sample_ohlc_data.copy()
        
        signals = pd.Series('flat', index=df.index)
        signals.iloc[-1] = 'long'
        
        # Modify last row so TP is NOT hit
        last_idx = df.index[-1]
        entry_price = df.loc[last_idx, 'Open']
        tp_price = entry_price + 0.0020
        df.loc[last_idx, 'High'] = entry_price + 0.0010  # Below TP
        df.loc[last_idx, 'Close'] = entry_price + 0.0005  # Small profit
        
        result = backtest_strategy_no_sl(
            df,
            signals,
            take_profit_pips=20.0,
            cost_per_trade_pips=2.0
        )
        
        assert len(result.trades) == 1
        assert result.trades.iloc[0]['tp_hit'] == False  # Use == instead of is for numpy bool
        assert result.trades.iloc[0]['exit_reason'] == 'EOD'
        # Should exit at close price
        expected_pips = (df.loc[last_idx, 'Close'] - entry_price) * 10000 - 2.0
        assert abs(result.trades.iloc[0]['pips'] - expected_pips) < 0.1
    
    def test_backtest_strategy_no_sl_short_signal(self, sample_ohlc_data):
        """Test backtest with short signal (no stop loss)."""
        df = sample_ohlc_data.copy()
        
        signals = pd.Series('flat', index=df.index)
        signals.iloc[-1] = 'short'
        
        # Modify last row so TP is hit for short
        last_idx = df.index[-1]
        entry_price = df.loc[last_idx, 'Open']
        tp_price = entry_price - 0.0020  # 20 pips TP for short
        df.loc[last_idx, 'Low'] = tp_price - 0.0001  # TP hit
        
        result = backtest_strategy_no_sl(
            df,
            signals,
            take_profit_pips=20.0,
            cost_per_trade_pips=2.0
        )
        
        assert len(result.trades) == 1
        assert result.trades.iloc[0]['direction'] == 'short'
        assert result.trades.iloc[0]['tp_hit'] == True  # Use == instead of is for numpy bool
        assert result.trades.iloc[0]['exit_reason'] == 'TP'
        assert abs(result.trades.iloc[0]['pips'] - (20.0 - 2.0)) < 0.1
    
    def test_backtest_strategy_no_sl_transaction_cost(self, sample_ohlc_data):
        """Test that transaction costs are applied."""
        df = sample_ohlc_data.copy()
        
        signals = pd.Series('flat', index=df.index)
        signals.iloc[-1] = 'long'
        
        last_idx = df.index[-1]
        entry_price = df.loc[last_idx, 'Open']
        tp_price = entry_price + 0.0020
        df.loc[last_idx, 'High'] = tp_price + 0.0001
        
        result = backtest_strategy_no_sl(
            df,
            signals,
            take_profit_pips=20.0,
            cost_per_trade_pips=5.0  # Higher cost
        )
        
        assert len(result.trades) == 1
        # Should have TP - cost
        assert abs(result.trades.iloc[0]['pips'] - (20.0 - 5.0)) < 0.1
    
    def test_backtest_strategy_no_sl_all_flat(self, sample_ohlc_data):
        """Test backtest with all flat signals (no trades)."""
        df = sample_ohlc_data.copy()
        
        signals = pd.Series('flat', index=df.index)
        
        result = backtest_strategy_no_sl(
            df,
            signals,
            take_profit_pips=20.0
        )
        
        assert len(result.trades) == 0

