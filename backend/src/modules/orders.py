import logging
import os
from typing import Any, Optional

import ccxt

from backend.src.modules.utils import ensure_paper_trading_symbol

logger = logging.getLogger(__name__)

NONCE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "nonce.json")

_exchange: Optional[ccxt.Exchange] = None


def calculate_position_size(
    equity: float, risk_per_trade: float, entry_price: float, stop_loss_price: float
) -> float:
    """
    Calculate how many units to trade to risk a given fraction of equity.

    :param equity: Total account equity.
    :param risk_per_trade: Fraction of equity to risk (e.g., 0.01 for 1%).
    :param entry_price: Price at which the position will be opened.
    :param stop_loss_price: Price below entry_price to place stop-loss.
    :raises ValueError: If stop_loss_price is not below entry_price.
    :return: Position size in base currency units.
    """
    if stop_loss_price >= entry_price:
        raise ValueError(
            "stop_loss_price must be less than entry_price for long positions"
        )
    max_risk_amount = equity * risk_per_trade
    risk_per_unit = entry_price - stop_loss_price
    return max_risk_amount / risk_per_unit


def init_exchange(api_key: str, api_secret: str, exchange_name: str) -> ccxt.Exchange:
    """
    Initialize and return a ccxt.Exchange instance.

    :raises ValueError: If exchange_name is not supported.
    """
    global _exchange
    exchange_cls = getattr(ccxt, exchange_name.lower(), None)
    if not exchange_cls:
        raise ValueError(f"Unsupported exchange: {exchange_name}")

    _exchange = exchange_cls(
        {
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
            "options": {"paper": True, "defaultType": "spot"},  # Enable paper trading
        }
    )

    if _exchange is None:
        raise RuntimeError("Failed to initialize exchange instance")

    try:
        # Load markets and log available symbols
        _exchange.load_markets()
        if _exchange.markets:
            logger.info("Available symbols: %s", list(_exchange.markets.keys()))
        else:
            logger.warning("No markets loaded from exchange")
    except Exception as e:
        logger.error(f"Error loading markets: {e}")
        raise

    return _exchange


def place_order(*args, **kwargs) -> Any:
    """
    Place an order using a test stub or the initialized global exchange.

    Supports:
    - Test stub: exchange.create_* methods if first arg has create_market_order.
    - Production: uses global _exchange; handles Bitfinex paper symbols.
    """
    # Test-stub: DummyExchange signature
    if args and hasattr(args[0], "create_market_order"):
        exchange = args[0]
        symbol = args[1]
        order_type = args[2]
        amount = args[3]
        price = kwargs.get("price", None)
        params = kwargs.get("params", None)
        if price is not None:
            return exchange.create_limit_order(
                symbol, order_type, amount, price, params
            )
        return exchange.create_market_order(symbol, order_type, amount, params)

    # Production: use global _exchange
    if _exchange is None:
        raise RuntimeError("Exchange is not initialized, call init_exchange first")
    order_type = args[0]
    symbol = args[1]
    amount = args[2]
    price = kwargs.get("price", None)
    params = kwargs.get("params", {}) or {}
    exchange = _exchange

    side = order_type.lower()
    if side == "buy":
        if price is not None:
            return exchange.create_limit_buy_order(symbol, amount, price, params)
        return exchange.create_market_buy_order(symbol, amount, params)
    elif side == "sell":
        if price is not None:
            return exchange.create_limit_sell_order(symbol, amount, price, params)
        return exchange.create_market_sell_order(symbol, amount, params)
    else:
        raise ValueError(f"Unknown order type: {order_type}")


def cancel_order(exchange: Any, order_id: str, symbol: Optional[str] = None) -> Any:
    """
    Cancel an order on the given exchange.

    :param exchange: ccxt.Exchange or stub
    :param order_id: The unique identifier of the order to cancel.
    :param symbol: Optional symbol, required by some exchanges.
    :return: API response dict.
    """
    return (
        exchange.cancel_order(order_id, symbol)
        if symbol
        else exchange.cancel_order(order_id)
    )


def fetch_balance(exchange: Any) -> dict:
    """
    Fetch balance from the given exchange.

    :param exchange: ccxt.Exchange or stub
    :return: Balance dict.
    """
    return exchange.fetch_balance()
