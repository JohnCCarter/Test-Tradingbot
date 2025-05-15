import os
import json
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

class BotConfig(BaseModel):
    API_KEY: str
    API_SECRET: str
    EXCHANGE: str
    SYMBOL: str
    TIMEFRAME: str
    LIMIT: int
    EMA_LENGTH: int
    ATR_MULTIPLIER: float
    VOLUME_MULTIPLIER: float
    TRADING_START_HOUR: int
    TRADING_END_HOUR: int
    MAX_DAILY_LOSS: float
    MAX_TRADES_PER_DAY: int
    STOP_LOSS_PERCENT: float
    TAKE_PROFIT_PERCENT: float
    EMAIL_NOTIFICATIONS: bool
    EMAIL_SMTP_SERVER: str
    EMAIL_SMTP_PORT: int
    EMAIL_SENDER: str
    EMAIL_RECEIVER: str
    EMAIL_PASSWORD: str
    LOOKBACK: int
    TEST_BUY_ORDER: bool
    TEST_SELL_ORDER: bool
    TEST_LIMIT_ORDERS: bool
    METRICS_PORT: int
    HEALTH_PORT: int

def load_config(path: str = "config.json") -> BotConfig:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, 'r') as f:
        raw = json.load(f)

    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    if not api_key or not api_secret:
        raise ValueError("Sätt API_KEY och API_SECRET i din .env-fil")

    # Läs e-post från .env (fallback på config.json om satt där)
    raw["EMAIL_SENDER"]   = os.getenv("EMAIL_SENDER",   raw.get("EMAIL_SENDER",   ""))
    raw["EMAIL_RECEIVER"] = os.getenv("EMAIL_RECEIVER", raw.get("EMAIL_RECEIVER", ""))
    raw["EMAIL_PASSWORD"] = os.getenv("EMAIL_PASSWORD", "")

    return BotConfig(
        API_KEY=api_key,
        API_SECRET=api_secret,
        **raw
    )
