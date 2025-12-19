"""
Quick test script to verify the trading app is working.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.config.settings import Settings
from app.utils.oanda_client import OandaTradingClient
from app.strategies.sma20_strategy import get_current_signal


def test_connection():
    """Test OANDA API connection."""
    print("Testing OANDA API connection...")
    
    try:
        client = OandaTradingClient(
            api_token=Settings.OANDA_API_TOKEN,
            practice=Settings.OANDA_PRACTICE_MODE
        )
        
        account_info = client.get_account_info()
        print(f"✓ Connected successfully")
        print(f"  Account ID: {account_info['id']}")
        print(f"  Currency: {account_info['currency']}")
        
        # Get account summary
        summary = client.get_account_summary()
        print(f"  Balance: {summary['balance']} {summary['currency']}")
        print(f"  Unrealized P/L: {summary['unrealizedPL']} {summary['currency']}")
        
        return client
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return None


def test_market_data(client: OandaTradingClient):
    """Test fetching market data."""
    print("\nTesting market data fetch...")
    
    try:
        df = client.fetch_candles(
            instrument=Settings.INSTRUMENT,
            granularity="D",
            count=30
        )
        
        print(f"✓ Fetched {len(df)} candles")
        print(f"  Date range: {df['Date'].min()} to {df['Date'].max()}")
        print(f"\nLast 5 candles:")
        print(df[['Date', 'Close']].tail())
        
        return df
        
    except Exception as e:
        print(f"✗ Market data fetch failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_strategy(candles_df):
    """Test strategy signal generation."""
    print("\nTesting strategy signal...")
    
    try:
        signal, price, sma = get_current_signal(candles_df, Settings.SMA_PERIOD)
        
        print(f"✓ Signal generated")
        print(f"  Signal: {signal}")
        print(f"  Current Price: {price:.5f}" if price else "  Current Price: N/A")
        print(f"  SMA20: {sma:.5f}" if sma else "  SMA20: N/A")
        
        return signal
        
    except Exception as e:
        print(f"✗ Strategy test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run all tests."""
    print("=" * 80)
    print("TRADING APP TEST")
    print("=" * 80)
    print()
    
    Settings.print_settings()
    print()
    
    # Test connection
    client = test_connection()
    if not client:
        return
    
    # Test market data
    df = test_market_data(client)
    if df is None or len(df) < Settings.SMA_PERIOD:
        print(f"\n⚠️  Insufficient data for strategy test (need {Settings.SMA_PERIOD} candles)")
        return
    
    # Test strategy
    signal = test_strategy(df)
    
    print("\n" + "=" * 80)
    print("✓ All tests completed")
    print("=" * 80)


if __name__ == "__main__":
    main()

