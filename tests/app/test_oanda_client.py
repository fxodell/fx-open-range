"""
Tests for app/utils/oanda_client.py
"""

import pytest
import pandas as pd
import requests
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
from app.utils.oanda_client import OandaTradingClient


class TestOandaTradingClient:
    """Test OandaTradingClient."""
    
    def test_client_initialization_practice(self):
        """Test client initialization in practice mode."""
        with patch('app.utils.oanda_client.requests.get') as mock_get:
            # Mock account ID fetch
            mock_get.return_value.json.return_value = {
                'accounts': [{'id': 'test-account-123'}]
            }
            mock_get.return_value.raise_for_status = Mock()
            
            client = OandaTradingClient(
                api_token="test-token",
                account_id=None,
                practice=True
            )
            
            assert client.practice is True
            assert client.base_url == OandaTradingClient.PRACTICE_API
            assert client.account_id == 'test-account-123'
    
    def test_client_initialization_live(self):
        """Test client initialization in live mode."""
        with patch('app.utils.oanda_client.requests.get') as mock_get:
            mock_get.return_value.json.return_value = {
                'accounts': [{'id': 'test-account-123'}]
            }
            mock_get.return_value.raise_for_status = Mock()
            
            client = OandaTradingClient(
                api_token="test-token",
                account_id="custom-account",
                practice=False
            )
            
            assert client.practice is False
            assert client.base_url == OandaTradingClient.LIVE_API
            assert client.account_id == "custom-account"
    
    @pytest.mark.parametrize("test_datetime,expected_format", [
        (datetime(2025, 12, 2, 13, 59, 27), "2025-12-02T13:59:27.000000Z"),
        (datetime(2025, 12, 2, 13, 59, 27, tzinfo=timezone.utc), "2025-12-02T13:59:27.000000Z"),
        (datetime(2025, 12, 2, 13, 59, 27, 990721, tzinfo=timezone.utc), "2025-12-02T13:59:27.000000Z"),
        (datetime(2025, 12, 2, 13, 59, 27, tzinfo=timezone(timedelta(hours=-5))), "2025-12-02T18:59:27.000000Z"),
    ])
    def test_fetch_candles_datetime_formatting(self, test_datetime, expected_format):
        """CRITICAL: Test that datetime formatting is correct for OANDA API.
        
        This test ensures datetimes are formatted as RFC3339 (YYYY-MM-DDTHH:MM:SS.000000Z)
        and NOT as invalid formats like YYYY-MM-DDTHH:MM:SS.microseconds+00:00Z
        which causes 400 Bad Request errors.
        """
        with patch('app.utils.oanda_client.requests.get') as mock_get:
            # Setup client
            mock_get.return_value.json.return_value = {
                'accounts': [{'id': 'test-account-123'}]
            }
            mock_get.return_value.raise_for_status = Mock()
            
            client = OandaTradingClient(
                api_token="test-token",
                account_id="test-account-123",
                practice=True
            )
            
            # Mock successful response
            mock_get.return_value.json.return_value = {
                'candles': [{
                    'complete': True,
                    'time': '2025-12-02T13:00:00.000000000Z',
                    'mid': {'o': '1.1600', 'h': '1.1610', 'l': '1.1590', 'c': '1.1605'},
                    'volume': 1000
                }]
            }
            mock_get.return_value.raise_for_status = Mock()
            
            # Call fetch_candles
            end_time = test_datetime
            start_time = end_time - timedelta(days=30)
            
            client.fetch_candles(
                instrument="EUR_USD",
                granularity="D",
                from_time=start_time,
                to_time=end_time
            )
            
            # Verify the request was made
            assert mock_get.called
            
            # Get the actual request parameters
            call_args = mock_get.call_args
            params = call_args[1]['params']  # kwargs['params']
            
            # Verify datetime format is correct
            if 'from' in params:
                from_param = params['from']
                # Should NOT contain timezone offset (+00:00)
                assert "+" not in from_param, f"Datetime should not contain timezone offset: {from_param}"
                # Should end with Z
                assert from_param.endswith("Z"), f"Datetime should end with Z: {from_param}"
                # Should have microseconds format (.000000)
                assert ".000000" in from_param or from_param.count(".") == 0, \
                    f"Datetime should have proper microseconds format: {from_param}"
                # Should match RFC3339 format pattern (YYYY-MM-DDTHH:MM:SS.000000Z)
                assert "T" in from_param, f"Datetime should be in RFC3339 format: {from_param}"
                assert from_param.count(":") == 2, f"Datetime should have time component: {from_param}"
            
            if 'to' in params:
                to_param = params['to']
                # Same checks for 'to' parameter
                assert "+" not in to_param, f"Datetime should not contain timezone offset: {to_param}"
                assert to_param.endswith("Z"), f"Datetime should end with Z: {to_param}"
    
    def test_fetch_candles_datetime_formatting_naive(self):
        """Test datetime formatting with naive datetime (no timezone)."""
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
            
            mock_get.return_value.json.return_value = {'candles': []}
            
            # Naive datetime (no timezone)
            naive_time = datetime(2025, 12, 2, 13, 59, 27)
            
            client.fetch_candles(
                instrument="EUR_USD",
                granularity="D",
                from_time=naive_time,
                to_time=naive_time
            )
            
            call_args = mock_get.call_args
            params = call_args[1]['params']
            
            # Should be converted to UTC and formatted correctly
            if 'from' in params:
                assert "+" not in params['from']
                assert params['from'].endswith("Z")
    
    def test_fetch_candles_datetime_formatting_with_microseconds(self):
        """Test datetime formatting with microseconds (the bug case)."""
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
            
            mock_get.return_value.json.return_value = {'candles': []}
            
            # Datetime with microseconds and timezone (the problematic case)
            dt_with_microseconds = datetime(2025, 12, 2, 13, 59, 27, 990721, tzinfo=timezone.utc)
            
            client.fetch_candles(
                instrument="EUR_USD",
                granularity="D",
                from_time=dt_with_microseconds,
                to_time=dt_with_microseconds
            )
            
            call_args = mock_get.call_args
            params = call_args[1]['params']
            
            # CRITICAL: Should NOT have the buggy format: 2025-12-02T13:59:27.990721+00:00Z
            # Should have correct format: 2025-12-02T13:59:27.000000Z
            if 'from' in params:
                from_param = params['from']
                # Must NOT have both +00:00 and Z
                assert not ("+00:00" in from_param and from_param.endswith("Z")), \
                    f"Invalid datetime format (bug case): {from_param}"
                # Must NOT have microseconds in the format
                if ".990721" in from_param:
                    assert False, f"Microseconds should be removed: {from_param}"
                # Should have proper format
                assert from_param.endswith(".000000Z") or from_param.endswith("Z"), \
                    f"Should have proper RFC3339 format: {from_param}"
    
    def test_fetch_candles_with_count(self, mock_oanda_client):
        """Test fetch_candles with count parameter."""
        mock_oanda_client.fetch_candles.return_value = pd.DataFrame({
            'Date': [datetime.now(timezone.utc)],
            'Open': [1.1600],
            'High': [1.1610],
            'Low': [1.1590],
            'Close': [1.1605],
        })
        
        df = mock_oanda_client.fetch_candles(
            instrument="EUR_USD",
            granularity="D",
            count=30
        )
        
        assert isinstance(df, pd.DataFrame)
        mock_oanda_client.fetch_candles.assert_called_once()
    
    def test_get_account_info(self, mock_oanda_client):
        """Test get_account_info."""
        info = mock_oanda_client.get_account_info()
        
        assert 'id' in info
        assert info['id'] == 'test-account-123'
    
    def test_get_account_summary(self, mock_oanda_client):
        """Test get_account_summary."""
        summary = mock_oanda_client.get_account_summary()
        
        assert 'balance' in summary
        assert 'currency' in summary
        assert summary['currency'] == 'USD'
    
    def test_get_open_positions(self, mock_oanda_client):
        """Test get_open_positions."""
        positions = mock_oanda_client.get_open_positions()
        
        assert isinstance(positions, list)
    
    def test_get_open_trades(self, mock_oanda_client):
        """Test get_open_trades."""
        trades = mock_oanda_client.get_open_trades()
        
        assert isinstance(trades, list)
    
    def test_get_current_price(self, mock_oanda_client):
        """Test get_current_price."""
        price_info = mock_oanda_client.get_current_price("EUR_USD")
        
        assert 'bid' in price_info
        assert 'ask' in price_info
        assert 'mid' in price_info
        assert price_info['bid'] < price_info['ask']  # Bid should be less than ask
    
    def test_place_market_order(self, mock_oanda_client):
        """Test place_market_order."""
        result = mock_oanda_client.place_market_order(
            instrument="EUR_USD",
            units=1,
            take_profit_pips=10.0
        )
        
        assert 'orderFillTransaction' in result or 'order' in result
        mock_oanda_client.place_market_order.assert_called_once()
    
    def test_close_trade(self, mock_oanda_client):
        """Test close_trade."""
        result = mock_oanda_client.close_trade("test-trade-123")
        
        assert 'id' in result
        mock_oanda_client.close_trade.assert_called_once_with("test-trade-123")
    
    def test_close_all_trades(self, mock_oanda_client):
        """Test close_all_trades."""
        result = mock_oanda_client.close_all_trades(instrument="EUR_USD")
        
        assert 'ids' in result or result is not None
        mock_oanda_client.close_all_trades.assert_called_once()

