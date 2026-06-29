import backtrader as bt
import pandas as pd
from strategies.indicators import SMCICTIndicators
import config

# ============================================
# SMC/ICT + ORB HYBRID STRATEGY
# ============================================

class SMCICTORBStrategy(bt.Strategy):
    """
    Hybrid strategy combining:
    - SMC/ICT: Fair Value Gaps, Supply/Demand, Liquidity Sweeps
    - ORB: Opening Range Breakout on daily chart
    - Risk Management: 2% per trade, 1:2 R:R minimum
    """
    
    params = (
        ('fvg_lookback', config.FVG_LOOKBACK),
        ('supply_demand_lookback', config.SUPPLY_DEMAND_LOOKBACK),
        ('atr_period', config.ATR_PERIOD),
        ('atr_multiplier', config.ATR_MULTIPLIER),
        ('risk_pct', config.RISK_PER_TRADE),
        ('reward_ratio', config.MIN_REWARD_RATIO),
    )
    
    def __init__(self):
        # Add technical indicators
        self.atr = bt.indicators.ATR(self.data, period=self.params.atr_period)
        self.rsi = bt.indicators.RSI(self.data, period=14)
        self.sma_fast = bt.indicators.SimpleMovingAverage(self.data, period=20)
        self.sma_slow = bt.indicators.SimpleMovingAverage(self.data, period=50)
        
        # Track state
        self.order = None
        self.trade_entry = None
        self.trade_exit = None
        self.trades_log = []
        
        # Initialize SMC/ICT indicators with pandas
        self.smc = SMCICTIndicators()
        self.df = None
        self.fvg = None
        self.sweep = None
        self.structure = None
        
    def next(self):
        """Called for each new bar"""
        
        # Skip if we need more data
        if len(self) < 50:
            return
        
        # Build pandas dataframe from backtrader data for SMC analysis
        if len(self) % 5 == 0:  # Update every 5 bars for efficiency
            self._update_smc_indicators()
        
        # Skip if pending order
        if self.order:
            return
        
        # Get current price and signals
        current_price = self.data.close[0]
        atr_value = self.atr[0]
        
        # SIGNAL 1: Trend filter (SMA)
        trend = 1 if self.sma_fast[0] > self.sma_slow[0] else -1
        
        # SIGNAL 2: RSI filter (avoid oversold/overbought)
        rsi_ok = 30 < self.rsi[0] < 70
        
        # SIGNAL 3: Market structure (from SMC)
        structure_signal = self.structure.iloc[-1] if self.structure is not None else 0
        
        # SIGNAL 4: FVG present
        fvg_signal = self.fvg.iloc[-1] if self.fvg is not None else 0
        
        # SIGNAL 5: Liquidity sweep (confluence)
        sweep_signal = self.sweep.iloc[-1] if self.sweep is not None else 0
        
        # ============================================
        # ENTRY LOGIC: All signals align
        # ============================================
        
        # LONG ENTRY
        if (trend == 1 and rsi_ok and structure_signal == 1 and 
            (fvg_signal == 1 or sweep_signal == 1) and self.position.size == 0):
            
            # Stop loss: Recent swing low - ATR buffer
            stop_loss = self.data.low[-5:].min() - (atr_value * self.params.atr_multiplier)
            
            # Risk calculation
            risk = current_price - stop_loss
            position_size = self._calculate_position_size(risk)
            
            # Take profit: 1:2 R:R
            take_profit = current_price + (risk * self.params.reward_ratio)
            
            # Validate setup (min R:R)
            if risk > 0 and (take_profit - current_price) / risk >= self.params.reward_ratio:
                self.trade_entry = current_price
                self.order = self.buy(size=position_size)
                self.log(f'BUY {position_size:.2f} @ {current_price:.2f} | SL: {stop_loss:.2f} | TP: {take_profit:.2f}')
        
        # SHORT ENTRY
        elif (trend == -1 and rsi_ok and structure_signal == -1 and 
              (fvg_signal == -1 or sweep_signal == -1) and self.position.size == 0):
            
            # Stop loss: Recent swing high + ATR buffer
            stop_loss = self.data.high[-5:].max() + (atr_value * self.params.atr_multiplier)
            
            # Risk calculation
            risk = stop_loss - current_price
            position_size = self._calculate_position_size(risk)
            
            # Take profit: 1:2 R:R
            take_profit = current_price - (risk * self.params.reward_ratio)
            
            # Validate setup
            if risk > 0 and (current_price - take_profit) / risk >= self.params.reward_ratio:
                self.trade_entry = current_price
                self.order = self.sell(size=position_size)
                self.log(f'SELL {position_size:.2f} @ {current_price:.2f} | SL: {stop_loss:.2f} | TP: {take_profit:.2f}')
        
        # ============================================
        # EXIT LOGIC
        # ============================================
        
        if self.position.size > 0:
            # LONG EXIT
            if current_price < (self.data.low[-5:].min() - atr_value * 2):
                self.order = self.close()
                self.log(f'CLOSE LONG @ {current_price:.2f}')
        
        elif self.position.size < 0:
            # SHORT EXIT
            if current_price > (self.data.high[-5:].max() + atr_value * 2):
                self.order = self.close()
                self.log(f'CLOSE SHORT @ {current_price:.2f}')
    
    def _update_smc_indicators(self):
        """Update SMC/ICT indicators using pandas"""
        # Build recent dataframe (last 50 candles)
        n = min(50, len(self))
        
        self.df = pd.DataFrame({
            'open': [self.data.open[-n + i] for i in range(n)],
            'high': [self.data.high[-n + i] for i in range(n)],
            'low': [self.data.low[-n + i] for i in range(n)],
            'close': [self.data.close[-n + i] for i in range(n)],
            'volume': [self.data.volume[-n + i] for i in range(n)],
        })
        
        # Calculate indicators
        self.fvg = self.smc.fair_value_gap(self.df, self.params.fvg_lookback)
        self.sweep = self.smc.liquidity_sweep(self.df)
        self.structure = self.smc.market_structure(self.df)
    
    def _calculate_position_size(self, risk_amount):
        """Calculate position size based on 2% account risk"""
        account_size = self.broker.getcash()
        max_risk = account_size * self.params.risk_pct
        
        if risk_amount <= 0:
            return 0
        
        position_size = max_risk / risk_amount
        max_position = account_size * 0.1  # Max 10% of account per trade
        
        return min(position_size, max_position)
    
    def notify_order(self, order):
        """Handle order execution"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED @ {order.executed.price:.2f}')
            else:
                self.log(f'SELL EXECUTED @ {order.executed.price:.2f}')
            
            self.order = None
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('ORDER CANCELED/REJECTED')
            self.order = None
    
    def notify_trade(self, trade):
        """Log completed trades"""
        if trade.isclosed:
            pnl = trade.pnl
            pnl_pct = (pnl / (trade.price * trade.size)) * 100 if trade.size > 0 else 0
            
            trade_record = {
                'entry': trade.baropen,
                'exit': self.data.close[0],
                'entry_price': trade.price,
                'size': trade.size,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
            }
            self.trades_log.append(trade_record)
            
            self.log(f'TRADE CLOSED | PNL: {pnl:.2f} ({pnl_pct:.2f}%)')
    
    def log(self, txt):
        """Logging utility"""
        dt = self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')
    
    def stop(self):
        """Called when strategy stops"""
        print(f'\nFinal Portfolio Value: {self.broker.getvalue():.2f}')
        print(f'Total Trades: {len(self.trades_log)}')
        
        if self.trades_log:
            df_trades = pd.DataFrame(self.trades_log)
            win_rate = (df_trades['pnl'] > 0).sum() / len(df_trades) * 100
            print(f'Win Rate: {win_rate:.2f}%')
            print(f'Avg PNL: {df_trades["pnl"].mean():.2f}')
            print(f'Total PNL: {df_trades["pnl"].sum():.2f}')
