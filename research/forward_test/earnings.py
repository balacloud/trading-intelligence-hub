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

try:
    import zoneinfo
except ImportError:  # not expected on this repo's Python version, kept as a documented fallback
    zoneinfo = None  # type: ignore

HARD_SKIP_DAYS = 14  # TBLA rule: earnings inside this many days is a hard discovery-stage skip
WITHIN_HOLD_DAYS = 35  # matches the 21-35 DTE hold window's outer edge
NEAR_BOUNDARY_DAYS = 7  # Finnhub's observed worst-case error size (Session 34) -- a result
# landing within this many days of either gate line gets flagged for manual
# confirmation rather than trusted silently, regardless of which source produced it.
FINNHUB_LOOKAHEAD_DAYS = 180  # comfortably covers any real DTE window (21-35) plus the
# WITHIN_HOLD ceiling (35) several times over -- earnings further out than this aren't
# relevant to any gate this module feeds.

# Sibling-project paths, resolved the same way build_and_log.py (same directory) already
# does it -- an env-var override plus a path computed relative to this repo's own root, NOT
# a hardcoded absolute path, which would only work on one machine.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # trading-intelligence-hub/
GEMINI_REPO = os.environ.get(
    "OPTIONS_IQ_GEMINI_PATH", os.path.join(os.path.dirname(_REPO_ROOT), "options_iq_gemini")
)
STA_REPO = os.environ.get(
    "SWING_TRADE_ANALYZER_PATH", os.path.join(os.path.dirname(_REPO_ROOT), "swing-trade-analyzer")
)
GEMINI_ENV_PATH = os.path.join(GEMINI_REPO, ".env")
FINNHUB_ENV_PATH = os.path.join(STA_REPO, "backend", ".env")

# Requires a strict "ANSWER: <value>" line from the prompt below -- deliberately not a bare
# date regex. An earlier version grabbed the first YYYY-MM-DD-shaped substring anywhere in
# the response, which would have silently returned the WRONG date if a grounded answer ever
# restated today's date before giving the real one (plausible LLM behavior even against
# explicit instructions) -- a "plausible but wrong" result, worse than returning None.
_ANSWER_RE = re.compile(r"\bANSWER:\s*(\d{4}-\d{2}-\d{2}|UNKNOWN)\b")


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
            f"ticker {ticker}, as of today {today.isoformat()}? Respond with EXACTLY one "
            f"line, no other text before or after it: either 'ANSWER: YYYY-MM-DD' if you "
            f"can confirm a date from a live source, or 'ANSWER: UNKNOWN' if you cannot. "
            f"Do not restate today's date or any other date anywhere else in your reply."
        )
        resp = client.models.generate_content(
            model="gemini-flash-latest", contents=prompt, config=config,
        )
        text = (resp.text or "").strip()
        match = _ANSWER_RE.search(text)
        if not match or match.group(1) == "UNKNOWN":
            return None
        return datetime.strptime(match.group(1), "%Y-%m-%d").date()
    except Exception:
        # Covers 429 quota exhaustion and any other API/network failure --
        # this source being unavailable is an expected, handled case, not
        # something the caller needs to see a traceback for.
        return None


@dataclass
class _FinnhubMatch:
    next_date: date
    exact_symbol_match: bool  # False when Finnhub returned a different listing
    # (e.g. requested "BB", got back "BB.TO") -- same underlying company in the
    # observed case, but nothing guarantees that in general, so the caller is
    # told rather than left to assume an exact match happened.


def fetch_via_finnhub(ticker: str, today: date, api_key: str, lookahead_days: int = FINNHUB_LOOKAHEAD_DAYS) -> _FinnhubMatch | None:
    """Queries Finnhub's per-symbol earnings calendar and returns the nearest
    upcoming date on/after `today`, plus whether the row's own symbol field
    exactly matched what was asked for. Returns None if no upcoming row exists
    or the request fails. See module docstring: this is Finnhub's own
    estimate, not a guaranteed-confirmed date."""
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
            upcoming.append((d, row.get("symbol") == ticker))
    if not upcoming:
        return None
    d, exact = min(upcoming, key=lambda pair: pair[0])
    return _FinnhubMatch(next_date=d, exact_symbol_match=exact)


def get_earnings_status(
    ticker: str,
    today: date | None = None,
    gemini_key: str | None = None,
    finnhub_key: str | None = None,
) -> EarningsResult:
    """Main entry point. Tries Gemini grounding first, falls back to Finnhub,
    and returns UNKNOWN (never a fabricated CLEAR) if both fail. Keys default
    to reading the sibling projects' own .env files if not passed explicitly.

    `today` defaults to the current date in America/New_York, matching this
    project's own wall-clock discipline (CLAUDE_CONTEXT.md) -- NOT bare
    date.today(), which is silent system-local time and has caused real
    errors before in this project when left unanchored."""
    if today is None:
        if zoneinfo is not None:
            today = datetime.now(zoneinfo.ZoneInfo("America/New_York")).date()
        else:
            today = date.today()  # documented fallback only, see the try/import above
    gemini_key = gemini_key or _load_env_key(GEMINI_ENV_PATH, "GEMINI_API_KEY")
    finnhub_key = finnhub_key or _load_env_key(FINNHUB_ENV_PATH, "FINNHUB_API_KEY")

    next_date = None
    source = "unavailable"
    finnhub_exact_match = True

    if gemini_key:
        next_date = fetch_via_gemini(ticker, today, gemini_key)
        if next_date is not None:
            source = "gemini"

    if next_date is None and finnhub_key:
        finnhub_result = fetch_via_finnhub(ticker, today, finnhub_key)
        if finnhub_result is not None:
            next_date = finnhub_result.next_date
            finnhub_exact_match = finnhub_result.exact_symbol_match
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
    if source == "finnhub" and not finnhub_exact_match:
        note = (
            f"Finnhub matched a different listing/symbol than requested ({ticker}) -- "
            f"observed with BB/BB.TO (Session 34), same underlying company there but not "
            f"guaranteed in general. Treat this date as unconfirmed for {ticker} specifically."
        )
    elif source == "finnhub" and near_boundary:
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
