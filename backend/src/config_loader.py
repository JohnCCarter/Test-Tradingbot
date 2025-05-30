"""
Configuration loader for trading bot.
Loads .env and config.json, provides BotConfig.
"""

import json
import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel


class BotConfig(BaseModel):
    """
    Pydantic model for bot configuration.
    Includes config.json fields and API keys from env.
    """

    # Core strategy settings
    EXCHANGE: str
    SYMBOL: str
    TIMEFRAME: str
    LIMIT: int

    EMA_LENGTH: int
    EMA_FAST: int
    EMA_SLOW: int
    RSI_PERIOD: int
    ATR_MULTIPLIER: float
    VOLUME_MULTIPLIER: float

    TRADING_START_HOUR: int
    TRADING_END_HOUR: int

    MAX_DAILY_LOSS: float
    MAX_TRADES_PER_DAY: int
    LOOKBACK: int

    # Credentials
    API_KEY: str
    API_SECRET: str

    # Optionals for test/config compatibility
    STOP_LOSS_PERCENT: Optional[float] = None
    TAKE_PROFIT_PERCENT: Optional[float] = None
    RISK_PER_TRADE: Optional[float] = None

    # Optional test flags
    TEST_BUY_ORDER: Optional[bool] = None
    TEST_SELL_ORDER: Optional[bool] = None
    TEST_LIMIT_ORDERS: Optional[bool] = None

    # Optional email settings
    EMAIL_NOTIFICATIONS: Optional[bool] = None
    EMAIL_SMTP_SERVER: Optional[str] = None
    EMAIL_SMTP_PORT: Optional[int] = None
    EMAIL_SENDER: Optional[str] = None
    EMAIL_RECEIVER: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None

    # Optional monitoring ports
    METRICS_PORT: Optional[int] = None
    HEALTH_PORT: Optional[int] = None


def load_config(path: str = "config.json") -> BotConfig:
    """
    Loads .env and config.json, returns BotConfig instance.
    """
    load_dotenv()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["API_KEY"] = os.getenv("API_KEY", "")
    data["API_SECRET"] = os.getenv("API_SECRET", "")
    return BotConfig(**data)
