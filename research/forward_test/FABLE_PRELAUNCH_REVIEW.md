# FABLE PRE-LAUNCH REVIEW — Survivors-vs-Rejects Forward Test
> Reviewer: Fable 5, fresh eyes, no authorship investment · July 6, 2026 (launch day)
> Scope: Tier A = `FORWARD_TEST_PROTOCOL.md` · Tier B = `WHATSAPP_SIGNALS_REVIEW.md` methodology · Tier C = Gemini journal subsystem (`app.py` 897–1085, `database.py`) — read-only
> Verdict: **LAUNCH WITH FIXES** — see the fix list at the end. Nothing here requires abandoning the design, but four ambiguities and two operational gates must be closed BEFORE the first row is logged, because after row one they become unrecoverable.

---

## 0. What is GOOD — do not touch

1. **Pre-registration exists at all.** A success criterion, timeline, and "nobody moves the goalposts" section written before day one is rarer than the edge being tested. Keep the spirit; fix the letter (Finding C1).
2. **Stand-down days recorded as data** (`group=STANDDOWN, ticker=NONE`). "Zero finalists for a week is a result about regime, not a malfunction" is exactly the right epistemics and directly encodes the system's most-validated behavior (refusal).
3. **Same-day, same-watchlist control.** Survivors and rejects are drawn on the same days from the same universe — market-regime and universe confounds are controlled by construction. This is the single strongest design property; everything else should bend to preserve it.
4. **`failed_gate` + failing value recorded per reject.** Enables per-gate stratified analysis later even if aggregate n is thin. Don't drop this to save typing.
5. **Dedupe rule (one setup = one trade).** Directly repairs the pseudo-replication flaw the review itself found in the random-entry control. Right instinct — see Finding A4 for its side effect, but keep the rule.
6. **Rules of honesty** — losses logged day-of, no editing resolved rows, "OI desert IS the data point." The last one is a genuinely good pre-commitment against the classic silent-substitution corruption.
7. **FWD_TEST tagging + relay exclusion rule.** Contamination of Gemini's 1W/5L record was anticipated and guarded. The guard is not yet armed (Finding O1), but the design is right.
8. **`forward_test_log.csv` header already includes a `resolution` column** — the close-reason field the journal lacks. Good; formalize its role (Finding A6).
9. **Tier B: the verification-first methodology of the WhatsApp review.** Verifying 764 signals against real OHLC instead of the group's claims, conservative collision handling, the delisted-ticker survivorship caveat, and above all §8's three-conclusion honest reading ("refusal validated, discrimination unproven") — the review resisted the temptation to claim more than the data supports. The forward test exists precisely because the review was honest. Keep that standard.
10. **Tier C: the Phase 12 zero/None entry-price guard in `/journal/monitor`** (app.py:980–985) is correct, and the hub's Known Issues note about `entry_price or 1.0` at app.py:590 is **stale — the pattern no longer exists in the live file** (line 590 is now scanner code). One point to the live-read rule; update the Known Issues table.
11. **Using Gemini's journal instead of a hand-rolled CSV** is the right call in principle (existing monitor, existing UI, one store) — with the caveats in Tier C below.

---

## TIER A — Experiment design

### A1. CRITICAL — Reject-arm scoring procedure is underspecified; as written, the experiment can measure target-setting, not gate discrimination

Protocol step 4: survivors that clear Directional Builder get "the system's own entry / target / stop / expiry." Rejects get "the same hypothetical structure (nearest 21–35 DTE, ATM-zone strike)." Three unanswered questions, each fatal to comparability:

