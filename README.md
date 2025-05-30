# Trading Bot

En Python-baserad tradingbot som använder FVG breakout-strategi med EMA, volym och reglerade trading-tider.

## 🚀 Funktioner

- FVG breakout-strategi
- EMA + volymfilter
- Stop-loss och take-profit
- Risk management (position sizing)
- Backtesting & paper trading
- E-postnotifieringar
- Hälsomonitorering
- API-server (Flask)
- Web UI (Next.js / React)

---

## 🧠 Struktur (används av Cursor AI)

```plaintext
trading-bot/
├── backend/src/dashboard.py    # Huvudserver (Flask)
├── frontend/src/app/           # Next.js App Router
├── start_servers.py            # Startar både frontend och backend
├── config.json                 # Bot-konfiguration
├── logs/                       # Loggfiler
├── .env                        # API-nycklar
└── .vscode/, cursor.json, jsconfig.json
```

---

## ⚙️ Installation

### Backend (Conda)

> Både för Bash och PowerShell

```bash
cd backend
conda env create -f environment.yml
conda activate tradingbot_env
```

> 🔍 Obs! Ersätt `tradingbot` med det namn du har definierat i `environment.yml` under `name:`.

### Frontend Installation

```bash
cd frontend
npm install
```

---

## 🧪 Utveckling

### Starta båda servrar

#### Bash

```bash
python3 start_servers.py
```

#### PowerShell

```powershell
python .\start_servers.py
```

Backend körs på: `http://localhost:5000`  
Frontend körs på: `http://localhost:3000`

---

## 🧪 Testning

### Backend

```bash
cd backend
pytest
```

### Frontend

```bash
cd frontend
npm test
```

---

## 🧠 Bot-kommandon (via Makefile)

> ⚠️ `make` fungerar som standard i Bash/WSL/Git Bash. För PowerShell-användare: kör motsvarande Python- eller npm-kommando manuellt om `make` inte är installerat.

```bash
make run         # Startar live trading
make backtest    # Kör historisk backtest
make format      # Formatterar kod
make test        # Kör alla tester
make shell       # Interaktiv utvecklingssession
```

---

## 🛠 Konfiguration (`config.json`)

| Nyckel               | Beskrivning               |
|----------------------|---------------------------|
| `EXCHANGE`           | Ex: Bitfinex              |
| `SYMBOL`             | T.ex. BTC/USD             |
| `TIMEFRAME`          | Tidsram (ex: 1h)          |
| `EMA_LENGTH`         | EMA-längd (ex: 20)        |
| `VOLUME_MULTIPLIER`  | Min volymfaktor           |
| `STOP_LOSS_PERCENT`  | Stop-loss (ex: 2.5)       |
| `TAKE_PROFIT_PERCENT`| Take-profit (ex: 5.0)     |
| `RISK_PER_TRADE`     | Risknivå i % per trade    |

---

## 🔐 Säkerhet

- API-nycklar hanteras via `.env`
- Indatavalidering & HTTPS
- Säker nonce-hantering
- Logging av kritiska händelser

---

## 🤖 Instruktioner för Cursor AI

### 🧠 Teknikstack

#### 🔹 Backend (Python)

- Python 3.9+
- Flask (API + dashboard)
- Asynkron kodstruktur (`asyncio`)
- TA-Lib, pandas, numpy (indikatorer, datamanipulation)
- ccxt (börsintegration)
- Pydantic (konfigvalidering)
- pytest (testning)
- retry-decorator (felhantering)
- Docker, Makefile, .env, config.json

#### 🔹 Frontend (Next.js)

- Node.js v24, npm v11
- Next.js (React-baserad UI)
- src/pages/, templates/, app/ (standard Next-struktur)
- TypeScript / JavaScript (styrs av `jsconfig.json`)
- Konfigfiler: `next.config.js`, `package.json`, `package-lock.json`

#### 🛠 Viktigt

- Frontend körs via `npm run dev`
- Backend startas via `flask run` (via dashboard.py)
- Båda miljöer körs lokalt – inget är installerat globalt
- Cursor AI bör alltid förklara sina ändringar och inte anta något utan kontext.
- All kod ska vara testbar och dokumenterad om det påverkar användarflödet.

---

## 📜 Licens

None

## Starta dashboarden korrekt

För att undvika importfel, starta alltid dashboarden så här från projektroten:

```bash
python -m backend.src.dashboard
python -m dashboard
```

**Starta aldrig med:**  

```bash
python backend/src/dashboard.py
```

eller  

```bash
python dashboard.py
```

Detta ger importfel på grund av relativa imports i koden.
