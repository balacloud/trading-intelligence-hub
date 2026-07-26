# SKILL_CONVERSION_SCOREBOARD.md
> Tracks how much of each skill's logic is deterministic (Python-able) vs. genuine LLM judgment.
> Not a rewrite plan — a running measurement. Update alongside session close, same cadence as the Known Issues table in `CLAUDE_CONTEXT.md`.
> **Refreshed Session 34 (Jul 25, 2026)** — this file went stale for ~2 weeks (last touched Session 24 continuation, Jul 11) while Sessions 30-33 quietly built and used seven real Python modules. Caught the same way this hub catches every other staleness: checked the live files (`research/forward_test/*.py`) instead of trusting what this doc already claimed.

---

## Why this exists

Session 24 question: how many of the hub's skills are actually doing arithmetic an LLM shouldn't need to re-derive every run, vs. doing something only an LLM can do (synthesis, judgment, reading an ambiguous chart)?

The honest reason to convert a component to Python isn't speed — it's determinism. A skill re-deriving IV/HV or a direction-vote each run can silently drift from `OPTIONS_SIEVE_SPEC.md`. Python code can't reinterpret a threshold; a prompt instruction can. Every conversion below should be justified by *"this removes a drift risk,"* not *"this is possible."*

**Scoring rule:** % = (components that could run as deterministic Python today) / (total components in the skill), estimated from reading the skill file, not guessed. A component only counts as converted once real code exists and has been run against a live case — not when it's merely "clearly Python-able."

---

## Two separate tracks — don't conflate them

This file originally scored the **web-uploaded skill files** (`.md`, prompt-only, no code execution — see Constraint below). That track hasn't moved: the skills as uploaded to claude.ai are still 100% prompt-executed, unchanged since Session 24. Table below, unchanged in substance.

