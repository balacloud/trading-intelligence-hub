# SKILL_MAP.md — Trading Intelligence Hub

> One-page map of every Claude skill in this hub: what it does, who it serves, what triggers it, and where it sits in the pipeline.
> Source of truth for skill inventory. Read alongside `CLAUDE_CONTEXT.md` and `PERSONA.md`.
> Last updated: June 30, 2026 (Session 16) — Audit #2 confirmed 7/7 web skills aligned with local files.

---

## At a Glance

| # | Skill | File | Version | Serves | Entry/Stage | Status |
|---|-------|------|---------|--------|-------------|--------|
| 1 | IBKR Radar | `skill-options-ibkr-radar.md` | v2 | Options IQ Gemini | PATH A entry (manual paste) | ✅ Active |
| 2 | Options Scanner | `skill-options-scanner.md` | v2 | Options IQ Gemini | PATH B entry (autonomous) | ✅ Active |
| 3 | Directional Builder | `skill-options-directional-builder.md` | v1.4 | Options IQ Gemini | Shared downstream (Stage 1) | ✅ Active |
| 4 | Trade Validator | `skill-options-trade-validator.md` | v3 | Options IQ Gemini | Independent / second opinion | ✅ Active |
| 5 | IBKR Scan | `skill-sta-ibkr-scan.md` | — | STA (swing equities) | STA entry | 🔧 In design |

**4 live skills + 1 in design.** Skills 1–4 serve the Options IQ Gemini pipeline. Skill 5 serves the Swing Trade Analyzer (STA). Naming convention (standardized June 30, 2026): `skill-[engine]-[purpose].md` where the filename stem **equals** the manifest `name:` — `options-*` family for Gemini, `sta-*` for STA. Claude Web identity is the manifest name, not the filename.

---

## 1. IBKR Radar — `skill-options-ibkr-radar.md` (v2)

- **Skill name (manifest):** `options-ibkr-radar`
- **Serves:** Options IQ Gemini
- **Role in pipeline:** PATH A entry point — used when you already have IBKR scanner data in hand.

**What it does:** Runs the **Fantastic 4-Sieve Engine** on IBKR MultiSort scanner output (screenshot or pasted table) and returns the **top 3 finalists** with mathematical edge, directional context, and an earnings gate.

**Triggers when** you paste/screenshot an IBKR options scanner table, ask to screen for candidates, or want the best setups from a watchlist scan.

**The sieves / gates:**
- **Sieve 1** — IVR ≤ 45 purge (Volatility Tax gate)
- **Sieve 1.5** — Gate A (market cap ≥ $1B), Gate B (IV ≤ 150%), Gate C (dollar volume ≥ $100M)
- **Sieve 2** — IV/HV < 100% ranking → top 3
- **From screenshot:** computes RVOL (Volume ÷ AvgVol) + 52-week range position, zero extra API calls
- **Web search per finalist:** earnings date vs 21–35 DTE window (TBLA rule) + 200d SMA trend

**Output:** Top 3 finalists, Radar format, with a Centaur Handoff directive. *(Footer fix pending — should route to Directional Builder, not direct to Gemini.)*

**Note:** The IBKR scanner pre-sorts and pre-filters, but IBKR rounds/truncates/lags — Radar's own sieves are the authoritative gates. Never assume a ticker is clean just because it survived the scanner.

---

## 2. Options Scanner — `skill-options-scanner.md` (v2 — Curated Edge Monitor)

- **Skill name (manifest):** `options-scanner`
- **Serves:** Options IQ Gemini
- **Role in pipeline:** PATH B entry point — autonomous, no manual paste needed.

**What it does:** Screens a **curated watchlist** of liquid, high-beta optionable names through live IBKR MCP for the volatility-mispricing edge, applies the 4-Sieve gates, and outputs a **Radar-format top 3** ready for Directional Builder.

**Triggers when** you ask to scan for setups, find candidates for today, run the pipeline from scratch, or check the watchlist.

**Phases:**
- **Phase 0** — VIX pull → STANDARD / HIGH-FEAR regime; wall-clock date anchor via python3
- **Phase 1** — Curated CORE (~20) + EXTENDED (~50) watchlist; MCP-only, no FinViz scrape; contract_id cache
- **Phase 2** — `get_price_snapshot` per ticker → IVR/IV/HV computed → Sieve 1 + Gates B/C + Sieve 2b (Gate A pre-satisfied by curation)
- **Phase 3** — Web search per finalist: earnings (TBLA, 21–35 DTE) + 200d trend

