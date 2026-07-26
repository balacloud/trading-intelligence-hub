"""
Regression tests for two real bugs found in build_and_log.py's own direction-
scoring logic during Session 34's three-pass code review, plus (Session 35)
coverage for the earnings-gate wiring added the same session. Not a full test
suite for the module -- SKILL_CONVERSION_SCOREBOARD.md already flags an open
question about whether this module should be updated to call the newer
sieves/technicals/contracts/centaur_payload modules directly or be retired;
these tests cover what was actually broken/added, not the whole surface.
"""
from datetime import date
from unittest.mock import patch

import build_and_log
import earnings
from build_and_log import build_position, score_direction


def test_score_direction_denominator_excludes_unscored_signals():
    # Regression test: a clean, unanimous 2-0 bullish vote among the signals
    # that were actually evaluated used to be reported as MIXED, because the
    # old filter (`v is not None or k in signals`) was tautologically true for
    # every key already in the dict and filtered nothing -- total_scored
    # counted the 3 genuinely-unscored signals as if they'd been evaluated.
    signals = {"SMA200": "bullish", "YTD": "bullish", "RANGE_52W": None,
               "EMA_STACK": None, "TODAY_PC": None}
    direction, bullish, bearish, total_scored = score_direction(signals)
    assert direction == "BULLISH"
    assert total_scored == 2  # only the 2 signals with a real value, not all 5


def test_score_direction_genuine_tie_among_scored_signals_is_mixed():
    signals = {"SMA200": "bullish", "YTD": "bearish", "RANGE_52W": None,
               "EMA_STACK": None, "TODAY_PC": None}
    direction, bullish, bearish, total_scored = score_direction(signals)
    assert direction == "MIXED"
    assert total_scored == 2


def test_score_direction_all_unscored_is_mixed_not_a_crash():
    # total_scored == 0 would previously have divided by zero once the
    # denominator was fixed to use the real (possibly-empty) scored count --
    # matches technicals.py's own score_direction, which already guards this.
    signals = {"RANGE_52W": None, "EMA_STACK": None, "TODAY_PC": None}
    direction, bullish, bearish, total_scored = score_direction(signals)
    assert direction == "MIXED"
    assert total_scored == 0


def _fake_tradier_get(path, token, params):
    if path == "/markets/options/expirations":
        return {"expirations": {"date": ["2026-08-15"]}}
    if path == "/markets/options/chains":
        return {"options": {"option": []}}
    raise AssertionError(f"unexpected tradier_get call in this fixture: {path}")


_BULLISH_DIRECTION_INFO = {
    "price": 100.0, "signals": {"SMA200": "bullish", "YTD": "bullish", "EMA_STACK": "bullish",
                                 "RANGE_52W": None, "TODAY_PC": None},
    "price_vs_sma200_pct": 5.0, "ytd_change_pct": 10.0, "range_52w_pct": 70.0, "trend_200d": "UPTREND",
}


def test_build_position_earnings_hard_skip_returns_before_any_chain_call():
    # Session 35: earnings.py wired into the TBLA gate. A HARD_SKIP result must stop
    # build_position before it spends a live Tradier chain call on a name about to be
    # rejected anyway -- proven here by making that specific call raise if reached.
    row = {"ticker": "TEST", "group": "CORE"}
    hard_skip = earnings.EarningsResult(
        ticker="TEST", next_date=date(2026, 8, 1), source="finnhub", days_out=6,
        status="HARD_SKIP", near_boundary=False,
        note="Finnhub matched a different listing/symbol than requested",
    )

    def _chain_call_must_not_happen(path, token, params):
        if path == "/markets/options/chains":
            raise AssertionError("chain lookup must not run once the earnings gate hard-skips")
        return _fake_tradier_get(path, token, params)

    with patch.object(build_and_log, "compute_direction", return_value=dict(_BULLISH_DIRECTION_INFO)), \
         patch.object(build_and_log, "pick_expiry", return_value=("2026-08-15", 28, False)), \
         patch.object(build_and_log, "add_today_pc_ratio"), \
         patch.object(build_and_log, "tradier_get", side_effect=_chain_call_must_not_happen), \
         patch.object(earnings, "get_earnings_status", return_value=hard_skip):
        result = build_position(row, token="tok", today=date(2026, 7, 26), existing_open=[])

    assert result["outcome"] == "EARNINGS_HARD_SKIP"
    assert "2026-08-01" in result["note"]
    # Regression: EarningsResult.note (the specific caveat text -- near-boundary /
    # cross-listing-mismatch warnings) must survive into the outcome, not be silently
    # dropped -- it exists specifically so a human reviewing the CSV can catch a bad skip.
    assert "different listing/symbol" in result["note"]


def test_build_position_earnings_within_hold_flags_but_proceeds():
    # WITHIN_HOLD (14-35 days out) must NOT block -- it flags and proceeds, matching
    # this project's existing "flag, don't silently block on an uncertain/soft signal"
    # convention for VIX regime. Proceeding all the way to a real (mocked-empty) chain
    # call and landing on NO_CONTRACT -- not EARNINGS_HARD_SKIP -- is the proof.
    row = {"ticker": "TEST", "group": "CORE"}
    within_hold = earnings.EarningsResult(
        ticker="TEST", next_date=date(2026, 8, 20), source="gemini", days_out=25,
        status="WITHIN_HOLD", near_boundary=False, note="test fixture",
    )

    with patch.object(build_and_log, "compute_direction", return_value=dict(_BULLISH_DIRECTION_INFO)), \
         patch.object(build_and_log, "pick_expiry", return_value=("2026-08-15", 28, False)), \
         patch.object(build_and_log, "add_today_pc_ratio"), \
         patch.object(build_and_log, "tradier_get", side_effect=_fake_tradier_get), \
         patch.object(earnings, "get_earnings_status", return_value=within_hold):
        result = build_position(row, token="tok", today=date(2026, 7, 26), existing_open=[])

    assert result["outcome"] == "NO_CONTRACT"


def test_build_position_earnings_unknown_also_proceeds_not_blocked():
    # Both earnings.py sources failing yields UNKNOWN, never a fabricated CLEAR --
    # but per this module's own docstring, UNKNOWN reflects a real data gap, not a
    # disagreement worth stopping on, so it must also proceed rather than hard-skip.
    row = {"ticker": "TEST", "group": "CORE"}
    unknown = earnings.EarningsResult(
        ticker="TEST", next_date=None, source="unavailable", days_out=None,
        status="UNKNOWN", near_boundary=False, note="test fixture: both sources failed",
    )

    with patch.object(build_and_log, "compute_direction", return_value=dict(_BULLISH_DIRECTION_INFO)), \
         patch.object(build_and_log, "pick_expiry", return_value=("2026-08-15", 28, False)), \
         patch.object(build_and_log, "add_today_pc_ratio"), \
         patch.object(build_and_log, "tradier_get", side_effect=_fake_tradier_get), \
         patch.object(earnings, "get_earnings_status", return_value=unknown):
        result = build_position(row, token="tok", today=date(2026, 7, 26), existing_open=[])

    assert result["outcome"] == "NO_CONTRACT"
