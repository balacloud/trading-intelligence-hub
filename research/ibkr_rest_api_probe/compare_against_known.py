"""
Cross-reference a probe_fields.py output against a real, known IV Rank value
(paste it in from an actual IBKR watchlist - never fabricate this input).

This only ever produces LEADS, not confirmation. A field matching on one ticker
could be coincidence (lots of 0-100-range numbers exist - RSI, range position,
percentile fields that aren't IVR at all). Real confirmation needs the same
field ID landing close across 2-3 tickers with meaningfully different known
IVR values - see README.md's "what success looks like" section.

Usage:
  python3 compare_against_known.py probe_results_NVDA_20260722T190000Z.json --known-ivr 41
"""
import argparse
import json
import re


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("probe_file", help="Output JSON from probe_fields.py")
    parser.add_argument(
        "--known-ivr", type=float, required=True,
        help="The REAL IV Rank for this ticker, pasted from an actual IBKR watchlist. "
             "Never estimate or guess this value - the whole point is comparing against ground truth.",
    )
    parser.add_argument(
        "--tolerance", type=float, default=3.0,
        help="How close (absolute difference) counts as a candidate match. Default 3.0.",
    )
    args = parser.parse_args()

    data = json.loads(open(args.probe_file).read())
    print(f"Comparing {data['symbol']} (conid {data['conid']}) against known IV Rank = {args.known_ivr}\n")

    candidates = []
    for field_id, value in data["non_null_fields"].items():
        num = _try_parse_number(value)
        if num is None:
            continue
        # Only consider values plausibly in IVR's 0-100 range - a $400 stock price
        # or a 5-million-share volume figure isn't a candidate no matter how you squint.
        if not (0 <= num <= 100):
            continue
        diff = abs(num - args.known_ivr)
        if diff <= args.tolerance:
            candidates.append((field_id, value, num, diff))

    if not candidates:
        print("No candidate fields found within tolerance. Either IV Rank genuinely "
              "isn't in this field set, or the tolerance is too tight - try --tolerance 5 "
              "and sanity-check the non_null_fields list by eye too.")
        return

    candidates.sort(key=lambda c: c[3])
    print(f"{len(candidates)} candidate field(s) - LEADS ONLY, not confirmed:\n")
    for field_id, raw_value, num, diff in candidates:
        print(f"  field {field_id}: raw={raw_value!r}  parsed={num}  |diff|={diff:.2f}")

    print(
        "\nNext step: run this same probe against 2-3 more tickers with clearly "
        "different known IVR values. A field ID that keeps landing close across all "
        "of them is a real finding. A field that only matched once here is coincidence "
        "until proven otherwise - the 0-100 range is small enough that false positives "
        "are expected, not surprising."
    )


def _try_parse_number(value):
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        m = re.match(r"^-?\d+(\.\d+)?", value.strip().rstrip("%"))
        if m:
            return float(m.group())
    return None


if __name__ == "__main__":
    main()
