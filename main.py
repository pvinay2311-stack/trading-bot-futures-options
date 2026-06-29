import os
import sys
from datetime import datetime
from paper_trader.alpaca_connector import AlpacaPaperTrader
import config

print(f"\n{'='*60}")
print(f"TRADING BOT STARTED")
print(f"{'='*60}")
print(f"Time: {datetime.now()}")
print(f"Mode: {config.MODE}")

# Initialize trader
try:
    trader = AlpacaPaperTrader()
    
    # Get account info
    account = trader.get_account_info()
    print(f"\nAccount Status:")
    print(f"  Cash: ${account['cash']:,.2f}")
    print(f"  Portfolio: ${account['portfolio_value']:,.2f}")
    print(f"  Buying Power: ${account['buying_power']:,.2f}")
    
    # Get positions
    positions = trader.get_positions()
    
    # Get open orders
    orders = trader.get_orders('open')
    
    print(f"\n✓ Bot is running and monitoring...")
    
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)

print(f"\n{'='*60}")
