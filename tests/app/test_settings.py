"""
Tests for app/config/settings.py
"""

import pytest
import os
from unittest.mock import patch
from app.config.settings import Settings


class TestSettings:
    """Test Settings class."""
    
    def test_default_values(self):
        """Test that default values are set correctly."""
        assert Settings.INSTRUMENT == "EUR_USD"
        assert Settings.TAKE_PROFIT_PIPS == 10.0
        assert Settings.STOP_LOSS_PIPS is None
        assert Settings.POSITION_SIZE == 1
        assert Settings.SMA_PERIOD == 20
        assert Settings.DUAL_MARKET_OPEN_ENABLED is True
        assert Settings.EUR_MARKET_OPEN_HOUR == 8
        assert Settings.US_MARKET_OPEN_HOUR == 13
        assert Settings.MAX_DAILY_TRADES == 2
    
    def test_validate_with_token(self, monkeypatch):
        """Test validation with API token set."""
        monkeypatch.setenv("OANDA_API_TOKEN", "test-token")
        monkeypatch.setattr(Settings, 'OANDA_API_TOKEN', 'test-token')
        monkeypatch.setattr(Settings, 'OANDA_PRACTICE_MODE', True)
        
        warnings = Settings.validate()
        
        # Should not have ERROR about missing token
        error_warnings = [w for w in warnings if "ERROR" in w]
        assert len(error_warnings) == 0
    
    def test_validate_without_token(self, monkeypatch):
        """Test validation without API token."""
        monkeypatch.setattr(Settings, 'OANDA_API_TOKEN', None)
        
        warnings = Settings.validate()
        
        # Should have ERROR about missing token
        error_warnings = [w for w in warnings if "ERROR" in w and "OANDA_API_TOKEN" in w]
        assert len(error_warnings) > 0
    
    def test_validate_practice_mode(self, monkeypatch):
        """Test validation in practice mode."""
        monkeypatch.setattr(Settings, 'OANDA_PRACTICE_MODE', True)
        
        warnings = Settings.validate()
        
        # Should have practice mode message
        practice_warnings = [w for w in warnings if "Practice mode" in w]
        assert len(practice_warnings) > 0
    
    def test_validate_live_mode(self, monkeypatch):
        """Test validation in live mode."""
        monkeypatch.setattr(Settings, 'OANDA_PRACTICE_MODE', False)
        
        warnings = Settings.validate()
        
        # Should have live mode warning
        live_warnings = [w for w in warnings if "LIVE MODE" in w]
        assert len(live_warnings) > 0
    
    def test_validate_large_position_size(self, monkeypatch):
        """Test validation with large position size."""
        monkeypatch.setattr(Settings, 'POSITION_SIZE', 20000)
        
        warnings = Settings.validate()
        
        # Should have warning about large position size
        size_warnings = [w for w in warnings if "Large position size" in w]
        assert len(size_warnings) > 0
    
    def test_validate_no_stop_loss(self):
        """Test validation with no stop loss."""
        warnings = Settings.validate()
        
        # Should have warning about no stop loss
        sl_warnings = [w for w in warnings if "No stop loss" in w]
        assert len(sl_warnings) > 0
    
    def test_print_settings(self, capsys):
        """Test that print_settings outputs correctly."""
        Settings.print_settings()
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "TRADING APPLICATION SETTINGS" in output
        assert "Instrument:" in output
        assert "Strategy:" in output
        assert "EUR_USD" in output or "EUR" in output
    
    def test_log_dir_path(self):
        """Test that LOG_DIR is a valid Path."""
        assert hasattr(Settings.LOG_DIR, 'parent')
        assert Settings.LOG_DIR.name == "logs"
    
    def test_data_dir_path(self):
        """Test that DATA_DIR is a valid Path."""
        assert hasattr(Settings.DATA_DIR, 'parent')
        assert Settings.DATA_DIR.name == "data"

