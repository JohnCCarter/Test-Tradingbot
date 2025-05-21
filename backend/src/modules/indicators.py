import pandas as pd
import numpy as np
import talib

def calculate_indicators(
    df: pd.DataFrame,
    ema_length: int,
    volume_multiplier: float,
    trading_start_hour: int,
    trading_end_hour: int
) -> pd.DataFrame:
    """
    Add EMA, ATR, avg_volume, high_volume, RSI, ADX, and within_trading_hours
    columns to the DataFrame.
    """
    df = df.copy()
    df["ema"] = talib.EMA(df["close"].astype(float), timeperiod=ema_length)
    atr_period = min(14, len(df))
    high_low = df["high"] - df["low"]
    high_pc = (df["high"] - df["close"].shift()).abs()
    low_pc = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_pc, low_pc], axis=1).max(axis=1)
    df["atr"] = tr.rolling(window=atr_period, min_periods=1).mean()
    df["avg_volume"] = df["volume"].rolling(window=20, min_periods=1).mean()
    df["high_volume"] = df["volume"] > df["avg_volume"] * volume_multiplier
    df["rsi"] = talib.RSI(df["close"], timeperiod=min(14, max(1, len(df)-1))).fillna(0)
    df["adx"] = talib.ADX(df["high"], df["low"], df["close"], timeperiod=min(14, max(1, len(df)-1))).fillna(0)
    df["hour"] = pd.to_datetime(df["datetime"]).dt.hour
    df["within_trading_hours"] = df["hour"].between(trading_start_hour, trading_end_hour)
    return df

def detect_fvg(
    df: pd.DataFrame,
    lookback: int,
    bullish: bool = True
) -> tuple[float, float]:
    """
    Detect Fair Value Gap (FVG) high/low for bullish or bearish case.
    """
    if len(df) < 2:
        return np.nan, np.nan
    if bullish:
        return df["high"].iloc[-2], df["low"].iloc[-1]
    return df["high"].iloc[-1], df["low"].iloc[-2]

def calculate_ema(series, period):
    """Beräkna EMA för en given serie och period."""
    arr = np.array(series, dtype=float)
    return talib.EMA(arr, timeperiod=period)

def calculate_rsi(series, period):
    """Beräkna RSI för en given serie och period."""
    arr = np.array(series, dtype=float)
    return talib.RSI(arr, timeperiod=period)
