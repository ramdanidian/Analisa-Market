#!/usr/bin/env python3
"""
Forex Market Analyzer
Reads forex_data.csv and outputs a single final trading decision.
"""

import os


DATA_FILE = os.path.join(os.path.dirname(__file__), "forex_data.csv")


def parse_csv(filepath):
    sections = {}
    current_section = None
    current_headers = None
    current_rows = []

    metadata = {}

    with open(filepath, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()

            # Skip empty lines and top-level comments
            if not line:
                if current_section and current_rows:
                    sections[current_section] = {
                        "headers": current_headers,
                        "rows": current_rows,
                    }
                    current_section = None
                    current_headers = None
                    current_rows = []
                continue

            # Section headers (e.g.  # M5 CANDLES …)
            if line.startswith("# ") and not line.startswith("# Generated") and not line.startswith("# Symbol") and not line.startswith("# Last") and not line.startswith("# MARKET"):
                if current_section and current_rows:
                    sections[current_section] = {
                        "headers": current_headers,
                        "rows": current_rows,
                    }
                current_section = line[2:].strip()
                current_headers = None
                current_rows = []
                continue

            # Metadata key-value pairs (no commas used as delimiter)
            if current_section == "PAIR INFORMATION":
                parts = line.split(",", 1)
                if len(parts) == 2:
                    metadata[parts[0].strip()] = parts[1].strip()
                continue

            # Header row (first non-comment row inside a section)
            if current_section and current_headers is None:
                current_headers = [h.strip() for h in line.split(",")]
                continue

            # Data rows
            if current_section and current_headers:
                values = [v.strip() for v in line.split(",")]
                if len(values) >= len(current_headers):
                    row = dict(zip(current_headers, values))
                    current_rows.append(row)

    # flush last section
    if current_section and current_rows:
        sections[current_section] = {
            "headers": current_headers,
            "rows": current_rows,
        }

    return metadata, sections


def trend_score(candles):
    """
    Returns a value between -1.0 (fully bearish) and +1.0 (fully bullish).
    Weighted so that recent candles count more.
    """
    if not candles:
        return 0.0
    total_weight = 0.0
    weighted_sum = 0.0
    for i, c in enumerate(candles):
        weight = i + 1  # most recent candle (last in list) gets highest weight
        direction = 1 if c.get("Direction", "").upper() == "UP" else -1
        weighted_sum += direction * weight
        total_weight += weight
    return weighted_sum / total_weight


def price_momentum(candles):
    """Returns net change from first candle open to last candle close."""
    if len(candles) < 2:
        return 0.0
    try:
        start = float(candles[0]["Open"])
        end = float(candles[-1]["Close"])
        return end - start
    except (KeyError, ValueError):
        return 0.0


def analyze(filepath=DATA_FILE):
    metadata, sections = parse_csv(filepath)

    # ── Current price ───────────────────────────────────────────────────────
    try:
        bid = float(metadata.get("Current Bid", "0"))
        ask = float(metadata.get("Current Ask", "0"))
    except ValueError:
        bid = ask = 0.0

    symbol = metadata.get("Pair", "UNKNOWN")
    server_time = metadata.get("Server Time", "")

    # ── Candle data ──────────────────────────────────────────────────────────
    m5_candles  = sections.get("M5 CANDLES (Last 10 closed)",  {}).get("rows", [])
    m15_candles = sections.get("M15 CANDLES (Last 10 closed)", {}).get("rows", [])
    h1_candles  = sections.get("H1 CANDLES (Last 10 closed)",  {}).get("rows", [])

    # Candles in the file are most-recent-first; reverse so oldest is index 0
    # (trend_score gives index-based weight so highest index = most recent = most weight)
    m5_candles  = list(reversed(m5_candles))
    m15_candles = list(reversed(m15_candles))
    h1_candles  = list(reversed(h1_candles))

    m5_score  = trend_score(m5_candles)
    m15_score = trend_score(m15_candles)
    h1_score  = trend_score(h1_candles)

    # momentum: oldest-open → newest-close (negative = falling price)
    m5_mom  = price_momentum(m5_candles)
    m15_mom = price_momentum(m15_candles)
    h1_mom  = price_momentum(h1_candles)

    # ── Active positions ─────────────────────────────────────────────────────
    active_rows = sections.get("ACTIVE POSITIONS", {}).get("rows", [])
    active_types = [r.get("Type", "").upper() for r in active_rows]
    active_profit = sum(
        float(r.get("Profit", 0)) for r in active_rows if r.get("Profit", "-") != "-"
    )

    # ── Composite score (H1 weighted most) ──────────────────────────────────
    composite = (m5_score * 0.25) + (m15_score * 0.35) + (h1_score * 0.40)

    # Incorporate momentum alignment as a small boost to confidence
    # (if all three momentum values agree with the trend direction, +10% confidence)
    tf_scores = {"M5": m5_score, "M15": m15_score, "H1": h1_score}
    bearish_tfs = [tf for tf, s in tf_scores.items() if s < 0]
    bullish_tfs = [tf for tf, s in tf_scores.items() if s > 0]

    THRESHOLD = 0.15  # minimum absolute score to trigger directional signal

    # Confidence: how far the composite is from 0, scaled to 0-100
    raw_confidence = int(min(abs(composite) / 1.0, 1.0) * 100)

    if composite <= -THRESHOLD:
        decision = "SELL"
        agreeing = bearish_tfs
        confidence = min(100, raw_confidence + (10 if len(agreeing) == 3 else 0))
        if len(agreeing) == 3:
            reason = "Tren bearish pada semua timeframe (M5, M15, H1)"
        else:
            reason = f"Tren bearish dominan – timeframe bearish: {', '.join(agreeing)}"
    elif composite >= THRESHOLD:
        decision = "BUY"
        agreeing = bullish_tfs
        confidence = min(100, raw_confidence + (10 if len(agreeing) == 3 else 0))
        if len(agreeing) == 3:
            reason = "Tren bullish pada semua timeframe (M5, M15, H1)"
        else:
            reason = f"Tren bullish dominan – timeframe bullish: {', '.join(agreeing)}"
    else:
        decision = "HOLD"
        confidence = 100 - raw_confidence
        reason = "Sinyal tidak jelas / pasar sideways"

    # ── Print report ─────────────────────────────────────────────────────────
    separator = "=" * 60
    print(separator)
    print(f"  ANALISA FOREX  |  {symbol}  |  {server_time}")
    print(separator)
    print(f"  Harga Saat Ini : Bid {bid:.3f}  /  Ask {ask:.3f}")
    print()
    print("  SKOR TREN PER TIMEFRAME")
    print(f"    M5  : {m5_score:+.2f}  (momentum: {m5_mom:+.3f})")
    print(f"    M15 : {m15_score:+.2f}  (momentum: {m15_mom:+.3f})")
    print(f"    H1  : {h1_score:+.2f}  (momentum: {h1_mom:+.3f})")
    print(f"    GABUNGAN (weighted) : {composite:+.2f}")
    print()
    if active_rows:
        print(f"  POSISI AKTIF   : {len(active_rows)} posisi  "
              f"({', '.join(active_types)})  |  Profit: {active_profit:+.2f}")
        print()
    print(separator)
    print(f"  KEPUTUSAN FINAL  :  *** {decision} ***")
    print(f"  Alasan           :  {reason}")
    print(f"  Keyakinan        :  {confidence}%")
    print(separator)

    return decision


if __name__ == "__main__":
    analyze()
