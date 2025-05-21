from dotenv import load_dotenv
load_dotenv()
import json
import pytest
import sys
import os

# Add backend directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config_loader import load_config, BotConfig

def test_load_config(tmp_path):
    sample = {
        "EXCHANGE": "bitfinex",
        "SYMBOL": "tTESTBTC:TESTUSD",
        "TIMEFRAME": "1m",
        "LIMIT": 100,
        "EMA_LENGTH": 14,
        "EMA_FAST": 12,
        "EMA_SLOW": 26,
        "RSI_PERIOD": 14,
        "ATR_MULTIPLIER": 1.5,
        "VOLUME_MULTIPLIER": 1.2,
        "TRADING_START_HOUR": 0,
        "TRADING_END_HOUR": 23,
        "MAX_DAILY_LOSS": 100.0,
        "MAX_TRADES_PER_DAY": 10,
        "LOOKBACK": 20
    }
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(json.dumps(sample))
    cfg = load_config(str(cfg_file))
    assert isinstance(cfg, BotConfig)
    assert cfg.EXCHANGE == "bitfinex"
    assert cfg.EMA_FAST == 12
    assert cfg.EMA_SLOW == 26
    assert cfg.RSI_PERIOD == 14
