"""
Technical indicators + direction vote, as pure functions over OHLCV data.

Formalizes logic that was previously computed ad hoc in disposable /tmp scripts
each time a Directional Builder read was needed (see PLAN_deterministic_pipeline_formalization.md
Section 2.3). Every function here takes explicit lists/values in and returns an
explicit typed result out -- none of them fetch their own data. The caller (an
LLM with live IBKR/Tradier access, or build_and_log.py's Tradier-only fetch path)
is responsible for supplying OHLCV.

RSI and ATR use true Wilder smoothing (recursive), not a flat N-period average.
This is a deliberate correctness fix over the ad hoc scratch scripts used earlier
in Session 30 (which used a flat average) -- see the Plan doc Section 6, item 1.
Values computed this way will NOT match those earlier scratch-script numbers
exactly; that's expected, not a bug.

Missing/insufficient data returns None, never a partial-window value silently
labeled as the full-period indicator (GOLDEN_RULES.md: "return null, not a
plausible fake").
"""
from __future__ import annotations

from typing import Literal, Optional

Signal = Optional[Literal["bullish", "bearish"]]


def sma(vals: list[float], period: int) -> float | None:
    if len(vals) < period:
        return None
    return sum(vals[-period:]) / period


def ema_series(vals: list[float], period: int) -> list[float] | None:
    """Full EMA series (seeded from vals[0]), so callers needing MACD's
    intermediate values or a squeeze midline can reuse this directly."""
    if not vals:
        return None
    k = 2 / (period + 1)
    e = [vals[0]]
    for v in vals[1:]:
        e.append(v * k + e[-1] * (1 - k))
    return e


def rsi_wilder(close: list[float], period: int = 14) -> float | None:
    """True Wilder-smoothed RSI. Returns None if fewer than `period` deltas
    are available."""
    if len(close) < period + 1:
        return None
    deltas = [close[i] - close[i - 1] for i in range(1, len(close))]
    gains = [max(d, 0.0) for d in deltas]
    losses = [max(-d, 0.0) for d in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def macd(
    close: list[float], fast: int = 12, slow: int = 26, signal: int = 9
) -> tuple[float, float, float] | None:
    """Returns (macd_line, signal_line, histogram). None if insufficient data."""
    if len(close) < slow + signal:
        return None
    ema_fast = ema_series(close, fast)
    ema_slow = ema_series(close, slow)
    macd_line_series = [f - s for f, s in zip(ema_fast, ema_slow)]
    signal_series = ema_series(macd_line_series, signal)
    macd_line = macd_line_series[-1]
    signal_line = signal_series[-1]
    return macd_line, signal_line, macd_line - signal_line


def atr_wilder(high: list[float], low: list[float], close: list[float], period: int = 14) -> float | None:
    """True Wilder-smoothed ATR. Returns None if fewer than `period` true
    ranges are available."""
    if len(close) < period + 1:
        return None
    trs = []
    for i in range(1, len(close)):
        trs.append(max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1])))

    atr = sum(trs[:period]) / period
    for i in range(period, len(trs)):
        atr = (atr * (period - 1) + trs[i]) / period
    return atr


def bollinger(close: list[float], period: int = 20, k: float = 2.0) -> tuple[float, float, float] | None:
    """Returns (upper, lower, width_pct). width_pct = (upper-lower)/sma*100."""
    if len(close) < period:
        return None
    mid = sma(close, period)
    window = close[-period:]
    variance = sum((x - mid) ** 2 for x in window) / period
    sd = variance**0.5
    upper, lower = mid + k * sd, mid - k * sd
    width_pct = (upper - lower) / mid * 100
    return upper, lower, width_pct


def keltner(
    close: list[float], high: list[float], low: list[float], period: int = 20, mult: float = 1.5
) -> tuple[float, float] | None:
    """Returns (upper, lower). Midline is EMA(period) of close; width is
    mult * Wilder ATR(period)."""
    ema_mid_series = ema_series(close, period)
    atr_val = atr_wilder(high, low, close, period)
    if ema_mid_series is None or atr_val is None:
        return None
    mid = ema_mid_series[-1]
    return mid + mult * atr_val, mid - mult * atr_val


