# IBKR MCP Capabilities Reference
> Documented: June 20, 2026 — dry run against NVDA (NASDAQ, contract_id: 4815747)
> Purpose: (1) Baseline for tracking MCP upgrades over time. (2) Input spec for Options IQ Gemini skill architecture.
> Update this file whenever a new MCP field is discovered or an existing field changes behavior.

---

## MCP Tools Used

| Tool | Purpose |
|------|---------|
| `search_contracts(query, security_type)` | Resolve ticker → contract_id. Works for STK. Does NOT return individual OPT contracts (strikes/expiries). |
| `get_price_snapshot(contract_id, exchange, market_data_names[])` | Pull live/close market data fields. Multiple fields in one call. |
| `get_price_history(contract_id, exchange, security_type, step, period, outside_rth)` | Pull OHLCV bars. `ONE_YEAR` + `ONE_DAY` step = ~251 daily bars. |
| `get_account_positions()` | All open positions — size, cost basis, market price, P&L, currency. |

---

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Field returns valid, useful data |
| ⚠️ | Field returns data but requires calibration or is stale |
| ❌ | Field returns 0 / empty / invalid |

**Data type distinction — the most important concept in this document:**

| Type | Definition | Examples |
|------|-----------|---------|
| **STATIC** | Derived from prior session closes or historical bars. Always available regardless of market hours. Returns the same value whether the market is open or closed. | IV, HV, IVR, SMA 200, RSI, 52w range, YTD, portfolio positions |
| **LIVE** | Intraday / real-time data. Returns 0 or empty `{}` when the market is closed. Populates with real data during market hours (9:30 AM – 4:00 PM ET). The ❌ when closed is not a bug — it means no trading has happened yet today. | RVOL, today's volume, today's P/C flow, intraday OHLC, live bid/ask |

---

## Category 1 — Volatility Regime

*Source: `get_price_snapshot` → `implied_vol_underlying`, `historical_vol`, `implied_volatility_percentile`*
*Data type: STATIC — all fields derived from prior session. Updates intraday when market is open.*

| Field | MCP Field Name | Market Closed | Market Open | Skill Signal |
|-------|---------------|--------------|-------------|-------------|
| Implied Volatility annual % | `implied_vol_underlying.annual_iv` | ✅ prior session | ✅ live, updates intraday | Absolute IV level |
| Implied Volatility daily % | `implied_vol_underlying.daily_iv` | ✅ prior session | ✅ live | Used in expected move calc: `price × daily_iv × √DTE` |
| Historical Volatility 30d % | `historical_vol.annual_pct` | ✅ prior session | ✅ live | Realized vol baseline |
| IV/HV ratio | computed: `annual_iv ÷ annual_pct` | ✅ | ✅ | <100% = buyer's edge · >115% = avoid debit |
| IVR 13-week | `implied_volatility_percentile.high_13w` | ✅ prior session | ✅ live | IV vs own 13w history |
| IVR 26-week | `implied_volatility_percentile.high_26w` | ✅ prior session | ✅ live | IV vs own 26w history |
| IVR 52-week | `implied_volatility_percentile.high_52w` | ✅ prior session | ✅ live | Primary gate: ≤0.45 = pass |
| IVR multi-window divergence | computed across 3 windows | ✅ | ✅ | 13w low + 52w high = recent compression only, not structural |

**Validated values (NVDA, June 18 2026):** IV 35.70% · HV 39.40% · IV/HV 90.6% · IVR-13w 26.6% · IVR-26w 26.4% · IVR-52w 29.5%

---

## Category 2 — Price & Market Data

*Source: `get_price_snapshot` → `last`, `prior_close`, `change`, `open`, `high`, `low`, `bid_ask`, `year_to_date_change`*

| Field | MCP Field Name | Market Closed | Market Open | Skill Signal |
|-------|---------------|--------------|-------------|-------------|
| Last price + session flag | `last.price` + `last.is_close` | ✅ prior close (`is_close: true`) | ✅ live tick (`is_close: false`) | Price anchor. Flag tells the skill which mode it's in. |
| Prior close | `prior_close` | ✅ | ✅ | Previous session reference |
| Positions market price | `positions[].market_price` | ✅ more current than snapshot | ✅ live mark | Use as price anchor when snapshot lags (closed-day workaround) |
| Intraday change $ / % | `change.change` + `change.change_pct` | ❌ empty `{}` | ✅ live | Today's momentum vs prior close |
| Intraday open | `open.open` | ❌ returns 0 | ✅ live | Gap up/down detection |
| Intraday high | `high.high` | ❌ returns 0 | ✅ live | Today's range ceiling |
| Intraday low | `low.low` | ❌ returns 0 | ✅ live | Today's range floor |
| Live bid / ask | `bid_ask.bid` + `bid_ask.ask` | ❌ empty `{}` | ✅ live | Execution spread — required for entry decision |
| YTD change $ / % | `year_to_date_change.change` + `.change_pct` | ✅ prior session | ✅ live | Momentum + direction inference input |

