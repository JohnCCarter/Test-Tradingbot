import asyncio
import logging
from config_loader import load_config
from modules.utils import retry, ensure_paper_trading_symbol
from modules.orders import init_exchange, place_order
from modules.indicators import calculate_indicators, detect_fvg

def setup_logger():
    logger = logging.getLogger("tradingbot")
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    return logger

async def main():
    log = setup_logger()
    config = load_config()
    exchange = init_exchange(
        api_key=config.API_KEY,
        api_secret=config.API_SECRET,
        exchange_name=config.EXCHANGE
    )
    log.info("Tradingbot startad (stub).")
    import pandas as pd

    # 1) Hämta senaste OHLCV
    log.info(f"Hämtar {config.LIMIT} candles för {config.SYMBOL} på {config.TIMEFRAME}")
    ohlcv = exchange.fetch_ohlcv(config.SYMBOL, config.TIMEFRAME, config.LIMIT)

    # 2) Bygg DataFrame
    df = pd.DataFrame(ohlcv, columns=["timestamp","open","high","low","close","volume"])
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)

    # 3) Beräkna indikatorer
    data = calculate_indicators(
        df,
        config.EMA_LENGTH,
        config.VOLUME_MULTIPLIER,
        config.TRADING_START_HOUR,
        config.TRADING_END_HOUR
    )

    # 4) Detektera FVG på lookback och plocka sista raden
    bull_high, bull_low = detect_fvg(data, config.LOOKBACK, bullish=True)
    last = data.iloc[-1]

    # 5) Enkel köp‐signal
    if (
        not pd.isna(bull_high)
        and last["close"] < bull_low
        and last["close"] > last["ema"]
        and last["high_volume"]
        and last["within_trading_hours"]
    ):
        log.info(f"Köp‐signal! Close={last['close']:.2f} < bull_low={bull_low:.2f}")
        place_order("buy", config.SYMBOL, amount=0.001)

    # (sov en sekund innan avslut/fortsättning)
    await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
