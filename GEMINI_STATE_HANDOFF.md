# TRADING-INTELLIGENCE-HUB → OPTIONS IQ GEMINI STATE HANDOFF
> **Auto-generated:** 2026-07-28 15:33:02
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
### July 28, 2026 — Session 37

**Built the paste→sieve→log orchestrator (`run_scan.py`) after Bala flagged hand-rolled scratchpad Python as error-prone; found and fixed two real bugs by actually running the new code and actually rendering the new artifacts; applied TRADER_LENS directly, in real time, to two of Bala's own hypotheses about the forward test's real-dollar results, reframing both rather than accepting or dismissing either outright.**

Opened with the mandatory cross-repo check catching a real stale row: the Known Issues line for Gemini's stale skill-file-path references (drafted, never sent) turned out already fixed — Gemini's own `STATE_HANDOFF.md`/`KNOWN_ISSUES.md` said so, verified directly against the live `PROTOCOL.md`/`.agents/AGENTS.md`/`Docs/CLAUDE_MCP_SKILL_HANDOFF.md` files rather than trusted on the claim, and flipped RESOLVED. Committed a pre-existing uncommitted `resolve_positions.py` batch from Jul 27 (6 positions: NVDA/GS STOP, XLF/LW TARGET, plus a second trend-aligned DOWNTREND loss each on PATH and CAG) and logged it as `FORKING_PATHS_LOG.md` Entry 6 — re-running Entry 4/5's UPTREND/DOWNTREND split against the newly-grown resolved set (18→25) found the previously striking 0%/64% gap had narrowed to 22%/54%, a concrete demonstration of how far a "compelling" small-n split can move once n grows even modestly.

Ran two real PATH A batches and one PATH B batch through the pipeline (by hand at first, then via the new orchestrator): CAG logged a third time (id 70, the exact ticker Entry 5/6 already flagged as the standing trend-hypothesis counter-example), XLF/PATH/NIO via PATH B (ids 71-73), and BAH (id 74, BEARISH 4/4 unanimous) via the finished `run_scan.py`. Bala asked directly whether the pipeline is "regime gated, trading with the market not against it" — checked the live code rather than assumed: VIX regime is fetched and logged every run but never gates anything. Documented as a new Guardrail 7 in `FORWARD_TEST_PROTOCOL.md`, splitting "regime" into three genuinely different things (VIX level / broad-market trend / per-name trend-alignment) and deliberately not wiring any of them into a live gate mid-test — doing so now would be exactly the gate-shopping Guardrail 1 already bans.

**Built `run_scan.py`** (+ `sieves.sieve_input_from_paste_row()`), chaining `parse_paste()` → the sieve stack → `build_and_log.py`'s own `compute_builds()`/`apply_builds()` — replacing the manual CSV-construction step flagged as a known gap since Session 30. Verified live against both of that day's real pastes, exact match to the hand-run results including dedupe skips. Stress-tested it further at Bala's explicit request ("thoroughly test the gaps") past the point normal review would stop: floating-point drift in the IV/HV back-solve came back negligible (worst case 1.42e-14), a `--format` mismatch fails loud correctly, but a real bug turned up — a PATH A row with a missing Market Cap or dollar-volume field was silently falling through Gate A/C as if pre-cleared by PATH B's curation convention, when PATH A has no curation to justify that skip. Fixed: now explicitly `UNSCREENABLE`. Also missed the `GOLDEN_RULES.md` three-pass review ritual on the first two rounds of new code, both times only running it after being asked directly — corrected both retroactively and saved a standing feedback memory (`feedback_three_pass_review.md`) so it runs unprompted from here on, not only when asked a second time.

Built two artifacts. `pipeline_map.html` — a plain-language map of Path A/Path B, the Sieve, Hub-vs-Gemini enforcement, and the 9-script toolbox. Then `money_simulation.html` (+ `generate_money_simulation.py`), a real-dollar replay of every resolved trade, which surfaced something the percentage-only view had hidden: at 1 contract per trade, SURVIVOR is down **-$2,302.50** in real dollars while REJECT is up **+$756**, driven disproportionately by one GS stop-out (-$1,380 — roughly 7x any other trade's swing, purely because GS trades at $1,070/share). Two real bugs found only by actually running/rendering the new code, not by re-reading it: a within-batch classification gap (a real trade with an unrecognized `resolution` value could silently vanish from both totals — now fails loud) and a genuine CSS bug in the artifact itself (color tokens scoped to `.viz-root` but referenced on `body`, its ancestor — custom properties never cascade upward, leaving the page genuinely invisible on a dark platform background until fixed).

**TRADER_LENS applied directly to two of Bala's own reads of the money simulation**, not just to external claims. First: "REJECT beating SURVIVOR this cleanly means the market is being manipulated, an insider is involved" — set aside in favor of three cheaper, already-on-file explanations (n=25 nowhere near n≈30/group; Entry 4's own finding that the IV/HV-compression thesis might be backwards, not sabotaged; the standing trend-regime hypothesis already being tracked). Second: "favor cheap options over costly ones" — reframed from a selection-filter idea (which would discard valid edge on expensive names) into the actual fix, fixed-dollar-risk position sizing, built as a second toggleable view in the same artifact. Sizing every trade to ~$500 of risk instead of 1 flat contract flips the simulation's total from -$1,546.50 to **+$1,310.50** (+3.3% ROI) — GS alone can't be sized under that budget even at 1 contract, flagged explicitly rather than forced. Logged as a new dated entry in `TRADER_LENS.md`'s Feedback Log. **Left open at close:** the hosted artifact URL for the rebuilt money simulation renders blank on the actual claude.ai page despite the file being verified fully correct — including live toggle interaction — via a local test server; looks like a platform-side propagation issue specific to this republish, not a code defect, unconfirmed by Bala as of close. 158 tests passing (was 133). Forward test: 13 SURVIVOR (23% win rate) / 12 REJECT (58% win rate) resolved, 17 SURVIVOR / 17 REJECT open — survivor-shortfall checkpoint at 13/15 with ~49 days left to Sept 15.

---

## 3. Open cross-repo Known Issues (from the hub's Known Issues table, filtered to rows tagged "cross-repo")
No open cross-repo Known Issues rows as of this generation. (Valid state, not an extraction failure.)
