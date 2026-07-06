# Forward Test Protocol — Survivors vs. Rejects

> Started: (first entry expected Monday, July 6, 2026) · Designed Session 21
> Motivation: the WhatsApp gate-replay experiment (`research/WHATSAPP_SIGNALS_REVIEW.md` §8) proved the sieve stack **refuses** bad flow but produced no evidence it **discriminates** — survivors vs. baseline was n=8. This test generates that evidence live.

## The question this answers

*Do names that pass the full gate stack outperform names that narrowly fail it?*

Not "does the pipeline make money" (that needs the 30-sample run and real fills) — but "do the gates rank-order outcomes," which is the claim the WhatsApp replay could not test.

## Daily procedure (market hours, ~10 min, Claude Code with IBKR MCP)

1. Run PATH B Scanner on the CORE watchlist (EXTENDED if < 3 finalists).
2. **Log every finalist** (gate survivors) — up to 3/day, but **0 is a valid and expected count; never force a fill**. Stand-down days are recorded as a row with `ticker=NONE`.
3. **Log up to 3 near-miss rejects** — names that failed exactly one gate. Record which gate and the failing value. These are the control group.
4. For each survivor that also clears Directional Builder: record the system's own entry / target / stop / expiry (21–35 DTE contract per spec). For rejects, record the same hypothetical structure (nearest 21–35 DTE, ATM-zone strike) so both groups are scored identically.
5. Daily thereafter: update MTM; resolve on **target touch**, **day-close stop**, **time stop (DTE × 0.60 held)**, or **expiry** — whichever first. Same rules for both groups.

## Dedupe rule

A ticker already open in the log (either group) is not re-entered while its position is unresolved. Persistence of a setup across days is one trade, not five.

## Where positions live: Gemini's paper-trade journal (decided after live-read of `app.py`/`database.py`)

Positions (both groups) are logged into `options_iq_gemini`'s SQLite journal via its API (`POST localhost:5002/journal/log`), NOT a hand-maintained CSV:

- **Daily tracking is already built:** `GET /journal/monitor` marks every OPEN position live (premium, delta kill-switch < 0.25, gamma-surge trailing stop, stop-loss breach, stagnation ≥ 5 days). Resolutions via `PUT /journal/close/<id>`.
- **Tagging (mandatory, prevents contaminating Gemini's own record):** `setup_context` must start with `FWD_TEST:SURVIVOR|` or `FWD_TEST:REJECT|` followed by the gate blob: `failed_gate, ivr, iv_hv_pct, squeeze, rvol, trend_200d, rr_ratio`. Tagged rows are excluded from Gemini's performance tallies — relay this rule to Gemini's session before the first log (pending, see Next Steps).
- **Dependency:** `/journal/monitor` marks via Tradier — **dead token = no auto-marks.** Until refreshed, mark manually via IBKR MCP `get_option_data`. Token refresh is the #1 pre-Monday blocker.
- `rr_ratio` is logged because the R:R ≥ 1.5 floor (WhatsApp review §6.3) is being trialed here before formalizing in the Directional Builder skill.

## What stays hub-side (`forward_test_log.csv`)

Only what the journal can't hold: **stand-down days** (`group=STANDDOWN, ticker=NONE`) and, at analysis time, a full export of tagged journal rows merged with stand-down records — the CSV is an analysis artifact, not the primary store.

## Sample-size and timeline expectations (set now, so nobody moves the goalposts later)

- 3 weeks ≈ 15 trading days ≈ 10–20 **unique** setups after dedupe (not 45 — setups persist across days), plus the stand-down record.
- First resolutions: ~2 weeks in (time stops). Expiry wave: weeks 4–5.
- **30+ resolved positions per group ≈ mid-September 2026.** No conclusions before then beyond anecdote; interim looks are allowed but labeled interim.
- Success criterion (pre-registered): survivors' win rate exceeds rejects' win rate with the difference's 95% Wilson CI excluding zero, OR survivors' mean return exceeds rejects' by more than the spread cost. Anything less = "gates refuse, but do not discriminate" and we say so.

## Rules of honesty (from the WhatsApp review's failure catalog)

- Losses are logged the day they resolve, same rigor as wins. No editing resolved rows.
- Premium marks are bid/ask mid at the daily check; if the chain is a desert (OI < 500), that IS the data point — log it, don't substitute the underlying.
- If the Scanner produces zero finalists for a week straight, that is a result about market regime, not a malfunction to be tuned away mid-test.
