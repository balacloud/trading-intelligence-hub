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

Two sizing modes, both computed and shipped in the same payload so the artifact
can toggle between them client-side:
  - lot1: exactly 1 contract per trade (the original view). A trade's dollar
    P&L swing is purely a function of the underlying's own share price -- a
    $1,070 stock (GS) swings ~7x harder than a $15 stock (CAG) for the same
    percentage move, unrelated to trade quality.
  - fixed_risk: contracts sized so max loss (entry-stop)*100*contracts is
    approximately constant across every trade (RISK_BUDGET_DEFAULT). Added
    Session 37 after Bala's real observation that GS's single stop-out
    swamped the whole 1-lot simulation -- reframed from "avoid costly
    options" (which would discard valid edge on expensive names) to "size
    every trade to the same dollar risk" (TRADER_LENS.md, Jul 28 2026 entry).
    Some trades' minimum 1-contract risk already exceeds the budget (GS: a
    single contract risks $1,380 against a $500 budget) -- flagged explicitly
    as budget_exceeded rather than silently forcing an undersized allocation
    that reads as if it worked.

Usage:
    python3 generate_money_simulation.py --output /path/to/money_simulation.html
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os

CONTRACT_MULT = 100  # 1 lot = 1 contract = 100 shares, the standard equity-option multiplier
RISK_BUDGET_DEFAULT = 500.0  # illustrative fixed $ risked per trade under fixed_risk sizing
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


def contracts_for_trade(entry, stop, mode, risk_budget=RISK_BUDGET_DEFAULT):
    """Returns (contracts, budget_exceeded). lot1 is always 1 contract, flat.
    fixed_risk sizes contracts so (entry-stop)*100*contracts approximates
    risk_budget -- floor to a whole contract (never fractional), minimum 1
    (a trade can't be sized to zero contracts; that's declining the trade,
    not sizing it, and this function only sizes trades that were actually
    taken). budget_exceeded=True when even 1 contract's own risk already
    exceeds the budget (e.g. GS: $1,380 risk vs a $500 budget) -- surfaced
    explicitly rather than silently accepting an oversized allocation as if
    the sizing target had been met."""
    if mode == "lot1":
        return 1, False
    if mode != "fixed_risk":
        raise ValueError(f"unknown sizing mode {mode!r}")
    risk_per_contract = round((entry - stop) * CONTRACT_MULT, 4)
    if risk_per_contract <= 0:
        # Stop must be below entry for a real, already-built long option position
        # (build_and_log.py's STOP_MULTIPLIER < 1.0 always) -- a non-positive risk
        # would mean corrupted input, not a real sizing case. Fail loud.
        raise ValueError(f"non-positive risk_per_contract ({risk_per_contract}) from entry={entry}, stop={stop}")
    contracts = math.floor(risk_budget / risk_per_contract)
    budget_exceeded = contracts < 1
    return max(1, contracts), budget_exceeded


def build_trades(resolved, mode="lot1", risk_budget=RISK_BUDGET_DEFAULT):
    """Resolved trades, chronological by resolve_date, with a running cumulative
    P&L -- the exact order the equity curve replays them in."""
    resolved_sorted = sorted(resolved, key=lambda r: (r["resolve_date"], r["ticker"]))
    trades = []
    running = 0.0
    for r in resolved_sorted:
        entry = float(r["entry_premium_mid"])
        exitp = float(r["exit_premium_mid"])
        stop = float(r["stop"])
        contracts, budget_exceeded = contracts_for_trade(entry, stop, mode, risk_budget)
        cost = round(entry * CONTRACT_MULT * contracts, 2)
        proceeds = round(exitp * CONTRACT_MULT * contracts, 2)
        pnl = round(proceeds - cost, 2)
        running = round(running + pnl, 2)
        trades.append({
            "ticker": r["ticker"], "group": r["group"], "entry_date": r["entry_date"],
            "resolve_date": r["resolve_date"], "resolution": r["resolution"],
            "entry_premium": entry, "exit_premium": exitp, "contracts": contracts,
            "budget_exceeded": budget_exceeded,
            "cost": cost, "proceeds": proceeds, "pnl": pnl,
            "ret_pct": round(float(r["ret_pct"]), 1), "running_pnl": running,
        })
    return trades


