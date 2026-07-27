"""
Forward test position builder — automates the Build+Log half of the pipeline
(everything downstream of the Scan step). Mirrors resolve_positions.py's shape:
Tradier-only, deterministic, one command.

Explicitly NOT automated (and can't be without a live MCP session): Sieve 1 IVR
screening. That needs IBKR MCP's implied_volatility_percentile / historical_vol
fields, which have no Tradier equivalent. Run the Scanner interactively first,
then feed its finalist/reject list to this script via --input.

The TBLA earnings gate (earnings.py, wired in Session 35) runs per candidate right
after direction is resolved and before any option-chain call: earnings < 14 days out
is a hard skip (EARNINGS_HARD_SKIP, no position built, no Tradier chain call wasted on
a name about to be rejected anyway); 14-35 days out (WITHIN_HOLD) and UNKNOWN (both
earnings.py sources failed) both flag-and-proceed rather than block, matching the
project's existing "flag, don't silently block on an uncertain signal" convention for
VIX regime -- earnings.py itself never fabricates a date, so UNKNOWN reflects a real
data gap, not a disagreement worth stopping on.

Direction inference here uses only what Tradier can supply: SMA200 trend, YTD
change, EMA9/21/50 stack, 52w range position, and today's P/C ratio (summed
from the chosen expiry's chain volume). This is a REDUCED signal set vs the
full skill-options-directional-builder.md (that also scores avg 90-day P/C
ratio, which has no reliable Tradier-only historical source — dropped rather
than faked). Still uses the same strict-majority-of-scored-signals rule.

Input CSV columns (one row per Scan finalist/near-miss reject):
    ticker,group,failed_gate,failed_value,ivr,iv_hv_pct,dollar_vol_ok,vix_regime

vix_regime is optional (defaults to UNKNOWN if the column is absent or blank) — pass
through the STANDARD/HIGH-FEAR reading the Scanner's own Phase 0 VIX pull already
produced, so it persists into forward_test_log.csv for the regime-confound check in
FORWARD_TEST_PROTOCOL.md's Interpretation Guardrails (added Session 30).

Usage:
    python3 build_and_log.py --input today_scan.csv            # builds and logs
    python3 build_and_log.py --input today_scan.csv --dry-run  # reports only
"""
import argparse
import csv
import os
import statistics
import sys
from datetime import datetime, timedelta, timezone

import requests

import earnings

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEMINI_REPO = os.environ.get(
    "OPTIONS_IQ_GEMINI_PATH", os.path.join(os.path.dirname(REPO_ROOT), "options_iq_gemini")
)
GEMINI_BASE_URL = "http://localhost:5002"
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "forward_test_log.csv")
TRADIER_BASE_URL = "https://api.tradier.com/v1"

# Session 27 (Jul 16, 2026): briefly changed target to 1.80 (+80%), then reverted to the
# original 1.60 (+60%) same session per Bala's call — faster regime turnover argues for
# locking in gains sooner rather than letting winners run further. See FORWARD_TEST_PROTOCOL.md.
STOP_MULTIPLIER = 0.70
TARGET_MULTIPLIER = 1.60

DTE_MIN = 21
DTE_MAX = 35

VIX_HIGH_FEAR_THRESHOLD = 25.0  # matches paste_parser.py / skill-options-scanner.md Phase 0,
# unchanged since Session 13 -- VIX <= 25 -> STANDARD, > 25 -> HIGH-FEAR


def load_tradier_token():
    env_path = os.path.join(GEMINI_REPO, ".env")
    if not os.path.exists(env_path):
        raise FileNotFoundError(f"Tradier token source not found: {env_path}")
    with open(env_path) as f:
        for line in f:
            if line.startswith("TRADIER_ACCESS_TOKEN="):
                return line.strip().split("=", 1)[1]
    raise ValueError(f"TRADIER_ACCESS_TOKEN not found in {env_path}")


def tradier_get(path, token, params):
    resp = requests.get(
        f"{TRADIER_BASE_URL}{path}", params=params,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}, timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def ema(vals, period):
    k = 2 / (period + 1)
    e = [vals[0]]
    for v in vals[1:]:
        e.append(v * k + e[-1] * (1 - k))
    return e


