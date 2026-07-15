# CLAUDE_CONTEXT.md — Trading Intelligence Hub
> Source of truth for this project. Read this at the start of every Claude Code session.
> Last updated: July 15, 2026 (Session 26, closed — the forward test's first real, non-placeholder entries, across two full daily cycles, plus a real architecture fix. Retried `get_option_data` first thing per the Session 25 queue: 4/4 clean (AFRM, GDX, OKLO, NIO), resolving the Session 25 blocker — briefly. Ran Directional Builder on the two rejects (OKLO, NIO both BEARISH), resolved the actual entry contracts, and logged **AFRM 85 Call (id 8), GDX 74 Put (id 9), OKLO 46 Put (id 10)** to Gemini's journal — GDX logged as originally selected despite its IVR drifting from 44.4% (Jul 13 pass) to 48.2% (now a fail) between selection and execution, per Bala's explicit call to honor the scan as the selection event rather than silently re-gating. NIO's put had no live quote on two tries — recorded `NO_QUOTE`, not forced. Added 20 tickers to `skill-options-scanner.md` EXTENDED (v2.2→v2.3) from Bala's own conviction research, after deduping against the existing watchlist and filtering out 10 Canadian TSX/Venture-only names with no US options market (Gemini is Tradier/US-only by design). Then ran a full second, genuine Jul 15 Scanner cycle: CORE 0/20 again, EXTENDED 58/59 resolved (ABB unresolvable, same as Session 25) with 4 Sieve-1 passes and exactly 1 true finalist, **CCJ** (IVR 43.0%, IV/HV 97.9%, earnings Jul 30 — 15 days out, WITHIN HOLD). **`get_option_data` then failed 5/5** on the second attempt of the same session (after being clean 4/4 earlier) — Bala questioned whether this was an IBKR call-volume/overload issue and asked directly why Tradier wasn't used instead. That second question led to a real fix: Gemini's own `app.py` already had a working Tradier `/markets/options/chains` integration, and the token (alive since Session 24) works fine for chains/quotes — the Fundamentals Beta gap was always calendar-only. Read the token from `options_iq_gemini/.env` (Bala's explicit go-ahead) and called Tradier's REST API directly — clean chain data for CCJ/MP/URA/XLF on the first try. **Tradier is now the primary chain-data path for the forward test, IBKR MCP demoted to fallback** (`FORWARD_TEST_PROTOCOL.md` updated). Logged the second round: **CCJ 91 Put (id 11), MP 50 Put (id 12), URA 41 Put (id 13), XLF 57 Call (id 14)** — 8 positions now genuinely OPEN in Gemini's journal, the forward test's first real data after 5 sessions of delay. Prior: Session 25 (Jul 13), closed — the actual first live forward-test Scanner run, queued since Session 21. Confirmed the Tradier earnings endpoint is a real 404 (Fundamentals Beta not on this account's plan) — not a token problem, correcting a wrong assumption tracked since Session 19. Ran PATH B live end-to-end: VIX 16.25 (STANDARD), 64 names screened (CORE 20 + EXTENDED 44/45 — ABB unresolvable). **CORE: 0/20 survivors** — every name failed the IVR gate, a real "no edge today" result. **EXTENDED: 2 survivors (AFRM, GDX) + 2 clean near-miss rejects (OKLO, NIO)**, all recorded in `forward_test_log.csv`. Also settled the Session 19 Gate C units question live: `avg_90d_usd_volume` is a daily average, not a 90-day total. **Then hit a real, hard blocker:** `get_option_data` failed 15/15 times — varied ticker/expiry/strike (ruled out a parameter mistake), reproduced independently by Bala on claude.ai web chat (ruled out the known Claude-Code-vs-Claude-Chat OAuth bug), and still failed against a freshly re-fetched `expiration_id` (ruled out staleness). Real, isolated, unexplained past that — most likely a server-side issue in the final step of IBKR's option-chain lookup chain. No contract or quote was fabricated to force a log entry; the gap is recorded honestly as `LOGGING_BLOCKED`. This is now the actual #1 blocker for the forward test, ahead of anything Tradier-related. Prior: Session 24 continuation (Jul 12), closed — same session resumed after Sunday's close, cleared the entire Session 19 Fable 5 backlog in one pass. User asked "keep going" three times across the backlog rather than scoping one item at a time. **Pine script** (`tradingview/gemini-edge-scanner.pine`): fixed all 5 sub-findings — `barstate.isconfirmed` gating on S/R mutation (repaint fix), a strict inequality on the resistance-break condition (same-bar double-flip fix), new `all_res_pivots`/`all_sup_pivots` history arrays with a `broken` flag (Bug B/ECHO fallback — a pivot rejected by the proximity filter can re-enter later without resurrecting one already flipped), named inputs for the `0.0005`/`0.85` wedge literals. Verified by careful read only — no Pine compiler available in Claude Code, still needs the TradingView paste-test already queued in Next Steps. **`skill-options-directional-builder.md`** v1.5→v1.6: `INSUFFICIENT HISTORY`/`N/A`/`--` table states now explicitly excluded from Step 6's direction vote and its scored-signal denominator. **`skill-options-trade-validator.md`** v3→v3.1: Mode 1 now explicitly accepts a Gemini Centaur briefing as a first-class trigger, with a field-availability table (built from a live read of `options_iq_gemini/app.py`) showing Gemini's briefing has no Gamma/Vega/IV%/HV30/terminal score — state "not provided," never fabricate; Market Chameleon IVR search replaced with an honest fallback (confirmed dead per Session 12). **`SKILL_MAP.md`** fully regenerated (was stale in 4+ places, including missing the cross-repo-fix-verification skill entirely). **`PERSONA.md`** critique section now points to the living Known Issues table instead of a static (and by-then-stale) critique list. **`skill-options-ibkr-radar.md`** v2.2→v2.3: added the Phase 0 VIX regime pull back-ported from Scanner (Session 13), with an honest `UNKNOWN` fallback — Radar previously had no VIX source at all beyond "if the user mentions it." **`skill-options-scanner.md`** v2.1→v2.2: the "Gate A pre-satisfied by curation" claim was checked, not just documented — live web search **confirmed HIVE currently trades below the $1B floor** (~$790–900M) and POET dipped sub-$1B as recently as mid-June; added a per-run live Gate A check for these two specifically. **Left for Bala:** whether to keep HIVE on CORE given it's currently failing the gate it's supposed to be pre-cleared on — a watchlist-content call, not a code fix. All four skills need web re-upload (Next Steps, manifests unchanged). Prior: Session 24 (Jul 11) close — resumed after an abrupt interruption mid-session. The interrupted session had already made two uncommitted edits: built `SKILL_CONVERSION_SCOREBOARD.md` (measurement only — 0% of any skill actually converted to Python, just estimated Python-able % per skill) and flipped the Known Issues "Scanner watchlist review" row to RESOLVED (Bala approved the CORE/EXTENDED tables). That row's trailing clause — "immediately before the first live Scanner run (forward test)" — implied the run happened; it hadn't. Checked directly rather than assumed: `options_iq_gemini/trades.db` has zero `FWD_TEST` rows and zero paper-trade entries since PLTR closed Jun 26, and `backend.log` shows only `GET /tradier/ping` + `GET /journal/history` calls on Jul 10 — no `POST /journal/log`, no `POST /analyze/centaur`. The first live run never happened; the session cut off between approving the watchlist and executing it. Corrected the Known Issues row's wording to stop implying otherwise. One real finding from the check: the Tradier ping returned success (200, confirmed via the actual success-only branch in `app.py:1111-1141`, not just an HTTP code) for the first time since the token died ~Jul 5 — worth a real functional test (`test_tradier_calendar.py` or a live `/analyze/centaur` call) before trusting it, since a ping only proves auth, not that the chain/calendar endpoints work. Market is closed today (Saturday, Jul 11) — the actual first live run + Tradier functional check now lands Monday, July 13. Prior: Session 23, closed — verified Gemini's session-open status summary against live code rather than accepting it. Confirmed true: the `IBKR_VERIFIED` sentinel fix (Phase 14, "Session 21 Relay Application," Jul 6) — read `options_iq_gemini/app.py:811-826` directly, confirmed `analyze_centaur` now fails loud with `400 MISSING_IVR`. That surfaced a stale hub tracker: the Known Issues table still said "unfixed — cross-repo" and the relay checklist still said "not yet sent" even though Gemini had already fixed it independently off its own read of `GEMINI_STATE_HANDOFF.md`. Known Issues row flipped to RESOLVED, relay item marked moot. Root-caused the lag (Gemini can fix hub-reported findings with no report-back mechanism) and closed it going forward: promoted `skill-cross-repo-fix-verification.md` from "manual invocation only" to a mandatory session-start step whenever the Known Issues table has a cross-repo row. Forward test confirmed still not started (user-confirmed directly; no live read needed). Prior: Session 22, closed — orientation/status-check only, no deliverables. User asked "where are we"; answered from a live read of this file. Checked `research/forward_test/forward_test_log.csv` directly — still only the header row, zero entries logged, despite the Session 21 addendum's Tue Jul 7 target for first forward-test entries. Not checked this session: whether `FWD_TEST:` rows actually exist in Gemini's own paper-trade journal (would need a live read of `options_iq_gemini/database.py` / `/journal` to confirm one way or the other) — flagged to the user as open, not assumed either way. Prior: Session 21, closed — Fable 5 review of a 3-year WhatsApp signal group (21,634 msgs): deciphered the method, verified 764 signals against real price data (stocks 50.0% win = indistinguishable from random control at 53.3%; options 46% expired worthless; 157 win claims vs ~2 loss admissions). Replayed their 254 option signals through the hub's gate stack — full stack refuses 121/121 single-name signals: refusal validated (60/60 worthless blocked), within-flow discrimination unproven (40/42 winners blocked too; survivors n=8). Designed the survivors-vs-rejects forward test (`research/forward_test/`) with positions living in Gemini's paper-trade journal via API (live-read of `/journal/*` + `database.py` first), `FWD_TEST:` tagging to protect Gemini's own record, pre-registered success criterion, first entries Monday July 6. Tradier token refresh is now the #1 pre-Monday blocker (blocks TBLA verification AND forward-test auto-marks). Prior: Session 20 — built `OPTIONS_SIEVE_SPEC.md` (pending since Session 13), resolving real Radar/Scanner drift (Gate C computation, finalist IV/HV qualification — Radar bumped v2.1→v2.2). Reviewed Gemini's real `CENTAUR_SCHEMA_v2.json` directly. Consolidated the full end-to-end pipeline into this file's own section (previously only existed in fragments across both repos). Verified Gemini's `STATE_HANDOFF.md` automation twice by running it, not reading it — found and confirmed-fixed a real path-fragility bug and a factual conflation. Built the hub's own mirror (`scripts/generate_gemini_handoff.py` → `GEMINI_STATE_HANDOFF.md`), formalized `skill-cross-repo-fix-verification.md` as a reusable procedure, and adopted `GOLDEN_RULES.md` from STA (curated, three rules explicitly rejected with reasoning). One new sharpened finding logged, not yet relayed: `IBKR_VERIFIED` masks silently-absent IVR data as pre-verified. Prior: Session 19 — Fable 5 critical review of project/skills/Pine + 4 highest-severity fixes; verified Gemini's contract-hardening fixes by reading live code and running its test suite, corrected two overstated claims, and ran a refined regime-segmented backtest finding the edge concentrates in vol-compressed setups, not trend alone.)
> **Also load at session start:** [PERSONA.md](./PERSONA.md) — the Alex lens (systems architect + quant trader). Every design decision runs through this persona.

---

## Project Identity

**Project:** Trading Intelligence Hub
**Purpose:** Research lab, peer reviewer, skill creator, code author, and **agent builder** for THREE trading systems: Options IQ Gemini (single-name options), OptionsIQ (ETF-only options), and Swing Trade Analyzer / STA (swing equities).
**Status:** Active — 4 live skills, 1 skill in design, HTML terminal in maintenance
**Boundary:** Serve all three trading systems. Any request — research, code fix, new skill, new agent, peer review of a diff — is in scope if it serves Options IQ Gemini, OptionsIQ (ETF), or STA.
**Environment:** VS Code + Claude Code

---

## Project Scope

This hub plays five roles for Options IQ Gemini, OptionsIQ (ETF), and STA:

1. **Researcher** — investigate quant signals, market structure rules, edge definitions
2. **Peer reviewer** — audit code for correctness and quant validity (REVIEW_SESSION5.md pattern)
3. **Skill creator** — author and maintain Claude skills that plug into the pipelines
4. **Code author** — write Python/JS/other code to complement or extend any of the three engines
5. **Agent builder** — design and build agents that serve the trading systems