**Closed-day note:** When `last.is_close = true`, snapshot price can lag by one session. Use `get_account_positions()[ticker].market_price` as the more current anchor.

---

## Category 3 — Volume & RVOL

*Source: `get_price_snapshot` → `volume`, `avg_90d_usd_volume` · `get_price_history` → volume array*

| Field | MCP Field Name | Market Closed | Market Open | Skill Signal |
|-------|---------------|--------------|-------------|-------------|
| Today's share volume | `volume.volume` | ❌ returns 0 | ✅ live, cumulative | Raw flow — builds through the session |
| 90d avg USD volume | `avg_90d_usd_volume.volume` | ✅ ⚠️ static | ✅ ⚠️ static | Volume baseline — **units need calibration** (see note) |
| RVOL (today ÷ avg) | computed | ❌ not computable (0 ÷ avg) | ✅ computable | Institutional participation signal — only meaningful during RTH |
| Historical volume array | `get_price_history` → `volume[]` | ✅ prior sessions | ✅ prior sessions | Volume trend on up vs down days over last N bars |
| Volume on up vs down days | computed from history | ✅ | ✅ | Confirms or contradicts price direction |

**Units calibration note:** `avg_90d_usd_volume` returned 34,245,807,434 for NVDA. At $200/share this implies ~171M shares/day, which doesn't match history bar volumes (~15–30M shares/day). Likely total 90-day USD, not per-day average — needs IBKR clarification on next MCP upgrade. Cross-check against history volume array before using.

---

## Category 4 — Range & Performance

*Source: `get_price_snapshot` → `misc_statistics`, `cumulative_perf_*`, `year_to_date_change`*

| Field | MCP Field Name | Market Closed | Market Open | Skill Signal |
|-------|---------------|--------------|-------------|-------------|
| 52-week high | `misc_statistics.high_52w` | ✅ static | ✅ updates if new high | Annual ceiling |
| 52-week low | `misc_statistics.low_52w` | ✅ static | ✅ updates if new low | Annual floor |
| 13-week high / low | `misc_statistics.high_13w` / `low_13w` | ✅ static | ✅ live | Quarterly range |
| 26-week high / low | `misc_statistics.high_26w` / `low_26w` | ✅ static | ✅ live | Semi-annual range |
| 52w range position % | computed: `(price − 52wLow) ÷ (52wHigh − 52wLow) × 100` | ✅ | ✅ | <25% lower third · 25–75% mid · >75% upper/momentum |
| Performance 1-week | `cumulative_perf_1w` | ✅ static | ✅ live | Short-term momentum |
| Performance 1-month | `cumulative_perf_1m` | ✅ static | ✅ live | Monthly trend |
| Performance 1-year | `cumulative_perf_1y` | ✅ static | ✅ live | Annual trend |
| Performance 1-day | `cumulative_perf_1d` | ❌ returns 0 | ✅ live | Today's move vs prior close |

**Validated values (NVDA, June 18 2026):** 52w high $236.54 · 52w low $142.01 · Range position 66.3% (MID RANGE) · YTD +9.74%

---

## Category 5 — Technical Indicators (computed from price history)

*Source: `get_price_history(period=ONE_YEAR, step=ONE_DAY)` → ~251 daily OHLCV bars*
*Data type: fully STATIC — all computed from end-of-day bars. Adding today's bar requires a market-open re-pull after close.*
*No extra MCP calls needed — all computed from raw bar data by the skill.*