def format_entry_greeks(eg: dict) -> str:
    """Formats the `entry_greeks` dict (delta/gamma/theta/vega/mid_iv, any of which may be
    None -- Tradier can return greeks=null even when requested, on thin/no-model contracts)
    into a CSV-notes-ready sentence. Never fabricates a value: a missing Greek prints 'N/A',
    not a 0.0 that would read as a real reading."""
    if not any(v is not None for v in eg.values()):
        return " Entry Greeks: unavailable (Tradier returned no model data for this contract)."
    delta = eg.get("delta")
    gamma = eg.get("gamma")
    theta = eg.get("theta")
    vega = eg.get("vega")
    mid_iv = eg.get("mid_iv")
    iv_str = f"{mid_iv * 100:.1f}%" if mid_iv is not None else "N/A"
    return (
        f" Entry Greeks (Tradier, at build time): "
        f"delta {delta if delta is not None else 'N/A'}, "
        f"gamma {gamma if gamma is not None else 'N/A'}, "
        f"theta {theta if theta is not None else 'N/A'}, "
        f"vega {vega if vega is not None else 'N/A'}, "
        f"mid IV {iv_str}."
    )


def fetch_vix_regime(token):
    """Fetches VIX directly via Tradier ('/markets/quotes?symbols=VIX' -- confirmed
    live Jul 27 2026, plain 'VIX' works, '$VIX.X'/'VIX.X' both return unmatched_symbols)
    and classifies STANDARD/HIGH-FEAR. This makes the regime read independent of
    whatever the day's Scan paste does or doesn't carry -- PATH B pastes have always
    included a VIX row (paste_parser.py), but whether PATH A's dynamic screener paste
    ever can was an open question (CLAUDE_CONTEXT.md Known Issues); fetching it here
    directly makes that question moot for this script's own runs. Returns (None,
    "UNKNOWN") on any failure -- never a fabricated regime, same convention as every
    other "can't determine this" case in this pipeline."""
    try:
        data = tradier_get("/markets/quotes", token, {"symbols": "VIX", "greeks": "false"})
        quote = data.get("quotes", {}).get("quote")
        if not quote or "last" not in quote or quote["last"] is None:
            return None, "UNKNOWN"
        level = quote["last"]
        regime = "STANDARD" if level <= VIX_HIGH_FEAR_THRESHOLD else "HIGH-FEAR"
        return level, regime
    except Exception:
        return None, "UNKNOWN"


def fetch_daily_history(ticker, token, today):
    start = (today - timedelta(days=400)).isoformat()
    data = tradier_get("/markets/history", token,
                        {"symbol": ticker, "interval": "daily", "start": start, "end": today.isoformat()})
    days = data.get("history", {}).get("day", [])
    if isinstance(days, dict):
        days = [days]
    if not days:
        raise ValueError(f"No Tradier history for {ticker}")
    return days


def compute_direction(ticker, token, today):
    days = fetch_daily_history(ticker, token, today)
    close = [d["close"] for d in days]
    high = [d["high"] for d in days]
    low = [d["low"] for d in days]
    price = close[-1]

    signals = {}  # name -> "bullish" / "bearish" / None (unscored)

    if len(close) >= 200:
        sma200 = statistics.mean(close[-200:])
        signals["SMA200"] = "bullish" if price > sma200 else "bearish"
        price_vs_sma200_pct = (price - sma200) / sma200 * 100
    else:
        price_vs_sma200_pct = None  # not enough history; row drops out, not scored

    year = today.year
    prior_year_closes = [d["close"] for d in days if d["date"] < f"{year}-01-01"]
    baseline = prior_year_closes[-1] if prior_year_closes else close[0]
    ytd_change_pct = (price - baseline) / baseline * 100
    signals["YTD"] = "bullish" if ytd_change_pct > 0 else "bearish"

    high_52w = max(high[-252:]) if high else price
    low_52w = min(low[-252:]) if low else price
    # None (not a fabricated 50.0) when the range is flat -- matches technicals.py's
    # range_52w_pct(), which returns None for the identical edge case. The old 50.0
    # fallback was a real, if practically rare, "return null not a plausible fake"
    # violation (Session 34 three-pass review) -- a genuinely flat 252-day high==low
    # is near-impossible for a real liquid name, but a fabricated neutral reading is
    # still wrong on principle, and cheap to fix once noticed.
    range_52w_pct = (price - low_52w) / (high_52w - low_52w) * 100 if high_52w != low_52w else None
    if range_52w_pct is None:
        signals["RANGE_52W"] = None
    elif range_52w_pct > 60:
        signals["RANGE_52W"] = "bullish"
    elif range_52w_pct < 40:
        signals["RANGE_52W"] = "bearish"
    else:
        signals["RANGE_52W"] = None

    ema9, ema21, ema50 = ema(close, 9)[-1], ema(close, 21)[-1], ema(close, 50)[-1]
    if ema9 > ema21 > ema50:
        signals["EMA_STACK"] = "bullish"
    elif ema9 < ema21 < ema50:
        signals["EMA_STACK"] = "bearish"
    else:
        signals["EMA_STACK"] = None

    trend_200d = None
    if signals.get("SMA200") == "bullish":
        trend_200d = "UPTREND"
    elif signals.get("SMA200") == "bearish":
        trend_200d = "DOWNTREND"

    return {
        "price": price, "signals": signals,
        "price_vs_sma200_pct": price_vs_sma200_pct, "ytd_change_pct": round(ytd_change_pct, 2),
        "range_52w_pct": round(range_52w_pct, 1) if range_52w_pct is not None else None,
        "trend_200d": trend_200d,
    }


