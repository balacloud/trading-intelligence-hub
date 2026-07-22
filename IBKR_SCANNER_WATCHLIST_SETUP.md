# IBKR Watchlist Setup — Options IQ Scanner (v3.0, BUYING-tuned)
> **Watchlist names:** `HUB_CORE` (20 tickers, default run), `HUB_EXTENDED` (deep-scan bench)
> **Also maintained live in IBKR** via the IBKR MCP `create_watchlist`/`edit_watchlist` tools — membership auto-syncs from `skill-options-scanner.md`'s CORE/EXTENDED tables. This doc covers the **column setup**, which is a one-time manual step in TWS/IBKR mobile (columns aren't API-settable).
> **Companion doc, not a template:** `options-iq/docs/stable/IBKR_WATCHLIST_SETUP.md` documents a premium-**SELLING** watchlist with inverted thresholds. Reuse the column *plumbing* from that doc; **never** its decision matrix. See the trap note below.

---

## ⚠️ The trap — buying vs selling inversion

This scanner is a premium-**BUYING** system: buy when IV is cheap relative to its own history and to realized vol (`IVR ≤ 45`, `IV/HV < 100%`). OptionsIQ's watchlist (the other project on this machine) is a premium-**SELLING** system: sell when IV is rich (`IV/HV ≥ 110%`, `IVR ≥ 35`). **The thresholds are inverted, not just differently calibrated.** A row OptionsIQ would reject — say IV/HV 94% — is exactly the row this scanner wants. If you ever find yourself pattern-matching against OptionsIQ's decision matrix while reading a Scanner paste, stop; you're importing the wrong system's rules.

---

## Column Configuration

**How to add:** IBKR Watchlist → edit icon (pencil, top right) → Manage Columns

### Exact column names as they appear in IBKR UI

| # | IBKR Display Name | Manage Columns Category | Scanner field |
|---|-------------------|------------------------|---------------|
| 1 | UNDERLYING PRICE | Options | `price_last` |
| 2 | 52 WEEK IV RANK | Options | `ivr_52w` — Sieve 1 gate (≤ 45) |
| 3 | IMPLIED VOL./HIST. VOL % | Options | `iv_hv_ratio` — Sieve 2b edge ranking (< 100%) |
| 4 | OPT. IMPLIED VOLATILITY % | Options | `iv_annual` — Gate B (> 150% → eliminate) |
| 5 | HIST VOL CLOSE % | Options | `hv_30d` — card display only |
| 6 | OPTION OPEN INTEREST | Options | `oi` — OI gate (≥ 500) |
| 7 | OPT VOLUME | Options | `opt_volume` — liquidity context (optional) |
| 8 | PRICE/EMA(200) | Technical Indicator | `trend` — replaces the 200d web search |
| 9 | 52 WEEK HIGH (price) | Technical Indicator / Price | `high_52w` — RANGE |
| 10 | 52 WEEK LOW (price) | Technical Indicator / Price | `low_52w` — RANGE |
| 11 | PUT/CALL VOLUME | Options | `put_call_vol` — context flag, sentiment (not a gate) |
| 12 | OPT. VOLUME CHANGE % | Options | `opt_vol_change_pct` — context flag, unusual activity (not a gate) |
| 13 | PRICE/EMA(50) | Technical Indicator | `price_ema50` — context flag, pullback detector (not a gate) |
| 14 | OPT. IMP. VOL. CHANGE | Options | `iv_change` — display only, no rule yet |

**Do NOT confuse `52 WEEK HIGH/LOW` (price) with `52 WEEK IV HIGH/LOW` (implied vol) — IBKR exposes both, and only the price pair belongs in this watchlist.**

**Columns 11–14 added (Session 31):** pulled from `options-iq`'s watchlist doc (the selling system) — same column *plumbing*, but their thresholds are built for a premium-selling decision and do not transfer here without their own first-principles read. See "How to Read" below for each.

**Do NOT add** `52 IV PERC.` from the OptionsIQ template — that column belongs to the selling system's IV-percentile cross-check (Decision Matrix, OptionsIQ doc) and has no role here; the Scanner's IVR gate uses `52 WEEK IV RANK` alone, per `OPTIONS_SIEVE_SPEC.md`.

**Add a VIX row** — a separate watchlist row for the `VIX` index (not a stock), used only for its `LAST` value to set the regime (STANDARD ≤ 25, HIGH-FEAR > 25). No options columns apply to it.

---

## How to Read Each Column (BUYING thresholds — inverted from OptionsIQ)

### 52 WEEK IV RANK
- Shows as raw number (e.g., `34`, not `34%`)
- **≤ 45:** Passes Sieve 1. IV is at or below the median of its own 52-week history — not paying the Volatility Tax.
- **> 45:** Purge. IV above median = structurally negative EV for a debit buyer before the stock even moves.
- **This is the real IBKR Rank**, not MCP's `implied_volatility_percentile` proxy — trust it over any MCP re-check (see Phase 3.5's caveat in `skill-options-scanner.md`).

### IMPLIED VOL./HIST. VOL %
- Shows as percentage (e.g., `87.3%` = IV is 0.873× HV)
- **< 70%:** Deep edge — market severely underpricing realized vol.
- **70–100%:** Buyer edge — qualifies as a finalist.
- **100–115%:** Neutral — does NOT qualify as a finalist.
- **> 115%:** Expensive — does NOT qualify as a finalist, avoid buying naked premium.
- **Opposite of OptionsIQ's read:** on that watchlist, ≥ 110% is the *tradable* signal. Here, < 100% is what you want.

