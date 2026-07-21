# Forward Test Protocol — Survivors vs. Rejects (v2, post-review)

> Designed Session 21 · **Revised same session after `FABLE_PRELAUNCH_REVIEW.md` (verdict: LAUNCH WITH FIXES — all six gating findings addressed below)**
> First entries: **Tuesday July 7, 2026 at the earliest** — gated on (a) Gemini confirming the `FWD_TEST:` exclusion rule (relay `HANDOFF_gemini_relay_session21.md`) and (b) a working quote source for marks. Monday July 6 = relay + green-path validation + dry-run of this procedure with no logging.
> Motivation: the WhatsApp gate-replay experiment (`research/WHATSAPP_SIGNALS_REVIEW.md` §8) proved the sieve stack **refuses** bad flow but produced no evidence it **discriminates**. This test generates that evidence live.

## The question this answers

*Do names that pass the full gate stack outperform names that narrowly fail it?*

Not "does the pipeline make money" — but "do the gates rank-order outcomes," which is the claim the WhatsApp replay could not test.

## Symmetry rules (review findings A1/A2 — the experiment is void without these)

Both groups get **identical, mechanical trade structure**. Gate status is the ONLY thing that differs between arms:

- **Contract:** nearest-ATM call (or put if the Directional Builder direction is bearish), nearest expiry inside 21–35 DTE. Same rule, both groups. **Standing exceptions (decided live, Sessions 25–26, applied consistently since):** if no monthly falls inside the window, use the nearest weekly inside it instead (Session 25). If this name has no expiry at all inside 21–35 DTE — no weekly exists in between its available expiries — use whichever available expiry overshoots the window by less, logged with an explicit DTE note (Session 26, first hit on INFQ: only 2-day and 37-day expiries existed; used the 37-day one as the closer overshoot).
- **Direction:** Directional Builder is run for BOTH survivors and rejects (rejects still get a Builder read — failing a sieve gate doesn't block the Builder from producing a direction). If the Builder outputs MIXED/no-direction for either group's name, that name is not logged (recorded in the hub CSV as `BUILDER_MIXED`, both groups alike — prevents silent survivorship inside the survivor arm).
- **Entry price:** bid/ask **mid at log time**, both groups, from a live quote the hub pulls itself. No Gemini-recommended pullback limits, no hypothetical fills — that's the fantasy-fill bug the WhatsApp review itself catalogued (§4.1).
- **Target / stop (mechanical, both groups):** stop = entry mid × 0.70 (the system's standard 30% hard stop); target = entry mid × 1.60 (+60% profit-take, R:R 2.0 on premium, clears the ≥1.5 floor being trialed). **Session 27 (Jul 16, 2026) briefly changed this to × 1.80 (+80%), then reverted to × 1.60 the same session** — Bala's call: faster regime turnover argues for locking in gains sooner rather than letting winners run further, and × 1.60 is also the originally pre-registered value, not a new number. No live positions were ever logged under the × 1.80 rule (the two positions logged in the interim, XLF id 21 and JD id 22, were built before the × 1.80 code change landed and already carry × 1.60) — so this reversion doesn't create a mixed cohort, just closes out a same-day round trip. The resolution script never recomputes a target — it always reads each trade's own stored `target_price`/`stop_loss`. Gemini's synthesized levels, if any, are recorded as metadata only and never drive resolution.
- **Quote-or-skip:** a position (either group) is only logged if the contract has a verified live quote (bid > 0 and ask > 0) at log time. A reject too illiquid to quote is recorded in the hub CSV as `NO_QUOTE`, not logged to the journal — see G1 below.

## Daily procedure (market hours, ~10 min, Claude Code with IBKR MCP)

1. Run PATH B Scanner on the CORE watchlist (EXTENDED if < 3 finalists).
2. **Log every finalist** (gate survivors) — **0 is a valid and expected count; never force a fill**. Stand-down days are recorded in the hub CSV (`group=STANDDOWN, ticker=NONE`).
3. **Log up to 3 near-miss rejects** — names that failed exactly one gate. Record which gate and the failing value.
4. Apply the symmetry rules above to construct both groups' positions; log to Gemini's journal (see below).
5. Daily thereafter: **the hub marks positions itself** — Tradier directly (`/markets/quotes` + `/markets/options/chains`, confirmed live Session 26) is now the primary path; IBKR MCP `get_option_data` is the fallback if Tradier is ever down — at bid/ask mid. Resolution is evaluated **on the daily mark, close-of-day basis** (consistent with the day-close stop discipline): mark ≤ stop → STOP; mark ≥ target → TARGET; held ≥ DTE × 0.60 → TIME; expiry → settle at intrinsic. **A "win" = resolved return > 0 after round-trip half-spread.** (Review A6: touch-based resolution is unimplementable with once-daily checks — resolution is mark-based, both groups, stated here so nobody "improves" it mid-test.)

**Resolution lockdown (Session 27, Jul 16, 2026):** `FWD_TEST:` positions may only be closed via the hub's own `research/forward_test/resolve_positions.py`, which calls Gemini's `PATCH /journal/resolve/<id>`. This followed a real incident — two positions (AFRM, AVAV) got closed the same day via the Gemini dashboard's native Close button, using intraday `last` price instead of the mandated close-of-day mid (accepted as the real recorded outcome, not reversed — see `forward_test_log.csv` notes on those two rows). A guard rejecting `/journal/close` and `/journal/update` status changes on `FWD_TEST:` rows was requested from Gemini's side (`HANDOFF_gemini_fwd_test_close_lockdown.md`) — until confirmed live, treat the dashboard's Close button as still capable of bypassing this on the Gemini side, and don't rely on it being blocked without re-verifying.

## Dedupe & migration (review A4)

- A ticker with an unresolved position is not re-entered **within the same group**.
- **Cross-group migration is allowed and logged:** if a rejected name later passes all gates (or a survivor's name later shows up as a reject), the new position IS taken in the other group, tagged `migrated` in the hub CSV. First-classification-wins would censor exactly the converts that carry the most gate information — biasing the test toward null.
- Idempotency: max one new position per ticker per group per day; before logging, check `/journal/history` for an existing open FWD_TEST row on that ticker+group.

## Where positions live: Gemini's paper-trade journal — with API traps mapped (review G1–G8)

Positions are logged via `POST localhost:5002/journal/log` with `setup_context` prefixed `FWD_TEST:SURVIVOR|` or `FWD_TEST:REJECT|` (exact string, no variants — group membership rides this prefix) followed by the gate blob: `failed_gate, ivr, iv_hv_pct, vix_regime, squeeze, rvol, trend_200d, rr_ratio, migrated`. **`vix_regime` added Session 30** (Interpretation Guardrails, Guardrail 3) — persists the STANDARD/HIGH-FEAR reading from the Scanner's own Phase 0 VIX pull so a regime-conditioned re-analysis is possible at n=30 without reconstructing it after the fact. Historical rows logged before Session 30 carry a blank `vix_regime` in `forward_test_log.csv` — not backfilled or guessed.

Hard-learned rules from the pre-launch code review of `app.py`/`database.py`:

- **G1 — CRITICAL: `/journal/monitor` can crash on our rows.** It calls `float(quote.get("last", 0))` and `.get()` on a possibly-`null` `greeks` object; Tradier returns null quotes for exactly the illiquid strikes rejects gravitate to, and one bad quote 500s the whole endpoint — killing marks for **Gemini's real positions too**. Mitigations: the quote-or-skip rule above; the hub never depends on `/journal/monitor` for marks (advisory only); a hardening suggestion (per-trade try/except + null-greeks guard) is in the relay.
- **G2:** monitor marks with `last`, not mid — never use its numbers as experiment marks (systematically stale on illiquid contracts, violates the marking rule).
- **G3:** `/journal/log` returns no row id, and `/journal/close` silently succeeds on a nonexistent id. After every log: `GET /journal/history`, capture the new row's `id` into the hub CSV. After every close: re-read history and verify status flipped.
- **G4:** **never call `/journal/update` on a FWD_TEST row** — it nulls omitted fields and can wipe `final_pl` on closed rows. Resolution reason/metadata live only in the hub CSV.
- **G6:** never analyze `high_water_mark` — the monitor (a GET that writes state) mutates it on every frontend poll; it is not our data.
- **Dependency — resolved, path flipped (Session 26, Jul 15):** Tradier token is alive (confirmed working for `/markets/quotes` and `/markets/options/chains` directly, via curl using the token in `options_iq_gemini/.env` — the Fundamentals Beta gap that killed the earnings calendar is unrelated and doesn't affect chains/quotes). `get_option_data` (IBKR MCP) proved intermittent within a single session — 4/4 clean at ~09:15 ET, 5/5 failed at ~14:30 ET, with `get_price_snapshot` on the identical contract succeeding immediately after the failure (ruling out a session-wide outage). **Tradier is now the primary path for chain construction and daily marks; IBKR MCP `get_option_data` is the fallback**, not the other way around as originally written here.

## What stays hub-side (`forward_test_log.csv`)

Stand-down days, `BUILDER_MIXED` / `NO_QUOTE` records, journal row ids, resolution reasons, migration tags — plus, at analysis time, a full export of tagged journal rows merged with these records. The CSV is the experiment's book of record for everything the journal can't hold.

## Success criterion — pre-registered, single AND clause (review A3)

**The gates discriminate if and only if:** the bootstrap 95% CI of (survivors' mean resolved return − rejects' mean resolved return) excludes zero **AND** the point estimate exceeds the mean round-trip spread cost. Win-rate difference is reported alongside (Newcombe interval, not per-group Wilson) but is **not** a pass condition — n≈30/group only detects a ~±25pp win-rate gap, and pretending otherwise is how goalposts move.

**Power honesty:** at n=30/group this test detects only large effects. A null result means "no large effect detected," not "gates don't discriminate."

**Survivor-shortfall rule (pre-registered):** if < 15 resolved survivors by Sept 15, extend to Oct 31. If still < 15, the result is reported as **"insufficient survivor flow"** — itself a finding about gate strictness in this regime, not a failure to be tuned away.

## Sample-size and timeline expectations

- 3 weeks ≈ 15 trading days ≈ 10–20 **unique** setups after dedupe (not 45 — setups persist across days), plus the stand-down record. Survivor flow may be far thinner than reject flow — that asymmetry is data, see shortfall rule.
- First resolutions: ~2 weeks in (time stops). Expiry wave: weeks 4–5. 30 resolved per group ≈ mid-September *if flow allows* — see shortfall rule; no conclusions before resolution counts are met, interim looks labeled interim.

## Rules of honesty (from the WhatsApp review's failure catalog)

- Losses are logged the day they resolve, same rigor as wins. No editing resolved rows (enforced structurally: G4 — update endpoint is never used).
- If a daily check is missed, the gap is logged as a gap (`MISSED_DAY` row in the CSV); marks resume next session — never backfilled from memory or interpolated.
- Premium marks are bid/ask mid at the daily check; if the chain is a desert, that IS the data point.
- If the Scanner produces zero finalists for a week straight, that is a result about market regime, not a malfunction to be tuned away mid-test.

## Interpretation Guardrails (added Session 30, Jul 21 2026)

**Why this section exists:** the success criterion above (n≈30/group, pre-registered bootstrap CI) governs when a *conclusion* is valid. It says nothing about what's allowed *before* that — and a live session on Jul 21 (n=11 resolved) drifted straight into narrating an interim REJECT-outperforming-SURVIVOR read as if it meant something, then ran an unplanned sub-analysis (breaking rejects down by how close each missed the IV/HV line) and started treating that breakdown like a finding too. Neither was wrong to *look at* — both were wrong to *narrate as evidence* without saying so explicitly. This section closes that gap. Without it, the experiment's real risk isn't "not enough data" — it's "enough half-formed narratives accumulate before n=30 that everyone's already decided what the answer is going to be," which makes the eventual confirmatory test theater, not science.

### The three states of the data

1. **MONITORING** (any n, always allowed) — purely descriptive: resolved count per group, win rate, open positions, regime tags. No causal language ("the edge is...", "rejects are winning because..."). No threshold-change discussion triggered by a monitoring number.
2. **EXPLORATORY** (any n, always labeled) — a sub-analysis not specified in the pre-registered criterion (e.g., "how close did each reject miss the IV/HV line by," "does squeeze-firing status split the reject group"). Allowed and often useful — but every single time it's surfaced, it carries the label `EXPLORATORY — not confirmatory, n=[X]` and gets an entry in `FORKING_PATHS_LOG.md` (see below). An exploratory finding is a hypothesis for the eventual confirmatory pass, never a standalone conclusion.
3. **CONFIRMATORY** (only at n≥30/group, only via the exact bootstrap-CI method already pre-registered above) — the only state in which "the gates discriminate" or "the gates don't discriminate" may be asserted as a result.

**Rule: every time interim results are discussed, state which of the three states the discussion is in.** If unstated, default to MONITORING — the most restrictive.

### Guardrail 1 — Peeking is fine, acting on a peek is not

Daily marking requires looking at the data constantly; that's not "peeking" in the p-hacking sense and is not banned. What's banned: changing a gate threshold, a sieve, the IV/HV cutoff, or any other pipeline rule *because* an interim read looked a certain way. The only three legitimate reasons to change something mid-test are Guardrail 5 below — "the pattern looked convincing" is explicitly not one of them, no matter how many trades it's based on, until n=30/group and the pre-registered method says so.

### Guardrail 2 — Every exploratory question gets logged, not just the ones that pan out

New file: `research/forward_test/FORKING_PATHS_LOG.md`. Every exploratory question asked of the data gets an entry: date, n at the time, the question, and the answer — logged whether or not it looks interesting. This is what makes it possible to later tell the difference between "we predicted this in advance" and "we went looking until we found something that fit." A sub-analysis that isn't logged before the confirmatory pass doesn't get to count as having been predicted.

### Guardrail 3 — Confound tracking, not post-hoc reconstruction

Two confounds are already visible and neither is currently tagged per-trade: (a) **regime** — Gemini's own Phase 17 note and this session's own read both independently suspect the kinetic-timing signal (squeeze/RVOL), not the IV/HV edge, may be doing the work, especially if the current regime is "lifting all compression setups" generally; (b) **daily-checkpoint overshoot** — resolution only checks once a day, so realized win/loss magnitudes systematically exceed the nominal ±60%/−30% (confirmed this session: avg TARGET +76% vs nominal +60%, avg STOP −42% vs nominal −30%). Going forward, every new row in `forward_test_log.csv` should carry the VIX regime at entry (already computed at Scanner Phase 0 — just persist it) and the squeeze status (already a column) so a regime-conditioned re-analysis is possible at n=30 without reconstructing history from memory or chat logs.

### Guardrail 4 — magnitude is not the primary lens pre-n=30

Because of the checkpoint-overshoot artifact (Guardrail 3b), individual trade return magnitudes are noisy in a known, systematic direction and should not be quoted as if they were clean. Win rate (with n stated) is the primary MONITORING-state metric; magnitude-based statements belong in EXPLORATORY state only, labeled as such.

### Guardrail 5 — the only legitimate reasons to stop or change something before n=30/group

(a) The survivor-shortfall rule already pre-registered above. (b) A genuine data-integrity break — a resolution bug, a dead token, a marking error — which pauses the test for a fix, never triggers a conclusion. (c) Bala's explicit judgment call for reasons outside the statistics (the project's existing pattern — e.g., cutting HIVE from the watchlist was a content decision, not a stats decision). **Not a legitimate reason:** "the interim number is already convincing" — that's precisely the failure mode this section exists to block.

### Pre-registered secondary test — IV/HV near-miss margin (locked Session 30, Jul 21 2026)

`FORKING_PATHS_LOG.md` Entry 2 (Jul 21, n=11 resolved) surfaced a real hypothesis: the IV/HV<100% cutoff may behave as a smooth gradient near the boundary rather than a sharp discontinuity, meaning near-miss REJECTs may perform statistically indistinguishably from just-qualifying SURVIVORs while far-miss REJECTs may show a real gap. This was not part of the original pre-registered criterion. Per Guardrail 2, it graduates from exploratory to confirmatory only if locked before more data accumulates — so it's locked here, now, at n=11:

**Margin buckets (fixed, based on `failed_value` for IV/HV-gate REJECTs only):** `NEAR` = missed by <2 points (100.0–101.99%), `MID` = missed by 2–10 points (102.0–109.99%), `FAR` = missed by >10 points (≥110%). SURVIVORs are not bucketed — they're the single comparison group.

**Secondary success criterion (reported alongside the primary one, never in place of it):** at n≥30/group for the primary test, compute the bootstrap 95% CI of (SURVIVOR mean return − NEAR-bucket REJECT mean return) separately from (SURVIVOR mean return − FAR-bucket REJECT mean return). If NEAR's CI includes zero while FAR's excludes it, that's evidence for the gradient hypothesis. This is exploratory-graduated-to-secondary, not primary — the primary criterion (undifferentiated REJECT vs SURVIVOR) remains the test that decides whether the gates discriminate. A significant secondary result without a significant primary result is a calibration finding (move the cutoff), not a validation of the pipeline as currently configured.

**Power note:** splitting REJECT into 3 buckets divides an already-thin arm three ways — this sub-test will likely need well past n=30/group to say anything, and that limitation is stated now, not discovered later when the split looks underpowered.

### Guardrail 6 — the standing interim check-in template

Any time results are reported before n=30/group, use this shape, in this order:
1. **State:** which of the three states (almost always MONITORING or EXPLORATORY).
2. **n:** resolved count per group, open count per group.
3. **The number** (win rate, or whatever's being reported) — MONITORING only, no causal framing.
4. **Standing banner:** *"NOT YET INTERPRETABLE — pre-registered n≈30/group not reached; see FORWARD_TEST_PROTOCOL.md's Success Criterion."*
5. If anything exploratory is being discussed: label it, and confirm it's been added to `FORKING_PATHS_LOG.md`.
