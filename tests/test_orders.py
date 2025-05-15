# tests/test_orders.py

import pytest
import ccxt
from modules.orders import (
    init_exchange,
    place_order,
    cancel_order,
    fetch_balance,
    calculate_position_size,
)
from modules.utils import ensure_paper_trading_symbol


# --- existing tests for orders.py ---

class DummyExchange:
    """A simple stub to simulate ccxt Exchange methods."""
    def __init__(self):
        self.id = "dummy"
        self.orders = {}

    def create_market_order(self, symbol, side, amount, params=None):
        return {"method": "market", "symbol": symbol, "side": side, "amount": amount, "params": params}

    def create_limit_order(self, symbol, side, amount, price, params=None):
        return {"method": "limit", "symbol": symbol, "side": side, "amount": amount, "price": price, "params": params}

    def cancel_order(self, order_id, symbol=None):
        return {"status": "canceled", "order_id": order_id, "symbol": symbol}

    def fetch_balance(self):
        return {"free": {"BTC": 1.0, "USD": 1000.0}, "used": {}, "total": {"BTC": 1.0, "USD": 1000.0}}


def test_place_market_order():
    ex = DummyExchange()
    res = place_order(ex, "BTC/USD", "buy", 0.5)
    assert res["method"] == "market"
    assert res["side"] == "buy"
    assert res["amount"] == 0.5


def test_place_limit_order():
    ex = DummyExchange()
    res = place_order(ex, "BTC/USD", "sell", 0.1, price=50)
    assert res["method"] == "limit"
    assert res["price"] == 50


def test_cancel_order():
    ex = DummyExchange()
    res = cancel_order(ex, "12345", symbol="BTC/USD")
    assert res["status"] == "canceled"
    assert res["order_id"] == "12345"


def test_fetch_balance():
    ex = DummyExchange()
    bal = fetch_balance(ex)
    assert "total" in bal and "free" in bal


# --- new tests for calculate_position_size ---

@pytest.mark.parametrize(
    "equity,risk_per_trade,entry_price,stop_loss_price,expected",
    [
        (1000.0, 0.01, 50.0, 45.0, (1000.0 * 0.01) / (50.0 - 45.0)),
        (5000.0, 0.02, 100.0, 90.0, (5000.0 * 0.02) / (100.0 - 90.0)),
        (2500.0, 0.005, 200.0, 190.0, (2500.0 * 0.005) / (200.0 - 190.0)),
    ],
)
def test_calculate_position_size_valid(equity, risk_per_trade, entry_price, stop_loss_price, expected):
    result = calculate_position_size(equity, risk_per_trade, entry_price, stop_loss_price)
    assert pytest.approx(expected, rel=1e-8) == result


def test_calculate_position_size_zero_distance():
    # entry_price == stop_loss_price should raise ValueError
    with pytest.raises(ValueError):
        calculate_position_size(1000.0, 0.01, 50.0, 50.0)


def test_calculate_position_size_negative_distance():
    # Negative distance (stop_loss above entry for long) also invalid
    with pytest.raises(ValueError):
        calculate_position_size(1000.0, 0.01, 50.0, 55.0)
