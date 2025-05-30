"""
Indicator calculation functions for trading bot.
Adds EMA, ATR, volume, RSI, ADX, and trading hours columns.
"""

import numpy as np
import pandas as pd
import ta
from ta.momentum import RSIIndicator
from ta.trend import ADXIndicator, EMAIndicator
from ta.volatility import AverageTrueRange


def calculate_indicators(
    df: pd.DataFrame,
    ema_length: int,
    volume_multiplier: float,
    trading_start_hour: int,
    trading_end_hour: int,
) -> pd.DataFrame:
    """
    Adds EMA, ATR, avg_volume, high_volume, RSI, ADX, and within_trading_hours.
    """
    df = df.copy()
    df["ema"] = EMAIndicator(df["close"], window=ema_length).ema_indicator()
    df["atr"] = AverageTrueRange(
        df["high"], df["low"], df["close"]
    ).average_true_range()
    df["avg_volume"] = df["volume"].rolling(window=ema_length, min_periods=1).mean()
    df["high_volume"] = df["volume"] > (df["avg_volume"] * volume_multiplier)
    df["rsi"] = RSIIndicator(df["close"], window=14).rsi()
    df["adx"] = ADXIndicator(df["high"], df["low"], df["close"], window=14).adx()
    df["within_trading_hours"] = df["timestamp"].dt.hour.between(
        trading_start_hour, trading_end_hour
    )
    return df


def detect_fvg(
    df: pd.DataFrame, lookback: int, bullish: bool = True
) -> tuple[float, float]:
    """
    Detects fair value gap (FVG) in the last lookback bars.
    Returns (low, high) for bullish, (high, low) for bearish.
    """
    if len(df) < lookback + 2:
        return (np.nan, np.nan)
    window = df.iloc[-(lookback + 2) :]
    if bullish:
        low = window["low"].min()
        high = window["high"].max()
        return (low, high)
    else:
        high = window["high"].max()
        low = window["low"].min()
        return (high, low)


def calculate_ema(series: pd.Series, window: int) -> pd.Series:
    """
    Calculates EMA for a pandas Series.
    """
    return EMAIndicator(series, window=window).ema_indicator()


def calculate_rsi(series: pd.Series, window: int) -> pd.Series:
    """
    Calculates RSI for a pandas Series.
    """
    return RSIIndicator(series, window=window).rsi()
