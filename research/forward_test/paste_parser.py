"""
Parses a raw IBKR screener/watchlist paste (copy-pasted table text) into
structured PasteRow objects the Sieve stack can consume.

Two known formats, auto-detected from the header row:
  PATH A -- "Spec_Compliant_Screener" dynamic Market Scanner paste. Per-name
    Market Cap and dollar volume are present, so Gates A/B/C can all be
    independently verified from the paste itself (see OPTIONS_SIEVE_SPEC.md).
  PATH B -- HUB_CORE / HUB_EXTENDED curated watchlist paste. No Market Cap or
    dollar-volume columns -- Gates A/C are pre-satisfied by curation per
    protocol, only Sieve 1 / Gate B / Sieve 2b run off the paste directly.

Fail-loud philosophy (matching sieves.py/technicals.py/contracts.py): a row
that doesn't match the expected shape for its detected format raises
ParseError immediately, naming the ticker and what was wrong. This module
never guesses a missing field's value, never drops a row silently, and never
falls back to a default when the paste's structure doesn't match what it
claims to be. If the format can't be confidently detected at all, parsing the
whole paste raises rather than picking a format and hoping.

Column-count ambiguity (PATH A only): PATH A's P/E column is sometimes blank
(loss-making names), which paste-copies as a wider whitespace gap rather than
an explicit placeholder -- unlike PATH B, which always uses an explicit "-"
for a missing cell. A naive whitespace split cannot distinguish "P/E blank"
from "P/E present" by gap width alone, so PATH A rows are parsed from BOTH
ends: the last 7 fields (open/high/low/52wHigh/52wLow/bid/ask) are always
present and anchor the right side; the first 9 fields anchor the left side;
P/E is whatever's left in between (0 or 1 tokens). A token count outside
{16, 17} for a PATH A row is a genuine parse failure, not absorbed silently.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

TICKER_LINE_RE = re.compile(r"^[A-Z]{1,6}$")
_MULTI_WS_RE = re.compile(r"\s+")

PATH_A_HEADER_MARKERS = ("Opt. Implied Volatility %", "Market Cap")
PATH_B_HEADER_MARKERS = ("Price/EMA(50)", "Price/EMA(200)")

PATH_A_FIELD_COUNT_NO_PE = 16
PATH_A_FIELD_COUNT_WITH_PE = 17
PATH_B_FIELD_COUNT = 19


class ParseError(ValueError):
    """Raised on any paste that doesn't match its detected (or claimed)
    format -- never caught and silently downgraded to a skip by this module.
    The caller decides what to do with a raised ParseError; this module's
    job ends at 'yell, with specifics'."""


@dataclass
class PasteRow:
    ticker: str
    company_name: str
    ivr_52w: float | None
    iv_hv_pct: float | None
    opt_implied_vol_pct: float | None
    bid: float | None
    ask: float | None
    market_cap_usd: float | None = None  # PATH A only
    dollar_vol_usd: float | None = None  # PATH A only -- last * average_volume (Gate C's own formula)
    extra: dict = field(default_factory=dict)  # every other parsed column, format-specific, never dropped


def _num(token: str) -> float | None:
    """Parses a single numeric token. '-' / '--' -> None (never a fabricated
    zero). Strips %, leading +, and B/M/K magnitude suffixes."""
    t = token.strip()
    if t in ("-", "--", ""):
        return None
    sign = 1.0
    if t.startswith("+"):
        t = t[1:]
    elif t.startswith("-"):
        sign = -1.0
        t = t[1:]
    if t.endswith("%"):
        t = t[:-1]
    mult = 1.0
    if t and t[-1] in "BMK":
        mult = {"B": 1e9, "M": 1e6, "K": 1e3}[t[-1]]
        t = t[:-1]
    try:
        return sign * float(t) * mult
    except ValueError:
        raise ParseError(f"could not parse numeric token {token!r}")


def _detect_format(text: str) -> str:
    has_a = all(m in text for m in PATH_A_HEADER_MARKERS)
    has_b = all(m in text for m in PATH_B_HEADER_MARKERS)
    if has_a and not has_b:
        return "PATH_A"
    if has_b and not has_a:
        return "PATH_B"
    raise ParseError(
        f"could not confidently detect paste format (PATH A markers present={has_a}, "
        f"PATH B markers present={has_b}) -- expected exactly one to match, refusing to guess"
    )


def _split_triples(lines: list[str]) -> list[tuple[str, str, str]]:
    """Scans for the repeating (TICKER, NAME, DATA) pattern -- a line that is
    1-6 uppercase letters only, followed by a name line, followed by a data
    line. This naturally skips headers/timestamps/UI chrome without needing
    to hardcode their exact text, since only a real ticker-shaped line ever
    triggers row consumption. A ticker line found with no following data line
    (truncated paste) raises rather than silently dropping the partial row."""
    triples = []
    i = 0
    while i < len(lines):
        if TICKER_LINE_RE.match(lines[i]):
            if i + 2 >= len(lines):
                raise ParseError(
                    f"ticker line {lines[i]!r} at line {i} has no following name+data lines "
                    f"-- paste looks truncated"
                )
            ticker, name, data = lines[i], lines[i + 1], lines[i + 2]
            triples.append((ticker, name, data))
            i += 3
        else:
            i += 1
    if not triples:
        raise ParseError("no (TICKER, NAME, DATA) row triples found in paste at all")
    return triples


def _parse_path_a_row(ticker: str, name: str, data: str) -> PasteRow:
    tokens = _MULTI_WS_RE.split(data.strip())
    if len(tokens) not in (PATH_A_FIELD_COUNT_NO_PE, PATH_A_FIELD_COUNT_WITH_PE):
        raise ParseError(
            f"{ticker}: PATH A data row has {len(tokens)} fields, expected "
            f"{PATH_A_FIELD_COUNT_NO_PE} (no P/E) or {PATH_A_FIELD_COUNT_WITH_PE} (with P/E) -- "
            f"raw tokens: {tokens}"
        )
    has_pe = len(tokens) == PATH_A_FIELD_COUNT_WITH_PE
    left = tokens[:9]
    pe = tokens[9] if has_pe else None
    right = tokens[9 + (1 if has_pe else 0):]
    opt_iv, iv_hv, ivr, mktcap, last, change, change_pct, volume, avg_vol = left
    open_, high, low, w52h, w52l, bid, ask = right

    last_v = _num(last)
    avg_vol_v = _num(avg_vol)
    dollar_vol = last_v * avg_vol_v if last_v is not None and avg_vol_v is not None else None

    return PasteRow(
        ticker=ticker, company_name=name,
        ivr_52w=_num(ivr), iv_hv_pct=_num(iv_hv), opt_implied_vol_pct=_num(opt_iv),
        bid=_num(bid), ask=_num(ask),
        market_cap_usd=_num(mktcap), dollar_vol_usd=dollar_vol,
        extra={
            "pe": _num(pe) if pe is not None else None,
            "last": last_v, "change": _num(change), "change_pct": _num(change_pct),
            "volume": _num(volume), "average_volume": avg_vol_v,
            "open": _num(open_), "high": _num(high), "low": _num(low),
            "week52_high": _num(w52h), "week52_low": _num(w52l),
        },
    )


def _parse_path_b_row(ticker: str, name: str, data: str) -> PasteRow:
    tokens = _MULTI_WS_RE.split(data.strip())
    if len(tokens) != PATH_B_FIELD_COUNT:
        raise ParseError(
            f"{ticker}: PATH B data row has {len(tokens)} fields, expected {PATH_B_FIELD_COUNT} -- "
            f"raw tokens: {tokens}"
        )
    (last, change_pct, bid, ask, volume, opt_imp_vol_change, price_ema50, opt_vol_change_pct,
     put_call_vol, w52l, w52h, price_ema200, opt_volume, opt_oi, hist_vol_close, opt_iv,
     iv_hv, ivr, underlying_price) = tokens

    return PasteRow(
        ticker=ticker, company_name=name,
        ivr_52w=_num(ivr), iv_hv_pct=_num(iv_hv), opt_implied_vol_pct=_num(opt_iv),
        bid=_num(bid), ask=_num(ask),
        market_cap_usd=None, dollar_vol_usd=None,  # PATH B: Gates A/C pre-satisfied by curation, not in the paste
        extra={
            "last": _num(last), "change_pct": _num(change_pct), "volume": _num(volume),
            "opt_imp_vol_change": _num(opt_imp_vol_change), "price_ema50_pct": _num(price_ema50),
            "opt_vol_change_pct": _num(opt_vol_change_pct), "put_call_volume": _num(put_call_vol),
            "week52_low": _num(w52l), "week52_high": _num(w52h), "price_ema200_pct": _num(price_ema200),
            "opt_volume": _num(opt_volume), "opt_open_interest": _num(opt_oi),
            "hist_vol_close_pct": _num(hist_vol_close), "underlying_price": _num(underlying_price),
        },
    )


def parse_paste(text: str, expected_format: str | None = None) -> tuple[str, list[PasteRow]]:
    """Parses a raw paste. Returns (format, rows). `expected_format` (if given,
    "PATH_A" or "PATH_B") is cross-checked against auto-detection and raises
    on mismatch -- lets a caller who knows what they pasted catch the case
    where the paste is actually the other format."""
    detected = _detect_format(text)
    if expected_format is not None and expected_format != detected:
        raise ParseError(
            f"caller expected {expected_format} but the paste's own headers detected {detected} -- "
            f"format mismatch, refusing to parse under the wrong rules"
        )

    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]  # drop blank lines only -- never drop a non-blank line silently
    triples = _split_triples(lines)

    parser = _parse_path_a_row if detected == "PATH_A" else _parse_path_b_row
    rows = [parser(ticker, name, data) for ticker, name, data in triples]
    return detected, rows