| Skill | File | Status | Serves | Purpose |
|-------|------|--------|--------|---------|
| IBKR Radar | `skill-options-ibkr-radar.md` | v2.3 ✅ Active | Options IQ Gemini | 4-Sieve Engine on IBKR scanner paste/screenshot → top 3 finalists |
| Trade Validator | `skill-options-trade-validator.md` | v3.1 ✅ Active | Options IQ Gemini | Second opinion on Gemini recommendations + ad-hoc + Canadian stocks |
| Directional Builder | `skill-options-directional-builder.md` | v1.6 ✅ Live tested | Options IQ Gemini | Ticker + direction (+ optional TradingView screenshot) → IBKR MCP pull → vol/trend/technicals + options-liquidity pre-screen + strike zone → CENTAUR JSON |
| **Options Scanner** | **`skill-options-scanner.md`** | **v2.2 ✅ Rebuilt (Session 13)** | **Options IQ Gemini** | **Curated-watchlist monitor: IBKR MCP screens CORE/EXTENDED watchlist for structural IVR/IV/HV edge. MCP-only, no scrape. Horizon-correct for 21–35 DTE.** |
| IBKR Scan | `skill-sta-ibkr-scan.md` | 🔧 In design | STA | Parse IBKR screenshots via Claude vision → call STA API → rank top 5–10 (⚠️ name collides with the ETF engine's own `options-iq/skills/ibkr-scan.md` — different skill, different project) |
| **Cross-Repo Fix Verification** | **`skill-cross-repo-fix-verification.md`** | **v1 ✅ Active (Session 20)** | **Hub-level (all engines)** | **Process skill, not an engine skill — encodes the "don't trust the summary, read the live code, run it, check for silent-failure/hardcoded/overstated-language patterns" procedure used repeatedly this session to verify Gemini's claimed fixes.** |

**HTML terminal** (`options-research-terminal-v3.html`) — v3.3, maintenance mode. No active development. Kept for reference and fallback.

---

## File Structure

```
trading-intelligence-hub/
├── skill-options-ibkr-radar.md              ← IBKR 4-Sieve Radar (v2) — scanner paste/screenshot path [Radar alignment pending — see HANDOFF doc]
├── skill-options-scanner.md         ← Autonomous Scanner (v2) — curated watchlist + IBKR MCP, MCP-only, no scrape
├── OPTIONS_SIEVE_SPEC.md            ← Shared sieve/gate/output canonical spec (anti-drift) — built Session 19/20, resolves the Gate C + finalist-qualification divergence between Radar and Scanner
├── HANDOFF_session13_scanner_radar.md ← Work order for Sonnet: Radar alignment + shared core + CLAUDE_CONTEXT sync
├── HANDOFF_gemini_contract_hardening.md ← Work order for Gemini (options_iq_gemini, separate repo — NOT executed here): consolidate CENTAUR_SCHEMA_v2 into one file, add runtime validation on /analyze/centaur, a contract test suite, and a schema-version-bump line in PROTOCOL.md's close checklist. Written after a field-by-field audit found ~18 of ~30 CENTAUR JSON fields (incl. iv_hv_ratio, trade_direction) are silently dropped on ingest.
├── SKILL_MAP.md                     ← One-page skill inventory (5 skills): job, triggers, sieves/modes, pipeline view. Regenerate from live skill files when versions/roles change.
├── SKILL_CONVERSION_SCOREBOARD.md   ← Tracks % of each skill's logic that's deterministic (Python-able) vs genuine LLM judgment; built Session 24. Update alongside session close.
├── skill-options-directional-builder.md     ← Directional Trade Builder (v1.6) — IBKR MCP + optional TradingView chart + options-liquidity pre-screen → CENTAUR JSON
├── skill-options-trade-validator.md         ← Trade validator (v3) — second opinion + ad-hoc + Canadian
├── PROJECT_INSTRUCTIONS_GEMINI.md   ← Claude Project instructions (intent router + engine facts) — paste into claude.ai Project
├── tradingview/
│   ├── gemini-edge-scanner.pine     ← Pine v6 indicator: EMAs + S/R zones + patterns + dashboard table ("Claude's eyes on the chart")
│   ├── OPUS_HANDOFF.md              ← Opus review/build handoff for the Pine script
│   └── PINE_DESIGN_BRIEF.md         ← Full design spec for the Pine script
├── research/
│   ├── options_edge_backtest_v2.py  ← Refined proxy backtest (Fable 5): CORE watchlist universe, regime-segmented, random-entry control, realized-vol-compression proxy for IV/HV, approx. Black-Scholes payoff. Read-only against options_iq_gemini/swing-trade-analyzer.
│   ├── backtest_v2_trades.csv       ← Raw trade log, 1,230 trades (118 kinetic-signal + 1,112 random-control)
│   ├── WHATSAPP_SIGNALS_REVIEW.md   ← Session 21: critical review of a 3-yr WhatsApp signal group — deciphered method, verified pass/fail vs real prices, gate-replay experiment (§8)
│   ├── whatsapp_signals_dataset.csv ← 629 parsed signals with independently verified outcomes (labeled test set)
│   └── forward_test/
│       ├── FORWARD_TEST_PROTOCOL.md ← Survivors-vs-rejects live test: rules, Gemini-journal integration, FWD_TEST tagging, pre-registered success criterion
│       └── forward_test_log.csv     ← Hub-side log: stand-down days + analysis export only (positions live in Gemini's journal)
├── options-research-terminal-v3.html ← HTML terminal (v3.3, maintenance only)
├── ibkr-mcp-capabilities.md         ← IBKR MCP field reference (69 fields, gaps, upgrade checklist)
├── config.js                        ← API keys (gitignored — never committed)
├── config.example.js                ← key template (committed, safe)
├── .gitignore                       ← ignores config.js
├── PERSONA.md                       ← Alex persona
├── GOLDEN_RULES.md                  ← Cross-project rules adopted from STA (curated, not copied) + the 5-type audit taxonomy (Claim/Coherence/Behavioral/Design/External)
├── CLAUDE_CONTEXT.md                ← this file
└── archive/
    └── options-trade-validator-v2.skill ← stale, ignore
```

**Skill naming convention (standardized June 30, 2026):** `skill-[engine]-[purpose].md` — filename stem **equals** the manifest `name:`. Family prefixes: `options-*` (Gemini), `sta-*` (STA). Claude Web identity is the manifest `name:`, not the filename — renaming a file alone needs no re-upload; changing a manifest name creates a new web entry (delete the old one).

---

## How to Start Every Claude Code Session

```bash
cd trading-intelligence-hub
claude
```

First message every session:
> "Read CLAUDE_CONTEXT.md and PERSONA.md — continuing Trading Intelligence Hub session."

`GOLDEN_RULES.md` is a reference doc, not required reading every session — consult it when scoping a review (use the audit taxonomy) or when a "this looks like a familiar bug" moment comes up (check the cross-project-validated findings section first).

**Mandatory if the Known Issues table has any row tagged "cross-repo":** run `skill-cross-repo-fix-verification.md` against Gemini's own `STATE_HANDOFF.md` / `KNOWN_ISSUES.md` before trusting any hub row's fixed/unfixed status. Gemini can fix a hub-reported finding independently (it reads `GEMINI_STATE_HANDOFF.md` too) with no mechanism to report back — Session 23 caught a 4-day-stale `IBKR_VERIFIED` row this way. Don't skip this because the table "looks current."

---

## Active Skills — Current State

### `skill-options-ibkr-radar.md` — v2 ✅ (Options IQ Gemini)

**Job:** Run the Fantastic 4-Sieve Engine on IBKR scanner screenshots or pasted table data. Output top 3 finalists with mathematical edge + directional context. Hand off to Options IQ Gemini Centaur Mode.

**What it does beyond the Gemini Gem (v1 was parity; v2 is advantage):**
- Computes RVOL from Volume ÷ AvgVol columns visible in the screenshot (zero extra API calls)
- Computes 52-week range position from Last / 52wkHigh / 52wkLow columns on screen
- Flags intraday RVOL as unconfirmed (pre-3PM ET) — prevents false signals
- Web-searches earnings date per finalist against 21–35 DTE window (TBLA rule at discovery stage)
- Web-searches 200d SMA trend per finalist (UPTREND/DOWNTREND) — directional framing for Centaur Mode
- Formalizes the Cheap IVR Trap (WBD canonical example: IVR 10 / IV/HV 165% — trap)
- Clarifies IBKR pre-sorts vs Radar hard-filters distinction
- Direction aware, not prescriptive — surfaces trend, never prescribes call vs put

**Install:** claude.ai → Customize → Skills → Upload a skill → select `skill-options-ibkr-radar.md`

**Tested:** May 19, 2026 — full pipeline run. IBKR screenshot → Radar → NFLX/PYPL/HOOD finalists → Centaur Mode → Gemini Intelligence. All three NO TRADE (SQUEEZE: NORMAL + signal conflicts). System worked correctly — stand down is a valid output.

---

### `skill-options-trade-validator.md` — v3 ✅ (Options IQ Gemini)

**Job:** Validate individual trade setups. Three modes: quick verdict (~150 words), deep dive (6-phase), comparison (two options, pick one).

**Current use cases:**
1. **Second opinion on Gemini recommendations** — paste Gemini's trade plan output and get Claude's independent read
2. **Ad-hoc trades** — ideas not coming through the IBKR Radar flow (tips, watchlist names, manual ideas)
3. **Canadian stocks** — Options IQ Gemini is US-only (Tradier); trade validator handles TSX underlyings

**Note:** Accepts plain trade descriptions ("NFLX $93 PUT Jun 18 at $4.72") or Options IQ Gemini trade plan output — just describe the trade.

**Install:** claude.ai → Customize → Skills → Upload a skill → select `skill-options-trade-validator.md`

---

### `skill-options-scanner.md` — v2 ✅ (Options IQ Gemini)

**Job:** Autonomously discover top 3 options candidates without any manual IBKR paste. Entry point for the pipeline when the user doesn't have scanner data ready.

**v2 design (rebuilt Session 13 — horizon-correct):**
- **Universe:** Curated CORE (20 names) + EXTENDED (~50 names, organized by theme) watchlist of liquid/high-beta names where the IV/HV < 100% edge actually appears. Themes: AI power/infra, semis & equipment, nuclear/uranium, critical materials, memory/storage, software, fintech, China ADR/EV, financials, space, energy, sector ETFs (unleveraged only). Leveraged ETFs (TQQQ/SPXL/SOXL) permanently excluded. No FinViz scrape — MCP-only.
- **Phase 0:** VIX pull → STANDARD / HIGH-FEAR regime. Wall-clock date anchor via python3.
- **Phase 1:** Watchlist (CORE default; EXTENDED on "deep scan" or < 3 finalists). contract_id cache halves MCP calls once populated.
- **Phase 2:** `get_price_snapshot` per ticker → IVR/IV/HV computed → Sieve 1 + Gates B/C + Sieve 2b. Gate A (micro-cap) pre-satisfied by curation.
- **Phase 3:** Web search per finalist — earnings (TBLA, 21–35 DTE) + 200d trend.
- **Output:** Radar-format TOP 3. Footer → Directional Builder (correct pipeline order).

**Key design rationale (the horizon principle):** Selection uses signals that persist over 28 days (IVR, IV/HV, trend, earnings-in-window, sustained liquidity). Daily RVOL / intraday volume is an execution-timing signal owned by Centaur Mode — never used for selection. This is why v1's "top 30 by today's volume" was wrong.

**Gate A pre-satisfied:** All watchlist names > $1B by curation. No per-run market-cap MCP call needed.

**Watchlist expanded (Session 13 continuation):** CORE (20 names): added GEV, VRT, PWR, ALB; moved SNOW/NET/HOOD/SOFI to EXTENDED. EXTENDED (~50 names): expanded with all approved thematic additions from ETF holdings research (GEV, VRT, ALB, PWR in CORE; AMAT, LRCX, KLAC, CEG, ETN, ANET, ALAB, CCJ [fixed from CCO], OKLO, WDC, MP, TECK, ABB, GS, SMH, URA, XLF, DRAM, SOXX, XBI, GDX in EXTENDED). Bala to review and approve before first live run.

**DTE authority:** 21–35 DTE confirmed in `gemini.md` line 15 — that is the authoritative source. Skill files are derived.

**Install:** claude.ai → Customize → Skills → Upload → `skill-options-scanner.md`

---

### `skill-sta-ibkr-scan.md` — 🔧 In Design (STA)

**Job:** Parse IBKR scanner screenshots via Claude vision, apply STA's 10-filter SEPA/CAN SLIM configuration, call STA API (`localhost:5001`), rank top 5–10 candidates.

**Research complete (STA Day 77):** 10 validated filters confirmed by 3-LLM audit (Perplexity + GPT + Gemini):
- Market Cap ≥ $1B, AvgVol ≥ $5M, Price/EMA(200) 1.05–1.65, Price/EMA(50) 1.00–1.20
- ROE ≥ 15%, EarnGrw% ≥ 20%, Inst.Held 25–90%, 52W High Proximity ≤ -25%, MACD Histogram ≥ 0, Change% -2 to +8

**Status:** Design complete, ready to build.

---

## The Full Options IQ Pipeline

**This section is the single complete end-to-end picture — the hub's own diagram used to stop at the Gemini handoff, and `options_iq_gemini/PROTOCOL.md`'s funnel diagram stops at "Live Position Management" without saying what that actually means. Neither one had the whole thing in one place until Session 19/20. If you change the pipeline, update this section, not just a skill file or `app.py`.**

Sieve/gate logic for PATH A and PATH B is now governed by `OPTIONS_SIEVE_SPEC.md` (canonical, anti-drift) — both skills defer to it rather than each describing the rules independently, which is how they drifted from each other before Session 19/20.

Two entry points, same downstream from Directional Builder onward:

```
PATH A — Manual (user has IBKR scanner data):
  IBKR Scanner (MultiSort: AvgOptVol + IV/HV + IVR)
      ↓ screenshot or paste
  [Claude skill: skill-options-ibkr-radar]  ·  see OPTIONS_SIEVE_SPEC.md for sieve/gate rules
      · Sieve 1: IVR ≤ 45 purge (real watchlist Rank — authoritative on this path)
      · Sieve 1.5: Gates A/B/C · Sieve 2b: IV/HV ranking, all 3 finalists must be <100%
      · Screenshot: RVOL + 52wk range · Web search: earnings (0-35 day span) + 200d SMA
      ↓ top 3 finalists

PATH B — Autonomous (no paste needed):
  [Claude skill: skill-options-scanner]  ·  see OPTIONS_SIEVE_SPEC.md for sieve/gate rules
      · Phase 0: VIX pull → STANDARD / HIGH-FEAR regime + wall-clock anchor
      · Phase 1: Curated CORE (~20) + EXTENDED (~50) watchlist (MCP-only, no scrape)
      · Phase 2: IBKR MCP per-ticker → Sieves 1/1.5/2b (⚠️ IVR here is an MCP-percentile
        proxy, not a real Rank — see OPTIONS_SIEVE_SPEC.md; Gate C's units are unverified)
      · Phase 3: Web search (earnings + 200d SMA)
      ↓ top 3 finalists

SHARED DOWNSTREAM (both paths):
      ↓ top 3 tickers
  [Claude skill: skill-options-directional-builder]  ← run per finalist
      · IBKR MCP: vol regime, RSI, EMA stack, TTM Squeeze, ATR, strike zone
      · Direction inference (up to 8 signals — dynamic strict-majority, not a fixed count)
      · Portfolio context · Options liquidity pre-screen
      ↓ CENTAUR_SCHEMA_v2 JSON (single enforced schema: options_iq_gemini/Docs/CENTAUR_SCHEMA_v2.json)
      ↓ POST within 30-min TTL
  [Options IQ Gemini — Centaur Mode]  (options_iq_gemini/, port 5002)
      · jsonschema validation on ingest (malformed/incomplete payload → 400, not silent drop)
      · HARD GATES (verified live, Session 19/20): iv_hv_ratio >= 1.0 → reject (EDGE_VIOLATION)
        · IVR > 45 → reject · trade_direction filters the chain (calls-only/puts-only, double-enforced)
        · portfolio context reaches the synthesis prompt
      · Earnings gate re-derived locally (TBLA rule) — ⚠️ fix applied but UNVERIFIED against a
        live Tradier response; Tradier token has been dead all of Session 19/20
      · Sieve 3: Fractal Squeeze (daily only — no weekly confirmation despite docs claiming it)
      · Sieve 4: RVOL ≥ 1.5 · Chain pull via Tradier (OI>500, spread<10%, delta 0.45-0.60)
      · Gate 1b: Liquidity Gravity (bid/ask asymmetry — noisy signal, no real calibration; treat
        as the least-trustworthy gate in the stack)
      ↓ (all gates pass)
  [Gemini Intelligence — Senior Quant, or deterministic Python fallback if Gemini is down]
      · Strike + expiry · Entry / target / stop / time stop (text recommendation only)
      ↓ (optional second opinion)
  [Claude skill: skill-options-trade-validator]
      · Independent verdict · Mode 1: quick · Mode 2: deep · Mode 3: compare
      ↓
  HUMAN EXECUTES MANUALLY IN IBKR / TRADIER — no order-placement code exists anywhere
  in options_iq_gemini. The "30% hard stop" and Gamma Surge trailing stop are MONITORED
  and FLAGGED (via /journal/monitor), never auto-fired. Risk management execution is a
  human-discipline requirement by design, not a software guarantee — confirmed by
  reading app.py directly (Session 19/20), not assumed.
```

**Evidence behind this pipeline (Session 19/20):** a regime-segmented proxy backtest (`research/options_edge_backtest_v2.py`, hub-side, read-only against both other repos) found the actual edge concentrates in vol-compressed setups specifically (56.7% win rate, survives a pessimistic IV-crush scenario) — the 200d trend filter *alone* is statistically indistinguishable from random entry. Only the long-call side has any backtest coverage; the put/bearish side is completely unvalidated in either version. Six live paper trades logged in `options_iq_gemini/history.md` stand at 1 win, 5 losses. Trade small; treat every live trade as more informative than another backtest iteration.

## The STA Pipeline

```
IBKR Scanner (STA 10-filter SEPA/CAN SLIM config)
    ↓ screenshot
[Claude skill: skill-sta-ibkr-scan] (🔧 in design)
    · Parse screenshot via Claude vision
    · Apply 10-filter SEPA/CAN SLIM gates
    · Call STA API (localhost:5001) for full analysis
    · Rank top 5–10 candidates
    ↓
[STA — Swing Trade Analyzer]  (swing-trade-analyzer/)
    · Categorical assessment: Strong/Decent/Weak
    · BUY / HOLD / AVOID verdict
    · Entry, stop loss, target, R:R
```

---

## Related Projects Reference

### Options IQ Gemini
**Location:** `/Users/balajik/projects/options_iq_gemini/`
**Stack:** Python/Flask (port 5002) + React/Vite/Tailwind (port 5175) + Tradier API + Gemini 1.5 Flash
**Key files:**
| File | Purpose |
|------|---------|
| `app.py` | Traffic cop — routing, data acquisition, API endpoints |
| `quant_math.py` | Junior Analyst — vectorized pandas technical analysis (squeeze, RVOL, trend, liquidity gravity) |
| `frontend/` | Bloomberg-style React dashboard |
| `gemini.md` | Core architecture, persona, 4-Sieve logic, Centaur architecture — source of truth |
| `history.md` | Phase-by-phase architectural decisions (Phase 12 current) |
| `KNOWN_ISSUES.md` | Active bugs + technical debt log |
| `AUDIT.md` | Quant Truth Audit Framework — weekly alignment verification SOP |
| `Docs/CLAUDE_MCP_SKILL_HANDOFF.md` | Stage 1→2 pipeline contract: schema, field mapping, TTL, Stage 2 checklist |

**Current state:** Phase 12, Centaur Ingestion live, Tradier sole data source.

> **Disambiguation:** `options_iq_gemini` (this one, underscores) = **single-name** US options via Tradier, port 5002, single-leg debit buying, Centaur/Gemini brain. Do NOT confuse with `options-iq` (hyphen) = **ETF-only** spreads via IBKR Gateway, port 5051. Different engines, different edges.

---

### OptionsIQ — ETF Options Engine (`options-iq`)
**Location:** `/Users/balajik/projects/options-iq/`
**Stack:** Python/Flask (backend port 5051) + React (frontend port 3050) + IB Gateway (port 4001, direct ib_insync — NOT Tradier) + SQLite (IV history, paper trades)
**Domain:** **ETF-only** options. 16-ticker universe (11 sector SPDRs XLK/XLF/XLV/XLE/XLU/XLI/XLY/XLP/XLB/XLRE/XLC + MDY/IWM/SCHB/QQQ/TQQQ). Non-ETF tickers rejected with HTTP 400 since v0.15.0.
**What it does:** Analysis only — zero orders sent. Pulls live chain from IBKR, runs a 9+ gate quality framework, ranks strike/expiry for **vertical spreads**, outputs GO/CAUTION/BLOCKED verdict + step-by-step IBKR Client Portal execution guide.
**Four directions:** buy_call (long ITM call, 45–90 DTE), sell_call (bear call spread, delta 0.30/0.15, 21–45 DTE), buy_put (long ITM put), sell_put (bull put spread, delta 0.30/0.15). Sells premium too — unlike Gemini, which is buyer-only.
**Sector rotation:** Consumes STA's relative-strength data to classify ETFs (Leading/Improving/Weakening/Lagging) → suggested direction. SPY 200 SMA regime + broad-selloff detection. If STA offline, sector scan 503s but analysis still works.
**Provider cascade:** IBKR live → IBKR cache (2-min TTL) → Alpaca → yfinance → Mock. All IBKR calls serialized through a single `ib-worker` thread.
**Key files:** `backend/analyze_service.py` (orchestrator), `gate_engine.py` (frozen), `strategy_ranker.py` (spread builder), `constants.py` (single source of truth for thresholds), `iv_store.py` (SQLite IVR from 252d history), `sector_scan_service.py` (STA consumer). Docs in `docs/stable/` (GOLDEN_RULES, ROADMAP, API_CONTRACTS, MASTER_AUDIT_FRAMEWORK).
**Project-local skills (slash-command style, live in `options-iq/skills/`):** `catalyst-check`, `chartreview`, `ibkr-scan` (⚠️ name collides with the hub's in-design STA `skill-sta-ibkr-scan.md` — different skill), `ki` (known-issue logger). These are NOT hub skills — they ship inside the ETF repo.
**Current state:** v0.36.2, Day 70 (Jun 16, 2026). 27 pytest tests, all mock-data (no IBKR needed).

**To run:**
```bash
cd /Users/balajik/projects/options-iq
./start.sh   # backend 5051 + frontend 3050; needs IB Gateway on 4001
```

> ⚠️ **LIVE-READ RULE — non-negotiable:**
> Before making any claim about what `app.py` validates, what fields the schema requires, what TTL is enforced, or what `quant_math.py` computes — **read the live file**. Summarized context goes stale. Session 10 caught a TTL error (documented as 5 min, actual code = 30 min) because the summary was trusted over the code.
>
> **Minimum reads before any Gemini IQ engine work:**
> - `app.py` → grep for the endpoint in question (`/analyze/centaur`, `/analyze/scanner`, etc.)
> - `quant_math.py` → if touching any indicator logic
> - `Docs/CLAUDE_MCP_SKILL_HANDOFF.md` → if touching the Stage 1 → Stage 2 schema
> - `gemini.md` → if touching architecture or adding new gates
> - `handoff_summary.md` → current phase status and recent milestones

**To run:**
```bash
cd /Users/balajik/projects/options_iq_gemini
python app.py          # backend port 5002
cd frontend && npm run dev  # frontend port 5175
```

---

### Swing Trade Analyzer (STA)
**Location:** `/Users/balajik/projects/swing-trade-analyzer/`
**Stack:** Python/Flask (port 5001) + React frontend
**Methodology:** Minervini SEPA + O'Neil CAN SLIM. Categorical assessments (Strong/Decent/Weak). BUY/HOLD/AVOID verdicts.
**Key files:**
| File | Purpose |
|------|---------|
| `docs/claude/CLAUDE_CONTEXT.md` | STA session context — source of truth |
| `docs/claude/stable/GOLDEN_RULES.md` | Core rules + lessons learned |
| `docs/claude/stable/ROADMAP.md` | Canonical roadmap |

**Current state:** Day 77, v4.36. Paper trading phase. All 5 gates cleared. `/ibkr-scan` skill design complete (research done Day 77).

**To run:**
```bash
cd /Users/balajik/projects/swing-trade-analyzer
./start.sh   # starts both backend (5001) and frontend
```

---

## IBKR MCP Reference

**Capabilities doc:** `ibkr-mcp-capabilities.md` — load this whenever building or modifying any skill that uses IBKR MCP.

**Gemini CLI handoff doc:** `options_iq_gemini/Docs/CLAUDE_MCP_SKILL_HANDOFF.md` — load this when testing the Stage 1 → Stage 2 pipeline end-to-end. Defines exact CENTAUR_SCHEMA_v2 payload, field-to-endpoint mapping, confirmed MCP gaps, and Stage 2 checklist. Baked into `options_iq_gemini/PROTOCOL.md` session open/close.

**Dry-run baseline:** NVDA, June 18 2026. 68 fields mapped across 9 categories.

| Dimension | Current state |
|-----------|--------------|
| Total fields mapped | 68 |
| Closed-day safe | 55 (vol regime, technicals, range, portfolio context all work) |
| Live-only | 13 (RVOL, intraday OHLC, live bid/ask, today's option flow) |
| Confirmed gaps | 7 (chain, per-strike Greeks, OI, earnings, fundamentals) |
| MCP tools used | `search_contracts`, `get_price_snapshot`, `get_price_history`, `get_account_positions` |

**Key architectural finding:** IBKR MCP is a per-ticker enrichment layer, not a scanner. It cannot browse the options chain or discover individual OPT contract IDs. Chain resolution stays with Tradier → Options IQ Gemini.

**For Options IQ Gemini (Phase 12 Stage 2):** The MCP handoff block populates the `finalists[TICKER]` fields in the Phase 12 ingestion JSON (`Gemini_Web_Pro_Reference/gemini-code-1781813864206.md`). Fields `mcp_chain_candidate` (OCC symbol, Greeks, bid/ask) still require Tradier.

**Upgrade checklist:** See `ibkr-mcp-capabilities.md` → "MCP Upgrade Checklist" for what to test when IBKR releases a new MCP version.

---

## Key Design Decisions (First Principles)

| Decision | Rationale |
|----------|-----------|
| IVR ≤ 45 hard gate | Above-median IV for this stock's own history = Volatility Tax. Negative EV before the stock moves. |
| IV/HV < 100% edge | IV below realized vol = market underpricing future movement. Debit buyer's mathematical edge. |
| IBKR pre-sorts, Radar hard-filters | IBKR MultiSort floats best tickers but never cuts at IVR 45. Radar enforces the gate. |
| 21–35 DTE window | Options IQ Gemini time horizon (gemini.md). Different from HTML terminal's 21–45. |
| SQUEEZE gate in Centaur Mode | No compression = no kinetic trigger. SQUEEZE: NORMAL → stand down, not flip direction. |
| Stand down is a valid output | If no finalists pass all gates, the correct output is "wait." Not a fallback to weaker setups. |
| Cheap IVR Trap | IVR 10 + IV/HV 165% = trap. IVR measures IV vs own history, not vs realized vol. Check both. |
| Direction aware, not prescriptive | Radar surfaces trend; trader decides call vs put. Never flip direction to force a trade. |
| STA: categorical not numerical | Score-to-return correlation = 0.011 (Day 27 backtest). System is a filter, not a ranker. |

---

## Known Issues / Active Debt

| Priority | Item | Notes |
|----------|------|-------|
| RESOLVED | ONDS micro-cap liquidity flag | Session 11: Sieve 1.5 Gate A added to skill-options-ibkr-radar.md. Session 13: Market Cap ≥ $1B added to IBKR scanner settings — Gate A now a backstop, not primary catch. |
| RESOLVED | Radar footer skips Directional Builder | Session 17 (A1): footer now routes Radar → Directional Builder → Centaur. Radar skill needs web re-upload (Bala, after testing). |
| PENDING (Sonnet) | Radar missing MCP-verify step | Finalists selected on stale scanner data (lag + misread risk). Fix in HANDOFF Task A2. |
| PENDING (Bala) | IBKR TWS — add 2 new scanner settings | Market Cap ≥ $1B + Option OI ≥ 500. Confirm they save. |
| RESOLVED | Scanner watchlist review | Bala approved CORE/EXTENDED tables in skill-options-scanner.md Session 24 (Jul 10, 2026). The first live Scanner run itself did NOT happen that session — confirmed via `options_iq_gemini/trades.db` (zero FWD_TEST rows) + `backend.log` (no POST calls Jul 10) — session cut off before execution. Still pending; see Next Steps. |
| RESOLVED | skill-options-trade-validator Mode 1 trigger | Session 24 continuation (Jul 12): Mode 1 trigger now explicitly names the Gemini Centaur briefing (`# INSTITUTIONAL BRIEFING: ... OPTIONS SYNTHESIS`) as a first-class, primary trigger alongside the HTML terminal and plain-text descriptions. Same fix as the row below — v3 → v3.1. |
| RESOLVED | `skill-options-directional-builder` `room_to_support_pct` sign | Session 17: formula was already correct; added a sign-guard note (nearest_support must be below price → emit null, never a negative). Root cause of the ACN -3.4 was support-above-price on a new low, not a formula bug. |
| MEDIUM | `skill-options-directional-builder` extra schema fields | `risk_flags[]`, `dual_signal_conflict`, and NEW `options_liquidity_proxy` (Session 16) should be formalized in `CLAUDE_MCP_SKILL_HANDOFF.md` as optional fields so Gemini Stage 2 ingestion expects them. Coordinate field shape with Gemini before finalizing. |
| HIGH (finding) | `options_liquidity_proxy` LIQUID can mask a per-contract OI desert | Session 17 live end-to-end test: AFRM proxy = LIQUID (underlying avg opt vol 20,123 = 12,763 call + 7,360 put) but the live Centaur/Tradier pull rejected **184/184** contracts on OI > 500. Underlying option volume != per-strike open interest. Likely amplified by the 21-35 DTE window landing entirely on low-OI weeklies (AFRM monthly Aug 15 = 43 DTE, just outside the window). Lesson: the proxy is directional early-warning only — NEVER treat a LIQUID verdict as "chain is tradeable." Reinforces the Gemini USAR feedback and the coordination item above. |
| RESOLVED (stale) | `options_iq_gemini/app.py:590` `entry_price or 1.0` falsy check | Session 21 Fable pre-launch review found the pattern no longer exists in live `app.py`; verified by grep same session. Housekeeping note added to the Session 21 relay so Gemini closes its own tracker entry. |
| LOW | HTML terminal Canadian ticker error | Maintenance mode — low priority. |
| RESOLVED | Earnings gate 14–20 day hole (Radar + Scanner + PROJECT_INSTRUCTIONS_GEMINI.md) | Session 19 (Fable 5 review): a trade opened at 21–35 DTE holds through day 15–20, but earnings there classified CLEAR ✅ (only 21–35 was checked) — the TBLA failure class, reachable through the gate built to prevent it. Fixed: earnings gate now spans the full 0–35 day hold (new WITHIN HOLD label, <14 days still hard TBLA skip). Also reconciled the block-vs-flag disagreement between the skills and the router doc — both now say "flag, Gemini Stage 2 decides against the actual expiry." |
| RESOLVED | PATH B / CENTAUR JSON IVR-percentile mislabeling | Session 19: Scanner Sieve 1 and Directional Builder's `iv_rank_13w/26w/52w` run on MCP's `implied_volatility_percentile` (not the paste-verified watchlist IV Rank) with no caveat anywhere the value is computed or gated on — AFRM already showed a 34 (Rank) vs 18.3 (percentile) divergence. Added explicit caveat text at the point of computation/gating in both skills + PROJECT_INSTRUCTIONS_GEMINI.md, plus an additive `iv_rank_source: "mcp_percentile_proxy"` JSON field (needs formalizing in `CLAUDE_MCP_SKILL_HANDOFF.md` alongside `risk_flags[]`/`dual_signal_conflict`/`options_liquidity_proxy` — same unresolved coordination item as those). Not fixed: the underlying divergence itself — this only makes it visible, it doesn't calibrate it. |
| RESOLVED | Directional Builder expected-move formula off by 100x | Session 19: `expected_move = price × iv_daily × √28` used `iv_daily` as a percentage number without converting to a decimal fraction — a $100 stock at iv_daily=2.2 computed a $1,164 "expected move" instead of ~$11.60. Fixed: divide `iv_daily` by 100 before use in the formula. |
| RESOLVED | Direction-inference "/5" denominator stale | Session 19: the signal table grew to up to 8 rows (chart signals added in v1.2/1.3) but the AUTO threshold (≥4) and the JSON `direction_signal_count` field still assumed 5 signals — a 4-4 tie out of 8 satisfied both AUTO:BULLISH and AUTO:BEARISH rows simultaneously. Fixed: replaced the fixed count with a dynamic strict-majority rule (bullish/bearish count vs. half of whatever was actually scored this run); an exact tie now correctly falls to MIXED. |
| RESOLVED | Project had no version control | Fable 5 review flagged this as the single largest architectural defect. Fixed same session (Session 19): `git init` + root commit `07d716d` (28 files, excludes `.DS_Store`, `config.js`, and an unrelated PDF swept in by `git add -A`). `.gitignore` extended to cover both. |
| RESOLVED | OPTIONS_SIEVE_SPEC.md was never built (pending since Session 13) | Fable 5 review found the drift it was meant to prevent had become real: Gate C computed two different ways (Radar: screen-based `Last × Average_Volume_Shares`; Scanner: MCP `avg_90d_usd_volume`), and finalist IV/HV qualification differed (Scanner required all 3 finalists <100%, Radar did not). **Fixed Session 19/20:** built `OPTIONS_SIEVE_SPEC.md` as the canonical source; both skills now carry a sync-note header pointing to it; Radar's finalist selection updated to require IV/HV<100% matching Scanner. Gate C's PATH B units are still unverified (needs a live MCP pull) — documented explicitly in the spec as a known gap rather than silently resolved either way. |
| RESOLVED (needs TradingView paste-test) | Pine script: intrabar repaint + same-bar double-flip + Bug B only half-fixed + Session 18 changes broke the Directional Builder's table-row contract + magic numbers in wedge detection | Fable 5 review (Session 19) — all five sub-findings fixed directly in `tradingview/gemini-edge-scanner.pine` and `skill-options-directional-builder.md` (Session 24 continuation, Jul 12): (1) role-reversal mutation and pivot detection both gated behind `barstate.isconfirmed` — zones no longer flip/un-flip on intrabar ticks; (2) the resistance-side promotion condition changed from `lvl <= close` to strict `lvl < close`, so an exact close==level bar can only satisfy one of the two role-reversal loops, not both (was the same-bar double-flip); (3) Bug B/ECHO fallback: new `all_res_pivots`/`all_sup_pivots` arrays (+ a `broken` flag) retain every pivot ever confirmed and re-check the proximity filter every confirmed bar, so a pivot once too far from price to qualify can enter later as price approaches, without resurrecting one already role-reversed; (4) `skill-options-directional-builder.md` (v1.5→v1.6) now explicitly documents the `INSUFFICIENT HISTORY`/`N/A`/`--  (<200 bars)` table states and excludes them from Step 6's direction-inference vote and its scored-signal denominator, instead of risking them being scored as NEUTRAL/BLOCK; (5) the `0.0005` wedge-slope and `0.85` narrowing literals are now named inputs (`i_wslope`, `i_wnarrow`). **Not yet done:** this hasn't been pasted into TradingView and run — no Pine compiler available in Claude Code, so correctness is by careful read, not by execution. Re-test per the existing Next Steps item (PURR/ECHO) before trusting it live, and re-upload the Directional Builder skill to web (manifest unchanged). |
| RESOLVED | Scanner Gate C likely gates on wrong units | Fable 5 review: `avg_90d_usd_volume` may be a 90-day *total*, not a daily average — `ibkr-mcp-capabilities.md` already flagged this uncertainty against NVDA's returned value. **Settled Jul 13, 2026 (first live forward-test Scanner run):** confirmed a **daily average** — the tool's own field description says so explicitly ("Average USD trading volume over the last 90 calendar days"), and NVDA's live value ($32.9B) is only sane as a daily figure (a 90-day total would imply ~$370M/day, far too low for NVDA's real trading volume). The $100M/day Gate C threshold is correctly scaled; no recalibration needed. |
| RESOLVED | Radar requires a VIX regime it has no source for | Fable 5 review finding, fixed Session 24 continuation (Jul 12): added a Phase 0 VIX regime step to `skill-options-ibkr-radar.md`, back-ported from `skill-options-scanner` (Session 13) — MCP pull (`search_contracts`/`get_price_snapshot`) when running in Claude Code, honest `UNKNOWN — VIX unavailable` fallback otherwise (never a silent default to STANDARD). Scan header and Rule 5 updated to match. v2.2 → v2.3. |
| RESOLVED | Watchlist "Gate A pre-satisfied" claim is asserted, never checked | Fable 5 review finding, verified and fixed Session 24 continuation (Jul 12): live web search **confirmed HIVE currently trades below the $1B floor** (~$790–900M as of this check — small-cap crypto miners are volatile, "curated once" ≠ "safe forever") and POET has dipped sub-$1B as recently as mid-June 2026 though currently above it. Not just documented — `skill-options-scanner.md` now carries an explicit per-run Gate A market-cap check for these two specifically (MCP `misc_statistics`, purge as `GATE_A_MICROCAP` if < $1B), rather than trusting the curation-wide exemption for names known to sit near the line. v2.1 → v2.2. **Still open for Bala:** decide whether to keep HIVE on CORE given it's currently failing the gate it's supposed to be pre-cleared on, or cut/downgrade it — that's a watchlist-content call, not something to resolve unilaterally in code. |
| RESOLVED | Trade Validator coupled to a dead system and a dead data source | Fable 5 review finding, fixed Session 24 continuation (Jul 12): (1) Mode 1's trigger and required-inputs section named only the maintenance-mode HTML terminal — now explicitly covers three input shapes (Gemini Centaur briefing / HTML terminal / plain-text description), with a field-by-field table built from a live read of `options_iq_gemini/app.py`'s actual briefing output (both the deterministic-fallback and real-Gemini-LLM paths) showing which fields Gemini's briefing does NOT provide (Gamma, Vega, IV%, HV30, terminal score, breakeven) so the validator states "not provided" instead of fabricating a plausible number, and computes what it can (DTE, breakeven) instead of requiring it be pre-supplied; (2) Mode 1 search #4 no longer queries Market Chameleon by name (Session 12 already found it, Barchart's IV page, and Barchart's API all JS-rendered/401) — now falls back honestly to "IVR not available" + the IV-vs-HV30 comparison alone, rather than a search guaranteed to fail silently. v3 → v3.1. |
| RESOLVED | SKILL_MAP.md stale in ≥3 places | Fable 5 review finding, fixed Session 24 continuation (Jul 12): fully regenerated from the live skill files rather than patched — all 4 versions corrected (Radar v2.3, Scanner v2.2, Directional Builder v1.6, Trade Validator v3.1), the stale "Radar footer pending" and "room_to_support_pct known bug" notes removed (both resolved Session 17), the "5 signals" direction-inference count updated to "up to 8, dynamic strict-majority" (Session 19 fix), and the missing 6th skill (`skill-cross-repo-fix-verification.md`, built Session 20) added — it wasn't in the map at all. |
| RESOLVED | PERSONA.md's concrete critique is 8 sessions stale | Fable 5 review finding, fixed Session 24 continuation (Jul 12): the "Standing Critique" section now explicitly says it gates the skills architecture, relabels the old HTML-terminal critique as historical/reference-only, and points to `CLAUDE_CONTEXT.md`'s Known Issues table as the living critique of the current architecture — instead of duplicating that table's contents here (which would just create a second copy that goes stale the same way). |
| RESOLVED | Scanner's `contract_id` cache instructs itself to "edit this file" | Fable 5 review finding, fixed Session 24 continuation (Jul 12): the instruction now says explicitly this only works in Claude Code against the local repo file (which it can edit) — on claude.ai, an uploaded skill is read-only, so there's no file to persist the cached value into. Every claude.ai run resolves `contract_id` fresh; documented as an accepted extra MCP call, not a bug. No version bump (doc clarification only, no logic change — same precedent as Session 20's sync-note header addition). |
| RESOLVED (cross-repo) | Most of the CENTAUR_SCHEMA_v2 payload was silently dropped by Options IQ Gemini's `/analyze/centaur` | Session 19: a field-by-field trace against the live `app.py` found ~18 of ~30 CENTAUR fields silently unused, incl. `iv_hv_ratio` (the core edge) and `trade_direction`. Work order (`HANDOFF_gemini_contract_hardening.md`) handed to Gemini's own dev session — nothing edited from this repo. **Verified fixed by direct code read + running the tests myself** (not by trusting Gemini's summary): `iv_hv_ratio >= 1.0` and `IVR > 45` now hard-reject with `EDGE_VIOLATION`, `trade_direction` filters the option chain (double-enforced), `portfolio` is traced all the way into the Gemini prompt, `jsonschema` validation is live on ingest, and `test_centaur_contract.py` genuinely passes 3/3 when run. |
| PARTIAL — proxy validated, real IV/HV still untested | Core edge (IV/HV mispricing) had never been backtested anywhere in either project | Gemini's own first pass (`options_edge_backtest.py`, Phase 13) tested a *different* signal (momentum/kinetic timing) on 5 cherry-picked mega-caps and claimed "mathematically proved" — overstated (see pushback sent to Gemini, not reproduced here). A refined version was built and actually run: `research/options_edge_backtest_v2.py` + `research/backtest_v2_trades.csv` (1,230 trades, real universe = the hub's own CORE watchlist, 2019–2024, regime-segmented, with a random-entry control and an approximate Black-Scholes payoff instead of a threshold heuristic). **Real finding, not just a bigger number:** a realized-vol-compression proxy for IV/HV is where the edge actually concentrates (compressed: 56.7% win, +31.8% mean, holds under a pessimistic IV-crush scenario; non-compressed: worse than random) — while the 200d trend filter *alone* is statistically indistinguishable from random entry. 2022 bear regime was a wipeout (n=9, mean −53%), consistent with first-principles expectations for long premium in a downtrend. Also caught and fixed a real look-ahead bias in Gemini's original harness (filled at signal-day close using same-day volume; v2 fills at next-day open). **Still not resolved:** realized vol is not real implied vol (richer real premiums likely mean worse real returns than modeled); the universe is survivorship-biased by construction; only the long-call side has any coverage — the bearish/put side of the engine has zero backtest evidence in either version. |
| RESOLVED (cross-repo) | `IBKR_VERIFIED` string default masks missing IVR data as pre-verified good data | Session 20: sharpened via STA's `GOLDEN_RULES.md` ("return null, not a plausible fake" — Day 54). Original bug: `iv_rank = vol_data.get("iv_rank_52w", "IBKR_VERIFIED")` in `analyze_centaur` — a silently-absent field defaulted to a string that *reads as confirmation that verification happened*, broader than the already-fixed IVR>45 hard gate (which only covers the value-present-but-fails-threshold case). Gemini fixed this independently (Phase 14, "Session 21 Relay Application," Jul 6) off its own read of `GEMINI_STATE_HANDOFF.md` — ahead of the hub's own relay batch, which was still marked "not yet sent." **Verified fixed by direct code read, Session 23** (not accepted on Gemini's summary alone): `options_iq_gemini/app.py` lines 811-826 now do `float(iv_rank)` and return `400 MISSING_IVR` on a missing/non-numeric value; the sentinel string is gone from that path. Backed by `test_session21_relay.py` (mocked, schema-on and schema-off paths). |
| HIGH (finding, confirmed) | Tradier `fundamentals/calendars` endpoint returns 404, not a token problem | Jul 13, 2026: ran `test_tradier_calendar.py` for real (this was queued since Session 19/20 as "the moment the token is refreshed, run this"). Result: **HTTP 404 "Resource not found"** — not 401, so this isn't the dead-token issue tracked since Jul 5. The account simply doesn't have the Fundamentals Beta product enabled; `get_earnings_date()` in `app.py` will always fall through to the `EARNINGS_UNKNOWN` sentinel on this account regardless of token state (already hardened to fail loud, per the Jul 1 fix — it doesn't silently bypass the TBLA gate, it just never has real data to give it). Refreshing the token will not fix this; it needs Bala to check whether the Tradier plan can add Fundamentals Beta, or the pipeline needs to accept that Gemini-side earnings verification is permanently unavailable and rely entirely on the hub skills' own web-search-based earnings check upstream. |
| RESOLVED (superseded) | `get_option_data` MCP tool is intermittent, not simply down or up | Jul 13, 2026: 15/15 failures during the first live forward-test Scanner run. Jul 15, 2026, Session 26, two different results in the same session: 4/4 clean at ~09:15 ET (AFRM/GDX/OKLO/NIO), then 5/5 failed at ~14:30 ET (CCJ/MP/URA/XLF), with `get_price_snapshot` on the identical CCJ contract succeeding immediately after — confirming the failure is isolated to `get_option_data` specifically, not a session/auth problem, and that it flips between working and failing within a single day. **Root cause still unconfirmed, but now moot for this pipeline:** Bala suggested calling Tradier directly instead of fighting IBKR MCP's intermittency. Confirmed the Tradier token is alive for `/markets/quotes` and `/markets/options/chains` (the Fundamentals Beta gap is calendar-only, doesn't touch chains). **Tradier is now the primary chain-data path for the forward test** (`FORWARD_TEST_PROTOCOL.md` updated); IBKR MCP `get_option_data` demoted to fallback. |

---

## Session History

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

### July 13, 2026 — Session 25
**The actual first live forward-test Scanner run — real survivors found, then a hard infrastructure blocker stopped contract construction cold.**
- **Tradier verified functionally, for real this time:** ran `test_tradier_calendar.py` (queued since Session 19/20). Result: **HTTP 404**, not 401 — this account's Tradier plan doesn't include the Fundamentals Beta product. `get_earnings_date()` will always fall through to `EARNINGS_UNKNOWN` here regardless of token state. Corrected the long-standing "pending token refresh" framing — refreshing the token was never going to fix this.
- **Ran PATH B Scanner live, both tiers, for the first time ever:** VIX 16.25 (STANDARD regime) via IBKR MCP. **CORE (20 names): 0 survivors** — every single name failed Sieve 1 (IVR > 45%); NVDA (46.8%) and ALB (47.2%) closest, but both also independently fail Sieve 2b, so no clean near-misses either. Per the Scanner's own trigger rule (<3 finalists → scan EXTENDED), continued to **EXTENDED (44 of 45 resolved — ABB unresolvable; discovered `search_contracts` silently empties on multi-word "TICKER Name" queries, ticker-only works reliably): 2 survivors, 2 clean near-miss rejects.** Survivors: **AFRM** (IVR 13.6%, IV/HV 90.1%, uptrend, Gate C $413.8M/day) and **GDX** (IVR 44.4% — provisional/near the cutoff, IV/HV 78.8%, downtrend, Gate C $1.63B/day). Near-miss rejects (failed exactly one gate — Sieve 2b IV/HV): **OKLO** (IVR 35.2%, IV/HV 109.8%) and **NIO** (IVR 18.4%, IV/HV 113.0%).
- **Resolved a real open question along the way:** Session 19 flagged `avg_90d_usd_volume` as possibly a 90-day total rather than a daily average (which would make Gate C's $100M threshold off by ~90x). Settled with live data: it's a daily average — the tool's own field description confirms it, and NVDA's live $32.9B figure only makes sense as a daily number.
- **Surfaced a real protocol gap:** no monthly expiry fell inside 21-35 DTE this cycle (nearest monthly was 39 DTE) for any of the four candidates, since they share an identical options calendar. Asked Bala rather than deciding unilaterally — chose "use the nearest weekly inside the window" (Aug 7, 2026, 25 DTE) as the standing rule going forward. `FORWARD_TEST_PROTOCOL.md`'s "nearest monthly" language may need amending if this recurs.
- **Then hit a genuinely hard blocker: `get_option_data` failed 15/15 times.** Methodically ruled out three explanations rather than assuming the first one: (1) not a parameter mistake — varied ticker/expiry-type/strike-range across attempts, identical generic error every time; (2) not Claude-Code-specific — found two real, relevant bugs on Anthropic's own GitHub trackers (`claude-code#69917`, an OAuth path-mismatch specific to Claude Code vs. Claude Chat; `claude-ai-mcp#405`, IBKR token-expiry with no reconnect) that looked like promising explanations, but Bala independently reproduced the identical failure on claude.ai web chat, which rules both out — those bugs describe total connector failure, not this selective single-tool pattern; (3) not a stale `expiration_id` — re-fetched fresh immediately before a final retry, got a byte-for-byte identical id, still failed. `search_contracts`, `get_price_snapshot`, `get_option_parameters` all worked fine throughout, including the fresh re-fetch. Real, isolated, cross-environment failure with no root cause identified past "something in IBKR's final chain-lookup step, not a session/auth/parameter issue on our side."
- **Held the line on honesty over forcing a result:** did not fabricate a contract, quote, or premium to produce a forward-test log entry. Recorded the real Scanner data (both survivors and near-miss rejects, with all computed gate values) in `forward_test_log.csv` with `resolution=LOGGING_BLOCKED` and a precise note on what failed and why. This is exactly the discipline the forward-test protocol's own honesty rules were written to enforce.
- Two commits this session: Scanner run + findings (`ea94ff7`), plus this close.

### July 12, 2026 — Session 24 continuation
**Cleared the entire Session 19 Fable 5 review backlog — every remaining "finding, unfixed" row in Known Issues is now RESOLVED.**
- User asked "what's next," got a prioritized list, then said "keep going" three separate times rather than scoping the work item-by-item — worked the backlog in order: Pine script bugs (HIGH) → Trade Validator dead couplings (MEDIUM) → SKILL_MAP/PERSONA staleness (LOW) → Radar's VIX source (MEDIUM) → Scanner's contract_id self-edit note (LOW) → watchlist Gate A claim (MEDIUM).
- **`tradingview/gemini-edge-scanner.pine`** — all 5 sub-findings fixed: `barstate.isconfirmed` gating on all S/R zone mutation (was repainting on every intrabar tick); the resistance-break promotion condition changed from `lvl <= close` to strict `lvl < close` so an exact close==level bar can't satisfy both role-reversal loops in the same bar (was the double-flip); new `all_res_pivots`/`all_sup_pivots`/`all_*_broken` arrays let a pivot once rejected by the 25% proximity filter re-enter later as price approaches it, without resurrecting one already role-reversed (Bug B/ECHO fallback); `0.0005`/`0.85` wedge-detection literals promoted to named inputs. **Honest caveat, repeated because it matters:** no Pine compiler is available in Claude Code — this is verified by careful read, not by execution. Still needs the TradingView paste-test already queued in Next Steps before being trusted live.
- **`skill-options-directional-builder.md` v1.5→v1.6:** the Pine script's `INSUFFICIENT HISTORY`/`N/A`/`--  (<200 bars)` table states (added Session 18, but never given a home in the Directional Builder's Step 6 scoring contract) are now explicitly excluded from the direction-inference vote and its scored-signal denominator, instead of risking them being counted as NEUTRAL/BLOCK.
- **`skill-options-trade-validator.md` v3→v3.1:** read `options_iq_gemini/app.py` live to build an accurate field-availability table for Gemini's actual Centaur briefing output (both the deterministic-fallback and real-LLM paths) — it does NOT contain Gamma, Vega, IV%, HV30, or a terminal score, so the validator now says "not provided" instead of risking a fabricated plausible number. Market Chameleon IVR search replaced with an honest fallback (Session 12 already found it dead).
- **`SKILL_MAP.md`** fully regenerated from the live skill files rather than patched — 4 stale versions corrected, two false "pending"/"known bug" notes removed (both actually resolved Session 17), the direction-inference signal count corrected (was "5", is "up to 8, dynamic strict-majority" since Session 19), and a whole 6th skill (`skill-cross-repo-fix-verification.md`) added that wasn't in the map at all.
- **`PERSONA.md`:** relabeled the old v3.1-HTML-terminal critique as historical/reference-only and pointed the active critique at `CLAUDE_CONTEXT.md`'s Known Issues table instead of duplicating it — avoids recreating the exact staleness this fix was responding to.
- **`skill-options-scanner.md`:** two fixes. (1) The `contract_id` cache's "edit this file" instruction now states plainly it only works in Claude Code (local file, editable) — not on claude.ai (uploaded skill, read-only) — documented as an accepted extra MCP call there, not a bug. (2) **Live web search confirmed HIVE currently trades below the $1B watchlist floor** (~$790–900M) and POET dipped sub-$1B as recently as mid-June — the "Gate A pre-satisfied by curation" claim was asserted but never actually checked. Added a per-run live market-cap check for these two specifically (v2.1→v2.2). **Left open for Bala:** whether to keep HIVE on CORE given it's currently failing its own pre-clearance gate, or cut/downgrade it.
- **`skill-options-ibkr-radar.md` v2.2→v2.3:** back-ported the Phase 0 VIX regime pull from Scanner (fixed there Session 13, never ported) — MCP pull when available, honest `UNKNOWN — VIX unavailable` otherwise; Radar previously had no VIX source beyond "if the user happens to mention it."
- All four touched skills need web re-upload (manifests unchanged) — added to Next Steps alongside the existing queue.

### July 10–11, 2026 — Session 24
**Resumed after an abrupt mid-session interruption; verified the "first live Scanner run" implied by the interrupted session's own edit never actually happened.**
- Session was interrupted before closing. Uncommitted at resume: `SKILL_CONVERSION_SCOREBOARD.md` (new file, measurement-only pass on how much of each skill's logic is deterministic Python-able vs. genuine LLM judgment — 0% converted anywhere, this was scoring not conversion) and a Known Issues row flip (Scanner watchlist CORE/EXTENDED tables approved by Bala).
- That row's wording implied the first live Scanner run followed the approval. Didn't assume it — checked directly: `options_iq_gemini/trades.db` has zero `FWD_TEST` rows and no new paper-trade entries since PLTR closed Jun 26; `backend.log` shows only `GET /tradier/ping` and `GET /journal/history` on Jul 10, no `POST /journal/log` or `POST /analyze/centaur`. **The first live run never happened** — session cut off between watchlist approval and execution. Corrected the Known Issues row so it no longer implies otherwise.
- **Real finding surfaced by that check:** the Jul 10 `/tradier/ping` call returned success — confirmed by reading `app.py:1111-1141` directly, where 200 only comes back on the actual success branch (profile fetched, account ID extracted), not a swallowed error. First sign of life from the Tradier token since it went dead ~Jul 5 (the #1 blocker tracked since Session 19/20). Not yet treated as fully resolved: a ping only proves auth works, not that chain pulls or the earnings calendar endpoint do — that still needs `test_tradier_calendar.py` or a live `/analyze/centaur` call.
- Today (Jul 11) is a Saturday — market closed, so no live IBKR/Tradier run is possible right now. The actual first live Scanner run (and the Tradier functional check) is deferred to the next trading day, Monday July 13.
- Closed properly this time: header rewritten, Known Issues row corrected, this entry added, changes committed.

### July 10, 2026 — Session 23
**Verified Gemini's own status-summary claims against live code; confirmed FWD test hasn't started.**
- User pasted Gemini's session-open summary (WhatsApp audit takeaways, forward-test mandate, `IBKR_VERIFIED` bug, skill versions) and asked whether the hub agreed. Checked each claim against source rather than accepting the summary — gate-replay numbers, skill versions, and FWD_TEST tagging rule all confirmed accurate.
- **`IBKR_VERIFIED` claim confirmed true by direct read of `options_iq_gemini/app.py:811-826`:** Gemini already applied the fix (Phase 14, "Session 21 Relay Application," Jul 6) — `analyze_centaur` fails loud with `400 MISSING_IVR` instead of the old sentinel. This closed a stale gap: the hub's own Known Issues table still said "unfixed" and the relay batch still said "not yet sent," even though Gemini had read the handoff and fixed it independently. Known Issues row flipped to RESOLVED; relay checklist item (2) marked moot.
- **Forward test:** user confirmed directly it has not started — no live read needed this session. Gemini's phrasing ("the hub is running a forward test") was ahead of reality; left as an open item, not corrected in the hub's own files (nothing to fix, it's Gemini's phrasing, not this repo's).

### July 9, 2026 — Session 22
**Orientation/status-check only. No deliverables.**
- User asked "where are we" — answered from a live read of `CLAUDE_CONTEXT.md` (Project Identity, Known Issues, Session History, Immediate Next Steps), not from memory.
- Checked `research/forward_test/forward_test_log.csv` directly: still only the header row — no forward-test entries logged, despite the Session 21 addendum setting Tue Jul 7 as the earliest date for first real entries.
- **Left open, not resolved:** whether the forward test actually started inside Gemini's own paper-trade journal (positions live there via API, not in this repo's CSV) — would need a live read of `options_iq_gemini/database.py` / a `/journal` query to confirm. Flagged to the user rather than assumed.
- `git status` clean at session start and close — nothing else changed.

### July 5, 2026 — Session 21
**WhatsApp signal-group review (764 signals verified against real prices) + gate-replay experiment + survivors-vs-rejects forward test designed.**
- **Reviewed the "Traders - Seriously ☺️" WhatsApp export** (21,634 messages, Jun 2023–Jul 2026) via full parse + independent price verification (yfinance, 324 tickers) — never trusting chat-claimed outcomes. Deciphered method: discretionary long-only S/R swing trading (2-tier accumulation entries, resistance targets +21%, day-close support stops −12%, R:R ~1.8:1) plus vol-blind near-ATM call buying (median 15 DTE, zero IV/IVR mentions in 3 years). No formal grading system exists — "safe/risky traders" exit tiers + analyst-rating screenshots.
- **Verified performance:** stocks 50.0% win to first target (164W/164L), +5.2%/trade expectancy — but a random-entry control on the same tickers/geometry won 53.3%: no selection skill, all structure + bull beta (SPY +77% same window). Options: 35% plausibly profitable, 46% expired worthless (intrinsic proxy, 196 verifiable), EV ≈ 0 before costs. Reporting bias: 157 win-claim messages vs ~2 genuine loss admissions. Deliverables: `research/WHATSAPP_SIGNALS_REVIEW.md` + `research/whatsapp_signals_dataset.csv` (629-row labeled test set).
- **Gate-replay experiment (review §8):** replayed their 254 option signals through the hub's stack (proxy definitions copied verbatim from `options_edge_backtest_v2.py`). Full stack refuses 121/121 evaluable single-name signals (DTE 21–35 alone blocks 72%) — blocks 60/60 worthless expiries but also 40/42 winners. **Honest reading: the stack is validated as a refusal mechanism; within-flow discrimination remains unproven** (survivors n=8 did worse than baseline). Superiority over the group: proven on process, still unproven on outcomes (our evidence remains backtest_v2 + 6 paper trades 1W/5L).
- **Forward test designed (`research/forward_test/FORWARD_TEST_PROTOCOL.md`):** the discrimination evidence generator — log daily Scanner survivors AND up to 3 near-miss rejects (control group), score both identically (target touch / day-close stop / DTE×0.60 time stop / expiry). Stand-down days count as data; never force top-3 (that would rebuild the group's always-a-signal machine). Positions live in **Gemini's paper-trade journal** via API (`/journal/log|monitor|close` — schema and endpoints live-read from `app.py`/`database.py` first): `/journal/monitor` automates daily marks (delta kill-switch, gamma-surge trail, stagnation flag). Mandatory `FWD_TEST:SURVIVOR|`/`FWD_TEST:REJECT|` prefix in `setup_context` keeps control rows out of Gemini's own performance record. Hub CSV holds only stand-down days + analysis exports. **Pre-registered success criterion** (survivors beat rejects, CI excluding zero) written down before first entry; 30-resolved-per-group ≈ mid-September. Realistic yield ~10–20 unique setups/3 weeks after dedupe, not 45.
- **Borrowed from the group (only surviving items):** R:R ≥ 1.5 floor (trialed in the forward test before formalizing in Directional Builder), day-close stop discipline (candidate for `OPTIONS_SIEVE_SPEC.md` exit language), GOLDEN_RULES candidate: "a bull market does not rescue short-dated long calls — 46% of a 196-trade retail sample expired worthless while SPY rose 77%."

### July 5, 2026 — Session 20
**Closed the OPTIONS_SIEVE_SPEC.md gap (pending since Session 13) + reviewed Gemini's real schema file + consolidated the end-to-end pipeline doc.**
- **Reviewed `options_iq_gemini/Docs/CENTAUR_SCHEMA_v2.json` directly** (Gemini's real implementation, not assumed from the handoff doc draft) — confirmed it faithfully matches what was recommended: required fields, nullable fields, and every enum checked against the hub's actual skill output (`trend_label`, `range_52w_label`, `price_source`). One minor non-blocking gap: no `additionalProperties: false` anywhere, so a typo'd field name would be silently ignored rather than caught.
- **Built `OPTIONS_SIEVE_SPEC.md`** — the canonical sieve/gate spec that's been pending since Session 13. Re-verified the two real divergences a live audit found (not re-derived from memory): Gate C computed two different ways (Radar: screen `Last × Average_Volume_Shares`; Scanner: MCP `avg_90d_usd_volume`, units unverified) and finalist IV/HV qualification differing between paths (Scanner required <100% on all 3, Radar didn't). Documented Gate C's divergence explicitly as an open question (PATH A trusted more until PATH B's units are settled with a live MCP pull) rather than picking a side without evidence. **Fixed** the finalist-qualification divergence by updating Radar to match Scanner's explicit IV/HV<100% requirement (Radar bumped v2.1 → v2.2). Added a one-line sync-note header to both Radar and Scanner pointing at the new spec.
- **Consolidated the full end-to-end pipeline into `CLAUDE_CONTEXT.md`'s own pipeline section** — previously the workflow only existed in pieces (this file's old PATH A/B diagram stopped at the Gemini handoff; `options_iq_gemini/PROTOCOL.md`'s funnel diagram stopped at "Live Position Management" without saying what that means). The rewritten section now includes the hardened Centaur ingestion gates (verified working, not assumed), the fact that execution and stop-loss monitoring are entirely manual (no order-placement code exists in `options_iq_gemini`), and a pointer to the backtest evidence and its sizing implications.
- **Verified Gemini's `STATE_HANDOFF.md` automation, twice, by running it — not reading it.** Round 1: confirmed the concept was real (source docs, e.g. `AUDIT.md`, actually got corrected per earlier pushback, not just new tooling layered on old claims) but found three real gaps by testing, not guessing: running the generator from `scripts/` instead of the repo root silently produced a broken file while printing a success message; `Docs/CENTAUR_SCHEMA_v2.json` review was clean; Section 4 of the generated file had a hardcoded "Tradier expired" string that would never self-update. Drafted and the user relayed a pushback with working code fixes (path-anchoring via `__file__`, fail-loud exceptions, moving the Tradier fact into `KNOWN_ISSUES.md` as a real tracked entry). Round 2: re-ran all three tests directly against the fixed code (bad cwd, bad marker, missing file) — all pass. Caught one remaining inaccuracy (Phase 13 conflated "TTM Squeeze" with the separate realized-vol-compression proxy that actually drove the backtest edge) — corrected on the same round-trip, verified landed in both `history.md` and the regenerated `STATE_HANDOFF.md`.
- **Built the hub's own mirror: `scripts/generate_gemini_handoff.py` → `GEMINI_STATE_HANDOFF.md`.** Applies the lessons from reviewing Gemini's version directly: path-anchored to the script's own location, fails loud (non-zero exit, no overwrite) on a missing file or a Known-Issues-table/Session-History header that's changed shape, and nothing hardcoded that actually changes over time. Verified the same way Gemini's was verified — ran it from the wrong directory, and simulated both failure modes directly against real files rather than trusting a read-through. Caught and fixed one design bug during testing: the naive cross-repo-issue filter surfaced an already-RESOLVED row under an "Open" heading. Drafted the one-line `AGENTS.md` addition needed on Gemini's side to actually read this file at session open — user will relay, nothing edited in `options_iq_gemini`.
- **Formalized `skill-cross-repo-fix-verification.md`** — the "don't trust the summary, read the live code, run it, check for silent-failure/hardcoded-content/path-fragility/overstated-language patterns" procedure had repeated three times this session; turned it into a reusable skill rather than re-deriving the checklist each time. Manual invocation only for now (`@`-reference or ask directly) — not registered as an auto-triggering Claude Code skill.
- **Adopted `GOLDEN_RULES.md` from STA's own golden rules, curated not copied.** Kept what independently validates or sharpens existing findings (STA's "VIX=20 on failure" ≈ this project's own VIX Kill-Zone bug; STA's "return null, not a plausible fake" sharpens the `IBKR_VERIFIED` masking issue into its own tracked Known Issues row, separate from the already-fixed IVR>45 gate; STA's "dual endpoints diverge silently" ≈ the Gate C divergence `OPTIONS_SIEVE_SPEC.md` closed). Adopted the 5-type audit taxonomy (Claim/Coherence/Behavioral/Design/External) as shared vocabulary for scoping future review requests. Explicitly rejected three STA rules that conflict with how this hub actually operates or with a harder standing rule (one-file-at-a-time generation, autonomous git commits without asking, flat-API-structure preference) — recorded with reasoning, not silently ignored.

### July 4, 2026 — Session 19
**Fable 5 critical review (project + skills + Pine) + fixed the 4 highest-severity findings.**
- Ran a full GOOD/BAD/IMPROVEMENTS review via a background agent on `claude-fable-5` — read CLAUDE_CONTEXT.md, PERSONA.md, all four active skills, and `gemini-edge-scanner.pine`. Full review published as an artifact; findings logged into Known Issues above (RESOLVED entries for what was fixed this session, HIGH/MEDIUM/LOW "finding, unfixed" entries for everything deferred).
- **Fixed 4 bugs with real trading-decision impact** (user chose "critical bugs only" scope over the full 20+-item list):
  1. Earnings gate 14–20 day hole in Radar + Scanner + `PROJECT_INSTRUCTIONS_GEMINI.md` — earnings between the TBLA cutoff (14 days) and the 21–35 selection window start (day 21) were silently classified CLEAR ✅ despite falling inside the trade's hold. New WITHIN HOLD label covers the full 0–35 day exposure window. Also reconciled a real disagreement: the router doc said "no trade," the skills said "flag" — both now say flag, Gemini Stage 2 decides against the actual chosen expiry.
  2. PATH B / CENTAUR JSON silently emitted MCP's `implied_volatility_percentile` as `iv_rank_52w` — a metric the project's own memory already proved diverges from the real IBKR watchlist IV Rank (AFRM: 34 vs 18.3). Added explicit caveats at the point of computation and gating in Scanner + Directional Builder + the router doc, plus an additive `iv_rank_source: "mcp_percentile_proxy"` JSON field. This makes the divergence visible, it does not calibrate it away — PATH A (paste) remains the authoritative source.
  3. Directional Builder's expected-move formula (`price × iv_daily × √28`) was off by ~100x — `iv_daily` is a percentage number, not a decimal fraction, and the formula never converted it. Fixed with an inline units comment and the wrong-vs-right numeric example.
  4. Direction-inference scoring's AUTO threshold and JSON `direction_signal_count` still assumed a fixed 5-signal table after it grew to 8 rows (chart signals added in v1.2/1.3) — a 4-4 tie could satisfy both AUTO:BULLISH and AUTO:BEARISH simultaneously. Replaced with a dynamic strict-majority rule.
- Versions bumped: Radar v2 → v2.1, Scanner v2 → v2.1, Directional Builder v1.4 → v1.5. **All three need re-upload to web** (see Next Steps).
- **`git init` done later the same session** (initially deferred, then explicitly requested): root commit `07d716d`, 28 files. `git add -A` swept in an unrelated PDF under `Frameworks/` (a "TicketTransaction" receipt, not project content) — caught before committing, excluded, and added to `.gitignore` alongside `.DS_Store`. Git auto-assigned committer identity from username/hostname; set `git config --global user.email` before ever pushing this repo anywhere.
- **Deliberately not fixed this session** (logged as findings, not resolved): `OPTIONS_SIEVE_SPEC.md` still unbuilt, Scanner Gate C's likely wrong units (needs a live MCP data pull to settle before recalibrating — couldn't do inline), Radar's missing VIX source, the unverified sub-$1B watchlist names (HIVE/POET), Trade Validator's dead-terminal/dead-search coupling, SKILL_MAP.md and PERSONA.md staleness, the Scanner `contract_id` self-edit instruction, and the full set of Pine script bugs (repaint risk, double-flip, half-fixed Bug B, broken Session-18-to-Builder contract, magic numbers) — the Pine fixes specifically need a TradingView re-test after editing, which wasn't in scope for this pass.

### July 4, 2026 — Session 18
**Pine v6 Bug A + Bug B fixed. First-principles S/R review.**
- **S/R quality review (Alex + 30-year trader lens):** Identified two fundamental flaws in the original approach: (1) delete-only pruning violated role reversal — the most important S/R principle; (2) one-touch pivots treated equally regardless of confluence. Decided role reversal was the correct Bug B fix, superior to the three OPUS_HANDOFF options (re-arm/fallback/flag).
- **Bug A fixed (`gemini-edge-scanner.pine` → still v6):** `no_ema200 = na(e200)` flag guards `trend_str` (→ "INSUFFICIENT HISTORY"), `gate_call`/`gate_put` (→ "N/A" gray), `sl200` (→ "--"), EMA 200 table cell (→ "--  (<200 bars)"). 52W line drawing guarded against `na(high_52w)`/`na(low_52w)` — prevents runtime crash on < 252-bar charts. Fixes the PURR false BLOCK/BLOCK.
- **Bug B fixed:** `f_make_zone` updated to accept `left_bar` parameter — pivot zones use `bar_index[i_pr]`, role-reversed zones use `bar_index` (marks the crossover bar). Pruning block rewritten: when resistance ≤ close, delete red box and promote level to support (green box); when support ≥ close, delete green box and promote to resistance (red box). Distance eviction applied to the receiving array when at cap of 3. Fixes ECHO S1 = 52W Low; intermediate shelves now survive as green support after breakout.
- **Pending:** Bala to paste updated script into TradingView and test PURR (INSUFFICIENT HISTORY) + ECHO (intermediate green supports visible).

### July 3, 2026 — Session 17
**First full end-to-end pipeline run in one session (Radar -> Directional Builder -> live Centaur POST) + 3 quick fixes + Pine live-test on 4 names.**
- **Three quick fixes from the Sonnet handoff (Task A partial):** (A1) Radar footer no longer skips Directional Builder — replaced the "Open Options IQ Gemini / CENTAUR HANDOFF" block with the correct DIRECTIONAL BUILDER HANDOFF. (A5) Unified the Cheap IVR Trap number to **IVR 10 / IV/HV 165%** across `CLAUDE_CONTEXT.md` + `PROJECT_INSTRUCTIONS_GEMINI.md` (were "IVR 9") to match the skill. Added a sign-guard note for `room_to_support_pct` (formula was already correct — RESOLVED). **Radar skill needs re-upload to web** (footer change; manifest unchanged = replace).
- **Pine v6 live-test (NVDA, ECHO, PURR, AFRM):** prior fixes held (RVOL uses last completed bar; no red zones below price). **Two new bugs logged in `tradingview/OPUS_HANDOFF.md`:** Bug A (real, quick) — NaN EMA200 on < 200-bar names (PURR) forces a false CALL+PUT BLOCK; needs an `na(e200)` guard -> "INSUFFICIENT HISTORY". Bug B (design decision) — on parabolic movers (ECHO) S/R collapses to the 52W extremes because pruning permanently deletes broken levels; options: re-arm broken levels / widen proximity fallback / flag the empty state.
- **Radar run on a 15-row IBKR paste:** top 3 = ECHO / PURR / AFRM (PURR flagged borderline; CDE the clean alternate). Purged RILY (Gate A), RXRX/PPTA/STUB (Gate C), BTG (IV/HV > 100%).
- **Directional Builder chart-read caught a trap:** ECHO ranked #1 on IV/HV (69.4%) but the chart showed a fresh ~30% crash — its "deep edge" is a **realized-vol-spike artifact** (crash inflated HV, depressing IV/HV), not a true mispricing. Stand down. PURR disqualified (< 200 bars, tool can't read it). AFRM = the only clean CALL (but extended, RSI 69.5, at R1).
- **Full live pipeline on AFRM:** pulled IBKR MCP (contract 465119069), computed technicals from 252 daily bars (EMA stack BULLISH, RSI 69.5, ATR 4.14 — all matched the Pine dashboard; **TTM squeeze NOT_FIRING**, BB width 37%). Live-verified IV/HV 88.3% (BUYER_EDGE) and confirmed the **IVR-vs-percentile divergence live** (watchlist Rank 34 vs MCP percentile 18.3% — use the Rank). No AFRM position (CLEAN_ENTRY). Built a correctly-shaped CENTAUR payload — **live-read of `app.py:732` caught that the endpoint reads `price_last`, not `price`** — and POSTed to `localhost:5002/analyze/centaur`.
- **Verdict: STAND DOWN (correct).** Centaur pulled the Tradier chain and rejected 184/184 contracts (all failed OI > 500). Two independent stand-down reasons converged (no squeeze + dead chain). Gemini's LLM was never called — the chain gate short-circuits at `app.py:749` before synthesis, so no API spent on a DOA chain.
- **Key finding logged (Known Issues):** `options_liquidity_proxy` = LIQUID but the chain was an OI desert — the proxy is directional only, never proof a chain is tradeable. Likely the 21-35 DTE window landing on low-OI weeklies.
- **Green-path validation deferred:** market closed July 3 (Independence Day observed). A live Centaur POST would false-reject on stale closed-market spreads before reaching Gemini synthesis. Run Monday July 6 during market hours.

### July 1–2, 2026 — Session 16
**Web sync Audit #2 (all ✅) + built & live-tested the TradingView Pine "chart eyes" + Directional Builder v1.1 → v1.4 (chart input + dashboard read model + options-liquidity gate).**
- **Web skill sync Audit #2:** Bala completed all Session-15 pending re-uploads. Re-exported 7 skills into `Validate_ClaudeWeb_Skill/`; unzipped + diffed → **7/7 ✅ aligned** (0-line diffs on all 4 hub skills; ETF trio's 1 blank line = export-wrapper artifact). Old `directional-trade-builder` confirmed deleted; `options-scanner` (PATH B) + Sieve-1.5 Radar + 30-min-TTL Directional now live on web. `WEB_SYNC_STATUS.md` updated (Audit #2, next due July 14).
- **`PROJECT_INSTRUCTIONS_GEMINI.md` created** — Claude Project instructions = intent router (which skill for which phrase) + engine facts (Tradier, port 5002, buyer-only, 21–35 DTE, TTL 30 min, sieve gates). Paste into a claude.ai Project so skills auto-route without remembering names.
- **TradingView Pine built — `tradingview/gemini-edge-scanner.pine` (v6):** "Claude's eyes on the chart." Reads a daily chart screenshot so Directional Builder can infer trend/S-R/patterns visually. Features: EMA 21/50/200 + trend tint; **S/R zones** (shaded boxes, nearest-3 with distance eviction, position-classified: red above / green below); 52W high/low lines; BASE / WEDGE / TRIANGLE / BREAK / FAILED pattern markers; volume-colored candles; and a **top-right dashboard table** (price, trend, EMAs, RSI, ATR, RVOL, buyer-only CALL/PUT bias, pattern state, R1/R2/S1/S2, 52W H/L). Opus review fixed 4 bugs (critical: zone-cap froze on oldest pivots → distance eviction; resistance-below-price classification; loose wedge convergence; negative bar_index) + Pine line-continuation error (multi-line ternaries indented by ×4 spaces) + bumped v5 → v6. Docs: `OPUS_HANDOFF.md`, `PINE_DESIGN_BRIEF.md`.
- **`skill-options-directional-builder.md` v1.1 → v1.3:** v1.2 added chart-screenshot as optional input (CHART INPUT section, direction scoring rows, CHART ANALYSIS output block, Rule 11). v1.3 restructured CHART INPUT to make the **dashboard table the primary read surface** (table-row map), chart overlays secondary; removed standalone trend/RVOL labels (now in table); priority table = "Table wins" for S/R/trend/52W. **⚠️ Needs re-upload to web** (manifest `options-directional-builder` unchanged — replace, no delete).
- **Note:** Pine files are NOT Claude skills — they live in `tradingview/` and are pasted into TradingView's Pine Editor. Not part of the web skill audit.
- **Live test (July 2, 2026 — HOOD daily):** Pine compiled on v6, dashboard rendered. Two output bugs caught + fixed: (1) RVOL read `0.05x` because the forming intraday bar has partial volume → table RVOL now uses last completed bar (`volume[1]/sma[1]`); (2) `R1/R2` showed levels BELOW price ($84.75/$113.44 vs price $118) because fast-mover blew through old resistance and zones weren't removed → added per-bar zone **pruning** (resistance ≤ close or support ≥ close is deleted). Re-test confirmed: RVOL 0.84x, R1/R2 now correctly $139.75/$150.47 (the Oct–Dec peak region — real overhead). Dashboard correctly flagged HOOD as "bullish trend but extended/chase" (RSI 69.6, +19.7% above EMA21, 0.84x volume). Chart-read path validated end-to-end.
- **Directional Builder v1.3 → v1.4 — Options Liquidity Pre-Screen (addresses Gemini feedback):** Gemini rejected USAR (great technical breakdown — broke 200d SMA, bearish EMA stack, support break at 19.82) because the options chain was a *desert*: 0/70 puts passed OI ≥ 500 (max OI 223, most ~45), 44/70 failed spread < 10% (14–22% spreads), 63/70 failed delta 0.45–0.60. Gemini's point: our skills sent a DOA chain all the way to Stage 2. **Root cause:** per-contract OI/spread/delta are confirmed MCP gaps (Tradier-only, Category 10) — but `underlying_avg_option_volume` (avgCall + avgPut, STATIC) is a reliable early-warning proxy the Directional Builder already pulled for P/C ratio but never gated on. **Fix:** added a tradeability gate — total avg option vol ≥ 10k = LIQUID, 2k–10k = THIN (warn), < 2k = 🔴 LIKELY DESERT (stand down, don't spend a Stage 2 call). Added to output (OPTIONS LIQUIDITY block), CENTAUR JSON (`options_liquidity_proxy` field), and Rule 12. The gate lives only in Directional Builder — the choke point every path (Radar/Scanner/ad-hoc) flows through. Proxy is directional, not definitive; Gemini Stage 2 still runs the authoritative per-contract gates.

### June 30, 2026 — Session 15
**Onboarded the 3rd engine (OptionsIQ ETF) + web skill audit + naming standardization.**
- **Third trading system documented:** `options-iq` (hyphen) = **ETF-only** options engine. IB Gateway direct (port 4001, ib_insync, NOT Tradier), backend 5051 / frontend 3050. 16-ETF universe, vertical SPREADS, 4 directions, **sells premium** (opposite edge to Gemini's buyer-only single-name). Analysis-only. Consumes STA for sector rotation. v0.36.2 / Day 70. Has its own project-local slash skills (catalyst-check, chartreview, ibkr-scan, ki). Added full section to Related Projects + disambiguation note (options_iq_gemini vs options-iq). Memory `project_three_engines.md` written.
- **Web-vs-local skill audit (NEW `WEB_SYNC_STATUS.md`, biweekly cadence; next due July 14):** Bala exported all 6 uploaded Claude Web skills into `Validate_ClaudeWeb_Skill/`. Unzipped `.skill` archives, diffed each against local. Findings: `options-trade-validator` ✅ byte-identical; `options-ibkr-radar` 🔴 web missing entire Sieve 1.5 (pre-Session-11, would not purge micro-caps); `directional-trade-builder` 🟠 web has wrong 5-min TTL (local correct = 30 min); `options-scanner` ⚫ never uploaded (PATH B absent in web); ETF engine's 3 skills (ibkr-scan/catalyst-check/chartreview) ✅ aligned with their `options-iq/skills/` sources.
- **Fixed:** `skill-options-directional-builder.md` title v1 → v1.1 (was stale vs CLAUDE_CONTEXT).
- **Naming standardized (engine-prefixed):** filename stem now == manifest `name:`. Renamed `skill-ibkr-radar`→`skill-options-ibkr-radar`, `skill-directional-builder`→`skill-options-directional-builder` (+ manifest `directional-trade-builder`→`options-directional-builder`), `skill-trade-validator`→`skill-options-trade-validator`; scanner already conformed. STA in-design ref → `skill-sta-ibkr-scan.md` (resolves the `ibkr-scan` collision permanently). Updated all references across living docs + handoff + skill cross-refs (left Gemini snapshot untouched).
- **Key lesson reinforced:** Claude Web identifies skills by manifest `name:`, NOT filename — renaming a file alone needs no re-upload; changing a manifest name creates a NEW web entry (must delete the old).

### June 29, 2026 — Session 14
**Created `SKILL_MAP.md` + skill-routing on a live scanner paste.**
- Loaded CLAUDE_CONTEXT.md + PERSONA.md.
- **Built `SKILL_MAP.md`** — single-page inventory of all 5 skills (4 live + 1 in design), generated from the live skill files (not summaries). Each entry: manifest name, job, exact triggers, sieves/phases/modes, outputs, pipeline stage. Includes at-a-glance table + ASCII pipeline view. Framing that emerged: skills 1 & 2 are interchangeable entry points (manual paste vs autonomous) both feeding 3 → Gemini; 4 is standalone second-opinion; 5 is a separate STA pipeline.
- **Skill-routing answer:** User pasted a 28-row IBKR MultiSort scanner table and asked which skill. Correct answer = **IBKR Radar** (PATH A, paste trigger). Quick sieve preview: all rows pass Sieve 1 (max IVR in table = 43); deepest IV/HV edge = LUNR 69.6% (IVR 43 — a deferred Jun 23 finalist), PCT 81.5% (IVR 26), TRIP 83.5% (IVR 18); Gate A would purge BTBT ($639M) + ASST ($955M); data-artifact flags on ASST (52wk high $252 vs $11.71 last) and CLOV. Full sieve run not executed — skills live at claude.ai, not invokable in Claude Code.
- **Session 13 handoff tasks (A–D) still unstarted.**

### May 7, 2026 — Session 1
Built: terminal v3, skill v2, CLAUDE_CONTEXT v1
Tested: ALLY $45 Call Jun 18 → BUY 6.5/10

### May 8, 2026 — Session 2
Fixed: terminal onclick bug (v3.0 → v3.1)
Tested: ADM CALL (expensive), TBLA $5 Call (WAIT — catalyst consumed post-earnings)
Decision: migrate to VS Code + Claude Code

### May 9, 2026 — Session 3
Created: PERSONA.md — composite Alex persona
Alex's critique applied: OI hard gate, IVR, earnings on card, delta tiers, named constants

### May 12, 2026 — Session 4
Built (terminal v3.1 → v3.3): config.js, OI gate, earnings warning, 200d SMA trend, Bollinger squeeze, entry timing, breakeven reachability, OI snapshot store
Skill bumped to v3: IVR web search, TREND line, OI delta in Phase 4

### May 19, 2026 — Session 5
**Scope change:** HTML terminal enters maintenance mode. Active development in `options_iq_gemini/`.
Built: `skill-options-ibkr-radar.md` v1 → v2. Tested full pipeline: IBKR screenshot → Radar → NFLX/PYPL/HOOD → Centaur Mode → Gemini Intelligence. All three NO TRADE. Ran full implementation review of `options_iq_gemini/` — `REVIEW_SESSION5.md` created. 3 critical bugs + 4 medium + 2 low documented.

### May 19, 2026 — Session 6
Verified Gemini's fixes to `REVIEW_SESSION5.md` — all 9 issues resolved. `REVIEW_SESSION5.md` closed. One residual: `app.py:590` falsy check (Phase 12).

### May 27, 2026 — Session 7
**Project renamed:** `options-research-terminal` → `trading-intelligence-hub`. Scope expanded to serve both Options IQ Gemini and Swing Trade Analyzer (STA). STA context loaded: Day 77, v4.36, paper trading, `/ibkr-scan` skill design complete and ready to build.

### May 29, 2026 — Session 8
**Context load + orientation only.** No deliverables completed. Loaded CLAUDE_CONTEXT.md + PERSONA.md, reviewed all active/in-design skills and pipeline state. Session 9 work queue unchanged.

### June 16–20, 2026 — Session 9
**IBKR MCP deep investigation.** No skill built yet. Key findings:
- Mapped all 68 IBKR MCP fields across 9 categories. 55 closed-day safe, 13 live-only.
- Live dry run on NVDA: vol regime (IV 35.7%, HV 39.4%, IV/HV 90.6% = buyer's edge), IVR 52w 29.5%, SMA 200 ~$189.90 (UPTREND ↑), TTM Squeeze not firing, RSI ~50.
- Confirmed MCP architectural limit: cannot browse options chain or discover OPT contract IDs. Tradier/Gemini still required for chain resolution.
- Discovered portfolio context from `get_account_positions`: NVDA 10 shares @ $175.30 avg. No open options positions.
- Created `ibkr-mcp-capabilities.md` — permanent reference + upgrade checklist.
- New skill scoped: `skill-options-directional-builder.md` — ticker + direction in, best contract out. Two-stage: MCP (vol/trend/technicals/strike zone) → Gemini (chain resolution, earnings gate, Greeks, P&L grid).

### June 26, 2026 — Session 13
**Deep review of both skills + scanner v2 rebuild + IBKR settings update + handoff doc.**

**The horizon insight (most important finding):** The entire pipeline trades 21–35 DTE (confirmed `gemini.md` line 15 — authoritative source). For a 28-day hold, *candidate selection* must use signals that persist over weeks: IVR, IV/HV, 200d trend, earnings-in-window, sustained exit liquidity. Daily RVOL / intraday volume is an execution-timing signal for Centaur Mode — using it to *select* candidates was the core flaw in scanner v1 (top 30 by today's volume selects for the loudest names, anti-correlated with the quiet mispricing edge).

**Scanner v1 review findings (8 issues):**
- Core quant flaw: volume-based universe selects *against* the edge (mega-caps + news-driven movers = elevated IV, fail Sieve 1)
- VIX regime fabricated (no Phase 0 pull)
- 52wk range field orphaned (pulled via misc_statistics but never computed)
- FinViz free has no IV rank filter — IVR pre-screening was absent at universe stage
- FinViz default page = 20 rows, not 30 (URL pagination missing)
- ETFs consume universe slots before MCP stage
- cap_smallover feeds $300M–1B names that Gate A immediately purges (wastes calls)
- Trap check scope ambiguous (must run on all Sieve-1 survivors, not just finalists)

**Scanner v2 rebuild:** Curated-watchlist monitor. CORE (~20) + EXTENDED (~26) liquid/high-beta names. MCP-only — no FinViz scrape. Phase 0 adds VIX + wall-clock anchor. Gate A pre-satisfied by curation. contract_id cache. Trap check scope explicit. Horizon Principle section explains the DTE rationale up front. Watchlist pending Bala review.

**Radar review findings (8 issues — NOT yet fixed, in handoff doc for Sonnet):**
- Footer skips Directional Builder, routes direct to Gemini (known bug)
- No MCP-verify step for finalists — selection runs on stale scanner data (lag + misread risk; Session 11: scanner 67.0% vs live MCP 70.4%)
- No wall-clock DTE anchor for earnings classification
- Sieve 1 framing misleading (scanner pre-enforces it; Sieve 1.5 is the real work)
- Sieve 4 framing misleading (defers to Centaur; not actually a selection gate)
- Trap example numbers drift (IVR 10 in skill vs IVR 9 in CLAUDE_CONTEXT — must unify)
- No shared-core spec — both skills share sieve/gate/output logic but no anti-drift mechanism
- Intraday-RVOL projection idea rejected: day-trader fix on a swing system

**IBKR_SCANNER_SETTINGS.md updated** — 2 new settings added (7 → 9 parameters):
- **Market Cap ≥ $1B** — eliminates micro-caps at source (ONDS was the trigger); makes Radar Gate A a backstop not a patch
- **Option OI ≥ 500** — 28-day exit liquidity gate; OI measures standing inventory (can you exit in 4 weeks), daily volume measures flow only
- Bala to add both in IBKR TWS and confirm they save

**Handoff doc created:** `HANDOFF_session13_scanner_radar.md` — self-contained work order for Sonnet. 4 tasks: (A) Radar alignment, (B) shared-core extraction into OPTIONS_SIEVE_SPEC.md, (C) CLAUDE_CONTEXT sync, (D) embed updated 9-row IBKR settings table inline in both skills (replaces dead file-path references that don't work at claude.ai runtime).

**Watchlist fully expanded (session 13 continuation):** CORE/EXTENDED tables updated with all approved additions from thematic ETF research (GRID, SMH, URA, SETM, DRAM, PAVE holdings + user's personal 20-symbol watchlist review). CORE stays at 20; EXTENDED grew to ~50 organized by theme. Leveraged ETF exclusion rule added. OI verification warnings on thin names (OKLO, ALAB, DRAM, POET, LUNR, RKLB). Bala review required before first live run.

**DTE authority chain established:** `gemini.md` line 15 → `skill-options-directional-builder.md` → skill files. If conflict, trust `gemini.md`.

### June 25, 2026 — Session 12
**Built `skill-options-scanner.md` v1 — autonomous scanner eliminating the manual IBKR paste step.**
- **Problem solved:** The single biggest friction point in the pipeline was requiring the user to open IBKR TWS, run the MultiSort scanner, copy-paste 50 rows, and paste into Claude before Radar could run.
- **Research phase (plan mode):** Investigated Barchart IV rank page, Barchart unusual activity, Barchart core API, Market Chameleon volatility rankings — all JS-rendered or 401 Unauthorized. **FinViz `screener.ashx` confirmed as static HTML** — only public source that returns real data without JavaScript rendering.
- **Architecture decision:** FinViz (universe pre-filter, top 30 by volume) + IBKR MCP (authoritative IVR/IV/HV per ticker) — no fragile scraping of edge metrics. MCP is the reliable leg. FinViz is purely a universe filter.
- **Key design notes:**
  - FinViz free tier has no IV rank filter — IBKR MCP `get_price_snapshot` provides IVR 52w, annual IV, 30d HV.
  - FinViz filter: `cap_smallover` (> $300M pre-filter) + `option_option` + sorted by `-volume` (most active = natural unusual activity proxy).
  - Gate A ($1B market cap floor) is enforced via MCP, not FinViz (no exact $1B filter on free tier).
  - Same sieve logic as Radar: Sieve 1 (IVR ≤ 45) + Gates A/B/C + Sieve 2b (IV/HV ranking).
  - Output format mirrors Radar exactly — consistent experience regardless of entry path.
  - Footer: DIRECTIONAL BUILDER HANDOFF (not Centaur directly — correct pipeline order).
  - Fallback: if FinViz fetch fails → routes user to paste-based Radar, no silent failure.
  - Cap of 30 MCP candidates per run to prevent timeout.
- **Pipeline now has two entry points:** PATH A (manual IBKR paste → Radar) and PATH B (autonomous → Scanner). Both converge at Directional Builder.
- **Radar Centaur Handoff footer fix NOT done** — still on next steps.

### June 23, 2026 — Session 11
**Full pipeline run: Radar → Directional Builder → CENTAUR JSON → Gemini.**
- Ran 4-Sieve Engine on 50-row IBKR scanner data. All 50 passed Sieve 1 (IVR ≤ 45 pre-enforced by scanner). Top 3 finalists: HIVE (IV/HV 67.0%), LUNR (67.7%), POET (68.1%).
- **Scanner quality finding:** IV cap (0.03–0.50) and dollar volume floor ($100M) not filtering reliably in IBKR. LASE at 263% IV and $84M market cap appeared in results.
- **Sieve 1.5 added to `skill-options-ibkr-radar.md`** — three compensating gates run before edge ranking:
  - Gate A: market cap < $1B → PURGE (catches micro-caps that slip through dollar volume filter)
  - Gate B: IV > 150% → ELIMINATE + SCANNER ALERT (IV cap inactive signal)
  - Gate C: estimated dollar volume (price × avg_vol_shares) < $100M → ELIMINATE
  - PURGE LOG format updated to show all four gate layers.
- **Ran Directional Builder on HIVE via IBKR MCP in Claude Code** (contract_id 641568851):
  - 251 daily bars pulled. Computed: RSI 51, EMA stack BULLISH (short-term), MACD BULLISH, BB Width 36%, TTM Squeeze NOT FIRING (bands expanded), ATR $0.48.
  - IVR 52w 43.8% PASS. IV/HV 70.4% (live MCP; scanner showed 67.0% — slight lag). YTD +79%. P/C avg 0.134 (heavy call bias). 4/5 direction signals BULLISH.
  - No HIVE position in account.
  - Expected move 28d: $1.70. Strike zone: $4.50–$5.00.
  - CENTAUR JSON produced, ASCII-cleaned, validated. Saved to `hive_centaur_payload.json`.
- **Timestamp lesson (critical for all future payload generation):**
  - ❌ Do NOT hardcode timestamps approximated from Unix epoch — produces wrong time.
  - ✅ Always use: `python3 -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))"`
- **JSON Unicode lesson:** em-dashes (—) and emoji (⏳) cause malformed JSON in strict parsers. Strip to ASCII before delivery: em-dash → hyphen, emoji → remove or replace with text.
- **Pipeline status on HIVE:** TTM Squeeze NOT FIRING + RVOL 1.29x unconfirmed (intraday). Payload delivered to Gemini. Gemini Stage 2 owns: earnings confirmation, chain pull, Greeks, P&L grid.
- LUNR and POET Directional Builder runs deferred — no hard blocker, HIVE was priority.

### June 22–23, 2026 — Session 10
**skill-options-directional-builder v1.1 patched, live tested, production quality confirmed.**
- Patched `skill-options-directional-builder.md` v1.0 → v1.1. Six schema fixes to align with `app.py /analyze/centaur`:
  1. CRITICAL: `rvol_mcp` moved from top-level finalist into `technical` block (was silently breaking `volume_breakout` gate — always returned False)
  2. `regime` → `volatility_regime` (CENTAUR_SCHEMA_PLAN alignment)
  3. Added `trade_direction` inside each finalist block
  4. Added `radar_notes` narrative field inside each finalist block
  5. Added ⚠️ TTL warning to STAGE 2 HANDOFF output section
  6. Added `POST http://localhost:5002/analyze/centaur` endpoint URL to footer
- Created `options_iq_gemini/Docs/CLAUDE_MCP_SKILL_HANDOFF.md` — Gemini CLI's briefing doc. Contains: skill reference table, MCP gaps + owners, full CENTAUR_SCHEMA_v2 example, field-to-endpoint mapping, Stage 2 execution checklist, version log.
- Established boundary rule: `options_iq_gemini/PROTOCOL.md` is Gemini's SOD document — Claude reads only, never writes. (Saved to memory.)
- **Live test — ACN (FULL EXECUTION BRIEF, market open, Jun 22 ~3:47 PM ET):**
  - Skill output: production quality. Dual-signal conflict (IVR 82.4% FLAG vs IV/HV 0.663 Deep Buyer Edge) correctly detected and surfaced. 5/5 bearish unanimous. RVOL 9.5x EXTREME flagged. New 52w low flagged.
  - Skill added `risk_flags[]` array and `dual_signal_conflict` field beyond base schema — valid Gemini context, should be formalized.
  - Verdict: near-certain post-earnings IV crush scenario (Jun 18 gap-down on 9.5x RVOL = earnings day). TBLA rule expected to kill trade at Gemini Stage 2. Correct outcome — stand down is valid.
  - Bug found: `room_to_support_pct` sign inverted (shows -3.4, should be +3.4). Logged in Known Issues.
  - ACN is an extreme/atypical first test. NVDA (IVR 22.8% PASS, clean signals) is the recommended next test for green-path pipeline validation.

---

## Immediate Next Steps (Session 24)

> Start with: "Read CLAUDE_CONTEXT.md and PERSONA.md — continuing Trading Intelligence Hub session."
>
> Note: keep `SKILL_MAP.md` and `WEB_SYNC_STATUS.md` in sync whenever a skill's version, name, triggers, or role changes. (SKILL_MAP.md is itself already stale per the Session 19 review — see Known Issues.)

### Fresh from Session 26 — next session pre-flight (in priority order)
- [ ] **Daily marks now begin for real, via Tradier (primary path):** 8 positions OPEN in Gemini's journal as of Jul 15, 2026 — AFRM (id 8), GDX (id 9), OKLO (id 10), CCJ (id 11), MP (id 12), URA (id 13), XLF (id 14). Mark daily via Tradier `/markets/quotes` + `/markets/options/chains` (token in `options_iq_gemini/.env`, confirmed working Session 26) at bid/ask mid, close-of-day basis. IBKR MCP `get_option_data` is now the fallback, not primary — never `/journal/monitor` (G1/G2, advisory only).
- [ ] **NIO's put (5 strike, Aug 7 '26) had no live quote at market open via IBKR** (two consecutive empty `bid-ask` pulls) — recorded `NO_QUOTE`, not logged. Retry via Tradier first at the next daily mark before assuming it's genuinely quote-less.
- [ ] **GDX's IVR drifted above its own selection gate between scan (Jul 13, 44.4%) and log (Jul 15, 48.2%)** — logged anyway per Bala's explicit call, drift recorded not smoothed over. Also flag a wide bid/ask spread at log time (bid 1.52/ask 4.15 via IBKR, ~93% of mid) — worth a sanity re-quote via Tradier at the next daily mark.
- [ ] **CCJ's earnings (Jul 30, 2026) land 15 days out — WITHIN HOLD, one day outside the TBLA line.** Not a skip, but worth a closer look at the next check-in given how close it sits to the 14-day cutoff.
- [ ] **Tradier's `fundamentals/calendars` endpoint returns 404** — plan lacks Fundamentals Beta (confirmed Session 25). This is calendar-only and does NOT affect the quotes/chains endpoints now used for daily marks (confirmed working Session 26). `get_earnings_date()` in Gemini's own app.py will still return `EARNINGS_UNKNOWN`; hub skills' web-search-based earnings check remains the real source for that.
- [ ] **Re-upload `skill-options-scanner.md`** to web — now v2.3 (Session 26: 20 new EXTENDED tickers from Bala's conviction research). Manifest unchanged → replace, no delete.

### Fresh from Session 21 — Monday July 6 pre-flight (in priority order)
- [x] ~~**Bala: refresh the Tradier token**~~ — `/tradier/ping` succeeded Jul 10 (confirmed via the real success branch in `app.py:1111-1141`, not just an HTTP 200). Not fully closed: still needs a functional test (calendar/chain) — see Session 24 items above.
- [ ] **Relay batch to Gemini's session (now two, not three):** (1) the `AGENTS.md` "read `GEMINI_STATE_HANDOFF.md` at session open" addition (drafted Session 20); (2) ~~the `IBKR_VERIFIED` null-masking pushback~~ — moot, Gemini fixed it independently (Phase 14, Jul 6) before the relay went out; verified Session 23, Known Issues row flipped to RESOLVED. (3) NEW — "journal rows whose `setup_context` starts with `FWD_TEST:` are excluded from your performance tallies" (forward-test contamination guard).
- [ ] **Monday market-hours run:** green-path Centaur validation (firing squeeze + monthly in 21–35 DTE; pre-screen CDE/KTOS/MP/UEC) + forward-test DRY RUN (procedure only, no logging). **First real entries: Tuesday July 7 at the earliest** — gated on Gemini confirming the `FWD_TEST:` exclusion rule + a working quote source. Slip decided by the Fable pre-launch review (below), not schedule pressure.
- [x] ~~Fable pre-launch review of the forward test~~ — done (Session 21, post-close): verdict **LAUNCH WITH FIXES**, full review in `research/forward_test/FABLE_PRELAUNCH_REVIEW.md`. All six gating findings fixed on paper same session: protocol v2 (symmetry rules: identical mechanical structure/mid-entry/quote-or-skip for both arms; mark-based close-basis resolution; single AND success criterion with power honesty + pre-registered survivor-shortfall rule; cross-group migration allowed; journal API traps G1–G8 mapped) + relay amended (monitor crash warning replaces the wrong "expected and harmless" claim; `/journal/update` never used on FWD_TEST rows).
- [ ] **Decide:** adopt the 15-DTE GOLDEN_RULES candidate ("a bull market does not rescue short-dated long calls — 46% of a 196-trade retail sample expired worthless while SPY rose 77%").
- [ ] **After forward-test data accrues:** formalize the R:R ≥ 1.5 floor in `skill-options-directional-builder.md` if the trial confirms it (don't formalize before — that's the point of trialing).

### Fresh from Session 20 (top priority)
- [x] ~~**Hand `HANDOFF_gemini_contract_hardening.md` to Gemini's dev session**~~ — done. All four contract fixes and all four hardening tasks verified implemented by reading live `app.py` directly and running `test_centaur_contract.py` myself (3/3 pass) — not accepted on Gemini's summary alone. Two overstated claims corrected (TBLA "resolved" → unverified pending live Tradier; backtest "mathematically proved" → real-but-conditional edge, addendum added to the handoff doc's STATUS UPDATE section).
- [x] ~~**Built `OPTIONS_SIEVE_SPEC.md`**~~ — done, see Session 20 history entry above. Resolved the finalist-qualification divergence (Radar → v2.2); Gate C's PATH B units remain an open, documented question pending a live MCP pull.
- [x] ~~**Verified + hardened Gemini's `STATE_HANDOFF.md` automation**~~ — done, two rounds, by running the code both times, not reading it. Both real gaps found by testing (path fragility, one factual conflation) were relayed and confirmed fixed on the live files.
- [x] ~~**Built the hub's own `GEMINI_STATE_HANDOFF.md` mirror + `skill-cross-repo-fix-verification.md` + `GOLDEN_RULES.md`**~~ — done, see Session 20 history entries above.
- [→] ~~Relay the `AGENTS.md` addition~~ — folded into the Session 21 relay batch above (not yet sent).
- [→] ~~Relay the sharpened `IBKR_VERIFIED` finding~~ — folded into the Session 21 relay batch above (not yet sent).
- [ ] **Settle Scanner Gate C's units** — pull `avg_90d_usd_volume` + the price-history volume array for 3-5 names via live IBKR MCP and confirm whether it's a 90-day total or daily average. This is the one remaining piece of `OPTIONS_SIEVE_SPEC.md`'s "known implementation gaps" that needs data, not more reasoning.
- [x] ~~**The moment the Tradier token is refreshed: run `test_tradier_calendar.py`**~~ — done, Jul 13, 2026. Result: **404, not a real date** — the account's Tradier plan doesn't have Fundamentals Beta enabled. This isn't the token-refresh fix anyone expected; see the new Known Issues row. `get_earnings_date` cannot be verified as "returns a real date" on this account until that product is added.
- [x] ~~**All Session 19 Fable 5 findings**~~ — every one fixed Session 24 continuation (Jul 12): Radar's VIX source, Trade Validator's dead couplings, SKILL_MAP.md/PERSONA.md staleness, the Pine script bugs, and the watchlist Gate A claim (live-verified: HIVE confirmed currently sub-$1B). See Known Issues, all flipped RESOLVED.
- [ ] **Bala decision needed: HIVE on the CORE watchlist.** Confirmed via live web search (Jul 12, 2026) that HIVE currently trades ~$790–900M — below the $1B floor it's supposed to be pre-cleared on by curation. The scanner now checks this live each run and will purge it automatically if still sub-$1B, but you may want to just cut or downgrade it to EXTENDED given it's a small-cap crypto miner prone to sitting near this line.

### Fresh from Session 17 (top priority)
- [ ] **GREEN-PATH VALIDATION (Mon Jul 6, market hours):** re-run a Centaur POST on a name with a *firing* TTM squeeze + a monthly inside 21–35 DTE, so Gemini's synthesis actually fires (the one stage never exercised). AFRM stood down correctly (no squeeze + OI desert). Optional closed-day-safe prep: MCP pre-screen CDE/KTOS/MP/UEC for a firing squeeze.
- [ ] **Re-upload `skill-options-ibkr-radar.md`** to web — Session 17 footer fix (Radar → Directional Builder). Manifest unchanged → replace, no delete. (Bala: after full testing, per your note.)
- [x] ~~**Pine Bug A:**~~ `na(e200)` guard done — `INSUFFICIENT HISTORY` + `N/A` gates on < 200-bar names. 52W lines guarded against na crash. (Session 18)
- [x] ~~**Pine Bug B:**~~ S/R role reversal implemented — broken resistance promoted to support, broken support promoted to resistance. Replaces delete-only pruning. `f_make_zone` takes `left_bar` param; role-reversed zones anchored at crossover bar. (Session 18)
- [ ] **Paste updated `gemini-edge-scanner.pine` into TradingView** — test PURR (expect INSUFFICIENT HISTORY) + ECHO (expect intermediate green support zones, not 52W Low as S1). **Also covers the Session 24-continuation Pine fixes (Jul 12): confirm it compiles clean (untested against the real Pine compiler), no visible zone flicker on a live/forming bar (repaint fix), and a distant old pivot correctly appears as price approaches it (Bug B fallback).**
- [ ] **Formalize `options_liquidity_proxy` limitation** in `CLAUDE_MCP_SKILL_HANDOFF.md`: LIQUID proxy != tradeable chain (AFRM 20,123 avg opt vol but 184/184 failed OI>500). Coordinate with Gemini.

### Web skill re-uploads (Bala — manual on claude.ai; see `WEB_SYNC_STATUS.md`)
- [x] ~~Session 15 queue (Radar / Directional / Scanner uploads + old-entry delete)~~ — **DONE, confirmed by Audit #2 (7/7 ✅).**
- [ ] **Re-upload `skill-options-directional-builder.md`** → web has v1.1; local is now **v1.6** (chart-screenshot input + dashboard-table read model + options-liquidity pre-screen + Session 19 fixes: expected-move formula, signal-count denominator, IVR-percentile caveat + Session 24-continuation fix: `INSUFFICIENT HISTORY`/`N/A` table states excluded from Step 6's vote and denominator). Manifest `options-directional-builder` unchanged → replace, no delete.
- [ ] **Re-upload `skill-options-ibkr-radar.md`** → local is now **v2.3** (Session 19: earnings gate spans the full 0–35 day hold; Session 20: finalist selection now requires IV/HV<100% per `OPTIONS_SIEVE_SPEC.md`, plus a sync-note header; Session 24 continuation: Phase 0 VIX regime pull back-ported from Scanner, honest UNKNOWN fallback instead of no source at all). Manifest unchanged → replace, no delete.
- [ ] **Re-upload `skill-options-scanner.md`** → local is now **v2.2** (Session 19: same earnings-gate fix + IVR-percentile caveat added; Session 20: sync-note header added, no logic change; Session 24 continuation: per-run Gate A market-cap check added for HIVE/POET, confirmed sub-$1B risk isn't hypothetical). Manifest unchanged → replace, no delete.
- [ ] **Re-upload `skill-options-trade-validator.md`** → local is now **v3.1** (Session 24 continuation, Jul 12: Mode 1 trigger now names the Gemini Centaur briefing explicitly + a field-availability table for what Gemini's briefing does/doesn't provide; Market Chameleon IVR search replaced with an honest "not available" fallback). Manifest `options-trade-validator` unchanged → replace, no delete.
- [ ] After each re-upload, re-export into `Validate_ClaudeWeb_Skill/` → "run the web skill sync audit" → confirm all four flip ✅.
- [ ] **Next biweekly web audit due: July 14, 2026**

### TradingView Pine (Bala — test the new chart tool)
- [ ] Paste `tradingview/gemini-edge-scanner.pine` into Pine Editor (Create new → **Indicator**) → Add to chart. Should compile clean on v6 (no warnings). Use **Daily, 1–2yr view**.
- [ ] Test on NVDA: verify dashboard table renders top-right; S/R zones track near price (not stuck on old levels); no red zones below the candles.
- [ ] Then screenshot + paste into Directional Builder alongside a ticker to validate the chart-read path end-to-end.

### Handoff doc (Sonnet executes `HANDOFF_session13_scanner_radar.md`)
- [ ] **Task A — Radar alignment:** ~~Footer fix~~ (A1 DONE S17); ~~unify WBD trap numbers~~ (A5 DONE S17 — IVR 10 canonical). STILL PENDING: A2 MCP-verify finalists step; A3 wall-clock DTE anchor; A4 Sieve 1/4 reframes.
- [ ] **Task B — Shared core:** Create `OPTIONS_SIEVE_SPEC.md`; add sync-note headers to both skills
- [ ] **Task C — CLAUDE_CONTEXT sync** (this file — scanner v2 pipeline diagram + scanner skill description)
- [ ] **Task D — Embed IBKR settings inline** in both skills (9-row updated table; replaces dead file-path references)

### Bala actions (before next pipeline run)
- [ ] **Add 2 new IBKR scanner settings in TWS:** Market Cap ≥ $1,000M + Option OI ≥ 500. Confirm they save (re-open scanner and verify — lesson from Session 11 where IV cap and dollar vol floor didn't persist).
- [ ] **Review scanner watchlist** (CORE/EXTENDED tables in `skill-options-scanner.md`) — watchlist was expanded this session with all thematic ETF research additions. Bala to approve or cut names before first live run. Verify OI ≥ 500 for thin names: OKLO, ALAB, DRAM, POET, LUNR, RKLB.

### Pipeline runs
- [ ] **Test skill-options-scanner v2** — first live run after watchlist review. IBKR MCP must be loaded. Confirm CORE scan completes, top 3 output matches Radar format.
- [ ] **Run LUNR and POET through Directional Builder** — complete top 3 finalists from Jun 23 scan. LUNR (IVR 44, IV/HV 67.7%), POET (IVR 45, IV/HV 68.1%).
- [ ] **Run NVDA green-path validation** — IVR 22.8% PASS, clean signals. Full JSON → Gemini Centaur Mode end-to-end.

### Still pending from earlier sessions
- [x] ~~Fix `room_to_support_pct` sign bug~~ — Session 17: formula was already correct; added a sign-guard note (support below price → null, never negative).
- [ ] **Formalize `risk_flags[]`, `dual_signal_conflict`, and `options_liquidity_proxy`** as optional schema fields in `CLAUDE_MCP_SKILL_HANDOFF.md`. The `options_liquidity_proxy` field (Session 16) closes the loop on Gemini's USAR feedback — Gemini should read the LIKELY_DESERT verdict and can skip/short-circuit its own chain pull when Stage 1 already flagged a dead chain. Coordinate exact field shape with Gemini.
- [ ] Build `skill-sta-ibkr-scan.md` for STA — research done (Day 77), 10 filters validated, design complete.
- [ ] skill-options-trade-validator: add explicit note that Mode 1 accepts Options IQ Gemini trade plan output.
- [ ] `options_iq_gemini/app.py:590` — fix `entry_price or 1.0` falsy check (Phase 12 item).
- [ ] Continue 30-sample paper trade run — rescan NFLX/PYPL/HOOD when SQUEEZE transitions from NORMAL.

---

## Bala's Trading Profile

- Accounts: Wealthsimple, IBKR, Questrade, SunLife, Webull (household with Sathya)
- Account types: TFSA, RRSP, RESP, NonReg (CAD + USD)
- Strategy: DCA weekly + manual swing trades + options
- Options preference: single-leg calls/puts, 3–6 week expiry, premium = max loss
- Tool philosophy: zero decision fatigue, one recommendation, no fluff
- Systems: Options IQ Gemini (options pipeline) + STA (swing equities pipeline)
- Skills: Claude skills in this hub serve as intelligence layer for both systems

---

*Update this file at the end of every session before closing VS Code.*

*If this session touched a skill's version, the Session History, or a cross-repo-tagged Known Issues row, run `python3 scripts/generate_gemini_handoff.py` before closing — it regenerates `GEMINI_STATE_HANDOFF.md` for the next Options IQ Gemini session to read. Fails loud (non-zero exit, no file overwrite) if a source file or expected header is missing — don't ignore that message.*