def add_today_pc_ratio(direction_info, ticker, token, expiry):
    chain = tradier_get("/markets/options/chains", token,
                         {"symbol": ticker, "expiration": expiry, "greeks": "false"})
    options = chain.get("options", {}).get("option", [])
    if isinstance(options, dict):
        options = [options]
    call_vol = sum(o.get("volume") or 0 for o in options if o.get("option_type") == "call")
    put_vol = sum(o.get("volume") or 0 for o in options if o.get("option_type") == "put")
    if call_vol == 0:
        direction_info["signals"]["TODAY_PC"] = None
        direction_info["today_pc_ratio"] = None
        return
    ratio = put_vol / call_vol
    direction_info["today_pc_ratio"] = round(ratio, 3)
    if ratio < 0.7:
        direction_info["signals"]["TODAY_PC"] = "bullish"
    elif ratio > 1.2:
        direction_info["signals"]["TODAY_PC"] = "bearish"
    else:
        direction_info["signals"]["TODAY_PC"] = None


def score_direction(signals):
    # Session 34 three-pass review: the old filter (`v is not None or k in signals`) is
    # tautologically true for every key already in `signals` -- it filtered nothing, and
    # total_scored = len(signals) then counted unscored (None-valued) signals like a
    # neutral RANGE_52W or TODAY_PC as if they'd been evaluated. Confirmed with a live
    # repro: a clean, unanimous 2-0 bullish vote (3 other signals genuinely unscored)
    # was reported as MIXED purely because the denominator was inflated to 5. This is
    # the exact "denominator counts unscored signals" bug technicals.py's own
    # score_direction was already built correctly to avoid -- this function just never
    # got updated to match when that fix landed.
    scored = {k: v for k, v in signals.items() if v is not None}
    total_scored = len(scored)
    bullish = sum(1 for v in scored.values() if v == "bullish")
    bearish = sum(1 for v in scored.values() if v == "bearish")
    if total_scored == 0:
        return "MIXED", 0, 0, 0
    if bullish > bearish and bullish > total_scored / 2:
        return "BULLISH", bullish, bearish, total_scored
    if bearish > bullish and bearish > total_scored / 2:
        return "BEARISH", bullish, bearish, total_scored
    return "MIXED", bullish, bearish, total_scored


def pick_expiry(expirations, today):
    in_window = []
    outside_window = []
    for e in expirations:
        edate = datetime.strptime(e, "%Y-%m-%d").date()
        dte = (edate - today).days
        if DTE_MIN <= dte <= DTE_MAX:
            in_window.append((dte, e))
        else:
            dist = max(DTE_MIN - dte, dte - DTE_MAX)
            outside_window.append((dist, dte, e))
    if in_window:
        in_window.sort()
        return in_window[0][1], in_window[0][0], False
    outside_window.sort()
    return outside_window[0][2], outside_window[0][1], True


def pick_atm_contract(chain_options, price, option_type):
    candidates = [o for o in chain_options if o.get("option_type") == option_type]
    if not candidates:
        return None
    return min(candidates, key=lambda o: abs(o["strike"] - price))


