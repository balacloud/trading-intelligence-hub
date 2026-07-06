# TRADING-INTELLIGENCE-HUB → OPTIONS IQ GEMINI STATE HANDOFF
> **Auto-generated:** 2026-07-06 12:04:55
> **Purpose:** What changed on the hub side that's relevant to Options IQ Gemini. Read this
> at session start alongside your own STATE_HANDOFF.md -- that file covers your own repo's
> state; this one covers the upstream skill/contract side you don't otherwise see.
> **Canonical references (not duplicated here -- go to the source, don't trust a stale copy):**
> `Docs/CENTAUR_SCHEMA_v2.json` (your own copy is authoritative) and the hub's own
> `OPTIONS_SIEVE_SPEC.md` if you need to understand *why* a payload looks the way it does.

---

## 1. Current skill versions (the things that produce your CENTAUR JSON)
- `skill-options-ibkr-radar.md`: Options IQ — IBKR Radar v2.2
- `skill-options-scanner.md`: Options IQ — Autonomous Scanner (v2.1 — Curated Edge Monitor)
- `skill-options-directional-builder.md`: Directional Trade Builder — v1.5
- `skill-options-trade-validator.md`: Options Trade Validator v3

---

## 2. Latest hub session (may or may not be Gemini-relevant -- read for context, not everything here concerns you)
### July 5, 2026 — Session 21
**WhatsApp signal-group review (764 signals verified against real prices) + gate-replay experiment + survivors-vs-rejects forward test designed.**
- **Reviewed the "Traders - Seriously ☺️" WhatsApp export** (21,634 messages, Jun 2023–Jul 2026) via full parse + independent price verification (yfinance, 324 tickers) — never trusting chat-claimed outcomes. Deciphered method: discretionary long-only S/R swing trading (2-tier accumulation entries, resistance targets +21%, day-close support stops −12%, R:R ~1.8:1) plus vol-blind near-ATM call buying (median 15 DTE, zero IV/IVR mentions in 3 years). No formal grading system exists — "safe/risky traders" exit tiers + analyst-rating screenshots.
- **Verified performance:** stocks 50.0% win to first target (164W/164L), +5.2%/trade expectancy — but a random-entry control on the same tickers/geometry won 53.3%: no selection skill, all structure + bull beta (SPY +77% same window). Options: 35% plausibly profitable, 46% expired worthless (intrinsic proxy, 196 verifiable), EV ≈ 0 before costs. Reporting bias: 157 win-claim messages vs ~2 genuine loss admissions. Deliverables: `research/WHATSAPP_SIGNALS_REVIEW.md` + `research/whatsapp_signals_dataset.csv` (629-row labeled test set).
- **Gate-replay experiment (review §8):** replayed their 254 option signals through the hub's stack (proxy definitions copied verbatim from `options_edge_backtest_v2.py`). Full stack refuses 121/121 evaluable single-name signals (DTE 21–35 alone blocks 72%) — blocks 60/60 worthless expiries but also 40/42 winners. **Honest reading: the stack is validated as a refusal mechanism; within-flow discrimination remains unproven** (survivors n=8 did worse than baseline). Superiority over the group: proven on process, still unproven on outcomes (our evidence remains backtest_v2 + 6 paper trades 1W/5L).
- **Forward test designed (`research/forward_test/FORWARD_TEST_PROTOCOL.md`):** the discrimination evidence generator — log daily Scanner survivors AND up to 3 near-miss rejects (control group), score both identically (target touch / day-close stop / DTE×0.60 time stop / expiry). Stand-down days count as data; never force top-3 (that would rebuild the group's always-a-signal machine). Positions live in **Gemini's paper-trade journal** via API (`/journal/log|monitor|close` — schema and endpoints live-read from `app.py`/`database.py` first): `/journal/monitor` automates daily marks (delta kill-switch, gamma-surge trail, stagnation flag). Mandatory `FWD_TEST:SURVIVOR|`/`FWD_TEST:REJECT|` prefix in `setup_context` keeps control rows out of Gemini's own performance record. Hub CSV holds only stand-down days + analysis exports. **Pre-registered success criterion** (survivors beat rejects, CI excluding zero) written down before first entry; 30-resolved-per-group ≈ mid-September. Realistic yield ~10–20 unique setups/3 weeks after dedupe, not 45.
- **Borrowed from the group (only surviving items):** R:R ≥ 1.5 floor (trialed in the forward test before formalizing in Directional Builder), day-close stop discipline (candidate for `OPTIONS_SIEVE_SPEC.md` exit language), GOLDEN_RULES candidate: "a bull market does not rescue short-dated long calls — 46% of a 196-trade retail sample expired worthless while SPY rose 77%."

---

## 3. Open cross-repo Known Issues (from the hub's Known Issues table, filtered to rows tagged "cross-repo")
| MEDIUM (finding, unfixed — cross-repo) | `IBKR_VERIFIED` string default masks missing IVR data as pre-verified good data | Session 20: sharpened via STA's `GOLDEN_RULES.md` ("return null, not a plausible fake" — Day 54). `iv_rank = vol_data.get("iv_rank_52w", "IBKR_VERIFIED")` in `analyze_centaur` — when the field is absent, the code doesn't default to null/missing, it defaults to a string that *reads as confirmation that verification happened*. This is broader than the already-fixed IVR>45 hard gate: that fix only covers the case where the value is present and fails the threshold. It does nothing for the case where the value is silently absent and gets treated as pre-verified. Separate finding, not yet relayed to Gemini as its own pushback. |
