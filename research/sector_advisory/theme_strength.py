"""
Sub-industry relative-strength computation for the theme clusters in
ticker_themes.py that have a proxy ETF (Semis, Memory/Storage, AI Infra/Power,
Nuclear/Uranium, Critical Materials, Gold Miners, Biotech, Financials/Fintech).

Nothing in this ecosystem computes relative strength below the 11 broad GICS
sectors -- STA's own /api/sectors/rotation (see broad_sector_context.py) stops
at that level, which is why a genuinely sector-wide semis selloff (Session 38,
Jul 29 2026: SMH -3.34%, SOXX -3.68%, DRAM -4.69% same day) only shows up there
as "XLK: Weakening" -- true but far too soft to be useful context on its own.
This module fills that gap with new, standalone code, not a port of anyone
else's formula.

RS-Ratio here is a standard, named JdK-style relative-strength ratio (proxy
price / SPY price, indexed to 100 at the start of the lookback window) --
deliberately NOT claiming to replicate STA's own sector-rotation math, which
its own code already documents as "NOT standard de Kempenaer RRG" (flagged
Session 28). Keeping this module's formula plain and standard, and saying so,
avoids repeating that same overclaim in a second place.

Tradier token loading / GET wrapper mirror build_and_log.py's own
load_tradier_token()/tradier_get() exactly, duplicated in miniature rather than
imported -- this script lives in a sibling directory and is meant to stay a
fully standalone, advisory-only tool with zero coupling to the forward-test
pipeline's own modules (Bala's explicit call, Session 38).
"""
from __future__ import annotations

import os
from datetime import date, timedelta

import requests

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEMINI_REPO = os.environ.get(
    "OPTIONS_IQ_GEMINI_PATH", os.path.join(os.path.dirname(REPO_ROOT), "options_iq_gemini")
)
TRADIER_BASE_URL = "https://api.tradier.com/v1"

RS_LOOKBACK_TRADING_DAYS = 126  # ~6mo, matches STA's own /api/sectors/rotation window
RS_MOMENTUM_LOOKBACK_DAYS = 10  # ~2 weeks -- short enough to catch a fast rollover like
# today's semis selloff, long enough not to be pure single-day noise
MIN_USABLE_HISTORY_DAYS = 20  # below this, the RS-ratio series is too short to mean
# anything even as a shortened window -- quadrant comes back None, not a guess

# 126 TRADING days is not 126 CALENDAR days -- a first version of this constant used
# "+30" calendar days as the pad, which under-fetched by ~35 days and made every proxy
# (including decades-old ETFs like XLF/GDX) come back flagged short_history=True. 5
# trading days per 7 calendar days, plus a buffer for US market holidays.
RS_LOOKBACK_CALENDAR_DAYS = int(RS_LOOKBACK_TRADING_DAYS * 7 / 5) + 20


def load_tradier_token() -> str:
    env_path = os.path.join(GEMINI_REPO, ".env")
    if not os.path.exists(env_path):
        raise FileNotFoundError(f"Tradier token source not found: {env_path}")
    with open(env_path) as f:
        for line in f:
            if line.startswith("TRADIER_ACCESS_TOKEN="):
                return line.strip().split("=", 1)[1]
    raise ValueError(f"TRADIER_ACCESS_TOKEN not found in {env_path}")


def tradier_get(path: str, token: str, params: dict) -> dict:
    resp = requests.get(
        f"{TRADIER_BASE_URL}{path}", params=params,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}, timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_daily_closes(ticker: str, token: str, today: date, lookback_days: int = RS_LOOKBACK_CALENDAR_DAYS) -> list[float]:
    """Returns closes oldest-to-newest. lookback_days is calendar days (see
    RS_LOOKBACK_CALENDAR_DAYS's own comment on why this isn't just
    RS_LOOKBACK_TRADING_DAYS). Raises on a ticker with zero history (a typo or
    a genuinely delisted symbol) rather than returning an empty series silently."""
    start = (today - timedelta(days=lookback_days)).isoformat()
    data = tradier_get("/markets/history", token,
                        {"symbol": ticker, "interval": "daily", "start": start, "end": today.isoformat()})
    days = data.get("history", {}).get("day", [])
    if isinstance(days, dict):
        days = [days]
    if not days:
        raise ValueError(f"No Tradier history for {ticker}")
    return [d["close"] for d in days]


