"""
Live pull of STA's (swing-trade-analyzer) broad 11-GICS-sector rotation data,
for context alongside the sub-industry proxies computed in theme_strength.py.

STA is a separate local Flask backend (localhost:5001, confirmed reachable
Session 38) with no uptime track record in *this* pipeline -- unlike Tradier,
which build_and_log.py/resolve_positions.py already depend on directly. This
module never raises: any failure degrades to `available: False` and the
report renders "STA unavailable" for this one section, never blocking the
sub-industry or forward-test-crossref sections. Matches the same
try/except-and-degrade shape options-iq's own sector_scan_service.py already
uses for this exact call.
"""
from __future__ import annotations

import requests

STA_BASE_URL = "http://localhost:5001"
STA_TIMEOUT_SEC = 5


def fetch_sta_rotation(base_url: str = STA_BASE_URL) -> dict:
    try:
        resp = requests.get(f"{base_url}/api/sectors/rotation", timeout=STA_TIMEOUT_SEC)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        return {"available": False, "reason": str(exc)}

    sectors = data.get("sectors", [])
    return {
        "available": True,
        "macro_alignment_status": data.get("macro_alignment_status"),
        "macro_alignment": data.get("macro_alignment"),
        "sectors": [
            {"etf": s.get("etf"), "quadrant": s.get("quadrant"),
             "rs_ratio": s.get("rsRatio"), "momentum_pct": s.get("rsMomentum")}
            for s in sectors
        ],
    }
