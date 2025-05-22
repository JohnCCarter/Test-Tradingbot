import asyncio
import logging

import pandas as pd

from backend.src.config_loader import load_config
from backend.src.modules.indicators import calculate_indicators, detect_fvg
from backend.src.modules.orders import (calculate_position_size, fetch_balance,
                                        init_exchange, place_order)
from backend.src.modules.utils import ensure_paper_trading_symbol, retry

# Use the root logger instead of creating a new one
logger = logging.getLogger(__name__)


class TradingBot:
    def __init__(self, config):
        self.log = logger
        self.cfg = config
        self.exchange = None
        self.is_running = False
        self.current_position = None
        self.trade_history = []
        self.last_update = None

    async def start_async(self):
        """Asynkron version av start-funktionen"""
        try:
            self.exchange = init_exchange(
                self.cfg.API_KEY, self.cfg.API_SECRET, self.cfg.EXCHANGE
            )
            self.is_running = True
            self.log.info("Trading bot started asynchronously")
            return True
        except Exception as e:
            self.log.error(f"Failed to start bot asynchronously: {str(e)}")
            return False

    async def stop_async(self):
        """Asynkron version av stop-funktionen"""
        try:
            self.is_running = False
            self.log.info("Trading bot stopped asynchronously")
            return True
        except Exception as e:
            self.log.error(f"Failed to stop bot asynchronously: {str(e)}")
            return False

    def start(self):
        """Synkron version av start-funktionen"""
        try:
            self.exchange = init_exchange(
                self.cfg.API_KEY, self.cfg.API_SECRET, self.cfg.EXCHANGE
            )
            self.is_running = True
            self.log.info("Trading bot started")
            return True
        except Exception as e:
            self.log.error(f"Failed to start bot: {str(e)}")
            return False

    def stop(self):
        """Synkron version av stop-funktionen"""
        try:
            # Close any open positions
            if self.current_position:
                self.close_position("MANUAL")

            self.is_running = False
            self.log.info("Trading bot stopped")
            return True
        except Exception as e:
            self.log.error(f"Failed to stop bot: {str(e)}")
            return False

    def update_position(self):
        """Update current position information"""
        if not self.current_position:
            return None

        try:
            # Get current price
            if not self.exchange:
                raise ValueError("Exchange not initialized")

            ticker = self.exchange.fetch_ticker(self.cfg.SYMBOL)
            if not ticker or "last" not in ticker:
                raise ValueError("Invalid ticker data received")

            current_price = ticker["last"]

            # Calculate unrealized PnL
            if not self.current_position or "entry_price" not in self.current_position:
                raise ValueError("Invalid position data")

            entry_price = self.current_position["entry_price"]
            size = self.current_position["size"]
            unrealized_pnl = size * (current_price - entry_price)

            # Calculate time in position
            entry_time = pd.Timestamp(self.current_position["entry_time"])
            time_in_position = str(pd.Timestamp.now() - entry_time)

            self.current_position.update(
                {
                    "current_price": current_price,
                    "unrealized_pnl": unrealized_pnl,
                    "time_in_position": time_in_position,
                }
            )

            return self.current_position
        except Exception as e:
            self.log.error(f"Error updating position: {e}")
            return None

    def close_position(self, reason="MANUAL"):
        """Close current position"""
        if not self.current_position:
            return None

        try:
            # Get current price
            if not self.exchange:
                raise ValueError("Exchange not initialized")

            ticker = self.exchange.fetch_ticker(self.cfg.SYMBOL)
            if not ticker or "last" not in ticker:
                raise ValueError("Invalid ticker data received")

            exit_price = ticker["last"]

            # Calculate PnL
            if not self.current_position or "entry_price" not in self.current_position:
                raise ValueError("Invalid position data")

            entry_price = self.current_position["entry_price"]
            size = self.current_position["size"]
            pnl = size * (exit_price - entry_price)

            # Create trade record
            trade = {
                "timestamp": pd.Timestamp.now().isoformat(),
                "type": self.current_position["type"],
                "entry_price": entry_price,
                "exit_price": exit_price,
                "size": size,
                "pnl": pnl,
                "reason": reason,
            }

            # Add to trade history
            self.trade_history.append(trade)

            # Clear current position
            self.current_position = None

            return trade
        except Exception as e:
            self.log.error(f"Error closing position: {e}")
            return None

    async def run(self):
        """Main trading loop"""
        if not self.is_running:
            return

        try:
            # Fetch OHLCV data
            if not self.exchange:
                raise ValueError("Exchange not initialized")

            ohlcv = self.exchange.fetch_ohlcv(
                self.cfg.SYMBOL, self.cfg.TIMEFRAME, limit=self.cfg.LIMIT
            )
            if not ohlcv:
                raise ValueError("No OHLCV data received")

            # Build DataFrame
            df = pd.DataFrame(
                ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
            )
            df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)

            # Calculate indicators
            data = calculate_indicators(
                df,
                ema_length=self.cfg.EMA_LENGTH,
                volume_multiplier=self.cfg.VOLUME_MULTIPLIER,
                trading_start_hour=self.cfg.TRADING_START_HOUR,
                trading_end_hour=self.cfg.TRADING_END_HOUR,
            )

            # Update current position
            if self.current_position:
                self.update_position()

                # Check stop loss
                if data.iloc[-1]["low"] <= self.current_position["sl_price"]:
                    self.close_position("SL")

                # Check take profit
                elif data.iloc[-1]["high"] >= self.current_position["tp_price"]:
                    self.close_position("TP")

            # Look for new entry if no position
            elif self.is_running:
                low_zone, high_zone = detect_fvg(data, self.cfg.LOOKBACK, bullish=True)
                last = data.iloc[-1]

                if high_zone and last["close"] > high_zone:
                    # Calculate position size
                    balance = fetch_balance(self.exchange)
                    quote = self.cfg.SYMBOL.split(":")[-1]
                    equity = balance.get("total", {}).get(quote, 0)

                    entry_price = last["close"]
                    sl_price = entry_price * (1 - self.cfg.STOP_LOSS_PERCENT / 100)
                    tp_price = entry_price * (1 + self.cfg.TAKE_PROFIT_PERCENT / 100)

                    size = calculate_position_size(
                        equity, self.cfg.RISK_PER_TRADE, entry_price, sl_price
                    )

                    # Place order
                    order = place_order(
                        "buy", self.cfg.SYMBOL, size=size, price=entry_price
                    )

                    if order:
                        self.current_position = {
                            "type": "LONG",
                            "entry_price": entry_price,
                            "sl_price": sl_price,
                            "tp_price": tp_price,
                            "size": size,
                            "entry_time": pd.Timestamp.now().isoformat(),
                        }
                        self.log.info(f"Opened long position: {self.current_position}")

            self.last_update = pd.Timestamp.now()

        except Exception as e:
            self.log.error(f"Error in trading loop: {e}")


async def main():
    """Main async entrypoint for the tradingbot"""
    cfg = load_config()
    bot = TradingBot(cfg)

    if bot.start():
        while bot.is_running:
            await bot.run()
            await asyncio.sleep(5)  # Update every 5 seconds


if __name__ == "__main__":
    asyncio.run(main())
