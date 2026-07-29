"""
Sync-guard: every ticker listed in docs/skills/skill-options-scanner.md's
CORE/EXTENDED/Sector-ETFs tables must appear in ticker_themes.py's CLUSTERS,
so the skill file (the actual watchlist definition) and this advisory panel's
mapping never silently drift apart -- same discipline as test_spec_sync.py.
"""
import os
import re

from ticker_themes import CLUSTERS, all_mapped_tickers, ticker_to_cluster

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKILL_PATH = os.path.join(REPO_ROOT, "docs", "skills", "skill-options-scanner.md")

TICKER_ROW_RE = re.compile(r"^\|\s*([A-Z]{1,6}(?: [A-Z]{1,2})?)\s*\|")


def _tickers_from_skill_file() -> set[str]:
    with open(SKILL_PATH) as f:
        text = f.read()
    start = text.index("## THE WATCHLIST")
    end = text.index("## COLUMN SPEC")
    section = text[start:end]

    tickers = set()
    for line in section.splitlines():
        if line.startswith("| Ticker") or line.startswith("|--------"):
            continue
        m = TICKER_ROW_RE.match(line)
        if m:
            tickers.add(m.group(1))
    return tickers


def test_every_skill_file_ticker_is_mapped():
    skill_tickers = _tickers_from_skill_file()
    mapped = all_mapped_tickers()
    missing = skill_tickers - mapped
    assert not missing, (
        f"{len(missing)} ticker(s) in skill-options-scanner.md have no entry in "
        f"ticker_themes.py CLUSTERS: {sorted(missing)}"
    )


def test_every_cluster_ticker_appears_exactly_once():
    seen = {}
    for cluster_name, info in CLUSTERS.items():
        for t in info["tickers"]:
            assert t not in seen, f"{t} appears in both {seen[t]!r} and {cluster_name!r}"
            seen[t] = cluster_name


def test_almost_every_cluster_has_a_researched_proxy():
    # Session 38 second pass: verified a real ETF per cluster via live Tradier quotes
    # rather than defaulting to "no proxy" for anything not already on the watchlist.
    # Only a cluster with no genuinely fitting ETF should stay proxy-less -- currently
    # just "Past survivors" (POET, a photonics niche name). If this count grows, it
    # should be because a new cluster with no defensible proxy was added, not because
    # research was skipped for one that has an obvious fit (the original miss on
    # Energy/XLE and Defense/ITA).
    no_proxy_clusters = [name for name, info in CLUSTERS.items() if info["proxy"] is None]
    assert no_proxy_clusters == ["Past survivors"]


def test_ticker_to_cluster_resolves_stock_and_proxy():
    assert ticker_to_cluster("NVDA") == "Semis"
    assert ticker_to_cluster("SMH") == "Semis"  # proxy itself resolves too
    assert ticker_to_cluster("DRAM") == "Memory/Storage"
    assert ticker_to_cluster("NOTATICKER") is None


def test_dram_and_wdc_land_in_memory_cluster():
    # The exact real case that prompted this whole panel (Session 38, Jul 29 2026).
    assert ticker_to_cluster("DRAM") == "Memory/Storage"
    assert ticker_to_cluster("WDC") == "Memory/Storage"