| Indicator | Inputs from History | Market Closed | Market Open | Skill Signal |
|-----------|-------------------|--------------|-------------|-------------|
| SMA 200 | `close[]` last 200 bars | ✅ | ✅ same (daily bars) | Primary trend: above = UPTREND ↑ |
| SMA 50 | `close[]` last 50 bars | ✅ | ✅ | Intermediate trend |
| SMA 20 | `close[]` last 20 bars | ✅ | ✅ | Short-term mean |
| EMA 9 / 21 / 50 stack | `close[]` | ✅ | ✅ | 9>21>50 = bullish alignment |
| Price vs SMA 200 % | computed | ✅ | ✅ | >20% above = overextended |
| RSI 14 | `close[]` | ✅ | ✅ | >70 overbought · <30 oversold · ~50 neutral |
| MACD (12, 26, 9) | `close[]` | ✅ | ✅ | Momentum direction + histogram crossover |
| MACD histogram | computed | ✅ | ✅ | Expanding = acceleration · Contracting = fading |
| Bollinger Band upper / lower (20, 2σ) | `close[]` | ✅ | ✅ | Price envelope |
| Bollinger Band width % | computed | ✅ | ✅ | Low = coiling · High = trending |
| ATR 20 | `high[]`, `low[]`, `close[]` | ✅ | ✅ | Expected daily move · stop sizing |
| Keltner Channel (20, 1.5×ATR) | `close[]` + ATR | ✅ | ✅ | Squeeze envelope |
| TTM Squeeze (BB inside KC) | BB vs KC | ✅ | ✅ | True = coiling before breakout |
| Pivot highs / lows (recent) | `high[]`, `low[]` | ✅ | ✅ | Key support / resistance |
| Distance to resistance | computed | ✅ | ✅ | Room to run before ceiling |
| Distance to support | computed | ✅ | ✅ | Buffer below current price |
| Rate of change ROC 10 | `close[]` | ✅ | ✅ | Price acceleration — speeding up or fading? |

**Validated values (NVDA, 251 bars):** SMA 200 ≈ $189.90 · Price +7.8% above (UPTREND ↑) · RSI 14 ≈ 50 (neutral) · BB(20,2) upper $224.31 / lower $199.27 · ATR ≈ $7.50 · TTM Squeeze: NOT firing

---

## Category 6 — Option Flow

*Source: `get_price_snapshot` → `underlying_avg_option_volume`, `underlying_today_option_volume`*

| Field | MCP Field Name | Market Closed | Market Open | Skill Signal |
|-------|---------------|--------------|-------------|-------------|
| Avg call volume 90d | `underlying_avg_option_volume.avgCallVolume` | ✅ static | ✅ static | Structural call flow baseline |
| Avg put volume 90d | `underlying_avg_option_volume.avgPutVolume` | ✅ static | ✅ static | Structural put flow baseline |
| P/C ratio (avg 90d) | computed: `avgPutVolume ÷ avgCallVolume` | ✅ | ✅ | <0.7 = call-dominant · >1.2 = put-dominant. Structural bias. |
| Today's call volume | `underlying_today_option_volume.callVolume` | ❌ returns 0 | ✅ live, cumulative | Live call flow — builds through the session |
| Today's put volume | `underlying_today_option_volume.putVolume` | ❌ returns 0 | ✅ live, cumulative | Live put flow |
| Today's P/C ratio | computed from above | ❌ not computable | ✅ real-time sentiment | Compare to 90d avg P/C — divergence is the signal |

**Validated values (NVDA):** Avg call vol 2,146,455 · Avg put vol 1,307,768 · Structural P/C 0.61 (call-dominant)

**OPT-specific fields note:** `option_open_interest`, `option_midpoint_iv`, `implied_vol` exist in the MCP schema but return invalid/0 when applied to the underlying STK contract (contract_id: 4815747). These require individual OPT contract IDs (specific strike × expiry). Chain browsing to discover OPT contract IDs is not possible via MCP — see Category 10 gaps.

---

## Category 7 — Market Regime (VIX)

*Source: separate `search_contracts("VIX")` → contract_id → `get_price_snapshot`*
*Data type: STATIC when closed (prior session VIX). LIVE when market is open.*

| Field | Market Closed | Market Open | Skill Signal |
|-------|--------------|-------------|-------------|
| VIX level | ✅ prior session close | ✅ live, updates every ~15s | Fear gauge |
| Regime classification | ✅ based on prior VIX | ✅ live | ≤20 = CALM · 20–25 = ELEVATED · >25 = HIGH-FEAR (tighten all gates: vol floor 5M, spread <2%) |

**Implementation note:** Requires a separate two-step MCP sequence — `search_contracts("VIX")` → contract_id → `get_price_snapshot(last)`. Run this at skill init before pulling the ticker.

---

## Category 8 — Portfolio Context

*Source: `get_account_positions()`*
*Data type: STATIC — reflects last known account state. Updates when positions change, not intraday tick-by-tick.*