def build_position(row, token, today, existing_open):
    ticker = row["ticker"]
    group = row["group"]

    existing_same_group = [t for t in existing_open if t["ticker"] == ticker and t["group"] == group]
    if existing_same_group:
        return {"ticker": ticker, "group": group, "outcome": "SKIPPED_DUPLICATE",
                "note": f"already OPEN in {group} (id {existing_same_group[0]['id']})"}

    existing_other_group = [t for t in existing_open if t["ticker"] == ticker and t["group"] != group]
    migrated = bool(existing_other_group)
    migration_note = (f"CROSS_GROUP_MIGRATION_FROM_{existing_other_group[0]['group']}_ID{existing_other_group[0]['id']}"
                       if migrated else None)

    direction_info = compute_direction(ticker, token, today)
    expirations = tradier_get("/markets/options/expirations", token, {"symbol": ticker}).get("expirations", {}).get("date", [])
    expiry, dte, is_overshoot = pick_expiry(expirations, today)
    add_today_pc_ratio(direction_info, ticker, token, expiry)

    direction, bull_n, bear_n, scored_n = score_direction(direction_info["signals"])
    if direction == "MIXED":
        return {"ticker": ticker, "group": group, "outcome": "BUILDER_MIXED",
                "note": f"{bull_n} bullish/{bear_n} bearish/{scored_n} scored - no strict majority",
                "row": row, "direction_info": direction_info}

    earnings_result = earnings.get_earnings_status(ticker)
    if earnings_result.status == "HARD_SKIP":
        return {"ticker": ticker, "group": group, "outcome": "EARNINGS_HARD_SKIP",
                "note": f"earnings {earnings_result.next_date} ({earnings_result.days_out}d out, "
                        f"source={earnings_result.source}) inside {earnings.HARD_SKIP_DAYS}d hard-skip window"
                        + (f" -- {earnings_result.note}" if earnings_result.note else ""),
                "row": row, "direction_info": direction_info}

    option_type = "call" if direction == "BULLISH" else "put"
    # greeks=true (flipped Session 36, Jul 27 2026): Tradier returns Delta/Gamma/Theta/Vega
    # and bid/mid/ask IV in this exact same response at no extra API-call cost -- previously
    # requested as "false" and the values simply discarded. Captures real entry-time Greeks/IV
    # for the forward-test record instead of leaving them uncomputed everywhere in this hub's
    # own code (see the field-availability research, Session 36 -- these were flagged as
    # "not implemented anywhere" and this closes that specific, cheap gap).
    chain = tradier_get("/markets/options/chains", token, {"symbol": ticker, "expiration": expiry, "greeks": "true"})
    options = chain.get("options", {}).get("option", [])
    if isinstance(options, dict):
        options = [options]
    contract = pick_atm_contract(options, direction_info["price"], option_type)
    if contract is None:
        return {"ticker": ticker, "group": group, "outcome": "NO_CONTRACT",
                "note": f"no {option_type} contracts at expiry {expiry}"}

    bid, ask = contract.get("bid"), contract.get("ask")
    if not bid or not ask or bid <= 0 or ask <= 0:
        return {"ticker": ticker, "group": group, "outcome": "NO_QUOTE",
                "note": f"{contract['symbol']} bid={bid} ask={ask}"}

    mid = round((bid + ask) / 2, 4)
    target = round(mid * TARGET_MULTIPLIER, 4)
    stop = round(mid * STOP_MULTIPLIER, 4)

    # Tradier can return greeks=null even when requested (observed on thin/no-model
    # contracts) -- `or {}` so a missing model never crashes the build, and every
    # individual value stays None (never a fabricated 0.0) rather than silently
    # defaulting to something that reads as a real Greek.
    greeks = contract.get("greeks") or {}
    entry_greeks = {
        "delta": greeks.get("delta"), "gamma": greeks.get("gamma"),
        "theta": greeks.get("theta"), "vega": greeks.get("vega"),
        "mid_iv": greeks.get("mid_iv"),
    }

    return {
        "ticker": ticker, "group": group, "outcome": "BUILT", "row": row,
        "direction": direction, "direction_info": direction_info,
        "bull_n": bull_n, "bear_n": bear_n, "scored_n": scored_n,
        "occ_symbol": contract["symbol"], "strike": contract["strike"], "expiry": expiry, "dte": dte,
        "is_overshoot": is_overshoot, "bid": bid, "ask": ask, "mid": mid, "target": target, "stop": stop,
        "migrated": migrated, "migration_note": migration_note, "earnings": earnings_result,
        "entry_greeks": entry_greeks,
    }


