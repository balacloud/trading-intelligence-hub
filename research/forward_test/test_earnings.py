from datetime import date, timedelta
from unittest.mock import patch

import pytest

from earnings import EarningsResult, classify, get_earnings_status

TODAY = date(2026, 7, 25)


def test_classify_hard_skip():
    status, near = classify(9)
    assert status == "HARD_SKIP"
    assert near is True  # 9 is within 7 of the 14-day line


def test_classify_within_hold_not_near_boundary():
    status, near = classify(25)
    assert status == "WITHIN_HOLD"
    assert near is False  # 25 is >7 from both 14 and 35


def test_classify_within_hold_near_upper_boundary():
    status, near = classify(30)
    assert status == "WITHIN_HOLD"
    assert near is True  # 30 is within 7 of the 35-day line


def test_classify_clear():
    status, near = classify(60)
    assert status == "CLEAR"
    assert near is False


def test_classify_exact_hard_skip_line():
    status, near = classify(14)
    assert status == "WITHIN_HOLD"  # 14 itself is NOT a hard skip -- <14 is
    assert near is True


def test_get_earnings_status_both_sources_fail_returns_unknown():
    with patch("earnings.fetch_via_gemini", return_value=None), \
         patch("earnings.fetch_via_finnhub", return_value=None):
        result = get_earnings_status("ZZZZ", today=TODAY, gemini_key="fake", finnhub_key="fake")
    assert result.status == "UNKNOWN"
    assert result.next_date is None
    assert result.source == "unavailable"
    assert "verify manually" in result.note


def test_get_earnings_status_gemini_success_skips_finnhub():
    gemini_date = TODAY + timedelta(days=20)
    with patch("earnings.fetch_via_gemini", return_value=gemini_date) as mock_gemini, \
         patch("earnings.fetch_via_finnhub") as mock_finnhub:
        result = get_earnings_status("AAPL", today=TODAY, gemini_key="fake", finnhub_key="fake")
    assert result.source == "gemini"
    assert result.days_out == 20
    assert result.status == "WITHIN_HOLD"
    mock_finnhub.assert_not_called()


def test_get_earnings_status_falls_back_to_finnhub_when_gemini_fails():
    # 10 days out is within NEAR_BOUNDARY_DAYS(7) of the 14-day HARD_SKIP line
    # (|10-14|=4<=7) -- a Finnhub-sized error (observed up to 7 days, Session 34)
    # could plausibly flip this across the gate, so it should carry the caveat.
    finnhub_date = TODAY + timedelta(days=10)
    with patch("earnings.fetch_via_gemini", return_value=None), \
         patch("earnings.fetch_via_finnhub", return_value=finnhub_date):
        result = get_earnings_status("BB", today=TODAY, gemini_key="fake", finnhub_key="fake")
    assert result.source == "finnhub"
    assert result.days_out == 10
    assert result.status == "HARD_SKIP"
    assert result.near_boundary is True
    assert "Session 34" in result.note  # near-boundary Finnhub caveat should fire


def test_get_earnings_status_finnhub_far_from_boundary_shorter_note():
    finnhub_date = TODAY + timedelta(days=60)
    with patch("earnings.fetch_via_gemini", return_value=None), \
         patch("earnings.fetch_via_finnhub", return_value=finnhub_date):
        result = get_earnings_status("WEX", today=TODAY, gemini_key="fake", finnhub_key="fake")
    assert result.source == "finnhub"
    assert result.status == "CLEAR"
    assert result.near_boundary is False
    assert "not independently confirmed" in result.note


def test_no_keys_returns_unknown_without_network_calls():
    # Passing None alone isn't enough to prove "no credentials" -- the real
    # get_earnings_status falls back to reading the sibling .env files when a
    # key arg is None (the intended production default), which would hit live
    # Finnhub/Gemini here since those files genuinely exist in this repo's
    # environment. Mock the loader itself to get true isolation.
    with patch("earnings._load_env_key", return_value=None):
        result = get_earnings_status("XYZ", today=TODAY)
    assert result.status == "UNKNOWN"
    assert result.source == "unavailable"
    assert result.next_date is None
