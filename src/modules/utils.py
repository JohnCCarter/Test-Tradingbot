import functools
import time

def retry(max_attempts: int = 3, initial_delay: float = 1.0):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except KeyboardInterrupt:
                    # Låt KeyboardInterrupt bubbla upp
                    raise
                except Exception:
                    if attempt == max_attempts:
                        raise
                    time.sleep(delay)
                    delay *= 2
        return wrapper
    return decorator

def ensure_paper_trading_symbol(symbol: str) -> str:
    """Konvertera t.ex. 'BTC/USD' → 'tTESTBTC:TESTUSD' för Bitfinex paper trading."""
    if symbol.startswith("tTEST"):
        return symbol
    if "/" in symbol:
        base, quote = symbol.split("/")
        return f"tTEST{base}:TEST{quote}"
    if symbol.startswith("t") and not symbol.startswith("tTEST"):
        return f"tTEST{symbol[1:]}"
    # Fallback
    return f"tTEST{symbol}"
