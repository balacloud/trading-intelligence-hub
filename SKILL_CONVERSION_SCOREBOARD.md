# SKILL_CONVERSION_SCOREBOARD.md
> Tracks how much of each skill's logic is deterministic (Python-able) vs. genuine LLM judgment.
> Not a rewrite plan — a running measurement. Update alongside session close, same cadence as the Known Issues table in `CLAUDE_CONTEXT.md`.

---

## Why this exists

Session 24 question: how many of the hub's skills are actually doing arithmetic an LLM shouldn't need to re-derive every run, vs. doing something only an LLM can do (synthesis, judgment, reading an ambiguous chart)?

The honest reason to convert a component to Python isn't speed — it's determinism. A skill re-deriving IV/HV or a direction-vote each run can silently drift from `OPTIONS_SIEVE_SPEC.md`. Python code can't reinterpret a threshold; a prompt instruction can. Every conversion below should be justified by *"this removes a drift risk,"* not *"this is possible."*

**Scoring rule:** % = (components that could run as deterministic Python today) / (total components in the skill), estimated from reading the skill file, not guessed. A component only counts as converted once real code exists and has been run against a live case — not when it's merely "clearly Python-able."

---

## Scoreboard

| Skill | Score | Converted | Deterministic (Python-able) | LLM-required (judgment/vision) |
|---|---|---|---|---|
| **skill-options-scanner.md** (v2.1) | 85% est. / **0% converted** | — | VIX regime pull, watchlist iteration, Sieve 1/1.5/2b math, IVR/IV-HV computation, contract_id caching | Web-search synthesis of earnings date + 200d trend framing into prose |
| **skill-options-directional-builder.md** (v1.5) | 85% est. / **0% converted** | — | EMA stack, RSI, ATR, TTM squeeze, direction-inference majority vote, options-liquidity gate, CENTAUR JSON assembly | Optional TradingView chart-screenshot read (though the Pine dashboard already table-izes these values — could become a data pull instead of vision, see Next Milestones) |
| **skill-options-ibkr-radar.md** (v2.2) | 70% est. (paste mode) / **0% converted** | — | Sieve math identical to Scanner, RVOL/52wk-range computation from pasted columns | Screenshot-vision parsing (when not in paste mode); web-search synthesis |
| **skill-sta-ibkr-scan.md** (in design) | 70% est. / **0% converted** | — | 10-filter SEPA/CAN SLIM numeric threshold checks, ranking top 5-10 | Screenshot-vision parsing of the IBKR scanner |
| **skill-options-trade-validator.md** (v3) | 30% est. / **0% converted** | — | R:R calc, IV/HV sub-computations | Quick verdict / deep-dive synthesis — the actual value-add is reasoning about the setup, not arithmetic |
| **skill-cross-repo-fix-verification.md** (v1) | 15% est. / **0% converted** | — | Grep-able anti-pattern checks (silent-default sentinels, hardcoded strings) could be a partial lint pass | The core act — read a diff, judge if a claim is overstated or a fix is real — doesn't reduce to a threshold check |

**Total hub score: 0% converted** (all skills are still 100% prompt-executed). Estimates above are ceiling, not progress.

---

## Next Milestones (ordered by drift risk removed, not ease)

1. **Scanner Sieve math → Python module.** Highest payoff: this is the exact same math Radar and STA-scan also need (`OPTIONS_SIEVE_SPEC.md` already exists to prevent drift between them — a shared Python module *enforces* it instead of documenting it). Candidate: a `sieve_core.py` both Scanner and Radar call into (via Claude Code running it, since claude.ai skills can't execute arbitrary code — see Constraint below).
2. **Directional Builder technicals → Python module.** Second highest: literal duplicate of what `quant_math.py` already does in `options_iq_gemini`. Could import/adapt directly instead of having the LLM re-derive EMA/RSI/ATR from raw bars each run.
3. **Directional Builder chart-read → data pull instead of vision.** The Pine dashboard table already contains the exact fields the skill currently reads via screenshot vision (trend, EMAs, RSI, ATR, RVOL, S/R levels, pattern state). If TradingView alerts/webhooks can export that table, the vision step disappears entirely rather than getting "better."
4. **Cross-repo verification anti-pattern lint.** Low priority, low ceiling — but a quick grep for known bug shapes (`.get(key, "SOME_STRING")` sentinel defaults, hardcoded status strings) could pre-flag candidates before the judgment pass, not replace it.

---

## Constraint this scoreboard has to respect

Claude Web skills (uploaded `.md` files) **cannot execute Python** — they're prompt instructions read by an LLM with tool access (MCP, web search), not a code runtime. Any "conversion" therefore has one of two shapes:
- **(a) Runs in Claude Code**, where Python execution is real (Bash tool) — converts the skill from "LLM re-derives the math" to "LLM calls a script and reads the output." Fully deployable today.
- **(b) Runs inside one of the three engines' own backends** (`quant_math.py`, `gate_engine.py`, a new STA endpoint) — the skill's job shrinks to "call the API, hand back the result," matching what Directional Builder already does for MCP pulls. Requires coordinating with each engine, not just the hub.

Claude Web skills alone can never fully "convert" — they'll always keep the parts that need vision, live search, or judgment. The ceiling on the scoreboard reflects that, not a bug in the estimate.

---

## Update log

- **Session 24 (July 10, 2026):** Scoreboard created. All skills read live (not from memory) to estimate the Python-able %. Zero conversions made yet — this session was measurement only.
- **Session 24 continuation (July 11, 2026):** No scoreboard changes — reconciled this file's own uncommitted state after a session interruption and committed it alongside the Known Issues correction in `CLAUDE_CONTEXT.md`.
