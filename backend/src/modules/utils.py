"""
Utility functions for trading bot modules.
Includes retry decorator, symbol helpers, and nonce management.
"""

import functools
import os
import time
from typing import Callable

NONCE_FILE = "nonce.txt"


def retry(max_attempts: int = 3, initial_delay: float = 1.0) -> Callable:
    """
    Decorator for retrying a function on exception.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts:
                        raise
                    time.sleep(delay)
                    delay *= 2

        return wrapper

    return decorator


def ensure_paper_trading_symbol(symbol: str) -> str:
    """
    Ensures Bitfinex paper trading symbol is correct.
    """
    if symbol and symbol.startswith("t") and ":" in symbol:
        return symbol
    if symbol and symbol.upper() == "BTC/USD":
        return "tTESTBTC:TESTUSD"
    return symbol


def get_next_nonce() -> int:
    """
    Returns next nonce, persisting last value in NONCE_FILE.
    """
    last_nonce = 0
    if os.path.exists(NONCE_FILE):
        with open(NONCE_FILE, "r", encoding="utf-8") as f:
            try:
                last_nonce = int(f.read().strip())
            except Exception:
                last_nonce = 0
    next_nonce = last_nonce + 1
    with open(NONCE_FILE, "w", encoding="utf-8") as f:
        f.write(str(next_nonce))
    return next_nonce
