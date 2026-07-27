"""
Thin wrapper around the IBKR Client Portal REST Gateway.

Assumes the gateway is already running and authenticated (see README.md —
the login step is interactive, via browser, and cannot be automated from here).

Self-signed cert on localhost: verify=False is safe in this specific loopback
context (not a general recommendation), same as IBKR's own documented examples.
"""
from __future__ import annotations

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://localhost:5055/v1/api"
TIMEOUT = 10


def auth_status() -> dict:
    r = requests.get(f"{BASE_URL}/iserver/auth/status", verify=False, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def tickle() -> dict:
    """Keep-alive ping. Call periodically during a long probe run."""
    r = requests.post(f"{BASE_URL}/tickle", verify=False, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def search_conid(symbol: str, sec_type: str = "STK") -> int:
    """Resolve a ticker symbol to its numeric conid. Raises if no exact match found."""
    r = requests.get(
        f"{BASE_URL}/iserver/secdef/search",
        params={"symbol": symbol},
        verify=False,
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    results = r.json()
    for row in results:
        if row.get("symbol", "").upper() == symbol.upper():
            for section in row.get("sections", []):
                if section.get("secType") == sec_type:
                    return int(row["conid"])
    raise ValueError(f"No exact {sec_type} match for {symbol!r} in: {results}")


def secdef_search_full(symbol: str) -> list[dict]:
    """Raw /iserver/secdef/search response -- includes each section's available
    expiry months (for OPT/FOP sections), needed before strikes/info can be called."""
    r = requests.get(
        f"{BASE_URL}/iserver/secdef/search",
        params={"symbol": symbol},
        verify=False,
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def option_months(symbol: str) -> list[str]:
    """Available option expiry months (IBKR's own 'MMMYY' format, e.g. 'AUG26') for
    a symbol's OPT section."""
    results = secdef_search_full(symbol)
    for row in results:
        if row.get("symbol", "").upper() == symbol.upper():
            for section in row.get("sections", []):
                if section.get("secType") == "OPT":
                    return section.get("months", "").split(";")
    raise ValueError(f"No OPT section found for {symbol!r}")


def strikes(underlying_conid: int, month: str) -> dict:
    """GET /iserver/secdef/strikes -- {'call': [...], 'put': [...]} for a given
    underlying conid + expiry month."""
    r = requests.get(
        f"{BASE_URL}/iserver/secdef/strikes",
        params={"conid": underlying_conid, "sectype": "OPT", "month": month},
        verify=False,
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def option_conid(underlying_conid: int, month: str, strike: float, right: str,
                  expiry_date: str | None = None) -> int:
    """GET /iserver/secdef/info -- resolves a specific option contract (by
    underlying conid + expiry month + strike + C/P) to ITS OWN conid, distinct
    from the underlying's. `right` is 'C' or 'P'.

    IMPORTANT (found the hard way, Session 36, Jul 27 2026): a single 'month'
    value (e.g. 'AUG26') returns EVERY expiry falling in that calendar month --
    all weeklies plus the monthly, not one unambiguous contract. Blindly taking
    results[0] silently grabs whichever expiry IBKR lists first (observed: the
    earliest weekly, e.g. Aug 3 instead of the intended Aug 21 monthly) -- a
    real, wrong contract with a plausible-looking price, not an error. Caught
    only by cross-checking the resolved premium against Tradier's own quote for
    the intended expiry and finding them far apart. `expiry_date` (YYYYMMDD)
    is now required in practice: pass it to select the exact maturityDate you
    mean; omitting it keeps the old (unsafe) first-match behavior only for
    backward compatibility, not recommended."""
    r = requests.get(
        f"{BASE_URL}/iserver/secdef/info",
        params={"conid": underlying_conid, "sectype": "OPT", "month": month,
                 "strike": strike, "right": right},
        verify=False,
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    results = r.json()
    if not results:
        raise ValueError(f"No option contract found for conid={underlying_conid} "
                          f"month={month} strike={strike} right={right}")
    if expiry_date is not None:
        matches = [row for row in results if row.get("maturityDate") == expiry_date]
        if not matches:
            available = sorted(row.get("maturityDate") for row in results)
            raise ValueError(
                f"No contract with maturityDate={expiry_date} among {len(results)} "
                f"results for month={month} strike={strike} right={right} -- "
                f"available dates: {available}"
            )
        return int(matches[0]["conid"])
    return int(results[0]["conid"])


def snapshot(conids: list[int], fields: list[str]) -> list[dict]:
    """
    Raw snapshot call. `fields` must be <= 50 items per IBKR's documented limit.
    First call after a fresh conid often returns partial data — IBKR's own docs
    note the snapshot endpoint may need a warm-up call before fields populate.
    """
    if len(fields) > 50:
        raise ValueError(f"{len(fields)} fields requested, API caps at 50 per call")
    r = requests.get(
        f"{BASE_URL}/iserver/marketdata/snapshot",
        params={"conids": ",".join(str(c) for c in conids), "fields": ",".join(fields)},
        verify=False,
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()
