"""
Tests for src/backtest.py
"""

import pytest
import pandas as pd
import numpy as np
from src.backtest import backtest_strategy, BacktestResult


class TestBacktestResult:
    """Test BacktestResult class."""
    
    def test_backtest_result_initialization(self):
        """Test BacktestResult initialization."""
        trades = pd.DataFrame({
            'date': [pd.Timestamp('2025-12-01')],
            'direction': ['long'],
            'entry_price': [1.1600],
            'exit_price': [1.1610],
            'pips': [8.0],
        })
        equity_curve = pd.Series([10000.0, 10080.0])
        
        result = BacktestResult(trades, equity_curve)
        
        assert isinstance(result.trades, pd.DataFrame)
        assert isinstance(result.equity_curve, pd.Series)
        assert len(result.trades) == 1
        assert len(result.equity_curve) == 2
    
    def test_get_summary_stats_with_trades(self):
        """Test get_summary_stats with trades."""
        trades = pd.DataFrame({
            'date': pd.date_range('2025-12-01', periods=10, freq='D'),
            'direction': ['long'] * 7 + ['short'] * 3,
            'entry_price': [1.1600] * 10,
            'exit_price': [1.1610] * 10,
            'pips': [8.0] * 8 + [-5.0] * 2,  # 8 wins, 2 losses
        })
        equity_curve = pd.Series([10000.0 + i * 10 for i in range(11)])
        
        result = BacktestResult(trades, equity_curve)
        stats = result.get_summary_stats()
        
        assert stats['total_trades'] == 10
        assert stats['long_trades'] == 7
        assert stats['short_trades'] == 3
        assert stats['total_pips'] == (8.0 * 8) + (-5.0 * 2)  # 64 - 10 = 54
        assert stats['win_rate'] == 80.0  # 8 wins out of 10
        assert stats['avg_win'] == 8.0
        assert stats['avg_loss'] == -5.0
    
    def test_get_summary_stats_no_trades(self):
        """Test get_summary_stats with no trades."""
        trades = pd.DataFrame(columns=['date', 'direction', 'entry_price', 'exit_price', 'pips'])
        equity_curve = pd.Series([10000.0] * 10)
        
        result = BacktestResult(trades, equity_curve)
        stats = result.get_summary_stats()
        
        assert stats['total_trades'] == 0
        assert stats['total_pips'] == 0.0
        assert stats['win_rate'] == 0.0
        assert stats['max_drawdown_pips'] >= 0.0  # Should still calculate drawdown
    
    def test_get_summary_stats_profit_factor(self):
        """Test profit factor calculation."""
        trades = pd.DataFrame({
            'date': pd.date_range('2025-12-01', periods=10, freq='D'),
            'direction': ['long'] * 10,
            'entry_price': [1.1600] * 10,
            'exit_price': [1.1610] * 10,
            'pips': [10.0] * 5 + [-5.0] * 5,  # 5 wins, 5 losses
        })
        equity_curve = pd.Series([10000.0 + i * 5 for i in range(11)])
        
        result = BacktestResult(trades, equity_curve)
        stats = result.get_summary_stats()
        
        # Profit factor = gross profit / gross loss = (10*5) / (5*5) = 50/25 = 2.0
        expected_pf = (10.0 * 5) / abs(-5.0 * 5)
        assert abs(stats['profit_factor'] - expected_pf) < 0.01
    
    def test_print_summary(self, capsys):
        """Test print_summary output."""
        trades = pd.DataFrame({
            'date': [pd.Timestamp('2025-12-01')],
            'direction': ['long'],
            'entry_price': [1.1600],
            'exit_price': [1.1610],
            'pips': [8.0],
        })
        equity_curve = pd.Series([10000.0, 10080.0])
        
        result = BacktestResult(trades, equity_curve)
        result.print_summary()
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "BACKTEST SUMMARY" in output
        assert "Total Trades" in output
        assert "Total Pips" in output
        assert "Win Rate" in output