| Field | MCP Field | Market Closed | Market Open | Skill Signal |
|-------|----------|--------------|-------------|-------------|
| Existing position in ticker | `contract_description` match | ✅ | ✅ | Avoid unintended double directional exposure |
| Position size & direction | `position` | ✅ | ✅ | Long stock + long call = leveraged add, not new position |
| Avg cost basis | `average_price` | ✅ | ✅ | P&L framing — already profitable or underwater? |
| Unrealized P&L | `unrealized_pnl` | ✅ | ✅ | Existing risk already on |
| Daily P&L | `daily_pnl` | ✅ prior day | ✅ live | Today's P&L impact |
| Market price (positions API) | `market_price` | ✅ more current than snapshot | ✅ live | Use as price anchor when snapshot lags |
| Currency of position | `currency` | ✅ | ✅ | USD vs CAD — relevant for Questrade/Wealthsimple context |

---

## Category 9 — Derived / Computed (no extra MCP calls)

| Computed Output | Formula / Inputs | Market Closed | Market Open | Purpose |
|----------------|-----------------|--------------|-------------|---------|
| Expected move (DTE-specific) | `price × daily_iv × √DTE` | ✅ | ✅ tighter with live IV | How far stock could move in trade window |
| Expected move (annual) | `price × annual_iv × √(DTE/365)` | ✅ | ✅ | Annualized version |
| Strike zone estimate | `current_price ± expected_move` | ✅ | ✅ | Narrows chain search before Tradier pull |
| Direction inference | YTD + avg P/C + 52w position + SMA 200 | ✅ static inputs only | ✅ + live P/C + intraday change | Auto-infer bull/bear. Flag MIXED if signals conflict. User can override. |
| Structural trade type | IV/HV + IVR | ✅ | ✅ | DEBIT (buyer edge) vs CREDIT (seller edge) |
| Market open/closed gate | `last.is_close` flag | ✅ detects closed | ✅ detects open | Routes skill to pre-trade brief (closed) or full execution brief (open) |

---

## Category 10 — Confirmed Gaps (MCP Cannot Provide)

| Gap | Detail | Market Closed | Market Open | Who Fills It |
|-----|--------|--------------|-------------|-------------|
| Options chain (strikes × expiries) | `search_contracts(OPT)` returns underlying, not individual contracts | ❌ | ❌ | Tradier → Options IQ Gemini |
| Per-strike Greeks (delta, gamma, theta, vega) | Not in `market_data_names` enum — no greeks field exists | ❌ | ❌ | Tradier → Options IQ Gemini |
| Per-contract OI | Requires individual OPT contract_id — not discoverable via MCP | ❌ | ❌ | Tradier → Options IQ Gemini |
| Per-contract bid / ask | Same — OPT contract_id required | ❌ | ❌ | Tradier → Options IQ Gemini |
| Earnings date | No MCP field exists for this in any snapshot | ❌ | ❌ | Web search — TBLA rule, non-negotiable |
| Fundamentals (P/E, EPS, revenue) | Not in any snapshot field | ❌ | ❌ | Out of scope for this skill |
| Chain browsing / discovery | No `/secdef/strikes` equivalent in MCP | ❌ | ❌ | Tradier → Options IQ Gemini |

---

## Skill Operating Modes

The skill runs in one of two modes based on `last.is_close`:

```
PRE-TRADE BRIEF (market closed — is_close: true)
  Available: vol regime, IVR × 3, IV/HV, technicals (SMA/RSI/MACD/BB/Squeeze),
             range position, 52w levels, YTD, avg P/C ratio, strike zone estimate,
             direction inference (static), portfolio context
  Unavailable: RVOL, today's P/C flow, intraday OHLC, live bid/ask
  Output: "Setup brief — verify RVOL + live flow at market open before entry"

FULL EXECUTION BRIEF (market open — is_close: false)
  Available: everything above + RVOL, today's P/C flow, intraday change,
             live bid/ask spread, real-time direction confirmation
  Output: complete entry decision package
```

---

## Capability Summary

| Category | Total Fields | STATIC (both) | LIVE (open only) |
|----------|-------------|--------------|-----------------|
| Volatility regime | 8 | 8 | 0 |
| Price & market data | 9 | 3 | 6 |
| Volume & RVOL | 5 | 2 | 3 |
| Range & performance | 9 | 8 | 1 |
| Technical indicators (history) | 17 | 17 | 0 |
| Option flow | 6 | 3 | 3 |
| Market regime (VIX) | 2 | 2 | 0 |
| Portfolio context | 7 | 7 | 0 |
| Derived / computed | 6 | 5 | 1 |
| **Total** | **69** | **55** | **14** |

