# 🧠 Instruktioner för Cursor AI-assistent

Detta projekt består av en tradingbot med backend i Python/Flask och frontend i Next.js. Cursor AI-assistenten ska följa dessa instruktioner strikt.

---

## 🔹 Teknikstack

### Backend

- Python 3.9+
- Flask (API + dashboard)
- `asyncio` för asynkron struktur
- TA-Lib, pandas, numpy (indikatorer)
- ccxt (börsintegration)
- Pydantic (konfigvalidering)
- pytest (testning)
- retry-decorator (felhantering)
- Docker, Makefile, .env, config.json

### Frontend

- Node.js v24, npm v11
- Next.js med App Router (`src/app/`)
- TypeScript / JavaScript (jsconfig-styrt)
- ESLint, Prettier, next.config.js

---

## 🧠 Cursor-regler

### Kodförståelse

- Analysera strategin (FVG breakout med EMA, volym och tidsfönster)
- Förstå riskhantering (SL/TP, position sizing)
- Identifiera beroenden mellan moduler innan kodändringar görs

### Kodändringar

- Bevara asynkron struktur (`async def`) i `tradingbot.py`
- Använd alltid `retry-decorator` enligt befintligt mönster
- Validera konfig med `Pydantic`
- Säkerställ testbarhet med `pytest`

### Implementering

- Använd `edit_file()` – ändra endast det som behövs
- Lägg till alla nödvändiga `imports`
- Uppdatera relaterade tester om funktionalitet påverkas
- Följ PEP 8 och använd `black` + `isort`

### Varje ändring ska inkludera

- Förklaring av vad som ändras och varför
- Verifiering att ändringen fungerar
- Kontroll att alla tester passerar
- Uppdatering av dokumentation om nödvändigt

---

## 🧪 Användbara verktyg

- `run_terminal_cmd` – för att köra t.ex. `pytest`
- `grep_search` – för att hitta specifika mönster
- `list_dir` – för att navigera i strukturen

---

## 🛠 Cursor arbetsmetod

- Börja med att läsa filstruktur och beroenden
- Jobba stegvis, metodiskt och systematiskt
- Skriv underhållbar kod med tydliga kommentarer
- Kontrollera dina ändringar med tester
- Minimera risker och skapa inga dolda sidoeffekter
- Verifiera alltid filvägar innan du skapar eller raderar filer

---

## ❓ Om något är oklart

Cursor ska ställa frågor **innan** det gör antaganden. Hellre fråga än gissa.
