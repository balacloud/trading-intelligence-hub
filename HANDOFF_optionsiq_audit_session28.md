# HANDOFF: OptionsIQ — Hub Audit Findings (Session 28, Jul 17 2026)

> **Status:** DRAFTED, not yet relayed to an OptionsIQ dev session. This is the first time hub-side Claude has audited this engine (previously only Gemini received cross-repo audits).
> **Source:** `HUB_AUDIT_FRAMEWORK.md` — two Fable agents (Backend: Categories 1/2/4/5/6/7/8; Frontend: Category 9), against `docs/stable/MASTER_AUDIT_FRAMEWORK.md` v1.7's own checklist. All findings below were spot-checked by the hub session directly (file:line verified), not taken on the subagent's word alone. Test suite confirmed passing (110/110) during the audit — these are logic/data-integrity gaps the suite doesn't cover, not regressions.
> **Guardrail:** hub-side Claude does not edit this repo directly (read-only boundary). This file is the handoff for OptionsIQ's own session to action.

## HIGH severity (4)

**1. BOD cache write path is dead code — the cache tier can never fire.**
`data_service.py:126` defines `_cache_set`, but it's never called anywhere in the codebase (single grep hit = the definition itself). `run_bod_batch` (`batch_service.py:107-141`) fetches chains via `get_chain` and discards them — nothing is ever written to `chain_cache`. Newest rows in the DB are from May 5. Every reference to a warm "bod_cache" tier in docs and the frontend banner describes a path that structurally cannot execute.
*Fix:* wire `run_bod_batch`'s fetched chains into `_cache_set`, or remove the bod_cache tier from the docs/banner if it's intentionally retired.

**2. Stale-cache fallback has no age cap.**
`_cache_get(allow_stale=True)` (`data_service.py:148-170`) never checks `CHAIN_CACHE_STALE_SEC` (`constants.py:178`) — that constant is defined but never imported/used anywhere. A Tradier outage today would silently serve May-5th chains, labeled "ibkr_stale" (implying recency), through the live analyze path.
*Fix:* enforce the age cap in `_cache_get`; if a cached row is older than `CHAIN_CACHE_STALE_SEC`, treat it as a miss.

**3. yfinance HV20 is stored as an IV proxy, contaminating IVR history.**
`analyze_service.py:432-434` calls `provider.get_historical_iv()` when local history is <30 days. `yfinance_provider.py:202-206`'s own docstring: *"yfinance has no direct IV history. Returns 20-day rolling realized volatility (HV20) as an IV proxy."* This gets written into `iv_history.db` and used in IVR percentile math going forward — realized vol permanently mixed into what's supposed to be an implied-vol history.
*Fix:* either exclude yfinance-sourced points from IVR percentile computation, or tag them distinctly so they can be filtered/weighted differently — don't let them silently blend into the same series as real IV readings.

**4. `scan_context` IVR override doesn't actually reach the gate payload.**
`scan_context_parser.py:66-68` sets a local `ivr_confidence="known"` but never writes it into `gate_payload` — the merge at line 87 only includes `ivr_for_gates`, which lacks that key. `analyze_service.py:974-976` never re-injects it either. When local IV history is thin (exactly the case the paste-a-scan-context feature exists for), seller gates still branch on the stale `ivr_confidence=="unknown"` (`gate_engine.py:1374`) and show "IVR unknown" even though a live IVR was just pasted in.
*Fix:* trace the actual key the seller/buyer gates read (`ivr_confidence`, per gate_engine.py:1374 and :760) and make sure `apply_scan_context_to_gate_payload` sets that exact key, not a differently-named local variable.

## MEDIUM severity — grouped, see full agent output for file:line on each

