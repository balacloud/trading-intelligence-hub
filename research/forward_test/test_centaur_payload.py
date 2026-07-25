"""
Regression tests for centaur_payload.py -- schema validity, and specifically
the iv_hv_ratio units guard. hive_centaur_payload.json (repo root) already
shipped the exact mistake this guard exists to catch: "iv_hv_ratio": 0.704
where the schema requires percentage-style (70.4).
"""
import json
import os

import jsonschema
import pytest

import centaur_payload as cp
from sieves import SieveResult


def _nvda_sieve_result():
    return SieveResult(
        ticker="NVDA", outcome="FINALIST", ivr_52w=40.64, iv_hv_pct=96.23, ivr_gate="PASS",
        trap_flag=False, reason="IVR 40.6% pass, IV/HV 96.2%", provisional=True,
    )


def _nvda_payload():
    return cp.build_payload(
        ticker="NVDA", direction="BULLISH", timestamp="2026-07-21T15:40:50Z",
        volatility_regime="STANDARD", vix_live=17.23,
        sieve=_nvda_sieve_result(),
        technical={
            "rsi_14": 51.7, "ema_stack": "BULLISH", "macd_histogram": "BULLISH",
            "bb_upper": 213.29, "bb_lower": 190.01, "bb_width_pct": 11.55,
            "ttm_squeeze": "NOT_FIRING", "rvol_mcp": None,
            "rvol_note": "not computed this run", "atr_20": 7.16,
            "nearest_resistance": 212.71, "nearest_support": 199.36,
            "room_to_resistance_pct": 2.89, "room_to_support_pct": 3.57,
        },
        price_last=206.74, trend_label="UPTREND", sma_200=192.58, price_vs_sma200_pct=7.29,
        range_52w_pct=58.7,
        portfolio={"existing_position": "NONE", "avg_cost": None, "unrealized_pnl": None,
                  "portfolio_note": "CLEAN_ENTRY"},
        earnings={"next_date": "2026-08-26", "status": "CLEAR - 36 days out"},
        radar_notes="Sole Sieve-1 survivor of 20 CORE names.",
        direction_signal_count="3 bullish / 1 bearish / 5 scored",
    )


def test_build_payload_validates_against_schema():
    payload = _nvda_payload()
    cp.validate_payload(payload)  # raises on failure -- no assertion needed


def test_build_payload_emits_iv_hv_ratio_as_percentage():
    payload = _nvda_payload()
    ratio = payload["finalists"]["NVDA"]["volatility"]["iv_hv_ratio"]
    assert ratio == 96.23
    assert ratio > 3  # sanity: a percentage-style number, not a fraction like 0.9623


def test_validate_payload_catches_hive_style_fraction_mistake():
    """Reproduces the exact bug already shipped in hive_centaur_payload.json:
    iv_hv_ratio recorded as a decimal fraction (0.704) instead of a
    percentage (70.4). validate_payload must reject this, not silently
    accept it."""
    payload = _nvda_payload()
    payload["finalists"]["NVDA"]["volatility"]["iv_hv_ratio"] = 0.704
    with pytest.raises(ValueError, match="decimal fraction"):
        cp.validate_payload(payload)


def test_validate_payload_against_actual_hive_file():
    """Loads the real repo file and confirms validate_payload rejects it.

    hive_centaur_payload.json actually fails schema validation for an
    unrelated, older reason first (vix_live: null against a non-nullable
    number type) -- jsonschema.ValidationError, not our custom ValueError.
    Both are real rejections; this test only asserts *some* validation
    failure fires, since jsonschema checks structural validity before our
    business-rule unit check ever runs. The unit-check-specific behavior is
    covered by test_validate_payload_catches_hive_style_fraction_mistake
    using a structurally-valid fixture."""
    hive_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "hive_centaur_payload.json")
    with open(hive_path) as f:
        hive_payload = json.load(f)
    ratio = hive_payload["finalists"]["HIVE"]["volatility"]["iv_hv_ratio"]
    assert ratio == 0.704  # confirms the bug is still there
    with pytest.raises((ValueError, jsonschema.exceptions.ValidationError)):
        cp.validate_payload(hive_payload)


def test_missing_earnings_emits_loud_unavailable_marker_not_a_fake_clear():
    payload = cp.build_payload(
        ticker="NVDA", direction="BULLISH", timestamp="2026-07-21T15:40:50Z",
        volatility_regime="STANDARD", vix_live=17.23,
        sieve=_nvda_sieve_result(),
        technical={"rsi_14": 51.7},
        price_last=206.74, trend_label="UPTREND", sma_200=192.58, price_vs_sma200_pct=7.29,
        range_52w_pct=58.7,
        portfolio={"existing_position": "NONE", "avg_cost": None, "unrealized_pnl": None,
                  "portfolio_note": "CLEAN_ENTRY"},
        earnings=None,  # caller has no earnings data
        radar_notes="test", direction_signal_count="n/a",
    )
    earnings = payload["finalists"]["NVDA"]["earnings"]
    assert earnings["next_date"] == cp.EARNINGS_UNAVAILABLE
    assert "VERIFY" in earnings["status"]
    cp.validate_payload(payload)  # a minimal technical dict (only rsi_14) must still validate --
    # every other technical field is schema-optional, confirmed by actually validating here,
    # not just asserting on the earnings sub-object.


