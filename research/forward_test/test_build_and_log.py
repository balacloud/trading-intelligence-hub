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


def test_fetch_vix_regime_standard_below_threshold():
    with patch.object(build_and_log, "tradier_get",
                       return_value={"quotes": {"quote": {"last": 19.31}}}):
        level, regime = build_and_log.fetch_vix_regime(token="tok")
    assert level == 19.31
    assert regime == "STANDARD"


def test_fetch_vix_regime_high_fear_above_threshold():
    with patch.object(build_and_log, "tradier_get",
                       return_value={"quotes": {"quote": {"last": 31.4}}}):
        level, regime = build_and_log.fetch_vix_regime(token="tok")
    assert level == 31.4
    assert regime == "HIGH-FEAR"


def test_fetch_vix_regime_exactly_25_is_standard():
    # Matches paste_parser.py's own VIX_HIGH_FEAR_THRESHOLD convention: <=25 -> STANDARD.
    with patch.object(build_and_log, "tradier_get",
                       return_value={"quotes": {"quote": {"last": 25.0}}}):
        level, regime = build_and_log.fetch_vix_regime(token="tok")
    assert regime == "STANDARD"


def test_fetch_vix_regime_failure_returns_unknown_not_fabricated():
    # Real failures observed in this project: Tradier down, unmatched_symbols (e.g. the
    # '$VIX.X'/'VIX.X' variants tried live Jul 27 2026 before landing on plain 'VIX').
    with patch.object(build_and_log, "tradier_get", side_effect=Exception("connection error")):
        level, regime = build_and_log.fetch_vix_regime(token="tok")
    assert level is None
    assert regime == "UNKNOWN"

    with patch.object(build_and_log, "tradier_get",
                       return_value={"quotes": {"unmatched_symbols": {"symbol": "VIX"}}}):
        level, regime = build_and_log.fetch_vix_regime(token="tok")
    assert level is None
    assert regime == "UNKNOWN"


def test_compute_builds_overrides_row_vix_regime_with_live_fetch():
    # The whole point of this fix (Bala, Session 36, Jul 27 2026): a row's vix_regime
    # must not depend on whether the day's Scan paste happened to carry a VIX row --
    # compute_builds should overwrite it with a live Tradier read regardless of what
    # the input CSV says, unless the live fetch itself failed.
    rows = [{"ticker": "TEST", "group": "SURVIVOR", "vix_regime": "UNKNOWN"}]
    with patch.object(build_and_log, "load_tradier_token", return_value="tok"), \
         patch.object(build_and_log, "fetch_existing_open", return_value=[]), \
         patch.object(build_and_log, "fetch_vix_regime", return_value=(19.31, "STANDARD")), \
         patch.object(build_and_log, "build_position", return_value={"outcome": "NO_CONTRACT"}) as mock_build:
        build_and_log.compute_builds(rows, today=date(2026, 7, 27))

    passed_row = mock_build.call_args[0][0]
    assert passed_row["vix_regime"] == "STANDARD"


def test_compute_builds_keeps_row_value_when_live_fetch_fails():
    rows = [{"ticker": "TEST", "group": "SURVIVOR", "vix_regime": "STANDARD"}]
    with patch.object(build_and_log, "load_tradier_token", return_value="tok"), \
         patch.object(build_and_log, "fetch_existing_open", return_value=[]), \
         patch.object(build_and_log, "fetch_vix_regime", return_value=(None, "UNKNOWN")), \
         patch.object(build_and_log, "build_position", return_value={"outcome": "NO_CONTRACT"}) as mock_build:
        build_and_log.compute_builds(rows, today=date(2026, 7, 27))

    passed_row = mock_build.call_args[0][0]
    # A live-fetch failure must never overwrite a real value with "UNKNOWN" --
    # falls back to whatever the row already had (which may itself be UNKNOWN).
    assert passed_row["vix_regime"] == "STANDARD"


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


def test_format_entry_greeks_with_real_values():
    eg = {"delta": 0.53, "gamma": 0.018, "theta": -0.188, "vega": 0.206, "mid_iv": 0.428}
    s = build_and_log.format_entry_greeks(eg)
    assert "delta 0.53" in s
    assert "gamma 0.018" in s
    assert "theta -0.188" in s
    assert "vega 0.206" in s
    assert "mid IV 42.8%" in s


