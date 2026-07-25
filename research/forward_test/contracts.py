"""
Contract resolution -- two deliberately separate concerns (Plan Section 2.2):

  Part A: pick the correct US-listed underlying row out of search_contracts'
  noisy result set (IBKR MCP data, pure filter).

  Part B: pick the best option contract off an already-resolved Tradier
  chain, by delta band + liquidity floor (Tradier data, pure filter).

Neither function fetches anything -- both take already-fetched rows/chains
and filter them. This replaces build_and_log.py's pick_atm_contract(), which
only picked nearest-strike-to-spot with no delta/OI/spread filtering at all
(confirmed cruder than the manual selection process it was meant to
automate -- see PLAN_deterministic_pipeline_formalization.md Section 0).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TARGET_DELTA_LOW = 0.45
TARGET_DELTA_HIGH = 0.60
OI_MIN = 500
MAX_SPREAD_PCT = 0.10  # (ask - bid) / mid


def resolve_underlying(rows: list[dict], ticker: str) -> dict | None:
    """Selects the correct US-listed stock row from a search_contracts result.

    Rule (skill-options-directional-builder.md Step 1): exact `symbol` match
    on `ticker`, `country_code == "US"`, section list includes "STK", prefer
    NASDAQ or NYSE over other US exchanges (ARCA, BATS, AMEX, etc.) when more
    than one US listing exists.

    Returns None (never guesses) if there is no exact-symbol US match, or if
    more than one remains after preferring NASDAQ/NYSE (ambiguous -- fail loud
    rather than silently pick the first row).
    """
    us_matches = [
        r for r in rows
        if r.get("symbol") == ticker
        and r.get("country_code") == "US"
        and "STK" in {s.get("security_type") for s in r.get("sections", [])}
    ]
    if not us_matches:
        return None

    preferred = [r for r in us_matches if r.get("exchange") in ("NASDAQ", "NYSE")]
    candidates = preferred if preferred else us_matches

    if len(candidates) != 1:
        return None  # ambiguous -- caller must resolve manually, never guess

    return candidates[0]


@dataclass
class ContractSelection:
    contract: dict
    reason: str


def select_contract(
    chain_options: list[dict],
    direction: Literal["BULLISH", "BEARISH"],
    delta_low: float = TARGET_DELTA_LOW,
    delta_high: float = TARGET_DELTA_HIGH,
    oi_min: int = OI_MIN,
    max_spread_pct: float = MAX_SPREAD_PCT,
) -> ContractSelection | None:
    """Selects the best contract off a single-expiry Tradier chain (option_type,
    strike, bid, ask, open_interest, greeks.delta fields expected per contract,
    matching Tradier's /markets/options/chains response shape).

    Filters: option_type matches direction (call for BULLISH, put for BEARISH),
    |delta| within [delta_low, delta_high], open_interest >= oi_min, spread
    (ask-bid)/mid < max_spread_pct. Among survivors, picks the one whose delta
    is closest to the band midpoint, tie-broken by tighter spread.

    Returns None (stand down) if no contract clears every filter -- never
    relaxes a gate to force a pick. `reason` on failure names which filter
    eliminated everyone, for a PURGE-LOG-style message.
    """
    if direction not in ("BULLISH", "BEARISH"):
        raise ValueError(
            f"select_contract requires direction to be exactly 'BULLISH' or 'BEARISH', got {direction!r} -- "
            f"e.g. a MIXED direction from score_direction() must never reach contract selection; "
            f"the caller must stand down before calling this function, not let it default to a put."
        )
    option_type = "call" if direction == "BULLISH" else "put"
    band_mid = (delta_low + delta_high) / 2

    same_type = [o for o in chain_options if o.get("option_type") == option_type]
    if not same_type:
        return None

    in_band = []
    for o in same_type:
        greeks = o.get("greeks") or {}
        delta = greeks.get("delta")
        if delta is None:
            continue
        if delta_low <= abs(delta) <= delta_high:
            in_band.append(o)
    if not in_band:
        return None

    liquid = []
    for o in in_band:
        bid, ask, oi = o.get("bid"), o.get("ask"), o.get("open_interest")
        if not bid or not ask or bid <= 0 or ask <= 0 or oi is None or oi < oi_min:
            continue
        mid = (bid + ask) / 2
        spread_pct = (ask - bid) / mid  # mid is always >0 here -- bid>0 and ask>0 were
        # already required above, so there's no real "mid falsy" case to guard against
        if spread_pct < max_spread_pct:
            liquid.append((o, spread_pct))
    if not liquid:
        return None

    liquid.sort(key=lambda pair: (abs(abs(pair[0]["greeks"]["delta"]) - band_mid), pair[1]))
    chosen, spread_pct = liquid[0]
    return ContractSelection(
        contract=chosen,
        reason=f"delta {chosen['greeks']['delta']:.3f} in [{delta_low},{delta_high}], "
               f"OI {chosen['open_interest']}, spread {spread_pct*100:.2f}%",
    )
