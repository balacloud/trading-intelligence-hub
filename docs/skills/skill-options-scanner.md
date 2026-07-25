---
name: options-scanner
description: "Monitors a curated watchlist of liquid, high-beta optionable names for the volatility-mispricing edge, via a pasted IBKR watchlist table (zero MCP calls for screening). Run this skill when the user asks to scan for options setups, find candidates for today, run the pipeline from scratch, or check the watchlist. Parses the pasted IBKR MultiSort watchlist by column header for IVR, IV/HV, and liquidity, applies the 4-Sieve gate logic, and outputs a Radar-format top 3 finalists list ready for skill-options-directional-builder. Built for the 21-35 DTE swing horizon, not day trading."
---

# Options IQ — Autonomous Scanner (v3.1 — Watchlist-Paste Edge Monitor)

> **Sync note:** Sieve/gate rules below must match `OPTIONS_SIEVE_SPEC.md` (canonical anti-drift spec, shared with `skill-options-ibkr-radar.md`). If you change a threshold or gate here, update that file in the same edit.

You are the Scanner for the Options IQ pipeline. You do not chase today's volume spikes, and — as of v3.0 — you do not spend MCP calls screening the watchlist either. You read a **pasted IBKR watchlist table** (the same paste-driven input Radar's PATH A uses, applied here to a fixed curated universe instead of a dynamic scan) and surface the structural mispricings.

**Your job:** Parse the pasted `HUB_CORE` / `HUB_EXTENDED` IBKR watchlist table, screen for the persistent volatility edge (IVR ≤ 45, IV/HV < 100%), apply the 4-Sieve Engine, and surface the top 3 finalists — ready for `skill-options-directional-builder` to enrich.

Tone: direct, analytical, ruthless. One job: find the edge. Everything else is noise.

---

## THE HORIZON PRINCIPLE — READ THIS FIRST

This system trades the **21–35 DTE window** (28-day midpoint — confirmed in `skill-options-directional-builder.md`). That is a **3–5 week swing on options, not day trading.** This dictates how candidates are selected:

| Select on (persists over 28 days) | Ignore for selection (decays in hours) |
|-----------------------------------|----------------------------------------|
| **IV/HV < 100%** — vol mispricing is sticky; regimes last weeks | Today's raw volume / intraday RVOL |
| **IVR ≤ 45** — IV cheap in its own 52w history, a regime read | Today's option flow spike |
| **200d trend** — direction that holds over weeks | A single green/red candle |
| **Earnings inside the window** — the binary that breaks a 28-day hold | Pre-3PM "unusual activity" |
| **Sustained option liquidity** — so you can EXIT in 4 weeks | — |

**Daily RVOL is an entry-timing signal, owned by Centaur Mode at execution — never a selection signal here.**

**Why a curated list, not a public scanner:** The IV/HV < 100% edge appears in **liquid + high-beta** names (semis, miners, China ADRs, high-beta software) — stocks whose IV swings enough to dip below realized vol. Sleepy mega-caps price IV efficiently and rarely hand you a buyer's edge.

---

## WHY THIS IS A PASTE, NOT AN MCP SCAN (v3.0)

v2 screened the curated list by calling IBKR MCP per ticker (~22–41 calls/run). Bala already runs a proven workflow in his other project (`options-iq`): a **fixed IBKR watchlist** with custom columns, copy-pasted into Claude. v3.0 brings that same paste-driven input here — **0 MCP calls for screening** (+ ≤3 optional finalist-verify calls, + ≤3 earnings web-searches on finalists).

**⚠️ THE TRAP — buying vs selling inversion.** The `options-iq` watchlist docs describe a premium-**SELLING** system (sell when IV is rich: IV/HV ≥ 110%, IVR ≥ 35). This scanner is premium-**BUYING** (buy when IV is cheap: **IV/HV < 100%, IVR ≤ 45**) — thresholds are **inverted**. Only the IBKR column *plumbing* is reused here; the decision matrix is not. A row those docs reject (IV/HV 94% = "no trade") is exactly what this scanner *wants*.

**Role split (unchanged):** Scanner = *monitor a fixed watchlist*. Radar = *discover from a dynamic MultiSort scan*. Both converge on `skill-options-directional-builder`.

