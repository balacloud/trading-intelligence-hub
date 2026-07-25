"""
Earnings-date lookup for the TBLA gate (the 0-35 day earnings-in-hold check
skill-options-ibkr-radar.md and skill-options-scanner.md both apply per
finalist). Replaces the ad hoc WebSearch every prior session ran by hand.

Two sources, tried in order, each with a real, tested characteristic this
docstring records rather than presenting either as simply "a date":

1. Gemini API search grounding (GEMINI_API_KEY, options_iq_gemini/.env) --
   most likely to return the company's own confirmed date, since it's a live
   grounded search rather than a pre-aggregated estimate. BUT: the account's
   grounding quota is a real, separate cap from plain generation -- confirmed
   Session 34 by a live test that hit 429 RESOURCE_EXHAUSTED on the very
   first grounded call, even though plain (non-grounded) calls on the same
   key worked fine. May be unavailable on any given day regardless of key
   validity -- this module treats that as an expected, handled case, not an
   error to surface.

2. Finnhub calendar/earnings (FINNHUB_API_KEY, swing-trade-analyzer's own
   backend/.env -- reused from a sibling project, not duplicated). Reliable
   and tested working (Session 34), but the returned date is Finnhub's own
   estimate, not necessarily the company's confirmed date: cross-checked
   live against 5 real tickers the same session -- 3 matched a live web
   search exactly (BB, WEX, KMX/GS), but 2 were off by ~7 days (PRAX:
   Finnhub Aug 10 vs. confirmed Aug 3; CELC: Finnhub Aug 6 vs. confirmed
   Aug 13). Never trust a Finnhub date blindly when it lands near a gate
   boundary -- see NEAR_BOUNDARY_DAYS below, which exists specifically
   because of this observed error size.

Both sources return None on failure -- never a fabricated date (GOLDEN_RULES:
"return null, not a plausible fake"). If both fail, the result's status is
"UNKNOWN", the same honest sentinel skill-options-ibkr-radar.md already uses
when earnings can't be verified -- never silently treated as CLEAR.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta

import requests

HARD_SKIP_DAYS = 14  # TBLA rule: earnings inside this many days is a hard discovery-stage skip
WITHIN_HOLD_DAYS = 35  # matches the 21-35 DTE hold window's outer edge
NEAR_BOUNDARY_DAYS = 7  # Finnhub's observed worst-case error size (Session 34) -- a result
# landing within this many days of either gate line gets flagged for manual
# confirmation rather than trusted silently, regardless of which source produced it.

GEMINI_ENV_PATH = "/Users/balajik/projects/options_iq_gemini/.env"
FINNHUB_ENV_PATH = "/Users/balajik/projects/swing-trade-analyzer/backend/.env"

_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")


@dataclass
class EarningsResult:
    ticker: str
    next_date: date | None
    source: str  # "gemini" / "finnhub" / "unavailable"
    days_out: int | None
    status: str  # "HARD_SKIP" / "WITHIN_HOLD" / "CLEAR" / "UNKNOWN"
    near_boundary: bool  # True if days_out is within NEAR_BOUNDARY_DAYS of either gate line
    note: str


def _load_env_key(path: str, var_name: str) -> str | None:
    if not os.path.exists(path):
        return None
    with open(path) as f:
        for line in f:
            if line.startswith(f"{var_name}="):
                val = line.strip().split("=", 1)[1]
                return val or None
    return None


def classify(days_out: int) -> tuple[str, bool]:
    """Returns (status, near_boundary). Mirrors the existing TBLA convention:
    <14 days = hard skip, 14-35 = within hold (flag, not exclude), >35 = clear."""
    near = abs(days_out - HARD_SKIP_DAYS) <= NEAR_BOUNDARY_DAYS or abs(days_out - WITHIN_HOLD_DAYS) <= NEAR_BOUNDARY_DAYS
    if days_out < HARD_SKIP_DAYS:
        return "HARD_SKIP", near
    if days_out <= WITHIN_HOLD_DAYS:
        return "WITHIN_HOLD", near
    return "CLEAR", near


def fetch_via_gemini(ticker: str, today: date, api_key: str) -> date | None:
    """Asks Gemini's grounded search for the ticker's next earnings date.
    Returns None on any failure (quota, parse failure, no clear answer) --
    never guesses. Requires the google-genai SDK; import is local so this
    module doesn't hard-fail to import if that package isn't installed."""
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return None

    try:
        client = genai.Client(api_key=api_key)
        grounding_tool = types.Tool(google_search=types.GoogleSearch())
        config = types.GenerateContentConfig(tools=[grounding_tool])
        prompt = (
            f"What is the next confirmed earnings report date for the US-listed stock "
            f"ticker {ticker}, as of today {today.isoformat()}? Reply with ONLY the date "
            f"in YYYY-MM-DD format if you can confirm one from a live source, or the "
            f"single word UNKNOWN if you cannot confirm one. No other text."
        )
        resp = client.models.generate_content(
            model="gemini-flash-latest", contents=prompt, config=config,
        )
        text = (resp.text or "").strip()
        match = _DATE_RE.search(text)
        if not match:
            return None
        return datetime.strptime(match.group(1), "%Y-%m-%d").date()
    except Exception:
        # Covers 429 quota exhaustion and any other API/network failure --
        # this source being unavailable is an expected, handled case, not
        # something the caller needs to see a traceback for.
        return None


def fetch_via_finnhub(ticker: str, today: date, api_key: str, lookahead_days: int = 180) -> date | None:
    """Queries Finnhub's per-symbol earnings calendar and returns the nearest
    upcoming date on/after `today`. Returns None if no upcoming row exists or
    the request fails. See module docstring: this is Finnhub's own estimate,
    not a guaranteed-confirmed date."""
    try:
        resp = requests.get(
            "https://finnhub.io/api/v1/calendar/earnings",
            params={
                "symbol": ticker, "token": api_key,
                "from": today.isoformat(),
                "to": (today + timedelta(days=lookahead_days)).isoformat(),
            },
            timeout=15,
        )
        resp.raise_for_status()
        rows = resp.json().get("earningsCalendar", [])
    except Exception:
        return None

    upcoming = []
    for row in rows:
        try:
            d = datetime.strptime(row["date"], "%Y-%m-%d").date()
        except (KeyError, ValueError):
            continue
        if d >= today:
            upcoming.append(d)
    return min(upcoming) if upcoming else None


def get_earnings_status(
    ticker: str,
    today: date | None = None,
    gemini_key: str | None = None,
    finnhub_key: str | None = None,
) -> EarningsResult:
    """Main entry point. Tries Gemini grounding first, falls back to Finnhub,
    and returns UNKNOWN (never a fabricated CLEAR) if both fail. Keys default
    to reading the sibling projects' own .env files if not passed explicitly."""
    today = today or date.today()
    gemini_key = gemini_key or _load_env_key(GEMINI_ENV_PATH, "GEMINI_API_KEY")
    finnhub_key = finnhub_key or _load_env_key(FINNHUB_ENV_PATH, "FINNHUB_API_KEY")

    next_date = None
    source = "unavailable"

    if gemini_key:
        next_date = fetch_via_gemini(ticker, today, gemini_key)
        if next_date is not None:
            source = "gemini"

    if next_date is None and finnhub_key:
        next_date = fetch_via_finnhub(ticker, today, finnhub_key)
        if next_date is not None:
            source = "finnhub"

    if next_date is None:
        return EarningsResult(
            ticker=ticker, next_date=None, source="unavailable", days_out=None,
            status="UNKNOWN", near_boundary=False,
            note="Both Gemini grounding and Finnhub failed or returned no upcoming date -- "
                 "verify manually via web search before treating this name as CLEAR.",
        )

    days_out = (next_date - today).days
    status, near_boundary = classify(days_out)
    note = ""
    if source == "finnhub" and near_boundary:
        note = (
            f"Finnhub estimate lands within {NEAR_BOUNDARY_DAYS} days of a gate boundary "
            f"({status}) -- Session 34 observed up to 7-day errors on names like this "
            f"(PRAX, CELC). Confirm via web search before excluding or clearing on this "
            f"date alone."
        )
    elif source == "finnhub":
        note = "Finnhub estimate, not independently confirmed -- generally reliable but not guaranteed exact."
    elif source == "gemini":
        note = "Gemini grounded search result."

    return EarningsResult(
        ticker=ticker, next_date=next_date, source=source, days_out=days_out,
        status=status, near_boundary=near_boundary, note=note,
    )