def compute_rs_ratio_series(proxy_closes: list[float], spy_closes: list[float]) -> list[float]:
    """proxy/SPY, indexed to 100 at the series' own first point. Aligns on the
    shorter of the two series' lengths (trailing-aligned -- both series' most
    recent close is index -1) since a young proxy (e.g. DRAM, launched Apr
    2026) can have materially less history than SPY.

    Known, accepted limitation (Pass 3 review, Session 38): alignment is by
    position, not by each day's actual date -- Tradier's /markets/history
    response does carry a date per day, but only closes are kept here. If one
    series ever has a data gap the other doesn't (rare for SPY/liquid sector
    ETFs specifically), positional trailing-alignment would silently shift
    dates by one day from that point backward rather than catching the
    mismatch. Not fixed: a full date-keyed join would add real complexity for
    an advisory-only panel where the failure mode is a slightly-off quadrant
    read, not a wrong trade -- worth revisiting only if this proxy set grows
    to include less liquid names where gaps are more likely."""
    n = min(len(proxy_closes), len(spy_closes))
    if n == 0:
        raise ValueError("empty closes series -- cannot compute RS-ratio")
    proxy_tail = proxy_closes[-n:]
    spy_tail = spy_closes[-n:]
    raw_ratio = [p / s for p, s in zip(proxy_tail, spy_tail)]
    base = raw_ratio[0]
    return [100.0 * r / base for r in raw_ratio]


def compute_quadrant(rs_ratio_series: list[float], momentum_lookback: int = RS_MOMENTUM_LOOKBACK_DAYS) -> dict:
    """Standard JdK-style quadrant from an RS-ratio series:
      RS-Ratio >= 100 and momentum > 0  -> Leading
      RS-Ratio >= 100 and momentum <= 0 -> Weakening
      RS-Ratio < 100  and momentum > 0  -> Improving
      RS-Ratio < 100  and momentum <= 0 -> Lagging
    momentum = pct change of the RS-ratio's last value vs `momentum_lookback`
    trading days prior. Returns quadrant=None (never a guessed label) when the
    series is shorter than MIN_USABLE_HISTORY_DAYS -- flags short_history=True
    whenever the full RS_LOOKBACK_TRADING_DAYS window wasn't available, even if
    a shortened read was still possible, so a thin-history read (e.g. DRAM) is
    never presented with the same confidence as a full 6mo one."""
    n = len(rs_ratio_series)
    short_history = n < RS_LOOKBACK_TRADING_DAYS
    if n < MIN_USABLE_HISTORY_DAYS:
        return {"quadrant": None, "rs_ratio": None, "momentum_pct": None,
                "short_history": short_history, "usable_days": n}

    rs_ratio = rs_ratio_series[-1]
    lookback = min(momentum_lookback, n - 1)
    prior = rs_ratio_series[-1 - lookback]
    momentum_pct = 100.0 * (rs_ratio - prior) / prior if prior else 0.0

    if rs_ratio >= 100:
        quadrant = "Leading" if momentum_pct > 0 else "Weakening"
    else:
        quadrant = "Improving" if momentum_pct > 0 else "Lagging"

    return {"quadrant": quadrant, "rs_ratio": round(rs_ratio, 2), "momentum_pct": round(momentum_pct, 2),
            "short_history": short_history, "usable_days": n}


def compute_cluster_strength(proxy: str, token: str, today: date, spy_closes: list[float] | None = None) -> dict:
    """Full pipeline for one proxy ETF: fetch its closes, fetch SPY's (unless
    already fetched by the caller -- SPY is shared across every cluster, worth
    fetching once), compute the RS-ratio series, classify the quadrant. Never
    raises on a data gap for the proxy itself (a young/thin ETF) -- returns
    quadrant=None with an `error` string instead, so one bad proxy can't take
    down the whole report."""
    try:
        proxy_closes = fetch_daily_closes(proxy, token, today)
        if spy_closes is None:
            spy_closes = fetch_daily_closes("SPY", token, today)
        rs_series = compute_rs_ratio_series(proxy_closes, spy_closes)
        result = compute_quadrant(rs_series)
        result["proxy"] = proxy
        result["error"] = None
        return result
    except Exception as exc:
        return {"proxy": proxy, "quadrant": None, "rs_ratio": None, "momentum_pct": None,
                "short_history": None, "usable_days": None, "error": str(exc)}
