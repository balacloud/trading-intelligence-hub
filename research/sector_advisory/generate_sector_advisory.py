"""
Generates the standalone Sector/Theme Advisory Panel -- a read-only HTML
report combining broad GICS-sector context (from STA), a new sub-industry
relative-strength read (semis, memory, nuclear, materials, gold, biotech,
financials -- theme_strength.py), and a cross-reference against today's open
forward-test positions (candidate_crossref.py) that flags when a logged
direction disagrees with its cluster's current quadrant.

Built at Bala's explicit request (Session 38, Jul 29 2026) after reviewing an
open DRAM position logged BULLISH on a thin 2/2-signal vote while semis
broadly sold off hard the same day. Purely advisory: reads
forward_test_log.csv, never writes to it; makes zero changes to run_scan.py /
build_and_log.py / sieves.py. Mirrors generate_money_simulation.py's own
render()/main() shape exactly -- same template-injection pattern
(__DATA_JSON__ placeholder swap), same "build one dataset dict, then render"
structure.

Usage:
    python3 generate_sector_advisory.py --output sector_advisory.html
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime, timezone
import zoneinfo

import broad_sector_context
import candidate_crossref
import provider_divergence
import theme_strength
from ticker_themes import CLUSTERS

TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sector_advisory_template.html")
DEFAULT_OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sector_advisory.html")


def build_sub_industry_and_no_proxy(token: str, today: date) -> tuple[list[dict], list[dict], dict]:
    """Returns (sub_industry_list, no_proxy_list, cluster_quadrants) where
    cluster_quadrants maps cluster name -> its compute_cluster_strength() result,
    for candidate_crossref to consume. SPY closes fetched once and shared across
    every proxy computation. If that one fetch fails, every cluster gets the same
    single error immediately -- passing spy_closes=None down to
    compute_cluster_strength instead would make each cluster silently re-attempt
    its own SPY fetch (8 redundant, doomed Tradier calls instead of 1), which is
    exactly the "fetched once" claim this docstring makes -- caught in this
    module's own Pass 2 review rather than left as a real inefficiency."""
    spy_error = None
    try:
        spy_closes = theme_strength.fetch_daily_closes("SPY", token, today)
    except Exception as exc:
        spy_closes = None
        spy_error = str(exc)

    sub_industry = []
    no_proxy = []
    cluster_quadrants = {}
    for cluster_name, info in CLUSTERS.items():
        proxy = info.get("proxy")
        if proxy is None:
            no_proxy.append({"cluster": cluster_name, "tickers": info["tickers"]})
            continue
        if spy_error is not None:
            result = {"proxy": proxy, "quadrant": None, "rs_ratio": None, "momentum_pct": None,
                      "short_history": None, "usable_days": None, "error": f"SPY fetch failed: {spy_error}"}
        else:
            result = theme_strength.compute_cluster_strength(proxy, token, today, spy_closes=spy_closes)
        result["cluster"] = cluster_name
        result["tickers"] = info["tickers"]
        sub_industry.append(result)
        cluster_quadrants[cluster_name] = result

    return sub_industry, no_proxy, cluster_quadrants


def build_dataset(csv_path: str = candidate_crossref.CSV_PATH) -> dict:
    token = theme_strength.load_tradier_token()
    today = date.today()

    sub_industry, no_proxy, cluster_quadrants = build_sub_industry_and_no_proxy(token, today)
    broad = broad_sector_context.fetch_sta_rotation()

    open_rows = candidate_crossref.load_open_rows(csv_path)
    open_positions = candidate_crossref.crossref_open_positions(open_rows, cluster_quadrants)

    divergences = provider_divergence.find_divergences(sub_industry, broad)

    try:
        now_et = datetime.now(timezone.utc).astimezone(zoneinfo.ZoneInfo("America/New_York"))
        generated_at = now_et.strftime("%Y-%m-%d %H:%M %Z")
    except Exception:
        generated_at = datetime.now(timezone.utc).isoformat()

    return {
        "generated_at": generated_at,
        "broad_sectors": broad,
        "sub_industry": sub_industry,
        "no_proxy_clusters": no_proxy,
        "open_positions": open_positions,
        "provider_divergences": divergences,
    }


def render(output_path: str, template_path: str = TEMPLATE_PATH, csv_path: str = candidate_crossref.CSV_PATH) -> dict:
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
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Path to write the HTML report")
    parser.add_argument("--template", default=TEMPLATE_PATH)
    parser.add_argument("--csv", default=candidate_crossref.CSV_PATH)
    args = parser.parse_args()

    dataset = render(args.output, template_path=args.template, csv_path=args.csv)
    print(f"Generated {args.output}")

    if not dataset["broad_sectors"].get("available"):
        print(f"  Broad sectors: STA unavailable ({dataset['broad_sectors'].get('reason')})")
    else:
        print(f"  Broad sectors: {len(dataset['broad_sectors']['sectors'])} GICS sectors pulled live")

    for c in dataset["sub_industry"]:
        if c["error"]:
            print(f"  {c['cluster']} ({c['proxy']}): ERROR — {c['error']}")
        else:
            print(f"  {c['cluster']} ({c['proxy']}): {c['quadrant']} "
                  f"(RS {c['rs_ratio']}, mom {c['momentum_pct']:+.2f}%)"
                  + (" [short history]" if c["short_history"] else ""))

    flagged = [p for p in dataset["open_positions"] if p["flagged"]]
    print(f"  Open positions: {len(dataset['open_positions'])} total, {len(flagged)} flagged")
    for p in flagged:
        print(f"    ⚠ {p['ticker']} ({p['group']}) {p['direction']} vs {p['cluster']}={p['quadrant']}")

    if dataset["provider_divergences"]:
        print(f"  Provider divergence: {len(dataset['provider_divergences'])} ticker(s) "
              f"disagree on momentum sign between Tradier and STA's yfinance")
        for d in dataset["provider_divergences"]:
            print(f"    ⚠ {d['ticker']}: hub(Tradier)={d['hub_momentum_pct']:+.2f}% vs "
                  f"STA(yfinance)={d['sta_momentum_pct']:+.2f}%")


if __name__ == "__main__":
    main()
