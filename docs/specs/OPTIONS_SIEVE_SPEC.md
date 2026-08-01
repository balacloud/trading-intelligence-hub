# OPTIONS_SIEVE_SPEC.md — Canonical Sieve/Gate Spec (anti-drift)

**Status:** Built Session 19/20 (pending since Session 13 — this closes that gap). **This file is the single source of truth for sieve/gate logic.** `skill-options-ibkr-radar.md` (PATH A) and `skill-options-scanner.md` (PATH B) must both defer to this spec rather than re-describing the rules independently — that's exactly how they drifted from each other in the first place.

**Why this exists:** Radar and Scanner both claim to run "the same 4-Sieve Engine," but a live audit found real divergence: Gate C was computed two different ways, and finalist IV/HV qualification differed between the two paths. Same disease as the CENTAUR contract drift on the Gemini side — logic described in prose in two places instead of enforced from one.

**Numbers are now also code (Session 30, `research/forward_test/sieves.py`):** the constants below are illustrative — `sieves.py`'s module-level constants are the authoritative source of truth. On any threshold change, edit the constant in `sieves.py` **and** the machine-readable block immediately below in the same commit; `research/forward_test/test_spec_sync.py` fails the build if the two ever diverge. This extends this file's own sync discipline (previously covering `skill-options-ibkr-radar.md` and `skill-options-scanner.md`) to a third artifact — see PLAN_deterministic_pipeline_formalization.md Section 3.

```yaml
# SPEC_SYNC_BLOCK — parsed by test_spec_sync.py, must equal sieves.py's constants exactly.
IVR_MAX: 45.0
IV_ANOMALY_MAX: 150.0
DOLLAR_VOL_FLOOR: 100000000
MARKET_CAP_FLOOR: 1000000000
IVHV_FINALIST_MAX: 100.0
TRAP_IVR_MAX: 20.0
TRAP_IVHV_MIN: 120.0
FINALIST_COUNT: 3
```

---

## The Four Sieves — canonical definitions

### Sieve 1 — IVR Purge (Volatility Tax)

**Rule:** `IVR > 45 → PURGE`. Survivors: `IVR ≤ 45`.

**Why:** IV above the median of the stock's own 52-week history is structurally negative EV for a debit buyer before the stock even moves.

**⚠️ Data source differs by path — this is not drift, it's structural:**
- **PATH A (Radar):** IVR comes from the pasted/screenshotted IBKR watchlist column ("52 Wk IV Rank") — the authoritative source.
- **PATH B (Scanner):** No paste exists, so IVR is approximated from MCP's `implied_volatility_percentile` — a *different metric* (percentile, not rank) that has been confirmed to diverge from the real watchlist number (AFRM: Rank 34 vs percentile 18.3). Treat a PATH B pass near the 45 threshold as provisional, not confirmed. See `reference_ivr_vs_percentile` memory for the full history of this issue.

### Sieve 1.5 — Compensation Gates (run on all Sieve 1 survivors, before edge ranking)

**Gate A — Market Cap Floor.** `Market cap < $1B → PURGE`. PATH A checks this from the screen if the column is visible. PATH B has it **pre-satisfied by watchlist curation** (all CORE/EXTENDED names are asserted >$1B) — this is an assertion, not a per-run check; see Known Issues below for the unverified names.

