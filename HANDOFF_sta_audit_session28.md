# HANDOFF: STA (Swing Trade Analyzer) — Hub Audit Findings (Session 28, Jul 17 2026)

> **Status:** DRAFTED, not yet relayed. First time hub-side Claude has audited this engine.
> **Source:** `HUB_AUDIT_FRAMEWORK.md` — one Fable agent, Coherence Audit Layer 1 (docs match code) only, scoped to `README.md`, `docs/SWING_TRADING_REFERENCE_BUNDLE.md`, `docs/STA_BREAKOUT_HUMAN_IN_LOOP_WORKFLOW.md` against the specific code those docs reference.
> **Scope note, stated up front:** this run deliberately did **not** honor STA's own Day-50 lesson ("spot-check = 92.8% pass, exhaustive = 21% pass — always check every item"). The codebase is ~20,236 lines against 3 relatively thin doc files; a full exhaustive read is out of scope for a routine hub-triggered pass. Everything below is real, but it is not a substitute for STA's own internal audit cadence — treat this as a lightweight external sanity check, not a Category 1-9 run. A `"run the hub audit — STA deep"` variant exists in `HUB_AUDIT_FRAMEWORK.md` for full-exhaustive coverage on request.

## Findings — all staleness, no fabrications, no CRITICAL/HIGH

**1. README teaches a dead OHLCV fallback chain.** README (lines 349, 464, 479, 1127) still describes "TwelveData → yfinance → Stooq," with Stooq as "last resort." Live code (`backend/providers/orchestrator.py:92`): `[twelvedata, yfinance, tradier]` — Stooq was removed Day 82 ("dead, bot-blocked") and Tradier is the real third tier (Day 83). Stooq is still instantiated for status reporting but never called. **MEDIUM** — this is the one most likely to mislead a reader about actual failure behavior.

**2. The "9-criteria checklist" feature description still shows flat thresholds.** README:134 describes flat stop/volume thresholds (7% / $10M). `simplifiedScoring.js:121` and `liquidityThresholds.js:16-19` moved to cap-aware tiered thresholds (7%/9%/10% by cap size; $10M/$5M/$2M by cap size) back on Day 70B — and README's own changelog (v4.32, line 1272) records the change. The feature-list section just never got updated to match. **MEDIUM.**

**3-10 (LOW/INFO, batch when convenient):** Fear & Greed band edges in README (60-80/35-60) don't match `categoricalAssessment.js:481-507`'s actual bands (55-80/40-55) — informational only, doesn't affect verdict. Validation tolerance numbers in README (revenue_growth 50%, debt_equity 40%) are swapped/stale vs. `validation/engine.py:93-95`'s real 0.25/0.50. Decision Matrix / BottomLineCard still appear in the architecture diagram and Usage steps despite README's own feature list already saying they were removed Day 70. The Breakout doc's "Future v3 Enhancements" section (STA backend endpoint, Breakout scan tab) describes features that are already shipped (`backend.py:137-150`, `1929-2029`) — stale enough to risk someone duplicating already-done work. README's provider count says "5," code has 7 files (6 active + 1 dormant FMP kept for a future paid plan). Version footer: README says v2.33/Day 65, code is `BACKEND_VERSION='2.43'` and the file's own newest content is Day 88-89 — about 24 days of footer drift. `SWING_TRADING_REFERENCE_BUNDLE.md` presents itself as the current checklist but is a self-declared Day 33/v3.4 snapshot for bootstrapping other projects — drift here is by design, but nothing in the header warns a reader it no longer matches current STA.

## Confirmed clean (spot-checked)

Support/resistance engine (ZigZag 5%, 2% agglomerative merge, touch scoring, Fib extensions, MTF confluence weights) — all match `support_resistance.py` exactly. Technical/fundamental assessment thresholds, verdict logic (2 Strong + Favorable/Neutral = BUY, Weak Technical = AVOID non-negotiable), cache TTLs, circuit breaker (3 failures → 5min cooldown), fundamentals provider chain, pattern actionability threshold, all 7 Pine breakout statuses, and the backtest numbers STA's own README already honestly discloses as re-validated (PF 1.61 → 1.40 on unbiased re-check) — all verified against live code, no drift found.

## Recommendation

No urgent action needed — nothing here affects trading decisions, it's all documentation lag on a fast-moving codebase. Worth a documentation pass next time STA's own session does routine maintenance, prioritizing the OHLCV fallback chain (#1) and the checklist thresholds (#2) since those are the two most likely to actively mislead a reader rather than just look outdated.

---

## Part 2 — Tab-by-Tab Methodology Audit (Layer 2, Session 28 continued, Jul 18 2026)

> Different from Part 1 above: this is not doc-vs-code coherence, it's "is the actual logic behind each UI tab sound." 5 Fable agents, each scoped to strict line ranges (`HUB_AUDIT_FRAMEWORK.md`'s "STA Tab-by-Tab Methodology Audit" section has the full prompts — trigger with `"run the hub audit — STA tabs"`). **0 CRITICAL findings, 8 HIGH-equivalent, and — genuinely worth noting — no fabricated data found anywhere across all 5 tabs.** The one repeating pattern: STA's code comments are consistently more honest than its UI. Several screens present more rigor/authority than the underlying implementation has.

