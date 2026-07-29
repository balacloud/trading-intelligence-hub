"""
Static Ticker -> theme-cluster mapping for HUB_CORE / HUB_EXTENDED, transcribed
directly from docs/skills/skill-options-scanner.md's CORE/EXTENDED tables (the
skill's own hand-curated "Sector" column per ticker) -- not re-derived. That
skill file is the living source; test_ticker_themes.py asserts every ticker it
lists appears here in exactly one cluster, so the two never drift apart.

Each cluster optionally names a `proxy` ETF -- a real, tradeable ETF (verified
live against Tradier's own quotes, not asserted from memory) this hub can pull
daily price history for to compute a sub-industry relative-strength read.
First pass (Session 38) limited proxies to ETFs already on the HUB_EXTENDED
watchlist and left 12 clusters at `proxy: None` -- Bala pushed back hard on
that being lazy rather than researched (XLE for Energy, ITA for Defense were
clear misses, not real gaps). Second pass: verified a real candidate ETF per
cluster via live Tradier quotes (existence + average_volume), assigned proxies
to every cluster where a defensibly-fitting one exists, and only left a
cluster at `proxy: None` when no real ETF actually fits (currently just
"Past survivors"/POET -- a photonics niche name with no thematic ETF).
Liquidity only matters here for having a continuous daily-closes price series,
not for options tradability -- several of these proxies (DRIV, PHO, WGMI,
ITA) are thin by options-liquidity standards but perfectly fine as a pure
price-history input, a different bar than Gate C's dollar-volume floor
elsewhere in this hub. Imperfect fits (e.g. WGMI for the whole Crypto basket,
XLK doing double duty for both Optical/Connectivity and Enterprise Tech) are
disclosed in each cluster's own comment rather than presented as clean.

COPX/GRID/WGMI/IGV/KWEB/DRIV/UFO/XLK/ITA/BOTZ/PHO/XLE/XLC/XLY are all proxy-only
additions -- none are part of the live HUB_EXTENDED IBKR watchlist or the
options-screening pipeline; they exist solely as price-history inputs for this
advisory panel. See skill-options-scanner.md's Sector ETFs table for the
subset (COPX, GRID) documented there as future-watchlist candidates.
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
        # WGMI (CoinShares Bitcoin Mining ETF) is a precise fit for HIVE/MARA/RIOT
        # (literal bitcoin miners) but a looser one for COIN (exchange, different
        # business model) and MSTR (a levered BTC-holding company, not a miner) --
        # kept together anyway since all five trade as de facto BTC-price proxies
        # in practice; the imperfection is real and disclosed, not hidden.
        "tickers": ["HIVE", "MARA", "RIOT", "COIN", "MSTR"],
        "proxy": "WGMI",
    },
    "Software/SaaS": {
        "proxy": "IGV",  # iShares Expanded Tech-Software ETF -- precise fit, 18.5M avg vol
        "tickers": ["PLTR", "CRWD", "SNOW", "NET", "SHOP", "DDOG", "PATH", "GIB"],
    },
    "China Internet ADR": {
        # Split from the original "China ADR/EV" cluster (Session 38 pushback: forcing
        # BABA/PDD/JD's internet-ADR profile and NIO/LI/XPEV's EV-manufacturer profile
        # under one average was worse than two honest, narrower reads). KWEB (KraneShares
        # CSI China Internet ETF, 25.3M avg vol) fits this half cleanly.
        "proxy": "KWEB",
        "tickers": ["BABA", "PDD", "JD"],
    },
    "EV/Autonomous": {
        # The EV half of the old "China ADR/EV" split, plus RIVN pulled out of
        # "Space/Emerging" (RIVN is an EV maker, not a space name -- that was always
        # a labeling mismatch inherited from the skill file's own grouping). DRIV
        # (Global X Autonomous & Electric Vehicles ETF) is a literal, if thinner
        # (76K avg vol -- fine for a price-history read, no options liquidity needed
        # here), match for exactly this basket.
        "proxy": "DRIV",
        "tickers": ["NIO", "LI", "XPEV", "RIVN"],
    },
    "Space/Emerging": {
        "proxy": "UFO",  # Procure Space ETF, 1.3M avg vol -- clean fit now that RIVN is gone
        "tickers": ["LUNR", "RKLB", "ASTS"],
    },
    "Optical/Connectivity": {
        # No optical-networking-specific liquid ETF exists -- XLK (broad tech) is a
        # real, liquid fallback, not a precise one; disclosed as such rather than
        # left at "no proxy" when a reasonable directional read is still better than none.
        "proxy": "XLK",
        "tickers": ["GLW", "APH", "FN"],
    },
    "Enterprise Tech": {
        "proxy": "XLK",  # broad tech; TMUS moved out to Communication Services below
        "tickers": ["DELL", "HPE", "HPQ", "KEYS"],
    },
    "Communication Services": {
        # New cluster (Session 38) -- TMUS (telecom) and NFLX (streaming, moved out of
        # "Past survivors") both sit in GICS Communication Services; XLC is the standard,
        # liquid (6.4M avg vol) sector ETF.
        "proxy": "XLC",
        "tickers": ["TMUS", "NFLX"],
    },
    "Defense": {
        "proxy": "ITA",  # iShares U.S. Aerospace & Defense ETF -- standard, 801K avg vol
        "tickers": ["NOC"],
    },
    "Physical AI/Robotics": {
        "proxy": "BOTZ",  # Global X Robotics & AI ETF, 1.0M avg vol
        "tickers": ["CGNX", "ISRG"],
    },
    "Industrials/Water": {
        "proxy": "PHO",  # Invesco Water Resources ETF, 127K avg vol -- thinner but the
        # thematically precise choice over falling back to broad XLI
        "tickers": ["XYL"],
    },
    "Energy": {
        "proxy": "XLE",  # Energy Select Sector SPDR, 35.3M avg vol -- the clearest miss
        # in the first pass; OXY fits well, TRP (Canadian midstream) is a looser fit
        # within an E&P-weighted ETF but still the right real-world proxy
        "tickers": ["OXY", "TRP"],
    },
    "High-beta mega": {
        "proxy": "XLY",  # TSLA's actual GICS sector (Consumer Discretionary), 8.2M avg vol
        "tickers": ["TSLA"],
    },
    "Past survivors": {
        # POET (photonics) has no clean thematic ETF -- stays genuinely proxy-less
        # rather than forced into a bad fit. NFLX moved to Communication Services above.
        "proxy": None,
        "tickers": ["POET"],
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
