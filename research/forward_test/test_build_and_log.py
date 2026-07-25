"""
Regression tests for two real bugs found in build_and_log.py's own direction-
scoring logic during Session 34's three-pass code review. Not a full test
suite for the module -- SKILL_CONVERSION_SCOREBOARD.md already flags an open
question about whether this module should be updated to call the newer
sieves/technicals/contracts/centaur_payload modules directly or be retired;
these tests cover what was actually broken, not the whole surface.
"""
from build_and_log import score_direction


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