**⚠️ PATH A structural limitation, confirmed Jul 31, 2026 (live screenshots of `Spec_Compliant_Screener`'s actual filter panel):** the screener's Market Cap filter cannot be configured as a floor-only field — it only accepts a range, currently set 1.00–10.00 ($B). This is the maximum IBKR's platform allows, not a config choice; there is no way to request "≥ $1B" without an implicit ceiling. **Consequence: every PATH A scan silently excludes every $10B+ market-cap name before Gate A/Sieve 1 ever sees it.** Gate A's own logic (`market_cap_usd < $1B → PURGE`) only checks a floor and has no way to detect or compensate for names the screener already dropped upstream — this is a genuine, permanent blind spot in PATH A's candidate universe, not a bug in `sieves.py`. PATH B (watchlist paste) has no such ceiling and is unaffected.

**Gate B — IV Anomaly.** `IV > 150% → ELIMINATE`, plus a scanner-config alert (the underlying IV cap is supposed to exclude these before they're ever seen). Identical on both paths.

**Gate C — Liquidity / Dollar Volume Floor.** Target definition: **average daily dollar volume ≥ $100M** — this is the actual thing being gated on both paths; only the computation method differs:
- **PATH A (Radar):** `estimated_daily_$ = Last × Average_Volume_Shares` (screen-computed, both inputs visible on the IBKR scanner) — a real per-run check, always evaluated.
- **PATH B (Scanner):** **pre-satisfied by watchlist curation, same as Gate A** — corrected Session 36 (Jul 27, 2026). This spec previously said Gate C is "pulled directly from MCP" on PATH B as a real per-run check, distinct from Gate A's curation-assertion — that text was never reconciled against `skill-options-scanner.md`'s own v3.0 conversion (Session 30), which explicitly made Gate C curation-pre-satisfied ("no column required") as part of its "0 MCP calls for screening" design goal. `sieves.py` (built the same session as v3.0) had also encoded the old stricter reading and, as written, made every real PATH B row `UNSCREENABLE` — found by actually running the deterministic module against a real PATH B paste for the first time, not by re-reading either doc. `paste_parser.py` always sets PATH B's `dollar_vol_usd` to `None` (no dollar-volume column exists in that paste format) — `sieves.py` now treats that `None` as curation-asserted, mirroring Gate A. An optional live MCP finalist-verify (Phase 3.5, ≤3 calls) remains available as a staleness backstop but is not required for a name to clear Gate C. The $100M/day threshold itself is unchanged and still correctly scaled where it IS evaluated (PATH A) — confirmed twice with live data, Jul 13 and Jul 18, 2026 (NVDA $31.7B/day, HIVE $78.5M/day and $83.2M/day on two independent pulls).

If Gate A, B, or C fires on every remaining ticker (PATH A) or scanner quality looks off (PATH B): stand down, don't force survivors. Never route around a gate to get to 3 finalists.

### Sieve 2b — Edge Ranking + Finalist Qualification

**Rule:** Rank all Sieve 1 + Gate A/B/C survivors ascending by `IV/HV` ratio (`iv_annual ÷ hv_30d`). Select the top 3.

**Canonical finalist qualification (resolves a real divergence found in Session 19/20 audit):** **All 3 finalists must have IV/HV < 100%.** If fewer than 3 names clear that bar, output only the ones that do — never pad with a neutral (100-115%) or seller-edge (>115%) name just to hit a count of 3. **Stand down is a valid output.**

(Prior to this spec, Scanner stated this requirement explicitly; Radar did not — Radar's skill has been updated to match. See the fix log at the bottom of this file.)

| IV/HV % | Signal |
|---|---|
| < 70% | Deep edge |
| 70–100% | Edge exists — qualifies as a finalist |
| 100–115% | Neutral — does NOT qualify as a finalist |
| > 115% | Expensive — does NOT qualify as a finalist |

### Sieve 3 — Fractal Squeeze
Deferred entirely to Options IQ Gemini Stage 2 (Centaur Mode). Neither Radar nor Scanner computes this — it is not a Stage 1 gate.

### Sieve 4 — Institutional Volume (RVOL)
Pre-checked at Stage 1 as an unconfirmed/informational flag only (screenshot-derived on PATH A, MCP-derived on PATH B) — **never a hard gate at Stage 1 on either path.** The definitive RVOL ≥ 1.5 check belongs to Centaur Mode at execution time, per the Horizon Principle (daily RVOL is an execution-timing signal, not a selection signal — see `skill-options-scanner.md`'s Horizon Principle section for the full rationale).

---

## Earnings Gate (TBLA rule) — canonical, both paths (fixed Session 19)

Classify against the **full hold period** (0–35 days from today), not just the 21–35 DTE selection window — a position opened today at 21–35 DTE is exposed to earnings risk from day 0.

| Days to earnings | Label | Action |
|---|---|---|
| None within 35 days | CLEAR ✅ | Proceed |
| 14–35 days away | ⚠ WITHIN HOLD | Flag. Gemini Stage 2 decides against the actual chosen expiry — this is a flag, not a hard block, on either path. |
| < 14 days away | 🔴 TBLA RULE | Hard skip at Stage 1. Catalyst risk imminent. |

## The Cheap IVR Trap — canonical, both paths (already consistent, no drift found)

Run on **all Sieve 1 survivors**, not just finalists (a trap name that never becomes a finalist can still mislead if the user goes looking for a low-IVR name elsewhere). Flag: `IVR < 20% AND IV/HV > 120%` → "LOW IVR / HIGH IV-HV DIVERGENCE — IV cheap in history but expensive vs. realized vol. The edge is negative." Canonical example: WBD, IVR 10 / IV/HV 165%.

---

## Known implementation gaps (tracked, not silently ignored)

1. **PATH B Gate C units are unverified** — see Sieve 1.5 above. Needs a live MCP pull to settle before it can be trusted.
2. **PATH B IVR is a percentile proxy, not a real rank** — see Sieve 1 above. Structural limitation of having no paste, not a bug to "fix" so much as a confidence caveat to keep attached to every PATH B output.
3. **PATH B's "Gate A pre-satisfied by curation" is an assertion, never checked per-run** — at least two watchlist names (HIVE, POET) plausibly sit under the stated $1B floor. Worth a one-time audit of the whole CORE/EXTENDED list rather than trusting the assertion indefinitely.
4. **PATH A's Market Cap filter has a hard $10B ceiling, confirmed a platform limitation, not fixable** — see Gate A above. Silently excludes every $10B+ name from PATH A's candidate universe; `sieves.py` has no way to detect names dropped upstream of Gate A.
5. **PATH A's Average Volume ($) filter cannot hold a ceiling above ~$500M — proven via a controlled diagnostic (Jul 31, 2026, Session 40), not just a settings-panel read.** A clean-context isolated test confirmed no committed ceiling value survives between $500M and the intended $53.38B; a ticker pull-through at the last-working $316.23M ceiling confirmed it's a real enforced filter, not a display echo (AAPL/NVDA/MSFT/GOOGL/AMZN/META/TSLA — all $8B–$30B/day — genuinely absent from results at that ceiling). Left configured, this filter would silently exclude every liquid megacap from PATH A — worse than having no filter. **Decision: left unconfigured on the live screener.** Gate C's independent per-run computation (`Last × Average_Volume_Shares`, $100M floor, no ceiling) remains, as it always has, the sole real liquidity screen on PATH A — this was already true (see the Gate C row in `CLAUDE_CONTEXT.md`'s Known Issues), now with a fully proven mechanism instead of an assumed one.
6. **PATH A's Average Option Volume (>10K) and Put/Call Volume Ratio (0.00–1.68) filters were both successfully restored Jul 31, 2026 (Session 40)** and are live on `Spec_Compliant_Screener` — closes the Put/Call gap that previously had zero downstream compensation anywhere in the deterministic pipeline. Put/Call's backend enforcement (vs. just correct display) was not independently ticker-tested the way Average Volume ($) was above — treated as very likely real, not yet proven to the same standard.
7. **PATH A's Current Option Volume filter has the same unfixable ceiling bug as Average Volume ($) — confirmed and removed, same day.** No floor-only operator exists for this field; the ceiling snapped to the floor value (zero-width range, 0 results) on any wide-value attempt. Proven load-bearing, not cosmetic: a live scan with the accidental 1.00K–2.05K range returned 3 results; removing the filter and re-running the identical scan the same session returned 12. Left unconfigured going forward — nothing downstream independently compensates for this specific filter, but its own documented intent ("effectively no ceiling") means its absence just restores the originally-intended behavior rather than opening a new gap.

---

## Sync discipline

Both `skill-options-ibkr-radar.md` and `skill-options-scanner.md` carry a one-line header pointing here. **If you change a sieve/gate rule in either skill, update this file in the same edit — not after, not "later."** This file existing doesn't prevent drift by itself; treating it as optional reading is exactly how the previous divergence happened even with two skills that both claim to implement "the same engine."

---

## Fix log (this file's own changes)

- **Session 19/20 (creation):** Resolved the Gate C computation divergence (documented both methods, flagged PATH B's units as unverified rather than picking one arbitrarily). Resolved the finalist IV/HV<100% divergence by making Radar match Scanner's explicit requirement (Radar previously had no explicit threshold on its finalists, only "lowest IV/HV ratios that passed Sieve 1"). Confirmed the Cheap IVR Trap and earnings gate were already consistent between both paths post the earlier Session 19 earnings-gate fix.