- **Direction.** Survivors get direction from the Builder's 8-signal strict-majority inference. Rejects never run the Builder. Who decides call vs put for a reject? If it's "200d trend" or reviewer judgment, the two groups have different direction-selection procedures, and direction dominates single-leg option outcomes. *Failure scenario:* rejects get naive trend-following direction in a chopping market, survivors get the Builder's multi-signal read; survivors "win" and you publish gate discrimination when you actually measured the Builder's direction engine.
- **Target/stop provenance.** Survivor targets/stops come from Gemini synthesis; the protocol never says how reject targets/stops are set. The WhatsApp review's own core finding (§5, §6.3) is that **geometry dominates outcomes** — 50% accuracy prints money at 1.8:1. If reject geometry is set by a different procedure (mechanical %, ATR multiple, reviewer eyeball), win rates are incomparable by construction. *Failure scenario:* reject targets are set slightly closer than survivor targets → rejects hit "wins" more often → gates look useless; or the reverse → gates look brilliant. Either way the result is an artifact.
- **Survivors that fail Directional Builder.** Step 2 logs every finalist; step 4 only gives contracts to those that "also clear Directional Builder." What happens to a finalist that doesn't clear? If it's logged but unscoreable, it silently drops out of the survivor sample — post-gate selection *within* the survivor group, i.e., survivors of the survivors. *Failure scenario:* the Builder disproportionately drops the weakest finalists; the survivor group's measured performance now reflects gates + Builder, but you attribute it to gates.

