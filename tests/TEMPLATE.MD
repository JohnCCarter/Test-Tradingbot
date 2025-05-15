```  
// GitHub Copilot-prompt:
"""
Generera en komplett Python-projekttemplate för en tradingbot enligt denna struktur:

```
Tradingbot/
├── src/
│   ├── __init__.py
│   ├── tradingbot.py
│   ├── config_loader.py
│   └── modules/
│       ├── __init__.py
│       ├── indicators.py
│       ├── orders.py
│       └── utils.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_config_loader.py
│   ├── test_indicators.py
│   ├── test_orders.py
│   └── test_utils.py
├── environment.yml
├── .env.example
├── Makefile
├── Dockerfile
├── .pre-commit-config.yaml
└── README.md
```

– I varje Python-fil, skapa en grundläggande stub:  
  – `tradingbot.py`: importera `load_config`, initiera logger, anropa `main()`-funktion.  
  – `config_loader.py`: definiera Pydantic-modell `BotConfig` och `load_config()` som läser `config.json`.  
  – `modules/indicators.py`: stub­funktioner `calculate_indicators()`, `detect_fvg()`.  
  – `modules/orders.py`: stub­funktioner `place_order()`, `cancel_order()`, `fetch_balance()`.  
  – `modules/utils.py`: stub­funktioner `retry()`-decorator, `ensure_paper_trading_symbol()`, nonce-generator.  
– I `tests/`, skriv importvägar via `sys.path` till `src` och en enkel “import OK”-assert i varje testfil.  
– Fyll `environment.yml`, `.env.example`, `Makefile`, `Dockerfile` och `.pre-commit-config.yaml` med de avsnitt du redan delat.  
– I `README.md`, lägg in badges, installation, snabbstart, strukturöversikt och roadmap.

"""
```
