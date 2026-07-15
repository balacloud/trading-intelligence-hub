# TRADING-INTELLIGENCE-HUB → OPTIONS IQ GEMINI STATE HANDOFF
> **Auto-generated:** 2026-07-15 10:51:53
> **Purpose:** What changed on the hub side that's relevant to Options IQ Gemini. Read this
> at session start alongside your own STATE_HANDOFF.md -- that file covers your own repo's
> state; this one covers the upstream skill/contract side you don't otherwise see.
> **Canonical references (not duplicated here -- go to the source, don't trust a stale copy):**
> `Docs/CENTAUR_SCHEMA_v2.json` (your own copy is authoritative) and the hub's own
> `OPTIONS_SIEVE_SPEC.md` if you need to understand *why* a payload looks the way it does.

---

## 1. Current skill versions (the things that produce your CENTAUR JSON)
- `skill-options-ibkr-radar.md`: Options IQ — IBKR Radar v2.3
- `skill-options-scanner.md`: Options IQ — Autonomous Scanner (v2.3 — Curated Edge Monitor)
- `skill-options-directional-builder.md`: Directional Trade Builder — v1.6
- `skill-options-trade-validator.md`: Options Trade Validator v3.1

---

## 2. Latest hub session (may or may not be Gemini-relevant -- read for context, not everything here concerns you)
### July 15, 2026 — Session 26
**The `get_option_data` blocker resolved itself; the actual first live forward-test journal entries went in; watchlist expanded with 20 names from Bala's conviction research.**
- **Retried `get_option_data` first thing, per the Session 25 pre-flight queue:** 4/4 clean (AFRM, GDX, OKLO, NIO chains all resolved on the first attempt) — the 15/15 failure from Jul 13 is gone. No code change on this side; root cause stays unconfirmed (most likely transient, server-side, per Session 25's isolation), but the tool is verified working again.
- **Ran the reject arm's Directional Builder pass** (OKLO, NIO) — both score BEARISH (4/5 signals: SMA200 downtrend, negative YTD, bearish EMA stack, lower-third 52w range all outweigh a single bullish avg-P/C-ratio signal), so both take the nearest-ATM put per the protocol's symmetry rule. Computed via a Python script running the skill's own Step 4/5 formulas exactly, not a different methodology — just precise arithmetic over ~250 daily bars instead of hand-eyeballing it (a question the user asked directly this session — confirmed this is not a Centaur-Mode substitute; the forward test deliberately bypasses Gemini's Centaur synthesis by design, per `FORWARD_TEST_PROTOCOL.md`, so both arms get identical mechanical contract construction).
- **Real finding surfaced re-pulling live data 2 days after Session 25's scan:** GDX's IVR drifted from 44.4% (Jul 13, passed Sieve 1 provisionally) to 48.2% (Jul 15) — it would now fail the gate it was originally selected under. Asked Bala rather than deciding unilaterally; kept as originally selected (the scan is the selection event), with the drift recorded honestly in both the journal's `setup_context` and `forward_test_log.csv` rather than silently smoothed over.
- **First live entries actually logged to Gemini's journal:** AFRM 85 Call (id 8, entry mid $5.85), GDX 74 Put (id 9, entry mid $2.835 — flagged unusually wide spread at market open), OKLO 46 Put (id 10, entry mid $3.80), all Aug 7 2026 (25 DTE). **NIO's 5 Put got `NO_QUOTE`** — two consecutive live-quote pulls at market open both returned empty bid/ask; recorded honestly per the quote-or-skip rule, not fabricated or forced.
- **Ran a full second Scanner cycle same day** (the actual Jul 15 scan, not just executing Jul 13's backlog): CORE 0/20 again (all failed Sieve 1, despite VIX calm at 16.1); EXTENDED 58/59 resolved (ABB unresolvable again, same as Session 25) with only 4 names clearing Sieve 1 (CCJ, MP, URA, XLF) and just 1 true finalist — **CCJ** (IVR 43.0%, IV/HV 97.9%). MP/URA/XLF all failed exactly Sieve 2b, becoming the reject-arm control group.
- **`get_option_data` regressed mid-session** — 4/4 clean at ~09:15 ET, then 5/5 failed at ~14:30 ET on the same session, with `get_price_snapshot` succeeding immediately after on the identical contract (rules out a broader outage). Bala's diagnosis was two-part: (1) suspected the burst of MCP calls this session (VIX + 20 CORE + 58 EXTENDED snapshots) was overloading it, and (2) asked directly why Tradier wasn't being used instead. Point (2) led somewhere real: Gemini's own `app.py` already has a working `/markets/options/chains` Tradier integration, and the token (confirmed alive since Session 24's `/tradier/ping` success) works fine for chains/quotes — the Fundamentals Beta gap only ever blocked the earnings *calendar*, not chain data. Read the token from `options_iq_gemini/.env` (with Bala's explicit go-ahead first) and called Tradier's REST API directly via curl — clean chain data for all four names on the first try. **Tradier is now the primary chain-data path for the forward test, IBKR MCP demoted to fallback** — both `FORWARD_TEST_PROTOCOL.md` and this file updated.
- **Logged the second round:** CCJ 91 Put (id 11, survivor, BEARISH 5/5 signals despite being the day's one clean pass — earnings Jul 30 is 15 days out, WITHIN HOLD not TBLA), MP 50 Put (id 12), URA 41 Put (id 13), XLF 57 Call (id 14, the day's only BULLISH name). All via Tradier, all Aug 7 2026.
- **Watchlist expansion:** Bala supplied five separate conviction-stock research tables (AI Supply Chain framework, STRATUM critical-materials framework, Canadian conviction list, US conviction list). Deduped the full union against the existing CORE/EXTENDED watchlist and against each other, then filtered out 10 Canadian TSX/Venture-only tickers with no US options market (architecture constraint, not a judgment call — Gemini trades via Tradier, US-only). Verified 8 ambiguous tickers live via `search_contracts` before proposing them (GIB, TRP, ASTS, FN, MOD, CGNX, LSCC, PATH all confirmed real US-optionable listings). Added 20 net-new tickers to `skill-options-scanner.md` EXTENDED (v2.2 → v2.3) across 5 new theme sections plus 6 existing ones; 6 of the new names (MOD, FN, CGNX, LSCC, ASTS, PATH) join the existing thin-name OI-verification list. `SKILL_MAP.md` updated to match.

---

## 3. Open cross-repo Known Issues (from the hub's Known Issues table, filtered to rows tagged "cross-repo")
No open cross-repo Known Issues rows as of this generation. (Valid state, not an extraction failure.)