**Fix (before first entry):** write one paragraph into the protocol: (a) reject direction = output of the *identical* Directional Builder run on the reject ticker (run it; it's 2 minutes of MCP); (b) both groups' target/stop = one mechanical rule applied identically (e.g., target = entry premium × 2.0, stop = entry premium × 0.70, or an underlying-ATR rule — pick one, write it down); Gemini's synthesized levels are recorded as metadata, not used for scoring; (c) a finalist that fails the Builder is logged with a `builder_fail` note and *still gets the mechanical structure* — no silent drops.

### A2. CRITICAL — Entry price rule is unspecified: the limit-fill fantasy bug the review itself catalogued

Nothing in the protocol says what `entry_premium_mid` is. If survivor entries are logged at Gemini's *recommended* entry (often a pullback limit below current mid), positions that would never have filled get scored from a fantasy price — the exact flaw §4.1 flagged in the WhatsApp group's method ("stock fills are modeled, not actual"), reproduced in our own experiment. *Failure scenario:* Gemini recommends entry $1.20 when mid is $1.45; the option never trades at $1.20 and runs to $2.40; the survivor logs +100% on a fill that didn't exist; rejects, logged at live mid, carry no such subsidy. Survivor outperformance is manufactured.

**Fix:** entry = bid/ask mid at log time, both groups, no exceptions. Recommended-entry recorded as metadata only.

### A3. CRITICAL — The pre-registered success criterion is statistically incoherent and contains a p-hacking door

Line 42: "win rate difference with 95% Wilson CI excluding zero **OR** mean return difference > spread cost."

- **The OR arm has no test.** "Mean return difference > spread cost" is a point-estimate threshold. Option returns at n=30/group are heavy-tailed (±100% swings); the sample mean difference will exceed a few-percent spread cost by pure luck close to half the time. As written, the criterion is nearly a coin flip that only needs to land once. *Failure scenario:* win rates identical, one survivor lottery ticket prints +180%, mean difference = +6% > spread cost, experiment declared a success, R:R floor gets formalized into the Builder on noise.
- **Wilson CI is for a single proportion.** For a *difference* of proportions you need Newcombe's score method (or bootstrap). Pedantic, but a pre-registration that names the wrong test invites analysis-time improvisation — the thing pre-registration exists to prevent.
- **Power: n=30/group detects only enormous effects.** At worst-case p≈0.5, the 95% CI half-width on the win-rate difference is **±25 percentage points**. A plausible real effect (10–15pp) is undetectable; only a ~25pp+ gap can clear the criterion. This must be stated up front, or a true-but-moderate edge will be reported as "gates do not discriminate" with unearned confidence.

**Fix:** rewrite the criterion as: *primary* = difference in mean return per trade, 95% bootstrap CI excluding zero AND point estimate > round-trip spread cost (define spread cost: sum of half-spreads at entry and exit marks, in % of premium); *secondary* (reported, never decisive alone) = win-rate difference with Newcombe 95% CI. Add: "n=30/group can only detect a win-rate gap ≳25pp; a null result is 'not detected at this n,' never 'proven absent.'" One AND, no OR.

### A4. HIGH — Ticker migration + first-classification-wins biases toward null, and group samples are not independent

The dedupe rule ("open in either group → not re-entered") means a ticker's classification is frozen while open. Gate values fluctuate daily (RVOL crosses 1.5, squeeze fires, IVR drifts). *Failure scenario:* NVDA logged Monday as REJECT (failed RVOL at 1.3); Wednesday RVOL hits 1.8 and it's a genuine full-stack survivor — but it's locked in the reject group holding the setup the gates just endorsed. The control group systematically accumulates names *on their way to passing*, and the survivor group is censored of exactly those names. This drags the measured difference toward zero — the design's thumb is on the null's side of the scale. Second-order: with a ~20-name CORE watchlist over 10 weeks, the same tickers will appear in both groups sequentially, and all positions share market beta in the same window — the win/loss outcomes are **not independent**, so any binomial CI (Wilson, Newcombe, whatever) is anti-conservative as stated.

**Fix:** keep the dedupe rule (it's still right on net) but (a) log a `converted_while_open` note when an open reject later passes the full stack — at analysis time these rows can be examined separately; (b) add one sentence to the criterion: "CIs assume independence; overlapping-ticker and common-regime correlation make them optimistic — stated up front."

### A5. HIGH — The survivor-side sample-size promise is contradicted by every piece of evidence the project owns

"30+ resolved positions per group ≈ mid-September" needs ≈3.3 *resolved survivors per week* for ~9 weeks. Against that: the May full-pipeline live test produced 0 finalists (all NO TRADE); the gate replay refused 121/121; the protocol itself says "0 is a valid and expected count" and estimates 10–20 unique setups in 3 weeks *combined across both groups*. Extrapolated, that's ~33–66 combined by week 10 — of which survivors will be the minority, because near-misses (fail exactly one gate) are by construction more common than full passes. Survivor n by mid-September is plausibly 5–15, not 30. *Failure scenario:* mid-September arrives with 31 rejects and 9 survivors; there is no pre-registered rule for this, so the analysis either runs underpowered and over-claims, or the timeline silently extends — goalpost-moving by omission.

**Fix (one sentence, pre-registered now):** "If either group has <30 resolved by Sept 15, the test extends until both reach 30 or Nov 30, whichever first; if survivor flow can't reach 30 by Nov 30, the headline result is 'survivor scarcity — gates refuse too often to measure discrimination at this cadence,' which is itself the answer to the research question."

### A6. HIGH — "Win" is never defined, and touch-based resolution is unimplementable with once-daily checks

The criterion turns on "win rate," but the protocol never defines a win. Is a time-stop exit at +4% a win? An expiry at −8%? Second problem: resolution on "target touch" requires continuous observation; the procedure is a once-daily ~10-minute check with no historical intraday option data (the exact gap §3 lamented for the WhatsApp options). In practice "target touch" will silently degrade to "target observed at the daily check" — fast spikes that reverse intraday are missed, understating both groups' win rates and adding noise. Third: the journal has **no field for resolution reason** (Tier C, G4), so the `resolution` column in `forward_test_log.csv` is the *only* home for this datum — making the CSV primary for it, contradicting "the CSV is an analysis artifact, not the primary store."

**Fix:** pre-register: WIN = resolved return > 0 (any resolution path); resolution triggers are evaluated **at the daily check only** — restate "target touch" as "target reached at or before the daily mark"; the `resolution` column in the CSV is declared the primary store for close reason (target/stop/time/expiry), written the day of close, never edited.

### A7. MEDIUM — Reject selection among multiple near-misses is a cherry-pick door

"Log **up to 3** near-miss rejects" — on a day with 6 names failing exactly one gate, which 3? Unspecified selection is where unconscious bias lives; the operator (who wants the gates to work) picks rejects that "feel" doomed. **Fix:** deterministic rule — the 3 whose failing value is *closest* to the gate threshold (truest near-misses), ties broken alphabetically.

### A8. MEDIUM — No missed-day rule

Over 10 weeks, days will be missed (travel, token death, illness). A missed day delays stop/target detection; the eventual exit is recorded at a later, different price — direction of bias unknowable per event, but it corrupts returns and the day-close stop semantics. **Fix:** pre-register: on a missed day, next check marks as normal, logs `missed_day` in notes, and resolution uses the observed price at the actual check — no retroactive reconstruction of what "would have" resolved. (Honest degradation beats fabricated backfill.)

### A9. MEDIUM — Reject chains are unscreened for liquidity; survivors are OI>500/spread<10% screened

Asymmetric measurement error: survivor marks come from tight markets; reject marks from potential deserts. The "OI desert IS the data point" rule is right, but at analysis time wide-market noise in the reject arm inflates its return variance and makes mid-marks less meaningful. **Fix:** record OI and spread% for both groups at entry (columns exist half-way already); report the liquidity distribution of both arms alongside the headline numbers.

---

## TIER B — The WhatsApp analysis the design rests on

Overall: the review's conclusions are directionally sound and honestly caveated. Four places where the language outruns the evidence — none invalidates the forward test's motivation, but two should be softened before anyone quotes them externally.

### B1. HIGH — "EXPIRED_WORTHLESS is robust" overclaims; the 46% number is a hold-to-expiry upper bound, not realized group P&L

§4.2 says a signal is WORTHLESS if "the underlying never traded above strike + premium and finished OTM," and calls this robust because "the buyer lost most or all of it regardless of path." That last clause is false: a 15-DTE near-ATM call can be sold for a substantial time-value gain on an early favorable move without intrinsic ever reaching strike+premium (high gamma, days of time value left). The group's *documented* practice — "safe traders book at ~100% option ROI" — is exactly this early time-value exit. So a trade classified EXPIRED_WORTHLESS could have been a realized +100% for a disciplined follower. The review even concedes this ("an early exit on time value isn't captured") and then asserts robustness two sentences later — the two statements conflict. *Consequence:* "46% rode to zero" is true only under hold-to-expiry; the honest phrasing is "46% would have expired worthless if held, an upper bound on the loss rate; realized follower outcomes depend on exit discipline the data can't see." The damning conclusion (≈0 EV before costs) likely survives — theta on 15-DTE ATM is brutal and doubling requires real moves — but the certainty should be dialed down, including in the GOLDEN_RULES candidate quote in §6.4.

### B2. MEDIUM — The random-entry control's 53.3% is pseudo-replicated; "slightly below random" is an overread

20 trials per signal on the same tickers with overlapping windows means the 6,869 "resolved" control trades are massively correlated (same underlying paths sampled repeatedly). Effective sample size is closer to the number of distinct ticker-regime windows — order hundreds, not thousands. 53.3% vs 50.0% is well within noise at that effective n. The correct claim — "no evidence of selection skill above random timing" — is what §3's conclusion mostly says; the phrase "in fact slightly below" implies a resolvable ordering that the data cannot support. Strike or soften it.

### B3. MEDIUM — Target-on-intraday-high vs stop-on-close asymmetry inflates the +5.2% expectancy

Wins are detected on an intraday *touch* (assumes someone sold the exact high print at target); losses require a day-close breach. Both the signals and the control were scored under the same rules, so the *comparison* stands — but the standalone "+5.2% expectancy per trade" assumes perfect touch execution and is optimistic in absolute terms. One caveat sentence in §3 fixes it.

### B4. LOW–MEDIUM — Gate-replay proxy strictness and parser exclusions

- "0 of 121 survive the full stack" leans mostly on fully-reconstructable gates (DTE blocks 87/121; squeeze and RVOL are exact OHLCV formulas per `options_edge_backtest_v2.py`) — the refusal conclusion does **not** hinge on the vol-compression proxy, which is the right structure. But the proxy *does* block 83/121 alone, and on news-driven names realized-vol compression diverges most from implied-vol gates; the §8 caveat covers this. No change needed; just don't ever quote "0/121" without the DTE-dominance context.
- Parser exclusions (73 stock, 36 option signals): malformed signals (missing SL/target) plausibly correlate with impulsive/lower-quality calls — exclusion could flatter the group slightly. Worth one sentence in §4.6; direction unknown, magnitude small.
- One quiet implication for Tier A: the forward-test rejects come from a **curated watchlist already selected for the edge appearing** — near-misses inside a curated list are far closer to survivors than the WhatsApp firehose was. The true effect size in this experiment is plausibly *smaller* than anything §8 hints at, which compounds the A3 power problem.

---

## TIER C — Gemini's journal subsystem (read-only; all fixes are hub-side workarounds or relay items)

### G1. CRITICAL — One illiquid contract can 500 the entire `/journal/monitor` — including for Gemini's REAL positions. The relay's "expected and harmless" claim is wrong

app.py:952–955: `greeks = quote.get("greeks", {})` then `float(greeks.get("delta", 0))`, and `current_price = float(quote.get("last", 0))`. Tradier returns `"greeks": null` and `"last": null` for contracts with no trades/ORATS coverage — *exactly the profile of hypothetical reject strikes*. `None.get(...)` → AttributeError; `float(None)` → TypeError. The `try` wraps the **whole loop**, so one bad quote aborts the entire endpoint with a 500: no marks for any position that day — **including Gemini's own live paper trades**, silently disabling its kill-switch/stop monitoring. The relay message tells Gemini "no action needed on your side when a FWD_TEST row alarms" — it does not disclose that a FWD_TEST row can take down the monitor for Gemini's real record. *Failure scenario:* week 3, a reject on a thin name has `last: null`; every `/journal/monitor` call 500s for the life of that position; Gemini's UI shows a monitor error (or nothing); a real position blows through its 30% stop unmonitored; both experiments' daily marks stall and nobody notices for days because the failure is total rather than per-row.
**Hub-side mitigation (mandatory):** (a) only log rejects on contracts verified to have a live Tradier/IBKR quote with non-null last and greeks at entry; (b) the hub's daily mark must NOT depend on `/journal/monitor` — pull quotes directly (Tradier quotes endpoint or IBKR MCP `get_option_data`) and treat monitor as advisory; (c) **amend the relay** to disclose this failure mode and suggest (Gemini's call) a per-row try/except in the monitor loop.

### G2. CRITICAL/HIGH — The monitor marks with `last`, not bid/ask mid — the protocol's own pre-registered marking rule cannot be satisfied by the chosen instrument

Protocol honesty rule: "Premium marks are bid/ask mid at the daily check." app.py:955 marks with `quote.get("last")`, and the monitor response contains no bid/ask at all. For liquid survivors last≈mid; for illiquid rejects, last can be days stale — **systematically staler marks in exactly one arm of the experiment** (asymmetric measurement error, correlated with group membership). *Failure scenario:* reject positions show flat stale `last` prices for days, then "jump" at resolution; reject volatility and drawdowns are understated all experiment long; the mean-return comparison is contaminated in an unknowable direction.
**Fix:** the hub's daily mark of record = mid from its own quote pull (see G1b); `/journal/monitor`'s `unrealized_pl` is Gemini-side telemetry, never analysis data. Write this into the protocol.

### G3. HIGH — `/journal/log` returns no row id; `/journal/close` silently succeeds on a nonexistent id

- `journal_log` (app.py:897–912) returns only `{"status": "success"}` — no id. The hub must discover ids by scanning `/journal/history` and matching ticker/timestamp. Ten weeks of that = a wrong-row close eventually.
- `close_trade` (database.py:144–172): if the id doesn't exist, `row` is None, nothing updates, **and the endpoint still returns success**. *Failure scenario:* hub closes id 47 (typo for 74); gets "success"; position 74 stays OPEN and keeps getting marked; the resolved-count is silently wrong until analysis time, and the "loss logged the day it resolves" rule is unknowingly violated.
**Fix (hub-side SOP):** after every POST, immediately GET `/journal/history`, capture the new row's id into `forward_test_log.csv`; after every close, GET the row by history and verify `status == CLOSED` and `final_pl` is non-null. Two curl calls; make them part of the daily script.

### G4. HIGH — `/journal/update` is a full-row overwrite that nulls omitted fields and wipes `final_pl`; never use it on FWD_TEST rows

`journal_update` passes `data.get(...)` for every column into `update_trade`, which UPDATEs all of them (database.py:103–123). Any field you omit becomes NULL — including `entry_price`. Worse: `final_pl` is recomputed only if `status=='CLOSED'` and both prices are present in the payload; otherwise it is written as **None** — so "just appending the close reason to setup_context" on a closed row **erases its P/L**. *Failure scenario:* week 6, someone annotates 12 resolved rows with resolution reasons via PUT /journal/update; all 12 `final_pl` values become NULL; the analysis export finds 12 resolved trades with no P/L and no way to know if 0.0-vs-NULL rows elsewhere are real. **Fix:** protocol rule: FWD_TEST rows are touched by exactly two verbs — POST /journal/log and PUT /journal/close. Resolution reason lives in the hub CSV only (per A6). Never PUT /journal/update on a FWD_TEST row.

### G5. HIGH — On launch morning, the contamination guard is not armed and the token is (per protocol) still dead

- `HANDOFF_gemini_relay_session21.md` status: **"DRAFTED, not yet sent."** Grep of the Gemini repo finds zero occurrences of `FWD_TEST` in `KNOWN_ISSUES.md`/`AGENTS.md`/anywhere. The protocol's own note: logging must not start before the relay is confirmed, or Gemini's 1W/5L record is polluted from row one. Also note: the exclusion is a *convention*, not code — Gemini's frontend `TradeLedger.tsx` fetches all of `/journal/history` with no setup_context filter, so FWD_TEST rows **will** appear interleaved in Gemini's UI ledger regardless; the guard only covers Gemini's session-computed tallies.
- Tradier token: protocol calls the refresh "the #1 pre-Monday blocker." If it's still dead, G1b's direct-quote fallback (IBKR MCP) is the only marking path — verify `get_option_data` actually returns quotes for the specific reject strikes before relying on it.
**Fix:** send the relay and receive confirmation, and verify one live option quote end-to-end, before the first `POST /journal/log`. Day one can be Tuesday; a contaminated store cannot be un-contaminated.

### G6. MEDIUM — `/journal/monitor` is a GET that writes state, and the frontend polls it

Every monitor call persists `high_water_mark`/`gamma_surge_active` (app.py:975) — including for FWD_TEST rows, and including when Gemini's React UI polls it (`TradeLedger.tsx:65`). Consequences: (a) the hub can never be a purely passive reader; (b) HWM sampling density depends on whether someone had the UI open — HWM is a non-deterministic, sampling-dependent value and must not be used as analysis data (use only your own daily mid-marks); (c) a mid-loop crash (G1) leaves partial state — some rows' HWM updated, others not, on a "read." Accept and document; no hub action beyond "never analyze HWM."

### G7. MEDIUM — `DB_PATH = "trades.db"` is cwd-relative

database.py:5. If the Flask app is ever started from a different working directory over the 10 weeks, a fresh empty `trades.db` appears there and the forward test "loses" its store (both writes and reads split across two files). *Failure scenario:* a reboot in week 5, app relaunched from home dir, hub logs 2 weeks of rows into a second db nobody knows exists. **Fix (hub-side):** the daily script starts with `GET /journal/history` and sanity-checks that yesterday's known row ids are present; any sudden emptiness = stop and investigate. (Relay a suggestion to make DB_PATH absolute — Gemini's call.)