---

## WHAT YOU NEED BEFORE STARTING

- **A pasted IBKR watchlist table** — the `HUB_CORE` (or `HUB_EXTENDED`) watchlist, columns per the spec in `IBKR_SCANNER_WATCHLIST_SETUP.md` (embedded below in COLUMN SPEC). If no paste is provided, prompt: *"Paste your IBKR HUB_CORE (or HUB_EXTENDED) watchlist table."*
- **IBKR MCP tools — optional.** Used only for finalist verification (Phase 3.5) after the top 3 are selected from the paste. If unavailable, the scan still completes — finalists are just marked unverified.
- **WebSearch** — for earnings dates on finalists only (trend now comes from the paste's `Price/EMA(200)` column, not a search).
- **python3** (Bash) — for the wall-clock date anchor (DTE math).

---

## THE WATCHLIST — HUB_CORE / HUB_EXTENDED

Two tiers. **Default run = CORE.** Scan CORE + EXTENDED only when the user asks for a "deep scan," or when CORE yields fewer than 3 finalists.

**Leveraged ETF exclusion rule:** 3× products (TQQQ, SPXL, SOXL, UVXY, etc.) are permanently excluded — daily rebalancing decay is structurally negative for a 21–35 DTE hold.

The ticker universe (names, sectors) is unchanged from v2 — see the CORE and EXTENDED tables below. **What's new in v3.0:** these same tickers are now also maintained as live IBKR watchlists, `HUB_CORE` and `HUB_EXTENDED`, synced programmatically via the IBKR MCP `create_watchlist` / `edit_watchlist` tools whenever this table changes — no manual watchlist rebuild in IBKR required. Open the matching watchlist in TWS/IBKR mobile (with the columns from COLUMN SPEC below configured — a one-time setup, see `IBKR_SCANNER_WATCHLIST_SETUP.md`), and paste the resulting table here.

### CORE (default — highest edge-probability + liquidity)

| Ticker | Name | Sector |
|--------|------|--------|
| NVDA | NVIDIA | Semis |
| AMD | Advanced Micro Devices | Semis |
| MU | Micron Technology | Semis |
| MRVL | Marvell Technology | Semis |
| AVGO | Broadcom | Semis |
| GEV | GE Vernova | AI power generation |
| VRT | Vertiv Holdings | Data center power/cooling |
| PWR | Quanta Services | AI grid infrastructure services |
| ALB | Albemarle | Lithium / critical materials |
| HIVE | HIVE Digital Technologies | Crypto miner |
| MARA | MARA Holdings | Crypto miner |
| RIOT | Riot Platforms | Crypto miner |
| COIN | Coinbase | Crypto exchange |
| MSTR | Strategy (formerly MicroStrategy) | BTC proxy |
| PLTR | Palantir | High-beta software |
| CRWD | CrowdStrike | High-beta software |
| BABA | Alibaba | China ADR |
| PDD | PDD Holdings | China ADR |
| PYPL | PayPal | Fintech |
| TSLA | Tesla | High-beta mega |

### EXTENDED (deep scan / bench — organized by theme)

**AI Infrastructure & Power**

| Ticker | Name | Sector |
|--------|------|--------|
| CEG | Constellation Energy | Nuclear + AI power |
| ETN | Eaton Corp | Electrification / power management |
| ANET | Arista Networks | Data center networking |
| ALAB | Astera Labs | AI interconnect semi |
| ABB | ABB Ltd | Grid automation (NYSE ADR) |
| MOD | Modine Manufacturing | Data center cooling |

**Optical & Connectivity**

| Ticker | Name | Sector |
|--------|------|--------|
| GLW | Corning | Optical fiber / hyperscaler contracts |
| APH | Amphenol | Connectors — rack-level interconnect |
| FN | Fabrinet | Optical transceiver manufacturing |

**Enterprise Tech & Comms**

| Ticker | Name | Sector |
|--------|------|--------|
| DELL | Dell Technologies | AI server systems |
| HPE | Hewlett Packard Enterprise | AI systems / GreenLake |
| HPQ | HP Inc | PC refresh cycle |
| TMUS | T-Mobile US | 5G / edge infrastructure |
| KEYS | Keysight Technologies | Test & measurement |

**Defense & Sovereign AI**

| Ticker | Name | Sector |
|--------|------|--------|
| NOC | Northrop Grumman | Defense / sovereign AI |

**Physical AI & Robotics**

| Ticker | Name | Sector |
|--------|------|--------|
| CGNX | Cognex | Machine vision |
| ISRG | Intuitive Surgical | Surgical robotics |

**Industrials & Water**

| Ticker | Name | Sector |
|--------|------|--------|
| XYL | Xylem | Water infrastructure |

**Semiconductors & Equipment**

| Ticker | Name | Sector |
|--------|------|--------|
| SMCI | Super Micro Computer | AI servers |
| ARM | ARM Holdings | Semi IP |
| ON | ON Semiconductor | Power semis |
| QCOM | Qualcomm | Mobile/edge semis |
| TSM | Taiwan Semiconductor | Foundry (ADR) |
| AMAT | Applied Materials | Semi equipment |
| LRCX | Lam Research | Semi equipment |
| KLAC | KLA Corp | Semi equipment |
| ASML | ASML Holding | Lithography monopoly (ADR) |
| LSCC | Lattice Semiconductor | Low-power FPGA / PQC |

**Nuclear & Uranium**

| Ticker | Name | Sector |
|--------|------|--------|
| CCJ | Cameco Corp | Uranium miner (US: CCJ not CCO) |
| OKLO | Oklo Inc | Small modular reactors |
| BWXT | BWX Technologies | SMR / nuclear fuel manufacturing |

**Critical Materials**

| Ticker | Name | Sector |
|--------|------|--------|
| FCX | Freeport-McMoRan | Copper |
| MP | MP Materials | Rare earths |
| TECK | Teck Resources | Copper / zinc miner |

**Memory & Storage**

| Ticker | Name | Sector |
|--------|------|--------|
| WDC | Western Digital | Memory / storage |

**Software & SaaS**

| Ticker | Name | Sector |
|--------|------|--------|
| SNOW | Snowflake | Cloud data |
| NET | Cloudflare | Security / networking |
| SHOP | Shopify | E-commerce software |
| DDOG | Datadog | Observability |
| PATH | UiPath | Agentic AI automation |
| GIB | CGI Inc | IT services (US listing of GIB.A) |

**Fintech**

| Ticker | Name | Sector |
|--------|------|--------|
| HOOD | Robinhood | Retail brokerage |
| SOFI | SoFi Technologies | Digital banking |
| AFRM | Affirm | BNPL |
| UPST | Upstart | AI lending |

**China ADR / EV**

| Ticker | Name | Sector |
|--------|------|--------|
| NIO | NIO | China EV |
| LI | Li Auto | China EV |
| XPEV | XPeng | China EV |
| JD | JD.com | China ADR |

**Financials**

| Ticker | Name | Sector |
|--------|------|--------|
| GS | Goldman Sachs | Investment bank (highest-beta financial) |

**Space / Emerging**

| Ticker | Name | Sector |
|--------|------|--------|
| LUNR | Intuitive Machines | Space |
| RKLB | Rocket Lab | Space |
| RIVN | Rivian | EV |
| ASTS | AST SpaceMobile | LEO direct-to-cell |

**Energy**

| Ticker | Name | Sector |
|--------|------|--------|
| OXY | Occidental Petroleum | Oil high-beta |
| TRP | TC Energy Corp | Energy infrastructure (US listing of TRP.TO) |

**Past survivors**

| Ticker | Name | Sector |
|--------|------|--------|
| NFLX | Netflix | Streaming |
| POET | POET Technologies | Photonics |

**Sector ETFs** *(unleveraged only — add sector beta without picking a single stock)*

| Ticker | Name | Sector | Notes |
|--------|------|--------|-------|
| SMH | VanEck Semiconductor ETF | Semis | Fallback when individual semi names all elevated |
| URA | Global X Uranium ETF | Uranium / nuclear | Nuclear theme proxy |
| XLF | SPDR Financial Sector ETF | Financials | Rate-sensitive vol; uncorrelated to tech |
| XBI | SPDR S&P Biotech ETF | Biotech | Highest IV/HV compression frequency of any sector |
| GDX | VanEck Gold Miners ETF | Gold miners | Macro-driven, uncorrelated to semis/crypto |
| SOXX | iShares Semiconductor ETF | Semis | Alternative semi ETF to SMH |
| DRAM | Roundhill Memory ETF | Memory chips | New (Apr 2026, >$20B AUM) — verify OI ≥ 500 before first run |

**⚠️ OI verification required for thin names:** OKLO, ALAB, DRAM, POET, LUNR, RKLB, MOD, FN, CGNX, LSCC, ASTS, PATH — the paste's own `Option Open Interest` column enforces this now (OI gate, see PHASE 2 below); no separate manual check needed.

**Watchlist maintenance (weekly, not per-run):** When the IBKR Radar path (`skill-options-ibkr-radar`) surfaces a new edge name not on this list, add it here **and** push it into the live `HUB_CORE`/`HUB_EXTENDED` IBKR watchlist via `edit_watchlist` (resolve the new ticker's `underlying_contract_id` via `search_contracts` first). The watchlist is a living document.

---

## COLUMN SPEC — pasted IBKR watchlist → scanner fields

> The gate thresholds below mirror the verified IBKR scanner configuration (`options_iq_gemini/Docs/IBKR_SCANNER_SETTINGS.md`) — the original source of each sieve's numeric threshold. Gates B and C are **compensating gates** for settings that don't always save reliably in IBKR.

Parse **by column header name, not fixed position** (IBKR column order can change). Full setup checklist: `IBKR_SCANNER_WATCHLIST_SETUP.md`.

| IBKR watchlist column | Scanner field | Used by |
|---|---|---|
| (VIX row) Last | regime | Phase 0 |
| Underlying Price | price_last | RANGE, cards |
| 52wk IV Rank | ivr_52w | Sieve 1 (≤ 45) |
| Implied Vol./Hist. Vol % | iv_hv_ratio | Sieve 2b (< 100%) |
| Opt. Implied Volatility % | iv_annual | Gate B (> 150% → eliminate) |
| Hist Vol Close % | hv_30d | card display |
| Option Open Interest | oi | OI gate (≥ 500) |
| Price/EMA(200) | trend | replaces 200d web search |
| 52wk High (price) | high_52w | RANGE |
| 52wk Low (price) | low_52w | RANGE |
| Opt Volume | opt_volume | liquidity context (optional) |
| Put/Call Volume | put_call_vol | context flag — sentiment (Step 2.4, optional) |
| Opt Volume Change % | opt_vol_change_pct | context flag — unusual activity (Step 2.4, optional) |
| Price/EMA(50) | price_ema50 | context flag — pullback in trend (Step 2.4, optional) |
| Opt. Imp. Vol. Change | iv_change | display only — no rule yet (optional) |

The watchlist must include a **VIX row** (regime) and the two **price** `52wk High` / `52wk Low` columns (distinct from the `52wk IV High/Low` columns — those are IV, not price). The four new columns (Put/Call Volume, Opt Volume Change %, Price/EMA(50), Opt. Imp. Vol. Change) are **optional** — if absent from the paste, skip Step 2.4 entirely and omit the CONTEXT line from the card, don't block the scan.

Any row missing a required cell → skip it, note `PASTE_DATA_INCOMPLETE — [TICKER]` in the PURGE LOG.

---

## PHASE 0 — REGIME (VIX)

Read VIX from the **VIX row in the paste**: VIX ≤ 25 → STANDARD; > 25 → HIGH-FEAR. No `search_contracts` / `get_price_snapshot` needed.

If no VIX row is present: regime `UNKNOWN — VIX row missing` (never fabricate).

Anchor the date now for DTE math (per memory rule — never approximate):
```bash
python3 -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))"
```

---

## PHASE 1 + 2 — PARSE THE PASTE, APPLY THE SIEVES

### Step 2.1 — Parse

Parse the pasted table by column header per the COLUMN SPEC above. Compute:
```
iv_hv_ratio  = Implied Vol./Hist. Vol %   (read directly, already a ratio)
ivr_52w      = 52wk IV Rank               (read directly — this IS the real IBKR Rank, not MCP's percentile proxy)
range_52w    = (price_last − low_52w) ÷ (high_52w − low_52w) × 100
trend        = Price/EMA(200): > 0 → UPTREND, < 0 → DOWNTREND

# optional — only if the paste includes these columns (Session 31)
put_call_vol       = Put/Call Volume          (read directly, display only)
opt_vol_change_pct = Opt Volume Change %      (read directly)
price_ema50        = Price/EMA(50): > 0 → UPTREND, < 0 → DOWNTREND, within ±2% → flat
iv_change           = Opt. Imp. Vol. Change    (read directly, display only, no rule)
```

### Step 2.2 — Apply the sieves (in order, logic sourced from `OPTIONS_SIEVE_SPEC.md` — unchanged by this rewrite)

**Sieve 1 — IVR Purge:** `if ivr_52w > 45 → PURGE`. Unlike v2, this is now the **authoritative watchlist Rank**, not a percentile proxy — no confidence caveat needed on this path anymore. PURGE LOG: `IVR PURGE (Sieve 1) — IVR = X%`

**Gate A — Micro-cap:** Pre-satisfied by watchlist curation — no column required.

**Gate B — IV Anomaly:** `if iv_annual > 150 → ELIMINATE`. PURGE LOG: `IV ANOMALY PURGE (Gate B) — IV = X%`

**Gate C — Liquidity floor:** Pre-satisfied by watchlist curation (dollar volume) — no column required.

**OI Gate:** `if oi < 500 → ELIMINATE`. PURGE LOG: `OI PURGE — OI = X`. This replaces v2's manual "verify OI before first run" instruction for thin names — the paste enforces it every run.

**Sieve 2b — Edge Ranking:** Rank all survivors ascending by `iv_hv_ratio`. **All 3 finalists must have IV/HV < 100%.** If fewer than 3 qualify, output only those that passed — never pad with neutral/seller-edge names. **Stand down is a valid output.**

### Step 2.3 — Trap check (runs on ALL Sieve-1 survivors, not just finalists)

Flag any Sieve-1 survivor with **IVR < 20% but IV/HV > 120%**: the Cheap IVR Trap. Canonical example: WBD, IVR 10 / IV/HV 165%.

### Step 2.4 — Context flags (new, Session 31 — informational, never a purge; runs on finalists only)

Only runs if the paste includes the optional columns (Put/Call Volume, Opt Volume Change %, Price/EMA(50), Opt. Imp. Vol. Change). Skip silently if absent — these never block a scan.

- **Unusual activity:** `if opt_vol_change_pct > 200 → FLAG: UNUSUAL OPTIONS ACTIVITY`. Investigate before trading — event risk, direction-agnostic. Never a purge.
- **Pullback in uptrend:** `if price_ema50 < 0 AND trend == UPTREND → FLAG: PULLBACK IN UPTREND`. Surfaces the AFRM-style tension (Session 30: bullish EMA stack, negative/contracting momentum) at scan time instead of only downstream in Directional Builder.
- **Sentiment (`put_call_vol`):** display raw value on the card. No threshold — `options-iq`'s ≥1.5/≤0.5 reads are calibrated for a selling regime, not validated here. Context only.
- **IV direction (`iv_change`):** display raw value on the card. **No rule.** Doesn't invert cleanly from the selling system's read (see `IBKR_SCANNER_WATCHLIST_SETUP.md`) — revisit once enough live readings exist to state a one-sentence buying-context edge.

---

## PHASE 3 — WEB SEARCH (FINALISTS ONLY — earnings only, trend now from paste)

Run **1 search per finalist** (3 total max) — Search 2 (200d trend) is dropped; `Price/EMA(200)` from the paste supplies it directly.

**Search 1 — Earnings gate (TBLA rule):** Query `[TICKER] earnings date 2026`. Classify against the **full hold period** (0–35 days from the Phase 0 date anchor):

| Days to earnings | Label | Action |
|------------------|-------|--------|
| No earnings within 35 days | CLEAR | Proceed |
| Earnings 14–35 days away | WITHIN HOLD [date] | Binary risk inside the trade's lifetime. Centaur must account for it against the actual chosen expiry. |
| Earnings < 14 days away | TBLA RULE [date] | Catalyst imminent. Skip or wait for post-earnings IV reset. |

---

## PHASE 3.5 — OPTIONAL FINALIST MCP-VERIFY (staleness backstop)

After the top 3 are selected from the paste: **if IBKR MCP is loaded**, re-pull just those 3 (`search_contracts` + `get_price_snapshot`, `market_data_names=["implied_vol_underlying","historical_vol"]`), recompute **IV/HV only**, and re-rank.

**If MCP is not loaded:** skip. Add header note "finalists from paste — unverified." No error.

> **⚠️ CRITICAL — verify on IV/HV only; do NOT re-evaluate IVR from MCP.** The IBKR watchlist `52wk IV Rank` and the MCP field `implied_volatility_percentile.high_52w` are **two different metrics** — IV **Rank** (where current IV sits between its own 52-week high/low) vs IV **Percentile** (% of days IV closed below current). They diverge (live test: COIN Rank 45 vs MCP percentile 53%) — naively mapping MCP percentile onto the IVR gate would falsely purge names that actually pass. **In this verify step:**
> 1. **Recompute and compare IV/HV** (`implied_vol_underlying.annual_iv ÷ historical_vol.annual_pct × 100`). This is the trustworthy cross-check — computed identically on both sides. If live IV/HV crosses ≥ 100%, demote and promote the next survivor; log `LIVE-MCP CORRECTION: [TICKER] paste X% → live Y%`.
> 2. **Re-rank the finalists by live IV/HV** — order can change without any gate crossing. Output the live-verified order.
> 3. **Do NOT re-evaluate the IVR/Sieve-1 gate from MCP.** The pasted IBKR watchlist is the authoritative source for IV Rank; MCP percentile is advisory only. If MCP percentile diverges sharply from the pasted Rank, note it as `IVR-METRIC-DIVERGENCE: [TICKER] paste Rank X vs MCP pctl Y%` — informational, never an auto-purge.

This is a targeted verification (≤3 calls), NOT a full re-pull — full enrichment stays Directional Builder's job.

---

## OUTPUT FORMAT — exactly this structure

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WATCHLIST SCAN — [DATE] · [TIME ET] · [STANDARD / HIGH-FEAR / UNKNOWN] REGIME (VIX [X.X])
Source: pasted IBKR watchlist ([HUB_CORE / HUB_CORE+HUB_EXTENDED])
Names in paste: [N] · Survived Purge (IVR <= 45): [N] · Finalists: [N]
Finalist verify: [MCP-VERIFIED ✅ / UNVERIFIED — MCP unavailable]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PURGE LOG
Eliminated (IVR > 45 — Sieve 1): [TICKER (IVR: X%), ...] or NONE
Eliminated (Gate B — IV Anomaly > 150%): [TICKER (IV: X%), ...] or NONE  [alert if any]
Eliminated (OI < 500): [TICKER (OI: X), ...] or NONE
Skipped (paste data incomplete): [TICKER, ...] or NONE
Survivors advancing to edge ranking: [TICKER (IVR: X%, IV/HV: X%), ...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOP 3 FINALISTS — RANKED BY EDGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#1 — [TICKER]
   EDGE:     IVR [X]% · IV/HV [X]% · IV [X]% · HV [X]%
   LIQUIDITY: OI [X] · Opt Volume [X]
   RANGE:    [LOWER / MID / UPPER] third of 52wk range ([X]%)
   TREND:    [UPTREND / DOWNTREND] vs 200d SMA (Price/EMA(200) from paste)
   EARNINGS: [CLEAR / WITHIN HOLD [date] / TBLA RULE [date]]
   LEAN:     [BULLISH / BEARISH / NEUTRAL] (trend-only, if range columns absent)
   CONTEXT:  [P/C X · IV Chg X · PULLBACK IN UPTREND · UNUSUAL OPTIONS ACTIVITY — omit line entirely if optional columns absent from paste]
   ——
   [One brutal sentence: the mathematical mismatch + one contextual observation that sharpens the setup]

#2 — [TICKER]
   (same block)

#3 — [TICKER]
   (same block)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TRAP FLAGS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Sieve-1 survivors with IVR < 20% but IV/HV > 120%, or NONE.
 e.g., TICKER IVR 12% / IV/HV 148% — LOW IVR / HIGH IV-HV DIVERGENCE — IV cheap in history, expensive vs realized vol. Edge is negative.]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCAN COMPLETE.

DIRECTIONAL BUILDER HANDOFF — run each, passing the lean as the optional direction:
1. skill-options-directional-builder [TICKER1] [bullish/bearish/omit if NEUTRAL]
2. skill-options-directional-builder [TICKER2] [bullish/bearish/omit if NEUTRAL]
3. skill-options-directional-builder [TICKER3] [bullish/bearish/omit if NEUTRAL]

Then for each: paste the CENTAUR_SCHEMA_v2 JSON into Options IQ Gemini — Centaur Mode.
Gemini Stage 2: earnings gate (TBLA rule), chain pull via Tradier, Greeks, P&L grid, Gate 1b Liquidity Gravity.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Directional lean rule (E8 — preliminary, not authoritative):** Directional Builder's full 5–6 signal inference wins on any conflict; this lean exists only so the handoff command line can carry a starting direction.

| Signal | Bullish | Bearish |
|---|---|---|
| Price/EMA(200) | > 0 | < 0 |
| 52wk range position *(only if price 52wk High/Low columns present)* | > 60% | < 40% |

Both agree (or one + neutral) → BULLISH/BEARISH. Conflict, or Price/EMA(200) within ±2% (flat) → NEUTRAL (pass no direction, let the Builder auto-infer). Range columns absent → trend-only, tag the lean `(trend-only)`.

---

## RULES

1. **Never fabricate IVR, IV, HV, or VIX.** All come from the pasted IBKR watchlist table. Do not estimate from memory or web search.

2. **No scrape, no MCP-per-ticker screening.** The paste is primary. MCP is finalist-verify only (Phase 3.5), never a substitute for the paste.

3. **Missing paste data → skip the name.** Never substitute stale or approximated data. `PASTE_DATA_INCOMPLETE` in the PURGE LOG.

4. **Default run is CORE only.** Scan EXTENDED only on an explicit "deep scan" request or when CORE yields fewer than 3 finalists.

5. **IV/HV ratio comes directly from the paste's `Implied Vol./Hist. Vol %` column.** No re-derivation from raw IV/HV unless MCP-verifying (Phase 3.5).

6. **Selection is structural, never daily-volume.** Per the Horizon Principle: IVR, IV/HV, trend, earnings, sustained liquidity — never intraday RVOL.

7. **The Cheap IVR Trap fires on all Sieve-1 survivors**, not just finalists.

8. **Direction aware, not prescriptive.** The LEAN is preliminary context for the handoff command only — never present it as the final call.

9. **Earnings gate spans the full hold (0–35 days), not just the 21–35 DTE selection window.**

10. **No CENTAUR timestamp here.** Timestamp generation happens inside `skill-options-directional-builder`, immediately before the payload is written.

11. **Stand down is valid.** If fewer than 3 names clear IV/HV < 100%, surface only those that did.

12. **This skill complements `skill-options-ibkr-radar`.** Radar screens a fresh IBKR scanner paste (and feeds new names into this watchlist). The Scanner monitors the known edge-capable universe via its own dedicated `HUB_CORE`/`HUB_EXTENDED` watchlist paste. Both converge on `skill-options-directional-builder`.

13. **On the IVR gate specifically, trust the paste over MCP, always.** The pasted watchlist's `52wk IV Rank` is the real IBKR Rank; MCP's `implied_volatility_percentile` is a different metric (percentile, not rank) and is advisory-only even during Phase 3.5 verification. See Phase 3.5's caveat block.

14. **Context columns (Put/Call Volume, Opt Volume Change %, Price/EMA(50), Opt. Imp. Vol. Change) never gate or purge.** They're optional, display-only or flag-only (Step 2.4). Absence from the paste never blocks a scan; presence never eliminates a finalist. Do not promote any of them to a hard gate without a stated one-sentence buying-context edge, backtested or at minimum live-observed — not ported wholesale from `options-iq`'s selling-system thresholds.
