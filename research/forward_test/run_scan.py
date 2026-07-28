"""
Orchestrates the full Scan step end-to-end: a raw IBKR scanner/watchlist paste ->
paste_parser.parse_paste -> sieves.run_sieve_stack -> build_and_log.py's own
compute_builds()/apply_builds().

Closes the gap CLAUDE_CONTEXT.md's Known Issues has flagged since Session 30: this
hand-off was always done by hand -- sieve output read off a screen, then re-typed
into a small CSV for build_and_log.py --input. That manual transcription step is
exactly the kind of error-prone gap this project's own testing/automation culture
exists to close everywhere else in the pipeline (see sieves.py, contracts.py,
technicals.py, build_and_log.py itself). This script does the same job with zero
re-typing: sieve results flow directly into build_and_log's row objects in memory.

Still explicitly NOT automated (and can't be without a live MCP/browser session):
producing the paste itself. Run the Scanner/Radar/watchlist paste interactively
first, save the raw text to a file, then point this script at it.

Usage:
    python3 run_scan.py --paste today_scan.txt            # builds and logs
    python3 run_scan.py --paste today_scan.txt --dry-run   # reports only
"""
from __future__ import annotations

import argparse

import build_and_log as bl
import paste_parser as pp
import sieves as s

# Matches the failed_gate label already used throughout forward_test_log.csv for a
# name that cleared Sieve 1 + every gate but missed only the Sieve 2b IV/HV<100%
# finalist ceiling -- the REJECT arm of the forward test's SURVIVOR/REJECT design.
REJECT_GATE_LABEL = "SIEVE2B_IVHV"


def build_scan_rows(text: str, expected_format: str | None = None):
    """Parses a raw paste and returns the scan_rows list build_and_log.py's
    compute_builds()/apply_builds() expect: one dict per finalist (group=SURVIVOR)
    and one per REJECT-arm candidate (cleared every gate except the IV/HV<100%
    ceiling, group=REJECT). Purged names (failed Sieve 1, Gate A/B/C, or
    UNSCREENABLE) are excluded -- they don't belong to either arm of the forward
    test's design, matching every prior session's manual construction of this list.

    Returns (scan_rows, format, vix, all_results) -- all_results is the full
    PURGE LOG (every screened name, not just the two arms), for reporting.
    """
    fmt, rows, vix = pp.parse_paste(text, expected_format=expected_format)

    # PATH A always independently computes market_cap_usd/dollar_vol_usd from real
    # screener columns -- unlike PATH B, where both are None by deliberate,
    # documented curation-asserted design (sieves.py's own convention, corrected
    # Session 36). sieves.py's Gate A/C logic treats a None the same way regardless
    # of *why* it's None -- it has no way to tell "PATH B, pre-cleared by curation"
    # apart from "PATH A, a genuine parse/data gap for this one row." Silently
    # letting a real PATH A row fall through as if it were curation-asserted would
    # be exactly the class of bug Sieve 1.5 (Gate A) was built to catch in the first
    # place -- a micro-cap (or an untraded name) slipping through unverified. Flagged
    # loud as UNSCREENABLE instead, never silently sieved as if pre-cleared.
    screenable = []
    all_results = []
    for r in rows:
        if fmt == "PATH_A" and (r.market_cap_usd is None or r.dollar_vol_usd is None):
            missing = "market_cap_usd" if r.market_cap_usd is None else "dollar_vol_usd"
            all_results.append(s.SieveResult(
                r.ticker, "UNSCREENABLE", r.ivr_52w, None, None, False,
                f"PATH A row missing {missing} (a paste data gap, not PATH B's curation-asserted "
                f"None) -- cannot independently verify Gate A/C, refusing to silently pass it",
                provisional=False,
            ))
        else:
            screenable.append(s.sieve_input_from_paste_row(r))

    finalists, sieve_results = s.run_sieve_stack(screenable)
    all_results.extend(sieve_results)

    finalist_tickers = {f.ticker for f in finalists}
    scan_rows = []
    for r in all_results:
        if r.ticker in finalist_tickers:
            scan_rows.append({
                "ticker": r.ticker, "group": "SURVIVOR", "failed_gate": "NONE",
                "failed_value": "NONE", "ivr": f"{r.ivr_52w:.1f}",
                "iv_hv_pct": f"{r.iv_hv_pct:.1f}", "dollar_vol_ok": "Y",
            })
        elif r.outcome == "SURVIVOR" and r.iv_hv_pct is not None and r.iv_hv_pct >= s.IVHV_FINALIST_MAX:
            scan_rows.append({
                "ticker": r.ticker, "group": "REJECT", "failed_gate": REJECT_GATE_LABEL,
                "failed_value": f"{r.iv_hv_pct:.1f}", "ivr": f"{r.ivr_52w:.1f}",
                "iv_hv_pct": f"{r.iv_hv_pct:.1f}", "dollar_vol_ok": "Y",
            })
    return scan_rows, fmt, vix, all_results


