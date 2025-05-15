import functools
import time
import json
import os
from typing import Callable

NONCE_FILE = os.path.join(os.path.dirname(__file__), "nonce.json")

def retry(max_attempts: int = 3, initial_delay: float = 1.0) -> Callable:
    """
    Decorator for retrying a function with exponential backoff.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except KeyboardInterrupt:
                    raise
                except Exception:
                    if attempt == max_attempts:
                        raise
                    time.sleep(delay)
                    delay *= 2
        return wrapper
    return decorator

def ensure_paper_trading_symbol(symbol: str) -> str:
    """
    Convert e.g. 'BTC/USD' to 'tTESTBTC:TESTUSD' for Bitfinex paper trading.
    """
    if symbol.startswith("tTEST"):
        return symbol
    if "/" in symbol:
        base, quote = symbol.split("/")
        return f"tTEST{base}:TEST{quote}"
    if symbol.startswith("t") and not symbol.startswith("tTEST"):
        return f"tTEST{symbol[1:]}"
    return f"tTEST{symbol}"

def get_next_nonce() -> int:
    """
    Returns a unique, incrementing nonce, persisted in NONCE_FILE.
    """
    try:
        with open(NONCE_FILE, "r") as f:
            data = json.load(f)
            last_nonce = data.get("last_nonce", 0)
    except Exception:
        last_nonce = 0
    next_nonce = last_nonce + 1
    with open(NONCE_FILE, "w") as f:
        json.dump({"last_nonce": next_nonce}, f)
    return next_nonce
