#!/usr/bin/env python3
"""
create_discussion.py - Create a GitHub Issue with the trading analysis results.

Uses the GitHub REST API to create a labelled Issue containing the full
Markdown report so that Copilot agent sessions can be started from it.

Usage:
    python scripts/create_discussion.py \
        --input analysis_result.json \
        --report ANALYSIS_REPORT.md

Environment variables required:
    GITHUB_TOKEN   - GitHub token with issues:write permission
    REPO_OWNER     - Repository owner (username or org)
    REPO_NAME      - Repository name
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import requests

GITHUB_API = "https://api.github.com"
LABEL_NAME = "trading-analysis"
LABEL_COLOR = "0075ca"
LABEL_DESC = "Automated trading analysis report"


# ---------------------------------------------------------------------------
# GitHub helpers
# ---------------------------------------------------------------------------

def github_request(method: str, path: str, token: str, **kwargs) -> requests.Response:
    """Make an authenticated GitHub API request."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    url = f"{GITHUB_API}{path}"
    resp = getattr(requests, method)(url, headers=headers, timeout=30, **kwargs)
    return resp


def ensure_label(owner: str, repo: str, token: str) -> bool:
    """Create the analysis label if it does not exist yet."""
    check = github_request("get", f"/repos/{owner}/{repo}/labels/{LABEL_NAME}", token)
    if check.status_code == 200:
        return True
    if check.status_code == 404:
        create = github_request(
            "post",
            f"/repos/{owner}/{repo}/labels",
            token,
            json={"name": LABEL_NAME, "color": LABEL_COLOR, "description": LABEL_DESC},
        )
        return create.status_code == 201
    return False


def create_issue(owner: str, repo: str, token: str, title: str, body: str) -> dict:
    """Create a GitHub Issue and return the response JSON."""
    ensure_label(owner, repo, token)
    resp = github_request(
        "post",
        f"/repos/{owner}/{repo}/issues",
        token,
        json={
            "title": title,
            "body": body,
            "labels": [LABEL_NAME],
        },
    )
    if resp.status_code == 201:
        return resp.json()
    raise RuntimeError(
        f"Failed to create issue ({resp.status_code}): {resp.text[:300]}"
    )


# ---------------------------------------------------------------------------
# Body builder
# ---------------------------------------------------------------------------

def build_issue_body(result: dict, report_md: str) -> str:
    """Build the issue body: summary card + full report."""
    rec = result.get("final_recommendation", {})
    ver = result.get("verification", {})
    perf = result.get("performance_summary", {})
    risk = result.get("risk_assessment", {})
    ts = result.get("analysis_timestamp", datetime.now(timezone.utc).isoformat())
    symbol = result.get("symbol", "XAUUSD")

    action = rec.get("action", "?")
    conf = rec.get("confidence_pct", "?")
    entry = rec.get("entry_price", "?")
    sl = rec.get("stop_loss", "?")
    tp = rec.get("take_profit", "?")
    rr = rec.get("risk_reward_ratio", "?")

    action_icon = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(action, "❓")
    risk_icon = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴", "CRITICAL": "⛔"}.get(
        risk.get("risk_level", ""), "❓"
    )

    summary = f"""## {action_icon} {action} — {symbol} @ {entry}

| | |
|--|--|
| **Timestamp** | `{ts}` |
| **Confidence** | **{conf}%** |
| **Entry** | `{entry}` |
| **Stop Loss** | `{sl}` |
| **Take Profit** | `{tp}` |
| **R/R Ratio** | `{rr}` |
| **Risk Level** | {risk_icon} {risk.get('risk_level', 'N/A')} |
| **Win Rate** | {perf.get('win_rate_pct', 'N/A')}% |
| **Verification** | {ver.get('agreement_level', 'N/A')} ({ver.get('adjusted_action', action)} @ {ver.get('adjusted_confidence_pct', conf)}%) |

> **Reasoning:** {rec.get('reasoning', 'N/A')}

---

💡 *Open a [Copilot agent session](https://github.com/features/copilot) on this issue for interactive deep-dive analysis.*

---

<details>
<summary>📄 Full Analysis Report</summary>

{report_md}

</details>
"""
    return summary


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Create GitHub Issue with trading analysis")
    parser.add_argument("--input", required=True, help="Path to analysis_result.json")
    parser.add_argument("--report", required=True, help="Path to ANALYSIS_REPORT.md")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    owner = os.environ.get("REPO_OWNER")
    repo = os.environ.get("REPO_NAME")

    if not all([token, owner, repo]):
        print("[ERROR] GITHUB_TOKEN, REPO_OWNER, and REPO_NAME must be set")
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        result = json.load(f)

    report_md = ""
    if os.path.exists(args.report):
        with open(args.report, "r", encoding="utf-8") as f:
            report_md = f.read()

    ts = result.get("analysis_timestamp", datetime.now(timezone.utc).isoformat())
    symbol = result.get("symbol", "XAUUSD")
    rec = result.get("final_recommendation", {})
    action = rec.get("action", "HOLD")
    conf = rec.get("confidence_pct", 0)

    title = f"📊 [{symbol}] {action} — {conf}% confidence — {ts[:16].replace('T', ' ')} UTC"

    body = build_issue_body(result, report_md)

    print(f"[INFO] Creating GitHub Issue: {title}")
    issue = create_issue(owner, repo, token, title, body)
    print(f"[INFO] Issue created: {issue['html_url']}")


if __name__ == "__main__":
    main()
