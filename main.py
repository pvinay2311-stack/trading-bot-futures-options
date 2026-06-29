import os
import sys
import argparse
from datetime import datetime
import config
from backtester.runner import BacktestRunner
from paper_trader.alpaca_connector import AlpacaPaperTrader
from strategies.smcict_orb import SMCICTORBStrategy

# ============================================
# MAIN ENTRY POINT
# ============================================

def run_backtest():
    """Run historical backtest"""
    print("\n" + "="*60)
    print("STARTING BACKTEST")
    print("="*60 + "\n")
    
    symbols = ['SPY', 'QQQ', 'GLD']  # Proxies for ES, NQ, GC
    
    for symbol in symbols:
        runner = BacktestRunner(
            symbol=symbol,
            start_date='2022-01-01',
            end_date='2024-12-31',
            initial_cash=config.STARTING_CAPITAL
        )
        
        success = runner.run(plot=False)
        
        if not success:
            print(f"Backtest failed for {symbol}")
        
        print("\n")


def run_paper_trading():
    """Run live paper trading"""
    print("\n" + "="*60)
    print("STARTING PAPER TRADING")
    print("="*60 + "\n")
    
    # Initialize trader
    trader = AlpacaPaperTrader()
    
    # Get account info
    account = trader.get_account_info()
    print(f"Account Status:")
    print(f"  Cash: ${account['cash']:,.2f}")
    print(f"  Portfolio Value: ${account['portfolio_value']:,.2f}")
    print(f"  Buying Power: ${account['buying_power']:,.2f}\n")
    
    # Get positions
    print("Current Positions:")
    positions = trader.get_positions()
    
    if not positions:
        print("  No open positions\n")
    
    # Get orders
    print("Open Orders:")
    orders = trader.get_orders('open')
    
    if not orders:
        print("  No open orders\n")
    
    # Example: Fetch market data
    print("Recent Market Data (SPY):")
    data = trader.get_market_data('SPY', timeframe='1min')
    if data is not None:
        print(data.tail(5))
        print("\n")
    
    print("✓ Paper trading session started")
    print(f"  Time: {datetime.now().isoformat()}")
    print(f"  Mode: {config.MODE}")


def main():
    parser = argparse.ArgumentParser(description='Trading Bot - Backtest & Paper Trading')
    parser.add_argument('--mode', choices=['backtest', 'paper'], 
                       default=config.MODE, help='Run mode')
    parser.add_argument('--symbol', default='SPY', help='Symbol to backtest')
    parser.add_argument('--start', default='2022-01-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', default='2024-12-31', help='End date (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    # Banner
    print("""
╔════════════════════════════════════════════════════════════════╗
║        TRADING BOT: SMC/ICT + ORB Strategy                     ║
║        Backtesting & Paper Trading Platform                    ║
║        Powered by Backtrader, Alpaca, yfinance                 ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    if args.mode == 'backtest':
        run_backtest()
    
    elif args.mode == 'paper':
        run_paper_trading()
    
    else:
        print("Invalid mode. Choose 'backtest' or 'paper'")
        sys.exit(1)


if __name__ == '__main__':
    main()
