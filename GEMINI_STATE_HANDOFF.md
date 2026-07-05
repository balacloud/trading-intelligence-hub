# TRADING-INTELLIGENCE-HUB → OPTIONS IQ GEMINI STATE HANDOFF
> **Auto-generated:** 2026-07-05 07:35:52
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
### July 5, 2026 — Session 20
**Closed the OPTIONS_SIEVE_SPEC.md gap (pending since Session 13) + reviewed Gemini's real schema file + consolidated the end-to-end pipeline doc.**
- **Reviewed `options_iq_gemini/Docs/CENTAUR_SCHEMA_v2.json` directly** (Gemini's real implementation, not assumed from the handoff doc draft) — confirmed it faithfully matches what was recommended: required fields, nullable fields, and every enum checked against the hub's actual skill output (`trend_label`, `range_52w_label`, `price_source`). One minor non-blocking gap: no `additionalProperties: false` anywhere, so a typo'd field name would be silently ignored rather than caught.
- **Built `OPTIONS_SIEVE_SPEC.md`** — the canonical sieve/gate spec that's been pending since Session 13. Re-verified the two real divergences a live audit found (not re-derived from memory): Gate C computed two different ways (Radar: screen `Last × Average_Volume_Shares`; Scanner: MCP `avg_90d_usd_volume`, units unverified) and finalist IV/HV qualification differing between paths (Scanner required <100% on all 3, Radar didn't). Documented Gate C's divergence explicitly as an open question (PATH A trusted more until PATH B's units are settled with a live MCP pull) rather than picking a side without evidence. **Fixed** the finalist-qualification divergence by updating Radar to match Scanner's explicit IV/HV<100% requirement (Radar bumped v2.1 → v2.2). Added a one-line sync-note header to both Radar and Scanner pointing at the new spec.
- **Consolidated the full end-to-end pipeline into `CLAUDE_CONTEXT.md`'s own pipeline section** — previously the workflow only existed in pieces (this file's old PATH A/B diagram stopped at the Gemini handoff; `options_iq_gemini/PROTOCOL.md`'s funnel diagram stopped at "Live Position Management" without saying what that means). The rewritten section now includes the hardened Centaur ingestion gates (verified working, not assumed), the fact that execution and stop-loss monitoring are entirely manual (no order-placement code exists in `options_iq_gemini`), and a pointer to the backtest evidence and its sizing implications.

---

## 3. Open cross-repo Known Issues (from the hub's Known Issues table, filtered to rows tagged "cross-repo")
No open cross-repo Known Issues rows as of this generation. (Valid state, not an extraction failure.)
