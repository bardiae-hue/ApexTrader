# apex/trader

**Autonomous AI stock trading simulator powered by a local LLM.**

Apex Trader is a browser-based paper trading app that connects a local [Ollama](https://ollama.com) model to live Yahoo Finance price data. The AI reads real-time market indicators, manages a virtual portfolio, and executes trades — entirely on its own, with no hardcoded rules or signal thresholds.

![idle](https://img.shields.io/badge/status-paper%20trading%20only-blue) ![ollama](https://img.shields.io/badge/requires-ollama-black)

---

## How it works

Every N seconds (configurable, default 30s), the AI receives a structured prompt containing:

- Live price data and technical indicators (RSI, SMA5/20, momentum, volatility) for every watched ticker
- Current portfolio state: cash, open positions, unrealised P&L, trailing stops
- A rolling performance memory: per-symbol win rates, condition tags, consecutive loss streaks
- Recent closed trade history so the model can learn from mistakes

The model responds with a JSON decision object — `BUY`, `SELL`, or `HOLD` for each symbol, with a dollar amount, confidence score, and short reasoning. The app executes those decisions, enforcing hard guardrails the AI cannot override.

---

## Features

- **Fully autonomous** — the LLM decides what to buy, what to sell, and how much. No rule-based triggers.
- **Self-tuning risk** — an adaptive risk multiplier shrinks after losses and recovers slowly after wins, throttling position sizes automatically.
- **Compounding** — position sizes scale proportionally with portfolio growth.
- **Hard guardrails** — capital floor (−8% from start triggers full lockout), hard stop-loss per position, confidence gate (trades blocked below 60%), and consecutive-loss throttle.
- **Trailing stops** — 1.5% trailing stop updated on every price tick, independent of the AI.
- **40-ticker universe** — Mega-cap, volatile tech, finance, growth stocks, and broad ETFs, all toggleable from the watchlist.
- **Live charting** — normalised multi-series chart, single-symbol chart with entry/stop overlays, and a portfolio equity curve.
- **Full session memory** — per-symbol stats, condition-tag performance, win/loss streaks, best/worst trade, annualised return estimate.

---

## Requirements

| Dependency | Purpose |
|---|---|
| [Ollama](https://ollama.com) | Runs the LLM locally |
| `llama3.2` (or any supported model) | The trading brain |
| Python 3 | CORS proxy for Yahoo Finance |
| A modern browser | UI |

No Node.js, no build step, no API keys.

---

## Quick start

**1. Install Ollama and pull a model**

```bash
# Install from https://ollama.com, then:
ollama pull llama3.2
```

Other supported models: `phi3` (fastest), `llama3.1`, `gemma2`, `mistral`, `qwen2.5`.

**2. Run the CORS proxy**

Yahoo Finance blocks direct browser requests. A one-file Python proxy handles this:

```bash
python proxy.py
```

The proxy listens on `http://localhost:8765` and forwards requests to Yahoo Finance.

**3. Open the app**

Open `index.html` in your browser. No server required.

**4. Configure and start**

- Set your starting cash, max trade size, and max positions
- Toggle tickers on/off in the watchlist (or use the category buttons)
- Press **▶ Start**

The AI will fetch live prices, build its market snapshot, and begin making decisions immediately.

---

## Configuration

| Setting | Default | Description |
|---|---|---|
| Starting cash | $10,000 | Virtual account balance |
| Max single trade | $2,000 | Hard cap per trade (AI scales within this) |
| Hard stop loss | 4% | Forced sell if position drops this far from entry |
| Max positions | 4 | Maximum concurrent open positions |
| Cooldown | 5 min | Minimum time between trades on the same symbol |
| AI interval | 30 sec | How often the AI runs a full decision cycle |
| Price refresh | 10 sec | How often prices are fetched from Yahoo Finance |

---

## AI prompt design

The prompt given to the model each cycle includes strict rules the model is instructed to follow:

- **Capital floor**: if portfolio ≤ 92% of starting value, hold everything
- **Consecutive loss throttle**: after 3 losses in a row, max 1 buy per cycle capped at $100
- **Overbought gate**: no buys when RSI > 68
- **Trend filter**: only buy stocks above SMA20, unless RSI < 32 (deep oversold exception)
- **Partial profit-taking**: sell 50–70% when a position hits +0.8%, let the rest ride
- **Compounding instruction**: position sizes must scale with the portfolio growth factor

The model can deviate from these in its reasoning, but the JavaScript execution layer enforces the hard limits regardless of what the model outputs.

---

## Project structure

```
apex-trader/
├── index.html      # Entire app — UI, logic, charting, AI integration
├── proxy.py        # Python CORS proxy for Yahoo Finance
└── README.md
```

The entire trading engine is in a single HTML file (~1,000 lines of vanilla JS). There are no dependencies, frameworks, or build tools.

---

## Supported models

| Model | Speed | Quality | Notes |
|---|---|---|---|
| `phi3` | ⚡ Fastest | Good | Best for quick iteration |
| `llama3.2` | Fast | Very good | **Recommended** |
| `llama3.1` | Moderate | Very good | Larger context |
| `gemma2` | Moderate | Good | — |
| `mistral` | Moderate | Good | — |
| `qwen2.5` | Moderate | Good | Strong at structured output |

Smaller/faster models may occasionally produce malformed JSON. The app handles parse failures gracefully and logs the raw response for debugging.

---

## Disclaimer

This is a **paper trading simulator**. It uses real market data but executes no real trades.