def test_format_entry_greeks_all_none_says_unavailable():
    eg = {"delta": None, "gamma": None, "theta": None, "vega": None, "mid_iv": None}
    s = build_and_log.format_entry_greeks(eg)
    assert "unavailable" in s
    assert "N/A" not in s  # the unavailable-model sentence, not a per-field N/A soup


def test_format_entry_greeks_partial_missing_shows_na_per_field():
    # Tradier can return a partial greeks object -- never fabricate the missing pieces.
    eg = {"delta": 0.53, "gamma": None, "theta": None, "vega": None, "mid_iv": None}
    s = build_and_log.format_entry_greeks(eg)
    assert "delta 0.53" in s
    assert "gamma N/A" in s
    assert "mid IV N/A" in s


def _fake_tradier_get_with_chain(chain_response):
    def _inner(path, token, params):
        if path == "/markets/options/expirations":
            return {"expirations": {"date": ["2026-08-15"]}}
        if path == "/markets/options/chains":
            return chain_response
        raise AssertionError(f"unexpected tradier_get call in this fixture: {path}")
    return _inner


def test_build_position_captures_entry_greeks_from_chain():
    # Session 36 (Jul 27 2026): greeks=true is now requested on the entry-contract chain
    # call, and the chosen contract's Greeks/IV must survive into the BUILT result --
    # this was previously discarded (requested as "false") even though Tradier returns
    # them in the same response at no extra call cost.
    chain_response = {"options": {"option": [{
        "symbol": "TEST260815C00100000", "strike": 100.0, "option_type": "call",
        "bid": 5.0, "ask": 5.2,
        "greeks": {"delta": 0.53, "gamma": 0.018, "theta": -0.188, "vega": 0.206, "mid_iv": 0.428},
    }]}}
    row = {"ticker": "TEST", "group": "CORE"}

    with patch.object(build_and_log, "compute_direction", return_value=dict(_BULLISH_DIRECTION_INFO)), \
         patch.object(build_and_log, "pick_expiry", return_value=("2026-08-15", 28, False)), \
         patch.object(build_and_log, "add_today_pc_ratio"), \
         patch.object(build_and_log, "tradier_get", side_effect=_fake_tradier_get_with_chain(chain_response)), \
         patch.object(earnings, "get_earnings_status",
                      return_value=earnings.EarningsResult(
                          ticker="TEST", next_date=None, source="unavailable", days_out=None,
                          status="UNKNOWN", near_boundary=False, note="")):
        result = build_position(row, token="tok", today=date(2026, 7, 26), existing_open=[])

    assert result["outcome"] == "BUILT"
    assert result["entry_greeks"] == {"delta": 0.53, "gamma": 0.018, "theta": -0.188,
                                       "vega": 0.206, "mid_iv": 0.428}


def test_build_position_null_greeks_model_does_not_crash():
    # Tradier can return greeks=null on the option row even when greeks=true was
    # requested (observed on thin/no-model contracts, per this hub's own live probe
    # notes) -- must not crash, and every value must come through as None, not a
    # fabricated 0.0 that would read as a real (and misleadingly delta-neutral) Greek.
    chain_response = {"options": {"option": [{
        "symbol": "TEST260815C00100000", "strike": 100.0, "option_type": "call",
        "bid": 5.0, "ask": 5.2, "greeks": None,
    }]}}
    row = {"ticker": "TEST", "group": "CORE"}

    with patch.object(build_and_log, "compute_direction", return_value=dict(_BULLISH_DIRECTION_INFO)), \
         patch.object(build_and_log, "pick_expiry", return_value=("2026-08-15", 28, False)), \
         patch.object(build_and_log, "add_today_pc_ratio"), \
         patch.object(build_and_log, "tradier_get", side_effect=_fake_tradier_get_with_chain(chain_response)), \
         patch.object(earnings, "get_earnings_status",
                      return_value=earnings.EarningsResult(
                          ticker="TEST", next_date=None, source="unavailable", days_out=None,
                          status="UNKNOWN", near_boundary=False, note="")):
        result = build_position(row, token="tok", today=date(2026, 7, 26), existing_open=[])

    assert result["outcome"] == "BUILT"
    assert result["entry_greeks"] == {"delta": None, "gamma": None, "theta": None,
                                       "vega": None, "mid_iv": None}