def log_to_journal(built, today, dry_run):
    if dry_run:
        return
    contract_details = (
        f"{built['ticker']} {datetime.strptime(built['expiry'], '%Y-%m-%d').strftime('%b %d %Y')} "
        f"{built['strike']} {built['direction'] == 'BULLISH' and 'Call' or 'Put'} | resolved via Tradier | "
        f"mid ${built['mid']} (bid {built['bid']} / ask {built['ask']}) at {today.isoformat()} | source: build_and_log.py"
    )
    failed_gate = built["row"].get("failed_gate", "NONE")
    vix_regime = built["row"].get("vix_regime") or "UNKNOWN"
    er = built["earnings"]
    setup_context = (
        f"FWD_TEST:{built['group']}|failed_gate={failed_gate},ivr={built['row'].get('ivr','')},"
        f"iv_hv_pct={built['row'].get('iv_hv_pct','')},vix_regime={vix_regime},"
        f"trend_200d={built['direction_info']['trend_200d'] or 'INSUFFICIENT_HISTORY'},"
        f"earnings_status={er.status},earnings_date={er.next_date or 'UNKNOWN'},"
        f"rr_ratio={TARGET_MULTIPLIER:.2f},migrated={'YES' if built['migrated'] else 'NO'}"
        + (f",note={built['migration_note']}" if built["migration_note"] else "")
    )
    resp = requests.post(f"{GEMINI_BASE_URL}/journal/log", json={
        "ticker": built["ticker"], "occ_symbol": built["occ_symbol"], "contract_details": contract_details,
        "entry_price": built["mid"], "target_price": built["target"], "stop_loss": built["stop"],
        "setup_context": setup_context,
    }, timeout=10)
    resp.raise_for_status()
    body = resp.json()
    if body.get("status") != "success":
        raise RuntimeError(f"journal/log for {built['ticker']} did not report success: {body}")


def append_csv_rows(results, today_str, dry_run):
    if dry_run:
        return
    rows_to_write = []
    for r in results:
        if r["outcome"] == "BUILT":
            b = r
            di = b["direction_info"]
            er = b["earnings"]
            greeks_str = format_entry_greeks(b.get("entry_greeks") or {})
            notes = (
                f"Built via build_and_log.py. Direction={b['direction']}"
                f" {b['bull_n'] if b['direction'] == 'BULLISH' else b['bear_n']}/{b['scored_n']} scored"
                f" (YTD {di['ytd_change_pct']}%, 52w range {di['range_52w_pct']}%, today P/C {di.get('today_pc_ratio') if di.get('today_pc_ratio') is not None else 'N/A (no chain volume yet)'})."
                f" Contract: {b['strike']} {'Call' if b['direction']=='BULLISH' else 'Put'}, {b['expiry']}"
                f" ({b['dte']} DTE{', overshoot - no expiry fell inside 21-35 DTE' if b['is_overshoot'] else ''})."
                f" Entry mid ${b['mid']} (bid {b['bid']}/ask {b['ask']})."
                f"{greeks_str}"
                f" Earnings: {er.status} ({er.next_date or 'unknown date'}, source={er.source}"
                + (f", {er.days_out}d out" if er.days_out is not None else "") + ")."
                + (f" {er.note}" if er.note else "")
                + (f" {b['migration_note']}." if b["migration_note"] else "")
            )
            rows_to_write.append([
                today_str, b["group"], b["ticker"], b["row"].get("failed_gate", "NONE"),
                b["row"].get("failed_value", "NONE"), b["row"].get("ivr", ""), b["row"].get("iv_hv_pct", ""),
                b["row"].get("dollar_vol_ok", "Y"), b["row"].get("vix_regime") or "UNKNOWN", "NOT_COMPUTED",
                "NA_NOT_COMPUTED", di["trend_200d"] or "INSUFFICIENT_HISTORY",
                b["dte"], b["strike"], b["mid"], di["price"], b["target"], b["stop"], f"{TARGET_MULTIPLIER:.2f}",
                "", "OPEN", "", "", notes,
            ])
        elif r["outcome"] == "BUILDER_MIXED":
            row = r["row"]
            rows_to_write.append([
                today_str, r["group"], r["ticker"], row.get("failed_gate", "NONE"), row.get("failed_value", "NONE"),
                row.get("ivr", ""), row.get("iv_hv_pct", ""), row.get("dollar_vol_ok", "Y"),
                row.get("vix_regime") or "UNKNOWN", "NOT_COMPUTED",
                "NA_NOT_COMPUTED", "", "", "", "", "", "", "", f"{TARGET_MULTIPLIER:.2f}", "", "BUILDER_MIXED", "", "",
                f"Directional Builder result: {r['note']}. Not logged to Gemini's journal per protocol.",
            ])
        elif r["outcome"] == "EARNINGS_HARD_SKIP":
            row = r["row"]
            rows_to_write.append([
                today_str, r["group"], r["ticker"], row.get("failed_gate", "NONE"), row.get("failed_value", "NONE"),
                row.get("ivr", ""), row.get("iv_hv_pct", ""), row.get("dollar_vol_ok", "Y"),
                row.get("vix_regime") or "UNKNOWN", "NOT_COMPUTED",
                "NA_NOT_COMPUTED", "", "", "", "", "", "", "", f"{TARGET_MULTIPLIER:.2f}", "", "EARNINGS_HARD_SKIP", "", "",
                f"TBLA earnings gate: {r['note']}. Not logged to Gemini's journal per protocol.",
            ])
    if not rows_to_write:
        return
    with open(CSV_PATH, "a", newline="") as f:
        csv.writer(f).writerows(rows_to_write)


