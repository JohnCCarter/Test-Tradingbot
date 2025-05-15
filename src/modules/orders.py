import ccxt
from typing import Any, Optional
from .utils import ensure_paper_trading_symbol

_exchange: Optional[ccxt.Exchange] = None

def init_exchange(api_key: str, api_secret: str, exchange_name: str) -> ccxt.Exchange:
    global _exchange
    exchange_cls = getattr(ccxt, exchange_name.lower(), None)
    if not exchange_cls:
        raise ValueError(f"Unsupported exchange: {exchange_name}")
    _exchange = exchange_cls({
        "apiKey": api_key,
        "secret": api_secret,
        "enableRateLimit": True,
    })
    _exchange.load_markets()
    return _exchange

def place_order(
    order_type: str,
    symbol: str,
    amount: float,
    price: Optional[float] = None,
    params: Optional[dict] = None
) -> Any:
    if _exchange is None:
        raise RuntimeError("Exchange is not initialized, call init_exchange first")
    # Se till att paper-symbol är korrekt
    if _exchange.id.lower() == "bitfinex":
        symbol = ensure_paper_trading_symbol(symbol)

    if order_type.lower() == "buy":
        if price:
            return _exchange.create_limit_buy_order(symbol, amount, price, params or {})
        return _exchange.create_market_buy_order(symbol, amount, params or {})

    elif order_type.lower() == "sell":
        if price:
            return _exchange.create_limit_sell_order(symbol, amount, price, params or {})
        return _exchange.create_market_sell_order(symbol, amount, params or {})

    else:
        raise ValueError(f"Unknown order type: {order_type}")
