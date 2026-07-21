# Plan — Formalizing the Ad-Hoc Sieve / Technicals / Payload Stack

> **Planned:** Session 30 (Jul 21, 2026), via an Opus planning pass grounded in `GOLDEN_RULES.md` and `PERSONA.md` (Alex's two lenses — Systems Architect + Quant Trader — applied as an explicit review gate before the design, not after).
> **Status:** Planned, not yet built. Nothing in this document has been implemented.
> **Trigger:** across this session, most of the Options IQ Stage-1 pipeline (sieve/gate logic, contract resolution, technical indicators, CENTAUR payload construction, journal logging for one-off manual runs) turned out to be executed ad hoc — reading JSON tool results and doing the math by eye, or writing disposable `/tmp/*.py` scratch scripts that get deleted after one use — instead of calling tested, reusable code. This plan formalizes the deterministic parts without touching the parts that are genuine judgment.

---

## 0. Grounding facts confirmed by reading the code (not the docs)

- **`build_and_log.py` and `resolve_positions.py` are Tradier-only Python scripts, run as subprocesses. They have no IBKR MCP access.** `build_and_log.py`'s own header states Sieve 1 "can't be automated without a live MCP session." This is the single most important constraint in this whole plan — it's why the new modules must be pure transforms the LLM calls with data it already has, never fetchers that reach for their own MCP data.
- **The dashboard (`research/forward_test/dashboard/app.py`) imports both scripts as modules** and calls a fixed public API: `bl.compute_builds(scan_rows, today)`, `bl.apply_builds(results, today)`, `rp.compute_resolutions(today)`, `rp.apply_resolutions(...)`, `rp.load_tradier_token()`, `rp.fetch_live_mids(...)`, plus `rp.GEMINI_BASE_URL`. **Any refactor must preserve these names/signatures or it silently breaks the dashboard.**
- **`pick_atm_contract()` (`build_and_log.py:202`) is confirmed cruder than the manual process it's meant to replace** — `min(candidates, key=lambda o: abs(o["strike"] - price))`. No delta band, no OI floor, no spread check. Today's manual NVDA/UUUU picks applied all three by hand; the automated script doesn't.
- **`score_direction()` (`build_and_log.py:172`) has a latent denominator bug.** `total_scored = len(signals)` counts keys whose value is `None` (unscored signals). `skill-options-directional-builder.md` Step 6 is explicit the denominator must be *only actually-scored* signals, and calls this exact "stale denominator" pattern out as the Session 18/19 bug. The code reintroduced it. Fixing this is a real correctness win riding along with the formalization, not just tidying.
- **Doc drift already exists on Gate C units.** `OPTIONS_SIEVE_SPEC.md` (line 29) says `avg_90d_usd_volume` is RESOLVED as a genuine daily average (confirmed twice live). `ibkr-mcp-capabilities.md` (lines 83, 88, 293, 306) still says "units need calibration / likely 90-day total." Two docs in the same repo disagree — `sieves.py` forces a decision and one doc must be corrected in the same change.
- **The full technical set (RSI14, MACD, BB/KC squeeze, ATR14, pivots) exists only as prose** in the skill + disposable /tmp scripts. `build_and_log.py`'s `compute_direction()` is a deliberately *reduced* 5-signal set and doesn't compute RSI/MACD/squeeze/ATR/pivots at all.
- **`skill-options-directional-builder.md` is internally inconsistent on smoothing** — line 262 says "Wilder's RSI," lines 278–279 define ATR as a plain `mean()` of true ranges. The spec already disagrees with itself.

---

## 1. Alex's two-lens review (run first, per this project's standing rule)

### Systems Architect lens

**Passes, with one hard rule that has to be enforced or the whole thing fails: these modules must be pure transforms, not fetchers.** The instinct would be to have `sieves.py` "go get the snapshots." It can't — MCP only exists inside the live conversation, not in a subprocess. The correct shape:

> The LLM already receives the MCP JSON in-conversation (that's the "reading JSON by eye" being replaced). The module's job is the *tested, deterministic transform* the LLM calls **on data the caller hands it** — never a thing that invents or fetches its own inputs.

This satisfies "data contracts obvious from structure" (explicit typed dicts/lists in, explicit typed results out), "single responsibility" (transform, not transport), and "no invented data source" — and it's the only shape that actually works given MCP's execution model.

- **No magic numbers:** every threshold (45, 150, 100, $100M, 0.45–0.60, OI 500, 10% spread, IVR<20/IV-HV>120) becomes a named constant with a docstring citing `OPTIONS_SIEVE_SPEC.md`. Passes.
- **Fail loud:** the AVGO case (`implied_vol_underlying` absent) must return an explicit `UNSCREENABLE`/`None` outcome visible in the output, never a silent pass. Passes only if implemented deliberately (§2).
- **KISS / cold-read:** passes for `sieves.py`, `technicals.py`, `centaur_payload.py`. Risk: `contracts.py` trying to own both underlying-resolution (MCP rows) and option-chain selection (Tradier chain) — two different data worlds in one file. Addressed in §6.

### Quant Trader lens

- **Sieves, contract selection, earnings gate — formalize, clear pass.** These are hard gates currently applied by eye; eyeballing 20 JSON blobs for IVR≤45 is exactly the error-prone manual step formalization improves, directly improving go/no-go decision quality.
- **Contract selection (delta band / OI≥500 / spread<10%) — highest-value item in the whole plan.** The automated pick being cruder than the manual one means automation is currently a *downgrade*. Fixing this is the single biggest decision-quality win here.
- **Direction vote — formalize, but it's a score, never a gate.** Per Alex's framework #5, this stays a scoring module; its output (BULLISH/BEARISH/MIXED) must never masquerade as a hard gate.
- **What should NOT be built (Alex actively vetoing):**
  - **Do not fold VIX-regime classification into `sieves.py`.** One scalar, a two-line threshold table, orthogonal to per-ticker gates. Standalone function, not a module, not buried in the sieve pipeline.
  - **Do not build a "fetcher" layer for `sieves.py`/`contracts.py`.** Would be an invented data source and a lie about where data comes from.
  - **Do not auto-generate `radar_notes` prose or the "one brutal sentence."** Synthesis, not computation. `centaur_payload.py` accepts it as a passed-in string, never fabricates it.
  - **Do not let `technicals.py` silently substitute simple averages for Wilder smoothing while calling the field `rsi_14` as if canonical.** Either it's Wilder, or the field name/docstring says otherwise (§6 decision).

**Net: passes both lenses**, provided (a) the pure-transform boundary is inviolable, (b) VIX stays out of the sieve module, (c) the missing-field path is loud, (d) prose/judgment fields are never fabricated.

---

## 2. Module-by-module design

All modules live in `research/forward_test/`, alongside the existing scripts (shared Tradier plumbing, shared dashboard import path). All are pure/deterministic except two explicitly-marked Tradier fetch wrappers.

### 2.1 `sieves.py` — the Sieve/Gate stack

**Purpose:** one function per sieve, plus an orchestrator. Pure transforms over already-fetched IBKR snapshot dicts. Zero fetching. The executable form of `OPTIONS_SIEVE_SPEC.md`.

**Named constants** (each with a one-line reason + spec citation):
```python
IVR_MAX = 45.0                    # Sieve 1 — IV above 52w median = volatility tax
IV_ANOMALY_MAX = 150.0            # Gate B — distressed/event IV
DOLLAR_VOL_FLOOR = 100_000_000    # Gate C — daily USD vol floor
MARKET_CAP_FLOOR = 1_000_000_000  # Gate A
IVHV_FINALIST_MAX = 100.0         # Sieve 2b — all finalists must be < 100%
TRAP_IVR_MAX = 20.0               # Cheap IVR Trap
TRAP_IVHV_MIN = 120.0             # Cheap IVR Trap
FINALIST_COUNT = 3
```

**Data source** — every input traces to `get_price_snapshot` (IBKR MCP), passed in by the LLM. Field paths (`ibkr-mcp-capabilities.md`):
- IVR → `implied_volatility_percentile.high_52w × 100` (PATH B percentile proxy) **or** the pasted watchlist `52wk IV Rank` (PATH A, authoritative) — carried as `ivr_source` so provenance travels with the value.
- IV annual → `implied_vol_underlying.annual_iv × 100`
- HV → `historical_vol.annual_pct × 100`
- dollar vol → `avg_90d_usd_volume.volume` (daily USD, per the spec's twice-confirmed resolution)

**Signatures:**
```python
@dataclass
class SieveInput:
    ticker: str
    ivr_52w: float | None
    ivr_source: Literal["paste_rank", "mcp_percentile"]
    iv_annual_pct: float | None
    hv_30d_pct: float | None
    dollar_vol_usd: float | None
    market_cap_usd: float | None   # often None on PATH B (curation-asserted)

@dataclass
class SieveResult:
    ticker: str
    outcome: Literal["FINALIST","SURVIVOR","PURGED_IVR","ELIM_GATE_B",
                     "ELIM_GATE_C","ELIM_GATE_A","UNSCREENABLE"]
    iv_hv_pct: float | None
    ivr_gate: Literal["PASS","FLAG_VOLATILITY_TAX"] | None
    trap_flag: bool
    reason: str        # human-readable, drives the PURGE LOG line
    provisional: bool  # True when ivr_source == mcp_percentile and near threshold

def sieve1_ivr_purge(item: SieveInput) -> SieveResult | None
def gate_b_iv_anomaly(item) -> bool
def gate_c_dollar_volume(item) -> bool
def compute_iv_hv(item) -> float | None
def cheap_ivr_trap(ivr, iv_hv_pct) -> bool
def run_sieve_stack(items: list[SieveInput]) -> tuple[list[SieveResult], list[SieveResult]]
    # returns (finalists ≤3 all IV/HV<100, all_results_for_purge_log)
```

**Error handling — the AVGO case, load-bearing ("return null, not a plausible fake"):**
- `iv_annual_pct`/`hv_30d_pct` is `None` → `compute_iv_hv` returns `None`, outcome **`UNSCREENABLE`**, `reason="implied_vol_underlying absent from snapshot — cannot compute IV/HV"`. Excluded from finalists, listed explicitly in the purge log. Never a silent pass, never a default to 100%.
- `ivr_52w is None` → `UNSCREENABLE` (Sieve 1 can't run). Not a pass.
- `dollar_vol_usd is None` and `market_cap_usd is None` → `provisional=True`, `reason` names the skipped gate. Never silently "passes" a gate it couldn't evaluate.
- Fewer than 3 finalists is a **valid, first-class output** ("stand down"), never padded.

### 2.2 `contracts.py` — contract resolution + option selection

Two clearly separated concerns, kept explicit rather than sharing state.

**Part A — underlying `contract_id` resolution (IBKR MCP rows, pure).**
```python
def resolve_underlying(rows: list[dict], ticker: str) -> dict | None
    # Rule (directional-builder Step 1): exact symbol==ticker, country_code=="US",
    # prefer NASDAQ/NYSE over other US exchanges.
```
Zero exact-US matches → `None`, caller reports "no US listing resolved" — never guesses the closest-looking foreign/ADR row. Multiple ambiguous matches → `None` with an ambiguity marker, never silently picks the first.

**Part B — option contract selection off a resolved chain (Tradier, one fetch wrapper).**
```python
def select_contract(chain_options: list[dict], direction: str,
                    delta_low=0.45, delta_high=0.60,
                    oi_min=500, max_spread_pct=0.10) -> dict | None
    # Filter option_type by direction, |delta| in band, OI>=oi_min,
    # (ask-bid)/mid < max_spread_pct; among survivors, closest delta to
    # band midpoint, tie-break tighter spread. None = stand down.
```
**Replaces `pick_atm_contract`** — this is the fix for the finding that the automated pick underperforms the manual one. **Requires `greeks:"true"`** on the Tradier chain call (currently `"false"` in `build_and_log.py`) — a one-line change flagged here so it isn't missed. No contract clears all three filters → `None`, with a reason per eliminating filter — never relax a gate to force a pick.

### 2.3 `technicals.py` — indicators + direction vote

**Purpose:** the full technical set as pure functions over OHLCV, plus one thin Tradier fetch wrapper. Standalone-testable with the same copy-pasted arrays the /tmp scripts already used — fixtures port directly.

```python
def sma(vals, period) -> float
def ema_series(vals, period) -> list[float]
def rsi_wilder(close, period=14) -> float
def macd(close, fast=12, slow=26, signal=9) -> tuple[float,float,float]
def atr_wilder(high, low, close, period=14) -> float
def bollinger(close, period=20, k=2.0) -> tuple[float,float,float]
def keltner(close, high, low, period=20, mult=1.5) -> tuple[float,float]
def ttm_squeeze(close, high, low) -> bool
def pivot_levels(high, low, price, lookback=50) -> tuple[float|None,float|None]
def range_52w_pct(price, high_52w, low_52w) -> float
def compute_signals(ohlcv, spy_ytd=None) -> dict
def score_direction(signals: dict) -> tuple[str,int,int,int]   # single canonical impl
```

**The `score_direction` fix (correctness, not tidying):** canonical implementation counts the denominator as **non-None signals only**, matching skill prose and fixing the `build_and_log.py:172` bug. `build_and_log.py` imports this instead of keeping its own copy.

**Pivot sign guard:** port the directional-builder rule verbatim — `nearest_support` must be a pivot low *below* price or `None`; never a negative `room_to_support_pct`. No valid support below price → `None`, not a mislabeled level above price.

**Error handling:** `<200` closes → SMA200/trend signals emit `None` (drop out of the vote), never a partial-window average mislabeled SMA200. `<period` bars for any indicator → `None`, unscored.

### 2.4 `centaur_payload.py` — CENTAUR_SCHEMA_v2 assembly

```python
def build_payload(ticker, direction, sieve: SieveResult, tech: dict,
                  vix, regime, portfolio: dict, earnings: dict,
                  radar_notes: str, timestamp: str) -> dict
def validate_payload(payload: dict) -> None   # raises on schema violation
```
`validate_payload` uses `jsonschema` against `CENTAUR_SCHEMA_v2.json` — reuse the existing contract-hardening work (`test_centaur_contract.py`), don't reinvent. Producer (hub) validates before POST, per "producer defines the API."

**Error handling:** any `None` from the upstream modules emits JSON `null`, never `"IBKR_VERIFIED"`, `0`, or a placeholder that reads like confirmation. `iv_rank_source` carries `"paste_rank"` vs `"mcp_percentile_proxy"` honestly. Earnings MCP can't supply stays the explicit `"VERIFY — not available from MCP"` string.

**`iv_hv_ratio` units gotcha:** schema mandates percentage-style (71.4, not 0.714). **The existing `hive_centaur_payload.json` already violates this** (`"iv_hv_ratio": 0.704`) — `build_payload` must emit percentage form; add a fixture asserting it.

### 2.5 Extensions to `build_and_log.py`

**Preserve exactly** (the dashboard's import contract): `compute_builds`, `apply_builds`, `log_to_journal`, `append_csv_rows`, `fetch_existing_open`, `load_tradier_token`, `GEMINI_BASE_URL`.

**Swap internals, keep signatures:** `build_position` calls `contracts.select_contract` instead of `pick_atm_contract`; `compute_direction`'s scoring delegates to `technicals.score_direction`. Behavior improves, public API unchanged.

**New: a single-position entry path.** `build_and_log.py --single` (one ticker + group + failed_gate/ivr/iv_hv args) constructs a one-row `scan_rows` list and reuses `compute_builds`/`apply_builds` unchanged — no new logging logic. This is what kills the manual-curl-bypass pattern from today's UUUU/NVDA entries.

### 2.6 Watchlist sync — deliberately *not* a Python module

`HUB_EXTENDED` sync is 65 `search_contracts` calls + one `edit_watchlist` call — all MCP, in-conversation. A subprocess can't reach MCP, so this can't be scripted. The right formalization is `contracts.resolve_underlying` (2.2 Part A): the LLM still drives the MCP calls, but the noisy-row selection (done by eye 20 times already this session) becomes one tested function call per ticker. **Reduce the manual step; don't fake-automate the transport.**

---

## 3. The dual-computation-path risk — concrete sync discipline

Once `sieves.py` encodes IVR≤45 etc. as code, `OPTIONS_SIEVE_SPEC.md` (prose) and `sieves.py` (code) become two descriptions of one logic — the exact disease the spec was built to cure between Radar and Scanner.

1. **Single source of truth for numbers = `sieves.py` constants.** The spec's tables become illustrative, with a one-line banner: *"Thresholds are defined authoritatively in `research/forward_test/sieves.py`. The tables below mirror those constants; on any change, edit the constant and this file in the same commit."*
2. **A `test_spec_sync.py` guard.** The spec gets one small machine-readable fenced block (e.g. YAML) of `{IVR_MAX: 45, IV_ANOMALY_MAX: 150, ...}`. The test imports `sieves.py`'s constants and asserts equality against that block — drift becomes a build failure, not a months-later discovery. (Parsing prose tables is too brittle; one explicit block is the KISS version.)
3. **Extend `OPTIONS_SIEVE_SPEC.md`'s existing Sync Discipline section** to name `sieves.py` as a third artifact alongside the two skills. One rule, four files.
4. **Radar/Scanner keep pointing at the spec, not the code** — the skills are read by the LLM in prose contexts, sometimes without repo access, so they defer to the human-readable spec, which the test keeps honest against the code. Code owns *values*; spec owns *readability and rationale*.

---

## 4. Migration / validation strategy

**Principle (GOLDEN_RULES "Never implement without validation"):** no new function is trusted in a live run until it reproduces a known-good value.

**Regression fixtures from today's real numbers:**

| Fixture | Value | Smoothing-sensitive? | Use |
|---|---|---|---|
| NVDA SMA200 | 192.58 | No | Exact-match |
| NVDA EMA9/21/50 | 205.37/204.71/204.56 (bullish stack) | Seeding-sensitive | Stack = BULLISH exact; values within tight tol |
| NVDA RSI14 | 56.0 | **Yes (Wilder vs flat)** | See caveat below |
| NVDA MACD hist | +0.788 | EMA-seeded | Sign + close tol |
| NVDA squeeze | NOT_FIRING | No | Exact-match (boolean) |
| NVDA 52w range | 58.7% | No | Exact-match |
| UUUU SMA200 | −33.45% below | No | Exact-match |
| UUUU RSI14 | 28.6 | **Yes** | See caveat |
| UUUU stack | bearish | Seeding-sensitive | Stack = BEARISH exact |
| UUUU squeeze | NOT_FIRING | No | Exact-match |

**Critical caveat on RSI/ATR fixtures — a real trap, not a footnote:** today's RSI14 values were computed with flat N-period averaging, not Wilder. If `technicals.py` implements true Wilder smoothing (recommended, §6), it will **not** reproduce 56.0/28.6 exactly — that's expected and correct. So: deterministic fixtures (SMA200, EMA stack direction, squeeze boolean, range%, MACD sign) are exact-match regression tests, validating the bulk of the vote logic. For RSI/ATR: recompute the golden value with the chosen Wilder implementation and pin *that* as the fixture; keep today's flat value only as a documented "old method, expected to differ by ~N points" cross-check. **Do not pin 56.0 as the Wilder target** — that bakes the inaccuracy being fixed into the test suite.

**Sieve validation:** build a `SieveInput` fixture set from today's CORE snapshots (including the AVGO missing-field case) and assert: AVGO → `UNSCREENABLE`, appears in the purge log; finalist set matches what was selected by eye; a fewer-than-3 case returns a short list, not a padded one.

**Contract-selection validation:** today's NVDA/UUUU manual picks (which did apply delta/OI/spread by hand) become the golden output for `select_contract` against the same chains.

**Payload validation:** every assembled payload passes `validate_payload` (reuse `test_centaur_contract.py`). Assert `iv_hv_ratio` is emitted in percentage form (guards the `hive_centaur_payload.json` 0.704 mistake from recurring).

---

## 5. Build sequencing

**Phase 1 — `technicals.py`, standalone, zero risk to live automation.** Highest fixture coverage, settles the Wilder decision, shared dependency for Phases 4–5. Build first.

**Phase 2 — `sieves.py`, standalone.** Pure, fixture-driven, no live dependency. Land `test_spec_sync.py` + the spec banner (§3) in the same change. Independent of Phase 1.

**Phase 3 — `contracts.py`.** Part A validated against a saved noisy `search_contracts` result; Part B against today's NVDA/UUUU manual picks. Depends on nothing above.

**Phase 4 — `centaur_payload.py`.** Depends on 1–3 + jsonschema validation. Validate by reproducing a corrected `hive_centaur_payload.json`.

**Phase 5 — extend `build_and_log.py` (last, most caution).** Only after 1 and 3 are proven standalone: swap `pick_atm_contract → contracts.select_contract` (+ `greeks:"true"`), delegate scoring to `technicals.score_direction`, add `--single`. **Regression-test via the dashboard's exact call surface** (`compute_builds`/`apply_builds`) — dry-run diff before/after. This is the only phase that can break something already working, so it goes last, behind a diff.

Phases 1–4 are independently shippable and independently useful in-conversation immediately. Phase 5 is the only one coupled to the live pipeline.

---

## 6. Risks and open questions

1. **Wilder smoothing — recommend FIX, eyes open.** Implement true Wilder for RSI14/ATR14 (industry standard; the skill already says "Wilder's RSI"). Today's flat-computed fixtures won't reproduce exactly — handled per §4. Also fix the skill's own ATR-as-plain-mean inconsistency (lines 278–279) in the same change, or the refactor creates a new drift instead of closing one.
2. **VIX regime — recommend NOT in `sieves.py`.** Standalone `classify_vix_regime(vix: float | None) -> Literal["STANDARD","HIGH-FEAR","UNKNOWN"]`, named thresholds, "UNKNOWN" on absent/failed VIX (never silently STANDARD). Lives in a small helper, not its own pipeline stage.
3. **Contract selection location — recommend `contracts.py`, not `build_and_log.py`.** Reusable beyond the batch CSV flow (the manual path needs it too); keeping it in `build_and_log.py` re-buries it where it can't be reused — which is how the manual/automated divergence happened in the first place.
4. **Gate C units doc conflict — must be resolved, not straddled.** `sieves.py` treats `avg_90d_usd_volume` as daily USD (the spec's resolution). Correct `ibkr-mcp-capabilities.md`'s stale "units need calibration" lines in the same change so the repo speaks with one voice.
5. **`score_direction` denominator bug — fold into the consolidation, don't ship separately.** Canonical `technicals.score_direction` fixes the latent MIXED-bias silently. Add a fixture with a `None`-valued signal to lock the denominator behavior.
6. **PATH B IVR provisionality must survive into code.** `provisional` on `SieveResult` is required, not optional — the guard against a future caller treating an MCP-percentile pass as a paste-verified rank (the AFRM 34-vs-18.3 divergence class of bug).
7. **Open — does `build_and_log.py`'s reduced 5-signal direction stay reduced?** Recommendation: keep the documented reduced set for the automated batch (its honesty about being reduced is a feature — avg-90d-P/C genuinely has no Tradier source), but share the same `score_direction` aggregator and indicator functions so future signal additions happen in one place, not two.
8. **Open — `greeks:"true"` cost/latency.** Confirm Tradier latency on wide chains is acceptable for the batch path before enabling it there; the one-off path is unaffected either way.

---

## 7. Explicit non-goals

Stay human/LLM judgment. No module in this plan formalizes these:

- **Interpretation Guardrails** (`FORWARD_TEST_PROTOCOL.md` MONITORING/EXPLORATORY/CONFIRMATORY states, the forking-paths log). Not code.
- **Watchlist *content*** — which tickers belong on CORE/EXTENDED. `contracts.resolve_underlying` syncs chosen tickers to IBKR; it never decides which tickers.
- **Earnings-date source reconciliation** when web searches conflict. `centaur_payload.py` accepts an earnings dict; never fetches, adjudicates, or fabricates a date.
- **`radar_notes` / the "one brutal sentence" synthesis** — passed in as a string, never generated.
- **Any live-capital / go-live sign-off.** No module touches order placement or promotes a paper result to a live decision.
- **VIX-regime as a *gate*** — it classifies and flags; the decision to stand down in HIGH-FEAR stays with the operator.

**The tell for "this belongs in non-goals":** if the step involves reconciling conflicting sources, deciding what belongs, synthesizing prose, or authorizing capital, it's judgment. If it's deterministic arithmetic or filtering over data already in hand, it's a module above.

---

## Critical files for implementation

- `research/forward_test/build_and_log.py`
- `OPTIONS_SIEVE_SPEC.md`
- `/Users/balajik/projects/options_iq_gemini/Docs/CENTAUR_SCHEMA_v2.json`
- `skill-options-directional-builder.md`
- `research/forward_test/dashboard/app.py`
