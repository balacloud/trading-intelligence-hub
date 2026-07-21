"""
Assembles a CENTAUR_SCHEMA_v2-valid payload from data already computed by
sieves.py / technicals.py / the caller's portfolio+earnings context, and
validates it against the schema before returning. See
PLAN_deterministic_pipeline_formalization.md Section 2.4.

This module never fetches or fabricates data. Every field traces to an
explicit argument. Fields the caller doesn't have go in as None -> JSON null,
never a placeholder that reads like confirmation (GOLDEN_RULES: "return null,
not a plausible fake" -- the `iv_rank = ... or "IBKR_VERIFIED"` class of bug
this rule was written about).

iv_hv_ratio units: the schema requires a percentage-style number (71.4, not
0.714). This has already been violated once in this repo
(hive_centaur_payload.json has "iv_hv_ratio": 0.704) -- validate_payload
below plus its test fixture guard against that recurring.
"""
from __future__ import annotations

import json
import os
from typing import Literal

import jsonschema

from sieves import SieveResult

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # trading-intelligence-hub/
GEMINI_REPO = os.environ.get(
    "OPTIONS_IQ_GEMINI_PATH", os.path.join(os.path.dirname(_REPO_ROOT), "options_iq_gemini")
)
SCHEMA_PATH = os.path.join(GEMINI_REPO, "Docs", "CENTAUR_SCHEMA_v2.json")

TARGET_DTE_RANGE = [21, 35]
TARGET_DELTA_RANGE = [0.45, 0.60]

EARNINGS_UNAVAILABLE = "VERIFY — not available from MCP"


def _load_schema() -> dict:
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def build_payload(
    ticker: str,
    direction: Literal["BULLISH", "BEARISH"],
    timestamp: str,
    volatility_regime: Literal["STANDARD", "HIGH-FEAR"],
    vix_live: float | None,
    sieve: SieveResult,
    technical: dict,
    price_last: float,
    trend_label: Literal["UPTREND", "DOWNTREND"],
    price_vs_sma200_pct: float,
    range_52w_pct: float,
    portfolio: dict,
    earnings: dict | None,
    radar_notes: str,
    direction_signal_count: str,
    strike_zone: dict | None = None,
    mcp_chain_candidate: dict | None = None,
    risk_flags: list[str] | None = None,
) -> dict:
    """Assembles one finalist's CENTAUR_SCHEMA_v2 payload.

    `sieve` is a sieves.SieveResult -- its provisional flag maps to
    iv_rank_source honestly (paste_rank vs mcp_percentile_proxy), never
    silently dropped.

    `technical` must already contain: rsi_14, ema_stack, macd_histogram,
    bb_upper, bb_lower, bb_width_pct, ttm_squeeze ("FIRING"/"NOT_FIRING"),
    rvol_mcp, rvol_note, atr_20, nearest_resistance, nearest_support,
    room_to_resistance_pct, room_to_support_pct -- computed by technicals.py,
    this function only assembles, never computes.

    `earnings` is {"next_date": str, "status": str} or None -- if None,
    emits the loud EARNINGS_UNAVAILABLE marker rather than fabricating a
    CLEAR/date this function has no basis for.
    """
    ivr_source_label = "mcp_percentile_proxy" if sieve.provisional else "paste_rank"
    volatility = {
        "iv_rank_52w": sieve.ivr_52w,
        "iv_rank_source": ivr_source_label,
        "ivr_gate": sieve.ivr_gate,
        "iv_hv_ratio": sieve.iv_hv_pct,  # already percentage-style (e.g. 96.23), per schema comment
        "iv_hv_signal": _iv_hv_signal(sieve.iv_hv_pct),
    }

    finalist_entry = {
        "trade_direction": direction,
        "radar_notes": radar_notes,
        "price_last": price_last,
        "price_source": "live_tick",
        "range_52w_pct": range_52w_pct,
        "range_52w_label": (
            "LOWER_THIRD" if range_52w_pct < 25 else "UPPER_THIRD" if range_52w_pct > 75 else "MID_RANGE"
        ),
        "trend_200d_sma": technical.get("sma_200"),
        "trend_label": trend_label,
        "price_vs_sma200_pct": price_vs_sma200_pct,
        "technical": technical,
        "volatility": volatility,
        "portfolio": portfolio,
        "earnings": earnings if earnings is not None else {
            "next_date": EARNINGS_UNAVAILABLE,
            "status": EARNINGS_UNAVAILABLE,
        },
        "risk_flags": risk_flags or [],
        "dual_signal_conflict": False,
    }
    # strike_zone and mcp_chain_candidate are schema-typed as plain "object"
    # (not ["object","null"]) -- they're optional-by-omission, not
    # optional-by-null. Include the key only when a real value exists;
    # setting it to JSON null would itself be a schema violation, not a
    # "return null" case (GOLDEN_RULES' null-vs-fake rule is about faking a
    # *value*, not about which of two valid ways -- omission or null -- a
    # schema uses to represent "not provided").
    if strike_zone is not None:
        finalist_entry["strike_zone"] = strike_zone
    if mcp_chain_candidate is not None:
        finalist_entry["mcp_chain_candidate"] = mcp_chain_candidate

    payload = {
        "timestamp": timestamp,
        "volatility_regime": volatility_regime,
        "direction": direction,
        "direction_source": "AUTO_INFERRED",
        "direction_signal_count": direction_signal_count,
        "target_dte_range": TARGET_DTE_RANGE,
        "target_delta_range": TARGET_DELTA_RANGE,
        "finalists": {ticker: finalist_entry},
    }
    # vix_live is schema-typed as plain "number" (not nullable either) --
    # same reasoning as above.
    if vix_live is not None:
        payload["vix_live"] = vix_live

    return payload


def _iv_hv_signal(iv_hv_pct: float | None) -> str | None:
    if iv_hv_pct is None:
        return None
    if iv_hv_pct < 70:
        return "DEEP_BUYER_EDGE"
    if iv_hv_pct < 100:
        return "BUYER_EDGE"
    if iv_hv_pct <= 115:
        return "NEUTRAL"
    return "SELLER_EDGE"


def validate_payload(payload: dict) -> None:
    """Raises jsonschema.ValidationError on any schema violation. Also
    explicitly re-checks the iv_hv_ratio units convention (percentage-style,
    not a decimal fraction) since the schema's own numeric type doesn't
    distinguish 0.704 from 70.4 -- only the documented convention does, and
    this repo has already shipped that exact mistake once
    (hive_centaur_payload.json)."""
    schema = _load_schema()
    jsonschema.validate(instance=payload, schema=schema)

    for ticker, finalist in payload.get("finalists", {}).items():
        ratio = finalist.get("volatility", {}).get("iv_hv_ratio")
        if ratio is not None and 0 < ratio < 3:
            raise ValueError(
                f"{ticker}: iv_hv_ratio={ratio} looks like a decimal fraction, not a percentage "
                f"(schema requires e.g. 71.4, not 0.714) -- see hive_centaur_payload.json's known mistake"
            )
