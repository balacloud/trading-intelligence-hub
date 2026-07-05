# HANDOFF — Scanner v2 follow-through + Radar alignment (Session 13)

> **For the implementer (Sonnet):** This is a complete, self-contained work order. All strategy decisions are already made — do not re-litigate them. Just execute. Read `CLAUDE_CONTEXT.md` and `PERSONA.md` first. Live-read every file before editing (project rule).
>
> **Author:** Opus session, June 25–26 2026. **Status of work:** Scanner v2 rewritten + watchlist expanded (DONE). Remaining: Task A (Radar alignment), B (shared spec), C (CLAUDE_CONTEXT sync), D (embed IBKR settings), and **Task E (scanner → watchlist-paste mode — §5c, the newest and largest change to the scanner).**

---

## 0. Context you must internalize before touching anything

The whole pipeline trades the **21–35 DTE window** (28-day midpoint — confirmed in `skill-options-directional-builder.md`: `expected_move = price × iv_daily × √28`, `target_dte_range: [21,35]`). **This is a 3–5 week options swing, not day trading.** That single fact drove every decision below.

**Consequence:** Candidate *selection* must use signals that persist over 28 days — **IVR ≤ 45, IV/HV < 100%, 200d trend, earnings-in-window, sustained option liquidity.** Daily volume / intraday RVOL is an *execution-timing* signal owned by Centaur Mode — it must NEVER be used to select or rank candidates. If you find yourself adding a volume-based ranking, stop — that's the bug we just removed.

