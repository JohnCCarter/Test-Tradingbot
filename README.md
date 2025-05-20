# Trading Bot

En Python-baserad tradingbot som använder FVG breakout strategi med EMA, volym och trading-tider.

## Funktioner

- FVG breakout strategi
- Risk management med position sizing
- Stop-loss och take-profit
- Paper trading för testning
- Backtesting
- E-postnotifieringar
- Metrik- och hälsöövervakning

## Installation

1. Klona repot:
```bash
git clone <repo-url>
cd tradingbot
```

2. Skapa och aktivera conda-miljön:
```bash
make update-env
conda activate tradingbot_env
```

3. Konfigurera miljövariabler:
```bash
cp .env.example .env
# Redigera .env med dina API-nycklar
```

## Användning

### Starta boten
```bash
make run
```

### Kör backtest
```bash
make backtest
```

### Utveckling
```bash
# Formatera kod
make format

# Kör tester
make test

# Starta interaktiv shell
make shell
```

## Projektstruktur

```
tradingbot/
├── src/
│   ├── tradingbot.py      # Huvudapplikation
│   ├── config_loader.py   # Konfigurationshantering
│   └── modules/
│       ├── indicators.py  # Tekniska indikatorer
│       ├── orders.py      # Orderhantering
│       └── utils.py       # Hjälpfunktioner
├── tests/                 # Tester
├── config.json           # Konfiguration
├── environment.yml       # Conda-miljö
└── Makefile             # Byggkommandon
```

## Konfiguration

Se `config.json` för alla konfigurationsalternativ. Viktiga inställningar:

- `EXCHANGE`: Börs att handla på
- `SYMBOL`: Handlingspar
- `TIMEFRAME`: Tidsram för candles
- `EMA_LENGTH`: EMA-period
- `VOLUME_MULTIPLIER`: Volymfilter
- `STOP_LOSS_PERCENT`: Stop-loss i procent
- `TAKE_PROFIT_PERCENT`: Take-profit i procent
- `RISK_PER_TRADE`: Risk per trade i procent

## Säkerhet

- API-nycklar hanteras via .env
- Säker nonce-hantering
- Validering av indata
- HTTPS för API-anrop

## Licens

MIT