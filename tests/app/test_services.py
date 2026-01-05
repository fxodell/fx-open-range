"""
Tests for app/services/ modules
"""

import pytest
import pandas as pd
from unittest.mock import Mock
from app.services.market_data_service import MarketDataService
from app.services.signal_service import SignalService
from app.services.position_manager import PositionManager


class TestMarketDataService:
    """Test MarketDataService."""
    
    def test_service_initialization(self, mock_oanda_client):
        """Test service initialization."""
        service = MarketDataService(mock_oanda_client)
        
        assert service.client == mock_oanda_client
        assert service.instrument == "EUR_USD"
    
    def test_fetch_market_data(self, mock_oanda_client):
        """Test fetching market data."""
        service = MarketDataService(mock_oanda_client)
        
        sample_df = pd.DataFrame({
            'Date': pd.date_range('2025-12-01', periods=30, freq='D'),
            'Open': [1.1600] * 30,
            'High': [1.1610] * 30,
            'Low': [1.1590] * 30,
            'Close': [1.1605] * 30,
        })
        mock_oanda_client.fetch_candles.return_value = sample_df
        
        df = service.fetch_market_data(days=30)
        
        assert len(df) == 30
        mock_oanda_client.fetch_candles.assert_called_once()
    
    def test_prepare_data_for_strategy(self, mock_oanda_client):
        """Test preparing data for strategy."""
        service = MarketDataService(mock_oanda_client)
        
        sample_df = pd.DataFrame({
            'Date': pd.date_range('2025-12-01', periods=30, freq='D'),
            'Open': [1.1600] * 30,
            'High': [1.1610] * 30,
            'Low': [1.1590] * 30,
            'Close': [1.1605] * 30,
        })
        
        df = service.prepare_data_for_strategy(sample_df, sma_period=20)
        
        assert 'SMA20' in df.columns
        assert len(df) == 30
    
    def test_get_data_with_sma(self, mock_oanda_client):
        """Test getting data with SMA calculated."""
        service = MarketDataService(mock_oanda_client)
        
        sample_df = pd.DataFrame({
            'Date': pd.date_range('2025-12-01', periods=30, freq='D'),
            'Open': [1.1600] * 30,
            'High': [1.1610] * 30,
            'Low': [1.1590] * 30,
            'Close': [1.1605] * 30,
        })
        mock_oanda_client.fetch_candles.return_value = sample_df
        
        df = service.get_data_with_sma(days=30, sma_period=20)
        
        assert 'SMA20' in df.columns
        assert len(df) == 30


class TestSignalService:
    """Test SignalService."""
    
    def test_get_signal(self, sample_ohlc_data_with_sma):
        """Test getting signal."""
        service = SignalService()
        
        signal, price, sma = service.get_signal(sample_ohlc_data_with_sma, sma_period=20)
        
        assert signal in ['long', 'short', 'flat']
        assert price is not None or signal == 'flat'
        assert sma is not None or signal == 'flat'
    
    def test_get_dual_market_signals(self, sample_ohlc_data_with_opens):
        """Test getting dual market signals."""
        service = SignalService()
        
        signals = service.get_dual_market_signals(sample_ohlc_data_with_opens, sma_period=20)
        
        assert isinstance(signals, dict)
        assert 'eur' in signals
        assert 'us' in signals
    
    def test_get_market_open_signal(self, sample_ohlc_data):
        """Test getting market open signal."""
        service = SignalService()
        
        signal, price, sma = service.get_market_open_signal(sample_ohlc_data, 'eur', sma_period=20)
        
        assert signal in ['long', 'short', 'flat']
        assert price is not None or signal == 'flat'
        assert sma is not None or signal == 'flat'


class TestPositionManager:
    """Test PositionManager."""
    
    def test_manager_initialization(self, mock_oanda_client):
        """Test manager initialization."""
        manager = PositionManager(mock_oanda_client)
        
        assert manager.client == mock_oanda_client
        assert manager.instrument == "EUR_USD"
    
    def test_get_open_positions(self, mock_oanda_client):
        """Test getting open positions."""
        manager = PositionManager(mock_oanda_client)
        
        mock_oanda_client.get_open_trades.return_value = [
            {'id': 'trade-1', 'instrument': 'EUR_USD'},
            {'id': 'trade-2', 'instrument': 'GBP_USD'},  # Different instrument
        ]
        
        positions = manager.get_open_positions()
        
        # Should only return EUR_USD positions
        assert len(positions) == 1
        assert positions[0]['instrument'] == 'EUR_USD'
    
    def test_has_open_position(self, mock_oanda_client):
        """Test checking for open position."""
        manager = PositionManager(mock_oanda_client)
        
        mock_oanda_client.get_open_trades.return_value = [
            {'id': 'trade-1', 'instrument': 'EUR_USD'},
        ]
        
        assert manager.has_open_position() is True
        
        mock_oanda_client.get_open_trades.return_value = []
        
        assert manager.has_open_position() is False
    
    def test_close_all_positions(self, mock_oanda_client):
        """Test closing all positions."""
        manager = PositionManager(mock_oanda_client)
        
        mock_oanda_client.get_open_trades.return_value = [
            {'id': 'trade-1', 'instrument': 'EUR_USD'},
            {'id': 'trade-2', 'instrument': 'EUR_USD'},
        ]
        mock_oanda_client.close_trade.return_value = {'id': 'trade-1'}
        
        closed_count = manager.close_all_positions()
        
        assert closed_count == 2
        assert mock_oanda_client.close_trade.call_count == 2
    
    def test_validate_position_size(self, mock_oanda_client):
        """Test position size validation."""
        manager = PositionManager(mock_oanda_client)
        
        # Test valid position size
        assert manager.validate_position_size(1000) is True
        
        # Test with max limit (if set)
        from app.config.settings import Settings
        original_max = getattr(Settings, 'MAX_POSITION_SIZE', None)
        Settings.MAX_POSITION_SIZE = 500
        
        assert manager.validate_position_size(1000) is False
        assert manager.validate_position_size(100) is True
        
        # Restore
        Settings.MAX_POSITION_SIZE = original_max
    
    def test_get_position_count(self, mock_oanda_client):
        """Test getting position count."""
        manager = PositionManager(mock_oanda_client)
        
        mock_oanda_client.get_open_trades.return_value = [
            {'id': 'trade-1', 'instrument': 'EUR_USD'},
            {'id': 'trade-2', 'instrument': 'EUR_USD'},
        ]
        
        assert manager.get_position_count() == 2



