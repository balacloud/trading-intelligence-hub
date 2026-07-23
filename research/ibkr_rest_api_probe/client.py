"""
Thin wrapper around the IBKR Client Portal REST Gateway.

Assumes the gateway is already running and authenticated (see README.md —
the login step is interactive, via browser, and cannot be automated from here).

Self-signed cert on localhost: verify=False is safe in this specific loopback
context (not a general recommendation), same as IBKR's own documented examples.
"""
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
