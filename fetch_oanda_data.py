"""
Quick script to fetch EUR/USD data from OANDA API.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.oanda_api import OandaAPI, save_oanda_data

# Your OANDA API token
API_TOKEN = "965884e308ff2a75fcf9a5011a2cc39a-616820942fc0746b78b04062b603c20d"

if __name__ == "__main__":
    from src.oanda_api import main
    main()