### G8. MEDIUM — No idempotency, no schema for the tag, deletable from the UI

- Double-POST on a flaky curl = duplicate rows; no unique constraint exists. Hub fix: the G3 read-back-verify step catches duplicates same-day.
- Group membership rides on a fragile string prefix. A typo (`FWD_TEST:SURVIVER|`) silently drops the row from both the analysis *and* Gemini's exclusion. Hub fix: the daily script validates `setup_context` prefix against the exact two-string enum after every log.
- Gemini's UI has per-row delete with only a browser confirm (`TradeLedger.tsx:80`); a stray click deletes a FWD_TEST row permanently. Mitigation: the read-back ids in the CSV (G3) at least make the loss detectable.
- SQLite concurrency: single Flask writer + hub via API is fine; if Gemini's session ever runs direct scripts against trades.db while the server is up, expect occasional `database is locked` 500s — retry, don't re-log blind (see idempotency).

### G9. LOW — Timestamp semantics

`timestamp` is SQLite `CURRENT_TIMESTAMP` (UTC); `days_open` compares it to local `datetime.now()` (app.py:991–992) — skewed by the UTC offset, and the bare-except fallback sets `days_open=0` (stagnation flag never fires) on any format surprise. The hub's time-stop rule (DTE × 0.60) must be computed hub-side from the CSV `entry_date`, never from Gemini's `days_open`. Also: rows logged after ~8pm ET get tomorrow's UTC date — record `entry_date` in the CSV in ET at log time.

