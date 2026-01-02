"""
Error handling tests for src/oanda_api.py
"""

import pytest
import requests
from unittest.mock import Mock, patch
from src.oanda_api import OandaAPI


class TestOandaAPIErrors:
    """Test error handling in OandaAPI."""
    
    def test_fetch_candles_400_error(self):
        """Test handling of 400 Bad Request error."""
        with patch('src.oanda_api.requests.get') as mock_get:
            client = OandaAPI(api_token="test-token", practice=True)
            
            # Mock 400 error
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
                "400 Client Error: Bad Request"
            )
            mock_get.return_value = mock_response
            
            with pytest.raises(requests.exceptions.HTTPError):
                client.fetch_candles(
                    instrument="EUR_USD",
                    granularity="D",
                    count=30
                )
    
    def test_fetch_candles_401_error(self):
        """Test handling of 401 Unauthorized error."""
        with patch('src.oanda_api.requests.get') as mock_get:
            client = OandaAPI(api_token="test-token", practice=True)
            
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
    
    def test_fetch_candles_500_error(self):
        """Test handling of 500 Internal Server Error."""
        with patch('src.oanda_api.requests.get') as mock_get:
            client = OandaAPI(api_token="test-token", practice=True)
            
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
        with patch('src.oanda_api.requests.get') as mock_get:
            client = OandaAPI(api_token="test-token", practice=True)
            
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
        with patch('src.oanda_api.requests.get') as mock_get:
            client = OandaAPI(api_token="test-token", practice=True)
            
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
        with patch('src.oanda_api.requests.get') as mock_get:
            client = OandaAPI(api_token="test-token", practice=True)
            
            # Mock invalid JSON response
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_get.return_value = mock_response
            
            with pytest.raises(ValueError):
                client.fetch_candles(
                    instrument="EUR_USD",
                    granularity="D",
                    count=30
                )
    
    def test_get_instruments_error(self):
        """Test get_instruments error handling."""
        with patch('src.oanda_api.requests.get') as mock_get:
            client = OandaAPI(api_token="test-token", practice=True)
            
            # Mock API error
            mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError(
                "500 Server Error"
            )
            
            with pytest.raises(requests.exceptions.HTTPError):
                client.get_instruments()
    
    def test_get_account_info_error(self):
        """Test get_account_info error handling."""
        with patch('src.oanda_api.requests.get') as mock_get:
            client = OandaAPI(api_token="test-token", practice=True)
            
            # Mock API error
            mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError(
                "401 Unauthorized"
            )
            
            with pytest.raises(requests.exceptions.HTTPError):
                client.get_account_info()
    
    def test_fetch_daily_data_error(self):
        """Test fetch_daily_data error handling."""
        with patch('src.oanda_api.requests.get') as mock_get:
            client = OandaAPI(api_token="test-token", practice=True)
            
            # Mock API error
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
                "400 Bad Request"
            )
            mock_get.return_value = mock_response
            
            with pytest.raises(requests.exceptions.HTTPError):
                client.fetch_daily_data("EUR_USD", days=30)

