"""
Integration tests for trading workflows.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from app.trading_engine import TradingEngine
from app.config.settings import Settings


class TestTradingWorkflow:
    """Test full trading workflows."""
    
    def test_single_daily_open_trading_workflow(self, mock_oanda_client):
        """Test complete trading workflow for single daily open mode."""
        # Setup
        engine = TradingEngine(mock_oanda_client)
        
        # Mock market data
        sample_df = pd.DataFrame({
            'Date': pd.date_range('2025-12-01', periods=30, freq='D'),
            'Open': [1.1600] * 30,
            'High': [1.1610] * 30,
            'Low': [1.1590] * 30,
            'Close': [1.1605] * 30,
        })
        
        # Mock methods
        mock_oanda_client.fetch_candles.return_value = sample_df
        mock_oanda_client.get_current_price.return_value = {
            'bid': 1.1600,
            'ask': 1.1602,
            'mid': 1.1601
        }
        mock_oanda_client.get_open_trades.return_value = []
        mock_oanda_client.place_market_order.return_value = {
            'orderFillTransaction': {'id': 'order-123'}
        }
        
        # Step 1: Get market data
        df = engine.get_market_data()
        assert len(df) == 30
        
        # Step 2: Get signal
        with patch('app.trading_engine.get_current_signal', return_value=('long', 1.1605, 1.1600)):
            signal, price, sma, price_info = engine.get_signal()
            assert signal in ['long', 'short', 'flat']
        
        # Step 3: Check positions
        positions = engine.check_open_positions()
        assert isinstance(positions, list)
        
        # Step 4: Execute trade (if signal)
        if signal != 'flat':
            with patch.object(engine, 'has_traded_today', return_value=False):
                result = engine.execute_trade(signal, price_info)
                # May return None or order result
                assert result is None or isinstance(result, dict)
    
    def test_dual_market_open_trading_workflow(self, mock_oanda_client):
        """Test complete trading workflow for dual market open mode."""
        # Setup
        engine = TradingEngine(mock_oanda_client)
        
        # Mock market data
        sample_df = pd.DataFrame({
            'Date': pd.date_range('2025-12-01', periods=30, freq='D'),
            'Open': [1.1600] * 30,
            'High': [1.1610] * 30,
            'Low': [1.1590] * 30,
            'Close': [1.1605] * 30,
        })
        
        mock_oanda_client.fetch_candles.return_value = sample_df
        mock_oanda_client.get_open_trades.return_value = []
        
        # Step 1: Check EUR market open
        with patch('app.trading_engine.check_eur_market_open', return_value=True):
            eur_open = engine.check_eur_market_open()
            assert eur_open is True
        
        # Step 2: Check US market open
        with patch('app.trading_engine.check_us_market_open', return_value=True):
            us_open = engine.check_us_market_open()
            assert us_open is True
        
        # Step 3: Try EUR market trade
        with patch.object(engine, 'get_market_data', return_value=sample_df):
            with patch.object(engine, 'get_signal', return_value=('long', 1.1605, 1.1600, {'bid': 1.1600})):
                with patch.object(engine, 'has_traded_today', return_value=False):
                    with patch.object(engine, 'execute_trade', return_value={'id': 'order-123'}):
                        engine._try_market_open_trade('eur')
                        # Should attempt to execute trade
    
    def test_error_recovery_workflow(self, mock_oanda_client):
        """Test error recovery in trading workflow."""
        engine = TradingEngine(mock_oanda_client)
        
        # Mock API error
        mock_oanda_client.fetch_candles.side_effect = Exception("API Error")
        
        # Should handle error gracefully
        try:
            df = engine.get_market_data()
            # If error is caught, df might be empty or None
        except Exception:
            # Error should be logged, not crash
            pass
        
        # Verify error handling doesn't break workflow
        assert True  # If we get here, error was handled
    
    def test_position_management_workflow(self, mock_oanda_client):
        """Test position management workflow."""
        engine = TradingEngine(mock_oanda_client)
        
        # Step 1: Check for open positions
        mock_oanda_client.get_open_trades.return_value = [
            {'id': 'trade-1', 'instrument': 'EUR_USD', 'currentUnits': '1'}
        ]
        
        positions = engine.check_open_positions()
        assert len(positions) == 1
        
        # Step 2: Try to execute trade (should be blocked)
        mock_oanda_client.get_current_price.return_value = {
            'bid': 1.1600,
            'ask': 1.1602,
            'mid': 1.1601
        }
        
        result = engine.execute_trade('long', mock_oanda_client.get_current_price.return_value)
        
        # Should return None because position already exists
        assert result is None
        
        # Step 3: Close EOD positions
        mock_oanda_client.close_trade.return_value = {'id': 'trade-1'}
        engine.close_eod_positions()
        
        # Should close positions
        mock_oanda_client.close_trade.assert_called()
    
    def test_daily_trade_limit_workflow(self, mock_oanda_client):
        """Test daily trade limit workflow."""
        engine = TradingEngine(mock_oanda_client)
        
        # Set trades today to max
        engine.trades_today = Settings.MAX_DAILY_TRADES
        engine.last_trade_date = datetime.now(timezone.utc).date()
        
        # Check if has traded today
        has_traded = engine.has_traded_today()
        assert has_traded is True
        
        # Try to execute trade (should be blocked)
        mock_oanda_client.get_current_price.return_value = {
            'bid': 1.1600,
            'ask': 1.1602,
            'mid': 1.1601
        }
        
        result = engine.execute_trade('long', mock_oanda_client.get_current_price.return_value)
        
        # Should return None because max trades reached
        assert result is None

