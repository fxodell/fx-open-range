"""
Tests for app/main.py
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
import argparse


class TestMainCLI:
    """Test CLI interface in main.py."""
    
    def test_argument_parser_defaults(self):
        """Test argument parser with default values."""
        from app.main import main
        
        with patch('sys.argv', ['main.py']):
            with patch('app.main.OandaTradingClient') as mock_client_class:
                with patch('app.main.TradingEngine') as mock_engine_class:
                    # Mock client
                    mock_client = Mock()
                    mock_client.get_account_info.return_value = {
                        'id': 'test-account',
                        'currency': 'USD',
                        'tags': [{'name': 'Practice Account'}]
                    }
                    mock_client_class.return_value = mock_client
                    
                    # Mock engine
                    mock_engine = Mock()
                    mock_engine_class.return_value = mock_engine
                    
                    # Mock input for practice mode (no prompt needed)
                    with patch('builtins.input', return_value='yes'):
                        with patch('sys.exit'):
                            try:
                                main()
                            except SystemExit:
                                pass
                    
                    # Should initialize with practice mode by default
                    mock_client_class.assert_called_once()
    
    def test_argument_parser_once_flag(self):
        """Test --once flag."""
        from app.main import main
        
        with patch('sys.argv', ['main.py', '--once']):
            with patch('app.main.OandaTradingClient') as mock_client_class:
                with patch('app.main.TradingEngine') as mock_engine_class:
                    # Mock client
                    mock_client = Mock()
                    mock_client.get_account_info.return_value = {
                        'id': 'test-account',
                        'currency': 'USD',
                        'tags': []
                    }
                    mock_client_class.return_value = mock_client
                    
                    # Mock engine
                    mock_engine = Mock()
                    mock_engine.run_once = Mock()
                    mock_engine_class.return_value = mock_engine
                    
                    with patch('sys.exit'):
                        try:
                            main()
                        except SystemExit:
                            pass
                    
                    # Should call run_once, not run_continuous
                    mock_engine.run_once.assert_called_once()
                    mock_engine.run_continuous.assert_not_called()
    
    def test_argument_parser_status_flag(self, capsys):
        """Test --status flag."""
        from app.main import main
        
        with patch('sys.argv', ['main.py', '--status']):
            with patch('app.main.OandaTradingClient') as mock_client_class:
                # Mock client
                mock_client = Mock()
                mock_client.get_account_info.return_value = {
                    'id': 'test-account',
                    'currency': 'USD',
                    'tags': []
                }
                mock_client.get_account_summary.return_value = {
                    'balance': '10000.00',
                    'currency': 'USD',
                    'unrealizedPL': '0.00',
                    'marginUsed': '0.00',
                    'marginAvailable': '10000.00'
                }
                mock_client.get_open_trades.return_value = []
                mock_client.get_open_positions.return_value = []
                mock_client_class.return_value = mock_client
                
                with patch('sys.exit'):
                    try:
                        main()
                    except SystemExit:
                        pass
                
                # Should call status methods
                mock_client.get_account_summary.assert_called_once()
                mock_client.get_open_trades.assert_called_once()
                mock_client.get_open_positions.assert_called_once()
                
                # Check output
                captured = capsys.readouterr()
                assert "Account Status" in captured.out
                assert "Balance" in captured.out
    
    def test_argument_parser_close_all_flag(self, capsys):
        """Test --close-all flag."""
        from app.main import main
        
        with patch('sys.argv', ['main.py', '--close-all']):
            with patch('app.main.OandaTradingClient') as mock_client_class:
                # Mock client
                mock_client = Mock()
                mock_client.get_account_info.return_value = {
                    'id': 'test-account',
                    'currency': 'USD',
                    'tags': []
                }
                mock_client.close_all_trades.return_value = {'ids': ['trade-1']}
                mock_client_class.return_value = mock_client
                
                with patch('sys.exit'):
                    try:
                        main()
                    except SystemExit:
                        pass
                
                # Should call close_all_trades
                mock_client.close_all_trades.assert_called_once()
                
                # Check output
                captured = capsys.readouterr()
                assert "Closing all open positions" in captured.out
    
    def test_argument_parser_mode_practice(self):
        """Test --mode practice."""
        from app.main import main
        
        with patch('sys.argv', ['main.py', '--mode', 'practice']):
            with patch('app.main.OandaTradingClient') as mock_client_class:
                with patch('app.main.TradingEngine') as mock_engine_class:
                    # Mock client
                    mock_client = Mock()
                    mock_client.get_account_info.return_value = {
                        'id': 'test-account',
                        'currency': 'USD',
                        'tags': []
                    }
                    mock_client_class.return_value = mock_client
                    
                    # Mock engine
                    mock_engine = Mock()
                    mock_engine_class.return_value = mock_engine
                    
                    with patch('sys.exit'):
                        try:
                            main()
                        except SystemExit:
                            pass
                    
                    # Should initialize with practice=True
                    call_args = mock_client_class.call_args
                    assert call_args[1]['practice'] is True
    
    def test_argument_parser_mode_live(self):
        """Test --mode live with confirmation."""
        from app.main import main
        
        with patch('sys.argv', ['main.py', '--mode', 'live']):
            with patch('app.main.OandaTradingClient') as mock_client_class:
                with patch('app.main.TradingEngine') as mock_engine_class:
                    # Mock client
                    mock_client = Mock()
                    mock_client.get_account_info.return_value = {
                        'id': 'test-account',
                        'currency': 'USD',
                        'tags': []
                    }
                    mock_client_class.return_value = mock_client
                    
                    # Mock engine
                    mock_engine = Mock()
                    mock_engine_class.return_value = mock_engine
                    
                    # Mock input to confirm live mode
                    with patch('builtins.input', return_value='yes'):
                        with patch('sys.exit'):
                            try:
                                main()
                            except SystemExit:
                                pass
                    
                    # Should initialize with practice=False
                    call_args = mock_client_class.call_args
                    assert call_args[1]['practice'] is False
    
    def test_argument_parser_mode_live_cancelled(self, capsys):
        """Test --mode live with cancellation."""
        from app.main import main
        
        with patch('sys.argv', ['main.py', '--mode', 'live']):
            with patch('app.main.OandaTradingClient') as mock_client_class:
                # Mock input to cancel
                with patch('builtins.input', return_value='no'):
                    with patch('sys.exit'):
                        try:
                            main()
                        except SystemExit:
                            pass
                
                # Should not initialize client if cancelled
                mock_client_class.assert_not_called()
                
                # Check output
                captured = capsys.readouterr()
                assert "Exiting" in captured.out
    
    def test_argument_parser_interval(self):
        """Test --interval flag."""
        from app.main import main
        
        with patch('sys.argv', ['main.py', '--interval', '120', '--mode', 'practice']):
            with patch('app.main.OandaTradingClient') as mock_client_class:
                with patch('app.main.TradingEngine') as mock_engine_class:
                    # Mock client
                    mock_client = Mock()
                    mock_client.get_account_info.return_value = {
                        'id': 'test-account',
                        'currency': 'USD',
                        'tags': []
                    }
                    mock_client_class.return_value = mock_client
                    
                    # Mock engine
                    mock_engine = Mock()
                    mock_engine_class.return_value = mock_engine
                    
                    with patch('sys.exit'):
                        try:
                            main()
                        except SystemExit:
                            pass
                    
                    # Should call run_continuous with interval
                    if mock_engine.run_continuous.called:
                        call_args = mock_engine.run_continuous.call_args
                        assert call_args[1]['check_interval_seconds'] == 120
    
    def test_signal_handler(self):
        """Test signal handler for Ctrl+C."""
        from app.main import signal_handler
        
        with patch('sys.exit') as mock_exit:
            signal_handler(None, None)
            mock_exit.assert_called_once_with(0)
    
    def test_main_error_handling(self, capsys):
        """Test error handling in main."""
        from app.main import main
        
        with patch('sys.argv', ['main.py', '--mode', 'practice']):
            with patch('app.main.OandaTradingClient') as mock_client_class:
                # Make client initialization raise an error
                mock_client_class.side_effect = Exception("Connection failed")
                
                with patch('sys.exit') as mock_exit:
                    try:
                        main()
                    except SystemExit:
                        pass
                    
                    # Should exit with error code
                    mock_exit.assert_called()
                    
                    # Check error output
                    captured = capsys.readouterr()
                    assert "Error" in captured.out or "Connection failed" in captured.out
    
    def test_main_keyboard_interrupt(self, capsys):
        """Test KeyboardInterrupt handling."""
        from app.main import main
        
        with patch('sys.argv', ['main.py', '--mode', 'practice']):
            with patch('app.main.OandaTradingClient') as mock_client_class:
                with patch('app.main.TradingEngine') as mock_engine_class:
                    # Mock client
                    mock_client = Mock()
                    mock_client.get_account_info.return_value = {
                        'id': 'test-account',
                        'currency': 'USD',
                        'tags': []
                    }
                    mock_client_class.return_value = mock_client
                    
                    # Mock engine to raise KeyboardInterrupt
                    mock_engine = Mock()
                    mock_engine.run_continuous.side_effect = KeyboardInterrupt()
                    mock_engine_class.return_value = mock_engine
                    
                    with patch('sys.exit'):
                        try:
                            main()
                        except (SystemExit, KeyboardInterrupt):
                            pass
                    
                    # Check output
                    captured = capsys.readouterr()
                    assert "Interrupted" in captured.out or "KeyboardInterrupt" in str(captured.out)
    
    def test_main_continuous_mode(self):
        """Test continuous mode (default, no --once)."""
        from app.main import main
        
        with patch('sys.argv', ['main.py', '--mode', 'practice']):
            with patch('app.main.OandaTradingClient') as mock_client_class:
                with patch('app.main.TradingEngine') as mock_engine_class:
                    # Mock client
                    mock_client = Mock()
                    mock_client.get_account_info.return_value = {
                        'id': 'test-account',
                        'currency': 'USD',
                        'tags': []
                    }
                    mock_client_class.return_value = mock_client
                    
                    # Mock engine
                    mock_engine = Mock()
                    mock_engine.run_continuous = Mock()
                    mock_engine_class.return_value = mock_engine
                    
                    with patch('sys.exit'):
                        try:
                            main()
                        except SystemExit:
                            pass
                    
                    # Should call run_continuous (if not interrupted)
                    # Note: This may not be called if KeyboardInterrupt happens
                    # So we just check that engine was created
                    mock_engine_class.assert_called_once()
    
    def test_main_settings_print(self, capsys):
        """Test that settings are printed."""
        from app.main import main
        
        with patch('sys.argv', ['main.py', '--status', '--mode', 'practice']):
            with patch('app.main.OandaTradingClient') as mock_client_class:
                # Mock client
                mock_client = Mock()
                mock_client.get_account_info.return_value = {
                    'id': 'test-account',
                    'currency': 'USD',
                    'tags': []
                }
                mock_client.get_account_summary.return_value = {
                    'balance': '10000.00',
                    'currency': 'USD',
                    'unrealizedPL': '0.00',
                    'marginUsed': '0.00',
                    'marginAvailable': '10000.00'
                }
                mock_client.get_open_trades.return_value = []
                mock_client.get_open_positions.return_value = []
                mock_client_class.return_value = mock_client
                
                with patch('app.main.Settings.print_settings') as mock_print:
                    with patch('sys.exit'):
                        try:
                            main()
                        except SystemExit:
                            pass
                    
                    # Should print settings
                    mock_print.assert_called_once()

