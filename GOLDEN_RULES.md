# Golden Rules — Trading Intelligence Hub

> **Provenance:** Adapted from Swing Trade Analyzer's `docs/claude/stable/GOLDEN_RULES.md` (Day 76). Not a copy — curated for what actually fits this hub + the two options engines it coordinates with. Where a rule doesn't fit, that's stated explicitly rather than silently dropped, matching this project's own "don't accept a claim without checking it" discipline.

---

## Three-Pass Escalating Code Review (established Session 34, Jul 25 2026 — Bala's explicit standing rule)

**The rule:** every code change goes through three review-and-fix iterations before it's considered done. This is not three repeats of the same check — **each pass must be strictly more critical than the one before it.** Pass 2 assumes Pass 1 missed something; Pass 3 assumes Pass 2 missed something too. Applies going forward to every code change in this hub, not just this one.

**Reviewer persona:** a 30-year veteran senior software developer/architect — deliberately a *different, more seasoned* persona than `PERSONA.md`'s Alex, who is 30 years **old** with 3 years of quant-desk experience, not 30 years of experience. Worth stating plainly so the two don't get conflated: Alex reviews trading-logic design decisions through a systems-architect + quant-trader lens; this reviewer has shipped and maintained production systems across three decades and reviews with the scar tissue of having been personally burned by the failure modes a first-pass review misses — hardcoded paths that only work on one machine, timezone assumptions that silently drift, an external API's fuzzy match accepted as exact, a regex that grabs the wrong match in the response instead of the one actually asked for.

**Pass 1 — Correctness baseline.** Does the code do what it claims? Read it against its own docstring/intent. Run it (or its test suite) for real. Fix anything simply wrong.

