# OPTIONS_SIEVE_SPEC.md — Canonical Sieve/Gate Spec (anti-drift)

**Status:** Built Session 19/20 (pending since Session 13 — this closes that gap). **This file is the single source of truth for sieve/gate logic.** `skill-options-ibkr-radar.md` (PATH A) and `skill-options-scanner.md` (PATH B) must both defer to this spec rather than re-describing the rules independently — that's exactly how they drifted from each other in the first place.

**Why this exists:** Radar and Scanner both claim to run "the same 4-Sieve Engine," but a live audit found real divergence: Gate C was computed two different ways, and finalist IV/HV qualification differed between the two paths. Same disease as the CENTAUR contract drift on the Gemini side — logic described in prose in two places instead of enforced from one.

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

**Gate B — IV Anomaly.** `IV > 150% → ELIMINATE`, plus a scanner-config alert (the underlying IV cap is supposed to exclude these before they're ever seen). Identical on both paths.

**Gate C — Liquidity / Dollar Volume Floor.** Target definition: **average daily dollar volume ≥ $100M** — this is the actual thing being gated on both paths; only the computation method differs:
- **PATH A (Radar):** `estimated_daily_$ = Last × Average_Volume_Shares` (screen-computed, both inputs visible on the IBKR scanner).
- **PATH B (Scanner):** `avg_90d_usd_volume` pulled directly from MCP. **⚠️ Known unresolved issue — do not treat as authoritative yet:** `ibkr-mcp-capabilities.md` flags that this field's returned value for NVDA is consistent with a 90-day *total*, not a 90-day *daily average* — if so, the $100M threshold is off by roughly 90x and this gate may be a silent no-op on PATH B. This needs a live MCP data pull across a few names to settle the units before PATH B's Gate C can be trusted. Until resolved, PATH A's Gate C (screen-computed) is the more trustworthy of the two.

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

---

## Sync discipline

Both `skill-options-ibkr-radar.md` and `skill-options-scanner.md` carry a one-line header pointing here. **If you change a sieve/gate rule in either skill, update this file in the same edit — not after, not "later."** This file existing doesn't prevent drift by itself; treating it as optional reading is exactly how the previous divergence happened even with two skills that both claim to implement "the same engine."

---

## Fix log (this file's own changes)

- **Session 19/20 (creation):** Resolved the Gate C computation divergence (documented both methods, flagged PATH B's units as unverified rather than picking one arbitrarily). Resolved the finalist IV/HV<100% divergence by making Radar match Scanner's explicit requirement (Radar previously had no explicit threshold on its finalists, only "lowest IV/HV ratios that passed Sieve 1"). Confirmed the Cheap IVR Trap and earnings gate were already consistent between both paths post the earlier Session 19 earnings-gate fix.
