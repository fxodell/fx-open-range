"""
Fetch long-term EUR/USD historical data from Yahoo Finance.
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("yfinance not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance"])
    import yfinance as yf
    YFINANCE_AVAILABLE = True


def fetch_eurusd_data(start_date='2020-01-01', end_date=None):
    """
    Fetch EUR/USD historical data from Yahoo Finance.
    
    Parameters:
    -----------
    start_date : str
        Start date in YYYY-MM-DD format (default: 2020-01-01)
    end_date : str or None
        End date in YYYY-MM-DD format (default: today)
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with columns: Date, Open, High, Low, Close
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"Fetching EUR/USD data from {start_date} to {end_date}...")
    
    # EUR/USD ticker on Yahoo Finance
    ticker = "EURUSD=X"
    
    try:
        # Download data
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        
        if data.empty:
            print("No data retrieved. Trying alternative method...")
            # Try with interval parameter
            data = yf.download(ticker, start=start_date, end=end_date, interval="1d", progress=False)
        
        if data.empty:
            raise ValueError("Could not retrieve data from Yahoo Finance")
        
        # Reset index to make Date a column
        data = data.reset_index()
        
        # Rename columns to match expected format
        data = data.rename(columns={
            'Date': 'Date',
            'Open': 'Open',
            'High': 'High',
            'Low': 'Low',
            'Close': 'Price',  # Yahoo Finance uses 'Close', we'll rename to 'Price' to match CSV format
        })
        
        # Select only the columns we need
        data = data[['Date', 'Price', 'Open', 'High', 'Low']].copy()
        
        # Convert Date to datetime if it isn't already
        if not pd.api.types.is_datetime64_any_dtype(data['Date']):
            data['Date'] = pd.to_datetime(data['Date'])
        
        # Sort by date (oldest first)
        data = data.sort_values('Date').reset_index(drop=True)
        
        # Remove any rows with missing data
        data = data.dropna().reset_index(drop=True)
        
        print(f"✓ Successfully fetched {len(data)} days of data")
        print(f"  Date range: {data['Date'].min()} to {data['Date'].max()}")
        
        return data
        
    except Exception as e:
        print(f"Error fetching data: {e}")
        print("\nTrying alternative data source...")
        raise


def save_data(df, filename='eur_usd_long_term.csv'):
    """Save data to CSV file in the same format as existing data."""
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    filepath = data_dir / filename
    
    # Format date as MM/DD/YYYY to match existing format
    df_output = df.copy()
    df_output['Date'] = df_output['Date'].dt.strftime('%m/%d/%Y')
    
    # Add empty columns to match original format
    df_output['Vol.'] = ''
    df_output['Change %'] = ''
    
    # Reorder columns to match original
    df_output = df_output[['Date', 'Price', 'Open', 'High', 'Low', 'Vol.', 'Change %']]
    
    # Save to CSV
    df_output.to_csv(filepath, index=False)
    
    print(f"\n✓ Data saved to: {filepath}")
    print(f"  Total rows: {len(df_output)}")
    
    return filepath


def main():
    """Main function to fetch and save historical data."""
    print("=" * 80)
    print("FETCHING LONG-TERM EUR/USD HISTORICAL DATA")
    print("=" * 80)
    print()
    
    # Options for data periods
    print("Select time period:")
    print("1. Last 1 year")
    print("2. Last 2 years")
    print("3. Last 5 years")
    print("4. Since 2020")
    print("5. Custom date range")
    
    choice = input("\nEnter choice (1-5, default=3): ").strip() or "3"
    
    end_date = datetime.now()
    
    if choice == "1":
        start_date = end_date - timedelta(days=365)
    elif choice == "2":
        start_date = end_date - timedelta(days=730)
    elif choice == "3":
        start_date = end_date - timedelta(days=1825)  # ~5 years
    elif choice == "4":
        start_date = datetime(2020, 1, 1)
    elif choice == "5":
        start_str = input("Enter start date (YYYY-MM-DD): ").strip()
        end_str = input("Enter end date (YYYY-MM-DD, or press Enter for today): ").strip()
        start_date = datetime.strptime(start_str, '%Y-%m-%d')
        if end_str:
            end_date = datetime.strptime(end_str, '%Y-%m-%d')
        else:
            end_date = datetime.now()
    else:
        start_date = end_date - timedelta(days=1825)  # Default: 5 years
    
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    try:
        # Fetch data
        df = fetch_eurusd_data(start_date=start_str, end_date=end_str)
        
        # Save data
        filename = 'eur_usd_long_term.csv'
        filepath = save_data(df, filename)
        
        print("\n" + "=" * 80)
        print("SUCCESS!")
        print("=" * 80)
        print(f"\nData saved to: {filepath}")
        print(f"\nNext steps:")
        print(f"1. Review the data: {filepath}")
        print(f"2. Update your analysis scripts to use this file")
        print(f"3. Re-run backtests to see realistic performance with longer timeframe")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nAlternative options:")
        print("1. Check internet connection")
        print("2. Try a different date range")
        print("3. Use a different data source (e.g., download manually from:")
        print("   - https://finance.yahoo.com/quote/EURUSD%3DX/history")
        print("   - https://www.investing.com/currencies/eur-usd-historical-data")


if __name__ == "__main__":
    main()