def format_built_summary(r: dict) -> str:
    """A BUILT result carries no 'note' field at all (build_position() never sets
    one on that branch) -- printing it bare was the exact gap that forced a
    separate ad hoc inspection script before trusting CAG's build earlier this
    session. This gives every BUILT position the same at-a-glance detail that
    inspection script printed by hand, permanently, for every future run."""
    di = r["direction_info"]
    er = r["earnings"]
    opt_type = "Call" if r["direction"] == "BULLISH" else "Put"
    scored_n_direction = r["bull_n"] if r["direction"] == "BULLISH" else r["bear_n"]
    eg = r.get("entry_greeks") or {}
    greeks_bits = ", ".join(
        f"{k}={v}" for k, v in (("delta", eg.get("delta")), ("iv", eg.get("mid_iv"))) if v is not None
    ) or "n/a"
    return (
        f"{r['direction']} {scored_n_direction}/{r['scored_n']} scored, trend={di['trend_200d'] or 'INSUFFICIENT_HISTORY'} | "
        f"{r['strike']} {opt_type} {r['expiry']} ({r['dte']}DTE{'*overshoot' if r['is_overshoot'] else ''}) "
        f"mid ${r['mid']} (b{r['bid']}/a{r['ask']}) tgt ${r['target']}/stop ${r['stop']} | "
        f"greeks: {greeks_bits} | earnings {er.status} ({er.next_date or 'unknown'})"
        + (f" | {r['migration_note']}" if r.get("migration_note") else "")
    )


def print_purge_log(all_results, finalist_tickers, reject_tickers):
    """Two genuinely different buckets, printed separately -- lumping them together
    previously mislabeled clean SURVIVOR names (cleared every gate, just outside the
    top-3 FINALIST_COUNT and under the IV/HV<100% ceiling, so not REJECT-arm eligible
    either) as if they'd been purged, when nothing eliminated them at all."""
    also_survived = [r for r in all_results if r.outcome in ("SURVIVOR", "FINALIST")
                     and r.ticker not in finalist_tickers and r.ticker not in reject_tickers]
    purged = [r for r in all_results if r.outcome not in ("SURVIVOR", "FINALIST")]

    if also_survived:
        print(f"--- ALSO CLEARED EVERY GATE, not selected (outside top {s.FINALIST_COUNT} / "
              f"under the {s.IVHV_FINALIST_MAX}% REJECT-arm floor) ---")
        for r in sorted(also_survived, key=lambda r: r.iv_hv_pct):
            print(f"  {r.ticker:8} IVR {r.ivr_52w:.1f}%, IV/HV {r.iv_hv_pct:.1f}%")
        print()

    print("--- PURGED (Sieve 1 / Gate A/B/C / UNSCREENABLE) ---")
    for r in purged:
        print(f"  {r.ticker:8} {r.outcome:14} {r.reason}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--paste", required=True, help="Path to a raw IBKR scanner/watchlist paste (text)")
    parser.add_argument("--format", choices=["PATH_A", "PATH_B"], default=None,
                         help="Assert the expected paste format; raises on mismatch instead of silently parsing under the wrong rules")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with open(args.paste) as f:
        text = f.read()

    scan_rows, fmt, vix, all_results = build_scan_rows(text, expected_format=args.format)
    finalist_tickers = {r["ticker"] for r in scan_rows if r["group"] == "SURVIVOR"}
    reject_tickers = {r["ticker"] for r in scan_rows if r["group"] == "REJECT"}

    print(f"Format: {fmt} | {len(all_results)} screened | {len(finalist_tickers)} finalists | {len(reject_tickers)} REJECT-arm candidates")
    if vix:
        print(f"VIX (from paste): {vix.level} -> {vix.regime}")
    print()
    print_purge_log(all_results, finalist_tickers, reject_tickers)
    print()

    if not scan_rows:
        print("No SURVIVOR or REJECT-arm candidates this run -- nothing to build.")
        return

    results = bl.compute_builds(scan_rows)
    print()
    for result in results:
        detail = format_built_summary(result) if result["outcome"] == "BUILT" else result.get("note", "")
        print(f"{result['ticker']:8} {result['group']:9} {result['outcome']:18} {detail}")

    built = [r for r in results if r["outcome"] == "BUILT"]
    if args.dry_run:
        print(f"\nDRY RUN -- {len(built)} position(s) would be logged. Nothing written.")
        return

    bl.apply_builds(results)
    mixed = sum(1 for r in results if r["outcome"] == "BUILDER_MIXED")
    print(f"\n{len(built)} position(s) logged to Gemini's journal, {mixed} recorded as BUILDER_MIXED, CSV updated.")


if __name__ == "__main__":
    main()