def ttm_squeeze(close: list[float], high: list[float], low: list[float]) -> bool | None:
    """True when Bollinger Bands sit entirely inside Keltner Channels --
    volatility compression, the TTM Squeeze condition. Maps directly to the
    CENTAUR_SCHEMA_v2 `ttm_squeeze` enum: True -> "FIRING" (squeeze active,
    a breakout is being coiled), False -> "NOT_FIRING". No inversion needed
    at the call site."""
    bb = bollinger(close)
    kc = keltner(close, high, low)
    if bb is None or kc is None:
        return None
    bb_upper, bb_lower, _ = bb
    kc_upper, kc_lower = kc
    return bb_upper < kc_upper and bb_lower > kc_lower


def pivot_levels(
    high: list[float], low: list[float], price: float, lookback: int = 50, window: int = 3
) -> tuple[float | None, float | None]:
    """Returns (nearest_resistance, nearest_support) from fractal pivots in
    the trailing `lookback` bars. A pivot high/low is a local extreme over
    +/- `window` bars. Resistance must be strictly above price; support must
    be strictly below price -- never returns a mislabeled level on the wrong
    side (the ACN room_to_support sign-bug class of error)."""
    h = high[-lookback:]
    l = low[-lookback:]
    piv_highs, piv_lows = [], []
    for i in range(window, len(h) - window):
        if h[i] == max(h[i - window : i + window + 1]):
            piv_highs.append(h[i])
        if l[i] == min(l[i - window : i + window + 1]):
            piv_lows.append(l[i])
    resistances = sorted(p for p in piv_highs if p > price)
    supports = sorted((p for p in piv_lows if p < price), reverse=True)
    nearest_resistance = resistances[0] if resistances else None
    nearest_support = supports[0] if supports else None
    return nearest_resistance, nearest_support


def range_52w_pct(price: float, high_52w: float, low_52w: float) -> float | None:
    if high_52w == low_52w:
        return None
    return (price - low_52w) / (high_52w - low_52w) * 100


def ytd_change_pct(close: list[float], dates: list[str], as_of_year: int) -> float | None:
    """dates are ISO date strings (YYYY-MM-DD or full ISO timestamps) aligned
    1:1 with close. baseline = last close strictly before Jan 1 of as_of_year.
    Returns None if no such baseline exists in the series."""
    boundary = f"{as_of_year}-01-01"
    prior = [c for c, d in zip(close, dates) if d[:10] < boundary]
    if not prior:
        return None
    baseline = prior[-1]
    return (close[-1] - baseline) / baseline * 100


def compute_signals(
    price: float,
    sma200: float | None,
    ema9: float | None,
    ema21: float | None,
    ema50: float | None,
    range_pct: float | None,
) -> dict[str, Signal]:
    """Bundles the vote-eligible signals (mirrors skill-options-directional-builder.md
    Step 6's signal set, minus the P/C-ratio signals that have no local-only
    source). Each entry is 'bullish' / 'bearish' / None (unscored)."""
    signals: dict[str, Signal] = {}

    signals["SMA200"] = None if sma200 is None else ("bullish" if price > sma200 else "bearish")

    if ema9 is None or ema21 is None or ema50 is None:
        signals["EMA_STACK"] = None
    elif ema9 > ema21 > ema50:
        signals["EMA_STACK"] = "bullish"
    elif ema9 < ema21 < ema50:
        signals["EMA_STACK"] = "bearish"
    else:
        signals["EMA_STACK"] = None

    if range_pct is None:
        signals["RANGE_52W"] = None
    elif range_pct > 60:
        signals["RANGE_52W"] = "bullish"
    elif range_pct < 40:
        signals["RANGE_52W"] = "bearish"
    else:
        signals["RANGE_52W"] = None

    return signals


def score_direction(signals: dict[str, Signal]) -> tuple[str, int, int, int]:
    """Canonical strict-majority vote. Denominator is non-None (actually
    scored) signals only -- fixes the build_and_log.py:172 bug where the
    denominator counted unscored (None) signals too, matching
    skill-options-directional-builder.md Step 6's explicit requirement.

    Returns (direction, bullish_count, bearish_count, scored_count) where
    direction is "BULLISH" / "BEARISH" / "MIXED".
    """
    scored = {k: v for k, v in signals.items() if v is not None}
    total_scored = len(scored)
    bullish = sum(1 for v in scored.values() if v == "bullish")
    bearish = sum(1 for v in scored.values() if v == "bearish")
    if total_scored == 0:
        return "MIXED", 0, 0, 0
    if bullish > bearish and bullish > total_scored / 2:
        return "BULLISH", bullish, bearish, total_scored
    if bearish > bullish and bearish > total_scored / 2:
        return "BEARISH", bullish, bearish, total_scored
    return "MIXED", bullish, bearish, total_scored