**What's already done this session:** `skill-options-scanner.md` was rebuilt v1→v2 as a **curated-watchlist monitor**, and its CORE/EXTENDED watchlist tables were expanded with the approved thematic additions. **Task E (§5c) then changes its input mechanism** from MCP-per-ticker screening to **watchlist copy-paste** — that is the one place you DO rewrite the scanner's Phases 0–3. Leave the watchlist *names* alone (Bala's review pending); only change input acquisition + the sieve sourcing per Task B.

**DTE authority chain:** The 21–35 DTE window is confirmed in `gemini.md` line 15 (`Time Horizon: 21 to 35 Days to Expiration`). That is the authoritative source. `skill-options-directional-builder.md` mirrors it. If these ever conflict, trust `gemini.md`. Also: `IBKR_SCANNER_SETTINGS.md` was updated this session with two new settings (Market Cap ≥ $1B, Option OI ≥ 500) — Task D must embed the updated 9-row table, not the old 7-row version.

---

## 1. IMPORTANT runtime constraint (read before §3)

Claude skills are uploaded to claude.ai as **single, self-contained `.md` files**. A skill CANNOT `include` or `reference` another file at runtime — only the uploaded file's contents are loaded. Therefore:

- The "shared core" (§3) is a **repo-side canonical source of truth**, NOT a runtime import.
- Both skill files must still **embed the shared sections verbatim**.
- Anti-drift mechanism = a sync header in each skill pointing to the canonical spec, so a human/agent knows where the source lives and re-syncs after edits.

Do not naively make the skills "reference `OPTIONS_SIEVE_SPEC.md`" and delete the content — that would break them at runtime.

---

## 2. TASK A — Align `skill-options-ibkr-radar.md` with the scanner (and the horizon)

File: `/Users/balajik/projects/trading-intelligence-hub/skill-options-ibkr-radar.md`

Apply these edits. Each has the rationale so you can place it correctly even if line numbers have shifted.

### A1. Fix the handoff footer (KNOWN BUG)
Current footer (≈ lines 254–261) says *"CENTAUR HANDOFF … 1. Open Options IQ Gemini and engage the CENTAUR MODE toggle…"* — this skips the Directional Builder step. The correct pipeline is Radar → **Directional Builder** → CENTAUR JSON → Gemini.

Replace the footer with the same handoff the scanner now uses:
```
RADAR COMPLETE.

DIRECTIONAL BUILDER HANDOFF — Execute in this order:
1. Run skill-options-directional-builder on each finalist ticker (IBKR MCP enrichment — RSI, EMA stack, TTM Squeeze, ATR, strike zone → CENTAUR JSON).
2. Paste each CENTAUR_SCHEMA_v2 JSON payload into Options IQ Gemini — Centaur Mode.
3. Gemini Stage 2: earnings gate (TBLA rule), chain pull via Tradier, Greeks, P&L grid, Gate 1b Liquidity Gravity.
```

### A2. Add an MCP-verify step for finalists (closes the lag/misread gap)
**Why:** The Radar selects the top 3 from pasted/screenshotted IBKR numbers, which lag live by ~30 min and can be misread (Session 11: scanner IV/HV 67.0% vs live MCP 70.4%). A name at IVR 44 / IV-HV 98% on a stale scan could be 47 / 103% live — flipping a pass/fail or reordering. Selection currently runs on a different data vintage than Directional Builder's live re-pull.

Add a new section **after the sieves, before the WEB SEARCH section**, titled `## MCP VERIFICATION — FINALISTS + BORDERLINE`:
- Trigger: run only if IBKR MCP tools are available (if not, skip and note "MCP unavailable — finalists based on scanner values, unverified").
- Scope: the 3 finalists **plus** any survivor sitting on a boundary (IVR 43–47, or IV/HV 95–105%).
- For each: `search_contracts(query=TICKER, security_type=STK)` → `get_price_snapshot(contract_id, exchange, market_data_names=["implied_vol_underlying","historical_vol","implied_volatility_percentile"])`.
- Recompute `ivr_52w`, `iv_hv_ratio` (use the exact formulas from `skill-options-directional-builder.md` STEP 4 / `skill-options-scanner.md` Step 2.3).
- If live values move a finalist across a gate (IVR > 45 or IV/HV ≥ 100%), **demote it and promote the next survivor**. Note the correction in the PURGE LOG: `LIVE-MCP CORRECTION: [TICKER] scanner X% → live Y%`.
- This is a targeted verification, NOT a full re-pull — full enrichment stays Directional Builder's job.

### A3. Add the wall-clock date anchor for DTE math
**Why:** Earnings classification ("within 21–35 DTE", "<14 days") needs today's date; the skill currently eyeballs it. Project memory rule: never approximate dates.

In the WEB SEARCH section (Search 1 — Earnings gate), prepend an instruction to anchor the date first:
```bash
python3 -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))"
```
Then compute days-to-earnings from that anchor before classifying.

### A4. Reframe Sieve 1 and Sieve 4 honestly (small wording edits, no logic change)
**Why:** When the IBKR scanner is correctly configured it pre-enforces IVR ≤ 45, so Sieve 1 usually purges zero (Session 11: all 50 passed). The real filtering is done by **Sieve 1.5** (compensation gates), because it's the scanner's IV-cap and dollar-volume filters that fail. And Sieve 4 (volume floor) defers to Centaur intraday, so it gates ~nothing during market hours.

- In the Sieve 1 section, add one line: *"Note: when the IBKR scanner is correctly configured, Sieve 1 is a safety net that usually purges zero — the scanner pre-enforces IVR ≤ 45. The active filtering is done by Sieve 1.5. Never assume a clean scan; the gate stays."*
- In the Sieve 4 section, add one line: *"Sieve 4 is a context check, not a hard gate, during market hours — intraday volume is incomplete and the definitive RVOL ≥ 1.5 test belongs to Centaur Mode at execution. Daily/intraday RVOL is an entry-timing signal, never a selection signal (21–35 DTE horizon)."*
- **Do NOT** add time-of-day-projected RVOL. (An earlier idea — explicitly rejected. It's a day-trader fix on a swing system.)

### A5. Unify the Cheap IVR Trap canonical example
**Why:** Numbers drift across docs — `skill-options-ibkr-radar.md` says "WBD IVR 10 / IV/HV 165%"; `CLAUDE_CONTEXT.md` says "IVR 9". Pick ONE.
- **Action:** Ask Bala for the real WBD May-19 numbers. If unavailable, default to **IVR 10 / IV/HV 165%** (the value in the skill file itself) and make `CLAUDE_CONTEXT.md` line ~295 match. Search both files for "WBD" and "IVR 9" / "IVR 10" and unify.

---

## 3. TASK B — Extract the shared core (anti-drift)

Create `/Users/balajik/projects/trading-intelligence-hub/OPTIONS_SIEVE_SPEC.md` as the **canonical source of truth** for everything `skill-options-ibkr-radar.md` and `skill-options-scanner.md` share. (Re-read §1 first — this is repo-side, not a runtime include.)

Move these shared blocks into the spec (copy the current correct wording from `skill-options-scanner.md` v2, which is the most up-to-date):
- The IV/HV signal table (< 70% deep / 70–100% buyer / 100–115% neutral / > 115% seller)
- The IVR ≤ 45 gate + rationale (Volatility Tax)
- Gates A / B / C definitions
- Sieve 2b edge-ranking + "top 3, all < 100%, stand-down valid"
- The Cheap IVR Trap rule (with the unified canonical numbers from A5)
- The WEB SEARCH block (earnings TBLA gate 21–35 DTE + 200d trend), incl. the wall-clock anchor
- The TOP 3 FINALISTS output block + PURGE LOG format
- "Direction aware, not prescriptive" principle
- The Horizon Principle (21–35 DTE; structural-not-daily-volume)

Then in BOTH skill files:
- Keep the embedded sections (runtime needs them — §1).
- Add a header note directly under the frontmatter:
  `> Shared sieve/gate/output logic is canonical in OPTIONS_SIEVE_SPEC.md (vX). The sections below are synced copies — edit the spec, then re-sync here. Skill-specific logic (universe acquisition) lives only in this file.`
- Add a version tag to `OPTIONS_SIEVE_SPEC.md` and reference that version in each skill's sync note.

**Net effect:** one place to change shared logic; a clear signal in each skill that its shared sections are derived, so future edits don't silently diverge (the bug that produced the footer + trap-number drift).

---

## 4. TASK C — Sync `CLAUDE_CONTEXT.md`

File: `/Users/balajik/projects/trading-intelligence-hub/CLAUDE_CONTEXT.md`

- Update the `skill-options-scanner.md` entry (skills table + Active Skills section) to reflect **v2 — curated edge monitor, MCP-only, no FinViz**. The current text still describes the v1 FinViz design — replace it. Key points: curated CORE/EXTENDED watchlist, structural screening for 21–35 DTE, Gate A pre-satisfied by curation, VIX/regime pull, no scrape dependency, watchlist maintenance loop (Radar discovers → watchlist remembers → scanner monitors).
- Update the pipeline diagram PATH B to match (no FinViz; curated watchlist + MCP).
- Add a Session 13 history entry summarizing: scanner v2 rebuild rationale (DTE horizon insight — daily volume is wrong axis for 28-day holds), Radar alignment (MCP-verify, footer, reframes), shared-core extraction.
- Add to Known Issues / next steps: "Bala to review scanner watchlist tables (CORE/EXTENDED)."
- Mark these as resolved: Radar footer bug (A1), trap-number drift (A5).
- Fix `room_to_support_pct` sign bug in `skill-options-directional-builder.md` is STILL pending — leave it on next steps (not in this work order unless you have time; formula: `(price − nearest_support) / price × 100` must be positive when support is below price).

---

## 5. Verification (do this before declaring done)

1. **Static read-through:** Open both skill files end to end. Confirm no orphaned output fields (every field in the OUTPUT block is populated by a compute/search step). Confirm no stray code fences.
2. **Cross-file consistency:** `grep -n "WBD" *.md` and the IVR number — must be identical everywhere. `grep -n "Open Options IQ Gemini" skill-options-ibkr-radar.md` — must return nothing (footer fixed).
3. **Horizon audit:** `grep -ni "volume\|rvol" skill-options-ibkr-radar.md skill-options-scanner.md` — confirm no instance uses daily/intraday volume as a *selection or ranking* signal (context/Centaur-deferral mentions are fine).
4. **Sync-note presence:** both skills carry the OPTIONS_SIEVE_SPEC.md sync header with matching version.
5. **No runtime-include mistake:** confirm shared sections are still embedded verbatim in each skill (not deleted in favor of a reference).
6. Report what you changed, file by file. Do not commit unless Bala asks (project is not a git repo per environment; confirm before any VCS action).

---

## 5b. TASK D — Embed IBKR scanner settings inline in both skills

**Why this matters:** `skill-options-ibkr-radar.md` already references `options_iq_gemini/Docs/IBKR_SCANNER_SETTINGS.md` by file path (line ~18), but when the skill is uploaded to claude.ai, Claude cannot read external file paths — **the reference is dead at runtime.** Only what is embedded in the uploaded `.md` file is available to Claude.

Same gap in the scanner: the gate thresholds (IVR ≤ 45, IV/HV 40-100%, dollar vol ≥ $100M, avg opt vol ≥ 10K) appear as magic numbers with no documented source.

**Fix:** Embed the full settings table from `options_iq_gemini/Docs/IBKR_SCANNER_SETTINGS.md` inline in **both** skill files. Copy the table verbatim — do not paraphrase.

### In `skill-options-ibkr-radar.md`:
- **Location:** Replace the dead pointer on line ~18 (`"full spec: options_iq_gemini/Docs/IBKR_SCANNER_SETTINGS.md"`) with the heading `**Scanner configuration (IBKR MultiSort — verified settings):**` followed by the embedded table.
- The line currently reads: `**Scanner configuration** (full spec: \`options_iq_gemini/Docs/IBKR_SCANNER_SETTINGS.md\`):`
- Replace it with the actual table content from the settings file (all 7 parameters with their field settings, directions, and reasoning), followed by a note: `> Source: IBKR_SCANNER_SETTINGS.md — keep in sync if IBKR settings change.`

### In `skill-options-scanner.md`:
- **Location:** Add a new section `## IBKR SCANNER SETTINGS — GATE REFERENCE` after the HORIZON PRINCIPLE section and before WHAT YOU NEED BEFORE STARTING.
- Lead with: `> The gate thresholds used in Phase 2 MCP screening mirror the verified IBKR scanner configuration. These are the original source of each sieve's numeric threshold.`
- Embed the full settings table verbatim.
- This documents WHERE each threshold comes from: IVR ≤ 45 (52-Week IV Rank 0–45%), IV/HV 40-100% (IV/Historical Vol), dollar vol ≥ $100M (Average Volume $), avg opt vol ≥ 10K (Average Option Volume).
- Also note the Gates B and C thresholds are **compensating gates** for settings that don't always save reliably in IBKR (IV cap 0.03–0.50 and dollar volume floor $100M), per Session 11 finding.

### Do NOT:
- Do not duplicate the Calibration History log (§ "First-Principles Quant Log") — that is historical context and adds noise. Embed the settings table only.
- Do not change any gate thresholds — the embedding is documentation, not a logic change.

---

## 5c. TASK E — Convert the scanner from MCP-screening to watchlist-paste mode

File: `/Users/balajik/projects/trading-intelligence-hub/skill-options-scanner.md` (+ one new doc).

### E0. Why, and the one trap

Scanner v2 currently screens the curated CORE/EXTENDED list by calling IBKR MCP per ticker (~22–41 calls/run cold, ~22 warm). Bala already runs a proven workflow in his other project (`options-iq`): a **fixed IBKR watchlist** with custom columns that he **copy-pastes** into Claude. We are bringing that same paste-driven input to this scanner — eliminating the MCP screening loop.

**Net effect on call count:** ~22–41 MCP calls → **0 for screening** (+ ≤3 optional finalist-verify calls, + ≤3 earnings web-searches on finalists).

**Decision (do not re-litigate):** Scanner and Radar stay **two separate skills**. Role split: Scanner = *monitor a fixed watchlist*; Radar = *discover from the dynamic MultiSort scanner*. Anti-drift is already handled by Task B (`OPTIONS_SIEVE_SPEC.md`) — both skills carry synced copies of the shared sieve/gate/output logic. Task E only changes the scanner's **input-acquisition** sections (Phases 0–3). The sieve/gate/output logic is untouched and stays sourced from the spec.

**⚠️ THE TRAP — buying vs selling inversion.** The `options-iq` watchlist docs (`/Users/balajik/projects/options-iq/docs/stable/IBKR_DATA_SOURCES.md` and `IBKR_WATCHLIST_SETUP.md`) describe a premium-**SELLING** system (sell when IV is rich: IV/HV ≥ 110%, IV Pctl ≥ 60%, IVR ≥ 35). This scanner is a premium-**BUYING** system (buy when IV is cheap: **IV/HV < 100%, IVR ≤ 45**) — the thresholds are **inverted**. Reuse the IBKR column *plumbing* from those docs; **never** import their decision matrix. A row those docs reject (e.g. IV/HV 94% = "no trade") is exactly what this scanner *wants*.

### E1. Rewrite "WHAT YOU NEED BEFORE STARTING"
- Primary input is now a **pasted IBKR watchlist table**, not MCP.
- IBKR MCP becomes **optional** — used only for finalist verification (E5). WebSearch still required (earnings, E4).
- If no paste is provided: prompt the user — "Paste your IBKR scanner watchlist (the `Options_IQ_Scanner` view)."

### E2. Rewrite Phase 0 (Regime)
- Read VIX from the **VIX row in the paste**: VIX ≤ 25 → STANDARD; > 25 → HIGH-FEAR. No `search_contracts` / `get_price_snapshot` for VIX.
- If no VIX row present: regime `UNKNOWN — VIX row missing` (never fabricate).
- Keep the python3 wall-clock date anchor for DTE math — unchanged.

### E3. Rewrite Phases 1 + 2 as a paste parser
- **Parse by column header name, not fixed position** (IBKR column order can change).
- Use the column → field mapping in E6.
- Apply the existing sieves/gates on parsed values — **logic unchanged, sourced from `OPTIONS_SIEVE_SPEC.md`**: Sieve 1 (IVR ≤ 45), Gate B (IV > 150% → eliminate + alert), Sieve 2b (rank IV/HV ascending; top 3 all < 100%; stand-down valid), Trap check (IVR < 20% AND IV/HV > 120%, runs on all Sieve-1 survivors), OI gate (Option Open Interest ≥ 500).
- Gates A and C (market cap, dollar volume) remain **pre-satisfied by curation** — no column required.
- Any row missing a required cell → skip it, note `PASTE_DATA_INCOMPLETE — [TICKER]` in the PURGE LOG.

### E4. Trim Phase 3 (Web search)
- **Drop Search 2 (200d trend)** — the `Price/EMA(200)` column supplies it directly: > 0 → UPTREND, < 0 → DOWNTREND.
- **Keep Search 1 (earnings / TBLA gate)** — the watchlist has no earnings date; still web-searched on finalists only, against the Phase-0 date anchor.

### E5. Add optional finalist MCP-verify (mirror Task A2)
- After the top 3 are selected: **if IBKR MCP is loaded**, re-pull just those 3 (`search_contracts` + `get_price_snapshot`), recompute **IV/HV** and re-rank.
- **If MCP is not loaded:** skip; add header note "finalists from paste — unverified."
- This is the staleness backstop (paste lags live by minutes). Costs ≤3 calls and only on finalists.

> **⚠️ CRITICAL — verify on IV/HV only; IVR cannot be cleanly cross-checked (Session 13 live test finding).**
> The IBKR watchlist `52 Week IV Rank` column and the MCP field `implied_volatility_percentile.high_52w` are **two different metrics**: IV **Rank** = where current IV sits between the 52-week IV high/low; IV **Percentile** = % of days IV closed below current. They diverge — in the live test COIN read **Rank 45** (passes the ≤ 45 gate) on the watchlist but **Percentile 53%** via MCP. If the verify step naively maps MCP percentile onto the IVR gate, it would **falsely purge COIN**.
>
> **Therefore, in the verify step:**
> 1. **Recompute and compare IV/HV** (= `implied_vol_underlying.annual_iv` ÷ `historical_vol.annual_pct` × 100). This is computed identically on both sides — it is the trustworthy gate cross-check. If live IV/HV crosses ≥ 100%, demote and promote the next survivor; log `LIVE-MCP CORRECTION: [TICKER] paste X% → live Y%`.
> 2. **Re-rank the finalists by live IV/HV** — the order can change without any gate crossing (live test: NVDA overtook COIN for #2). Output the live-verified order.
> 3. **Do NOT re-evaluate the IVR/Sieve-1 gate from MCP.** The IBKR watchlist is the **authoritative source for IV Rank**; MCP percentile is advisory only. If MCP percentile diverges sharply from the pasted Rank, note it as `IVR-METRIC-DIVERGENCE: [TICKER] paste Rank X vs MCP pctl Y%` — informational, never an auto-purge.
> 4. Same correctness note belongs in `OPTIONS_SIEVE_SPEC.md` and in the scanner's Step 2.3 (the field that currently maps `implied_volatility_percentile.high_52w → ivr_52w` is mislabeled — it is a *percentile*, not a *rank*; in paste mode the true Rank comes from the watchlist column).
>
> **Project-wide impact — fix everywhere this field is used, not just E5:** `implied_volatility_percentile.high_52w` is labeled/treated as "IVR" in (a) the scanner Step 2.3, (b) the Radar MCP-verify step you are adding in **Task A2**, and (c) `skill-options-directional-builder.md`'s vol block. In all three, relabel it honestly as **IV Percentile** and stop calling the MCP value "IV Rank." Where a true IV Rank is needed and only MCP is available, state that MCP cannot supply Rank (only the IBKR watchlist/scanner can) — so the IVR ≤ 45 gate is enforced from pasted data, with MCP percentile as an advisory sanity check.

### E6. Column spec — embed inline AND as a standalone doc
Per §1 runtime constraint (claude.ai skills can't read external files), the column spec must be **embedded verbatim inside `skill-options-scanner.md`** AND written as a standalone repo reference `IBKR_SCANNER_WATCHLIST_SETUP.md` (so Bala has a setup checklist). The doc should mirror the *format* of `options-iq/docs/stable/IBKR_WATCHLIST_SETUP.md` but with **buying-tuned** roles (NOT the selling thresholds — see E0 trap).

**Column → scanner-field mapping (buying-tuned):**

| IBKR watchlist column | Scanner field | Used by |
|---|---|---|
| (VIX row) Last | regime | Phase 0 |
| Underlying Price | price_last | RANGE, cards |
| 52wk IV Rank | ivr_52w | Sieve 1 (≤ 45) |
| Implied Vol./Hist. Vol % | iv_hv_ratio | Sieve 2b (< 100%) |
| Opt. Implied Volatility % | iv_annual | Gate B (> 150% → eliminate) |
| Hist Vol Close % | hv_30d | card display |
| Option Open Interest | oi | OI gate (≥ 500) |
| Price/EMA(200) | trend | replaces 200d web search |
| 52wk High (price) | high_52w | RANGE |
| 52wk Low (price) | low_52w | RANGE |
| Opt Volume | opt_volume | liquidity context (optional) |

> The watchlist must include a **VIX row** (regime) and the two **price** `52wk High` / `52wk Low` columns (these are distinct from the `52wk IV High/Low` columns — those are IV, not price).

### E7. CLAUDE_CONTEXT sync (fold into Task C)
- PATH B diagram: Phase 1/2 becomes "paste IBKR watchlist → parse" (not "MCP per-ticker").
- Scanner skill description: input = watchlist paste; MCP optional (finalist verify only).
- Add `IBKR_SCANNER_WATCHLIST_SETUP.md` to the file-structure list.

### E8. Directional lean per finalist (for Directional Builder handoff)

Emit a **preliminary directional lean** for each finalist so the user can pass it straight into `skill-options-directional-builder` (whose INPUT accepts an optional `bullish`/`bearish`).

**This is preliminary, not authoritative.** The scanner has at most 2 directional signals from the paste; the Directional Builder runs the full 5–6 signal inference (Step 6) and **wins on any conflict**. Label the scanner lean accordingly — never present it as the final call.

**Lean rule (from paste columns only):**

| Signal | Bullish | Bearish |
|---|---|---|
| Price/EMA(200) | > 0 | < 0 |
| 52wk range position *(only if price `52wk High/Low` columns present)* | > 60% | < 40% |

- Both agree (or one + neutral) → **BULLISH** / **BEARISH**.
- Conflict, OR Price/EMA(200) within ±2% (flat) → **NEUTRAL**.
- Range columns absent → trend-only; tag the lean `(trend-only)`.

**Output:** add a `LEAN:` line to each finalist card, and append a ready-to-run handoff list:
```
DIRECTIONAL BUILDER HANDOFF — run each, passing the lean as the optional direction:
1. skill-options-directional-builder  [TICKER]  [bullish/bearish]
...
```
- For a **NEUTRAL** lean, pass **no** direction — let the Builder auto-infer (do not force a side).
- Keep the existing Directional Builder footer below this list.

### E9. Verification (before declaring Task E done)
1. **Dry parse:** paste VIX + ~5 tickers with the configured columns → confirm parse-by-header, IVR/IV-HV/RANGE/trend computed, sieves applied, **0 MCP calls**.
2. **Inversion check:** a row at IV/HV 94% is treated as a *buy* candidate, not rejected. (Guards against importing options-iq selling thresholds.)
3. **Missing-column resilience:** drop a column → `PASTE_DATA_INCOMPLETE`, no crash.
4. **Finalist verify:** MCP loaded → top-3 re-pull fires (≤3 calls), IV/HV re-ranks, gate-crossing demotes correctly, IVR divergence noted not purged (E5). MCP unloaded → "unverified" note, no error.
5. **Directional lean:** each finalist carries a BULLISH/BEARISH/NEUTRAL lean; trend-only tagged; NEUTRAL passes no direction in the handoff list.
6. **Output parity:** matches Radar/Directional-Builder format (TOP 3 cards + PURGE LOG + Directional Builder footer).

---

## 6. Boundaries — do NOT do these

- Do NOT edit `options_iq_gemini/PROTOCOL.md` (Gemini's SOD — read-only for Claude).
- Do NOT touch the scanner watchlist names (Bala's review pending).
- Do NOT add any web-scrape/FinViz logic back to the scanner.
- Do NOT add volume-based ranking anywhere.
- Do NOT commit `config.js` or any API keys.
- Do NOT make skills reference external files at runtime (§1).
- Do NOT import the `options-iq` watchlist *thresholds* (Task E0 trap) — that is a premium-SELLING system; this scanner BUYS. Reuse the column plumbing only.
- Do NOT add MCP per-ticker screening back to the scanner (Task E) — paste is primary; MCP is finalist-verify only.
