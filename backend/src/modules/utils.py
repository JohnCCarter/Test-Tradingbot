import functools
import json
import os
import time
from typing import Callable
import logging

logger = logging.getLogger(__name__)

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
    Convert symbol to paper trading format only if needed.
    Returns the original symbol if it's already in the correct format.
    """
    # If it's already a paper trading symbol, return as is
    if symbol.startswith("tTEST"):
        return symbol

    # If it's a regular trading symbol (e.g. BTC/USD), convert it
    if "/" in symbol:
        base, quote = symbol.split("/")
        return f"tTEST{base}:TEST{quote}"

    # If it's already in Bitfinex format (e.g. tBTCUSD), convert it
    if symbol.startswith("t") and not symbol.startswith("tTEST"):
        return f"tTEST{symbol[1:]}"

    # For any other format, try to convert it
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


def save_nonce(nonce):
    """Save nonce to file"""
    try:
        with open(NONCE_FILE, 'w', encoding='utf-8') as f:
            f.write(str(nonce))
    except Exception as e:
        logger.error("Error saving nonce: %s", e)
        raise


def load_nonce():
    """Load nonce from file"""
    try:
        if os.path.exists(NONCE_FILE):
            with open(NONCE_FILE, 'r', encoding='utf-8') as f:
                return int(f.read().strip())
    except Exception as e:
        logger.error("Error loading nonce: %s", e)
    return 0
