# SKILL_MAP.md — Trading Intelligence Hub

> One-page map of every Claude skill in this hub: what it does, who it serves, what triggers it, and where it sits in the pipeline.
> Source of truth for skill inventory. Read alongside `CLAUDE_CONTEXT.md` and `PERSONA.md`.
> Last updated: July 12, 2026 (Session 24 continuation) — full regeneration against the live skill files after this map was found stale in ≥4 places during a Fable 5 review (wrong versions, two "pending"/"known bug" notes that had already been fixed since Session 17, a whole skill missing). Regenerated from the actual skill files, not carried forward from memory.

---

## At a Glance

| # | Skill | File | Version | Serves | Entry/Stage | Status |
|---|-------|------|---------|--------|-------------|--------|
| 1 | IBKR Radar | `skill-options-ibkr-radar.md` | v2.3 | Options IQ Gemini | PATH A entry (manual paste) | ✅ Active |
| 2 | Options Scanner | `skill-options-scanner.md` | v3.0 | Options IQ Gemini | PATH B entry (watchlist-paste) | ✅ Active |
| 3 | Directional Builder | `skill-options-directional-builder.md` | v1.6 | Options IQ Gemini | Shared downstream (Stage 1) | ✅ Active |
| 4 | Trade Validator | `skill-options-trade-validator.md` | v3.1 | Options IQ Gemini | Independent / second opinion | ✅ Active |
| 5 | IBKR Scan | `skill-sta-ibkr-scan.md` | — | STA (swing equities) | STA entry | 🔧 In design |
| 6 | Cross-Repo Fix Verification | `skill-cross-repo-fix-verification.md` | v1 | Hub-level (all engines) | Process skill, not pipeline | ✅ Active (manual invocation only) |
| 7 | Session Start | `skill-session-start.md` | v1 | Hub-level (all engines) | Process skill — orientation | ✅ Active (Session 26) |
| 8 | Session Close | `skill-session-close.md` | v1 | Hub-level (all engines) | Process skill — closing ritual | ✅ Active (Session 26) |

**6 live skills + 1 in design.** Skills 1–4 serve the Options IQ Gemini pipeline. Skill 5 serves the Swing Trade Analyzer (STA). Skills 6–8 are hub-level process skills — none of them sit in either pipeline. Skill 6 (built Session 20) is the "don't trust the summary, read the live code" procedure for verifying Gemini's claimed fixes. Skills 7–8 (built Session 26) encode the session-open orientation and session-close checklist that had been executed from memory each time. Naming convention (standardized June 30, 2026): `skill-[engine]-[purpose].md` where the filename stem **equals** the manifest `name:` — `options-*` family for Gemini, `sta-*` for STA. Claude Web identity is the manifest name, not the filename.

---

## 1. IBKR Radar — `skill-options-ibkr-radar.md` (v2.3)

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

**Output:** Top 3 finalists, Radar format, footer routes to Directional Builder (fixed Session 17), which then hands off to Centaur Mode. Finalist selection requires IV/HV < 100% on all 3, matching Scanner (Session 20, bumped v2.1 → v2.2). A Phase 0 VIX regime pull was back-ported from Scanner (Session 24 continuation, bumped v2.2 → v2.3) — Radar previously had no VIX source beyond "if the user happens to mention it." Sieve/gate rules are governed by `OPTIONS_SIEVE_SPEC.md` — this skill defers to it rather than restating the rules independently.

**Note:** The IBKR scanner pre-sorts and pre-filters, but IBKR rounds/truncates/lags — Radar's own sieves are the authoritative gates. Never assume a ticker is clean just because it survived the scanner.

---

## 2. Options Scanner — `skill-options-scanner.md` (v3.0 — Watchlist-Paste Edge Monitor)

