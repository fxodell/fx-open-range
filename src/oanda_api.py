"""
OANDA API integration for fetching EUR/USD historical data.
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List
from pathlib import Path


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
            params["from"] = from_time.isoformat() + "Z"
        else:
            raise ValueError("Must provide either 'count' or 'from_time'")
        
        if to_time:
            params["to"] = to_time.isoformat() + "Z"
        
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


def main():
    """Example usage."""
    import sys
    
    # API token (from user)
    API_TOKEN = "965884e308ff2a75fcf9a5011a2cc39a-616820942fc0746b78b04062b603c20d"
    
    print("=" * 80)
    print("OANDA API - Fetch EUR/USD Historical Data")
    print("=" * 80)
    print()
    
    try:
        # Initialize API client
        print("Connecting to OANDA API...")
        api = OandaAPI(API_TOKEN, practice=True)  # Set practice=False for live account
        
        # Test connection
        try:
            account_info = api.get_account_info()
            print(f"✓ Connected successfully")
            print(f"  Account ID: {account_info.get('id', 'N/A')}")
            print(f"  Account Type: {account_info.get('tags', [{}])[0].get('type', 'N/A') if account_info.get('tags') else 'N/A'}")
        except Exception as e:
            print(f"⚠ Warning: Could not get account info: {e}")
            print("  Continuing anyway...")
        
        # Fetch data
        print("\nFetching EUR/USD daily data...")
        print("Options:")
        print("1. Last 1 year (365 days)")
        print("2. Last 2 years (730 days)")
        print("3. Last 5 years (~1825 days)")
        print("4. Custom number of days")
        
        choice = input("\nEnter choice (1-4, default=3): ").strip() or "3"
        
        if choice == "1":
            days = 365
        elif choice == "2":
            days = 730
        elif choice == "3":
            days = 1825
        elif choice == "4":
            days = int(input("Enter number of days: "))
        else:
            days = 1825
        
        print(f"\nFetching {days} days of EUR/USD data...")
        df = api.fetch_daily_data("EUR_USD", days=days)
        
        print(f"✓ Fetched {len(df)} days of data")
        print(f"  Date range: {df['Date'].min()} to {df['Date'].max()}")
        
        # Save to CSV
        filename = "eur_usd_oanda.csv"
        filepath = save_oanda_data(df, filename)
        
        print(f"\n✓ Data saved successfully!")
        print(f"\nYou can now use this data for backtesting:")
        print(f"  python test_long_term.py  # (modify to use {filename})")
        
    except requests.exceptions.HTTPError as e:
        print(f"\n✗ API Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"  Response: {e.response.text}")
        print("\nPossible issues:")
        print("  - Invalid API token")
        print("  - Account access issue")
        print("  - API endpoint incorrect")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

