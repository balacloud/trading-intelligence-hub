# TRADING-INTELLIGENCE-HUB → OPTIONS IQ GEMINI STATE HANDOFF
> **Auto-generated:** 2026-07-13 11:59:55
> **Purpose:** What changed on the hub side that's relevant to Options IQ Gemini. Read this
> at session start alongside your own STATE_HANDOFF.md -- that file covers your own repo's
> state; this one covers the upstream skill/contract side you don't otherwise see.
> **Canonical references (not duplicated here -- go to the source, don't trust a stale copy):**
> `Docs/CENTAUR_SCHEMA_v2.json` (your own copy is authoritative) and the hub's own
> `OPTIONS_SIEVE_SPEC.md` if you need to understand *why* a payload looks the way it does.

---

## 1. Current skill versions (the things that produce your CENTAUR JSON)
- `skill-options-ibkr-radar.md`: Options IQ — IBKR Radar v2.3
- `skill-options-scanner.md`: Options IQ — Autonomous Scanner (v2.2 — Curated Edge Monitor)
- `skill-options-directional-builder.md`: Directional Trade Builder — v1.6
- `skill-options-trade-validator.md`: Options Trade Validator v3.1

---

## 2. Latest hub session (may or may not be Gemini-relevant -- read for context, not everything here concerns you)
### July 13, 2026 — Session 25
**The actual first live forward-test Scanner run — real survivors found, then a hard infrastructure blocker stopped contract construction cold.**
- **Tradier verified functionally, for real this time:** ran `test_tradier_calendar.py` (queued since Session 19/20). Result: **HTTP 404**, not 401 — this account's Tradier plan doesn't include the Fundamentals Beta product. `get_earnings_date()` will always fall through to `EARNINGS_UNKNOWN` here regardless of token state. Corrected the long-standing "pending token refresh" framing — refreshing the token was never going to fix this.
- **Ran PATH B Scanner live, both tiers, for the first time ever:** VIX 16.25 (STANDARD regime) via IBKR MCP. **CORE (20 names): 0 survivors** — every single name failed Sieve 1 (IVR > 45%); NVDA (46.8%) and ALB (47.2%) closest, but both also independently fail Sieve 2b, so no clean near-misses either. Per the Scanner's own trigger rule (<3 finalists → scan EXTENDED), continued to **EXTENDED (44 of 45 resolved — ABB unresolvable; discovered `search_contracts` silently empties on multi-word "TICKER Name" queries, ticker-only works reliably): 2 survivors, 2 clean near-miss rejects.** Survivors: **AFRM** (IVR 13.6%, IV/HV 90.1%, uptrend, Gate C $413.8M/day) and **GDX** (IVR 44.4% — provisional/near the cutoff, IV/HV 78.8%, downtrend, Gate C $1.63B/day). Near-miss rejects (failed exactly one gate — Sieve 2b IV/HV): **OKLO** (IVR 35.2%, IV/HV 109.8%) and **NIO** (IVR 18.4%, IV/HV 113.0%).
- **Resolved a real open question along the way:** Session 19 flagged `avg_90d_usd_volume` as possibly a 90-day total rather than a daily average (which would make Gate C's $100M threshold off by ~90x). Settled with live data: it's a daily average — the tool's own field description confirms it, and NVDA's live $32.9B figure only makes sense as a daily number.
- **Surfaced a real protocol gap:** no monthly expiry fell inside 21-35 DTE this cycle (nearest monthly was 39 DTE) for any of the four candidates, since they share an identical options calendar. Asked Bala rather than deciding unilaterally — chose "use the nearest weekly inside the window" (Aug 7, 2026, 25 DTE) as the standing rule going forward. `FORWARD_TEST_PROTOCOL.md`'s "nearest monthly" language may need amending if this recurs.
- **Then hit a genuinely hard blocker: `get_option_data` failed 15/15 times.** Methodically ruled out three explanations rather than assuming the first one: (1) not a parameter mistake — varied ticker/expiry-type/strike-range across attempts, identical generic error every time; (2) not Claude-Code-specific — found two real, relevant bugs on Anthropic's own GitHub trackers (`claude-code#69917`, an OAuth path-mismatch specific to Claude Code vs. Claude Chat; `claude-ai-mcp#405`, IBKR token-expiry with no reconnect) that looked like promising explanations, but Bala independently reproduced the identical failure on claude.ai web chat, which rules both out — those bugs describe total connector failure, not this selective single-tool pattern; (3) not a stale `expiration_id` — re-fetched fresh immediately before a final retry, got a byte-for-byte identical id, still failed. `search_contracts`, `get_price_snapshot`, `get_option_parameters` all worked fine throughout, including the fresh re-fetch. Real, isolated, cross-environment failure with no root cause identified past "something in IBKR's final chain-lookup step, not a session/auth/parameter issue on our side."
- **Held the line on honesty over forcing a result:** did not fabricate a contract, quote, or premium to produce a forward-test log entry. Recorded the real Scanner data (both survivors and near-miss rejects, with all computed gate values) in `forward_test_log.csv` with `resolution=LOGGING_BLOCKED` and a precise note on what failed and why. This is exactly the discipline the forward-test protocol's own honesty rules were written to enforce.
- Two commits this session: Scanner run + findings (`ea94ff7`), plus this close.

---

## 3. Open cross-repo Known Issues (from the hub's Known Issues table, filtered to rows tagged "cross-repo")
No open cross-repo Known Issues rows as of this generation. (Valid state, not an extraction failure.)
