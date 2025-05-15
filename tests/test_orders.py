import pytest
from modules.orders import place_order, cancel_order, fetch_balance

class DummyExchange:
    def create_market_order(self, sym, side, amt, params=None):
        return {"status":"open"}
    def create_limit_order(self, sym, side, amt, price, params=None):
        return {"status":"open"}
    def cancel_order(self, oid, sym=None):
        return {"status":"canceled"}
    def fetch_balance(self):
        return {"free":{"USD":100}}

@pytest.fixture
def ex():
    return DummyExchange()

def test_place_market_order(ex):
    res = place_order(ex, "SYM", "buy", 1.0)
    assert res["status"] == "open"

def test_place_limit_order(ex):
    res = place_order(ex, "SYM", "sell", 1.0, price=10)
    assert res["status"] == "open"

def test_cancel_order(ex):
    res = cancel_order(ex, "123", "SYM")
    assert res["status"] == "canceled"

def test_fetch_balance(ex):
    bal = fetch_balance(ex)
    assert "USD" in bal["free"]
