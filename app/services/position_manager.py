"""
Position Manager - Handles position management and safety checks.
"""

from typing import List, Dict, Optional
from app.utils.oanda_client import OandaTradingClient
from app.config.settings import Settings


class PositionManager:
    """Manages trading positions and safety checks."""
    
    def __init__(self, client: OandaTradingClient, instrument: str = None):
        """
        Initialize position manager.
        
        Parameters:
        -----------
        client : OandaTradingClient
            OANDA API client
        instrument : str, optional
            Trading instrument (default: from Settings)
        """
        self.client = client
        self.instrument = instrument or Settings.INSTRUMENT
    
    def get_open_positions(self) -> List[Dict]:
        """
        Get all open positions for the instrument.
        
        Returns:
        --------
        List[Dict]
            List of open trade dictionaries
        """
        try:
            open_trades = self.client.get_open_trades()
            our_trades = [t for t in open_trades if t.get('instrument') == self.instrument]
            return our_trades
        except Exception:
            return []
    
    def has_open_position(self) -> bool:
        """
        Check if there is an open position.
        
        Returns:
        --------
        bool
            True if position is open, False otherwise
        """
        positions = self.get_open_positions()
        return len(positions) > 0
    
    def close_all_positions(self) -> int:
        """
        Close all open positions.
        
        Returns:
        --------
        int
            Number of positions closed
        """
        positions = self.get_open_positions()
        if not positions:
            return 0
        
        closed_count = 0
        for position in positions:
            try:
                self.client.close_trade(position['id'])
                closed_count += 1
            except Exception:
                pass
        
        return closed_count
    
    def validate_position_size(self, units: int) -> bool:
        """
        Validate position size against limits.
        
        Parameters:
        -----------
        units : int
            Number of units to trade
            
        Returns:
        --------
        bool
            True if position size is valid, False otherwise
        """
        # Check against maximum position size (if configured)
        max_position_size = getattr(Settings, 'MAX_POSITION_SIZE', None)
        if max_position_size and abs(units) > max_position_size:
            return False
        
        return True
    
    def get_position_count(self) -> int:
        """
        Get number of open positions.
        
        Returns:
        --------
        int
            Number of open positions
        """
        return len(self.get_open_positions())