**The horizon principle (core design rationale):** Selection uses signals that persist over a 28-day hold — IVR, IV/HV, trend, earnings-in-window, sustained liquidity. Daily/intraday RVOL is an *execution-timing* signal owned by Centaur Mode — never used for selection. (This is why scanner v1's "top 30 by today's volume" was wrong.)

**Output:** Radar-format top 3, footer routes to Directional Builder.

---

## 3. Directional Builder — `skill-options-directional-builder.md` (v1.1)

- **Skill name (manifest):** `options-directional-builder`
- **Serves:** Options IQ Gemini
- **Role in pipeline:** Shared downstream **Stage 1** — runs once per finalist from either entry path.

**What it does:** Pulls everything IBKR MCP knows about a single ticker, computes derived indicators from price history, infers/confirms directional bias, and emits a structured **Phase 12 / CENTAUR_SCHEMA_v2 JSON** handoff block for Gemini Stage 2.

**Triggers when** you name a ticker and want to build a trade / find the best setup / get a directional read (accepts ticker + optional bullish/bearish; auto-infers direction if not declared).

**Pulls/computes via MCP:** volatility regime (IV/HV/IVR), RSI, EMA stack, MACD, TTM Squeeze, Bollinger width, ATR, strike zone, put/call flow, portfolio context (`get_account_positions`).

**Direction inference:** 5 signals → BULLISH/BEARISH, surfaces conflicts (e.g. dual-signal IVR-vs-IV/HV conflict).

**What it does NOT do:** select strikes, recommend expiries, compute Greeks, promise outcomes — those belong to Gemini Stage 2 (chain resolution via Tradier).

**Output:** CENTAUR JSON (ASCII-clean), `POST localhost:5002/analyze/centaur`, with a TTL warning. *(Known bug: `room_to_support_pct` sign inverted.)*

---

## 4. Trade Validator — `skill-options-trade-validator.md` (v3)

- **Skill name (manifest):** `options-trade-validator`
- **Serves:** Options IQ Gemini
- **Role in pipeline:** Independent — second opinion / ad-hoc / Canadian, outside the main flow.

**What it does:** Validates a specific single-leg call or put on US **or Canadian** underlyings (equities + ETFs/indices). Three modes:

- **Mode 1 — Default Verdict** (~150 words): quick go/no-go. Always the default unless asked for more. Requires web search for current price + earnings before responding.
- **Mode 2 — Deep Dive** (6-phase): technical setup, fundamentals, macro regime, options flow & IV, Greeks, mandatory P&L tables → verdict.
- **Mode 3 — Comparison:** paste two options, pick one.

**Triggers when** you describe an options trade, give strike/expiry/premium, paste a Gemini trade plan for a second opinion, ask if a call/put is good, or want a risk/reward breakdown.

**Three use cases:** (1) second opinion on Gemini recommendations, (2) ad-hoc trades not from the Radar flow, (3) Canadian/TSX underlyings (Gemini is US-only via Tradier).

**Hard rule:** never skip the two required output tables; web search required in Modes 1 & 2.

---

## 5. IBKR Scan — `skill-sta-ibkr-scan.md` (🔧 in design)

- **Serves:** Swing Trade Analyzer (STA) — *not* the options pipeline
- **Role in pipeline:** STA entry point.

**What it will do:** Parse IBKR scanner screenshots via Claude vision, apply STA's 10-filter SEPA/CAN SLIM configuration, call the STA API (`localhost:5001`), and rank the top 5–10 candidates.

**10 validated filters** (3-LLM audit, STA Day 77): Market Cap ≥ $1B, AvgVol ≥ $5M, Price/EMA(200) 1.05–1.65, Price/EMA(50) 1.00–1.20, ROE ≥ 15%, EarnGrw% ≥ 20%, Inst.Held 25–90%, 52W High Proximity ≤ −25%, MACD Histogram ≥ 0, Change% −2 to +8.

**Status:** Design complete, ready to build.

---

## Where Each Skill Sits — Pipeline View

```
OPTIONS IQ GEMINI
  PATH A (manual):    IBKR scanner paste/screenshot
                          → [1] IBKR Radar ───────────┐
  PATH B (autonomous): "scan the watchlist"            │
                          → [2] Options Scanner ───────┤
                                                       ↓ top 3 finalists
                          → [3] Directional Builder (per finalist, Stage 1)
                                                       ↓ CENTAUR JSON
                          → Options IQ Gemini — Centaur Mode (Stage 2)
                                                       ↓
                          → Gemini Intelligence — Senior Quant
                                                       ↓ (optional)
                          → [4] Trade Validator (independent second opinion)

SWING TRADE ANALYZER (STA)
  IBKR scanner screenshot → [5] IBKR Scan (in design) → STA API → top 5–10
```

**Install (all skills):** claude.ai → Customize → Skills → Upload a skill → select the `skill-*.md` file.

---

*Regenerate this map from the live skill files whenever a skill's version, triggers, or role changes.*
