# Hub Audit Framework
> **Purpose:** Single, standing, self-triggerable framework for auditing all three engines (Gemini, OptionsIQ, STA) plus the hub's own root-level docs — for both doc-vs-code accuracy and trading-strategy soundness.
> **Location:** hub root (mirrors each engine's own `docs/.../MASTER_AUDIT_FRAMEWORK.md` convention — stable, undated, rarely restructured; results get logged, not the framework itself)
> **Created:** Session 28 (Jul 17, 2026), after reviewing all three engines' own existing audit frameworks and personas rather than inventing a hub-specific scheme from scratch.
> **How to run:** say **"run the hub audit"** (full run) or a scoped variant — see Trigger Convention below.

---

## Why this exists, and why it isn't invented from scratch

All three engines already run mature, actively-used, self-auditing frameworks — and they are **not** identical:

| Engine | Framework | Verdict labels | Severity | Cadence / last known run |
|---|---|---|---|---|
| Gemini | `options_iq_gemini/AUDIT.md` — 3 Pillars (Architectural Cohesion, Syntactic Integrity, Behavioral Truth) | inline pass/fail, no formal label set | MED/LOW/RESOLVED inline | Weekly Friday — last: Jul 15, 2026, Session 23, **PASSED** |
| OptionsIQ | `options-iq/docs/stable/MASTER_AUDIT_FRAMEWORK.md` v1.7 — 10 categories, own R1–R23 golden rules | `VERIFIED / PLAUSIBLE / MISLEADING / BROKEN / FALSE` | CRITICAL/HIGH/MEDIUM/LOW | Weekly Monday — log through Day 69 (Jun 16, 2026) |
| STA | `swing-trade-analyzer/docs/claude/stable/MASTER_AUDIT_FRAMEWORK.md` — 5 audit types (Claim/Coherence/Behavioral/Design/External) | `VERIFIED / PLAUSIBLE / MISLEADING / UNVERIFIED / HALLUCINATED` | CRITICAL/HIGH/MEDIUM/LOW/INFO | Log through Day 72 |

The hub's own `GOLDEN_RULES.md` only adopted STA's taxonomy — it doesn't reflect that OptionsIQ runs a different, more elaborate one. That mismatch is itself a standing finding (see Agent 5 below), not something this framework silently papers over.

**Consequence:** this framework does not invent a 4th taxonomy. Each engine gets audited in its *own* native categories and verdict labels — keeping findings compatible with that engine's own Audit Log if it wants to fold them back in. CRITICAL/HIGH/MEDIUM/LOW is the one severity axis all three already share, so it's the unifying column for hub-level synthesis.

**Personas — also not one-size-fits-all.** The hub has a single blended persona (`PERSONA.md` — Alex: 30yo, 3-years-quant-desk, systems-architect + quant-trader lenses combined). OptionsIQ has its own **Rule 22: two separate, non-negotiable personas** (`docs/stable/GOLDEN_RULES.md`) — Persona A (30-year systems architect) and **Persona B = Marcus Webb** (`docs/stable/QUANT_PERSONA.md`), a fully-specified 30-year options market-maker-turned-fund-manager built for adversarial gate review, with his own verdict taxonomy (KEEP AS-IS / DOWNGRADE TO WARN / REMOVE / MISSING) and closing question: *"is this a tool that helps find trades, or a machine for avoiding them?"* Neither Gemini nor STA has a dedicated persona doc. OptionsIQ is audited through its own two personas (overriding Rule 22 with the hub's blended Alex would audit it by a standard it doesn't hold itself to). Gemini and STA fall back to the hub's Alex, noted explicitly as a fallback, not their native lens.

**Trading-effectiveness — "does this system actually find winners," checked per engine before assuming it needs building:**
- **OptionsIQ** has a formal answer already: `MASTER_AUDIT_FRAMEWORK.md` Category 10 (Trading Effectiveness). The Marcus Webb pass below *is* Category 10.
- **Gemini's** answer is a live experiment, not a document: the forward test (SURVIVOR vs REJECT, `research/forward_test/FORWARD_TEST_PROTOCOL.md`), already running, already reviewed once (`FABLE_PRELAUNCH_REVIEW.md`). This framework checks whether Gemini's own docs *misrepresent* what the forward test has shown so far — a claim-accuracy check, not a new metric.
- **STA has no equivalent** — no Category-10 analog, no live win-rate tracking found. Reported as a genuine gap/recommendation each run, not papered over with an invented verdict.

---

## Guardrail

**Read-only across all three engine repos.** Same boundary as Gemini's `PROTOCOL.md` (hub memory: `feedback_protocol_boundary`), extended to OptionsIQ's and STA's own docs. No edits inside `options_iq_gemini/`, `options-iq/`, or `swing-trade-analyzer/` — ever, from this framework. All output lands in hub-side files (this doc's Audit Log, `HANDOFF_*.md` files).

---

## Trigger convention

