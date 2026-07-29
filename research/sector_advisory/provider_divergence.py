"""
Same-ticker, cross-data-provider consistency check -- Gap 2 mitigation
(Session 38, Jul 29 2026). This panel's Sub-Industry section fetches its
proxy ETFs' price history from Tradier; STA's Broad Sectors section
(broad_sector_context.py) computes its own 11 GICS ETFs from yfinance. Five
proxies happen to be the exact same instrument as one of STA's 11 broad
sectors (XLF, XLK x2, XLC, XLE, XLY) -- for those five, and only those five,
this module can compare the SAME ticker computed by two different data
providers, which is a real, meaningful check unlike comparing two different
tickers that just happen to be thematically related.

Deliberately narrow: this does NOT try to reconcile the two sides'
normalization conventions (this panel indexes RS-ratio to 100 at the start of
its own ~6mo window; STA uses a static midpoint of its own period -- two
different, both-legitimate choices that can disagree on absolute RS-ratio
level even with identical, correct input data). What SHOULD agree regardless
of convention is the 10-day MOMENTUM SIGN -- a short delta over the same
underlying price ratio, robust to how the longer window was normalized. A
momentum-sign disagreement on the same ticker is a real, worth-surfacing
signal (a genuine data discrepancy between Tradier and yfinance for that
name); a same-sign-but-different-magnitude read is expected and not flagged.
"""
from __future__ import annotations

# proxy ticker -> True if that proxy IS also one of STA's 11 broad-sector ETFs
SHARED_TICKERS = {"XLF", "XLK", "XLC", "XLE", "XLY"}


def find_divergences(sub_industry: list[dict], broad_sectors: dict) -> list[dict]:
    if not broad_sectors.get("available"):
        return []  # nothing to compare against -- not a divergence, just no STA data this run

    broad_by_etf = {s["etf"]: s for s in broad_sectors.get("sectors", [])}

    divergences = []
    for cluster in sub_industry:
        proxy = cluster.get("proxy")
        if proxy not in SHARED_TICKERS:
            continue
        broad = broad_by_etf.get(proxy)
        if broad is None:
            continue  # proxy isn't actually one of STA's 11 (shouldn't happen given SHARED_TICKERS)

        hub_mom = cluster.get("momentum_pct")
        sta_mom = broad.get("momentum_pct")
        if hub_mom is None or sta_mom is None:
            continue  # one side had an error/no read -- not a disagreement, just missing data

        hub_sign_positive = hub_mom > 0
        sta_sign_positive = sta_mom > 0
        if hub_sign_positive != sta_sign_positive:
            divergences.append({
                "ticker": proxy, "cluster": cluster["cluster"],
                "hub_quadrant": cluster.get("quadrant"), "hub_momentum_pct": hub_mom,
                "sta_quadrant": broad.get("quadrant"), "sta_momentum_pct": sta_mom,
            })
    return divergences
