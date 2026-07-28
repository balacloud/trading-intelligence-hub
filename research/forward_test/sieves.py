"""
The executable form of OPTIONS_SIEVE_SPEC.md -- Sieve 1, Gates A/B/C, Sieve 2b,
and the Cheap IVR Trap, as pure functions over already-fetched IBKR snapshot
data. See PLAN_deterministic_pipeline_formalization.md Section 2.1.

These functions never fetch data themselves -- they cannot, since IBKR MCP
access only exists inside a live Claude conversation, never in a subprocess
(see build_and_log.py's own docstring). The caller (an LLM with live MCP
access) hands in already-fetched SieveInput rows.

Sync discipline (Plan Section 3): the numeric constants below are the
authoritative source of truth. OPTIONS_SIEVE_SPEC.md's tables mirror these
values for human readability -- on any change, edit the constant here AND
that spec in the same commit. See test_spec_sync.py, which fails the build
if the two ever diverge.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import paste_parser as pp

# --- Sync block for test_spec_sync.py -- keep in lockstep with
# --- OPTIONS_SIEVE_SPEC.md's own copy of these numbers. ---
IVR_MAX = 45.0  # Sieve 1 -- IV above 52w median = the Volatility Tax
IV_ANOMALY_MAX = 150.0  # Gate B -- distressed/event-driven IV anomaly
DOLLAR_VOL_FLOOR = 100_000_000  # Gate C -- daily USD volume floor (confirmed a genuine
# daily average, not a 90-day total -- OPTIONS_SIEVE_SPEC.md Sieve 1.5, resolved twice live)
MARKET_CAP_FLOOR = 1_000_000_000  # Gate A -- micro-cap purge
IVHV_FINALIST_MAX = 100.0  # Sieve 2b -- all finalists must clear IV/HV < 100%
TRAP_IVR_MAX = 20.0  # Cheap IVR Trap
TRAP_IVHV_MIN = 120.0  # Cheap IVR Trap
FINALIST_COUNT = 3


IvrSource = Literal["paste_rank", "mcp_percentile"]
Outcome = Literal[
    "FINALIST", "SURVIVOR", "PURGED_IVR", "ELIM_GATE_B", "ELIM_GATE_C", "ELIM_GATE_A", "UNSCREENABLE"
]


@dataclass
class SieveInput:
    ticker: str
    ivr_52w: float | None  # already a percentage-style number, e.g. 40.64
    ivr_source: IvrSource
    iv_annual_pct: float | None
    hv_30d_pct: float | None
    dollar_vol_usd: float | None
    market_cap_usd: float | None = None  # often None on PATH B; curation-asserted instead


@dataclass
class SieveResult:
    ticker: str
    outcome: Outcome
    ivr_52w: float | None
    iv_hv_pct: float | None
    ivr_gate: Literal["PASS", "FLAG_VOLATILITY_TAX"] | None
    trap_flag: bool
    reason: str
    provisional: bool  # True when ivr_source == "mcp_percentile" -- a PATH B pass
    # near the threshold is provisional, never confirmed the way a PATH A paste-Rank pass is.


def compute_iv_hv(item: SieveInput) -> float | None:
    """iv_annual / hv_30d * 100. None if either input is missing -- never a
    fabricated ratio (GOLDEN_RULES: return null, not a plausible fake)."""
    if item.iv_annual_pct is None or item.hv_30d_pct is None or item.hv_30d_pct == 0:
        return None
    return item.iv_annual_pct / item.hv_30d_pct * 100


def cheap_ivr_trap(ivr: float | None, iv_hv_pct: float | None) -> bool:
    if ivr is None or iv_hv_pct is None:
        return False
    return ivr < TRAP_IVR_MAX and iv_hv_pct > TRAP_IVHV_MIN


def _evaluate_one(item: SieveInput) -> SieveResult:
    provisional = item.ivr_source == "mcp_percentile"

    if item.ivr_52w is None:
        return SieveResult(item.ticker, "UNSCREENABLE", None, None, None, False,
                            "ivr_52w missing -- Sieve 1 cannot run", provisional)

    iv_hv = compute_iv_hv(item)
    if iv_hv is None:
        return SieveResult(item.ticker, "UNSCREENABLE", item.ivr_52w, None, None, False,
                            "iv_annual_pct or hv_30d_pct missing from snapshot -- cannot compute IV/HV",
                            provisional)

    trap = cheap_ivr_trap(item.ivr_52w, iv_hv)

    if item.ivr_52w > IVR_MAX:
        return SieveResult(item.ticker, "PURGED_IVR", item.ivr_52w, iv_hv, "FLAG_VOLATILITY_TAX", trap,
                            f"IVR {item.ivr_52w:.1f}% > {IVR_MAX}% ceiling (Sieve 1)", provisional)

    # Corrected Session 36 (Jul 27 2026): dollar_vol_usd=None IS curation-asserted on
    # PATH B, the same way market_cap_usd=None already is -- paste_parser.py always sets
    # both to None for PATH B rows (no Market Cap or dollar-volume column exists in that
    # paste format), and skill-options-scanner.md's own operative text says so explicitly:
    # "Gate C -- Liquidity floor: Pre-satisfied by watchlist curation (dollar volume) --
    # no column required" -- part of the skill's stated "0 MCP calls for screening" design.
    # The prior stricter behavior (UNSCREENABLE on a missing value) was written the same
    # session as the v3.0 paste conversion but never reconciled against it -- as written,
    # it made every real PATH B row UNSCREENABLE, permanently, since dollar_vol_usd is
    # never populated on that path. Found by actually running this module against a real
    # PATH B paste for the first time. On PATH A, dollar_vol_usd is always a real
    # screen-computed number (Last x Average_Volume), so this never masks a genuine gap
    # there -- only a PATH B row (dollar_vol_usd=None by construction) skips the check.
    if item.market_cap_usd is not None and item.market_cap_usd < MARKET_CAP_FLOOR:
        return SieveResult(item.ticker, "ELIM_GATE_A", item.ivr_52w, iv_hv, "PASS", trap,
                            f"market cap ${item.market_cap_usd/1e9:.2f}B < $1B floor (Gate A)", provisional)

    if item.iv_annual_pct is not None and item.iv_annual_pct > IV_ANOMALY_MAX:
        return SieveResult(item.ticker, "ELIM_GATE_B", item.ivr_52w, iv_hv, "PASS", trap,
                            f"IV {item.iv_annual_pct:.1f}% > {IV_ANOMALY_MAX}% anomaly ceiling (Gate B)", provisional)

    # dollar_vol_usd is None on PATH B by construction (curation-asserted, like
    # market_cap_usd) -- only evaluate Gate C when a real PATH A screen-computed value
    # is actually present.
    if item.dollar_vol_usd is not None and item.dollar_vol_usd < DOLLAR_VOL_FLOOR:
        return SieveResult(item.ticker, "ELIM_GATE_C", item.ivr_52w, iv_hv, "PASS", trap,
                            f"dollar vol ${item.dollar_vol_usd/1e6:.1f}M/day < $100M floor (Gate C)", provisional)

    # Passed Sieve 1 + Gates A/B/C. SURVIVOR unless it also clears the
    # < 100% finalist bar -- that promotion happens in run_sieve_stack,
    # since it's a ranking decision across all survivors, not a per-name one.
    return SieveResult(item.ticker, "SURVIVOR", item.ivr_52w, iv_hv, "PASS", trap,
                        f"IVR {item.ivr_52w:.1f}% (Sieve 1 pass), IV/HV {iv_hv:.1f}%", provisional)


def sieve_input_from_paste_row(row: pp.PasteRow, ivr_source: IvrSource = "paste_rank") -> SieveInput:
    """Builds a SieveInput straight from a parsed PasteRow -- the hand-off that, until
    now, was always done manually (read the paste's IVR/IV/HV columns off the screen,
    re-type them into a SieveInput or a build_and_log.py --input CSV). That manual
    re-typing is exactly the error-prone step this function exists to remove.

    Both PATH A and PATH B pastes report IV/HV as a single pre-computed ratio
    (`iv_hv_pct`) rather than separate IV-annual/HV-30d figures -- unlike a live MCP
    pull (test_sieves.py's CORE_SCAN_2026_07_21), which has independent numbers for
    both. compute_iv_hv() always recomputes the ratio from iv_annual_pct/hv_30d_pct,
    so hv_30d_pct here is back-solved (opt_implied_vol_pct / iv_hv_pct * 100) to
    reproduce IBKR's own displayed ratio exactly. This isn't a fabricated number --
    both operands are already real, live IBKR figures off the same paste row; the
    back-solve just re-expresses their existing ratio in the shape SieveInput expects.
    A row missing either figure yields hv_30d_pct=None, which compute_iv_hv() already
    turns into a real UNSCREENABLE outcome downstream -- never a fabricated ratio.
    """
    hv_30d_pct = None
    if row.opt_implied_vol_pct is not None and row.iv_hv_pct:
        hv_30d_pct = row.opt_implied_vol_pct / row.iv_hv_pct * 100
    return SieveInput(
        ticker=row.ticker, ivr_52w=row.ivr_52w, ivr_source=ivr_source,
        iv_annual_pct=row.opt_implied_vol_pct, hv_30d_pct=hv_30d_pct,
        dollar_vol_usd=row.dollar_vol_usd, market_cap_usd=row.market_cap_usd,
    )


def run_sieve_stack(items: list[SieveInput]) -> tuple[list[SieveResult], list[SieveResult]]:
    """Runs the full stack over every input. Returns (finalists, all_results).

    finalists: up to FINALIST_COUNT survivors, ranked ascending by IV/HV,
    every one strictly < IVHV_FINALIST_MAX. Fewer than FINALIST_COUNT is a
    valid, first-class result -- never padded with a neutral/seller-edge name.

    all_results: every input's SieveResult, in input order -- this is what
    drives the PURGE LOG (including UNSCREENABLE entries like AVGO's missing
    implied_vol_underlying case, which must be visible, never silently
    dropped).
    """
    all_results = [_evaluate_one(item) for item in items]

    survivors = [r for r in all_results if r.outcome == "SURVIVOR" and r.iv_hv_pct is not None
                 and r.iv_hv_pct < IVHV_FINALIST_MAX]
    survivors.sort(key=lambda r: r.iv_hv_pct)
    finalists = survivors[:FINALIST_COUNT]

    for f in finalists:
        f.outcome = "FINALIST"

    return finalists, all_results
