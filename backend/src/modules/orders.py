"""
Order management functions for trading bot.
Includes exchange init, order placement, cancel, and balance fetch.
"""

from typing import Any, Optional

import ccxt

from .utils import ensure_paper_trading_symbol

_Exchange: Optional[ccxt.Exchange] = None

def init_exchange(api_key: str, api_secret: str, exchange_name: str) -> ccxt.Exchange:
    """
    Initializes and returns a ccxt exchange instance.
    """
    global _Exchange
    exchange_class = getattr(ccxt, exchange_name, None)
    if not exchange_class:
        raise RuntimeError(f"Exchange '{exchange_name}' not found in ccxt.")
    exchange = exchange_class({
        "apiKey": api_key,
        "secret": api_secret,
        "enableRateLimit": True,
    })
    _Exchange = exchange
    return exchange

def place_order(
    order_type: str,
    symbol: str,
    amount: float,
    price: float | None = None,
    params: dict | None = None,
) -> Any:
    """
    Places an order using the initialized exchange.
    """
    global _Exchange
    if _Exchange is None:
        raise RuntimeError("Exchange not initialized. Call init_exchange first.")
    ex = _Exchange
    sym = ensure_paper_trading_symbol(symbol) if ex.id == "bitfinex" else symbol
    params = params or {}
    if order_type == "market":
        return ex.create_market_order(sym, "buy", amount, params)
    elif order_type == "limit":
        if price is None:
            raise ValueError("Price required for limit order.")
        return ex.create_limit_order(sym, "buy", amount, price, params)
    else:
        raise ValueError(f"Unknown order type: {order_type}")

def cancel_order(exchange: ccxt.Exchange, order_id: str, symbol: str | None = None) -> Any:
    """
    Cancels an order on the given exchange.
    """
    sym = ensure_paper_trading_symbol(symbol) if symbol and exchange.id == "bitfinex" else symbol
    return exchange.cancel_order(order_id, sym) if sym else exchange.cancel_order(order_id)

def fetch_balance(exchange: ccxt.Exchange) -> dict:
    """
    Fetches account balance from the given exchange.
    """
    return exchange.fetch_balance()

def calculate_position_size(
    equity: float, risk_per_trade: float, entry_price: float, stop_loss_price: float
) -> float:
    """
    Calculate position size based on risk per trade and stop loss distance.

    :param equity: Account equity
    :param risk_per_trade: Fraction of equity to risk per trade (e.g. 0.01 for 1%)
    :param entry_price: Entry price of the trade
    :param stop_loss_price: Stop loss price
    :return: Position size (amount)
    :raises ValueError: If stop loss distance is zero or negative
    """
    risk_amount = equity * risk_per_trade
    stop_loss_distance = entry_price - stop_loss_price
    if stop_loss_distance <= 0:
        raise ValueError("Stop loss distance must be positive (entry_price > stop_loss_price for long positions).")
    return risk_amount / stop_loss_distance
