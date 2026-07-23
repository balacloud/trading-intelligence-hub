"""
Sweep IBKR's documented market-data field-ID ranges for a real ticker and record
every field that returns a non-null value. No field IDs are assumed to mean
anything in particular here - this just harvests raw (id -> value) pairs so a
human can cross-reference against a known real IV Rank afterward.

Ranges swept (documented in IBKR's Web API field reference as where market-data
tags live - not exhaustive, but covers the "core" quote fields and the
"extended"/fundamentals-and-options-adjacent block where IV/HV-style fields
have historically lived):
  - 31-90      core quote fields (price, bid/ask, volume, etc.)
  - 6000-6200  contract/identification fields
  - 7000-7900  extended fields (options greeks, IV/HV, fundamentals, technicals)

Usage:
  python3 probe_fields.py NVDA
  python3 probe_fields.py NVDA --sec-type STK
"""
import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import client

RANGES = [
    range(31, 91),
    range(6000, 6201),
    range(7000, 7901),
]

BATCH_SIZE = 50
PAUSE_BETWEEN_CALLS_SEC = 0.3  # be a reasonable citizen against the local gateway


def all_field_ids() -> list[str]:
    ids = []
    for r in RANGES:
        ids.extend(str(i) for i in r)
    return ids


def batched(items, size):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("symbol", help="Ticker to probe, e.g. NVDA")
    parser.add_argument("--sec-type", default="STK")
    args = parser.parse_args()

    status = client.auth_status()
    if not status.get("authenticated"):
        raise SystemExit(
            f"Gateway not authenticated: {status}\n"
            "Log in via browser at https://localhost:5000 first (see README.md)."
        )

    conid = client.search_conid(args.symbol, args.sec_type)
    print(f"{args.symbol} -> conid {conid}")

    field_ids = all_field_ids()
    print(f"Sweeping {len(field_ids)} field IDs in batches of {BATCH_SIZE}...")

    # Warm-up call - IBKR's own docs note the first snapshot request for a conid
    # often returns sparse data until the subscription "wakes up" server-side.
    client.snapshot([conid], field_ids[:10])
    time.sleep(1)

    found = {}
    raw_batches = []
    for batch_num, batch in enumerate(batched(field_ids, BATCH_SIZE), start=1):
        result = client.snapshot([conid], batch)
        raw_batches.append(result)
        if result:
            row = result[0]
            # IMPORTANT: IBKR's snapshot returns ALL currently-subscribed fields for
            # this conid, not just the ones requested in this specific call - capture
            # everything present in the response, not just keys matching `batch`.
            # (Found empirically: a call requesting 8 fields came back with 60+.)
            for field_id, value in row.items():
                if value not in (None, ""):
                    found[field_id] = value
        print(f"  batch {batch_num}: {len(field_ids)//BATCH_SIZE + 1} total, "
              f"{len(found)} non-null fields found so far")
        time.sleep(PAUSE_BETWEEN_CALLS_SEC)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = Path(__file__).parent / f"probe_results_{args.symbol}_{timestamp}.json"
    out_path.write_text(json.dumps({
        "symbol": args.symbol,
        "conid": conid,
        "probed_at_utc": timestamp,
        "non_null_fields": found,
        "raw_batches": raw_batches,
    }, indent=2))

    print(f"\n{len(found)} non-null fields found. Full detail: {out_path}")
    print("\nNon-null fields (id: value):")
    numeric = {k: v for k, v in found.items() if k.isdigit()}
    non_numeric = {k: v for k, v in found.items() if not k.isdigit()}
    for field_id, value in sorted(numeric.items(), key=lambda x: int(x[0])):
        print(f"  {field_id}: {value}")
    if non_numeric:
        print("\nNon-numeric keys (conid, server metadata, etc. - not market-data field tags):")
        for k, v in non_numeric.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
