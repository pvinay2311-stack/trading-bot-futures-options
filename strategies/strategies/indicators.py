import pandas as pd
import numpy as np
from typing import Tuple, List, Dict

# ============================================
# SMC/ICT INDICATOR LIBRARY
# ============================================

class SMCICTIndicators:
    """
    Supply/Demand, FVG, Liquidity, and Market Structure indicators
    for Smart Money Concepts / ICT methodology
    """

    @staticmethod
    def fair_value_gap(df: pd.DataFrame, lookback: int = 4) -> pd.Series:
        """
        Detect Fair Value Gaps (FVG) - 4-candle pattern
        FVG: Gap between high of candle N and low of candle N+2
        (candle N+1 is the gap candle)
        
        Returns:
            pd.Series: 1 = Bullish FVG, -1 = Bearish FVG, 0 = No FVG
        """
        fvg = pd.Series(0, index=df.index)
        
        for i in range(2, len(df) - 2):
            # Bullish FVG: Low of (i) > High of (i-2)
            if df['low'].iloc[i] > df['high'].iloc[i - 2]:
                fvg.iloc[i] = 1  # Bullish
            
            # Bearish FVG: High of (i) < Low of (i-2)
            elif df['high'].iloc[i] < df['low'].iloc[i - 2]:
                fvg.iloc[i] = -1  # Bearish
        
        return fvg

    @staticmethod
    def supply_demand_zones(df: pd.DataFrame, lookback: int = 20, threshold: float = 1.5) -> Dict[str, List[Tuple]]:
        """
        Identify Supply (resistance) and Demand (support) zones
        Based on: Swing highs/lows + volume confirmation
        
        Returns:
            Dict with 'supply' and 'demand' zones as (price_level, strength) tuples
        """
        zones = {"supply": [], "demand": []}
        
        high = df['high'].rolling(lookback).max()
        low = df['low'].rolling(lookback).min()
        volume = df['volume']
        
        for i in range(lookback, len(df)):
            # Demand zone: Low + volume spike
            if df['low'].iloc[i] == low.iloc[i] and volume.iloc[i] > volume.mean():
                zones["demand"].append((df['low'].iloc[i], volume.iloc[i] / volume.mean()))
            
            # Supply zone: High + volume spike
            if df['high'].iloc[i] == high.iloc[i] and volume.iloc[i] > volume.mean():
                zones["supply"].append((df['high'].iloc[i], volume.iloc[i] / volume.mean()))
        
        # Remove duplicates (merge nearby zones)
        zones["supply"] = SMCICTIndicators._merge_zones(zones["supply"], threshold)
        zones["demand"] = SMCICTIndicators._merge_zones(zones["demand"], threshold)
        
        return zones

    @staticmethod
    def _merge_zones(zones: List[Tuple], threshold: float) -> List[Tuple]:
        """Merge zones that are within threshold% of each other"""
        if not zones:
            return []
        
        zones = sorted(zones, key=lambda x: x[0])
        merged = [zones[0]]
        
        for zone in zones[1:]:
            pct_diff = abs(zone[0] - merged[-1][0]) / merged[-1][0]
            if pct_diff < threshold / 100:
                # Average the levels, combine strength
                avg_level = (merged[-1][0] + zone[0]) / 2
                combined_strength = merged[-1][1] + zone[1]
                merged[-1] = (avg_level, combined_strength)
            else:
                merged.append(zone)
        
        return merged

    @staticmethod
    def liquidity_sweep(df: pd.DataFrame, lookback: int = 20) -> pd.Series:
        """
        Detect liquidity sweeps (break of recent high/low + reversal)
        Sweep = Price breaks previous N candles' extreme, then reverses
        
        Returns:
            pd.Series: 1 = Bullish sweep (below demand swept up), 
                      -1 = Bearish sweep (above supply swept down)
        """
        sweep = pd.Series(0, index=df.index)
        recent_high = df['high'].rolling(lookback).max()
        recent_low = df['low'].rolling(lookback).min()
        
        for i in range(lookback + 1, len(df)):
            # Bullish sweep: Price breaks below recent low, then closes above
            if (df['low'].iloc[i] < recent_low.iloc[i - 1] and 
                df['close'].iloc[i] > recent_low.iloc[i - 1]):
                sweep.iloc[i] = 1
            
            # Bearish sweep: Price breaks above recent high, then closes below
            elif (df['high'].iloc[i] > recent_high.iloc[i - 1] and 
                  df['close'].iloc[i] < recent_high.iloc[i - 1]):
                sweep.iloc[i] = -1
        
        return sweep

    @staticmethod
    def market_structure(df: pd.DataFrame) -> pd.Series:
        """
        Market Structure Analysis: Higher Highs/Lows (uptrend) vs Lower Highs/Lows (downtrend)
        
        Returns:
            pd.Series: 1 = Uptrend (HH/HL), -1 = Downtrend (LH/LL), 0 = Undefined
        """
        structure = pd.Series(0, index=df.index)
        
        for i in range(2, len(df)):
            # Check for Higher High / Higher Low (uptrend)
            if df['high'].iloc[i] > df['high'].iloc[i - 2] and df['low'].iloc[i] > df['low'].iloc[i - 2]:
                structure.iloc[i] = 1
            
            # Check for Lower High / Lower Low (downtrend)
            elif df['high'].iloc[i] < df['high'].iloc[i - 2] and df['low'].iloc[i] < df['low'].iloc[i - 2]:
                structure.iloc[i] = -1
        
        return structure

    @staticmethod
    def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Average True Range for volatility"""
        tr = pd.Series(0.0, index=df.index)
        
        tr.iloc[0] = df['high'].iloc[0] - df['low'].iloc[0]
        for i in range(1, len(df)):
            tr.iloc[i] = max(
                df['high'].iloc[i] - df['low'].iloc[i],
                abs(df['high'].iloc[i] - df['close'].iloc[i - 1]),
                abs(df['low'].iloc[i] - df['close'].iloc[i - 1])
            )
        
        return tr.rolling(period).mean()

    @staticmethod
    def opening_range_breakout(df: pd.DataFrame, session_start_hour: int = 9, 
                               session_end_hour: int = 11, breakout_pct: float = 0.005) -> pd.Series:
        """
        Opening Range Breakout (ORB) strategy
        Identifies range formed in first 2 hours, alerts on breakout
        
        Args:
            session_start_hour: Start of session (9 = 9 AM)
            session_end_hour: End of range (11 = 11 AM)
            breakout_pct: Breakout threshold (0.5% = 0.005)
        
        Returns:
            pd.Series: 1 = Bullish breakout, -1 = Bearish breakout, 0 = No setup
        """
        df_copy = df.copy()
        df_copy['hour'] = pd.to_datetime(df_copy.index).hour if isinstance(df_copy.index, pd.DatetimeIndex) else 0
        
        orb_signal = pd.Series(0, index=df.index)
        
        for day in df_copy['date'].unique() if 'date' in df_copy.columns else [None]:
            # Get candles in range
            mask = (df_copy['hour'] >= session_start_hour) & (df_copy['hour'] < session_end_hour)
            range_candles = df_copy[mask]
            
            if len(range_candles) == 0:
                continue
            
            range_high = range_candles['high'].max()
            range_low = range_candles['low'].min()
            range_width = range_high - range_low
            
            # Find breakout threshold
            bullish_breakout = range_high + (range_width * breakout_pct)
            bearish_breakout = range_low - (range_width * breakout_pct)
            
            # Mark breakouts in rest of day
            post_range = df_copy[df_copy['hour'] >= session_end_hour]
            for idx, row in post_range.iterrows():
                if row['high'] > bullish_breakout:
                    orb_signal.loc[idx] = 1
                elif row['low'] < bearish_breakout:
                    orb_signal.loc[idx] = -1
        
        return orb_signal

    @staticmethod
    def confluence_score(df: pd.DataFrame, fvg: pd.Series, sweep: pd.Series, 
                        structure: pd.Series) -> pd.Series:
        """
        Confluence scoring: How many SMC signals align?
        
        Returns:
            pd.Series: Score 0-3 (higher = stronger setup)
        """
        score = pd.Series(0, index=df.index)
        
        # FVG point: +1 if present
        score += (fvg != 0).astype(int)
        
        # Liquidity sweep: +1 if present
        score += (sweep != 0).astype(int)
        
        # Market structure: +1 if strong direction
        score += (structure != 0).astype(int)
        
        return score