### Sectors tab — 2 HIGH-equivalent

**1. "RS Ratio 100 = market parity" is false.** `backend.py:2304-2312` computes RS Ratio as a raw price-ratio indexed to 100 at a **static midpoint date** (~3 months back), not a real de Kempenaer RRG normalization — the code even has an honest comment saying so ("swing-trading variant, NOT standard de Kempenaer RRG"). But `SectorRotationTab.jsx:286,302` tells the user 100 means market parity. It doesn't — a sector could underperform SPY all year and still read above 100 if it did even worse before the anchor date.
*Fix:* either implement real EMA-based normalization, or correct the UI copy to describe what the number actually measures.

**2. Footer data-source label is wrong.** `SectorRotationTab.jsx:302` says "Data from TwelveData"; the actual fetch (`backend.py:2276`) uses yfinance.
*Fix:* one-line label correction.

**Also:** no smoothing/hysteresis at the exact 100/0 quadrant boundaries — a sector near either line will flicker quadrants day-to-day on noise (`backend.py:2310, 2324-2331`). The prominent "Scan Rank #1" button bypasses the Leading/Improving-only scan gate that every other per-sector button respects (`jsx:247-257` vs `jsx:172-180`).

**Alex's verdict (Opus persona pass, Jul 18): FIX BEFORE TRUSTING, not KEEP or REBUILD.** All 4 findings above confirmed independently. The underlying idea — rank sectors by trailing ~3-month performance vs SPY — is a legitimate, usable heuristic; the problem is entirely in what the UI claims about it, not the ranking itself. Added one more: `jsx:45` renders `.toFixed(3)` — three decimals of false precision on an approximate, single-anchor-day-dependent number. Priority fix order Alex gave: (1) kill "market parity" copy everywhere, replace with an accurate one-liner ("100 = flat vs SPY over the lookback; >100 = outperformed over ~3mo"); (2) fix the TwelveData→yfinance label; (3) gate the Rank #1 CTA the same way per-card buttons are gated; (4) drop precision to 1 decimal; (5) give staleness visual weight past ~1 trading day, not just gray micro-text. Alex's own read: "the ordering, yes, I'd use it — with my own mental translation of what it means. The tab's stated framing, no — I'd have to ignore what it tells me the numbers mean. That gap is why it's FIX, not KEEP."

### Analyze + Scan tabs — 3 HIGH-equivalent

**1. Scan and Analyze are two unrelated logic paths that can disagree on the same ticker.** The Scan tab's TradingView-column filters never call the same pattern/breakout/trend-template functions the Analyze tab uses (`backend.py:1824-1994` vs the engine modules).

**2. The Scan tab's "Minervini" strategy checks only 2 of Minervini's real 8-criteria Trend Template** (close>SMA50>SMA200, cap≥$10B, 1W/1M change≥0 — `backend.py:1896-1904`) while presenting itself as "Minervini SEPA … Stage 2 uptrend" (`backend.py:2009-2012`). A ticker can pass this scan and fail the real trend template on the Analyze tab. Same overstated-pedigree pattern as the Value tab's "Buffett"/"Damodaran" badges (Part 2, Context+Value section below).

**3. Cup & Handle's documented "1-4 week handle" duration is never enforced in code** (`pattern_detection.py:474` claims it, `:556-571` never checks it).