**55 of 69 fields are always available (STATIC).** The 14 LIVE-only fields are not broken when closed — they return 0 because no trading has occurred yet today. They populate with real data the moment the market opens.

---

## IBKR Scanner Configuration — `skill-options-ibkr-radar` Input

> Documented: June 23, 2026. Finalized by Gemini CLI review — see full spec at `options_iq_gemini/Docs/IBKR_SCANNER_SETTINGS.md`.
> This scanner produces the input that `skill-options-ibkr-radar.md` processes. The Radar applies hard gates; the scanner pre-sorts and pre-filters.

### How the Scanner Works (Critical Distinction)

IBKR MultiSort **pre-sorts but does not hard-filter** at the IVR/IV-HV level. It floats the best candidates to the top of 3700+ results. The Radar enforces the hard IVR ≤ 45 gate. Both layers are needed.

### Final Settings (verified June 23, 2026)

| Parameter | Setting | Assessment |
|-----------|---------|------------|
| Average Option Volume | > 10,000 | ✅ Options liquidity floor |
| Average Volume ($) | $100M – $53.38B | ✅ Dollar volume — proper liquidity proxy. Includes megacaps. |
| Options Implied Volatility | 0.03 – 0.50 (3%–50% annual IV) | ✅ Scale corrected. Removes dead assets and post-earnings inflated names. |
| IV / Historical Vol % | 40% – 100% | ✅ Buyer's discount pre-filter. 40% floor = safety against stale data artifacts. Deep-edge setups (IV/HV 40–65%) now captured. |
| 52-Week IV Rank | 0% – 45% | ✅ Sieve 1 enforced at scanner level |
| Current Option Volume | 1,000 – 7.91M | ✅ Ceiling effectively removed |
| Put/Call Volume Ratio | 0.00 – 1.68 | ✅ Excludes panic flow |

### What the Scanner Produces vs What the Radar Does

| Layer | Tool | Role |
|-------|------|------|
| Scanner (IBKR TWS) | MultiSort config above | Pre-filters universe to ~15–20 candidates. IVR ≤ 45 pre-enforced. |
| Radar (skill) | `skill-options-ibkr-radar.md` | Hard-purges on IVR ≤ 45 (verifies scanner), ranks by IV/HV, web-searches earnings + 200d SMA, selects top 3 finalists. |
| Directional Builder (skill) | `skill-options-directional-builder.md` | MCP enrichment on each finalist — full technicals + Phase 12 JSON handoff to Gemini. |

---

## Known Issues / Calibration Flags

| Issue | Detail | Status |
|-------|--------|--------|
| `avg_90d_usd_volume` units unclear | Value 34.24B for NVDA doesn't reconcile vs history bar volumes (~15–30M shares/day) | Unresolved — cross-check against history volume array |
| Snapshot price lags on closed days | `last.is_close=true` price can be 1 session behind `positions[].market_price` | Workaround: use positions market_price as anchor |
| OPT chain not discoverable | `search_contracts(OPT)` returns underlying, not individual strike/expiry contracts | Architectural gap — Tradier fills this |
| Greeks not in snapshot enum | `market_data_names` has no delta/gamma/theta/vega field for any contract type | Confirmed gap — Tradier fills this |

---

## MCP Upgrade Checklist

When a new version of the IBKR MCP is released, test for:

- [ ] Does `search_contracts(security_type=OPT)` now return individual strike/expiry contracts?
- [ ] Are Greeks (delta, gamma, theta, vega) added to `market_data_names`?
- [ ] Is `avg_90d_usd_volume` clarified as per-day or total-90d? Units documented?
- [ ] Is an earnings calendar field added to snapshot?
- [ ] Is a chain-browsing tool added (equivalent to IBKR's `/iserver/secdef/strikes`)?
- [ ] Do `option_open_interest` / `option_midpoint_iv` work on the underlying STK contract (not just OPT)?
- [ ] Is a Greeks endpoint added for OPT contracts discovered via MCP?

---

*Update this file when: (a) a new MCP field is discovered in any tool, (b) a confirmed gap closes due to an IBKR MCP upgrade, (c) a calibration issue is resolved, or (d) a new skill uses MCP data in a new way.*