def fetch_existing_open():
    history = requests.get(f"{GEMINI_BASE_URL}/journal/history", timeout=10).json()
    existing_open = []
    for t in history:
        sc = t.get("setup_context") or ""
        if t.get("status") == "OPEN" and sc.startswith("FWD_TEST:"):
            group = sc.split("|")[0].split(":")[1]
            existing_open.append({"ticker": t["ticker"], "group": group, "id": t["id"]})
    return existing_open


def compute_builds(scan_rows, today=None):
    """No side effects — resolves direction/contract/quotes for a preview. Safe to call repeatedly."""
    today = today or datetime.now(timezone.utc).date()
    token = load_tradier_token()
    existing_open = fetch_existing_open()

    vix_level, vix_regime = fetch_vix_regime(token)
    print(f"VIX (live, Tradier): {vix_level if vix_level is not None else 'unavailable'} -> {vix_regime}")

    results = []
    for row in scan_rows:
        # Always prefer the live fetch over whatever (if anything) the input CSV's own
        # vix_regime column carries -- the paste this column was sourced from may not
        # have had a VIX row at all (confirmed unverified for PATH A dynamic-screener
        # pastes), and even when it did, a live Tradier pull at build time is more
        # current than a value read off the Scan-time paste. Only falls back to the
        # row's own value if the live fetch itself failed (vix_regime stays "UNKNOWN").
        if vix_regime != "UNKNOWN":
            row["vix_regime"] = vix_regime
        result = build_position(row, token, today, existing_open)
        results.append(result)
    return results


def apply_builds(results, today=None):
    """Performs the actual writes: journal POST for each BUILT position, then the CSV rows."""
    today = today or datetime.now(timezone.utc).date()
    built = [r for r in results if r["outcome"] == "BUILT"]
    for b in built:
        log_to_journal(b, today, dry_run=False)
    append_csv_rows(results, today.isoformat(), dry_run=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="CSV of Scan output: ticker,group,failed_gate,failed_value,ivr,iv_hv_pct,dollar_vol_ok")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    today = datetime.now(timezone.utc).date()

    with open(args.input, newline="") as f:
        scan_rows = list(csv.DictReader(f))

    results = compute_builds(scan_rows, today)
    for result in results:
        print(f"{result['ticker']:8} {result['group']:9} {result['outcome']:18} {result.get('note','')}")

    built = [r for r in results if r["outcome"] == "BUILT"]
    if args.dry_run:
        print(f"\nDRY RUN — {len(built)} position(s) would be logged. Nothing written.")
        return

    apply_builds(results, today)
    mixed = sum(1 for r in results if r["outcome"] == "BUILDER_MIXED")
    print(f"\n{len(built)} position(s) logged to Gemini's journal, {mixed} recorded as BUILDER_MIXED, CSV updated.")


if __name__ == "__main__":
    main()
