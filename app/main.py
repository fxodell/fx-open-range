"""
Main application entry point for automated OANDA trading.
"""

import sys
import argparse
import signal
from pathlib import Path

# Add parent directory to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config.settings import Settings
from app.utils.oanda_client import OandaTradingClient
from app.trading_engine import TradingEngine


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n\n⚠️  Interrupted by user. Shutting down gracefully...")
    sys.exit(0)


def main():
    """Main application entry point."""
    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Automated OANDA Trading Application")
    parser.add_argument(
        "--mode",
        choices=["practice", "live"],
        default="practice" if Settings.OANDA_PRACTICE_MODE else "live",
        help="Trading mode (default: practice)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (don't loop)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Check interval in seconds (default: 60)"
    )
    parser.add_argument(
        "--close-all",
        action="store_true",
        help="Close all open positions and exit"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show account status and exit"
    )
    
    args = parser.parse_args()
    
    # Print header
    print("=" * 80)
    print("AUTOMATED OANDA TRADING APPLICATION")
    print("Strategy: Price Trend (SMA20) Directional")
    print("=" * 80)
    print()
    
    # Update practice mode based on argument
    practice_mode = (args.mode == "practice")
    if not practice_mode:
        response = input("⚠️  LIVE MODE - This will trade with REAL MONEY! Continue? (yes/no): ")
        if response.lower() != "yes":
            print("Exiting...")
            return
    
    # Print settings
    Settings.OANDA_PRACTICE_MODE = practice_mode
    Settings.print_settings()
    print()
    
    try:
        # Initialize OANDA client
        print("Connecting to OANDA API...")
        client = OandaTradingClient(
            api_token=Settings.OANDA_API_TOKEN,
            account_id=Settings.OANDA_ACCOUNT_ID,
            practice=practice_mode
        )
        
        # Test connection
        account_info = client.get_account_info()
        print(f"✓ Connected successfully")
        print(f"  Account ID: {account_info['id']}")
        print(f"  Currency: {account_info['currency']}")
        print(f"  Account Name: {account_info.get('tags', [{}])[0].get('name', 'N/A') if account_info.get('tags') else 'N/A'}")
        print()
        
        # Handle special commands
        if args.close_all:
            print("Closing all open positions...")
            result = client.close_all_trades(instrument=Settings.INSTRUMENT)
            print(f"Result: {result}")
            return
        
        if args.status:
            print("Account Status:")
            print("-" * 80)
            summary = client.get_account_summary()
            print(f"Balance: {summary['balance']} {summary['currency']}")
            print(f"Unrealized P/L: {summary['unrealizedPL']} {summary['currency']}")
            print(f"Margin Used: {summary['marginUsed']} {summary['currency']}")
            print(f"Margin Available: {summary['marginAvailable']} {summary['currency']}")
            print()
            
            open_trades = client.get_open_trades()
            print(f"Open Trades: {len(open_trades)}")
            for trade in open_trades:
                print(f"  - {trade['instrument']}: {trade['currentUnits']} units, "
                      f"P/L: {trade['unrealizedPL']} {summary['currency']}")
            print()
            
            open_positions = client.get_open_positions()
            print(f"Open Positions: {len(open_positions)}")
            for pos in open_positions:
                print(f"  - {pos['instrument']}: {pos['long']['units']} long, "
                      f"{pos['short']['units']} short")
            return
        
        # Initialize trading engine
        engine = TradingEngine(client)
        
        # Run trading
        if args.once:
            print("Running once...")
            engine.run_once()
            print("Done.")
        else:
            print(f"Starting continuous trading (check every {args.interval} seconds)...")
            print("Press Ctrl+C to stop\n")
            engine.run_continuous(check_interval_seconds=args.interval)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Exiting...")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

