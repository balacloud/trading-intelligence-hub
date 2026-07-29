"""
Read-only cross-reference of forward_test_log.csv's OPEN positions against
their theme cluster's live quadrant -- the actual "would this have caught
DRAM" feature. Never writes to the CSV, never touches run_scan.py/
build_and_log.py/sieves.py -- advisory only (Bala's explicit call, Session 38).

Direction isn't a structured CSV column (checked build_and_log.py's row
construction directly rather than assuming) -- it only exists inside the free-
text `notes` field, always written as "Direction=BULLISH"/"Direction=BEARISH"
(build_and_log.py's own f-string, "Built via build_and_log.py. Direction=...").
Parsed via regex; a row with no match shows direction=None ("unknown"), never
guessed from the contract's strike/call-vs-put shape or anything else.
"""
from __future__ import annotations

import csv
import os
import re

from ticker_themes import ticker_to_cluster

CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "forward_test", "forward_test_log.csv"
)

DIRECTION_RE = re.compile(r"Direction=(BULLISH|BEARISH)")

# A cluster's current quadrant "agrees" with a logged direction when the trade bets the
# way the sector is actually leaning; anything else is flagged. BULLISH wants
# Leading/Improving; BEARISH wants Weakening/Lagging.
BULLISH_AGREES_WITH = {"Leading", "Improving"}
BEARISH_AGREES_WITH = {"Weakening", "Lagging"}


def load_open_rows(csv_path: str = CSV_PATH) -> list[dict]:
    """Real, still-open trades only -- resolution == "OPEN" AND a contract was
    actually built (entry_premium_mid present). Excludes EARNINGS_HARD_SKIP /
    BUILDER_MIXED / SIEVE-purged rows, which also have no resolve_date but were
    never real positions to begin with -- same "was a contract actually built"
    filter generate_money_simulation.py already uses for its own real-trade set."""
    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows
            if r.get("resolution") == "OPEN" and (r.get("entry_premium_mid") or "").strip() != ""]


def parse_direction(notes: str) -> str | None:
    m = DIRECTION_RE.search(notes or "")
    return m.group(1) if m else None


def crossref_open_positions(open_rows: list[dict], cluster_quadrants: dict[str, dict]) -> list[dict]:
    """cluster_quadrants: {cluster_name: theme_strength.compute_cluster_strength() result}
    for clusters that have a proxy. Returns one entry per OPEN row with its cluster,
    direction, the cluster's quadrant (if any), and whether they disagree."""
    out = []
    for r in open_rows:
        ticker = r["ticker"]
        cluster = ticker_to_cluster(ticker)
        direction = parse_direction(r.get("notes", ""))
        quadrant_info = cluster_quadrants.get(cluster) if cluster else None
        quadrant = quadrant_info["quadrant"] if quadrant_info else None

        flagged = False
        if direction and quadrant:
            if direction == "BULLISH" and quadrant not in BULLISH_AGREES_WITH:
                flagged = True
            elif direction == "BEARISH" and quadrant not in BEARISH_AGREES_WITH:
                flagged = True

        out.append({
            "ticker": ticker, "group": r["group"], "entry_date": r["entry_date"],
            "cluster": cluster, "direction": direction,
            "quadrant": quadrant, "rs_ratio": quadrant_info["rs_ratio"] if quadrant_info else None,
            "momentum_pct": quadrant_info["momentum_pct"] if quadrant_info else None,
            "flagged": flagged,
        })
    return out