class TestBacktestStrategy:
    """Test backtest_strategy function."""
    
    def test_backtest_strategy_long_signal_tp_hit(self, sample_ohlc_data):
        """Test backtest with long signal that hits TP."""
        # Create a copy to avoid modifying the fixture
        df = sample_ohlc_data.copy()
        
        # Create signal: long on last day
        signals = pd.Series('flat', index=df.index)
        signals.iloc[-1] = 'long'
        
        # Modify last row so TP is hit (High >= entry + TP)
        # IMPORTANT: Must ensure Low is above SL so SL is NOT hit first
        last_idx = df.index[-1]
        entry_price = df.loc[last_idx, 'Open']
        tp_price = entry_price + 0.0020  # 20 pips TP
        sl_price = entry_price - 0.0020  # 20 pips SL
        
        # Set High to hit TP, but Low must stay above SL
        df.loc[last_idx, 'High'] = tp_price + 0.0001  # TP hit
        df.loc[last_idx, 'Low'] = entry_price - 0.0010  # Above SL (so SL not hit)
        
        result = backtest_strategy(
            df,
            signals,
            take_profit_pips=20.0,
            stop_loss_pips=20.0,
            cost_per_trade_pips=2.0
        )
        
        assert len(result.trades) == 1
        assert result.trades.iloc[0]['direction'] == 'long'
        # Should have profit (TP hit - cost)
        assert abs(result.trades.iloc[0]['pips'] - (20.0 - 2.0)) < 0.1  # TP - cost
    
    def test_backtest_strategy_long_signal_sl_hit(self, sample_ohlc_data):
        """Test backtest with long signal that hits SL."""
        # Create a copy to avoid modifying the fixture
        df = sample_ohlc_data.copy()
        
        signals = pd.Series('flat', index=df.index)
        signals.iloc[-1] = 'long'
        
        # Modify last row so SL is hit (Low <= entry - SL)
        last_idx = df.index[-1]
        entry_price = df.loc[last_idx, 'Open']
        sl_price = entry_price - 0.0020  # 20 pips SL
        df.loc[last_idx, 'Low'] = sl_price - 0.0001  # SL hit
        # Ensure High doesn't hit TP (so SL is hit first)
        df.loc[last_idx, 'High'] = entry_price + 0.0010  # Below TP
        
        result = backtest_strategy(
            df,
            signals,
            take_profit_pips=20.0,
            stop_loss_pips=20.0,
            cost_per_trade_pips=2.0
        )
        
        assert len(result.trades) == 1
        # Should have loss (SL hit + cost)
        assert abs(result.trades.iloc[0]['pips'] - (-20.0 - 2.0)) < 0.1  # -SL - cost
    
    def test_backtest_strategy_eod_exit(self, sample_ohlc_data):
        """Test backtest with EOD exit (neither TP nor SL hit)."""
        # Create a copy to avoid modifying the fixture
        df = sample_ohlc_data.copy()
        
        signals = pd.Series('flat', index=df.index)
        signals.iloc[-1] = 'long'
        
        # Modify last row so neither TP nor SL is hit
        last_idx = df.index[-1]
        entry_price = df.loc[last_idx, 'Open']
        tp_price = entry_price + 0.0020
        sl_price = entry_price - 0.0020
        # Set High/Low so neither TP nor SL is hit
        df.loc[last_idx, 'High'] = entry_price + 0.0010  # Below TP
        df.loc[last_idx, 'Low'] = entry_price - 0.0010  # Above SL
        df.loc[last_idx, 'Close'] = entry_price + 0.0005  # Small profit
        
        result = backtest_strategy(
            df,
            signals,
            take_profit_pips=20.0,
            stop_loss_pips=20.0,
            cost_per_trade_pips=2.0
        )
        
        assert len(result.trades) == 1
        # Should exit at close price (Close - Open - cost)
        expected_pips = (df.loc[last_idx, 'Close'] - entry_price) * 10000 - 2.0
        assert abs(result.trades.iloc[0]['pips'] - expected_pips) < 0.1
    
    def test_backtest_strategy_short_signal(self, sample_ohlc_data):
        """Test backtest with short signal."""
        # Create a copy to avoid modifying the fixture
        df = sample_ohlc_data.copy()
        
        signals = pd.Series('flat', index=df.index)
        signals.iloc[-1] = 'short'
        
        # Modify last row so TP is hit for short
        # IMPORTANT: Must ensure High is below SL so SL is NOT hit first
        last_idx = df.index[-1]
        entry_price = df.loc[last_idx, 'Open']
        tp_price = entry_price - 0.0020  # 20 pips TP for short
        sl_price = entry_price + 0.0020  # 20 pips SL for short
        
        df.loc[last_idx, 'Low'] = tp_price - 0.0001  # TP hit
        df.loc[last_idx, 'High'] = entry_price + 0.0010  # Below SL (so SL not hit)
        
        result = backtest_strategy(
            df,
            signals,
            take_profit_pips=20.0,
            stop_loss_pips=20.0,
            cost_per_trade_pips=2.0
        )
        
        assert len(result.trades) == 1
        assert result.trades.iloc[0]['direction'] == 'short'
        assert abs(result.trades.iloc[0]['pips'] - (20.0 - 2.0)) < 0.1  # TP - cost
    
    def test_backtest_strategy_conservative_sl_first(self, sample_ohlc_data):
        """Test conservative assumption: SL hit first if both TP and SL possible."""
        # Create a copy to avoid modifying the fixture
        df = sample_ohlc_data.copy()
        
        signals = pd.Series('flat', index=df.index)
        signals.iloc[-1] = 'long'
        
        # Modify last row so BOTH TP and SL could be hit
        last_idx = df.index[-1]
        entry_price = df.loc[last_idx, 'Open']
        tp_price = entry_price + 0.0020
        sl_price = entry_price - 0.0020
        # Set High >= TP and Low <= SL (both possible)
        df.loc[last_idx, 'High'] = tp_price + 0.0001
        df.loc[last_idx, 'Low'] = sl_price - 0.0001
        
        result = backtest_strategy(
            df,
            signals,
            take_profit_pips=20.0,
            stop_loss_pips=20.0,
            cost_per_trade_pips=2.0
        )
        
        assert len(result.trades) == 1
        # Conservative: SL should be hit first
        assert abs(result.trades.iloc[0]['pips'] - (-20.0 - 2.0)) < 0.1  # -SL - cost
    
    def test_backtest_strategy_transaction_cost(self, sample_ohlc_data):
        """Test that transaction costs are applied."""
        # Create a copy to avoid modifying the fixture
        df = sample_ohlc_data.copy()
        
        signals = pd.Series('flat', index=df.index)
        signals.iloc[-1] = 'long'
        
        last_idx = df.index[-1]
        entry_price = df.loc[last_idx, 'Open']
        tp_price = entry_price + 0.0020
        sl_price = entry_price - 0.0020
        df.loc[last_idx, 'High'] = tp_price + 0.0001  # TP hit
        df.loc[last_idx, 'Low'] = entry_price - 0.0010  # Above SL (so SL not hit)
        
        result = backtest_strategy(
            df,
            signals,
            take_profit_pips=20.0,
            stop_loss_pips=20.0,
            cost_per_trade_pips=5.0  # Higher cost
        )
        
        assert len(result.trades) == 1
        # Should have TP - cost
        assert abs(result.trades.iloc[0]['pips'] - (20.0 - 5.0)) < 0.1
    
    def test_backtest_strategy_equity_curve(self, sample_ohlc_data):
        """Test that equity curve is calculated."""
        # Create a copy to avoid modifying the fixture
        df = sample_ohlc_data.copy()
        
        signals = pd.Series('flat', index=df.index)
        signals.iloc[-1] = 'long'
        
        last_idx = df.index[-1]
        entry_price = df.loc[last_idx, 'Open']
        tp_price = entry_price + 0.0020
        sl_price = entry_price - 0.0020
        df.loc[last_idx, 'High'] = tp_price + 0.0001  # TP hit
        df.loc[last_idx, 'Low'] = entry_price - 0.0010  # Above SL (so SL not hit)
        
        result = backtest_strategy(
            df,
            signals,
            take_profit_pips=20.0,
            stop_loss_pips=20.0,
            initial_equity=10000.0
        )
        
        assert len(result.equity_curve) == len(df)
        # Equity should start at initial_equity
        assert result.equity_curve.iloc[0] == 10000.0
        # Equity should increase after winning trade
        assert result.equity_curve.iloc[-1] > result.equity_curve.iloc[0]
    
    def test_backtest_strategy_all_flat_signals(self, sample_ohlc_data):
        """Test backtest with all flat signals (no trades)."""
        # Create a copy to avoid modifying the fixture
        df = sample_ohlc_data.copy()
        
        signals = pd.Series('flat', index=df.index)
        
        result = backtest_strategy(
            df,
            signals,
            take_profit_pips=20.0,
            stop_loss_pips=20.0
        )
        
        assert len(result.trades) == 0
        assert len(result.equity_curve) == len(df)
        # Equity should remain constant
        assert (result.equity_curve == 10000.0).all()

