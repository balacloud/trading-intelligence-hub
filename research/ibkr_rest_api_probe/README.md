# IBKR Client Portal REST API — IV Rank Field Probe

> Pet project, isolated from the forward test. Doesn't touch `forward_test_log.csv`, doesn't
> touch any live watchlist, doesn't change any skill. Safe to run, safe to abandon.

> **Done.** See `FINDINGS.md` for the full research log (method, evidence, false-positive
> analysis) or **`IBKR_REST_API_REFERENCE.md` for the portable, project-agnostic version** —
> written so `swing-trade-analyzer` or `options_iq_gemini` can reuse the confirmed field IDs and
> setup gotchas directly, without needing this hub's own context. Bottom line: 11 of ~14
> watchlist columns are available via REST, confirmed against real pasted data. `52 Week IV
> Rank` itself is not — a clean, cross-ticker-verified negative, independently corroborated —
> not an inconclusive one. Everything below is the original setup/method; kept for reference.

## The question this answers

Does IBKR's Client Portal **REST** API expose a field matching the real TWS/Client Portal
watchlist column **"52 Week IV Rank"** — or does the API only ever expose
`implied_volatility_percentile` (a *different*, already-confirmed-divergent metric)?

**Why this matters:** the whole reason `skill-options-scanner.md` moved to watchlist-paste
mode (v3.0, Session 30) instead of screening via IBKR MCP calls is that MCP's
`implied_volatility_percentile` field has repeatedly, measurably diverged from the real
watchlist Rank column (COIN: 45 vs 53%, AVAV: 40 vs 65.3%, WOLF: 26 vs 58.7% — all logged in
`CLAUDE_CONTEXT.md` Known Issues / Session History). If the raw REST API has the same gap,
switching from MCP to raw REST calls buys nothing for the one gate that matters most (Sieve 1).
If it *doesn't* have the gap — genuinely worth knowing.

**Method:** don't guess field IDs from memory. Sweep the documented numeric field-ID range in
batches (the snapshot endpoint's own limit), capture every field that returns a non-null value
for a real ticker, and manually cross-reference against a known-real IVR pasted from an actual
IBKR watchlist. Let the data answer it, not a remembered number.

## Prerequisites — not yet done, needs you

1. **Download the Client Portal Gateway** (different product from `IB Gateway 10.44`, which is
   already installed but is the TWS *socket* gateway, not this REST one):
   https://www.interactivebrokers.com/campus/ibkr-api-page/cpapi-v1/ → "Download" section.
   It's a zip, typically named `clientportal.gw.zip`.
2. **Port 5000 conflict, known gotcha on Mac:** macOS's AirPlay Receiver holds port 5000 by
   default (confirmed occupied by `ControlCenter` on this machine). Either disable AirPlay
   Receiver (System Settings → General → AirDrop & Handoff) or change the gateway's listen port
   in `root/conf.yaml` before starting it.
3. **Start the gateway:** `cd clientportal.gw && bin/run.sh root/conf.yaml` (macOS/Linux).
4. **Authenticate:** open `https://localhost:5055` (or your chosen port) in a browser, log in
   with your real IBKR credentials + 2FA. This has to be a real interactive login — nothing in
   this probe can automate that step.
5. Confirm it's live: `curl -sk https://localhost:5055/v1/api/iserver/auth/status` should return
   `{"authenticated": true, ...}`.

## Files

- `client.py` — thin wrapper: `auth_status()`, `search_conid(symbol)`, `snapshot(conids, fields)`.
  Handles the self-signed localhost cert (`verify=False` — safe here, it's loopback-only).
- `probe_fields.py` — the actual sweep. Resolves a test ticker's conid, then requests field IDs
  in batches of 50 (the API's per-call cap) across the documented range, and writes every
  non-null field to `probe_results_<TICKER>_<timestamp>.json` for inspection.
- `compare_against_known.py` — takes the probe output plus a manually-supplied real IVR value
  (paste it in from an actual watchlist), and flags any returned field whose value is
  numerically close, as a candidate — never a confirmed match on its own, just a lead to check
  by hand against a second ticker.

## How to run, once the gateway is up

```bash
cd research/ibkr_rest_api_probe
python3 probe_fields.py NVDA
# then, with a real pasted IVR for NVDA in hand:
python3 compare_against_known.py probe_results_NVDA_*.json --known-ivr 41
```

## What "success" looks like

Not a single number match on one ticker — that could be coincidence. Real confirmation needs
the *same* field ID landing close to the known IVR across 2-3 different tickers with different
IVR values. One hit is a lead; three consistent hits is a finding worth updating
`ibkr-mcp-capabilities.md` and the Scanner architecture over.

## What happens if this comes back empty

That's a real, useful result too — it confirms (empirically, not from a Known Issues note
written months ago) that IV Rank genuinely isn't API-accessible, and paste-mode stays the only
path. Either outcome is worth having; that's why this is safe to run.
