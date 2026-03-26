#!/usr/bin/env python3
"""
generate_report.py - Generate Markdown + JSON analysis reports and maintain history.

Reads analysis_result.json, writes ANALYSIS_REPORT.md, and appends to
analysis_history.json (retaining 30 days of records).

Usage:
    python scripts/generate_report.py \
        --input analysis_result.json \
        --report ANALYSIS_REPORT.md \
        --history analysis_history.json
"""

import argparse
import json
import os
from datetime import datetime, timezone, timedelta


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def trend_emoji(trend: str) -> str:
    return {"BULLISH": "📈", "BEARISH": "📉", "SIDEWAYS": "↔️"}.get(trend, "❓")


def action_emoji(action: str) -> str:
    return {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(action, "❓")


def risk_emoji(level: str) -> str:
    return {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴", "CRITICAL": "⛔"}.get(level, "❓")


def confidence_bar(pct) -> str:
    """Convert 0-100 confidence to a simple bar."""
    try:
        val = int(float(pct))
    except (TypeError, ValueError):
        return "░░░░░░░░░░ N/A"
    filled = val // 10
    bar = "█" * filled + "░" * (10 - filled)
    return f"{bar} {val}%"


def fmt_float(val, decimals=3) -> str:
    try:
        return f"{float(val):.{decimals}f}"
    except (TypeError, ValueError):
        return str(val)


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_markdown(result: dict) -> str:
    ts = result.get("analysis_timestamp", datetime.now(timezone.utc).isoformat())
    symbol = result.get("symbol", "XAUUSD")
    primary_model = result.get("primary_model", "N/A")
    verification_model = result.get("verification_model", "N/A")

    price = result.get("current_price", {})
    bid = fmt_float(price.get("bid"), 3)
    ask = fmt_float(price.get("ask"), 3)
    spread = fmt_float(price.get("spread_pips"), 1)

    perf = result.get("performance_summary", {})
    risk = result.get("risk_assessment", {})
    ta = result.get("technical_analysis", {})
    signals = result.get("trading_signals", [])
    rec = result.get("final_recommendation", {})
    ctx = result.get("market_context", {})
    ver = result.get("verification", {})

    lines = []

    # --- Header ---
    lines.append(f"# 📊 Trading Analysis Report — {symbol}")
    lines.append(f"")
    lines.append(f"> **Generated:** {ts}  ")
    lines.append(f"> **Models:** {primary_model} (primary) · {verification_model} (verification)")
    lines.append(f"")
    lines.append("---")
    lines.append("")

    # --- Quick summary box ---
    action = rec.get("action", "?")
    lines.append("## 🎯 Final Recommendation")
    lines.append("")
    lines.append(f"| Field | Value |")
    lines.append(f"|-------|-------|")
    lines.append(f"| **Action** | {action_emoji(action)} **{action}** |")
    lines.append(f"| **Confidence** | {confidence_bar(rec.get('confidence_pct'))} |")
    lines.append(f"| **Entry Price** | {fmt_float(rec.get('entry_price'))} |")
    lines.append(f"| **Stop Loss** | {fmt_float(rec.get('stop_loss'))} |")
    lines.append(f"| **Take Profit** | {fmt_float(rec.get('take_profit'))} |")
    lines.append(f"| **Risk/Reward** | {fmt_float(rec.get('risk_reward_ratio'), 2)} |")
    lines.append(f"| **Position Size** | {rec.get('position_size_suggestion', 'N/A')} |")
    lines.append(f"| **Time Horizon** | {rec.get('time_horizon', 'N/A')} |")
    lines.append(f"| **Invalidation** | {fmt_float(rec.get('invalidation_level'))} |")
    lines.append("")
    if rec.get("reasoning"):
        lines.append(f"**Reasoning:** {rec['reasoning']}")
        lines.append("")
    key_risks = rec.get("key_risks", [])
    if key_risks:
        lines.append("**Key Risks:**")
        for r in key_risks:
            lines.append(f"- ⚠️ {r}")
        lines.append("")

    # Verification badge
    agreement = ver.get("agreement_level", "N/A")
    adj_action = ver.get("adjusted_action", action)
    adj_conf = ver.get("adjusted_confidence_pct", rec.get("confidence_pct", "?"))
    lines.append(f"**Verification ({verification_model}):** `{agreement}` → {action_emoji(adj_action)} {adj_action} @ {adj_conf}% confidence")
    if ver.get("notes"):
        lines.append(f"> {ver['notes']}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # --- Market snapshot ---
    lines.append("## 📌 Market Snapshot")
    lines.append("")
    lines.append(f"| | |")
    lines.append(f"|--|--|")
    lines.append(f"| Bid | {bid} |")
    lines.append(f"| Ask | {ask} |")
    lines.append(f"| Spread | {spread} pips |")
    lines.append(f"| Volatility | {ctx.get('volatility', 'N/A')} |")
    lines.append(f"| Session | {ctx.get('session', 'N/A')} |")
    lines.append(f"| Sentiment | {trend_emoji(ctx.get('market_sentiment',''))} {ctx.get('market_sentiment', 'N/A')} |")
    lines.append("")
    if ctx.get("commentary"):
        lines.append(ctx["commentary"])
    lines.append("")
    lines.append("---")
    lines.append("")

    # --- Performance Summary ---
    lines.append("## 💰 Performance Summary")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Closed Deals | {perf.get('closed_deals_count', 'N/A')} |")
    lines.append(f"| Winning Trades | {perf.get('winning_trades', 'N/A')} |")
    lines.append(f"| Losing Trades | {perf.get('losing_trades', 'N/A')} |")
    lines.append(f"| Win Rate | {fmt_float(perf.get('win_rate_pct'), 1)}% |")
    lines.append(f"| Total Profit | {fmt_float(perf.get('total_profit'), 2)} |")
    lines.append(f"| Avg Profit/Trade | {fmt_float(perf.get('avg_profit_per_trade'), 2)} |")
    lines.append(f"| Best Trade | {fmt_float(perf.get('best_trade_profit'), 2)} |")
    lines.append(f"| Worst Trade | {fmt_float(perf.get('worst_trade_profit'), 2)} |")
    lines.append("")
    if perf.get("commentary"):
        lines.append(perf["commentary"])
    lines.append("")
    lines.append("---")
    lines.append("")

    # --- Risk Assessment ---
    risk_level = risk.get("risk_level", "N/A")
    lines.append(f"## {risk_emoji(risk_level)} Risk Assessment")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Risk Level | {risk_emoji(risk_level)} **{risk_level}** |")
    lines.append(f"| Active Positions | {risk.get('active_positions_count', 'N/A')} |")
    lines.append(f"| Total Exposure | {fmt_float(risk.get('total_exposure_lots'), 2)} lots |")
    lines.append(f"| Open P&L | {fmt_float(risk.get('open_pnl'), 2)} |")
    lines.append("")
    warnings = risk.get("risk_warnings", [])
    if warnings:
        lines.append("**Warnings:**")
        for w in warnings:
            lines.append(f"- ⚠️ {w}")
        lines.append("")
    if risk.get("commentary"):
        lines.append(risk["commentary"])
    lines.append("")
    lines.append("---")
    lines.append("")

    # --- Technical Analysis ---
    lines.append("## 📉 Technical Analysis")
    lines.append("")
    for tf_key, label in [("m5", "M5"), ("m15", "M15"), ("h1", "H1")]:
        tf = ta.get(tf_key, {})
        trend = tf.get("trend", "N/A")
        levels = tf.get("key_levels", {})
        tf_signals = tf.get("signals", [])
        lines.append(f"### {label} — {trend_emoji(trend)} {trend} (Strength: {tf.get('strength', 'N/A')}/100)")
        lines.append("")
        lines.append(f"| | |")
        lines.append(f"|--|--|")
        lines.append(f"| Last Close | {fmt_float(tf.get('last_close'))} |")
        lines.append(f"| Support | {fmt_float(levels.get('support'))} |")
        lines.append(f"| Resistance | {fmt_float(levels.get('resistance'))} |")
        lines.append("")
        if tf_signals:
            lines.append("**Signals:**")
            for s in tf_signals:
                lines.append(f"- {s}")
            lines.append("")
        if tf.get("commentary"):
            lines.append(f"*{tf['commentary']}*")
        lines.append("")

    lines.append("---")
    lines.append("")

    # --- Trading Signals ---
    lines.append("## 📡 Trading Signals")
    lines.append("")
    if not signals:
        lines.append("*No trading signals detected.*")
    else:
        lines.append("| TF | Action | Entry | SL | TP | R/R | Confidence | Reason |")
        lines.append("|----|--------|-------|----|----|-----|------------|--------|")
        for sig in signals:
            sig_action = sig.get("type", "?")
            lines.append(
                f"| {sig.get('timeframe','?')} "
                f"| {action_emoji(sig_action)} {sig_action} "
                f"| {fmt_float(sig.get('entry_price'))} "
                f"| {fmt_float(sig.get('stop_loss'))} "
                f"| {fmt_float(sig.get('take_profit'))} "
                f"| {fmt_float(sig.get('risk_reward_ratio'), 2)} "
                f"| {sig.get('confidence_pct','?')}% "
                f"| {sig.get('reason','?')} |"
            )
    lines.append("")
    lines.append("---")
    lines.append("")

    # --- Footer ---
    lines.append("*This report is generated automatically by the GitHub Actions trading analysis workflow.*  ")
    lines.append("*Use for informational purposes only. Always apply your own judgment before trading.*")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# History management
# ---------------------------------------------------------------------------

def update_history(history_path: str, result: dict, max_days: int = 30):
    """Append the current result to history, pruning entries older than max_days."""
    history = []
    if os.path.exists(history_path):
        with open(history_path, "r", encoding="utf-8") as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = []

    # Create a compact history entry
    rec = result.get("final_recommendation", {})
    ver = result.get("verification", {})
    entry = {
        "timestamp": result.get("analysis_timestamp", datetime.now(timezone.utc).isoformat()),
        "symbol": result.get("symbol", "XAUUSD"),
        "action": rec.get("action"),
        "confidence_pct": rec.get("confidence_pct"),
        "entry_price": rec.get("entry_price"),
        "stop_loss": rec.get("stop_loss"),
        "take_profit": rec.get("take_profit"),
        "risk_reward_ratio": rec.get("risk_reward_ratio"),
        "verification_agreement": ver.get("agreement_level"),
        "win_rate_pct": result.get("performance_summary", {}).get("win_rate_pct"),
        "total_profit": result.get("performance_summary", {}).get("total_profit"),
        "risk_level": result.get("risk_assessment", {}).get("risk_level"),
        "primary_model": result.get("primary_model"),
    }
    history.append(entry)

    # Prune entries older than max_days
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_days)
    pruned = []
    for h in history:
        try:
            h_ts = datetime.fromisoformat(h["timestamp"].replace("Z", "+00:00"))
            if h_ts >= cutoff:
                pruned.append(h)
        except (ValueError, KeyError):
            pruned.append(h)  # keep entries with unparseable timestamps

    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(pruned, f, indent=2, ensure_ascii=False)

    print(f"[INFO] History updated: {len(pruned)} entries kept (max {max_days} days)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate trading analysis report")
    parser.add_argument("--input", required=True, help="Path to analysis_result.json")
    parser.add_argument("--report", required=True, help="Path to output Markdown report")
    parser.add_argument("--history", required=True, help="Path to analysis history JSON")
    parser.add_argument("--max-days", type=int, default=30, help="Days to retain in history")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        result = json.load(f)

    print("[INFO] Generating Markdown report...")
    md = generate_markdown(result)
    with open(args.report, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[INFO] Report written to {args.report}")

    print("[INFO] Updating analysis history...")
    update_history(args.history, result, max_days=args.max_days)


if __name__ == "__main__":
    main()
