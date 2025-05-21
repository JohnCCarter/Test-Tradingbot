import json
import pytest
import time
from modules.utils import retry, ensure_paper_trading_symbol, get_next_nonce, NONCE_FILE

def test_retry_success():
    calls = {"c":0}
    @retry(max_attempts=3, initial_delay=0)
    def f(x):
        calls["c"] += 1
        if calls["c"] < 2:
            raise ValueError()
        return x
    assert f(5) == 5
    assert calls["c"] == 2

def test_retry_fail():
    @retry(max_attempts=2, initial_delay=0)
    def f(): raise RuntimeError()
    with pytest.raises(RuntimeError):
        f()

def test_ensure_symbol():
    assert ensure_paper_trading_symbol("BTC/USD").startswith("tTEST")
    assert ensure_paper_trading_symbol("tTESTX").startswith("tTEST")

def test_nonce(tmp_path):
    tmp = tmp_path / "n.json"
    # Temporärt ändra filen
    from modules import utils
    old = utils.NONCE_FILE
    utils.NONCE_FILE = str(tmp)
    n1 = get_next_nonce()
    n2 = get_next_nonce()
    assert n2 > n1
    data = json.loads(tmp.read_text())
    assert data["last_nonce"] == n2
    utils.NONCE_FILE = old