A **second track opened Session 30 and is now the one doing real work**: a parallel Python pipeline under `research/forward_test/`, built specifically for Claude-Code execution (Constraint's option (a), "fully deployable today"). It doesn't touch the web skill files at all — it's a separate implementation of much of the same logic (sieve math, technicals, contract selection, payload assembly), genuinely converted, genuinely tested, and in daily live use across Sessions 30-33's forward-test runs. This is real progress the old "0% converted" framing was hiding.

## Track 1 — Web skill files (unchanged)

| Skill | Score | Converted | Deterministic (Python-able) | LLM-required (judgment/vision) |
|---|---|---|---|---|
| **skill-options-scanner.md** (v3.1) | 85% est. / **0% converted** | — | VIX regime pull, watchlist iteration, Sieve 1/1.5/2b math, IVR/IV-HV computation, contract_id caching | Web-search synthesis of earnings date + 200d trend framing into prose |
| **skill-options-directional-builder.md** (v1.6) | 85% est. / **0% converted** | — | EMA stack, RSI, ATR, TTM squeeze, direction-inference majority vote, options-liquidity gate, CENTAUR JSON assembly | Optional TradingView chart-screenshot read (though the Pine dashboard already table-izes these values — could become a data pull instead of vision, see Next Milestones) |
| **skill-options-ibkr-radar.md** (v2.3) | 70% est. (paste mode) / **0% converted** | — | Sieve math identical to Scanner, RVOL/52wk-range computation from pasted columns | Screenshot-vision parsing (when not in paste mode); web-search synthesis |
| **skill-sta-ibkr-scan.md** (in design) | 70% est. / **0% converted** | — | 10-filter SEPA/CAN SLIM numeric threshold checks, ranking top 5-10 | Screenshot-vision parsing of the IBKR scanner |
| **skill-options-trade-validator.md** (v3.1) | 30% est. / **0% converted** | — | R:R calc, IV/HV sub-computations | Quick verdict / deep-dive synthesis — the actual value-add is reasoning about the setup, not arithmetic |
| **skill-cross-repo-fix-verification.md** (v1) | 15% est. / **0% converted** | — | Grep-able anti-pattern checks (silent-default sentinels, hardcoded strings) could be a partial lint pass | The core act — read a diff, judge if a claim is overstated or a fix is real — doesn't reduce to a threshold check |

**Track 1 score: still 0% converted.** Estimates above remain ceiling, not progress — nothing here changed because nothing here is where the actual conversion effort has been happening since Session 30.

## Track 2 — `research/forward_test/*.py` (real, tested, live-used)

| Module | Converts | Status |
|---|---|---|
| `sieves.py` | Sieve 1 (IVR≤45) + Gates A/B/C + Sieve 2b ranking + Cheap IVR Trap — exactly Milestone 1 below | **Converted.** Run live every PATH A/B session since Session 30; `test_sieves.py` + `test_spec_sync.py` keep it in lockstep with `OPTIONS_SIEVE_SPEC.md` |
| `technicals.py` | SMA/EMA, Wilder RSI/ATR, MACD, Bollinger/Keltner + squeeze, pivot S/R, direction vote — exactly Milestone 2 below | **Converted.** `test_technicals.py`; used in every Directional Builder read this session and prior |
| `contracts.py` | Underlying resolution from noisy `search_contracts` results; option contract selection by delta/OI/spread bands | **Converted.** `test_contracts.py`; stricter than the skill's original nearest-ATM logic |
| `centaur_payload.py` | CENTAUR_SCHEMA_v2 payload assembly + validation, including the iv_hv_ratio decimal-fraction bug class | **Converted.** `test_centaur_payload.py`; every real `/analyze/centaur` POST this session went through it |
| `paste_parser.py` | Raw IBKR screener/watchlist paste → structured rows, PATH A/B auto-detect, fail-loud on mismatch | **Converted Session 33.** `test_paste_parser.py`, 14 tests. Three-pass review (Session 34) caught a real bug: the PATH B em-dash placeholder (`—`, U+2014) wasn't recognized by `_num()`, which only checked ASCII hyphen — would have crashed on real input with a blank cell, never actually exercised against real user-pasted text until the review. Fixed. |
| `earnings.py` | TBLA earnings-date lookup — Gemini search grounding, falling back to Finnhub with a near-boundary caution flag | **Converted Session 34.** `test_earnings.py`, 12 tests; replaces the ad hoc WebSearch every prior session ran by hand. Three-pass review fixed 5 real issues before first commit: a silent system-local-time default, an unflagged Finnhub cross-listing match, an undocumented magic number, hardcoded absolute paths, and a regex that could have silently returned today's date instead of the real answer. |
| `build_and_log.py` | Scan output → dedupe/migration → direction inference (reduced signal set) → contract → journal POST → CSV row | **Converted**, though largely superseded in practice by the manual finalize-scripts this session used `sieves`/`technicals`/`contracts`/`centaur_payload` directly instead — worth deciding whether `build_and_log.py` should be updated to call the newer modules or retired. Three-pass review (Session 34) found `score_direction`'s denominator was silently broken (a real filter that did nothing) and a fabricated `50.0` fallback where `technicals.py`'s own equivalent correctly returns `None` — both fixed, and this module got its first test file. |
| `resolve_positions.py` | Close-of-day mark-based resolution — the only sanctioned path to close `FWD_TEST:` positions | **Converted.** Run live multiple times, including Session 33's disclosed mid-day exception. Three-pass review (Session 34) found `update_csv` matched resolutions to CSV rows by ticker+strike only, no expiry check — fixed with `dte` as a second match key, plus the module's first test file. |

**Track 2 score: 8/8 core pipeline steps converted, all live-tested against real data, not just written.** This is the actual, honest answer to "how much have we automated" — Track 1's 0% was true but had become a misleading answer to that question. `sieves.py`, `technicals.py`, `contracts.py`, and `centaur_payload.py` also went through the Session 34 three-pass review (see `GOLDEN_RULES.md`) — `sieves.py`/`technicals.py` came back clean, `contracts.py` had one line of dead code removed, `centaur_payload.py` had a hardcoded `dual_signal_conflict: False` turned into a real parameter (still unused by any caller, a separate follow-up).

---

## Next Milestones (ordered by drift risk removed, not ease)

1. ~~**Scanner Sieve math → Python module.**~~ **DONE — `sieves.py`, Session 30.**
2. ~~**Directional Builder technicals → Python module.**~~ **DONE — `technicals.py`, Session 30.**
3. **Directional Builder chart-read → data pull instead of vision.** Still open. The Pine dashboard table already contains the exact fields the skill currently reads via screenshot vision (trend, EMAs, RSI, ATR, RVOL, S/R levels, pattern state). If TradingView alerts/webhooks can export that table, the vision step disappears entirely rather than getting "better."
4. **Cross-repo verification anti-pattern lint.** Still open, still low priority/low ceiling.
5. **Decide `build_and_log.py`'s fate** — update it to call the newer `sieves`/`technicals`/`contracts`/`centaur_payload` modules instead of its own older reduced-signal-set logic, or retire it now that the finalize-scripts pattern this session used covers the same ground with the fuller module set.
6. **Reconsider Phase 5 of `PLAN_deterministic_pipeline_formalization.md`** now that `paste_parser.py` closed what was arguably that plan's last gap — flagged in `CLAUDE_CONTEXT.md`'s own Next Steps as worth a fresh look, not duplicated here.

---

## An open question, not a dead end — IBKR REST API and Sieve 1's IV Rank field

**Question that comes up periodically (most recently Sessions 34-35):** since `research/ibkr_rest_api_probe/` proved 11/14 watchlist columns are available via IBKR's REST API, why not call REST directly instead of relying on live MCP tool calls (or manual paste) — wouldn't that let more of the pipeline run unattended, outside a live Claude Code session with MCP access?

**As of Session 34: believed to be a dead end, three independent negative results.** `52 Week IV Rank` — the exact field Sieve 1 gates the entire pipeline on — appeared unavailable via REST: an exhaustive ~1,150-field snapshot sweep found no candidate field across 6 real tickers (IV Rank 28-91), the `Voyz/ibind` open-source reference library defined no such field either, and Tradier's API was checked too with the same negative result.

**Session 35 (Jul 26 2026): this was premature — the real field ID is now known, and the question is genuinely open, not closed.** A third source (`areed1192/interactive-broker-python-api`, an unofficial client for this exact Client Portal Web API) documents field **`7195`** as "52 Week IV Rank." Re-checked against the original probe's own saved raw response data: field 7195 was inside the swept range and was genuinely requested, but never appeared in any response — consistent with either "doesn't exist for this account" or "exists but gated behind a subscription entitlement the account didn't have that day." Bala's current Market Data Subscriptions include a paid US Equity and Options Add-On Streaming Bundle — not confirmed whether it covers this field, or whether it was even active during the original probe. A HANDOFF-style email to IBKR support and a live re-probe (`fields=7195` specifically) are both now warranted before concluding anything either way. Full detail: `research/ibkr_rest_api_probe/IBKR_REST_API_REFERENCE.md`'s "Confirmed NOT available" section, updated the same session this was found — don't trust this summary once that section has moved further.

**What was already true regardless, and still is:** IV Rank generally requires a full 52-week history of daily IV readings to compute, and most REST APIs (including Tradier's, also checked) expose only current/snapshot IV, not a historical time series — if field 7195 turns out to be genuinely inaccessible, this remains the likely structural reason. Everything else in the pipeline that legitimately *can* run via REST already does — price history and option chains both go through Tradier's REST API already (`technicals.py`'s data source, `contracts.py`'s chain source), not MCP.

---

## Constraint this scoreboard has to respect

Claude Web skills (uploaded `.md` files) **cannot execute Python** — they're prompt instructions read by an LLM with tool access (MCP, web search), not a code runtime. Any "conversion" therefore has one of two shapes:
- **(a) Runs in Claude Code**, where Python execution is real (Bash tool) — converts the skill from "LLM re-derives the math" to "LLM calls a script and reads the output." Fully deployable today.
- **(b) Runs inside one of the three engines' own backends** (`quant_math.py`, `gate_engine.py`, a new STA endpoint) — the skill's job shrinks to "call the API, hand back the result," matching what Directional Builder already does for MCP pulls. Requires coordinating with each engine, not just the hub.

Claude Web skills alone can never fully "convert" — they'll always keep the parts that need vision, live search, or judgment. The ceiling on the scoreboard reflects that, not a bug in the estimate. **Track 2 above is exactly option (a)** — this is what "fully deployable today" actually looked like once someone built it.

---

## Update log

- **Session 24 (July 10, 2026):** Scoreboard created. All skills read live (not from memory) to estimate the Python-able %. Zero conversions made yet — this session was measurement only.
- **Session 24 continuation (July 11, 2026):** No scoreboard changes — reconciled this file's own uncommitted state after a session interruption and committed it alongside the Known Issues correction in `CLAUDE_CONTEXT.md`.
- **Session 34 (July 25, 2026):** Real refresh after ~2 weeks stale — this file still said "0% converted, all skills 100% prompt-executed" while Sessions 30-33 built and live-used seven real Python modules under `research/forward_test/`. Added Track 2 to capture that honestly rather than let Track 1's unchanged 0% keep implying no progress had happened anywhere. Milestones 1-2 marked done (they were, months ago, just never checked off here). Also recorded the IBKR-REST-vs-MCP dead end (Session 32's own research, re-surfaced as a live question this session) so it doesn't get re-investigated from scratch next time someone has the same reasonable instinct.