**Pass 2 — Assume Pass 1 missed something.** Edge cases, boundary conditions, failure modes not yet handled, silent-fallback risks (this file's own "return null, not a plausible fake" rule below), whether it matches how it's actually called elsewhere in the codebase, whether it duplicates or drifts from an existing module's established pattern.

**Pass 3 — Adversarial; assume Pass 2 missed something too.** What would make this fail in production specifically — a caller passing something unexpected, a dependency being unavailable, a subtle parsing/matching bug that returns a *plausible but wrong* answer instead of failing loud, whether the design itself (not just the code) is right, whether an existing sibling file already solved the same problem a cleaner way.

**What this is not:** three people rubber-stamping the same read. If a later pass genuinely finds nothing a more skeptical read didn't already catch, say so plainly — inventing a finding to justify the ritual would be exactly the kind of dishonesty this hub's own Known Issues / TRADER_LENS discipline exists to catch everywhere else. A clean Pass 3 is a valid, reportable outcome.

---

## Rules already in effect here (confirmed, not newly adopted)

These overlap with STA's list but were already established this session via memory or convention — listed for completeness, not as new work:

- **Read before you write.** Never assume file/code structure — verify with the live file. (This hub's `feedback_live_read_rule` memory; the whole `skill-cross-repo-fix-verification.md` skill is this principle applied to cross-repo claims.)
- **Never claim a result you haven't run.** Run diagnostics/tests before asserting a fix works. (Verified repeatedly this session — `test_centaur_contract.py`, `test_tradier_calendar.py`, re-running `generate_handoff.py` from a different cwd.)
- **Local files first, then git.** Edit/Write, then `git add` + commit — never the reverse.
- **Update the "last updated" line** on any file that functions as a session-start reference (`CLAUDE_CONTEXT.md`, this file).

## Rules adopted fresh from STA — with the reasoning, not just the rule

**Producer defines the API; consumer adapts.** The hub's Directional Builder is the producer of CENTAUR_SCHEMA_v2 — Options IQ Gemini is the consumer and should validate/adapt to what's defined there, not silently reinterpret or drop fields it doesn't like. This is the architectural principle the whole contract-hardening effort (schema file, `jsonschema` validation, `OPTIONS_SIEVE_SPEC.md`) already embodies — now it's named.

**Return null, not a plausible fake.** A missing value should never be replaced with something that *reads like* a good value. This is sharper than how the Gemini review originally stated it: `iv_rank = vol_data.get("iv_rank_52w", "IBKR_VERIFIED")` doesn't just default to a placeholder on missing data — it defaults to a string that looks like confirmation. Worth relaying to Gemini as its own finding, separate from the IVR hard-gate fix, since the fix only covers the case where the value fails the >45 check — it doesn't cover the case where the value is silently absent and gets treated as pre-verified.

**Silent fallbacks are invisible lies.** STA's own example — VIX=20 on fetch failure — is functionally identical to the VIX Kill-Zone bug already logged in this hub's Known Issues (defaults to inert when the VIX fetch fails, which it usually does). Independent confirmation from a sibling project that this is a *pattern*, not a one-off.

**Dual computation paths guarantee silent divergence.** STA's "same data from 2 endpoints diverged silently" is the exact failure class `OPTIONS_SIEVE_SPEC.md` closed for Gate C. Also flags something not yet checked: `options_iq_gemini` has both `/analyze` and `/analyze/centaur` — worth confirming they don't compute the same technicals two different ways the way Radar/Scanner did.

**"Zero is not null."** Use `null` for missing data, never `0`, and never let `{value && <row>}`-style rendering treat a real zero as "nothing to show." Not yet audited on either engine's frontend — flagged as a future check, not a finding.

**Van Tharp position sizing (entry ≈10% of results, sizing ≈90%).** Directly relevant to the trading-readiness discussion earlier this session. The backtest evidence supports trading small regardless of how good the compression-gate edge looks — this rule is *why*: the edge quality matters far less than not oversizing while the edge is still only proxy-validated. Worth carrying into how position size gets discussed with Gemini, not just entry criteria.

**Never implement without validation — research, backtest, or practitioner consensus required.** This is, retroactively, the single rule that would have prevented "mathematically proved the edge" from ever being written in the first place. Worth being explicit that this is now a standing bar for any future edge claim from either engine, not just the one already caught.

## The 5-type audit taxonomy — adopted for how we scope review requests going forward

STA's taxonomy is more precise than anything this hub had. Adopting it as shared vocabulary:

| Situation | Audit type |
|---|---|
| Validate one specific claim/threshold | **Claim Audit** — verdict per assertion |
| After code changes, before trusting them | **Coherence Audit** — docs-match-code (Layer 1) + logic-is-sound (Layer 2) |
| After a feature ships | **Behavioral Audit** — runtime verification with real data |
| Before building something new | **Design Audit** — spec vs. architecture vs. correctness |
| Domain/research validation | **External Audit** — this hub's two Fable 5 reviews were this type |

Retroactively: the two Fable 5 reviews were **Design Audits**. `skill-cross-repo-fix-verification.md`'s procedure is a **Coherence + Behavioral Audit** combined. The CENTAUR field-by-field trace was a **Coherence Audit**, Layer 1 specifically. Naming this makes future review requests precise — "I want a Claim Audit on whether the compression proxy holds at n=200" is a different, smaller ask than "run a Design Audit on the whole engine."

*"README is marketing. Code is truth. But even true code can implement wrong logic."* — STA's framing, kept verbatim because it's exactly right and exactly what this session was about.

## Rules explicitly NOT adopted, and why

- **"Generate files one at a time, wait for confirmation before the next."** Conflicts with how this hub actually operates — batched, related edits (e.g. the `OPTIONS_SIEVE_SPEC.md` session: spec + two skill edits + doc updates in one pass) have been the norm and haven't caused problems. Adopting this would slow down exactly the kind of work that's gone well.
- **"Auto-update everything — never ask the user to run git commands."** This conflicts with a harder rule I operate under regardless of project preference: commits happen when explicitly asked, not autonomously. Not a judgment on STA's choice for itself — just not something this hub will mirror.
- **"Flat API structures preferred over nested."** CENTAUR_SCHEMA_v2's nesting (`technical{}`, `volatility{}`, `portfolio{}`) is logically organized by category and isn't implicated in any bug found this session (the bugs were about missing validation and unused fields, not nesting depth). Not worth a disruptive schema redesign to match a stylistic preference from a different codebase.
- **Daily `PROJECT_STATUS_DAY[N].md` files.** This hub's consolidated `CLAUDE_CONTEXT.md` Session History serves the same purpose in one file instead of a growing pile of dated ones. Not clearly worse, arguably easier to search — kept as-is.

---

*Update this file when a new cross-project lesson surfaces worth keeping — not on a schedule.*
