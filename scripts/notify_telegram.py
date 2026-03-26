#!/usr/bin/env python3
"""
notify_telegram.py - Send a concise Telegram notification with key trading insights.

Reads analysis_result.json and sends a formatted message to a Telegram chat
via the Bot API.

Usage:
    python scripts/notify_telegram.py --input analysis_result.json

Environment variables required:
    8733820401:AAHwfK5O1_2rN421UDW1r43CvYpxGk9vY8U  - Telegram bot token (from @BotFather)
    1823341851    - Target chat/channel ID
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import requests

TELEGRAM_API = "https://api.telegram.org"


# ---------------------------------------------------------------------------
# Message builder
# ---------------------------------------------------------------------------

def build_message(result: dict) -> str:
    rec = result.get("final_recommendation", {})
    ver = result.get("verification", {})
    perf = result.get("performance_summary", {})
    risk = result.get("risk_assessment", {})
    ctx = result.get("market_context", {})
    ta = result.get("technical_analysis", {})

    symbol = result.get("symbol", "XAUUSD")
    ts = result.get("analysis_timestamp", datetime.now(timezone.utc).isoformat())
    action = rec.get("action", "HOLD")
    conf = rec.get("confidence_pct", "?")
    entry = rec.get("entry_price", "?")
    sl = rec.get("stop_loss", "?")
    tp = rec.get("take_profit", "?")
    rr = rec.get("risk_reward_ratio", "?")

    action_icon = {"BUY": "🟢 BUY", "SELL": "🔴 SELL", "HOLD": "🟡 HOLD"}.get(action, action)
    risk_level = risk.get("risk_level", "N/A")
    risk_icon = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴", "CRITICAL": "⛔"}.get(risk_level, "")

    # Trend line
    m5_trend = ta.get("m5", {}).get("trend", "?")
    m15_trend = ta.get("m15", {}).get("trend", "?")
    h1_trend = ta.get("h1", {}).get("trend", "?")
    trend_icon = {"BULLISH": "📈", "BEARISH": "📉", "SIDEWAYS": "↔️"}

    def ti(t):
        return trend_icon.get(t, "❓") + " " + t

    win_rate = perf.get("win_rate_pct", "?")
    total_profit = perf.get("total_profit", "?")
    win_trades = perf.get("winning_trades", "?")
    lose_trades = perf.get("losing_trades", "?")

    ver_agreement = ver.get("agreement_level", "N/A")
    ver_action = ver.get("adjusted_action", action)
    ver_conf = ver.get("adjusted_confidence_pct", conf)

    reasoning = rec.get("reasoning", "N/A")
    # Truncate long reasoning for Telegram
    if len(str(reasoning)) > 200:
        reasoning = str(reasoning)[:197] + "..."

    session = ctx.get("session", "N/A")
    volatility = ctx.get("volatility", "N/A")

    time_str = ts[:16].replace("T", " ")

    msg = (
        f"📊 *TRADING ANALYSIS — {symbol}*\n"
        f"🕐 `{time_str} UTC`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"*RECOMMENDATION*\n"
        f"  {action_icon} @ `{entry}`\n"
        f"  🎯 Confidence: *{conf}%*\n"
        f"  🛑 Stop Loss: `{sl}`\n"
        f"  ✅ Take Profit: `{tp}`\n"
        f"  ⚖️ R/R Ratio: `{rr}`\n\n"
        f"*TECHNICAL TRENDS*\n"
        f"  M5: {ti(m5_trend)}  |  M15: {ti(m15_trend)}  |  H1: {ti(h1_trend)}\n"
        f"  Session: {session}  |  Volatility: {volatility}\n\n"
        f"*PERFORMANCE*\n"
        f"  Win Rate: *{win_rate}%*  ({win_trades}W / {lose_trades}L)\n"
        f"  Total P&L: `{total_profit}`\n\n"
        f"*RISK*\n"
        f"  {risk_icon} Level: *{risk_level}*\n"
        f"  Positions: {risk.get('active_positions_count', 0)}\n\n"
        f"*VERIFICATION* ({ver_agreement})\n"
        f"  → {ver_action} @ {ver_conf}%\n\n"
        f"*REASONING*\n"
        f"_{reasoning}_\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"_Automated analysis · For info only_"
    )
    return msg


# ---------------------------------------------------------------------------
# Send helpers
# ---------------------------------------------------------------------------

def send_message(bot_token: str, chat_id: str, text: str) -> bool:
    url = f"{TELEGRAM_API}/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    resp = requests.post(url, json=payload, timeout=30)
    if resp.status_code == 200:
        return True
    print(f"[ERROR] Telegram API error {resp.status_code}: {resp.text[:300]}")
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Send Telegram notification with trading insights")
    parser.add_argument("--input", required=True, help="Path to analysis_result.json")
    args = parser.parse_args()

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("[ERROR] TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set")
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        result = json.load(f)

    print("[INFO] Building Telegram message...")
    message = build_message(result)

    print(f"[INFO] Sending to chat {chat_id}...")
    ok = send_message(bot_token, chat_id, message)
    if ok:
        print("[INFO] Telegram notification sent successfully")
    else:
        print("[ERROR] Failed to send Telegram notification")
        sys.exit(1)


if __name__ == "__main__":
    main()
