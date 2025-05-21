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

## Projektstruktur

```
trading-bot/
├── frontend/                 # Next.js frontend
│   ├── src/
│   │   ├── app/            # Next.js app router
│   │   ├── components/     # React components
│   │   └── styles/        # CSS/SCSS files
│   ├── public/            # Static files
│   ├── package.json
│   └── next.config.js
│
├── backend/                # Flask backend
│   ├── src/
│   │   ├── modules/       # Trading modules
│   │   ├── templates/     # Flask templates
│   │   └── dashboard.py   # Main Flask app
│   ├── tests/            # Backend tests
│   └── requirements.txt
│
├── logs/                  # Log files
├── .env                  # Environment variables
└── config.json           # Bot configuration
```

## Installation

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # eller `venv\Scripts\activate` på Windows
pip install -r requirements.txt
```

### Frontend
```bash
cd frontend
npm install
```

## Utveckling

### Starta utvecklingsservrar

1. Starta backend:
```bash
cd backend
python src/dashboard.py
```

2. Starta frontend:
```bash
cd frontend
npm run dev
```

Backend körs på http://localhost:5000
Frontend körs på http://localhost:3000

## Testning

### Backend tester
```bash
cd backend
pytest
```

### Frontend tester
```bash
cd frontend
npm test
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