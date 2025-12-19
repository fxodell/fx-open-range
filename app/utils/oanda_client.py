"""
OANDA API client for trading operations.
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import time


class OandaTradingClient:
    """OANDA API client for executing trades and managing positions."""
    
    PRACTICE_API = "https://api-fxpractice.oanda.com"
    LIVE_API = "https://api-fxtrade.oanda.com"
    
    def __init__(self, api_token: str, account_id: Optional[str] = None, practice: bool = True):
        """
        Initialize OANDA trading client.
        
        Parameters:
        -----------
        api_token : str
            OANDA API token
        account_id : str, optional
            Account ID (will fetch first account if not provided)
        practice : bool
            Use practice API (default True)
        """
        self.api_token = api_token
        self.practice = practice
        self.base_url = self.PRACTICE_API if practice else self.LIVE_API
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        # Get account ID
        if account_id:
            self.account_id = account_id
        else:
            self.account_id = self._get_account_id()
    
    def _get_account_id(self) -> str:
        """Get the first account ID."""
        url = f"{self.base_url}/v3/accounts"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        accounts = response.json()['accounts']
        if not accounts:
            raise ValueError("No accounts found")
        
        return accounts[0]['id']
    
    def get_account_info(self) -> Dict:
        """Get account information."""
        url = f"{self.base_url}/v3/accounts/{self.account_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()['account']
    
    def get_account_summary(self) -> Dict:
        """Get account summary."""
        url = f"{self.base_url}/v3/accounts/{self.account_id}/summary"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()['account']
    
    def get_open_positions(self) -> List[Dict]:
        """Get all open positions."""
        url = f"{self.base_url}/v3/accounts/{self.account_id}/openPositions"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json().get('positions', [])
    
    def get_open_trades(self) -> List[Dict]:
        """Get all open trades."""
        url = f"{self.base_url}/v3/accounts/{self.account_id}/openTrades"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json().get('trades', [])
    
    def get_pricing(self, instrument: str) -> Dict:
        """Get current pricing for an instrument."""
        url = f"{self.base_url}/v3/accounts/{self.account_id}/pricing"
        params = {"instruments": instrument}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_current_price(self, instrument: str) -> Dict[str, float]:
        """Get current bid/ask price."""
        pricing = self.get_pricing(instrument)
        price_info = pricing['prices'][0]
        
        return {
            'bid': float(price_info['bids'][0]['price']),
            'ask': float(price_info['asks'][0]['price']),
            'mid': (float(price_info['bids'][0]['price']) + float(price_info['asks'][0]['price'])) / 2,
            'time': price_info['time']
        }
    
    def fetch_candles(self,
                     instrument: str,
                     granularity: str = "D",
                     count: Optional[int] = None,
                     from_time: Optional[datetime] = None,
                     to_time: Optional[datetime] = None) -> pd.DataFrame:
        """
        Fetch historical candle data.
        
        Parameters:
        -----------
        instrument : str
            Instrument pair (e.g., "EUR_USD")
        granularity : str
            Candle granularity: "D" (daily), "H4" (4 hours), etc.
        count : int, optional
            Number of candles to fetch (max 5000)
        from_time : datetime, optional
            Start time
        to_time : datetime, optional
            End time
            
        Returns:
        --------
        pd.DataFrame with columns: Date, Open, High, Low, Close
        """
        url = f"{self.base_url}/v3/instruments/{instrument}/candles"
        
        params = {
            "granularity": granularity,
            "price": "M"  # Mid price
        }
        
        if count:
            params["count"] = min(count, 5000)
        elif from_time:
            params["from"] = from_time.isoformat() + "Z"
        else:
            raise ValueError("Must provide either 'count' or 'from_time'")
        
        if to_time:
            params["to"] = to_time.isoformat() + "Z"
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        candles = data.get('candles', [])
        
        # Convert to DataFrame
        records = []
        for candle in candles:
            if candle.get('complete', False):
                records.append({
                    'Date': pd.to_datetime(candle['time']),
                    'Open': float(candle['mid']['o']),
                    'High': float(candle['mid']['h']),
                    'Low': float(candle['mid']['l']),
                    'Close': float(candle['mid']['c']),
                    'Volume': int(candle.get('volume', 0))
                })
        
        df = pd.DataFrame(records)
        if len(df) > 0:
            df = df.sort_values('Date').reset_index(drop=True)
        
        return df
    
    def place_market_order(self,
                          instrument: str,
                          units: int,
                          take_profit_pips: Optional[float] = None,
                          stop_loss_pips: Optional[float] = None) -> Dict:
        """
        Place a market order.
        
        Parameters:
        -----------
        instrument : str
            Instrument pair
        units : int
            Number of units (positive for long, negative for short)
        take_profit_pips : float, optional
            Take profit in pips
        stop_loss_pips : float, optional
            Stop loss in pips
            
        Returns:
        --------
        Dict with order response
        """
        url = f"{self.base_url}/v3/accounts/{self.account_id}/orders"
        
        # Get current price to calculate TP/SL prices
        price_info = self.get_current_price(instrument)
        mid_price = price_info['mid']
        
        # Calculate pip value (for EUR/USD, 1 pip = 0.0001)
        pip_value = 0.0001
        
        order_data = {
            "order": {
                "type": "MARKET",
                "instrument": instrument,
                "units": str(units),
            }
        }
        
        # Add take profit
        if take_profit_pips:
            if units > 0:  # Long position
                tp_price = mid_price + (take_profit_pips * pip_value)
            else:  # Short position
                tp_price = mid_price - (take_profit_pips * pip_value)
            
            order_data["order"]["takeProfitOnFill"] = {
                "price": str(round(tp_price, 5)),
                "timeInForce": "GTC"
            }
        
        # Add stop loss
        if stop_loss_pips:
            if units > 0:  # Long position
                sl_price = mid_price - (stop_loss_pips * pip_value)
            else:  # Short position
                sl_price = mid_price + (stop_loss_pips * pip_value)
            
            order_data["order"]["stopLossOnFill"] = {
                "price": str(round(sl_price, 5)),
                "timeInForce": "GTC"
            }
        
        response = requests.post(url, headers=self.headers, json=order_data)
        response.raise_for_status()
        return response.json()
    
    def close_trade(self, trade_id: str) -> Dict:
        """Close a specific trade."""
        url = f"{self.base_url}/v3/accounts/{self.account_id}/trades/{trade_id}/close"
        response = requests.put(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def close_all_trades(self, instrument: Optional[str] = None) -> Dict:
        """Close all trades (optionally for a specific instrument)."""
        url = f"{self.base_url}/v3/accounts/{self.account_id}/trades"
        params = {}
        if instrument:
            params['instrument'] = instrument
        
        response = requests.put(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_instruments(self) -> List[str]:
        """Get list of available instruments."""
        url = f"{self.base_url}/v3/accounts/{self.account_id}/instruments"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        instruments = response.json().get('instruments', [])
        return [inst['name'] for inst in instruments]

