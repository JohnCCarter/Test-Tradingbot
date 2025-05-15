---
applyTo: '**/*.md'
---
Coding standards, domain knowledge, and preferences that AI should follow.

**Key details:**
- **tradingbot.py** uses:
  - `load_config()` from `config_loader.py`
  - `retry` and `ensure_paper_trading_symbol` from `modules.utils`
  - `init_exchange` & `place_order` from `modules.orders`
  - `calculate_indicators` & `detect_fvg` from `modules.indicators`
  - Pandas for DataFrame construction, asyncio for loop, standard logging
- **config_loader.py** must:
  - Load `.env` via `python-dotenv`
  - Define a Pydantic `BotConfig` matching fields in `config.json` plus `API_KEY`/`API_SECRET` from env
  - Provide `load_config(path="config.json") -> BotConfig`
- **modules/utils.py** must:
  - `def retry(max_attempts: int = 3, initial_delay: float = 1.0) -> decorator`
  - `def ensure_paper_trading_symbol(symbol: str) -> str`
  - `def get_next_nonce() -> int` persisting last nonce in `NONCE_FILE`
- **modules/orders.py** must:
  - `def init_exchange(api_key: str, api_secret: str, exchange_name: str) -> ccxt.Exchange`
  - `def place_order(order_type: str, symbol: str, amount: float, price: float | None = None, params: dict | None = None) -> Any`
  - `def cancel_order(exchange: ccxt.Exchange, order_id: str, symbol: str | None = None) -> Any`
  - `def fetch_balance(exchange: ccxt.Exchange) -> dict`
  - Use `ensure_paper_trading_symbol` for Bitfinex paper symbols
  - Raise `RuntimeError` if exchange isn’t initialized (for init_exchange style) or accept exchange as param for test stubs
- **modules/indicators.py** must:
  - `def calculate_indicators(df: pandas.DataFrame, ema_length: int, volume_multiplier: float, trading_start_hour: int, trading_end_hour: int) -> pandas.DataFrame`
    - Adds `"ema"`, `"atr"`, `"avg_volume"`, `"high_volume"`, `"rsi"`, `"adx"`, `"within_trading_hours"` columns
  - `def detect_fvg(df: pandas.DataFrame, lookback: int, bullish: bool = True) -> tuple[float, float]`
    - Returns correct high/low values per tests
- **Tests** import exactly via:
  - `from modules.utils import …`
  - `from modules.orders import …`
  - `from modules.indicators import …`
  - `from config_loader import load_config, BotConfig`
  - Conftest puts `src/` at front of `sys.path`

**Requirements:**
1. **Do not modify** any test files or config files.
2. Use **relative imports** inside `src/modules` (e.g. `from .utils import retry`).
3. Add **docstrings** and **PEP8 styling** (80-char max).
4. Use **Python 3.12** built-in generics and union types (e.g. `list[dict]`, `str | None`).
5. Ensure running `pytest tests/` passes without errors.
6. Implement the complete code in:
   - `src/config_loader.py`
   - `src/modules/utils.py`
   - `src/modules/orders.py`
   - `src/modules/indicators.py`
   - `src/tradingbot.py`

Generate the full bodies of these files so Copilot can insert correct, ready-to-run code that satisfies all existing tests.