### OPT. IMPLIED VOLATILITY %
- Shows as percentage (e.g., `38.2%`)
- **> 150%:** Gate B eliminate — distressed/event-driven anomaly, options pricing a binary event, do not buy premium.
- Otherwise: sizing/display context only, not a pass/fail gate on its own.

### OPTION OPEN INTEREST
- Raw contract count (e.g., `1,240`)
- **< 500:** Eliminate. Chain isn't liquid enough to enter or exit cleanly on a 21–35 DTE hold.
- **≥ 500:** Passes. Higher is better but not scored — this is a hard floor, not a ranking input (per `PERSONA.md`'s liquidity-is-a-gate-not-a-score rule).

### PRICE/EMA(200)
- Shows as `+11.78%` (above) or `-0.51%` (below)
- **> 0:** UPTREND — directional lean context for the Directional Builder handoff.
- **< 0:** DOWNTREND.
- **Within ±2%:** flat — NEUTRAL lean, no direction passed to the handoff.
- Context only, never a hard gate here — Directional Builder's own signal stack has the final word on direction.

### 52 WEEK HIGH / LOW (price)
- Used with `UNDERLYING PRICE` to compute range position: `(price − low) / (high − low) × 100`.
- **< 25%:** lower third — near 52wk lows.
- **25–75%:** mid range.
- **> 75%:** upper third — near 52wk highs.
- Contextual framing only, feeds the directional LEAN alongside Price/EMA(200); never eliminates a finalist on its own.

### PUT/CALL VOLUME (new, Session 31)
- Shows as a ratio (e.g., `0.61`, `1.20`)
- Sentiment/flow — the one dimension in this pipeline genuinely orthogonal to trend (SMA200/EMA stack/YTD/52wk range all measure the same underlying "is it trending" question in different clothes; this measures options positioning instead).
- **No hard threshold here.** `options-iq`'s ≥1.5 (fear) / ≤0.5 (complacency) thresholds are calibrated for its selling-system regime read — not validated for this buying context. Display on the finalist card as context only; never a gate.

### OPT. VOLUME CHANGE % (new, Session 31)
- Shows as a percentage (e.g., `96.5%`, `210.3%`)
- **> 200%:** unusual options-activity spike — investigate before trading. Same read as `options-iq`'s system; event risk is direction-agnostic, so this transfers without recalibration.
- Flag on the card when it fires. Never a purge — it's a "look closer" signal, not a disqualifier.

### PRICE/EMA(50) (new, Session 31)
- Shows as `+11.78%` (above) or `-0.51%` (below), same shape as Price/EMA(200)
- Intermediate trend / pullback detector. Read alongside Price/EMA(200): **positive 200 + negative 50 = pullback inside an uptrend** — the exact tension Session 30 had to catch by hand on AFRM (bullish EMA stack, negative/contracting MACD histogram). This column surfaces it at scan time instead of only downstream in Directional Builder.
- Context only, never a hard gate — same status as Price/EMA(200) here.

### OPT. IMP. VOL. CHANGE (new, Session 31 — observe-only, no rule yet)
- Shows as a decimal (e.g., `-0.580`, `+0.246`)
- IV direction: is implied vol rising or falling right now. `options-iq` reads `≤0 = compressing = sell window` — that logic doesn't invert cleanly for a buyer. A buyer arguably wants cheap IV that's *about to* expand, not IV that's already compressing further — but that's a hypothesis, not a backtested rule. Per Alex's one-sentence-edge test, this doesn't pass yet.
- **Display the raw number on the card. Do not gate or flag on it.** Revisit once we've seen enough live readings to state the buying-context edge in one sentence.

---

## Sieve Summary (canonical logic — see `OPTIONS_SIEVE_SPEC.md`, this table is a quick reference only)

| Gate | Rule | Source column |
|---|---|---|
| Sieve 1 — IVR Purge | `IVR > 45 → PURGE` | 52 WEEK IV RANK |
| Gate A — Market cap | Pre-satisfied by curation | — (no column needed) |
| Gate B — IV Anomaly | `IV > 150% → ELIMINATE` | OPT. IMPLIED VOLATILITY % |
| Gate C — Liquidity | Pre-satisfied by curation | — (no column needed) |
| OI Gate | `OI < 500 → ELIMINATE` | OPTION OPEN INTEREST |
| Sieve 2b — Edge Ranking | Rank ascending by IV/HV, top 3 all < 100% | IMPLIED VOL./HIST. VOL % |
| Cheap IVR Trap | `IVR < 20% AND IV/HV > 120%` → flag, never a finalist | both above |

---

## Illustrative Example (not a live reading — canonical trap case)

| Ticker | IVR | IV/HV | OI | P/EMA200 | Verdict |
|--------|-----|-------|-----|----------|---------|
| WBD | 10 | 165% | 2,400 | +3.1% | **TRAP** — IVR passes Sieve 1 (≤45) but IV/HV 165% fails Sieve 2b AND trips the Cheap IVR Trap (IVR<20, IV/HV>120). Never a finalist despite the low IVR. |
| (hypothetical) | 34 | 87% | 1,100 | +8.4% | **FINALIST candidate** — IVR ≤45 passes, IV/HV 87% is BUYER EDGE, OI clears the floor, uptrend context. |

This table is illustrative only — every real scan pulls live numbers from the pasted watchlist, never from this doc.
