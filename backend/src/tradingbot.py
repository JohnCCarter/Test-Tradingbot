"""
Main trading bot entrypoint and TradingBot class.
Loads config, initializes exchange, runs trading loop.
"""

import asyncio
import logging

import pandas as pd

from .config_loader import load_config
from .modules.indicators import calculate_indicators, detect_fvg
from .modules.orders import init_exchange, place_order
from .modules.utils import ensure_paper_trading_symbol, retry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tradingbot")


class TradingBot:
    """
    TradingBot class for use in dashboard and tests.
    """

    def __init__(self, config=None):
        self.config = config or load_config()
        self.cfg = self.config  # Alias for compatibility with tests
        self.exchange = init_exchange(
            self.config.API_KEY, self.config.API_SECRET, self.config.EXCHANGE
        )
        self.is_running = False
        self.trade_history = []
        self.current_position = None
        self.last_update = None
        self.real_symbol = (
            self.config.SYMBOL if hasattr(self.config, "SYMBOL") else "BTC/USD"
        )

    def start(self):
        self.is_running = True
        return True

    def stop(self):
        self.is_running = False
        return True

    def run(self):
        """
        Example run method for TradingBot.
        """
        df = pd.DataFrame(
            {
                "timestamp": pd.date_range("2024-01-01", periods=100, freq="h"),
                "open": [1.0] * 100,
                "high": [1.1] * 100,
                "low": [0.9] * 100,
                "close": [1.0] * 100,
                "volume": [100] * 100,
            }
        )
        df = calculate_indicators(
            df,
            ema_length=14,
            volume_multiplier=1.5,
            trading_start_hour=9,
            trading_end_hour=17,
        )
        logger.info("Indicators calculated.")
        fvg = detect_fvg(df, lookback=3, bullish=True)
        logger.info(f"Detected FVG: {fvg}")
        # Example order (not actually sent)
        # place_order("market", self.config.SYMBOL, 0.01)
        logger.info("Trading bot run complete.")


async def main():
    """
    Main async trading loop.
    """
    bot = TradingBot()
    bot.start()
    bot.run()
    bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
    asyncio.run(main())
