# TRADING-INTELLIGENCE-HUB → OPTIONS IQ GEMINI STATE HANDOFF
> **Auto-generated:** 2026-08-02 13:43:06
> **Purpose:** What changed on the hub side that's relevant to Options IQ Gemini. Read this
> at session start alongside your own STATE_HANDOFF.md -- that file covers your own repo's
> state; this one covers the upstream skill/contract side you don't otherwise see.
> **Canonical references (not duplicated here -- go to the source, don't trust a stale copy):**
> `Docs/CENTAUR_SCHEMA_v2.json` (your own copy is authoritative) and the hub's own
> `docs/specs/OPTIONS_SIEVE_SPEC.md` if you need to understand *why* a payload looks the way it does.

---

## 1. Current skill versions (the things that produce your CENTAUR JSON)
- `docs/skills/skill-options-ibkr-radar.md`: Options IQ — IBKR Radar v2.3
- `docs/skills/skill-options-scanner.md`: Options IQ — Autonomous Scanner (v3.1 — Watchlist-Paste Edge Monitor)
- `docs/skills/skill-options-directional-builder.md`: Directional Trade Builder — v1.6
- `docs/skills/skill-options-trade-validator.md`: Options Trade Validator v3.1

---

## 2. Latest hub session (may or may not be Gemini-relevant -- read for context, not everything here concerns you)
### July 31, 2026 — Session 40

**A full live diagnostic of `Spec_Compliant_Screener`'s real IBKR platform settings — two genuine platform bugs found and fixed at the source, a real screener config finalized, one live pipeline run through the corrected screener, and a same-day `paste_parser.py` fix that got a real three-pass review only after being asked whether it had one.**

Opened by live-checking the screener's actual filter panel (screenshots, not memory) at Bala's request — closed two carried Next Steps items in one pass. **Gate C liquidity finding, settled for good:** no dollar-volume filter exists on this screener at all, confirmed by the panel showing only 4 filters where 8 were documented — Gate C's independent per-run computation has been the only real liquidity screen on PATH A this whole time, not backstopping a working pre-filter. **New finding the same look surfaced:** Market Cap has a hard $10B ceiling, a real IBKR platform limit (confirmed by Bala directly), meaning PATH A has silently excluded every $10B+ name for the life of the forward test — documented in `OPTIONS_SIEVE_SPEC.md`/`skill-options-ibkr-radar.md` as a permanent, unfixable structural limitation.

**Bala then tried restoring the 4 missing filters via a live TWS session (Claude Chrome extension).** Put/Call Volume Ratio and Average Option Volume both came back clean and held through save+reload — closing the one filter (Put/Call) that had zero downstream compensation anywhere in the pipeline. Average Volume ($) and Current Option Volume both hit the same real platform bug: a ceiling field that silently clamps to a much narrower value than typed, with no error shown. **Proven, not assumed** — a controlled clean-context test isolated the bug from every other filter, and a specific-ticker pull-through (AAPL/NVDA/MSFT/GOOGL/AMZN/META/TSLA all confirmed genuinely absent from results at the clamped $316.23M ceiling) proved it was a real enforced filter, not a display artifact. Both left deliberately unconfigured rather than kept at a silently-wrong narrow value — **directly proven load-bearing when broken**, not just theoretically risky: a live scan with the accidental 1.00K–2.05K Current Option Volume range returned only 3 results (MXL/VFC/MBLY); removing the filter and re-running the identical scan the same session returned 12. TRADER_LENS caught the mundane mechanical explanation (a suspicious clustering in one column) *before* it was confirmed, and separately caught and corrected an earlier same-session claim ("low consequence") that didn't survive the live comparison — full account in `TRADER_LENS.md`'s own Feedback Log.

**Ran the corrected screener's real 12-name output through Sieve 1.5/Gate A/B/C by hand** (Gate C purged FLG/MBLY; Sieve 2b ranked VFC/AMC/MXL as finalists, VFC checked and cleared against the Cheap IVR Trap despite its IVR of 4), then ran the full pipeline for real via `build_and_log.py`'s own functions rather than reconstructing a raw paste (the real screener's column set had already changed twice that session, a parser mismatch risk worth avoiding). VFC/MXL correctly dedupe-skipped (already OPEN). Logged 4 new positions — AMC (SURVIVOR, BULLISH 5/0/5 unanimous), CAG (REJECT, cross-group migration from SURVIVOR id 70), NCLH (REJECT), BB (REJECT) — verified independently against Gemini's live journal (ids 92-95), not just the script's own success message.

**Fixed `paste_parser.py`'s PATH A row parser for real, then fixed it properly after being asked whether it actually went through `GOLDEN_RULES.md`'s mandatory three-pass review.** The screener's two new display columns (Average Option Volume, Put/Call Volume) meant any real raw paste would now fail against the parser's old fixed 16/17-token layout — updated to 18/19 tokens, both new fields captured as context (never gated), 187/187 tests passing, verified live against a real reconstructed MXL/VFC paste through the actual `run_scan.py` entrypoint. **First pass was correctness-only** — admitted this plainly when asked, then ran the real Pass 2/Pass 3. Pass 2 found a genuine gap: the new header-splitting regex would have failed on a real single-tab-separated paste (every test fixture happened to mock multi-space separation, masking it) — fixed and covered with a dedicated test. Pass 3 (adversarial) surfaced the actual production-grade risk the whole exercise was worth doing for: the parser trusted fixed column *position* and never validated column *order* against the header — a same-count column reorder (not hypothetical; this exact screener reordered its own columns twice in this single session) would have silently misparsed values into the wrong fields with no error. Built `_validate_header_order()` to close it for real, applied symmetrically to PATH B (the exact failure class that hit `HUB_CORE` in Session 39, that time only caught because the count also happened to change too), with 6 new tests including two that construct a real reorder and confirm it now raises `ParseError` instead of silently succeeding. One honest residual limitation named, not hidden: a pathological paste with header markers split across two lines could still bypass the new check — extremely low probability, not fixed.

**Two more real `resolve_positions.py` batches found running outside this session's own control**, on top of the pattern already caught three times before. One (5 resolutions, dated Jul 30) was inherited at session start, same shape as always. **The second is new: found only at session close, dated today (Jul 31), with no `resolve_positions.py` invocation anywhere in this session's own conversation** — meaning it ran in a separate process while this session was still active, the first time this pattern has shown up *mid-session* rather than only between sessions. Both verified against Gemini's live journal, not just the local CSV, and committed together with this session's own work per established precedent.

**Forward test at close: 42 SURVIVOR built (28 resolved: 10 TARGET/18 STOP, 14 open) / 38 REJECT built (27 resolved: 10 TARGET/17 STOP, 11 open)** — the confirmatory bar (n≈30/group, resolved only) is now **2 SURVIVOR / 3 REJECT resolutions away**, closer than it looked mid-session precisely because of the second uncommitted batch found only at close.

---

## 3. Open cross-repo Known Issues (from the hub's Known Issues table, filtered to rows tagged "cross-repo")
No open cross-repo Known Issues rows as of this generation. (Valid state, not an extraction failure.)