- **Skill name (manifest):** `options-scanner`
- **Serves:** Options IQ Gemini
- **Role in pipeline:** PATH B entry point — reads a pasted `HUB_CORE`/`HUB_EXTENDED` IBKR watchlist table (same paste-driven input as Radar's PATH A, applied to a fixed universe).

**What it does:** Parses a **pasted IBKR watchlist** of liquid, high-beta optionable names (curated CORE/EXTENDED universe) for the volatility-mispricing edge, applies the 4-Sieve gates, and outputs a **Radar-format top 3** ready for Directional Builder. MCP is optional — finalist-verify only.

**Triggers when** you ask to scan for setups, find candidates for today, run the pipeline from scratch, or check the watchlist.

**Phases (v3.0, Session 30 — Task E conversion, spec'd since Session 13):**
- **Phase 0** — VIX from the paste's own VIX row → STANDARD / HIGH-FEAR regime; wall-clock date anchor via python3
- **Phase 1+2** — parse pasted `HUB_CORE`/`HUB_EXTENDED` table by column header → Sieve 1 (real watchlist IVR, not MCP percentile) + Gate B + OI gate (≥500, new) + Sieve 2b. Gates A/C pre-satisfied by curation.
- **Phase 3** — Web search per finalist: earnings only (TBLA, 0–35 day span). 200d trend now reads from the paste's `Price/EMA(200)` column, no search.
- **Phase 3.5 (new, optional)** — MCP-verify IV/HV only on the 3 finalists (≤3 calls), staleness backstop; IVR/Sieve-1 never re-evaluated from MCP.

**Net MCP call count:** ~22–41/run (v2) → **0 for screening** (v3.0).

**The horizon principle (core design rationale, unchanged):** Selection uses signals that persist over a 28-day hold — IVR, IV/HV, trend, earnings-in-window, sustained liquidity. Daily/intraday RVOL is an *execution-timing* signal owned by Centaur Mode — never used for selection.

**Output:** Radar-format top 3 with a directional LEAN per finalist, footer routes to Directional Builder.

**Live IBKR watchlists:** `HUB_CORE` (id 110, created Session 30, all 20 CORE tickers) and `HUB_EXTENDED` (pending — ~65 names, not yet built) mirror the tables below, synced via MCP `create_watchlist`/`edit_watchlist`. Column setup (one-time, not API-settable): `IBKR_SCANNER_WATCHLIST_SETUP.md`.

**⚠️ Buying vs selling inversion:** `options-iq`'s watchlist docs are a premium-SELLING system (IV/HV ≥ 110% = tradable). This scanner is premium-BUYING (IV/HV < 100% = edge) — thresholds are inverted, column plumbing only is shared.

**Watchlist expansion (Session 26, Jul 15):** 20 names added to EXTENDED from Bala's own conviction research, after deduping against the existing list and filtering out Canadian TSX/Venture-only tickers with no US options market. New theme sections: Optical & Connectivity (GLW, APH, FN), Enterprise Tech & Comms (DELL, HPE, HPQ, TMUS, KEYS), Defense & Sovereign AI (NOC), Physical AI & Robotics (CGNX, ISRG), Industrials & Water (XYL); plus additions to existing themes (BWXT→Nuclear, ASML/LSCC→Semis, PATH/GIB→Software, ASTS→Space, TRP→Energy, MOD→AI Infra/Power). Six of these (MOD, FN, CGNX, LSCC, ASTS, PATH) join the existing thin-name OI-verification list — now enforced every run via the paste's OI gate, not a manual pre-check.

---

## 3. Directional Builder — `skill-options-directional-builder.md` (v1.6)

- **Skill name (manifest):** `options-directional-builder`
- **Serves:** Options IQ Gemini
- **Role in pipeline:** Shared downstream **Stage 1** — runs once per finalist from either entry path.

**What it does:** Pulls everything IBKR MCP knows about a single ticker, computes derived indicators from price history, optionally reads a TradingView chart screenshot (**Gemini Edge Scanner** Pine indicator — dashboard table is the primary read surface), infers/confirms directional bias, runs an options-liquidity pre-screen, and emits a structured **Phase 12 / CENTAUR_SCHEMA_v2 JSON** handoff block for Gemini Stage 2.

**Triggers when** you name a ticker and want to build a trade / find the best setup / get a directional read (accepts ticker + optional bullish/bearish + optional chart screenshot; auto-infers direction if not declared).

**Pulls/computes via MCP:** volatility regime (IV/HV/IVR), RSI, EMA stack, MACD, TTM Squeeze, Bollinger width, ATR, strike zone, put/call flow, portfolio context (`get_account_positions`).

**Direction inference:** up to 8 signals (5 MCP-based always available + up to 3 conditional — today's P/C only if market open, 2 chart-derived rows only if a screenshot was provided and the chart has ≥ 200 bars) → BULLISH/BEARISH via a dynamic strict-majority rule (not a fixed count — Session 19 fix), surfaces conflicts (e.g. dual-signal IVR-vs-IV/HV conflict, or an exact tie falling to MIXED).

**What it does NOT do:** select strikes, recommend expiries, compute Greeks, promise outcomes — those belong to Gemini Stage 2 (chain resolution via Tradier).

**Output:** CENTAUR JSON (ASCII-clean), `POST localhost:5002/analyze/centaur`, with a 30-min TTL warning.

---

## 4. Trade Validator — `skill-options-trade-validator.md` (v3.1)

- **Skill name (manifest):** `options-trade-validator`
- **Serves:** Options IQ Gemini
- **Role in pipeline:** Independent — second opinion / ad-hoc / Canadian, outside the main flow.

**What it does:** Validates a specific single-leg call or put on US **or Canadian** underlyings (equities + ETFs/indices). Three modes:

- **Mode 1 — Default Verdict** (~150 words): quick go/no-go. Always the default unless asked for more. Accepts a Gemini Centaur briefing, an HTML-terminal paste, or a plain-text trade description — each has a different available-fields set (Gemini's briefing, notably, has no Gamma/Vega/IV%/HV30/terminal score; the skill states "not provided" rather than fabricating them). Requires web search for current price + earnings before responding.
- **Mode 2 — Deep Dive** (6-phase): technical setup, fundamentals, macro regime, options flow & IV, Greeks, mandatory P&L tables → verdict.
- **Mode 3 — Comparison:** paste two options, pick one.

**Triggers when** you describe an options trade, give strike/expiry/premium, paste a Gemini trade plan for a second opinion, ask if a call/put is good, or want a risk/reward breakdown.

**Three use cases:** (1) second opinion on Gemini recommendations — the primary one, (2) ad-hoc trades not from the Radar flow, (3) Canadian/TSX underlyings (Gemini is US-only via Tradier).

**Hard rule:** never skip the two required output tables; web search required in Modes 1 & 2. IV Rank via web search has no reliable free source (Market Chameleon/Barchart all blocked) — fall back to IV-vs-HV30 rather than a fabricated IVR number.

---

## 5. IBKR Scan — `skill-sta-ibkr-scan.md` (🔧 in design)

- **Serves:** Swing Trade Analyzer (STA) — *not* the options pipeline
- **Role in pipeline:** STA entry point.

**What it will do:** Parse IBKR scanner screenshots via Claude vision, apply STA's 10-filter SEPA/CAN SLIM configuration, call the STA API (`localhost:5001`), and rank the top 5–10 candidates.

**10 validated filters** (3-LLM audit, STA Day 77): Market Cap ≥ $1B, AvgVol ≥ $5M, Price/EMA(200) 1.05–1.65, Price/EMA(50) 1.00–1.20, ROE ≥ 15%, EarnGrw% ≥ 20%, Inst.Held 25–90%, 52W High Proximity ≤ −25%, MACD Histogram ≥ 0, Change% −2 to +8.

**Status:** Design complete, ready to build.

---

## 6. Cross-Repo Fix Verification — `skill-cross-repo-fix-verification.md` (v1)

- **Serves:** Hub-level — all three engines, not one pipeline
- **Role:** Process skill, not a pipeline stage. Doesn't sit in either diagram below.

**What it does:** Encodes the "don't trust the summary, read the live code, run it, check for silent-failure/hardcoded-content/path-fragility/overstated-language patterns" procedure — used repeatedly (Session 20) to verify Gemini's claimed fixes against `options_iq_gemini`'s actual code rather than accepting its own status write-up.

**Triggers when:** invoked manually (`@`-reference or ask directly) — **not** an auto-triggering Claude Code skill. Mandatory whenever `CLAUDE_CONTEXT.md`'s Known Issues table has a row tagged "cross-repo" (see that file's session-start instructions) — Gemini can fix a hub-reported finding independently, with no mechanism to report back, so a stale "unfixed" row is a real recurring failure mode this skill exists to catch.

**Status:** Active since Session 20.

---

## 7. Session Start — `skill-session-start.md` (v1)

- **Serves:** Hub-level — every session, all three engines
- **Role:** Process skill, read-only orientation. Doesn't sit in either pipeline.

**What it does:** Reads `CLAUDE_CONTEXT.md` + `PERSONA.md`, checks whether a cross-repo Known Issues row makes `skill-cross-repo-fix-verification.md` mandatory, anchors the wall-clock date/market status, and gives the user a short orientation (last session's close, top Next Steps, open blockers) instead of making them ask "where are we."

**Triggers when:** the start of a session — the user's first message, or an explicit "let's start" / "catch me up" / "where are we."

**Status:** Active since Session 26. Never edits, never commits.

---

## 8. Session Close — `skill-session-close.md` (v1)

- **Serves:** Hub-level — every session, all three engines
- **Role:** Process skill, the session-end checklist. Doesn't sit in either pipeline.

**What it does:** Establishes what actually changed this session (`git diff`/`git status`, not guesswork), updates Known Issues, appends a Session History entry, refreshes Immediate Next Steps, syncs `SKILL_MAP.md` if any skill version/role changed, regenerates `GEMINI_STATE_HANDOFF.md` when required, rewrites the header summary (prepend, never delete), then stages and commits by name.

**Triggers when:** the user explicitly says "close the session," "let's wrap up," "document everything," or "end of session" — never inferred from a task simply finishing.

**Status:** Active since Session 26. Formalizes a ritual this project had already been running by hand for 26 sessions.

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

HUB-LEVEL (all engines, not in either pipeline above)
  [6] Cross-Repo Fix Verification — invoked manually, or mandatory at session start if a cross-repo Known Issues row is unresolved
  [7] Session Start — every session opens here
  [8] Session Close — every session ends here
```

**Install (all skills):** claude.ai → Customize → Skills → Upload a skill → select the `skill-*.md` file. Skills 7–8 (session-start/close) are Claude Code-only in practice — they read/write local project files (`CLAUDE_CONTEXT.md`, `git`) that a claude.ai upload can't touch.

---

*Regenerate this map from the live skill files whenever a skill's version, triggers, or role changes.*
