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

A VIX row (any ticker literally "VIX"), if present, is pulled out of the returned
candidate rows and reported separately as regime info (STANDARD/HIGH-FEAR at the
VIX<=25 line, per skill-options-scanner.md's own Phase 0) -- it is never itself
sieved/gated/built as if it were a tradeable candidate.

Column-count ambiguity (PATH A only): PATH A's P/E column is sometimes blank
(loss-making names), which paste-copies as a wider whitespace gap rather than
an explicit placeholder -- unlike PATH B, which always uses an explicit "-"
for a missing cell. A naive whitespace split cannot distinguish "P/E blank"
from "P/E present" by gap width alone, so PATH A rows are parsed from BOTH
ends: the last 7 fields (open/high/low/52wHigh/52wLow/bid/ask) are always
present and anchor the right side; the first 11 fields anchor the left side;
P/E is whatever's left in between (0 or 1 tokens). A token count outside
{18, 19} for a PATH A row is a genuine parse failure, not absorbed silently.

Left-side field count changed 9 -> 11 (Jul 31, 2026, Session 40): `Spec_Compliant_Screener`
gained two live display columns the same session its Average Volume ($) and Current Option
Volume filters were found to have an unfixable IBKR platform ceiling-clamp bug and were
removed -- Average Option Volume (new first field, ahead of Opt. Implied Volatility %) and
Put/Call Volume (inserted between Market Cap and Last). Both are optional context, same
treatment PATH B already gives Put/Call Volume: captured into `extra`, never gated on.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

TICKER_LINE_RE = re.compile(r"^[A-Z]{1,6}$")
# Dual-class share tickers (e.g. "BF A" / "BF B" for Brown-Forman) paste from IBKR with a
# space between root and class letter -- TICKER_LINE_RE alone never matches them, and
# because the following NAME/DATA lines don't match it either, the whole 3-line row used to
# be skipped silently (all three lines just fall through the `else: i += 1` branch), never
# reaching a ticker or a ParseError. Found live (Jul 29, 2026) when a real PATH A paste
# containing "BF A"/"BF B" screened 48 rows out of 50 pasted with no error and no purge-log
# entry for either. Tradier's own symbol convention for these is root/class with a slash
# (confirmed live: "BF/B" resolves, "BF B"/"BF.B"/"BF-B"/"BFB" all return unmatched_symbols)
# -- normalized at extraction time so every downstream Tradier call already uses it.
DUAL_CLASS_TICKER_LINE_RE = re.compile(r"^[A-Z]{1,6} [A-Z]{1,2}$")
_MULTI_WS_RE = re.compile(r"\s+")

# ASCII hyphen-minus, en dash, em dash, minus sign, horizontal bar -- IBKR's own paste has been
# observed using an em dash (U+2014) specifically for PATH B's missing-cell placeholder ("—"),
# not the plain ASCII hyphen this module originally checked for. A token made ENTIRELY of these
# characters (any length/mix) is treated as an explicit "no value" marker; real numbers always
# contain a digit, so this can't false-positive on a genuine negative value like "-0.34".
_EMPTY_MARKER_CHARS = set("-–—−―")

PATH_A_HEADER_MARKERS = ("Opt. Implied Volatility %", "Market Cap")
PATH_B_HEADER_MARKERS = ("Price/EMA(50)", "Price/EMA(200)")

# Both row parsers below trust a FIXED column position once the token count matches --
# they never re-derive which token means what from the header itself. That's fine as
# long as the screener's actual column order never changes without the count also
# changing, but that assumption is exactly what broke once already for HUB_CORE (Session
# 39: PATH B column layout drifted, caught only because the count also happened to
# change) and is a live, non-theoretical risk again after Session 40 (Jul 31, 2026)
# added two new PATH A columns -- `Spec_Compliant_Screener` changed its own displayed
# column set twice in that single session. A same-count, reordered header would
# otherwise misparse SILENTLY (a value landing in the wrong field, no error raised) --
# the "plausible but wrong answer instead of failing loud" failure class GOLDEN_RULES.md's
# Pass 3 review exists to catch. This validation converts that into a fail-loud ParseError
# instead, without touching the deliberately-permissive chrome-skipping logic in
# _split_triples (whose job is different: tolerate arbitrary noise text around the real
# header, not validate the real header's own content).
# Deliberately NOT \s{2,} alone: a real copy-paste from a browser/TWS grid may use a
# single tab character between columns rather than multiple spaces (the data-row
# parser's own _MULTI_WS_RE already tolerates this for exactly that reason). A single
# tab must split; a single plain space must NOT (it's what separates the words inside
# a multi-word column name like "Average Option Volume"). Every existing test fixture
# in this codebase happens to use multi-space mocking, which would have masked this
# gap -- caught in Pass 2 review (Session 40, Jul 31 2026), not Pass 1.
_HEADER_COLUMN_SPLIT_RE = re.compile(r"\t+|[ ]{2,}")

PATH_A_EXPECTED_COLUMNS = (
    "Average Option Volume", "Opt. Implied Volatility %", "Implied Vol./Hist. Vol %",
    "52 Week IV Rank", "Market Cap", "Put/Call Volume", "Last", "Change", "Change %",
    "Volume", "Average Volume", "P/E", "Open", "High", "Low",
    "52 Week High", "52 Week Low", "Bid Price", "Ask Price",
)

PATH_B_EXPECTED_COLUMNS = (
    "Last", "Change %", "Bid", "Ask", "Volume", "Opt. Imp. Vol. Change", "Price/EMA(50)",
    "Opt. Volume Change %", "Put/Call Volume", "52 Week Low", "52 Week High", "Price/EMA(200)",
    "Opt. Volume", "Option Open Interest", "Hist. Vol. Close %", "Opt. Implied Volatility %",
    "Implied Vol./Hist. Vol %", "52 Week IV Rank", "Underlying Price",
)


def _validate_header_order(lines: list[str], fmt: str, markers: tuple[str, ...]) -> None:
    """Finds the real header line (the one containing every marker for this format --
    there should be exactly one in a well-formed paste) and checks its column order
    against the expected sequence. Raises ParseError naming the exact mismatch on any
    difference -- missing column, extra column, or reorder -- rather than silently
    trusting the fixed-position row parsers to still be right."""
    header_lines = [ln for ln in lines if all(m in ln for m in markers)]
    if not header_lines:
        return  # format was already detected via substring match elsewhere in the
        # text (e.g. markers split across two lines) -- nothing to validate against here,
        # not this function's job to second-guess _detect_format's own result.
    header_line = header_lines[0]
    actual = tuple(t for t in _HEADER_COLUMN_SPLIT_RE.split(header_line.strip()) if t)
    if actual and actual[0] == "Instrument":
        actual = actual[1:]
    expected = PATH_A_EXPECTED_COLUMNS if fmt == "PATH_A" else PATH_B_EXPECTED_COLUMNS
    if actual != expected:
        raise ParseError(
            f"{fmt} header column order doesn't match what the row parser expects -- "
            f"refusing to parse under a possibly-wrong field mapping. "
            f"Expected: {list(expected)}. Got: {list(actual)}."
        )

PATH_A_FIELD_COUNT_NO_PE = 18
PATH_A_FIELD_COUNT_WITH_PE = 19
PATH_B_FIELD_COUNT = 19

# skill-options-scanner.md's own Phase 0 convention: add a VIX row to the same watchlist
# being pasted (any format), read its Last price, classify STANDARD/HIGH-FEAR. This module
# extracts that row out of the candidate list rather than leaving it to be mis-treated as a
# tradeable ticker by sieves.py -- VIX has no market cap, dollar volume, or real per-name
# option-chain fields in the sense the rest of this module's fields mean.
VIX_TICKER = "VIX"
VIX_HIGH_FEAR_THRESHOLD = 25.0  # VIX <= 25 -> STANDARD, > 25 -> HIGH-FEAR (matches
# skill-options-ibkr-radar.md / skill-options-scanner.md Phase 0, unchanged since Session 13)


@dataclass
class VixInfo:
    level: float
    regime: str  # "STANDARD" / "HIGH-FEAR"


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
    if t == "" or set(t) <= _EMPTY_MARKER_CHARS:
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
        is_dual_class = DUAL_CLASS_TICKER_LINE_RE.match(lines[i])
        if TICKER_LINE_RE.match(lines[i]) or is_dual_class:
            if i + 2 >= len(lines):
                raise ParseError(
                    f"ticker line {lines[i]!r} at line {i} has no following name+data lines "
                    f"-- paste looks truncated"
                )
            ticker = lines[i].replace(" ", "/") if is_dual_class else lines[i]
            name, data = lines[i + 1], lines[i + 2]
            # A malformed/truncated paste (e.g. a row missing its data line entirely) would
            # otherwise misalign silently into a cascading, confusing field-count error several
            # calls downstream. Checking the data line is actually data-shaped here gives a
            # specific, immediate error instead -- "yell, with specifics" applied at the point
            # of the actual problem, not wherever it happens to blow up later.
            if not data or data[0] not in "+0123456789" and data[0] not in _EMPTY_MARKER_CHARS:
                raise ParseError(
                    f"ticker line {ticker!r} at line {i}: expected a data line at position "
                    f"{i + 2} (starting with a digit or a placeholder dash) but got {data!r} -- "
                    f"paste looks misaligned, possibly a row missing its name or data line"
                )
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
    left = tokens[:11]
    pe = tokens[11] if has_pe else None
    right = tokens[11 + (1 if has_pe else 0):]
    avg_opt_vol, opt_iv, iv_hv, ivr, mktcap, pc_vol, last, change, change_pct, volume, avg_vol = left
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
            # New Session 40 (Jul 31, 2026) columns -- context only, never gated on,
            # same treatment PATH B already gives its own put_call_volume field.
            "average_option_volume": _num(avg_opt_vol), "put_call_volume": _num(pc_vol),
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


def parse_paste(text: str, expected_format: str | None = None) -> tuple[str, list[PasteRow], VixInfo | None]:
    """Parses a raw paste. Returns (format, rows, vix). `expected_format` (if given,
    "PATH_A" or "PATH_B") is cross-checked against auto-detection and raises
    on mismatch -- lets a caller who knows what they pasted catch the case
    where the paste is actually the other format.

    `rows` never includes a VIX row -- it's pulled out into `vix` (a VixInfo, or None if
    no VIX row was present, or present but its own Last field didn't parse to a number).
    Never fabricated: an unusable VIX row yields `vix=None`, not a guessed regime, same
    as every other "can't determine this" case in this module."""
    detected = _detect_format(text)
    if expected_format is not None and expected_format != detected:
        raise ParseError(
            f"caller expected {expected_format} but the paste's own headers detected {detected} -- "
            f"format mismatch, refusing to parse under the wrong rules"
        )

    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]  # drop blank lines only -- never drop a non-blank line silently

    markers = PATH_A_HEADER_MARKERS if detected == "PATH_A" else PATH_B_HEADER_MARKERS
    _validate_header_order(lines, detected, markers)

    triples = _split_triples(lines)

    parser = _parse_path_a_row if detected == "PATH_A" else _parse_path_b_row
    all_rows = [parser(ticker, name, data) for ticker, name, data in triples]

    vix_rows = [r for r in all_rows if r.ticker.upper() == VIX_TICKER]
    if len(vix_rows) > 1:
        raise ParseError(
            f"found {len(vix_rows)} VIX rows in one paste -- ambiguous, expected at most 1"
        )
    rows = [r for r in all_rows if r.ticker.upper() != VIX_TICKER]

    vix = None
    if vix_rows:
        vix_last = vix_rows[0].extra.get("last")
        if vix_last is not None:
            regime = "STANDARD" if vix_last <= VIX_HIGH_FEAR_THRESHOLD else "HIGH-FEAR"
            vix = VixInfo(level=vix_last, regime=regime)

    return detected, rows, vix
