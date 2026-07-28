"""
Regenerates the "What Real Money Would Look Like" artifact from the live
forward_test_log.csv -- a 1-contract-per-trade dollar simulation (Session 37,
Jul 28 2026, at Bala's request after seeing the forward test's % returns and
wanting to see them as real money).

Built as a real script, not a one-off scratchpad computation, per the same
Session 37 discipline that produced run_scan.py: Bala flagged hand-rolled
scratchpad Python as error-prone, and this artifact's first version had a real
CSS bug (variables scoped to .viz-root but referenced on body, its ancestor --
custom properties never cascade upward) that only surfaced by actually
rendering the page. Regenerating from a committed template + this script means
that fix, once made, stays fixed on every future run.

Only real, already-recorded numbers go in: entry/exit premiums straight from
forward_test_log.csv, x100 for the standard option contract multiplier. Rows
with no entry_premium_mid (BUILDER_MIXED / EARNINGS_HARD_SKIP) never had a
contract built and are excluded -- no money was ever on the table for those.
Open positions show capital deployed only, never a guessed unrealized P&L.

Usage:
    python3 generate_money_simulation.py --output /path/to/money_simulation.html
"""
from __future__ import annotations

import argparse
import csv
import json
import os

CONTRACT_MULT = 100  # 1 lot = 1 contract = 100 shares, the standard equity-option multiplier
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "forward_test_log.csv")
TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "money_simulation_template.html")


def load_real_trades(csv_path=CSV_PATH):
    """Reads forward_test_log.csv and splits into (resolved, open) real trades --
    rows where a contract was actually built (entry_premium_mid is present).
    BUILDER_MIXED/EARNINGS_HARD_SKIP rows are never real trades -- no premium
    was ever recorded because no contract was ever built."""
    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))
    real = [r for r in rows if r["entry_premium_mid"] not in ("", None)]
    resolved = [r for r in real if r["resolution"] in ("TARGET", "STOP")]
    open_pos = [r for r in real if r["resolution"] == "OPEN"]

    # Every real trade (a contract was actually built) must land in exactly one
    # of the two buckets. A row with a real entry_premium_mid but a resolution
    # value that's neither TARGET/STOP/OPEN would otherwise vanish from the
    # simulation silently -- real money with nowhere to be counted. Fail loud
    # instead of quietly under-reporting total capital deployed.
    unclassified = [r for r in real if r not in resolved and r not in open_pos]
    if unclassified:
        tickers = ", ".join(f"{r['ticker']} ({r['resolution']!r})" for r in unclassified)
        raise ValueError(
            f"{len(unclassified)} row(s) have a real entry_premium_mid but an "
            f"unrecognized resolution value, not TARGET/STOP/OPEN: {tickers} -- "
            f"refusing to silently drop real money from the simulation"
        )
    return resolved, open_pos


def build_trades(resolved):
    """Resolved trades, chronological by resolve_date, with a running cumulative
    P&L -- the exact order the equity curve replays them in."""
    resolved_sorted = sorted(resolved, key=lambda r: (r["resolve_date"], r["ticker"]))
    trades = []
    running = 0.0
    for r in resolved_sorted:
        entry = float(r["entry_premium_mid"])
        exitp = float(r["exit_premium_mid"])
        cost = round(entry * CONTRACT_MULT, 2)
        proceeds = round(exitp * CONTRACT_MULT, 2)
        pnl = round(proceeds - cost, 2)
        running = round(running + pnl, 2)
        trades.append({
            "ticker": r["ticker"], "group": r["group"], "entry_date": r["entry_date"],
            "resolve_date": r["resolve_date"], "resolution": r["resolution"],
            "entry_premium": entry, "exit_premium": exitp,
            "cost": cost, "proceeds": proceeds, "pnl": pnl,
            "ret_pct": round(float(r["ret_pct"]), 1), "running_pnl": running,
        })
    return trades


def build_open_trades(open_pos):
    open_trades = []
    for r in sorted(open_pos, key=lambda r: r["entry_date"]):
        entry = float(r["entry_premium_mid"])
        open_trades.append({
            "ticker": r["ticker"], "group": r["group"], "entry_date": r["entry_date"],
            "entry_premium": entry, "cost": round(entry * CONTRACT_MULT, 2),
        })
    return open_trades


def build_summary(trades, open_trades):
    total_cost_resolved = round(sum(t["cost"] for t in trades), 2)
    total_pnl = round(sum(t["pnl"] for t in trades), 2)
    total_cost_open = round(sum(t["cost"] for t in open_trades), 2)

    by_group = {}
    for g in ("SURVIVOR", "REJECT"):
        gt = [t for t in trades if t["group"] == g]
        by_group[g] = {
            "n": len(gt), "cost": round(sum(t["cost"] for t in gt), 2),
            "pnl": round(sum(t["pnl"] for t in gt), 2),
            "wins": sum(1 for t in gt if t["resolution"] == "TARGET"),
            "losses": sum(1 for t in gt if t["resolution"] == "STOP"),
        }

    wins = [t for t in trades if t["resolution"] == "TARGET"]
    losses = [t for t in trades if t["resolution"] == "STOP"]

    return {
        "total_resolved": len(trades), "total_open": len(open_trades),
        "total_cost_resolved": total_cost_resolved, "total_pnl": total_pnl,
        "total_cost_open": total_cost_open,
        "roi_pct": round(total_pnl / total_cost_resolved * 100, 1) if total_cost_resolved else 0,
        "by_group": by_group,
        "avg_win": round(sum(t["pnl"] for t in wins) / len(wins), 2) if wins else 0,
        "avg_loss": round(sum(t["pnl"] for t in losses) / len(losses), 2) if losses else 0,
        "n_wins": len(wins), "n_losses": len(losses),
    }


def build_dataset(csv_path=CSV_PATH):
    resolved, open_pos = load_real_trades(csv_path)
    trades = build_trades(resolved)
    open_trades = build_open_trades(open_pos)
    summary = build_summary(trades, open_trades)
    return {"trades": trades, "open_trades": open_trades, "summary": summary}


def render(output_path, csv_path=CSV_PATH, template_path=TEMPLATE_PATH):
    dataset = build_dataset(csv_path)
    with open(template_path) as f:
        html = f.read()
    if "__DATA_JSON__" not in html:
        raise ValueError(f"{template_path} has no __DATA_JSON__ placeholder -- template may be corrupted")
    html = html.replace("__DATA_JSON__", json.dumps(dataset))
    with open(output_path, "w") as f:
        f.write(html)
    return dataset


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="Path to write the ready-to-publish HTML")
    parser.add_argument("--csv", default=CSV_PATH)
    parser.add_argument("--template", default=TEMPLATE_PATH)
    args = parser.parse_args()

    dataset = render(args.output, csv_path=args.csv, template_path=args.template)
    s = dataset["summary"]
    print(f"Regenerated {args.output}")
    print(f"  {s['total_resolved']} resolved trades, {s['total_open']} open")
    print(f"  Total P&L: ${s['total_pnl']:,.2f} ({s['roi_pct']:+.1f}% on ${s['total_cost_resolved']:,.2f} deployed)")


if __name__ == "__main__":
    main()
