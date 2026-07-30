# TRADING-INTELLIGENCE-HUB → OPTIONS IQ GEMINI STATE HANDOFF
> **Auto-generated:** 2026-07-30 14:01:54
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
### July 30, 2026 — Session 39

**Four live paste-driven scans logged 13 real forward-test positions, a real HUB_CORE column-layout bug got fixed live in TWS (not code), and a direct user correction reshaped how flags get handled going forward.**

Opened by finding `forward_test_log.csv` already dirty at session start — traced during close to a real `resolve_positions.py` batch (10 resolutions, dated Jul 29) that ran near close *after* Session 38's own documented close (which had only run `--dry-run`) and was never written up or committed. Third occurrence of this exact "local file state outlives the session that produced it" pattern (Sessions 37/38 each caught one already) — committed together with this session's own work.

Ran the paste-driven pipeline live four times. **HUB_EXTENDED** (65 names) logged 5 (PATH/JD/XLF REJECT-arm, GIB/DRAM SURVIVOR) — flagged DRAM's history (2 prior thin-vote `INSUFFICIENT_HISTORY` entries, both STOP) before logging a third, per Bala's explicit go-ahead. **PATH A** (50 of 153, first pull arrived truncated mid-row and was correctly rejected rather than guessed at; resent complete) logged POOL and MXL, flagging POOL's real ~89%-of-mid spread in the record rather than pausing on it. **HUB_CORE** (21 names) failed on the first real attempt — `ParseError: could not confidently detect paste format` — root-caused to a genuine TWS column-layout drift from `HUB_EXTENDED` (17 columns vs the parser's fixed 19-position PATH B format, different order, one dead duplicate column). Walked Bala through the exact target column order twice in TWS (first pass fixed which columns, not the order; second pass matched exactly) — closes the Session 33 Next Steps item that had sat untested for six sessions. Logged HIVE/PYPL/TSLA once fixed, flagging HIVE's genuinely thin quote (spread ~143% of mid) in the record. A second **PATH A** pull (50 of 151) logged AVAV/CPB/VFC, correctly holding back CZR on a dead 0-bid quote rather than fabricating a fill. 13 total new positions, ids 79-91, each verified directly against Gemini's own `trades.db`, not just script stdout.

**Received real, direct pushback mid-session** — "why are you asking me" — after pausing to ask permission a second time on a build (POOL) that had already cleared every deterministic gate. Corrected going forward: TRADER_LENS's job is to flag a caveat into the record, not gate a mechanical build the protocol already resolves; saved as a standing feedback memory. Applied immediately afterward on the HUB_CORE run (HIVE's spread flagged and logged, not asked about).

**DRAM's second `INSUFFICIENT_HISTORY` entry resolved STOP -56.61%**, found via the uncommitted-batch trace above — now 2-for-2 on the exact same thin-vote structural shape. Added `FORKING_PATHS_LOG.md` Entry 7, deliberately reading it against Entry 6's own three-day-old lesson (a much larger, cleaner-looking split had just regressed hard toward noise) rather than treating n=2 on one ticker as a pattern — a more mundane explanation (DRAM's consistently high 84-98% IV/HV) already sits in the data.

Answered a real user question on forward-test methodology directly rather than deferring: whether the once-daily close-of-day resolution (vs. real-time stops) should change now or after n=30/group. Found the exact same idea already scoped and parked once (`PARKED_IDEAS.md` Idea 1, Session 32) with its own explicit "revisit post-Checkpoint-A" trigger — pointed back to that rather than re-deriving new reasoning.

**Ran a real ad-hoc advisory query** (WMT/IBM, "what calls should I make," at Bala's own request) through the live pipeline instead of a narrative answer — reused `build_and_log.py`'s own functions for a one-off non-watchlist check. WMT purged Sieve 1 (IVR 49%); IBM cleared as a genuine SURVIVOR (IVR exactly 45.0%, IV/HV 46.4%, BEARISH 4/5, 222.5 Put) — confirmed a second time against a real live TWS paste of just those two names, matching the ad-hoc read almost exactly. Bala explicitly declined to log IBM as a real forward-test position (hand-picked, not a systematic sweep) — a second real instance of the advisory/forward-test boundary this hub drew once already for the Sector Advisory Panel (Session 38). Sanity-checked a live IBKR order ticket for the same contract against the pipeline's own numbers, catching two things: real quote depth (730x787) that upgraded an earlier OI-based liquidity caution, and that the quote was already up +19.25% intraday — distinguished confirming-in-real-time from chasing a move already priced in.

Forward test at close: **41 SURVIVOR built positions (22 resolved: 7 TARGET/15 STOP, 19 open) / 35 REJECT built positions (23 resolved: 10 TARGET/13 STOP, 12 open)**. Confirmatory bar (n≈30/group, resolved only) unchanged by today's new opens — still 8 SURVIVOR / 7 REJECT resolutions away.

---

## 3. Open cross-repo Known Issues (from the hub's Known Issues table, filtered to rows tagged "cross-repo")
| PENDING (cross-repo, drafted not yet relayed) | STA's `/api/sectors/rotation` has real RS-ratio/momentum/quadrant computation but zero automated test coverage | Session 38 (Jul 29, 2026): found while building the hub's new Sector/Theme Advisory Panel, which pulls this endpoint live for broad-sector context. Grepped `swing-trade-analyzer/backend/tests/` and every `test_*.py` in that repo — no coverage of this endpoint anywhere, unlike the rest of the repo's own test files (`test_categorical_comprehensive.py`, `test_verdict_parity.py`). Not a bug in the endpoint itself — its "swing-trading variant of RRG, not standard de Kempenaer RRG" self-documentation checked out fine, and matches STA's own Day 69 self-review ("Bug 0E-F," deliberately left as-is). Drafted `docs/handoffs/HANDOFF_sta_sector_rotation_test_coverage.md` — a complete, ready-to-drop-in test script matching STA's own established convention (standalone script against the live server, no pytest/mock dependency STA doesn't otherwise use), **verified live against the real running `localhost:5001` server before handoff** (9/9 checks passed), not just proposed. Not yet relayed into STA's own dev session. |
