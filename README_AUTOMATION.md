# 🤖 Automated Trading Analysis — Setup Guide

## Overview

This repository uses a **GitHub Actions workflow** to automatically analyze `forex_data.csv`
every time the file is updated (pushed to the repository).

All analysis is performed **locally in Python** using technical indicators — no external
AI subscription or API key is required.

```
EA (MT5) pushes forex_data.csv every 5 minutes
         ↓
GitHub detects push → triggers workflow
         ↓
analyze_trading.py  → Python technical analysis
                        RSI · EMA 9/21/50 · MACD · Bollinger Bands · ATR · S/R
         ↓  (cross-check)
                      → Rule-based second-opinion verification
         ↓
generate_report.py  → ANALYSIS_REPORT.md + analysis_history.json
         ↓
create_discussion.py → GitHub Issue (with Copilot agent session link)
         ↓  (always runs — skips gracefully if token absent)
notify_telegram.py  → Telegram bot message
         ↓
git commit + push   → results committed to repo
```

---

## Files

| File | Purpose |
|------|---------|
| `.github/workflows/auto-trading-analysis.yml` | Main GitHub Actions workflow |
| `scripts/analyze_trading.py` | Core analysis — pure Python indicators, returns JSON |
| `scripts/generate_report.py` | Generates Markdown report + maintains 30-day history |
| `scripts/create_discussion.py` | Creates a GitHub Issue with the analysis |
| `scripts/notify_telegram.py` | Sends a summary to Telegram |
| `ANALYSIS_REPORT.md` | Latest analysis report (auto-generated, committed by bot) |
| `analysis_history.json` | Rolling 30-day history of all analyses (auto-generated) |
| `analysis_result.json` | Raw JSON output of the last analysis run (CI artifact) |

---

## Quick Start

### 1. Enable GitHub Actions

GitHub Actions is enabled by default for public repositories. For private repos,
go to **Settings → Actions → General** and set to **"Allow all actions"**.

### 2. Configure repository permissions

Go to **Settings → Actions → General → Workflow permissions** and select:
- ✅ **Read and write permissions**
- ✅ **Allow GitHub Actions to create and approve pull requests**

### 3. Add Telegram bot token secret

The Telegram chat ID is already configured in the workflow (`1823341851`).
You only need to add the **bot token** as a secret:

Go to **Settings → Secrets and variables → Actions → New repository secret**:

| Secret name | Value |
|-------------|-------|
| `TELEGRAM_BOT_TOKEN` | Your bot token (from [@BotFather](https://t.me/BotFather)) |

> If this secret is not set the Telegram step is skipped automatically — no error.

### 4. Push `forex_data.csv`

Every time `forex_data.csv` is pushed (e.g. every 5 minutes from your MT5 EA),
the workflow runs automatically. No API keys or subscriptions needed.

### 5. Manually trigger (optional)

Go to **Actions → Auto Trading Analysis → Run workflow** to trigger manually.

---

## Workflow Inputs (manual trigger)

| Input | Default | Description |
|-------|---------|-------------|
| `create_issue` | `true` | Create a GitHub Issue with analysis |
| `send_telegram` | `true` | Send Telegram notification |

---

## Technical Indicators Used

| Indicator | Parameters | Purpose |
|-----------|-----------|---------|
| EMA | 9, 21, 50 | Trend direction & alignment |
| RSI | 14 | Momentum / overbought-oversold |
| MACD | 12, 26, 9 | Momentum crossover signals |
| Bollinger Bands | 20, 2σ | Volatility & breakout detection |
| ATR | 14 | Stop loss / take profit sizing |
| Support/Resistance | 30-bar swing | Key price levels |

Analysis runs on **M5, M15, and H1** timeframes simultaneously.
Final recommendation uses a **weighted vote** (H1=3, M15=2, M5=1).

---

## Analysis Output

### `ANALYSIS_REPORT.md` (Markdown)

- 🎯 **Final Recommendation** — BUY / SELL / HOLD with confidence %
- 📌 **Market Snapshot** — bid, ask, spread, session, volatility
- 💰 **Performance Summary** — win rate, P&L, trade stats
- 🛡️ **Risk Assessment** — exposure, open P&L, warnings
- 📉 **Technical Analysis** — M5, M15, H1 trends and key levels
- 📡 **Trading Signals** — entry, SL, TP, R/R ratio per timeframe
- ✅ **Verification** — rule-based second-opinion cross-check

### `analysis_history.json` (JSON)

Rolling 30-day record of every analysis run:

```json
{
  "timestamp": "2026-03-26T07:34:00+00:00",
  "symbol": "XAUUSD",
  "action": "SELL",
  "confidence_pct": 87,
  "entry_price": 4455.053,
  "stop_loss": 4511.368,
  "take_profit": 4361.195,
  "risk_reward_ratio": 1.67,
  "verification_agreement": "DISAGREE",
  "win_rate_pct": 20.0,
  "total_profit": 29.97,
  "risk_level": "LOW",
  "primary_model": "python-technical-analysis-v1"
}
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Workflow not triggered | `forex_data.csv` not in repo root | Move file or update `paths` in workflow |
| `403` on issue creation | Workflow lacks write permission | Enable read/write in **Settings → Actions → General** |
| Telegram not sending | Missing `TELEGRAM_BOT_TOKEN` secret | Add the bot token secret (see Quick Start step 3) |
| Empty history file | First run | Normal — history grows with each push |

---

## Privacy & Cost

- **No external API keys needed** — analysis is pure Python
- **No third-party AI services** — all processing in GitHub Actions (free)
- **Telegram bot** requires adding one repository secret (`TELEGRAM_BOT_TOKEN`)

---

*Generated for [ramdanidian/Analisa-Market](https://github.com/ramdanidian/Analisa-Market)*