def test_provisional_ivr_source_maps_to_mcp_percentile_proxy():
    payload = _nvda_payload()
    assert payload["finalists"]["NVDA"]["volatility"]["iv_rank_source"] == "mcp_percentile_proxy"


def test_dual_signal_conflict_defaults_false_but_is_now_a_real_parameter():
    # Regression test for a real Session 34 finding: dual_signal_conflict was
    # hardcoded False in the payload dict with no way to override it, unlike
    # risk_flags, which has always been a real parameter. Confirms the default
    # behavior is unchanged (no caller currently passes a computed value) AND
    # that passing one actually flows through, so the field isn't silently
    # discarded the way it used to be.
    default_payload = _nvda_payload()
    assert default_payload["finalists"]["NVDA"]["dual_signal_conflict"] is False

    conflicted_payload = cp.build_payload(
        ticker="NVDA", direction="BULLISH", timestamp="2026-07-21T15:40:50Z",
        volatility_regime="STANDARD", vix_live=17.23,
        sieve=_nvda_sieve_result(),
        technical={
            "rsi_14": 51.7, "ema_stack": "BULLISH", "macd_histogram": "BULLISH",
            "bb_upper": 213.29, "bb_lower": 190.01, "bb_width_pct": 11.55,
            "ttm_squeeze": "NOT_FIRING", "rvol_mcp": None,
            "rvol_note": "not computed this run", "atr_20": 7.16,
            "nearest_resistance": 212.71, "nearest_support": 199.36,
            "room_to_resistance_pct": 2.89, "room_to_support_pct": 3.57,
        },
        price_last=206.74, trend_label="UPTREND", sma_200=192.58, price_vs_sma200_pct=7.29,
        range_52w_pct=58.7,
        portfolio={"existing_position": "NONE", "avg_cost": None, "unrealized_pnl": None,
                  "portfolio_note": "CLEAN_ENTRY"},
        earnings={"next_date": "2026-08-26", "status": "CLEAR - 36 days out"},
        radar_notes="Sole Sieve-1 survivor of 20 CORE names.",
        direction_signal_count="3 bullish / 1 bearish / 5 scored",
        dual_signal_conflict=True,
    )
    assert conflicted_payload["finalists"]["NVDA"]["dual_signal_conflict"] is True
    cp.validate_payload(conflicted_payload)  # still schema-valid with the field set True


def test_iv_hv_signal_classification():
    assert cp._iv_hv_signal(65) == "DEEP_BUYER_EDGE"
    assert cp._iv_hv_signal(96.23) == "BUYER_EDGE"
    assert cp._iv_hv_signal(110) == "NEUTRAL"
    assert cp._iv_hv_signal(120) == "SELLER_EDGE"
    assert cp._iv_hv_signal(None) is None


def test_iv_hv_signal_exact_boundaries():
    """The four un-tested exact threshold values (70, 100, 115) -- boundary
    behavior was only implicitly covered by nearby round numbers before this,
    never proven at the lines themselves. Matches sieves.py's IVHV_FINALIST_MAX
    convention: 100.0 exactly reads NEUTRAL here too, consistently."""
    assert cp._iv_hv_signal(70.0) == "BUYER_EDGE"       # not DEEP (not < 70)
    assert cp._iv_hv_signal(69.99) == "DEEP_BUYER_EDGE"
    assert cp._iv_hv_signal(100.0) == "NEUTRAL"          # not BUYER_EDGE (not < 100)
    assert cp._iv_hv_signal(99.99) == "BUYER_EDGE"
    assert cp._iv_hv_signal(115.0) == "NEUTRAL"          # inclusive (<= 115)
    assert cp._iv_hv_signal(115.01) == "SELLER_EDGE"


def test_build_payload_rejects_none_range_52w_pct_loudly():
    """Before this fix, range_52w_pct=None crashed with a bare TypeError
    inside the range_52w_label comparison (`None < 25`) instead of a clear
    error -- a real gap found on a critical re-verification pass, not
    exercised by any of today's real-data fixtures (NVDA and UUUU both had
    genuine range data)."""
    with pytest.raises(ValueError, match="directional read"):
        cp.build_payload(
            ticker="NEWCO", direction="BULLISH", timestamp="2026-07-21T15:40:50Z",
            volatility_regime="STANDARD", vix_live=17.23,
            sieve=_nvda_sieve_result(), technical={"rsi_14": 50.0},
            price_last=10.0, trend_label="UPTREND", sma_200=None, price_vs_sma200_pct=None,
            range_52w_pct=None,  # e.g. <200 days of history -- technicals.py genuinely returns None here
            portfolio={"existing_position": "NONE", "avg_cost": None, "unrealized_pnl": None,
                      "portfolio_note": "CLEAN_ENTRY"},
            earnings=None, radar_notes="test", direction_signal_count="n/a",
        )


def test_build_payload_never_emits_null_for_non_nullable_trend_200d_sma():
    """Guards the other half of the same bug: even when sma_200 IS supplied,
    it must land in the schema-non-nullable trend_200d_sma field, not be
    silently dropped via an implicit technical.get('sma_200') lookup (the
    pre-fix implementation)."""
    payload = _nvda_payload()
    assert payload["finalists"]["NVDA"]["trend_200d_sma"] == 192.58
    cp.validate_payload(payload)