### G10. LOW — Stale hub bookkeeping

The Known Issues table still lists `app.py:590 entry_price or 1.0` — the live file no longer contains that pattern anywhere (the monitor path has the correct Phase 12 guard). Update the table; it's the live-read rule applied to ourselves.

---

## PRE-LAUNCH FIX LIST (ordered; 1–6 gate the first log entry)

1. **A1** — One paragraph in the protocol: identical Builder run for reject direction; one mechanical target/stop rule for BOTH groups; Builder-fail finalists logged, not dropped.
2. **A2** — Entry = bid/ask mid at log time, both groups. One sentence.
3. **A3 + A6** — Rewrite the success criterion (primary bootstrap-CI mean-return AND spread-cost; secondary Newcombe win-rate; no OR), define WIN = resolved return > 0, restate resolution as at-daily-check, state the ±25pp power limit and the A5 shortfall rule.
4. **G5** — Send the relay, get confirmation recorded in Gemini's repo, verify one live option quote (Tradier or IBKR MCP) end-to-end. Slipping launch to Tuesday is cheap; contamination is forever.
5. **G1/G2** — Protocol amendment: mark of record = hub's own mid-quote pull; `/journal/monitor` is advisory telemetry only; rejects only on contracts with verified live quotes. Amend the relay to disclose the null-greeks/null-last 500 risk to Gemini.
6. **G3/G4** — Daily-script SOP: read-back id capture after every log; status+final_pl verification after every close; never PUT /journal/update on FWD_TEST rows; resolution reason lives in the CSV.
7. **A7** — Deterministic reject-selection rule (closest-to-threshold).
8. **A4/A8/A9** — `converted_while_open` notes, missed-day rule, record OI/spread% both arms.
9. **B1/B2/B3** — Soften the three overclaims in WHATSAPP_SIGNALS_REVIEW.md before anything is quoted externally (especially the §6.4 GOLDEN_RULES candidate).
10. **G10** — Update the stale app.py:590 Known Issues entry.

## VERDICT: **LAUNCH WITH FIXES**

The design's skeleton is sound — same-day same-universe control, pre-registration, stand-down as data, contamination tagging — and most of what's wrong is *unwritten rules* rather than wrong rules. But items 1–6 are cheap to fix today and unrecoverable after row one: an ambiguous reject-scoring procedure, a fantasy-fill door, an OR-clause escape hatch, an unarmed contamination guard, and a marking instrument that both violates the protocol's own honesty rule and can be crashed by the experiment's own control arm. Fix on paper this morning; log the first row when the relay confirmation exists. If that costs one day, the experiment loses nothing — its own arithmetic says survivors arrive slowly anyway.
