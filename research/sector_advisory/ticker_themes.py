"""
Static Ticker -> theme-cluster mapping for HUB_CORE / HUB_EXTENDED, transcribed
directly from docs/skills/skill-options-scanner.md's CORE/EXTENDED tables (the
skill's own hand-curated "Sector" column per ticker) -- not re-derived. That
skill file is the living source; test_ticker_themes.py asserts every ticker it
lists appears here in exactly one cluster, so the two never drift apart.

Each cluster optionally names a `proxy` ETF -- a real, already-liquid ETF this
hub can pull live price history for (via Tradier) to compute a sub-industry
relative-strength read. Clusters with `proxy: None` have no clean ETF on the
watchlist to stand in for them (Crypto, Software/SaaS, China ADR/EV, Space,
etc.) -- shown in the advisory panel as "no sector-relative read available,"
never assigned a guessed/imperfect proxy (Bala's explicit call, Session 38).

COPX (critical materials) and GRID (AI power infra) are new proxies added this
session -- not yet part of the live HUB_EXTENDED IBKR watchlist, only used here
to pull price history directly via Tradier. See skill-options-scanner.md's
Sector ETFs table for the documented addition.
"""
from __future__ import annotations

CLUSTERS = {
    "Semis": {
        "proxy": "SMH",
        "fallback_proxy": "SOXX",
        "tickers": ["NVDA", "AMD", "MU", "MRVL", "AVGO", "SMCI", "ARM", "ON",
                    "QCOM", "TSM", "AMAT", "LRCX", "KLAC", "ASML", "LSCC", "ALAB"],
    },
    "Memory/Storage": {
        "proxy": "DRAM",
        "tickers": ["WDC"],
    },
    "AI Infra/Power": {
        "proxy": "GRID",
        "tickers": ["CEG", "ETN", "ANET", "ABB", "GEV", "VRT", "PWR", "MOD"],
    },
    "Nuclear/Uranium": {
        "proxy": "URA",
        "tickers": ["CCJ", "OKLO", "BWXT"],
    },
    "Critical Materials": {
        "proxy": "COPX",
        "tickers": ["ALB", "FCX", "MP", "TECK"],
    },
    "Gold Miners": {
        "proxy": "GDX",
        "tickers": [],  # GDX itself IS the theme -- no separate stock names on the watchlist
    },
    "Biotech": {
        "proxy": "XBI",
        "tickers": [],  # XBI itself IS the theme -- no separate stock names on the watchlist
    },
    "Financials/Fintech": {
        "proxy": "XLF",
        "tickers": ["GS", "PYPL", "HOOD", "SOFI", "AFRM", "UPST"],
    },
    # No proxy ETF on the watchlist for these -- "no sector-relative read", never guessed:
    "Crypto": {
        "proxy": None,
        "tickers": ["HIVE", "MARA", "RIOT", "COIN", "MSTR"],
    },
    "Software/SaaS": {
        "proxy": None,
        "tickers": ["PLTR", "CRWD", "SNOW", "NET", "SHOP", "DDOG", "PATH", "GIB"],
    },
    "China ADR/EV": {
        "proxy": None,
        "tickers": ["BABA", "PDD", "NIO", "LI", "XPEV", "JD"],
    },
    "Space/Emerging": {
        "proxy": None,
        "tickers": ["LUNR", "RKLB", "RIVN", "ASTS"],
    },
    "Optical/Connectivity": {
        "proxy": None,
        "tickers": ["GLW", "APH", "FN"],
    },
    "Enterprise Tech": {
        "proxy": None,
        "tickers": ["DELL", "HPE", "HPQ", "TMUS", "KEYS"],
    },
    "Defense": {
        "proxy": None,
        "tickers": ["NOC"],
    },
    "Physical AI/Robotics": {
        "proxy": None,
        "tickers": ["CGNX", "ISRG"],
    },
    "Industrials/Water": {
        "proxy": None,
        "tickers": ["XYL"],
    },
    "Energy": {
        "proxy": None,
        "tickers": ["OXY", "TRP"],
    },
    "High-beta mega": {
        "proxy": None,
        "tickers": ["TSLA"],
    },
    "Past survivors": {
        "proxy": None,
        "tickers": ["NFLX", "POET"],
    },
}


def ticker_to_cluster(ticker: str) -> str | None:
    """Returns the cluster name a ticker belongs to, or None if it's not in any
    cluster (e.g. a name added to the live watchlist but not yet transcribed
    here -- never silently misattributed to the wrong cluster)."""
    for cluster_name, info in CLUSTERS.items():
        if (ticker in info["tickers"] or ticker == info.get("proxy")
                or ticker == info.get("fallback_proxy")):
            return cluster_name
    return None


def all_mapped_tickers() -> set[str]:
    """Every ticker covered by this mapping, stock names plus the cluster's own
    proxy ETF(s) (a proxy can itself appear as a HUB_EXTENDED watchlist row,
    e.g. DRAM, SMH, SOXX, URA, XLF, XBI, GDX)."""
    covered = set()
    for info in CLUSTERS.values():
        covered.update(info["tickers"])
        if info.get("proxy"):
            covered.add(info["proxy"])
        if info.get("fallback_proxy"):
            covered.add(info["fallback_proxy"])
    return covered
