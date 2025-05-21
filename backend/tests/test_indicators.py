import pandas as pd
import numpy as np
from modules.indicators import calculate_indicators, detect_fvg

def make_df():
    ts = pd.date_range("2021-01-01", periods=5, freq="h", tz="UTC")
    df = pd.DataFrame({
        "timestamp": [int(t.value/1e6) for t in ts],
        "open": [1,2,3,4,5],
        "high": [2,3,4,5,6],
        "low": [0.5,1.5,2.5,3.5,4.5],
        "close": [1.5,2.5,3.5,4.5,5.5],
        "volume": [10,20,30,40,50]
    })
    df["datetime"] = ts
    return df

def test_calculate_indicators():
    df = make_df()
    out = calculate_indicators(df.copy(), ema_length=3, volume_multiplier=1.5, trading_start_hour=0, trading_end_hour=23)
    for col in ["ema","atr","avg_volume","high_volume","rsi","adx","within_trading_hours"]:
        assert col in out.columns

def test_detect_fvg():
    df = make_df()
    h,l = detect_fvg(df, lookback=2, bullish=True)
    assert h == df["high"].iloc[-2]
    assert l == df["low"].iloc[-1]
