# TRADING-INTELLIGENCE-HUB → OPTIONS IQ GEMINI STATE HANDOFF
> **Auto-generated:** 2026-07-23 15:45:16
> **Purpose:** What changed on the hub side that's relevant to Options IQ Gemini. Read this
> at session start alongside your own STATE_HANDOFF.md -- that file covers your own repo's
> state; this one covers the upstream skill/contract side you don't otherwise see.
> **Canonical references (not duplicated here -- go to the source, don't trust a stale copy):**
> `Docs/CENTAUR_SCHEMA_v2.json` (your own copy is authoritative) and the hub's own
> `OPTIONS_SIEVE_SPEC.md` if you need to understand *why* a payload looks the way it does.

---

## 1. Current skill versions (the things that produce your CENTAUR JSON)
- `skill-options-ibkr-radar.md`: Options IQ — IBKR Radar v2.3
- `skill-options-scanner.md`: Options IQ — Autonomous Scanner (v3.1 — Watchlist-Paste Edge Monitor)
- `skill-options-directional-builder.md`: Directional Trade Builder — v1.6
- `skill-options-trade-validator.md`: Options Trade Validator v3.1

---

## 2. Latest hub session (may or may not be Gemini-relevant -- read for context, not everything here concerns you)
### July 23, 2026 — Session 32

**A self-contained pet-project side quest: built and ran a real empirical test of whether IBKR's Client Portal REST API could substitute for the manual watchlist-paste step, settled it with hard evidence across two independent sources, and wrote it up in a form other engines can actually reuse — none of it touched the forward test, a skill, or a Known Issues row.**

Opened by reviewing a pasted research summary on using IBKR's REST API for `swing-trade-analyzer`'s own broker integration — verified the claims directly rather than accepting them (per Bala's explicit "don't jump to conclusions" ask): confirmed the Client Portal REST architecture and gateway-auth flow against IBKR's own docs, and tracked down the actual regulatory citation behind the Canadian auto-execution restriction (CIRO Dealer Member Rule 3200 A.1.(b)(i), not just "IBKR said so") — one correction made to the source doc's framing (the restriction is CIRO-wide, not Ontario-specific).

**That review turned into a live test.** Bala asked whether the REST API could eliminate the Scanner's copy-paste step. Built a real, isolated probe (`research/ibkr_rest_api_probe/`) rather than answer from memory: set up the actual Client Portal Gateway from scratch (found and fixed a real port-5000/macOS-AirPlay-Receiver conflict, found and reused the JRE already bundled inside the installed `IB Gateway 10.44.app` rather than requiring a separate Java install), authenticated live, and swept ~1,150 documented field IDs against real tickers. Found and fixed a real bug in the first version of the sweep script (IBKR's snapshot endpoint returns *all* currently-subscribed fields per conid, not just the ones requested that call — the original code only recorded matches against the current batch's request list, silently discarding the rest). Caught a real, unrelated privacy issue along the way: the snapshot response included Bala's actual live NVDA position P&L mixed into "market data" — gitignored the raw probe output immediately, before it could land in git with real account numbers in plaintext.

**Ran the real comparison, not a one-off.** Got genuine ground truth by having Bala paste fresh `HUB_CORE` rows (a Chrome-extension attempt to read the value directly was tried first and correctly abandoned after hitting a real site-permission wall, not forced through) for 6 tickers spanning IV Rank 28-91, and cross-referenced every REST field against them. Result: **11 of ~14 watchlist columns confirmed available via REST** (several matching exactly), plus full watchlist-membership access via `/iserver/watchlist` (checked both `HUB_CORE` id 110 and `HUB_EXTENDED` id 111) — but **`52 Week IV Rank`, the single field Sieve 1 gates the entire Scanner pipeline on, is absent everywhere**, with every apparent near-match traced to a different, already-confirmed field (Hist Vol Close %, Option OI, Opt Implied Vol %, 52wk Low) coincidentally landing close to that ticker's real IV Rank — not a real signal. Independently corroborated against `Voyz/ibind`, a real open-source IBKR REST client library with no connection to this project: same field mappings, same "no IV Rank field exists" conclusion. Also checked whether Tradier's API could substitute — same category of gap (current IV via ORATS, no historical-IV time series, no rank).

**Distinguished exactly which pipeline step the gap actually blocks**, at Bala's direct question: the Scan step (Sieve 1's purge gate, applied to the whole 20-65-name universe) is where it's load-bearing — without it, screening can't run at all. The Execution step (Gemini's own Centaur `IVR > 45` hard gate) re-validates the *same* number the hub already had to source upstream, not a second independent need — it mainly catches scan-to-execution staleness drift, the same phenomenon already documented on AFRM in Session 30.

**Closed by writing this up for reuse, not just as a research log.** `FINDINGS.md` is the full narrative (method, evidence, false-positive table). `IBKR_REST_API_REFERENCE.md` is a new, deliberately portable technical reference — project-agnostic, with the confirmed field-ID table, the setup gotchas (port conflict, bundled-JRE trick, the cumulative-subscription bug), and two sections written directly for the other engines: one telling `options_iq_gemini` this is hard evidence for *why* `app.py:651`'s IVR sentinel exists (not just an assumption baked into the code), and one telling `swing-trade-analyzer` these field IDs and gotchas are directly reusable if its own REST integration proposal moves forward, so nobody re-discovers any of this from scratch.

---

## 3. Open cross-repo Known Issues (from the hub's Known Issues table, filtered to rows tagged "cross-repo")
| LOW-MEDIUM (finding, cross-repo, unblocked not fixed) | UUUU (journal id 33) has a malformed `occ_symbol` (`'UUUU  260814P00013000'` — OCC-padded, two spaces — vs every other row's compact Tradier format like `NFLX260821P00070000`) | Session 31 (Jul 22, 2026): Bala noticed UUUU showing nothing in the dashboard monitor. Verified live, not assumed: pulled UUUU's option quote directly from Tradier (genuinely live — bid $1.25/ask $1.45, OI 233), confirming this is a stored-symbol-format bug, not a market-data gap. `/journal/monitor`'s skip-on-missing-quote logic (Session 21 hardening) is working correctly — it's the input that's wrong. **Operationally relevant now:** the hub's own `resolve_positions.py` will report `NO_QUOTE` for UUUU (false negative) until fixed — it keys quotes by the same malformed `occ_symbol`. Drafted `HANDOFF_gemini_uuuu_occ_symbol_fix.md` (one-row `UPDATE trades SET occ_symbol = 'UUUU260814P00013000' WHERE id = 33`, plus a suggestion to grep `trades.db` for any other rows with the same padding pattern). Not fixed yet — needs Gemini's dev session. |
