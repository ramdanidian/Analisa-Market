# 🤖 Automated Trading Analysis — Setup Guide

## Overview

This repository uses a **GitHub Actions workflow** to automatically analyze `forex_data.csv`
every time the file is updated (pushed to the repository).

The workflow calls the **GitHub Copilot API** (Claude Opus 4.5 as primary model and
Claude Sonnet 4.5 as verification model) to generate a comprehensive trading analysis
and commits the report back to the repo. Optionally, it creates a GitHub Issue and
sends a Telegram notification.

```
EA (MT5) pushes forex_data.csv every 5 minutes
         ↓
GitHub detects push → triggers workflow
         ↓
analyze_trading.py  → Copilot API (Claude Opus 4.5)
         ↓  (verification)
                    → Copilot API (Claude Sonnet 4.5)
         ↓
generate_report.py  → ANALYSIS_REPORT.md + analysis_history.json
         ↓
create_discussion.py → GitHub Issue (with Copilot agent session link)
         ↓  (optional)
notify_telegram.py  → Telegram bot message
         ↓
git commit + push   → results committed to repo
```

---

## Files

| File | Purpose |
|------|---------|
| `.github/workflows/auto-trading-analysis.yml` | Main GitHub Actions workflow |
| `scripts/analyze_trading.py` | Core analysis — calls Copilot API, returns JSON |
| `scripts/generate_report.py` | Generates Markdown report + maintains 30-day history |
| `scripts/create_discussion.py` | Creates a GitHub Issue with the analysis |
| `scripts/notify_telegram.py` | Sends a summary to Telegram (optional) |
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

### 3. (Optional) Add Telegram secrets

If you want Telegram notifications, add the following secrets under
**Settings → Secrets and variables → Actions → New repository secret**:

| Secret name | Value |
|-------------|-------|
| `TELEGRAM_BOT_TOKEN` | Your bot token from [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_CHAT_ID` | Your chat/channel ID (use [@userinfobot](https://t.me/userinfobot) to find it) |

No Telegram secrets = the notification step is automatically skipped.

### 4. Push `forex_data.csv`

Every time `forex_data.csv` is pushed (e.g. every 5 minutes from your MT5 EA),
the workflow runs automatically.

### 5. Manually trigger (optional)

Go to **Actions → Auto Trading Analysis → Run workflow** to trigger manually
with custom model and options.

---

## Workflow Inputs (manual trigger)

| Input | Default | Description |
|-------|---------|-------------|
| `model` | `claude-opus-4-5` | Primary analysis model |
| `create_issue` | `true` | Create a GitHub Issue with analysis |
| `send_telegram` | `false` | Send Telegram notification |

---

## AI Models

| Model ID | Role | Token limit |
|----------|------|-------------|
| `claude-opus-4-5` | Primary analysis (deep reasoning) | 200K |
| `claude-sonnet-4-5` | Verification pass (fast cross-check) | 200K |
| `gpt-4o` | Alternative if Claude unavailable | 128K |

All models are accessed via the **GitHub Copilot API**
(`https://api.githubcopilot.com/chat/completions`) using the built-in
`GITHUB_TOKEN` — no separate API key or billing required when you have an
active **Copilot Pro / Copilot Business** subscription.

---

## Analysis Output

### `ANALYSIS_REPORT.md` (Markdown)

The report includes:
- 🎯 **Final Recommendation** — BUY / SELL / HOLD with confidence %
- 📌 **Market Snapshot** — bid, ask, spread, session, volatility
- 💰 **Performance Summary** — win rate, P&L, trade stats
- 🛡️ **Risk Assessment** — exposure, open P&L, warnings
- 📉 **Technical Analysis** — M5, M15, H1 trends and key levels
- 📡 **Trading Signals** — entry, SL, TP, R/R ratio per timeframe
- ✅ **Verification** — second-opinion from Claude Sonnet

### `analysis_history.json` (JSON)

Rolling 30-day record of every analysis run. Each entry contains:

```json
{
  "timestamp": "2026-03-26T07:34:00+00:00",
  "symbol": "XAUUSD",
  "action": "BUY",
  "confidence_pct": 72,
  "entry_price": 4455.269,
  "stop_loss": 4440.0,
  "take_profit": 4480.0,
  "risk_reward_ratio": 1.6,
  "verification_agreement": "AGREE",
  "win_rate_pct": 40.0,
  "total_profit": 30.49,
  "risk_level": "LOW",
  "primary_model": "claude-opus-4-5"
}
```

---

## GitHub Issue / Copilot Agent Session

Each analysis creates a GitHub Issue labelled **`trading-analysis`** with:
- Summary card (action, confidence, entry/SL/TP)
- Full Markdown report in a collapsible section
- A direct link to start a **Copilot agent session** on the issue

To do a deeper interactive analysis, open the Issue and click the Copilot
icon to start an agent session. Example follow-up prompts:

```
Look at the active positions and the last 10 candles.
Is the current HOLD recommendation still valid or should I adjust?
```

```
Compare this analysis with the last 5 entries in analysis_history.json.
Is the win rate improving or declining?
```

```
Given the current M15 downtrend and RSI reading, what risk management
adjustments should I make to the open positions?
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Workflow not triggered | `forex_data.csv` not in repo root | Move file or update `paths` in workflow |
| `401 Unauthorized` from Copilot API | Token lacks Copilot scope | Ensure **Copilot Pro** is active on your account |
| `403` on issue creation | Workflow lacks write permission | Enable read/write in **Settings → Actions → General** |
| Telegram not sending | Missing secrets | Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` secrets |
| Empty history file | First run | Normal — history grows with each push |

---

## Privacy & Cost

- **No external API keys needed** — uses `GITHUB_TOKEN` (built-in, free)
- **No third-party services** — all processing in GitHub Actions
- **Copilot Pro** subscription covers all AI inference costs (no per-token billing)
- **Telegram bot** is optional and free for personal use

---

*Generated for [ramdanidian/Analisa-Market](https://github.com/ramdanidian/Analisa-Market)*
