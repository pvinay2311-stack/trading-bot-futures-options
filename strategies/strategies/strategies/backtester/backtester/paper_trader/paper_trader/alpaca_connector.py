import alpaca_trade_api as tradeapi
import pandas as pd
import json
import os
from datetime import datetime
import config

# ============================================
# ALPACA PAPER TRADING CONNECTOR
# ============================================

class AlpacaPaperTrader:
    """
    Live paper trading via Alpaca's free paper trading API
    No commission, real-time market data, live order execution
    """
    
    def __init__(self, api_key=None, secret_key=None):
        self.api_key = api_key or config.ALPACA_API_KEY
        self.secret_key = secret_key or config.ALPACA_SECRET_KEY
        self.base_url = config.ALPACA_BASE_URL
        
        # Initialize API connection
        self.api = tradeapi.REST(
            self.api_key,
            self.secret_key,
            self.base_url
        )
        
        self.account = None
        self.positions = []
        self.trades_log = []
        
        # Verify connection
        self._verify_connection()
    
    def _verify_connection(self):
        """Verify API credentials work"""
        try:
            self.account = self.api.get_account()
            print(f"✓ Connected to Alpaca")
            print(f"  Account: {self.account.account_number}")
            print(f"  Buying Power: ${float(self.account.buying_power):,.2f}")
            print(f"  Portfolio Value: ${float(self.account.portfolio_value):,.2f}\n")
            return True
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
    
    def get_account_info(self):
        """Get current account status"""
        self.account = self.api.get_account()
        
        return {
            'cash': float(self.account.cash),
            'portfolio_value': float(self.account.portfolio_value),
            'buying_power': float(self.account.buying_power),
            'multiplier': float(self.account.multiplier),
            'equity': float(self.account.equity),
            'daytrading_buying_power': float(self.account.daytrading_buying_power),
        }
    
    def get_market_data(self, symbol, timeframe='1min'):
        """Fetch recent OHLCV data"""
        try:
            barset = self.api.get_barset(symbol, timeframe, limit=100)
            bars = barset.get(symbol)
            
            if not bars:
                print(f"No data for {symbol}")
                return None
            
            df = pd.DataFrame([{
                'time': bar.t,
                'open': bar.o,
                'high': bar.h,
                'low': bar.l,
                'close': bar.c,
                'volume': bar.v,
            } for bar in bars])
            
            return df
        
        except Exception as e:
            print(f"Error fetching market data: {e}")
            return None
    
    def submit_order(self, symbol, qty, side, order_type='market', limit_price=None, 
                     stop_price=None, trail_percent=None):
        """
        Submit order to Alpaca
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            qty: Quantity
            side: 'buy' or 'sell'
            order_type: 'market', 'limit', 'stop', 'trailing_stop'
            limit_price: Price for limit orders
            stop_price: Price for stop orders
            trail_percent: Trail percent for trailing stops (e.g., 5 for 5%)
        """
        try:
            if order_type == 'market':
                order = self.api.submit_order(
                    symbol=symbol,
                    qty=qty,
                    side=side,
                    type='market',
                    time_in_force='day'
                )
            
            elif order_type == 'limit':
                order = self.api.submit_order(
                    symbol=symbol,
                    qty=qty,
                    side=side,
                    type='limit',
                    limit_price=limit_price,
                    time_in_force='day'
                )
            
            elif order_type == 'stop':
                order = self.api.submit_order(
                    symbol=symbol,
                    qty=qty,
                    side=side,
                    type='stop',
                    stop_price=stop_price,
                    time_in_force='day'
                )
            
            elif order_type == 'trailing_stop':
                order = self.api.submit_order(
                    symbol=symbol,
                    qty=qty,
                    side=side,
                    type='trailing_stop',
                    trail_percent=trail_percent,
                    time_in_force='day'
                )
            
            print(f"✓ Order submitted: {side.upper()} {qty} {symbol} @ {order_type}")
            return order
        
        except Exception as e:
            print(f"✗ Order failed: {e}")
            return None
    
    def close_position(self, symbol):
        """Close existing position in a symbol"""
        try:
            position = self.api.get_position(symbol)
            qty = int(position.qty)
            
            if qty == 0:
                print(f"No position in {symbol}")
                return None
            
            side = 'sell' if qty > 0 else 'buy'
            order = self.api.submit_order(
                symbol=symbol,
                qty=abs(qty),
                side=side,
                type='market',
                time_in_force='day'
            )
            
            print(f"✓ Closed {symbol} position")
            return order
        
        except Exception as e:
            print(f"Error closing position: {e}")
            return None
    
    def get_positions(self):
        """Get all open positions"""
        try:
            positions = self.api.list_positions()
            self.positions = positions
            
            print(f"\nOpen Positions ({len(positions)}):")
            print("-" * 60)
            
            for pos in positions:
                pnl = float(pos.unrealized_pl)
                pnl_pct = float(pos.unrealized_plpc) * 100
                
                print(f"{pos.symbol}: {pos.qty} shares")
                print(f"  Entry: ${float(pos.avg_fill_price):.2f}")
                print(f"  Current: ${float(pos.current_price):.2f}")
                print(f"  PNL: ${pnl:.2f} ({pnl_pct:.2f}%)\n")
            
            return positions
        
        except Exception as e:
            print(f"Error fetching positions: {e}")
            return []
    
    def get_orders(self, status='all'):
        """
        Get orders
        
        Args:
            status: 'open', 'closed', 'all'
        """
        try:
            orders = self.api.list_orders(status=status)
            
            print(f"\nOrders ({status.upper()}):")
            print("-" * 60)
            
            for order in orders:
                print(f"{order.symbol}: {order.side.upper()} {order.qty} @ {order.order_type}")
                print(f"  Status: {order.status}")
                print(f"  Created: {order.created_at}\n")
            
            return orders
        
        except Exception as e:
            print(f"Error fetching orders: {e}")
            return []
    
    def cancel_order(self, order_id):
        """Cancel an open order"""
        try:
            self.api.cancel_order(order_id)
            print(f"✓ Order {order_id} cancelled")
            return True
        except Exception as e:
            print(f"Error cancelling order: {e}")
            return False
    
    def log_trade(self, symbol, entry_price, exit_price, qty, side, pnl, pnl_pct):
        """Log completed trade"""
        trade = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'side': side,
            'qty': qty,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
        }
        
        self.trades_log.append(trade)
        
        # Save to file
        os.makedirs('results', exist_ok=True)
        with open('results/trades.json', 'a') as f:
            f.write(json.dumps(trade) + '\n')
    
    def get_portfolio_stats(self):
        """Calculate portfolio stats"""
        if not self.trades_log:
            print("No trades yet")
            return None
        
        df = pd.DataFrame(self.trades_log)
        
        stats = {
            'total_trades': len(df),
            'winning_trades': (df['pnl'] > 0).sum(),
            'losing_trades': (df['pnl'] < 0).sum(),
            'win_rate_pct': (df['pnl'] > 0).sum() / len(df) * 100,
            'total_pnl': df['pnl'].sum(),
            'avg_pnl': df['pnl'].mean(),
            'max_win': df['pnl'].max(),
            'max_loss': df['pnl'].min(),
            'profit_factor': abs(df[df['pnl'] > 0]['pnl'].sum() / df[df['pnl'] < 0]['pnl'].sum()) if len(df[df['pnl'] < 0]) > 0 else 0,
        }
        
        return stats


def demo_paper_trading():
    """Demo: Connect and fetch account info"""
    
    trader = AlpacaPaperTrader()
    
    # Get account info
    account = trader.get_account_info()
    print(f"Account Stats:")
    print(f"  Cash: ${account['cash']:,.2f}")
    print(f"  Portfolio: ${account['portfolio_value']:,.2f}")
    print(f"  Buying Power: ${account['buying_power']:,.2f}\n")
    
    # Get positions
    trader.get_positions()
    
    # Get open orders
    trader.get_orders('open')


if __name__ == '__main__':
    demo_paper_trading()
