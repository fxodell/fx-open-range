"""
Error handling tests for app/utils/oanda_client.py
"""

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from app.utils.oanda_client import OandaTradingClient


class TestOandaClientErrors:
    """Test error handling in OandaTradingClient."""
    
    def test_fetch_candles_400_error(self):
        """Test handling of 400 Bad Request error."""
        with patch('app.utils.oanda_client.requests.get') as mock_get:
            # Mock account ID fetch
            mock_get.return_value.json.return_value = {
                'accounts': [{'id': 'test-account-123'}]
            }
            mock_get.return_value.raise_for_status = Mock()
            
            client = OandaTradingClient(
                api_token="test-token",
                account_id="test-account-123",
                practice=True
            )
            
            # Mock 400 error
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
                "400 Client Error: Bad Request"
            )
            mock_get.return_value = mock_response
            
            # Should raise HTTPError
            with pytest.raises(requests.exceptions.HTTPError):
                client.fetch_candles(
                    instrument="EUR_USD",
                    granularity="D",
                    count=30
                )
    
    def test_fetch_candles_401_error(self):
        """Test handling of 401 Unauthorized error."""
        with patch('app.utils.oanda_client.requests.get') as mock_get:
            mock_get.return_value.json.return_value = {
                'accounts': [{'id': 'test-account-123'}]
            }
            mock_get.return_value.raise_for_status = Mock()
            
            client = OandaTradingClient(
                api_token="test-token",
                account_id="test-account-123",
                practice=True
            )
            
            # Mock 401 error
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
                "401 Client Error: Unauthorized"
            )
            mock_get.return_value = mock_response
            
            with pytest.raises(requests.exceptions.HTTPError):
                client.fetch_candles(
                    instrument="EUR_USD",
                    granularity="D",
                    count=30
                )
    
    def test_fetch_candles_403_error(self):
        """Test handling of 403 Forbidden error."""
        with patch('app.utils.oanda_client.requests.get') as mock_get:
            mock_get.return_value.json.return_value = {
                'accounts': [{'id': 'test-account-123'}]
            }
            mock_get.return_value.raise_for_status = Mock()
            
            client = OandaTradingClient(
                api_token="test-token",
                account_id="test-account-123",
                practice=True
            )
            
            # Mock 403 error
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
                "403 Client Error: Forbidden"
            )
            mock_get.return_value = mock_response
            
            with pytest.raises(requests.exceptions.HTTPError):
                client.fetch_candles(
                    instrument="EUR_USD",
                    granularity="D",
                    count=30
                )
    
    def test_fetch_candles_500_error(self):
        """Test handling of 500 Internal Server Error."""
        with patch('app.utils.oanda_client.requests.get') as mock_get:
            mock_get.return_value.json.return_value = {
                'accounts': [{'id': 'test-account-123'}]
            }
            mock_get.return_value.raise_for_status = Mock()
            
            client = OandaTradingClient(
                api_token="test-token",
                account_id="test-account-123",
                practice=True
            )
            
            # Mock 500 error
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
                "500 Server Error: Internal Server Error"
            )
            mock_get.return_value = mock_response
            
            with pytest.raises(requests.exceptions.HTTPError):
                client.fetch_candles(
                    instrument="EUR_USD",
                    granularity="D",
                    count=30
                )
    
    def test_fetch_candles_connection_error(self):
        """Test handling of connection errors."""
        with patch('app.utils.oanda_client.requests.get') as mock_get:
            mock_get.return_value.json.return_value = {
                'accounts': [{'id': 'test-account-123'}]
            }
            mock_get.return_value.raise_for_status = Mock()
            
            client = OandaTradingClient(
                api_token="test-token",
                account_id="test-account-123",
                practice=True
            )
            
            # Mock connection error
            mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
            
            with pytest.raises(requests.exceptions.ConnectionError):
                client.fetch_candles(
                    instrument="EUR_USD",
                    granularity="D",
                    count=30
                )
    
    def test_fetch_candles_timeout(self):
        """Test handling of timeout errors."""
        with patch('app.utils.oanda_client.requests.get') as mock_get:
            mock_get.return_value.json.return_value = {
                'accounts': [{'id': 'test-account-123'}]
            }
            mock_get.return_value.raise_for_status = Mock()
            
            client = OandaTradingClient(
                api_token="test-token",
                account_id="test-account-123",
                practice=True
            )
            
            # Mock timeout
            mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
            
            with pytest.raises(requests.exceptions.Timeout):
                client.fetch_candles(
                    instrument="EUR_USD",
                    granularity="D",
                    count=30
                )
    
    def test_fetch_candles_invalid_response_format(self):
        """Test handling of invalid response format."""
        with patch('app.utils.oanda_client.requests.get') as mock_get:
            mock_get.return_value.json.return_value = {
                'accounts': [{'id': 'test-account-123'}]
            }
            mock_get.return_value.raise_for_status = Mock()
            
            client = OandaTradingClient(
                api_token="test-token",
                account_id="test-account-123",
                practice=True
            )
            
            # Mock invalid JSON response
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_get.return_value = mock_response
            
            # Should raise ValueError
            with pytest.raises(ValueError):
                client.fetch_candles(
                    instrument="EUR_USD",
                    granularity="D",
                    count=30
                )
    
    def test_get_account_id_auto_detection_failure(self):
        """Test account ID auto-detection failure."""
        with patch('app.utils.oanda_client.requests.get') as mock_get:
            # Mock empty accounts list
            mock_get.return_value.json.return_value = {
                'accounts': []
            }
            mock_get.return_value.raise_for_status = Mock()
            
            # Should raise ValueError
            with pytest.raises(ValueError, match="No accounts found"):
                OandaTradingClient(
                    api_token="test-token",
                    account_id=None,
                    practice=True
                )
    
    def test_get_account_id_api_error(self):
        """Test account ID auto-detection with API error."""
        with patch('app.utils.oanda_client.requests.get') as mock_get:
            # Mock API error
            mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError(
                "401 Unauthorized"
            )
            
            # Should raise HTTPError
            with pytest.raises(requests.exceptions.HTTPError):
                OandaTradingClient(
                    api_token="test-token",
                    account_id=None,
                    practice=True
                )
    
    def test_place_market_order_error(self, mock_oanda_client):
        """Test place_market_order error handling."""
        mock_oanda_client.place_market_order.side_effect = requests.exceptions.HTTPError(
            "400 Bad Request"
        )
        
        with pytest.raises(requests.exceptions.HTTPError):
            mock_oanda_client.place_market_order(
                instrument="EUR_USD",
                units=1,
                take_profit_pips=10.0
            )
    
    def test_get_current_price_error(self, mock_oanda_client):
        """Test get_current_price error handling."""
        mock_oanda_client.get_current_price.side_effect = requests.exceptions.HTTPError(
            "500 Server Error"
        )
        
        with pytest.raises(requests.exceptions.HTTPError):
            mock_oanda_client.get_current_price("EUR_USD")
    
    def test_close_trade_error(self, mock_oanda_client):
        """Test close_trade error handling."""
        mock_oanda_client.close_trade.side_effect = requests.exceptions.HTTPError(
            "404 Not Found"
        )
        
        with pytest.raises(requests.exceptions.HTTPError):
            mock_oanda_client.close_trade("trade-123")
    
    def test_get_open_trades_error(self, mock_oanda_client):
        """Test get_open_trades error handling."""
        mock_oanda_client.get_open_trades.side_effect = requests.exceptions.HTTPError(
            "500 Server Error"
        )
        
        with pytest.raises(requests.exceptions.HTTPError):
            mock_oanda_client.get_open_trades()
    
    def test_get_open_positions_error(self, mock_oanda_client):
        """Test get_open_positions error handling."""
        mock_oanda_client.get_open_positions.side_effect = requests.exceptions.HTTPError(
            "500 Server Error"
        )
        
        with pytest.raises(requests.exceptions.HTTPError):
            mock_oanda_client.get_open_positions()


