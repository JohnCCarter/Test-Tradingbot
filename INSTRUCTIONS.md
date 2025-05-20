# Instruktioner för AI-assistent

## 🧠 Teknikstack

### 🔹 Backend (Python)

* Python 3.9+
* Flask (API + dashboard)
* Asynkron kodstruktur (`asyncio`)
* TA-Lib, pandas, numpy (indikatorer, datamanipulation)
* ccxt (börsintegration)
* Pydantic (konfigvalidering)
* pytest (testning)
* retry-decorator (felhantering)
* Docker, Makefile, .env, config.json

### 🔹 Frontend (Next.js)

* Node.js v24, npm v11
* Next.js (React-baserad UI)
* src/pages/, templates/, app/ (standard Next-struktur)
* TypeScript / JavaScript (styrs av `jsconfig.json`)
* Konfigfiler: `next.config.js`, `package.json`, `package-lock.json`

### 🛠 Viktigt:

* Frontend körs via `npm run dev`
* Backend startas via `flask run` (via dashboard.py)
* Båda miljöer körs lokalt – inget är installerat globalt

---

När du hjälper mig med min tradingbot, vänligen:

1. Förstå koden:

* Analysera tradingstrategin (FVG breakout med EMA, volym och trading-tider)
* Förstå risk management (position sizing, SL/TP)
* Identifiera beroenden mellan moduler

2. Vid kodändringar:

* Behåll den asynkrona strukturen i tradingbot.py
* Följ den etablerade felhanteringslogiken med retry-decorator
* Använd Pydantic för konfigurationsvalidering
* Upprätthåll testbarheten med pytest

3. När du implementerar ändringar:

* Använd edit\_file för att göra ändringar
* Lägg till nödvändiga imports
* Uppdatera relevanta tester
* Följ PEP 8 och använd black/isort

4. För varje ändring:

* Förklara vad som ändras och varför
* Verifiera att ändringarna fungerar
* Kontrollera att testerna passerar
* Uppdatera dokumentation vid behov

5. Vid behov:

* Använd run\_terminal\_cmd för att köra kommandon
* Använd grep\_search för att hitta specifika mönster
* Använd list\_dir för att utforska filstrukturen

6.

* Jobba stegvis, systematiskt, metodiskt.
* Skriv kod som är lättläst och underhållbar.
* Använd kommentarer och dokumentation för att förklara dina tankar och åtgärder.
* Kontrollera alltid dina ändringar med hjälp av tester och kontrollfunktioner.
* Försök att minimera risker och potentiella problem.

Om något är oklart eller om du behöver mer information, fråga gärna!
