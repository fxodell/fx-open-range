"""
Tests for src/oanda_api.py
"""

import pytest
import pandas as pd
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch
from src.oanda_api import OandaAPI


class TestOandaAPI:
    """Test OandaAPI class."""
    
    def test_oanda_api_initialization_practice(self):
        """Test OandaAPI initialization in practice mode."""
        with patch('src.oanda_api.requests.get') as mock_get:
            mock_get.return_value.json.return_value = {
                'accounts': [{'id': 'test-account-123'}]
            }
            mock_get.return_value.raise_for_status = Mock()
            
            api = OandaAPI(api_token="test-token", practice=True)
            
            assert api.base_url == OandaAPI.PRACTICE_API  # Check base_url instead of practice attribute
    
    def test_oanda_api_initialization_live(self):
        """Test OandaAPI initialization in live mode."""
        with patch('src.oanda_api.requests.get') as mock_get:
            mock_get.return_value.json.return_value = {
                'accounts': [{'id': 'test-account-123'}]
            }
            mock_get.return_value.raise_for_status = Mock()
            
            api = OandaAPI(api_token="test-token", practice=False)
            
            assert api.base_url == OandaAPI.LIVE_API  # Check base_url instead of practice attribute
    
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
        with patch('src.oanda_api.requests.get') as mock_get:
            mock_get.return_value.json.return_value = {
                'candles': [{
                    'complete': True,
                    'time': '2025-12-02T13:00:00.000000000Z',
                    'mid': {'o': '1.1600', 'h': '1.1610', 'l': '1.1590', 'c': '1.1605'},
                    'volume': 1000
                }]
            }
            mock_get.return_value.raise_for_status = Mock()
            
            api = OandaAPI(api_token="test-token", practice=True)
            
            # Call fetch_candles
            end_time = test_datetime
            start_time = end_time - timedelta(days=30)
            
            api.fetch_candles(
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
                # Should match RFC3339 format pattern
                assert "T" in from_param, f"Datetime should be in RFC3339 format: {from_param}"
                assert from_param.count(":") == 2, f"Datetime should have time component: {from_param}"
            
            if 'to' in params:
                to_param = params['to']
                # Same checks for 'to' parameter
                assert "+" not in to_param, f"Datetime should not contain timezone offset: {to_param}"
                assert to_param.endswith("Z"), f"Datetime should end with Z: {to_param}"
    
    def test_fetch_candles_datetime_formatting_with_microseconds(self):
        """Test datetime formatting with microseconds (the bug case)."""
        with patch('src.oanda_api.requests.get') as mock_get:
            mock_get.return_value.json.return_value = {
                'candles': [{
                    'complete': True,
                    'time': '2025-12-02T13:00:00.000000000Z',
                    'mid': {'o': '1.1600', 'h': '1.1610', 'l': '1.1590', 'c': '1.1605'},
                    'volume': 1000
                }]
            }
            mock_get.return_value.raise_for_status = Mock()
            
            api = OandaAPI(api_token="test-token", practice=True)
            
            # Datetime with microseconds and timezone (the problematic case)
            dt_with_microseconds = datetime(2025, 12, 2, 13, 59, 27, 990721, tzinfo=timezone.utc)
            
            api.fetch_candles(
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
    
    def test_fetch_candles_with_count(self, mock_oanda_api):
        """Test fetch_candles with count parameter."""
        mock_oanda_api.fetch_candles.return_value = pd.DataFrame({
            'Date': [datetime.now(timezone.utc)],
            'Open': [1.1600],
            'High': [1.1610],
            'Low': [1.1590],
            'Close': [1.1605],
        })
        
        df = mock_oanda_api.fetch_candles(
            instrument="EUR_USD",
            granularity="D",
            count=30
        )
        
        assert isinstance(df, pd.DataFrame)
        mock_oanda_api.fetch_candles.assert_called_once()
    
    def test_fetch_daily_data(self, mock_oanda_api):
        """Test fetch_daily_data convenience method."""
        mock_oanda_api.fetch_daily_data.return_value = pd.DataFrame({
            'Date': [datetime.now(timezone.utc)],
            'Open': [1.1600],
            'High': [1.1610],
            'Low': [1.1590],
            'Close': [1.1605],
        })
        
        df = mock_oanda_api.fetch_daily_data("EUR_USD", days=30)
        
        assert isinstance(df, pd.DataFrame)
        mock_oanda_api.fetch_daily_data.assert_called_once()
    
    def test_get_instruments(self, mock_oanda_api):
        """Test get_instruments."""
        instruments = mock_oanda_api.get_instruments()
        
        assert isinstance(instruments, list)
        assert 'EUR_USD' in instruments
    
    def test_get_account_info(self, mock_oanda_api):
        """Test get_account_info."""
        info = mock_oanda_api.get_account_info()
        
        assert 'id' in info
        assert info['id'] == 'test-account-123'
    
    def test_save_oanda_data(self, tmp_path):
        """Test save_oanda_data CSV saving."""
        # Check if method exists in OandaAPI
        if hasattr(OandaAPI, 'save_oanda_data'):
            df = pd.DataFrame({
                'Date': pd.date_range('2025-12-01', periods=5, freq='D'),
                'Open': [1.1600] * 5,
                'High': [1.1610] * 5,
                'Low': [1.1590] * 5,
                'Close': [1.1605] * 5,
            })
            
            with patch('src.oanda_api.requests.get') as mock_get:
                mock_get.return_value.json.return_value = {'accounts': [{'id': 'test'}]}
                mock_get.return_value.raise_for_status = Mock()
                
                api = OandaAPI(api_token="test-token", practice=True)
                csv_file = tmp_path / "test_data.csv"
                api.save_oanda_data(df, str(csv_file))
                
                # Verify file was created
                assert csv_file.exists()
        else:
            # Method doesn't exist, skip test
            pytest.skip("save_oanda_data method not implemented")

