import os
from datetime import datetime
from paper_trader.alpaca_connector import AlpacaPaperTrader

print(f"\n{'='*60}")
print(f"TRADING BOT STARTED - {datetime.now()}")
print(f"{'='*60}")

try:
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    
    trader = AlpacaPaperTrader(api_key, secret_key)
    
    account = trader.get_account_info()
    print(f"✓ BOT RUNNING")
    print(f"  Cash: ${account['cash']:,.2f}")
    print(f"  Portfolio: ${account['portfolio_value']:,.2f}")
    
except Exception as e:
    print(f"Error: {e}")

print(f"{'='*60}")