**Positive finding, stated plainly:** where STA does name a real methodology (Minervini Trend Template criteria, O'Neil Cup & Handle depth 12-35%), the actual numbers genuinely match the published methodology — this isn't fabricated, just inconsistently attributed elsewhere (breakout thresholds, pattern confidence weights are unattributed constants with no cited justification).

**Alex's verdict (Opus persona pass, Jul 18): the "Minervini" mislabel is MUST-FIX, HIGH severity — everything else here is LOW/MEDIUM cleanup.** On closer read it's worse than the Fable pass first flagged: the scan is really 1 exact match + 1 loose proxy of Minervini's 8 real criteria (not "2 of 8" cleanly), and the "$10B+ large-cap" framing actively *contradicts* what Minervini is known for (small/mid-cap breakout leaders, not mega-caps). Aggravating factor: the correct, full 8-criteria implementation already exists in the same codebase (`pattern_detection.py:229-295`) — so this is a naming lie, not a capability gap or data limitation. **Single highest-priority fix Alex would make:** strip "Minervini/SEPA/Stage 2" from the label (`backend.py:2010-2011`). **Bala's explicit call (Jul 18): don't rename this as a lesser "proxy" of someone else's method either.** STA's actual pattern-recognition system (the full 8-criteria Trend Template, VCP, Cup & Handle — all correctly implemented in `pattern_detection.py`, plus the genuinely backtested `best` strategy) is a real, good system in its own right — better in places than a borrowed label implies. The fix isn't "call it a cheaper Minervini," it's "give it its own name that describes what it actually does" (e.g. something like "Large-Cap Momentum Filter" for this specific 2-filter scan preset — un-borrowed, not framed as a downgrade of anything). Don't try to cram the full template into the TradingView query either way — if a scan that uses the real 8-criteria template is wanted, pipe survivors through the existing `check_trend_template()` function as a post-filter, reusing STA's own correct implementation rather than forking a second one.

**Two things Alex explicitly defends as correctly designed, not findings:** the "frozen" `market_phase_engine.py` — clearly labeled informational-only, never touches the verdict, and says so out loud in its own docstring; and the `best` scan strategy, which is genuinely backtested (238 trades, 53.78% win rate, profit factor 1.61, p=0.002) and correctly shares one implementation with the paper-trading engine rather than duplicating logic — "the gold standard the rest should aspire to."

### Context + Value tabs — 0 HIGH, but one worth fixing

**Value tab's ROE thresholds are badged "Buffett"/"Damodaran" in the UI** (`ValueTab.jsx:158,177,191,291`) but the code comment for their actual origin says "ChatGPT research validated" (`backend.py:2826`) — not those two named sources. The Graham Number formula itself IS genuinely Graham's real formula, correctly implemented. No fabricated fallback values found anywhere in this tab (errors fail visibly). Minor: a growth-rate unit-guessing heuristic (`backend.py:2929`) can misread large growth values; the market-context aggregator can render "NEUTRAL/mixed signals" when it actually just has too little data to conclude anything (`backend.py:2570-2577`).

### Validate + Data Sources tabs — 2 HIGH

**Missing/never-fetched data renders identically to genuinely fresh data** — `backend.py:740,756,771,846-847`: a ticker with zero cached data shows `'live', ageMinutes: 0, 'fetching fresh'`, the same status a just-fetched ticker would show. VIX/Fear&Greed/Sector-source labels are hardcoded strings never actually probed against real fetch success (`backend.py:774,801,793`). `/api/health` reports `'status': 'healthy'` unconditionally regardless of actual subsystem state (`backend.py:626-627`). Same bug family independently found in `HANDOFF_optionsiq_audit_session28.md`'s frontend quality-banner findings — worth treating as a pattern across both engines, not a one-off.

### Forward Testing tab — 1 HIGH

**Stop/target levels are recorded at trade entry but the daily resolution step doesn't actually read them back** — `daily_job.py:114-122` re-runs the full simulator fresh from entry to today using current code each time, rather than checking against the stored `initial_stop_price`/`initial_target_price`. If the simulator logic changes mid-test, open positions retroactively resolve under the new rules with no ledger trace of the change. Entry fills themselves are honest (real next-day open price, measured slippage) — comparable rigor to Gemini's forward test on that specific point. Also: momentum-path trades store identical net/gross P&L (`daily_job.py:127-129` — fee accounting not actually differentiated for that path), and per-position fetch failures are silently dropped rather than logged, which could bias results if failures correlate with bad outcomes.

### Recommendation

None of these are urgent — no fabricated data anywhere, and where real methodologies are named, the numbers back it up (confirmed independently by both the Fable pass and the Alex/Opus persona pass on Sectors and Analyze+Scan, Jul 18). Priority order across the whole tab audit, per the two Opus verdicts plus the 3 Fable-only tabs:

1. **The "Minervini" scan mislabel** (Analyze+Scan) — Alex's own MUST-FIX, HIGH. A user can read "Minervini SEPA, Stage 2 uptrend" and size a position on pedigree the calculation never earned, when the correct implementation already exists one file over.
2. **Sectors' "100 = market parity" claim and the TwelveData/yfinance label** — both outright false statements on screen, cheap one-line fixes.
3. **Forward Testing's exit-rule re-derivation** — the one place a future code change could silently re-grade trades already in progress with no ledger trace, the same class of integrity concern the hub's own `FORWARD_TEST_PROTOCOL.md` was built to prevent for Gemini.
4. Everything else (Value tab's overstated "Buffett/Damodaran" badges, Validate/DataSources' "live"/"healthy" labels that don't reflect real fetch success, unattributed tuning constants) — real, worth fixing, but none of it is trading-decision-critical on its own.