def build_open_trades(open_pos, mode="lot1", risk_budget=RISK_BUDGET_DEFAULT):
    open_trades = []
    for r in sorted(open_pos, key=lambda r: r["entry_date"]):
        entry = float(r["entry_premium_mid"])
        stop = float(r["stop"])
        contracts, budget_exceeded = contracts_for_trade(entry, stop, mode, risk_budget)
        open_trades.append({
            "ticker": r["ticker"], "group": r["group"], "entry_date": r["entry_date"],
            "entry_premium": entry, "contracts": contracts, "budget_exceeded": budget_exceeded,
            "cost": round(entry * CONTRACT_MULT * contracts, 2),
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
    budget_exceeded_trades = [t["ticker"] for t in trades if t.get("budget_exceeded")]

    return {
        "total_resolved": len(trades), "total_open": len(open_trades),
        "total_cost_resolved": total_cost_resolved, "total_pnl": total_pnl,
        "total_cost_open": total_cost_open,
        "roi_pct": round(total_pnl / total_cost_resolved * 100, 1) if total_cost_resolved else 0,
        "by_group": by_group,
        "avg_win": round(sum(t["pnl"] for t in wins) / len(wins), 2) if wins else 0,
        "avg_loss": round(sum(t["pnl"] for t in losses) / len(losses), 2) if losses else 0,
        "n_wins": len(wins), "n_losses": len(losses),
        "budget_exceeded_trades": budget_exceeded_trades,
    }


def build_dataset_for_mode(resolved, open_pos, mode, risk_budget=RISK_BUDGET_DEFAULT):
    trades = build_trades(resolved, mode=mode, risk_budget=risk_budget)
    open_trades = build_open_trades(open_pos, mode=mode, risk_budget=risk_budget)
    summary = build_summary(trades, open_trades)
    return {"trades": trades, "open_trades": open_trades, "summary": summary}


def build_dataset(csv_path=CSV_PATH, risk_budget=RISK_BUDGET_DEFAULT):
    resolved, open_pos = load_real_trades(csv_path)
    return {
        "risk_budget": risk_budget,
        "lot1": build_dataset_for_mode(resolved, open_pos, "lot1"),
        "fixed_risk": build_dataset_for_mode(resolved, open_pos, "fixed_risk", risk_budget),
    }


def render(output_path, csv_path=CSV_PATH, template_path=TEMPLATE_PATH, risk_budget=RISK_BUDGET_DEFAULT):
    dataset = build_dataset(csv_path, risk_budget=risk_budget)
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
    parser.add_argument("--risk-budget", type=float, default=RISK_BUDGET_DEFAULT,
                         help="Illustrative fixed $ risked per trade under fixed_risk sizing")
    args = parser.parse_args()

    dataset = render(args.output, csv_path=args.csv, template_path=args.template, risk_budget=args.risk_budget)
    print(f"Regenerated {args.output}")
    for mode in ("lot1", "fixed_risk"):
        s = dataset[mode]["summary"]
        print(f"[{mode}] {s['total_resolved']} resolved, {s['total_open']} open -- "
              f"P&L ${s['total_pnl']:,.2f} ({s['roi_pct']:+.1f}% on ${s['total_cost_resolved']:,.2f} deployed)")
        if s["budget_exceeded_trades"]:
            print(f"    budget-exceeded (1 contract alone risks more than ${args.risk_budget:,.0f}): "
                  f"{', '.join(s['budget_exceeded_trades'])}")


if __name__ == "__main__":
    main()
