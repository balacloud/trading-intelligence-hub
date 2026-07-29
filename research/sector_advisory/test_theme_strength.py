import pytest

from theme_strength import (
    MIN_USABLE_HISTORY_DAYS,
    RS_LOOKBACK_TRADING_DAYS,
    compute_quadrant,
    compute_rs_ratio_series,
)


def _flat_series(n, value=100.0):
    return [value] * n


def test_rs_ratio_series_indexed_to_100_at_start():
    proxy = [50.0, 51.0, 52.0]
    spy = [500.0, 500.0, 500.0]
    series = compute_rs_ratio_series(proxy, spy)
    assert series[0] == pytest.approx(100.0)
    assert series[-1] > series[0]  # proxy outpaced SPY -> ratio rose


def test_rs_ratio_series_aligns_on_shorter_series_trailing():
    proxy = [10.0, 10.0, 10.0]  # only 3 points (a young ETF)
    spy = [100.0] * 200  # much longer history
    series = compute_rs_ratio_series(proxy, spy)
    assert len(series) == 3


def test_rs_ratio_series_raises_on_empty_input():
    with pytest.raises(ValueError):
        compute_rs_ratio_series([], [])


def test_quadrant_leading_when_ratio_above_100_and_rising():
    series = _flat_series(RS_LOOKBACK_TRADING_DAYS, 100.0)
    series[-11:] = [95, 96, 97, 98, 99, 100, 102, 104, 106, 108, 110]
    result = compute_quadrant(series)
    assert result["quadrant"] == "Leading"
    assert result["rs_ratio"] == pytest.approx(110.0)
    assert not result["short_history"]


def test_quadrant_weakening_when_ratio_above_100_and_falling():
    series = _flat_series(RS_LOOKBACK_TRADING_DAYS, 100.0)
    series[-11:] = [112, 111, 110, 109, 108, 107, 106, 105, 104, 103, 102]
    result = compute_quadrant(series)
    assert result["quadrant"] == "Weakening"


def test_quadrant_improving_when_ratio_below_100_and_rising():
    series = _flat_series(RS_LOOKBACK_TRADING_DAYS, 100.0)
    series[-11:] = [80, 81, 82, 84, 86, 88, 90, 92, 94, 96, 98]
    result = compute_quadrant(series)
    assert result["quadrant"] == "Improving"


def test_quadrant_lagging_when_ratio_below_100_and_falling():
    series = _flat_series(RS_LOOKBACK_TRADING_DAYS, 100.0)
    series[-11:] = [98, 96, 94, 92, 90, 88, 86, 84, 82, 80, 78]
    result = compute_quadrant(series)
    assert result["quadrant"] == "Lagging"


def test_quadrant_boundary_exactly_100_counts_as_leading_or_weakening_not_improving_lagging():
    # rs_ratio == 100 exactly must fall on the >=100 side, never the <100 side
    series = _flat_series(RS_LOOKBACK_TRADING_DAYS, 100.0)
    series[-11:] = [95, 96, 97, 98, 99, 99.5, 100, 100, 100, 100, 100]
    result = compute_quadrant(series)
    assert result["quadrant"] in ("Leading", "Weakening")


def test_quadrant_none_when_series_shorter_than_minimum():
    series = _flat_series(MIN_USABLE_HISTORY_DAYS - 1, 100.0)
    result = compute_quadrant(series)
    assert result["quadrant"] is None
    assert result["rs_ratio"] is None


def test_quadrant_short_history_flag_true_below_full_lookback_but_still_computed():
    # DRAM-like case: enough history to compute a real read (>= MIN_USABLE_HISTORY_DAYS)
    # but short of the full RS_LOOKBACK_TRADING_DAYS window -- must still classify,
    # just flagged as thinner evidence.
    n = MIN_USABLE_HISTORY_DAYS + 15
    series = _flat_series(n, 100.0)
    series[-11:] = [95, 96, 97, 98, 99, 100, 102, 104, 106, 108, 110]
    result = compute_quadrant(series)
    assert result["quadrant"] == "Leading"
    assert result["short_history"] is True
