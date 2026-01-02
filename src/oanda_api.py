"""
OANDA API integration for fetching EUR/USD historical data.
"""

import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from pathlib import Path
import sys

# Add parent directory to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.utils.retry import retry_with_backoff


class OandaAPI:
    """OANDA API client for fetching historical data."""
    
    # OANDA API endpoints
    PRACTICE_API = "https://api-fxpractice.oanda.com"
    LIVE_API = "https://api-fxtrade.oanda.com"
    
    def __init__(self, api_token: str, practice: bool = True):
        """
        Initialize OANDA API client.
        
        Parameters:
        -----------
        api_token : str
            Your OANDA API token
        practice : bool
            Use practice API (default True) or live API (False)
        """
        self.api_token = api_token
        self.base_url = self.PRACTICE_API if practice else self.LIVE_API
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def get_instruments(self) -> List[str]:
        """Get list of available instruments."""
        url = f"{self.base_url}/v3/accounts"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        accounts = response.json()['accounts']
        if not accounts:
            raise ValueError("No accounts found")
        
        account_id = accounts[0]['id']
        
        url = f"{self.base_url}/v3/accounts/{account_id}/instruments"
        response = requests.get(url, headers=self.headers, params={"instruments": "EUR_USD"})
        response.raise_for_status()
        
        instruments = response.json()['instruments']
        return [inst['name'] for inst in instruments]
    
    def get_account_info(self):
        """Get account information."""
        url = f"{self.base_url}/v3/accounts"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        accounts = response.json()['accounts']
        if not accounts:
            raise ValueError("No accounts found")
        
        account_id = accounts[0]['id']
        
        url = f"{self.base_url}/v3/accounts/{account_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        return response.json()['account']
    
    @retry_with_backoff(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
    def fetch_candles(self,
                     instrument: str = "EUR_USD",
                     granularity: str = "D",  # D = daily, H4 = 4 hours, etc.
                     count: Optional[int] = None,
                     from_time: Optional[datetime] = None,
                     to_time: Optional[datetime] = None) -> pd.DataFrame:
        """
        Fetch historical candle data from OANDA.
        
        Parameters:
        -----------
        instrument : str
            Instrument pair (default: "EUR_USD")
        granularity : str
            Candle granularity: "D" (daily), "H12" (12 hours), "H4" (4 hours), etc.
            See OANDA docs for all options
        count : int, optional
            Number of candles to fetch (max 5000)
        from_time : datetime, optional
            Start time (must provide either count or from_time)
        to_time : datetime, optional
            End time (default: now)
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with columns: Date, Open, High, Low, Close
        """
        url = f"{self.base_url}/v3/instruments/{instrument}/candles"
        
        params = {
            "granularity": granularity,
            "price": "M"  # M = Mid price, B = Bid, A = Ask
        }
        
        if count:
            params["count"] = min(count, 5000)  # OANDA max is 5000
        elif from_time:
            # OANDA API expects RFC3339 format: YYYY-MM-DDTHH:MM:SS.000000Z
            # Ensure timezone-aware UTC and format correctly
            if from_time.tzinfo is None:
                from_time = from_time.replace(tzinfo=timezone.utc)
            else:
                from_time = from_time.astimezone(timezone.utc)
            # Format: use microseconds (6 digits) and Z suffix
            params["from"] = from_time.strftime("%Y-%m-%dT%H:%M:%S.000000Z")
        else:
            raise ValueError("Must provide either 'count' or 'from_time'")
        
        if to_time:
            # OANDA API expects RFC3339 format: YYYY-MM-DDTHH:MM:SS.000000Z
            # Ensure timezone-aware UTC and format correctly
            if to_time.tzinfo is None:
                to_time = to_time.replace(tzinfo=timezone.utc)
            else:
                to_time = to_time.astimezone(timezone.utc)
            # Format: use microseconds (6 digits) and Z suffix
            params["to"] = to_time.strftime("%Y-%m-%dT%H:%M:%S.000000Z")
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if 'candles' not in data:
            raise ValueError(f"No candles returned: {data}")
        
        candles = data['candles']
        
        # Convert to DataFrame
        records = []
        for candle in candles:
            if candle['complete']:  # Only include complete candles
                records.append({
                    'Date': pd.to_datetime(candle['time']),
                    'Open': float(candle['mid']['o']),
                    'High': float(candle['mid']['h']),
                    'Low': float(candle['mid']['l']),
                    'Close': float(candle['mid']['c']),
                    'Volume': int(candle['volume']) if 'volume' in candle else 0
                })
        
        df = pd.DataFrame(records)
        
        if len(df) == 0:
            raise ValueError("No complete candles returned")
        
        # Sort by date (oldest first)
        df = df.sort_values('Date').reset_index(drop=True)
        
        # Add 'Price' column (same as Close) to match existing format
        df['Price'] = df['Close']
        
        return df
    
    def fetch_daily_data(self,
                        instrument: str = "EUR_USD",
                        days: int = 365,
                        end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Convenience method to fetch daily EUR/USD data.
        
        Parameters:
        -----------
        instrument : str
            Instrument pair (default: "EUR_USD")
        days : int
            Number of days to fetch (default: 365)
        end_date : datetime, optional
            End date (default: today)
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with columns: Date, Price, Open, High, Low, Close
        """
        if end_date is None:
            end_date = datetime.now()
        
        # Fetch data in chunks if needed (OANDA limit is 5000)
        all_data = []
        
        if days <= 5000:
            # Single request
            from_time = end_date - timedelta(days=days + 10)  # Add buffer
            df = self.fetch_candles(instrument, "D", from_time=from_time, to_time=end_date)
            all_data.append(df)
        else:
            # Multiple requests
            remaining = days
            current_end = end_date
            
            while remaining > 0:
                chunk_days = min(remaining, 5000)
                from_time = current_end - timedelta(days=chunk_days + 10)
                
                df = self.fetch_candles(instrument, "D", from_time=from_time, to_time=current_end)
                all_data.append(df)
                
                # Move to next chunk
                current_end = from_time
                remaining -= len(df)
        
        # Combine all data
        if len(all_data) > 1:
            combined_df = pd.concat(all_data, ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=['Date']).sort_values('Date').reset_index(drop=True)
        else:
            combined_df = all_data[0]
        
        # Limit to requested days
        if len(combined_df) > days:
            combined_df = combined_df.tail(days).reset_index(drop=True)
        
        return combined_df


def save_oanda_data(df: pd.DataFrame, filename: str = "eur_usd_oanda.csv"):
    """
    Save OANDA data to CSV in the same format as existing data.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with Date, Open, High, Low, Close columns
    filename : str
        Output filename
    """
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    filepath = data_dir / filename
    
    # Format for output
    df_output = df.copy()
    df_output['Date'] = df_output['Date'].dt.strftime('%m/%d/%Y')
    
    # Add empty columns to match original format
    df_output['Vol.'] = ''
    df_output['Change %'] = ''
    
    # Reorder columns
    df_output = df_output[['Date', 'Price', 'Open', 'High', 'Low', 'Vol.', 'Change %']]
    
    # Save
    df_output.to_csv(filepath, index=False)
    
    print(f"Data saved to: {filepath}")
    print(f"Total rows: {len(df_output)}")
    print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
    
    return filepath

