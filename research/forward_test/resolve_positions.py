"""
Forward test close-of-day resolution — the only path allowed to close FWD_TEST: positions.

Built Session 27 (Jul 16, 2026) after two positions (AFRM, AVAV) got closed the same day via
Gemini's dashboard Close button, using intraday `last` price instead of the protocol's mandated
close-of-day bid/ask mid. See FORWARD_TEST_PROTOCOL.md's "Resolution lockdown" note and
HANDOFF_gemini_fwd_test_close_lockdown.md.

Usage:
    python3 resolve_positions.py            # resolves and writes changes
    python3 resolve_positions.py --dry-run  # reports what would happen, writes nothing
"""
import csv
import os
import re
import sys
from datetime import datetime, timezone

import requests

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEMINI_REPO = os.environ.get(
    "OPTIONS_IQ_GEMINI_PATH", os.path.join(os.path.dirname(REPO_ROOT), "options_iq_gemini")
)
GEMINI_BASE_URL = "http://localhost:5002"
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "forward_test_log.csv")

OCC_SYMBOL_RE = re.compile(r"^[A-Z]+(\d{6})[CP]\d{8}$")


def load_tradier_token():
    env_path = os.path.join(GEMINI_REPO, ".env")
    if not os.path.exists(env_path):
        raise FileNotFoundError(f"Tradier token source not found: {env_path}")
    with open(env_path) as f:
        for line in f:
            if line.startswith("TRADIER_ACCESS_TOKEN="):
                return line.strip().split("=", 1)[1]
    raise ValueError(f"TRADIER_ACCESS_TOKEN not found in {env_path}")


def occ_expiry_date(occ_symbol):
    m = OCC_SYMBOL_RE.match(occ_symbol)
    if not m:
        raise ValueError(f"Cannot parse expiry from occ_symbol: {occ_symbol}")
    yymmdd = m.group(1)
    return datetime.strptime("20" + yymmdd, "%Y%m%d").date()


def fetch_open_fwd_test_positions():
    resp = requests.get(f"{GEMINI_BASE_URL}/journal/history", timeout=10)
    resp.raise_for_status()
    trades = resp.json()
    return [
        t for t in trades
        if t.get("status") == "OPEN" and (t.get("setup_context") or "").startswith("FWD_TEST:")
    ]


def fetch_live_mids(occ_symbols, tradier_token):
    if not occ_symbols:
        return {}
    resp = requests.get(
        "https://api.tradier.com/v1/markets/quotes",
        params={"symbols": ",".join(occ_symbols)},
        headers={"Authorization": f"Bearer {tradier_token}", "Accept": "application/json"},
        timeout=10,
    )
    resp.raise_for_status()
    quotes = resp.json().get("quotes", {}).get("quote", [])
    if isinstance(quotes, dict):
        quotes = [quotes]
    mids = {}
    for q in quotes:
        bid, ask = q.get("bid"), q.get("ask")
        if bid and ask and bid > 0 and ask > 0:
            mids[q["symbol"]] = round((bid + ask) / 2, 4)
    return mids


def decide_resolution(trade, mid, today):
    entry_date = datetime.strptime(trade["timestamp"], "%Y-%m-%d %H:%M:%S").date()
    expiry_date = occ_expiry_date(trade["occ_symbol"])
    dte_at_entry = (expiry_date - entry_date).days
    days_held = (today - entry_date).days
    time_stop_days = dte_at_entry * 0.60

    stop_loss = trade["stop_loss"]
    target_price = trade["target_price"]

    if mid <= stop_loss:
        return "STOP"
    if mid >= target_price:
        return "TARGET"
    if days_held >= time_stop_days:
        return "TIME"
    return None


def resolve_trade(trade_id, mid, dry_run):
    if dry_run:
        return
    resp = requests.patch(
        f"{GEMINI_BASE_URL}/journal/resolve/{trade_id}",
        json={"status": "CLOSED", "exit_price": mid},
        timeout=10,
    )
    resp.raise_for_status()
    body = resp.json()
    if body.get("status") != "success":
        raise RuntimeError(f"journal/resolve/{trade_id} did not report success: {body}")


def update_csv(resolutions, today_str, dry_run):
    if dry_run or not resolutions:
        return
    with open(CSV_PATH, newline="") as f:
        rows = list(csv.reader(f))
    header = rows[0]
    idx = {name: i for i, name in enumerate(header)}

    by_occ = {r["occ_symbol"]: r for r in resolutions}
    matched_occ = set()
    for row in rows[1:]:
        if row[idx["resolve_date"]]:
            continue
        for occ, r in by_occ.items():
            if row[idx["ticker"]] == r["ticker"] and row[idx["entry_date"]] <= today_str:
                strike_in_row = row[idx["strike"]]
                strike_in_occ = float(occ[-8:]) / 1000 if occ[-8:].isdigit() else None
                if strike_in_row and strike_in_occ is not None and float(strike_in_row) == strike_in_occ:
                    row[idx["resolve_date"]] = today_str
                    row[idx["resolution"]] = r["resolution"]
                    row[idx["exit_premium_mid"]] = str(r["mid"])
                    row[idx["ret_pct"]] = str(r["ret_pct"])
                    matched_occ.add(occ)
                    break

    unmatched = set(by_occ) - matched_occ
    if unmatched:
        print(f"WARNING: could not match these resolved trades to a CSV row (fix manually): {unmatched}")

    with open(CSV_PATH, "w", newline="") as f:
        csv.writer(f).writerows(rows)


def main():
    dry_run = "--dry-run" in sys.argv
    today = datetime.now(timezone.utc).date()
    today_str = today.isoformat()

    tradier_token = load_tradier_token()
    positions = fetch_open_fwd_test_positions()
    if not positions:
        print("No open FWD_TEST positions.")
        return

    mids = fetch_live_mids([p["occ_symbol"] for p in positions], tradier_token)

    resolutions = []
    print(f"{'TICKER':8} {'ID':4} {'MID':>8} {'STOP':>8} {'TARGET':>8}  RESOLUTION")
    for p in positions:
        occ = p["occ_symbol"]
        mid = mids.get(occ)
        if mid is None:
            print(f"{p['ticker']:8} {p['id']:<4} {'NO_QUOTE':>8}")
            continue

        outcome = decide_resolution(p, mid, today)
        stop_disp = f"{p['stop_loss']:.3f}"
        target_disp = f"{p['target_price']:.3f}"
        print(f"{p['ticker']:8} {p['id']:<4} {mid:8.3f} {stop_disp:>8} {target_disp:>8}  {outcome or 'open'}")

        if outcome:
            ret_pct = round((mid - p["entry_price"]) / p["entry_price"] * 100, 2)
            resolutions.append({
                "id": p["id"], "ticker": p["ticker"], "occ_symbol": occ,
                "mid": mid, "resolution": outcome, "ret_pct": ret_pct,
            })

    for r in resolutions:
        resolve_trade(r["id"], r["mid"], dry_run)

    update_csv(resolutions, today_str, dry_run)

    if dry_run:
        print(f"\nDRY RUN — {len(resolutions)} position(s) would resolve. Nothing written.")
    else:
        print(f"\n{len(resolutions)} position(s) resolved and logged.")


if __name__ == "__main__":
    main()
