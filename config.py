import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# ALPACA PAPER TRADING (FREE)
# ============================================
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "YOUR_API_KEY_HERE")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "YOUR_SECRET_KEY_HERE")
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"  # Paper trading endpoint

# ============================================
# STRATEGY PARAMETERS
# ============================================
STARTING_CAPITAL = 100000  # Paper trading capital
RISK_PER_TRADE = 0.02  # 2% risk per trade
MIN_REWARD_RATIO = 2.0  # 1:2 risk:reward minimum
POSITION_SIZE_PCT = 0.05  # 5% position per trade

# ============================================
# ASSETS TO TRADE
# ============================================
SYMBOLS = {
    "equities": ["SPY", "QQQ", "NVDA"],
    "forex": ["EURUSD", "GBPUSD"],
    "crypto": ["BTC/USD", "ETH/USD"],
}

# ============================================
# TIMEFRAMES
# ============================================
TIMEFRAMES = {
    "daily": "1d",
    "4hour": "4h",
    "1hour": "1h",
    "15min": "15m",
}

PRIMARY_TF = "4h"
CONFIRMATION_TF = "1h"

# ============================================
# SMC/ICT STRATEGY PARAMETERS
# ============================================
FVG_LOOKBACK = 4
SUPPLY_DEMAND_LOOKBACK = 20
ATR_PERIOD = 14
ATR_MULTIPLIER = 2.0

# ORB Parameters
ORB_LOOKBACK_DAYS = 1
ORB_BREAKOUT_PERCENT = 0.005

# ============================================
# BACKTEST SETTINGS
# ============================================
BACKTEST_START_DATE = "2021-01-01"
BACKTEST_END_DATE = "2024-12-31"
BACKTEST_COMMISSION = 0.001
BACKTEST_SLIPPAGE = 0.0005

# ============================================
# NOTIFICATIONS
# ============================================
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
EMAIL_ALERTS = False
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")

# ============================================
# LOGGING
# ============================================
LOG_LEVEL = "INFO"
LOG_FILE = "logs/trading_bot.log"

# ============================================
# MODE: "backtest" or "paper_trade"
# ============================================
MODE = os.getenv("MODE", "backtest")