- Category 1 claim "BOD batch is dead — never called" is itself false (it *is* scheduled/called in 3 places) — but the batch is also ineffective (see HIGH #1), so both the doc claim and the underlying feature are broken in different ways.
- Framework's own `strike_vs_em_label` thresholds (Category 1/6, "1.0σ/0.8σ") are stale — code uses `EM_WARN=0.75`/`EM_WARN_STRONG=0.50` (changed Day 68); `API_CONTRACTS.md` (Last Updated Day 62) never synced.
- `scan_context` has no ticker/direction cross-check — pasting one ETF's context while analyzing a different ticker silently applies the wrong IVR/IV_HV/trend data.
- R18 (liquidity nearness must be direction-aware) is not honored: a single `STRIKE_NEARNESS_PCT=0.05` is applied uniformly, including to ITM buyer tracks whose R1 targets (delta 0.68, 8-20% ITM) structurally fail that nearness test by design.
- Several inline magic numbers violate R3 (no magic numbers): TQQQ VIX gate's `>=18`, several DTE bounds, `_SELL_TARGET_DELTA=0.22`, theta default `-0.2`.
- Category 5 (Threading Safety) checklist audits `ib_worker.py`/`ibkr_provider.py` — both deleted Day 69. The checklist itself is stale (though the actual posture — zero ib_insync references, no CB code in app.py — is clean).
- R14 violation: `_merge_swing` (`analyze_service.py:388-399`) fabricates several swing fields (stop_loss, target1/2, vcp_pivot, s1_support, risk_reward) that R14 explicitly forbids defaulting. Path is currently dead (ETF-only 400 guard blocks it), but the violation is real if that guard is ever relaxed.
- `chain_cache.db` locked/corrupt crashes the request with a 500 — only JSON decode errors are caught, not `sqlite3.OperationalError`.
- Frontend: `GateExplainer.jsx` GATE_KB has a dead entry keyed `fomc_gate`, but the backend emits `events` — the tier explanation never actually displays. 7 live-emitted gates (`event_density`, `stress_check`, `put_call_sentiment`, `skew_flow`, `trend_ema`, `tqqq_satellite`, `holdings_earnings`) have no KB entry at all and render a raw gate ID — `trend_ema` is notably the one hard-block gate.
- Frontend: `getTradeHeadline()` has no case for `buy_call`/`buy_put` — headline silently renders null for both buy directions (matches already-tracked KI-110).
- Frontend: `getMoneyness()`'s ITM/ATM/OTM classifier omits `sell_put` from its "is a put" list — the flagship strategy's zone display is currently oriented as if it were a call.
- Frontend: R/R context strings use `breakeven` as the max-profit/loss boundary where the math actually pivots at `strike` (buy_call max loss, sell_call max profit) — and `buy_put` renders a literal `$—` since it has no `long_strike`.
- Frontend: `DirectionGuide`'s sell_put risk copy still references a "bull put spread" cap that cannot occur (single-leg only since Day 57).

## LOW severity — doc/label drift, batch these opportunistically

R4 (app.py ≤150 lines — currently 352, and the framework's own note of "~475" is also stale), R7 (a reachable-in-theory `DEFAULT_ACCOUNT_SIZE=25_000` fallback contradicts the letter of "no default"), dead `ibkr_cache` frontend mapping keys (Header.jsx, SectorRotation.jsx — backend never emits the value), `QualityBanner.jsx` doesn't exist as a file (banner is inline in App.jsx — doc reference wrong, behavior itself is correct), `/api/health` doc shows fields the route doesn't return, duplicate/contradictory endpoint docs for deprecated routes (410 section is correct, but full legacy docs remain further down), an unreachable dead branch in event-density escalation logic (harmless), `memory/MEMORY.md` and `CLAUDE_CONTEXT.md` both still describe a 15-ETF universe and the deleted `ib_worker.py`/`ibkr_provider.py` files, LearnTab.jsx has two more dead gate-ID lookups (`fomc_imminent`, `historical_stress`) plus fabricated placeholder calendar events shown when gates pass.

## Confirmed clean (spot-checked, no action needed)

Tradier-primary chain path, sell-direction OTM filters and delta-centered sort, skew non-blocking null-safe path, all 4 directions' single-leg strategy types and delta targets, TQQQ delta caps, expected-move formula, exit-plan values, FOMC 3-tier gate (buyers never blocked), `trend_ema` direction-aware wiring across all 4 tracks, 5 advisory-only gates + GLD hard-block exception, exactly-6 ETF universe, deprecated-endpoint 410s, SPY regime via STA, IVR 40/35 tiering, `isBearish()` classification, `TopThreeCards.jsx` Day 57-58 field wiring, `BestSetups.jsx` no-mount-fetch behavior.
