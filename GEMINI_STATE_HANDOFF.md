# TRADING-INTELLIGENCE-HUB → OPTIONS IQ GEMINI STATE HANDOFF
> **Auto-generated:** 2026-08-03 11:30:23
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
### August 3, 2026 — Session 41

**Three real paste-driven scans, an earnings-lookup intermittency finding caught in both directions, and a self-caught overreach on an ad-hoc HPE query.**

Ran three live scans through the deterministic pipeline: a 10-name PATH A `Spec_Compliant_Screener` paste (JBLU logged SURVIVOR, MBLY purged on Gate C, VFC/AMC already open), `HUB_CORE` PATH B (ALB logged REJECT, MSTR logged SURVIVOR, HIVE correctly hard-skipped on a 10-day-out earnings date, PYPL/TSLA already open), and `HUB_EXTENDED` PATH B (PATH/NIO/POET all logged REJECT, OKLO/MP hard-skipped on earnings, GIB stood down on `NO_QUOTE`, CCJ/XPEV/NFLX/DRAM already open) — 6 new positions total, each verified directly against Gemini's journal and `forward_test_log.csv`, not just script output. Forward test now at 44 SURVIVOR built (28 resolved) / 42 REJECT built (27 resolved) — still 2 SURVIVOR / 3 REJECT resolutions from n≈30/group; no resolutions ran over the weekend, confirming Session 40's close numbers were still current at this session's start.

**Found and corrected a real earnings-lookup intermittency, in both directions, within the same session.** JBLU's dry-run build read earnings as CLEAR (2026-10-26, Finnhub); the real `build_and_log.py` run seconds later returned UNKNOWN. Checked externally rather than trusting either call blind: JBLU genuinely reported Q2 2026-07-28, confirming the dry-run had the real answer and the real run's UNKNOWN was a transient miss — corrected the CSV note in place with the verified date, old text preserved rather than deleted (same pattern as the Session 33 CAG correction). The same session, HIVE flipped the opposite way (dry-run UNKNOWN, real run correctly found and hard-skipped on an Aug 13 date), corroborated against an independent Finnhub pull already sitting in the Jul 30 HIVE CSV row — confirming this time the real run, not the dry-run, had it right. Logged as a new Known Issues finding: `compute_builds()` has no dry-run branch, so each call hits the live earnings API fresh and can disagree call-to-call, but the fail-safe design (UNKNOWN never fabricates CLEAR, and the real run's own check is what actually gates a build) meant neither flaky call produced an unsafe outcome.

**TRADER_LENS caught a real self-generated overreach on an ad-hoc HPE query, on direct request.** Asked casually about HPE (purged Sieve 1, IVR 61% > 45% ceiling), answered the gate fail correctly but added an unprompted, unsupported line that HPE looked like "a seller setup." Asked to run the finding through the lens specifically — retracted that line: this hub has zero backtest evidence, proxy or real, for any options-selling edge on any single name, so the comment was a confident-sounding conclusion built on nothing but "IV is elevated." Checked the mundane confound that should have been checked before saying anything about IV richness at all, per the TBLA lesson: HPE reports earnings 2026-09-02, 29 days out, squarely inside a normal hold window — an ordinary explanation for elevated IV that has nothing to do with mispricing. Also named, rather than left implicit, that the 45% IVR ceiling HPE failed against is itself a standing unresolved "why this number" question (Known Issues since Session 28) — doesn't change HPE's verdict at a 16-point margin, but the honest answer says so regardless. Full account in `TRADER_LENS.md`'s own Feedback Log.

**Cleaned up a stray file and answered a design question about the Sector Advisory Panel without building anything.** Deleted `research/sector_advisory/refresh_and_open.command alias`, a macOS Finder alias (not real content, likely created by an accidental Cmd-drag) that had sat untracked since before this session. Answered, without implementing, whether an HTML button could invoke the panel's `.command` refresh script directly: no — browser sandboxing hard-blocks a local page from running a local shell script, which is exactly why `refresh_and_open.command`'s own header comment already documents this as the deliberate middle-ground design (one-click regenerate, nothing left running in the background). The only real way to get an in-page button would be a small local backend server the page calls via `fetch()`, which reintroduces the persistent-background-process cost the current design was built to avoid — recommended keeping the `.command` file as-is rather than building that. `research/sector_advisory/sector_advisory.html` (the panel's generated output) remains untracked, not yet decided whether it should be committed or gitignored as a build artifact — Bala hasn't weighed in.

---

## 3. Open cross-repo Known Issues (from the hub's Known Issues table, filtered to rows tagged "cross-repo")
No open cross-repo Known Issues rows as of this generation. (Valid state, not an extraction failure.)