- **"run the hub audit"** → the full 8-agent run below.
- **"run the hub audit — OptionsIQ only"** / **"— Gemini only"** / **"— STA only"** → just that engine's agents (its Fable pass(es) + its Opus persona pass).
- **"run the hub audit — STA deep"** → adds a 9th agent: full exhaustive STA read (all ~20k lines, not just doc-referenced code), per STA's own Day-50 exhaustiveness lesson ("spot-check = 92.8% pass, exhaustive = 21% pass — check every item"). Not part of the default run — the default STA pass is deliberately scoped down (see Agent 4), and this is the explicit escalation path when full coverage is wanted.
- **"run the hub audit — STA tabs"** → the 5-agent STA Tab-by-Tab Methodology Audit (see dedicated section below) — Layer-2 logic-soundness per UI tab (Sectors, Context+Value, Analyze+Scan, Validate+DataSources, Forward Testing), not the doc-vs-code Layer-1 pass Agent 4 does. Separate from OptionsIQ (out of scope per Bala, Session 28) and separate from "STA deep" (that's exhaustive Layer-1 coherence; this is targeted Layer-2 per feature).
- **"run the hub audit — skills"** → the 2-agent Hub Skills Methodology Audit (see dedicated section below) — Opus/Alex reviewing whether the 4 trading-methodology skills (Scanner, Radar, Directional Builder, Trade Validator) are themselves sound, not just accurately documented. No Fable pre-pass (the skills are small enough to read directly).

---

## Audit Mode block (used verbatim in every agent prompt below)

Source: `swing-trade-analyzer/docs/research/AUDIT_MODE_PROMPT_TEMPLATE.md` (confirmed canonical), decision-tree order adjusted per Bala's preference (MISLEADING checked before PLAUSIBLE — catch "partially true but leads to a wrong conclusion" before settling for "merely plausible").

```
## AUDIT MODE — READ BEFORE RESPONDING
You are a rigorous auditor. Your job is NOT to be helpful or agreeable.
Your job is to be accurate.

### RULES (non-negotiable):
1. Do NOT assume a claim is true because it sounds plausible.
2. Do NOT fabricate citations, paper names, benchmark numbers, or doc URLs.
3. If you cannot cite a real source (a specific file:line), you MUST say so explicitly.
4. Express calibrated uncertainty. "I believe" ≠ "This is verified."
5. Reason step-by-step BEFORE issuing a verdict label.

### VERDICT LABELS (use exactly one per claim; use the engine-native set specified in your assignment below):
- [VERIFIED — SOURCE: <file:line>]
- [MISLEADING — CORRECTION: <what's actually true>]
- [PLAUSIBLE — REASON: <why, uncited>]
- [UNVERIFIED — NEEDS: <what test/evidence would resolve it>]
- [HALLUCINATED — FLAG: <why fabricated>]

Report format per finding:
> **Claim:** [exact quote + file:line]
> **Reality:** [file:line + what the code actually does]
> **Verdict:** [LABEL — details]
> **Severity:** CRITICAL / HIGH / MEDIUM / LOW (+ INFO where the engine's own framework uses it)

Be exhaustive within your assigned scope, not a spot-check — but do not read files outside your assigned scope. Report only real findings; if a section is clean, say so briefly rather than padding with non-findings.
```

---

## The 8 agents

Launch all in parallel: one message, N `Agent` tool calls, `run_in_background: true`. Each prompt = the Audit Mode block above + the engine-specific body below. Two prompts (Agent 6, 7, 8) require pasting a persona file's full contents in at launch time — marked `[PASTE ... HERE]`.

### Agent 1 — Fable / Gemini
```
Audit /Users/balajik/projects/options_iq_gemini/ — the "Options IQ Gemini" engine.

Read these docs: AUDIT.md, PROTOCOL.md, STATE_HANDOFF.md, KNOWN_ISSUES.md, history.md, FABLE_5_REVIEW.md (check first whether its items are already superseded — don't re-audit resolved ground).

Compare against this code: app.py, database.py, quant_math.py, scan_queries.py.

Run AUDIT.md's own 3-pillar checklist verbatim:
1. Architectural Cohesion (Docs vs Design) — API endpoints match gemini.md? Fantastic 4-Sieve matches app.py? Simulation Fallback documented and active? Fail-Loud Scanner aborts on simulated MarketData?
2. Syntactic Integrity (Design vs Code) — quant_math.py vectorized with pandas? API keys .strip()ed? datetime.now() injected into Gemini prompt? /journal/monitor Efficiency Parity math correct? Null-quote resilience (per-row isolation, null last never marked 0.0)? analyze_centaur rejects missing/non-numeric iv_rank_52w with MISSING_IVR? Gamma Surge 10% trailing stop relative to High Water Mark? PUT /journal/update preserves gamma_surge_active + high_water_mark? 0.25 Delta Stop enforced in UI logic?
3. Behavioral Truth (Code vs Execution, read-only trace — do not execute) — Kill-Zone returns 0 results in toxic regimes? Liquidity Gravity rejects Ask Size > 3x Bid Size? Inertia warning at >5 days? OCC mapping correct? FWD_TEST: rows excluded from every performance tally?

Then: spot-check 3 of the "RESOLVED" claims from the most recent "AUDIT PASSED" entry in AUDIT.md against the current code — is the clean bill of health still true today, or has drift occurred since?

Use AUDIT MODE's verdict labels above, but also tag each finding with Gemini's own inline convention (RESOLVED / open, with MED/LOW where AUDIT.md itself would use those) so this stays compatible with AUDIT.md's existing format.

Report: a findings table only (Claim/Reality/Verdict/Severity), no narrative summary. Under 150 lines of output.
```

### Agent 2 — Fable / OptionsIQ Backend
```
Audit /Users/balajik/projects/options-iq/ — the "OptionsIQ" ETF options engine (IBKR direct, buyer+seller).

Read: docs/stable/MASTER_AUDIT_FRAMEWORK.md (the full file — you need its exact checklist items), CLAUDE_CONTEXT.md, CLAUDE.md, memory/MEMORY.md.

Compare against: backend/app.py, gate_engine.py, strategy_ranker.py, pnl_calculator.py, data_service.py, the provider files (tradier/ibkr-alpaca/yfinance/marketdata), constants.py.

Run these categories from MASTER_AUDIT_FRAMEWORK.md verbatim (read the file for the exact current checklist — item text may have moved past what's summarized here):
- Category 1: Claim Verification Audit (the full claims checklist)
- Category 2: Golden Rule Compliance (all R1-R23, per docs/stable/GOLDEN_RULES.md)
- Category 4: Data Integrity Audit
- Category 5: Threading Safety Audit
- Category 6: API Contract Sync
- Category 7: Direction Coverage Audit
- Category 8: Error Handling Audit

Do NOT run Category 3 (Quant Correctness), Category 9 (Frontend UX), or Category 10 (Trading Effectiveness) — those are handled by other agents in this audit.

Then: spot-check 3 claims from the most recent full audit log entry in MASTER_AUDIT_FRAMEWORK.md's own Audit Log table against current code.

Use OptionsIQ's own native verdict labels: VERIFIED / PLAUSIBLE / MISLEADING / BROKEN / FALSE (not the AUDIT MODE label set — this engine's framework uses its own; keep the AUDIT MODE *rules and mindset*, swap only the label vocabulary). Severity: CRITICAL/HIGH/MEDIUM/LOW per OptionsIQ's own scale.

Report: a findings table only, no narrative summary. Under 200 lines of output (this is the largest-scope agent — stay disciplined on format, not depth).
```

### Agent 3 — Fable / OptionsIQ Frontend
```
Audit /Users/balajik/projects/options-iq/ frontend — Category 9 (Frontend UX Accuracy) only, from docs/stable/MASTER_AUDIT_FRAMEWORK.md (read the file for the exact current checklist).

Read the frontend files it references: TradeExplainer.jsx, GateExplainer.jsx, TopThreeCards.jsx, BestSetups.jsx, DirectionGuide component, LearnTab component (find these under the frontend source directory — check package.json/vite config if the path isn't obvious).

Cross-reference against backend/gate_engine.py and strategy_ranker.py to verify what the frontend claims about gates/strategies matches what the backend actually returns (strategy_type values, gate IDs, thresholds).

Why this matters (from the framework itself): wrong plain-English copy shown to a beginner can display "Profit Zone" where the math says loss — this category exists because a UX overhaul hardcoded knowledge into the frontend that can silently drift from backend logic.

Use OptionsIQ's severity mapping for this category specifically (check the framework doc — isBearish() wrong for an active type is CRITICAL, GATE_KB contradicting backend is HIGH, category misassignment is MEDIUM, LearnTab text drift is LOW).

Report: a findings table only. Under 100 lines of output.
```

### Agent 4 — Fable / STA
```
Audit /Users/balajik/projects/swing-trade-analyzer/ — the "Swing Trade Analyzer" engine. SCOPE NOTE, read this first: STA's own docs/claude/stable/MASTER_AUDIT_FRAMEWORK.md states "Spot-check = 92.8% pass. Exhaustive = 21% pass. Always check EVERY item" as a hard-won lesson (Day 50). This run deliberately does NOT honor that at full scale — the codebase is ~20,236 lines against 3 thin doc files, and a full exhaustive read is out of scope for a routine hub-triggered pass. You must state this limitation explicitly in your report's first line. (A "run the hub audit — STA deep" variant does the full-exhaustive pass — not this run.)

Read: README.md, docs/SWING_TRADING_REFERENCE_BUNDLE.md, docs/STA_BREAKOUT_HUMAN_IN_LOOP_WORKFLOW.md.

Run a Coherence Audit, Layer 1 only (docs match code — per docs/claude/stable/MASTER_AUDIT_FRAMEWORK.md Part 2, read that file for the exact protocol): for every claim in the 3 docs above, find where it's implemented in the code and confirm the doc's description matches. Only read the specific code files those docs actually reference — do not attempt to read the full backend/ directory.

Use STA's own native verdict labels: VERIFIED / PLAUSIBLE / MISLEADING / UNVERIFIED / HALLUCINATED. Severity: CRITICAL/HIGH/MEDIUM/LOW/INFO per STA's own scale.

Report: a findings table, plus one line at the top stating the scope limitation. Under 100 lines of output.
```

### Agent 5 — Fable / Hub
```
Audit /Users/balajik/projects/trading-intelligence-hub/ root-level docs — the layer no single engine's own framework covers, since these are hub-authored claims about all three engines plus the hub's own scripts/skills.

Read all of: CLAUDE_CONTEXT.md, GOLDEN_RULES.md, PERSONA.md, SKILL_MAP.md, SKILL_CONVERSION_SCOREBOARD.md, OPTIONS_SIEVE_SPEC.md, all skill-*.md files, all HANDOFF_*.md files, research/forward_test/FORWARD_TEST_PROTOCOL.md, research/forward_test/FABLE_PRELAUNCH_REVIEW.md, WEB_SYNC_STATUS.md, GEMINI_STATE_HANDOFF.md, HUB_AUDIT_FRAMEWORK.md (this file itself — check its own claims about each engine's framework are still accurate, since those engines' docs may have moved on since this was written).

For each doc, compare its claims against what it describes: does SKILL_MAP.md match the skill files that actually exist? Do HANDOFF_*.md files reflect their real resolved/open status (cross-check against options_iq_gemini/KNOWN_ISSUES.md and history.md where a HANDOFF claims something was relayed/fixed)? Does FORWARD_TEST_PROTOCOL.md's target-multiplier note match research/forward_test/build_and_log.py's actual TARGET_MULTIPLIER constant? Does the CORE/EXTENDED watchlist table in skill-options-scanner.md match what's actually there (spot-check a handful of tickers)?

Required finding (re-verify each run): confirm whether GOLDEN_RULES.md still only reflects STA's audit taxonomy without mentioning OptionsIQ's separately-evolved MASTER_AUDIT_FRAMEWORK.md — log as a real finding each time this is still true, not just once.

Use the hub's adopted (STA-derived) verdict labels: VERIFIED / PLAUSIBLE / MISLEADING / UNVERIFIED / HALLUCINATED. Severity: CRITICAL/HIGH/MEDIUM/LOW/INFO.

Report: a findings table only. Under 150 lines of output.
```

### Agent 6 — Opus / Marcus Webb, OptionsIQ
```
You are Marcus Webb. Full persona below, from /Users/balajik/projects/options-iq/docs/stable/QUANT_PERSONA.md — read that file in full and adopt it completely; do not paraphrase or soften it.

[PASTE THE FULL CURRENT CONTENTS OF /Users/balajik/projects/options-iq/docs/stable/QUANT_PERSONA.md HERE AT LAUNCH TIME]

Now read /Users/balajik/projects/options-iq/backend/gate_engine.py and strategy_ranker.py, plus docs/stable/MASTER_AUDIT_FRAMEWORK.md Category 3 (Quant Correctness) and Category 10 (Trading Effectiveness) — read that file for the exact current checklist items (IVR formula correctness, direction-DTE mapping, strike/delta targets, expected-move formula, exit-plan correctness, FOMC gate tiers, gate pass rate calibration targets, the "always one direction" claim, expected-value sanity).

Review the actual gate and strategy logic against Category 3 and Category 10's checklist items. Note: Category 10's Check 10.1 calls for live API calls across 20 ETF/direction combinations — you do NOT have execution access in this pass; audit whether the mechanism and thresholds are sound by reading the code, and explicitly flag that a live re-run of Check 10.1 is a separate follow-up, not something you can confirm from a read-only pass.

As Marcus, give a one-line verdict per gate: KEEP AS-IS / DOWNGRADE TO WARN / REMOVE / MISSING, per your own "How He Evaluates a Gate" 5-question framework from your persona doc.

Close with your own question, verbatim as your persona specifies: is this a tool that helps find trades, or a machine for avoiding them?

Report: your per-gate verdicts, findings in the Claim/Reality/Verdict/Severity format (CRITICAL/HIGH/MEDIUM/LOW), and your closing verdict. Stay in character — direct, specific, references specific historical events where relevant, no hedging language.
```

### Agent 7 — Opus / Alex, Gemini
```
You are Alex — the persona from /Users/balajik/projects/trading-intelligence-hub/PERSONA.md. Read that file in full and adopt it completely.

[PASTE THE FULL CURRENT CONTENTS OF /Users/balajik/projects/trading-intelligence-hub/PERSONA.md HERE AT LAUNCH TIME]

Now read /Users/balajik/projects/options_iq_gemini/quant_math.py and the relevant gate-logic sections of app.py, plus options_iq_gemini/AUDIT.md's "Behavioral Truth" pillar checklist (Kill-Zone, Liquidity Gravity, Gamma Surge trailing-stop, Inertia warning, OCC mapping, FWD_TEST exclusion).

For each Behavioral Truth item, don't just confirm the code path exists — apply your Quant Trader lens to whether the *logic* is sound (e.g., does the Gamma Surge trailing stop's adjustment on gamma collapse actually track a real risk change, or is it a plausible-sounding heuristic without a clear edge argument? Would you keep it as a hard rule or downgrade it to advisory, per your own "time stops are heuristics, not laws" standard?).

Separately: read /Users/balajik/projects/trading-intelligence-hub/research/forward_test/FORWARD_TEST_PROTOCOL.md and the current state of research/forward_test/forward_test_log.csv. Does options_iq_gemini/AUDIT.md or PROTOCOL.md make any claim about the forward test's results that overstates or misrepresents what the CSV actually shows so far? (The test is likely still in an early/interim state — flag any claim that reads like a conclusion when the pre-registered success criterion hasn't been met yet.)

Report: findings in Claim/Reality/Verdict/Severity format, in your own voice (first-principles, "if I can't explain the edge in one sentence" standard).
```

### Agent 8 — Opus / Alex, STA
```
You are Alex — the persona from /Users/balajik/projects/trading-intelligence-hub/PERSONA.md. Read that file in full and adopt it completely.

[PASTE THE FULL CURRENT CONTENTS OF /Users/balajik/projects/trading-intelligence-hub/PERSONA.md HERE AT LAUNCH TIME]

Now read /Users/balajik/projects/swing-trade-analyzer/backend/market_phase_engine.py, breakout_detection.py, and pattern_detection.py, plus docs/claude/stable/MASTER_AUDIT_FRAMEWORK.md Part 2 (Coherence Audit, Layer 2: Correctness — read that file for the exact protocol: is each threshold justified against academic research, backtest evidence, or practitioner methodology like Minervini/O'Neil/Van Tharp?).

Run a Layer 2 logic-soundness pass on these 3 modules only — is the core decision logic (phase classification, breakout confirmation, pattern recognition) justified, or are there unexplained thresholds/magic numbers that look arbitrary?

Separately, and explicitly: confirm whether STA has anything equivalent to OptionsIQ's MASTER_AUDIT_FRAMEWORK.md Category 10 (Trading Effectiveness — gate pass rate tracking, win-rate validation, "does this system find winners at a reasonable rate"). Search STA's docs for this before concluding it's absent. If it's genuinely missing, say so plainly as a recommendation (STA should build a Category 10 analog) — do not fabricate an effectiveness verdict STA has no data to support.

Report: findings in Claim/Reality/Verdict/Severity format, in your own voice.
```

---

## STA Tab-by-Tab Methodology Audit (Layer 2) — added Session 28 (Jul 18, 2026)

**Why this is separate from Agent 4:** Agent 4 is a Layer-1 Coherence pass (do the docs match the code) scoped to 3 doc files. This is Layer-2 (is the logic *sound*), scoped to STA's actual UI tabs — the surfaces Bala uses directly. Confirmed tab → code map, established by reading source directly (no browser automation needed — all 8 tabs, their exact backend routes, and their frontend components were found via `grep` on `App.jsx` and `backend.py` in one pass):

| Tab | Backend route(s) in `backend.py` | Frontend |
|---|---|---|
| Sectors | `/api/sectors/rotation` (:2246) | `SectorRotationTab.jsx` |
| Context | `/api/context/<ticker>` (:2549), `/api/market/phase` (:2455), `/api/cycles` (:2488), `/api/econ` (:2508), `/api/news` (:2528) | `ContextTab.jsx` |
| Value | `/api/value/<ticker>` (:2764) | `ValueTab.jsx` |
| Analyze | `/api/stock/<ticker>` (:910), `/api/sr/<ticker>` (:1481), `/api/patterns/<ticker>` (:1736) | inline in `App.jsx` (`ANALYZE TAB` section) |
| Scan Market | `/api/scan/tradingview` (:1824), `/api/scan/strategies` (:1998) | inline in `App.jsx` |
| Validate | `/api/validation/run|results|history` (:2043-2246) | inline in `App.jsx` |
| Data Sources | `/api/provenance/<ticker>` (:823), `/api/data/freshness` (:706), `/api/cache/status` (:677) | inline in `App.jsx` |
| Forward Testing | `/api/paper-trading/status|trigger` (:2615-2674) | inline in `App.jsx` |

**Token-efficiency rule for all 5 agents below: read ONLY the specific line ranges given — `backend.py` is 3044 lines total; do not read the full file.** OptionsIQ is out of scope (Bala's call, Session 28) — do not audit it even if referenced.

### STA-Tab Agent 1 — Fable / Sectors
```
[AUDIT MODE block from earlier in this document]

Audit STA's Sector Rotation Monitor. Read ONLY: /Users/balajik/projects/swing-trade-analyzer/backend/backend.py lines 2246-2455 (the /api/sectors/rotation route and whatever helper functions it calls in that range — if it calls a function defined outside this range, note that and read only that specific function, nothing else), and /Users/balajik/projects/swing-trade-analyzer/frontend/src/components/SectorRotationTab.jsx in full.

This tab displays an RS Ratio and RS Momentum per sector ETF, classified into 4 quadrants (Leading: RS>100 AND Momentum>0; Improving: RS<100, Momentum>0; Weakening: RS>100, Momentum<0; Lagging: RS<100, Momentum<0) — this is presented as a Relative Rotation Graph (RRG), a specific technique (Julius de Kempenaer's JdK RS-Ratio/RS-Momentum methodology) with a real, specific normalization method, not just "price ratio to SPY."

Answer directly, with file:line evidence:
1. Is the RS Ratio computed as the real JdK-style normalized ratio (smoothed, indexed to oscillate meaningfully around 100), or a simpler raw price-ratio dressed up to look like it? Quote the actual formula.
2. Is "Momentum" a genuine rate-of-change of the RS Ratio, and over what lookback window? A short window makes sectors flicker between quadrants on noise, not real rotation — is there any smoothing/hysteresis at the quadrant boundaries (exactly 100, exactly 0), or are they hard cutoffs?
3. Is there any staleness/freshness indicator tied to this data, or does a 9-hour-old ranking render with the same visual confidence as a fresh one?
4. The cap-size rotation panel (QQQ/MDY/IWM vs SPY) — same rigorous math as the sector panel, or a separate/simpler calculation?
5. The "Scan stocks in this sector →" link appears to be present for Leading/Improving sectors and absent for Weakening/Lagging — confirm this is real, intentional gating (makes sense: don't scan a lagging sector) and not a bug.

Report: answers to the 5 questions above with file:line citations, plus a findings table for anything you'd flag as MISLEADING/BROKEN/etc. per AUDIT MODE labels. Under 100 lines.
```

### STA-Tab Agent 2 — Fable / Context + Value
```
[AUDIT MODE block from earlier in this document]

Audit STA's Context and Value tabs. Read ONLY: /Users/balajik/projects/swing-trade-analyzer/backend/backend.py lines 2455-2615 (market/phase, cycles, econ, news, context routes) and lines 2764 to end of file (value route), plus /Users/balajik/projects/swing-trade-analyzer/frontend/src/components/ContextTab.jsx and ValueTab.jsx in full.

Context tab claims to give market-regime/phase context for a ticker. Value tab (Day 75, "Value investing lens" per App.jsx's own comment) presumably applies fundamental/value-investing criteria.

Answer directly, with file:line evidence:
1. What specific formulas/thresholds does /api/market/phase use to classify market phase? Are they attributed to a specific methodology (Weinstein stage analysis? something else?) or unexplained magic numbers?
2. Value tab — what specific value-investing criteria does /api/value/<ticker> actually check (P/E, P/B, dividend yield, DCF, something else?) — and are the thresholds used sourced from a recognizable value-investing framework (Graham, Buffett-style, etc.) or arbitrary?
3. Does /api/context aggregate the phase/cycles/econ/news data into a single verdict, and if so, is that aggregation logic sound (e.g., does it weight sources sensibly) or does it look like an arbitrary combination?
4. Any missing-data handling — does a failed news/econ fetch silently degrade the context (fabricated fallback) or fail visibly (null/warning)?

Report: answers with file:line citations, plus a findings table per AUDIT MODE labels. Under 100 lines.
```

### STA-Tab Agent 3 — Fable / Analyze + Scan (the core engine — largest scope, most consequential)
```
[AUDIT MODE block from earlier in this document]

Audit STA's Analyze and Scan Market tabs — the core stock-picking engine. Read ONLY: /Users/balajik/projects/swing-trade-analyzer/backend/backend.py lines 910-1048 (/api/stock), lines 1481-2043 (/api/sr, /api/patterns, /api/scan/tradingview, /api/scan/strategies), plus the full contents of market_phase_engine.py, breakout_detection.py, and pattern_detection.py in the same backend/ directory (these are the engine modules the analyze/scan routes call into).

Answer directly, with file:line evidence:
1. What is the actual scoring/verdict logic that turns raw technicals into a BUY/HOLD/AVOID-style verdict? Is the weighting of signals (trend, RS, pattern, volume) justified anywhere (comment, docstring, or a docs file it references), or arbitrary?
2. Breakout confirmation and pattern detection — are the thresholds (e.g., volume multiples, price-move percentages) attributed to a known practitioner methodology (Minervini, O'Neil, etc.) or unexplained constants?
3. Scan Market (TradingView-sourced scan + strategies) — does the scan apply the same verdict logic as the single-ticker Analyze path, or a separate/different one that could disagree with it on the same ticker?
4. Any magic numbers/unexplained thresholds worth flagging as MISLEADING or UNVERIFIED per AUDIT MODE.

Report: answers with file:line citations, plus a findings table. This is the most important cluster in this audit — be thorough within the assigned scope, but stay within the given line ranges and the 3 named engine files only. Under 150 lines.
```

### STA-Tab Agent 4 — Fable / Validate + Data Sources
```
[AUDIT MODE block from earlier in this document]

Audit STA's own self-checking machinery — the Validate and Data Sources tabs. Read ONLY: /Users/balajik/projects/swing-trade-analyzer/backend/backend.py lines 608-910 (health, cache/clear, cache/status, data/freshness, provenance) and lines 2043-2246 (validation/run, /results, /history).

Answer directly, with file:line evidence:
1. What does /api/validation/run actually validate — is it checking data quality (e.g., cross-provider agreement) or something else? Is a "validation pass" meaningful or cosmetic?
2. /api/provenance and /api/data/freshness — do these accurately reflect where data came from and how old it is, or could a stale/fallback data source be presented as fresh/primary (the same class of bug found in OptionsIQ this session — quality banners that don't match the real data source)?
3. Any silent fallback that could mask a real data problem as "validated" or "fresh" when it isn't?

Report: answers with file:line citations, plus a findings table. Under 100 lines.
```

### STA-Tab Agent 5 — Fable / Forward Testing
```
[AUDIT MODE block from earlier in this document]

Audit STA's Forward Testing (paper-trading) tab. Read ONLY: /Users/balajik/projects/swing-trade-analyzer/backend/backend.py lines 2615-2674 (/api/paper-trading/status, /api/paper-trading/trigger). If these routes call out to a separate paper-trading service/module, find and read that file too (search for its import at the top of backend.py) — but nothing else.

This hub's own Gemini forward test (research/forward_test/FORWARD_TEST_PROTOCOL.md) was built with specific care around: mark-based resolution (never touch-based), no "fantasy fills" (real bid/ask mid, not hypothetical), pre-registered target/stop rules not tuned mid-test, and honest logging of stand-down days. Check whether STA's paper-trading mechanism has comparable rigor:

1. Does it mark positions using real bid/ask/mid data, or last-traded-price / a simulated fill?
2. Are exit rules (target/stop) fixed at entry, or can they be recalculated/changed after the fact?
3. Is there any evidence of "fantasy fills" — assuming a limit order filled at a price that may not have actually been reachable?
4. Does it log losses/stand-downs with the same rigor as wins, or is there a risk of survivorship bias in what gets recorded?

Report: answers with file:line citations, plus a findings table. Under 100 lines.
```

---

## Hub Skills Methodology Audit (Layer 2) — added Session 28 (Jul 18, 2026)

**Why this is separate from Agent 5:** Agent 5 checked whether hub docs (including these skill files) *accurately describe* what exists (Layer 1 — e.g., does `SKILL_MAP.md` match the real skill files, do watchlist tables match). This is Layer 2 — is the trading *methodology* these skills specify actually sound. Same reasoning as the STA tab audit above.

**Scope: the 4 trading-methodology skills only** — `skill-options-scanner.md` (429 lines), `skill-options-ibkr-radar.md` (290 lines), `skill-options-directional-builder.md` (587 lines), `skill-options-trade-validator.md` (338 lines). Total 1,644 lines. The 3 process/meta skills (`skill-session-start.md`, `skill-session-close.md`, `skill-cross-repo-fix-verification.md`, 186 lines combined) are out of scope — they're operational procedure, not trading methodology; Alex's quant-trader lens doesn't apply to them.

**No separate Fable extraction pass** — unlike STA, these documents already *are* the methodology (not code to excavate it from), and the total size is modest. Going straight to Opus/Alex is the token-efficient choice here; a Fable pre-pass would just add overhead for no benefit.

**2 agents, split along the natural pipeline boundary**, not by file: Scanner+Radar answer "which candidates even get considered" (screening stage); Directional Builder+Trade Validator answer "given a candidate, which way and is it actually good" (direction+validation stage).

**Explicitly out of scope for this pass:** re-verifying whether Gemini's actual code implements these skills correctly — that cross-repo doc-vs-code check was already done extensively earlier this session (multiple `skill-cross-repo-fix-verification.md` cycles) and again by this audit's own Agent 1 (Fable/Gemini). This pass asks only "is the specified methodology itself good," not "did Gemini implement it right."

### Hub-Skills Agent 1 — Opus / Alex, Screening (Scanner + Radar)
```
[AUDIT MODE block from earlier in this document]

You are Alex — the persona from /Users/balajik/projects/trading-intelligence-hub/PERSONA.md. Read that file in full and adopt it completely.

[PASTE THE FULL CURRENT CONTENTS OF /Users/balajik/projects/trading-intelligence-hub/PERSONA.md HERE AT LAUNCH TIME]

Read /Users/balajik/projects/trading-intelligence-hub/skill-options-scanner.md and skill-options-ibkr-radar.md in full — both in the hub root. These are the two candidate-screening methods: Scanner runs a live multi-gate sieve (VIX regime, IVR percentile, market cap, IV ceiling, dollar-volume floor, IV/HV ratio ranking) over a curated CORE/EXTENDED watchlist; Radar is the manual-paste path for when a user hand-copies an IBKR scanner table.

Apply your two lenses (systems architect + quant trader) and your first-principles rule ("what is the simplest true thing this needs to do?"):

1. Are the gate thresholds (IVR≤45, IV/HV ceiling, dollar-volume floor, market-cap floor, etc.) justified anywhere in the document — research, backtest evidence, or at minimum an explained rationale — or are they asserted without justification? Flag any that read as arbitrary.
2. Does the gate ORDER make sense (cheap/broad filters before expensive/narrow ones), or could a differently-ordered sieve reach the same finalists faster / avoid a false elimination?
3. Liquidity check: per your own standing rule ("liquidity is table stakes, not a score component"), is illiquidity treated as a hard disqualifier in both Scanner and Radar, or could a thin-market name still score its way through?
4. Radar specifically: does the manual-paste path apply the same rigor as the live Scanner, or does it have any gates the live path enforces but Radar can't (or vice versa)? A divergence here is the same "two systems computing the same thing differently" failure mode flagged in the STA audit.
5. Is there a real, one-sentence edge being screened for here, or does the sieve stack just filter for "the absence of obvious problems" without positively identifying mispricing?

Report: findings in Claim/Reality/Verdict/Severity format (CRITICAL/HIGH/MEDIUM/LOW), in your own voice, plus a closing verdict — is this screening methodology sound as specified, and what's the single highest-priority fix if any. Under 150 lines.
```

### Hub-Skills Agent 2 — Opus / Alex, Direction + Validation (Directional Builder + Trade Validator)
```
[AUDIT MODE block from earlier in this document]

You are Alex — the persona from /Users/balajik/projects/trading-intelligence-hub/PERSONA.md. Read that file in full and adopt it completely.

[PASTE THE FULL CURRENT CONTENTS OF /Users/balajik/projects/trading-intelligence-hub/PERSONA.md HERE AT LAUNCH TIME]

Read /Users/balajik/projects/trading-intelligence-hub/skill-options-directional-builder.md and skill-options-trade-validator.md in full — both in the hub root. Directional Builder scores a strict-majority-of-scored-signals vote (SMA200 trend, YTD change, avg P/C ratio, 52w range position, EMA9/21/50 stack, today's P/C ratio) to call BULLISH/BEARISH/MIXED. Trade Validator is the final pre-trade sanity check before a contract gets logged/submitted.

Apply your two lenses and first-principles rule:

1. Is a strict-majority vote across 6 largely-correlated technical signals (several of these overlap conceptually — e.g. SMA200 trend and EMA9/21/50 stack both measure trend direction) actually giving 6 independent opinions, or is it double-counting one or two underlying signals dressed up as six? Does that inflate false confidence in the MIXED-vs-directional call?
2. The MIXED/no-direction fallback — is it a real hard gate (name gets excluded) or could it be overridden/ignored under time pressure? Per your "exits before entries" rule, does an uncertain direction call ever still result in a trade going out?
3. Trade Validator — what's the actual final checklist, and does it re-check anything the Scanner/Radar/Builder stages already verified (double-gatekeeping, the same anti-pattern OptionsIQ was flagged for this session), or does it add genuinely new information at the point of trade?
4. Any place where a threshold or rule is presented as a hard law when it's really a heuristic (per your "time stops are heuristics, not laws" standard) — should be labeled as such with rationale shown, not asserted as certain.

Report: findings in Claim/Reality/Verdict/Severity format, in your own voice, plus a closing verdict — is the direction-and-validation methodology sound as specified, and what's the single highest-priority fix if any. Under 150 lines.
```

---

## Execution sequence (each time this is triggered)

1. Launch the relevant agents in parallel (single message, N `Agent` tool calls, `run_in_background: true`), substituting the `[PASTE ... HERE]` placeholders with the actual current persona file contents at launch time.
2. Wait for all agents to report back (notified on completion — no polling).
3. Spot-check 2-3 findings per engine against live files before trusting them — subagents hallucinate too.
4. Synthesize into a dated write-up (only if findings warrant one beyond the Audit Log row below).
5. Append one row per engine (or one combined row) to the Audit Log table below.
6. Spin off `HANDOFF_*.md` files only for genuinely new, actionable findings — `HANDOFF_gemini_*.md` follows existing hub convention; `HANDOFF_optionsiq_*.md` / `HANDOFF_sta_*.md` would be new namespaces (first time hub-side Claude has audited these two engines).
7. Report a summary back to Bala — not the raw agent output.

## Verification

Every finding must cite file:line for both the claim and the code reality, in the engine's own native verdict-label format, so any finding can be checked in ~10 seconds without re-deriving it. Spot-check a handful per engine against live files before finalizing — the same "verify, don't trust the summary" discipline this hub has applied to Gemini's self-reports all along, now applied to this framework's own subagents.

---

## Audit Log

| Date | Scope | Findings | CRITICALs | HIGHs | Notes |
|---|---|---|---|---|---|
| 2026-07-17 | Gemini (Fable, 3 Pillars + spot-check) | ~17 (0 CRITICAL, ~10 MEDIUM, ~7 LOW/INFO/UNVERIFIED) | 0 | 0 | Real drift confirmed: July 15 "AUDIT PASSED" claimed `last_gamma` preserved through DB updates — spot-check found `PUT /journal/update` (app.py:1091-1106) silently resets it to 0.0 (writes DB default), preserved only via the monitor's own path. Also: `analyze_centaur` indentation bug can 500 a single-finalist payload (app.py:754-759); earnings-gate can never veto a real date (endpoint 404s, fallback doesn't veto on unknown); AUDIT.md's own IV/HV threshold description (1.0) is stale vs code (100.0, percent-units). See `HANDOFF_gemini_audit_session28.md`. |
| 2026-07-17 | OptionsIQ Backend (Fable, Categories 1/2/4/5/6/7/8 + spot-check) | 24 (0 CRITICAL, 4 HIGH, 8 MEDIUM, 12 LOW) | 0 | 4 | First-ever hub audit of this engine. Real data-integrity bugs: BOD cache write path dead code (`_cache_set` never called, data_service.py:126); stale-cache fallback has no age cap (constants.py's `CHAIN_CACHE_STALE_SEC` never imported/used — a Tradier outage could serve 2-month-old chains as current); `scan_context` IVR override never actually merged into the gate payload despite being the documented purpose of that feature; yfinance HV20 fed in and stored as an IV proxy when local history is thin (confirmed in the provider's own docstring), contaminating IVR percentile history. Test suite run live: 110 passed. See `HANDOFF_optionsiq_audit_session28.md`. |
| 2026-07-17 | OptionsIQ Frontend (Fable, Category 9) | 16 (0 CRITICAL, 4 HIGH, 6 MEDIUM, 2 LOW) | 0 | 4 | First-ever hub audit of this surface. Real risk-communication bugs: `GateExplainer.jsx` renders pass-copy text on warn-status gates (a 36% IVR warn shows "YES — IVR ≥ 40%, paid well"); `risk_defined` gate PASSES a naked single-leg `sell_call` as "defined-risk spread, max loss is known" (checks `max_gain>0` only, can't detect an uncapped position) while the same screen elsewhere correctly shows "Unlimited" for the identical trade; displayed seller IVR threshold (35%) and ETF seller DTE window (21-45) both don't match the actual code gates (40% / 30-45) — the DTE one is also stale in OptionsIQ's own framework doc. See `HANDOFF_optionsiq_audit_session28.md` (combined with backend). |
| 2026-07-17 | STA (Fable, Coherence Layer 1, scoped to 3 doc files — NOT exhaustive, see scope note) | 10 (0 CRITICAL/HIGH, 2 MEDIUM, 6 LOW, 2 INFO) | 0 | 0 | First-ever hub audit of this engine. All findings are staleness, no fabrications: README teaches a dead OHLCV fallback tier (Stooq, removed Day 82 — Tradier is the real fallback); "9-criteria checklist" feature description still shows flat 7%/$10M thresholds when code moved to cap-aware tiered thresholds (Day 70B); version footer ~24 days stale. Core S&R/technical/fundamental engines spot-checked clean. See `HANDOFF_sta_audit_session28.md`. |
| 2026-07-17 | Hub root docs (Fable) | 24 (0 CRITICAL, 1 HIGH — fixed same session, ~5 MEDIUM, ~11 LOW, ~7 INFO/VERIFIED-clean) | 0 | 1 (resolved) | HIGH: `CLAUDE_CONTEXT.md` (committed) + auto-gen `GEMINI_STATE_HANDOFF.md` both stated the forward-test target as ×1.80 when it was reverted to ×1.60 same session — spot-checked, confirmed, **fixed directly in both files this run** (regenerated via `scripts/generate_gemini_handoff.py`). Confirmed the GOLDEN_RULES.md/OptionsIQ-taxonomy gap is still real. Mostly stale phase numbers, skill counts, and orphaned "not yet sent" HANDOFF markers — all cross-repo HANDOFF resolved/open statuses verified accurate against Gemini's live repo. |

**Run summary:** 5 Fable agents, ~91 total findings, 0 CRITICAL, 9 HIGH (8 open in OptionsIQ, 1 fixed same-session in hub docs), no hallucinations found across 3 direct spot-checks of the most consequential claims. Opus persona passes (Marcus Webb/OptionsIQ, Alex/Gemini, Alex/STA) deferred to a separate follow-up run — not yet executed as of this entry.

| 2026-07-18 | STA Sectors tab (Fable, Layer 2, "run the hub audit — STA tabs" Agent 1) | 8 (0 CRITICAL, 2 HIGH-equivalent MISLEADING, 3 MEDIUM, 3 LOW) | 0 | 2 | Not real de Kempenaer RRG — a static-midpoint-indexed ratio, honestly labeled as a "swing-trading variant" in a code comment, but the UI claims "RS Ratio 100 = market parity" (false) and a footer data-source label ("TwelveData") that doesn't match the actual source (yfinance). No smoothing/hysteresis at quadrant boundaries (flicker risk). The prominent "Scan Rank #1" CTA bypasses the Leading/Improving safety gate that smaller per-card buttons respect. |
| 2026-07-18 | STA Context + Value tabs (Fable, Layer 2, Agent 2) | 10 (0 CRITICAL/HIGH, 3 MEDIUM, 4 LOW, 3 positive/clean) | 0 | 0 | No fabricated fallback values found anywhere — fetch failures fail visibly. Value tab displays "Buffett"/"Damodaran" framework badges on ROE thresholds whose actual code-comment provenance is "ChatGPT research validated," not a cited source — label overstates pedigree. A growth-rate unit-guess heuristic can misread large growth values. Context aggregation can silently render "NEUTRAL/mixed signals" when it actually has too little data to say anything. |
| 2026-07-18 | STA Analyze + Scan tabs (Fable, Layer 2, Agent 3 — largest/most consequential cluster) | 15 (0 CRITICAL, 3 HIGH-equivalent MISLEADING, ~7 UNVERIFIED/unattributed constants, ~5 VERIFIED/attributed) | 0 | 3 | Scan and Analyze are two independent, non-unified logic paths that can disagree on the same ticker — the scan's "Minervini" strategy checks only 2 of Minervini's 8 real Trend Template criteria while presenting itself as the full methodology (same overstated-pedigree pattern as the Value tab). Where methodology IS named (Minervini Trend Template, O'Neil Cup & Handle), the numbers genuinely match the real published criteria — good faith confirmed. One doc/code gap: Cup & Handle's documented "1-4 week handle" duration check is never actually enforced. Most breakout/pattern tuning constants are unattributed, uncited numbers. |
| 2026-07-18 | STA Validate + Data Sources tabs (Fable, Layer 2, Agent 4) | 8 (0 CRITICAL, 2 HIGH, 3 MEDIUM, 3 LOW) | 0 | 2 | Same bug class as OptionsIQ Frontend's quality-banner mismatch: missing/never-fetched data renders as `'live', ageMinutes: 0, 'fetching fresh'` — indistinguishable from genuinely fresh data. VIX/Fear&Greed/Sector source labels are hardcoded strings, never actually probed against real fetch success. `/api/health` reports `'status': 'healthy'` unconditionally regardless of actual subsystem state. |
| 2026-07-18 | STA Forward Testing tab (Fable, Layer 2, Agent 5) | 7 (0 CRITICAL, 1 HIGH, 1 MEDIUM, 1 LOW, 1 strength) | 0 | 1 | Entry fills are real (next-day actual open, not a fantasy price) — comparable rigor to Gemini's forward test on this point. The real gap: stop/target levels are recorded at entry but the daily resolution step re-derives exits from current simulator code each run instead of reading the stored values — mid-test logic changes could retroactively re-grade open positions under new rules with no ledger trace. Momentum-path trades store identical net/gross P&L (fee accounting not actually differentiated for that path). Per-position fetch failures are silently dropped rather than logged as failures — could bias results if failures correlate with bad outcomes (e.g. delistings). |

**STA tab-audit run summary:** 5 Fable agents (Layer 2, methodology soundness — not the Layer-1 doc-coherence pass from Agent 4), ~48 findings, 0 CRITICAL, 8 HIGH-equivalent, no fabricated data found anywhere across all 5 tabs (a genuine positive). Recurring pattern across all 5: code comments are more honest than the UI — several screens claim more rigor/authority (real-methodology names, "live"/"healthy" status) than the underlying implementation actually has.

| 2026-07-18 | STA Sectors — Opus/Alex persona pass | 5 (0 CRITICAL, 3 HIGH, 1 MEDIUM, 1 new: fake precision) | 0 | 3 | **Verdict: FIX BEFORE TRUSTING.** All 4 Fable findings independently confirmed. Underlying ranking idea (trailing ~3mo performance vs SPY) is legitimate and usable — the problem is entirely in what the UI claims about it. Added: `.toFixed(3)` renders false precision on an approximate, single-anchor-day-dependent number. 5-item prioritized fix list given (see `HANDOFF_sta_audit_session28.md`). |
| 2026-07-18 | STA Analyze+Scan — Opus/Alex persona pass | 6 (0 CRITICAL, 1 MUST-FIX HIGH, rest LOW/MEDIUM, 2 explicitly-defended-as-correct design choices) | 0 | 1 | **Verdict: the "Minervini" scan mislabel is MUST-FIX, HIGH — everything else is cleanup.** Worse than initially flagged: really 1 exact match + 1 loose proxy of Minervini's 8 real criteria, and the "$10B+ large-cap" framing contradicts what Minervini is actually known for. Aggravating factor: the correct 8-criteria implementation already exists in the same codebase — a naming lie, not a capability gap. Single fix given: rename the scan strategy honestly; if a real Minervini scan is wanted, pipe survivors through the existing `check_trend_template()` rather than forking new logic. Two things explicitly defended as good design, not findings: the frozen `market_phase_engine.py` (correctly labeled informational-only) and the `best` scan strategy (genuinely backtested, shares one implementation with paper-trading — "the gold standard the rest should aspire to"). |

**Full STA tab-audit summary (Fable + Opus combined):** 0 CRITICAL across all 7 agents, 4 HIGH-severity items worth prioritizing (Sectors' false "market parity"/data-source claims, the Minervini mislabel, Forward Testing's exit-rule re-derivation gap), no fabricated data found anywhere, and two design choices explicitly validated as sound rather than flagged. Full findings and fix priorities in `HANDOFF_sta_audit_session28.md`.
