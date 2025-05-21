# src/config_loader.py

import os
import json
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional

load_dotenv()

class BotConfig(BaseModel):
    """
    Pydantic-konfiguration för tradingbot:
    matchar alla nycklar i config.json + API_KEY/API_SECRET från .env.
    """

    # Credentials
    API_KEY: str
    API_SECRET: str

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

    # Optional strategy parameters
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
    Läser in JSON-konfiguration + miljövariabler (.env) och returnerar
    en BotConfig-instans. Saknade valfria fält blir None.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Läs API-nycklar från .env
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    if not api_key or not api_secret:
        raise ValueError("Sätt API_KEY och API_SECRET i din .env-fil")

    # E-post-överskrivningar (om satt i .env)
    raw["EMAIL_SENDER"]   = os.getenv("EMAIL_SENDER",   raw.get("EMAIL_SENDER"))
    raw["EMAIL_RECEIVER"] = os.getenv("EMAIL_RECEIVER", raw.get("EMAIL_RECEIVER"))
    raw["EMAIL_PASSWORD"] = os.getenv("EMAIL_PASSWORD", raw.get("EMAIL_PASSWORD"))

    # Ta bort API-nycklar från raw dictionaryt för att undvika TypeError
    raw.pop("API_KEY", None)
    raw.pop("API_SECRET", None)

    return BotConfig(
        API_KEY=api_key,
        API_SECRET=api_secret,
        **raw
    )
