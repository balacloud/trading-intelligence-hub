# Forward Test Protocol — Survivors vs. Rejects (v2, post-review)

> Designed Session 21 · **Revised same session after `FABLE_PRELAUNCH_REVIEW.md` (verdict: LAUNCH WITH FIXES — all six gating findings addressed below)**
> First entries: **Tuesday July 7, 2026 at the earliest** — gated on (a) Gemini confirming the `FWD_TEST:` exclusion rule (relay `HANDOFF_gemini_relay_session21.md`) and (b) a working quote source for marks. Monday July 6 = relay + green-path validation + dry-run of this procedure with no logging.
> Motivation: the WhatsApp gate-replay experiment (`research/WHATSAPP_SIGNALS_REVIEW.md` §8) proved the sieve stack **refuses** bad flow but produced no evidence it **discriminates**. This test generates that evidence live.

## The question this answers

*Do names that pass the full gate stack outperform names that narrowly fail it?*

Not "does the pipeline make money" — but "do the gates rank-order outcomes," which is the claim the WhatsApp replay could not test.

## Symmetry rules (review findings A1/A2 — the experiment is void without these)

Both groups get **identical, mechanical trade structure**. Gate status is the ONLY thing that differs between arms:

- **Contract:** nearest-ATM call (or put if the Directional Builder direction is bearish), nearest monthly expiry inside 21–35 DTE. Same rule, both groups.
- **Direction:** Directional Builder is run for BOTH survivors and rejects (rejects still get a Builder read — failing a sieve gate doesn't block the Builder from producing a direction). If the Builder outputs MIXED/no-direction for either group's name, that name is not logged (recorded in the hub CSV as `BUILDER_MIXED`, both groups alike — prevents silent survivorship inside the survivor arm).
- **Entry price:** bid/ask **mid at log time**, both groups, from a live quote the hub pulls itself. No Gemini-recommended pullback limits, no hypothetical fills — that's the fantasy-fill bug the WhatsApp review itself catalogued (§4.1).
- **Target / stop (mechanical, both groups):** stop = entry mid × 0.70 (the system's standard 30% hard stop); target = entry mid × 1.60 (R:R 2.0 on premium, clears the ≥1.5 floor being trialed). Gemini's synthesized levels, if any, are recorded as metadata only and never drive resolution.
- **Quote-or-skip:** a position (either group) is only logged if the contract has a verified live quote (bid > 0 and ask > 0) at log time. A reject too illiquid to quote is recorded in the hub CSV as `NO_QUOTE`, not logged to the journal — see G1 below.

## Daily procedure (market hours, ~10 min, Claude Code with IBKR MCP)

1. Run PATH B Scanner on the CORE watchlist (EXTENDED if < 3 finalists).
2. **Log every finalist** (gate survivors) — **0 is a valid and expected count; never force a fill**. Stand-down days are recorded in the hub CSV (`group=STANDDOWN, ticker=NONE`).
3. **Log up to 3 near-miss rejects** — names that failed exactly one gate. Record which gate and the failing value.
4. Apply the symmetry rules above to construct both groups' positions; log to Gemini's journal (see below).
5. Daily thereafter: **the hub marks positions itself** — Tradier directly (`/markets/quotes` + `/markets/options/chains`, confirmed live Session 26) is now the primary path; IBKR MCP `get_option_data` is the fallback if Tradier is ever down — at bid/ask mid. Resolution is evaluated **on the daily mark, close-of-day basis** (consistent with the day-close stop discipline): mark ≤ stop → STOP; mark ≥ target → TARGET; held ≥ DTE × 0.60 → TIME; expiry → settle at intrinsic. **A "win" = resolved return > 0 after round-trip half-spread.** (Review A6: touch-based resolution is unimplementable with once-daily checks — resolution is mark-based, both groups, stated here so nobody "improves" it mid-test.)

## Dedupe & migration (review A4)

- A ticker with an unresolved position is not re-entered **within the same group**.
- **Cross-group migration is allowed and logged:** if a rejected name later passes all gates (or a survivor's name later shows up as a reject), the new position IS taken in the other group, tagged `migrated` in the hub CSV. First-classification-wins would censor exactly the converts that carry the most gate information — biasing the test toward null.
- Idempotency: max one new position per ticker per group per day; before logging, check `/journal/history` for an existing open FWD_TEST row on that ticker+group.

## Where positions live: Gemini's paper-trade journal — with API traps mapped (review G1–G8)

Positions are logged via `POST localhost:5002/journal/log` with `setup_context` prefixed `FWD_TEST:SURVIVOR|` or `FWD_TEST:REJECT|` (exact string, no variants — group membership rides this prefix) followed by the gate blob: `failed_gate, ivr, iv_hv_pct, squeeze, rvol, trend_200d, rr_ratio, migrated`.

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
