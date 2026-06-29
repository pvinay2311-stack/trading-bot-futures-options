import backtrader as bt
import pandas as pd
import yfinance as yf
import os
from datetime import datetime
import json
from strategies.smcict_orb import SMCICTORBStrategy
import config

# ============================================
# BACKTEST RUNNER
# ============================================

class BacktestRunner:
    """
    Runs backtests on historical data and generates reports
    """
    
    def __init__(self, symbol, start_date, end_date, initial_cash=100000):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.initial_cash = initial_cash
        self.cerebro = None
        self.results = None
        self.portfolio_stats = None
        
        # Create results directory
        os.makedirs('results/backtest_reports', exist_ok=True)
    
    def fetch_data(self, interval='1d'):
        """Download historical data from yfinance"""
        print(f"Fetching {self.symbol} data from {self.start_date} to {self.end_date}...")
        
        try:
            df = yf.download(
                self.symbol,
                start=self.start_date,
                end=self.end_date,
                interval=interval,
                progress=False
            )
            
            # Validate data
            if df.empty:
                raise ValueError(f"No data fetched for {self.symbol}")
            
            # Rename columns for backtrader
            df.columns = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
            df.index.name = 'Date'
            
            print(f"✓ Downloaded {len(df)} bars of data")
            return df
        
        except Exception as e:
            print(f"✗ Error fetching data: {e}")
            return None
    
    def run(self, plot=False):
        """Execute backtest"""
        # Setup Cerebro engine
        self.cerebro = bt.Cerebro()
        
        # Set initial cash
        self.cerebro.broker.setcash(self.initial_cash)
        
        # Set commission (realistic for futures/options)
        self.cerebro.broker.setcommission(commission=config.BACKTEST_COMMISSION)
        
        # Add strategy
        self.cerebro.addstrategy(SMCICTORBStrategy)
        
        # Fetch and add data
        df = self.fetch_data(interval='1d')
        if df is None:
            return False
        
        # Create backtrader data feed
        data = bt.feeds.PandasData(dataname=df)
        self.cerebro.adddata(data)
        
        # Run backtest
        print("Running backtest...")
        self.results = self.cerebro.run()
        
        # Generate report
        self._generate_report()
        
        # Plot if requested
        if plot:
            try:
                self.cerebro.plot()
            except:
                print("Plotting not available in this environment")
        
        return True
    
    def _generate_report(self):
        """Generate performance report"""
        final_value = self.cerebro.broker.getvalue()
        
        # Calculate metrics
        start_value = self.initial_cash
        total_return = (final_value - start_value) / start_value * 100
        
        print("\n" + "="*60)
        print(f"BACKTEST REPORT: {self.symbol}")
        print("="*60)
        print(f"Period: {self.start_date} to {self.end_date}")
        print(f"Initial Capital: ${start_value:,.2f}")
        print(f"Final Portfolio: ${final_value:,.2f}")
        print(f"Total Return: {total_return:.2f}%")
        print("="*60 + "\n")
        
        # Save report
        report = {
            'symbol': self.symbol,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'initial_capital': start_value,
            'final_value': final_value,
            'total_return_pct': total_return,
            'timestamp': datetime.now().isoformat(),
        }
        
        # Save to JSON
        report_path = f'results/backtest_reports/{self.symbol}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✓ Report saved to {report_path}\n")


def run_multi_symbol_backtest():
    """Run backtest across multiple symbols"""
    
    symbols = {
        'SPY': '2021-01-01',
        'QQQ': '2021-01-01',
        'GLD': '2021-01-01',
    }
    
    results_summary = []
    
    for symbol, start_date in symbols.items():
        runner = BacktestRunner(
            symbol=symbol,
            start_date=start_date,
            end_date='2024-12-31',
            initial_cash=config.STARTING_CAPITAL
        )
        
        if runner.run(plot=False):
            results_summary.append({
                'symbol': symbol,
                'status': 'Success',
            })
        else:
            results_summary.append({
                'symbol': symbol,
                'status': 'Failed',
            })
    
    # Print summary
    print("\n" + "="*60)
    print("BACKTEST SUMMARY")
    print("="*60)
    for result in results_summary:
        print(f"{result['symbol']}: {result['status']}")
    print("="*60 + "\n")


if __name__ == '__main__':
    # Run single symbol backtest
    runner = BacktestRunner(
        symbol='SPY',
        start_date='2022-01-01',
        end_date='2024-12-31',
        initial_cash=config.STARTING_CAPITAL
    )
    
    runner.run(plot=False)
