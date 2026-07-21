"""
Regression tests for contracts.py, using real search_contracts and Tradier
chain data pulled live on 2026-07-21 (Session 30) -- NVDA and UUUU's actual
option chains, where the manual picks that session applied the delta/OI/
spread filters this module now formalizes.
"""
import contracts as c

# --- Part A fixtures: a trimmed version of the real NVDA search_contracts
# result (the noisy rows -- leveraged ETFs, foreign listings -- that had to
# be filtered by eye that session). ---
NVDA_SEARCH_RESULTS = [
    {"underlying_contract_id": 4815747, "exchange": "NASDAQ", "symbol": "NVDA",
     "description": "NVIDIA CORP", "country_code": "US",
     "sections": [{"security_type": "STK"}, {"security_type": "OPT"}]},
    {"underlying_contract_id": 84223567, "exchange": "MEXI", "symbol": "NVDA",
     "description": "NVIDIA CORP", "country_code": "MX", "sections": [{"security_type": "STK"}]},
    {"underlying_contract_id": 541229759, "exchange": "TSE", "symbol": "NVDA",
     "description": "NVIDIA CORP-CDR", "country_code": "CA",
     "sections": [{"security_type": "STK"}, {"security_type": "OPT"}]},
    {"underlying_contract_id": 602261424, "exchange": "NASDAQ", "symbol": "NVDL",
     "description": "GRANITESH 2X LNG NVDA ETF", "country_code": "US",
     "sections": [{"security_type": "STK"}, {"security_type": "OPT"}]},
]


def test_resolve_underlying_picks_us_nasdaq_row():
    result = c.resolve_underlying(NVDA_SEARCH_RESULTS, "NVDA")
    assert result["underlying_contract_id"] == 4815747
    assert result["exchange"] == "NASDAQ"


def test_resolve_underlying_rejects_foreign_listings():
    """The Canadian CDR and Mexican listing both have symbol=='NVDA' too --
    country_code filtering must exclude them, not just prefer NASDAQ."""
    us_only = [r for r in NVDA_SEARCH_RESULTS if r["symbol"] == "NVDA"]
    result = c.resolve_underlying(us_only, "NVDA")
    assert result["country_code"] == "US"


def test_resolve_underlying_rejects_leveraged_etf_noise():
    """NVDL (2x leveraged NVDA ETF) has a different symbol and must never
    be selected even though it's obviously NVDA-related."""
    result = c.resolve_underlying(NVDA_SEARCH_RESULTS, "NVDA")
    assert result["symbol"] == "NVDA"
    assert result["symbol"] != "NVDL"


def test_resolve_underlying_none_when_no_us_match():
    foreign_only = [r for r in NVDA_SEARCH_RESULTS if r["country_code"] != "US"]
    assert c.resolve_underlying(foreign_only, "NVDA") is None


# --- Part B fixtures: real NVDA Aug 14 2026 call chain (Tradier, greeks=true) ---
NVDA_AUG14_CALLS = [
    {"option_type": "call", "strike": 190.0, "bid": 19.5, "ask": 19.85, "open_interest": 276,
     "greeks": {"delta": 0.7956}},
    {"option_type": "call", "strike": 195.0, "bid": 15.65, "ask": 15.95, "open_interest": 995,
     "greeks": {"delta": 0.7285}},
    {"option_type": "call", "strike": 200.0, "bid": 12.2, "ask": 12.45, "open_interest": 1290,
     "greeks": {"delta": 0.6441}},
    {"option_type": "call", "strike": 205.0, "bid": 9.25, "ask": 9.4, "open_interest": 2189,
     "greeks": {"delta": 0.548}},
    {"option_type": "call", "strike": 210.0, "bid": 6.7, "ask": 6.85, "open_interest": 3575,
     "greeks": {"delta": 0.449}},
    {"option_type": "call", "strike": 215.0, "bid": 4.7, "ask": 4.8, "open_interest": 3292,
     "greeks": {"delta": 0.3553}},
]

# UUUU Aug 14 2026 put chain (Tradier, greeks=true) -- deliberately thin/wide-spread
UUUU_AUG14_PUTS = [
    {"option_type": "put", "strike": 12.0, "bid": 0.79, "ask": 1.08, "open_interest": 83,
     "greeks": {"delta": -0.4513}},
    {"option_type": "put", "strike": 12.5, "bid": 1.07, "ask": 1.34, "open_interest": 62,
     "greeks": {"delta": -0.5265}},
    {"option_type": "put", "strike": 13.0, "bid": 1.3, "ask": 1.67, "open_interest": 233,
     "greeks": {"delta": -0.5992}},
]


def test_select_contract_nvda_matches_manual_pick():
    """The manual pick that session was strike 205, delta 0.548 -- best OI
    (2189) and tightest spread (1.6%) in the 0.45-0.60 band."""
    result = c.select_contract(NVDA_AUG14_CALLS, direction="BULLISH")
    assert result is not None
    assert result.contract["strike"] == 205.0
    assert result.contract["open_interest"] == 2189


def test_select_contract_excludes_out_of_band_deltas():
    """The 210 strike (delta 0.449) is just outside the 0.45 floor and must
    not be selected even though it has excellent OI (3575)."""
    result = c.select_contract(NVDA_AUG14_CALLS, direction="BULLISH")
    assert result.contract["strike"] != 210.0


def test_select_contract_returns_none_when_no_liquid_candidate_in_band():
    """UUUU's chain that session had 3 candidates in the delta band, but
    every one failed either the OI>=500 floor or the <10% spread ceiling
    (real, live outcome -- this is why UUUU wasn't a clean liquid pick).
    select_contract must return None (stand down), never relax a gate to
    force a selection."""
    result = c.select_contract(UUUU_AUG14_PUTS, direction="BEARISH")
    assert result is None


def test_select_contract_never_relaxes_gates_to_force_a_pick():
    result = c.select_contract(UUUU_AUG14_PUTS, direction="BEARISH", oi_min=500, max_spread_pct=0.10)
    assert result is None
    # confirm it's genuinely because nothing clears both floors, not a bug:
    best_oi = max(o["open_interest"] for o in UUUU_AUG14_PUTS)
    assert best_oi < 500


def test_select_contract_wrong_option_type_returns_none():
    result = c.select_contract(NVDA_AUG14_CALLS, direction="BEARISH")  # no puts in this fixture
    assert result is None


def test_select_contract_missing_delta_is_skipped_not_crashed():
    chain = [{"option_type": "call", "strike": 200.0, "bid": 5.0, "ask": 5.1,
              "open_interest": 1000, "greeks": {}}]  # delta missing
    result = c.select_contract(chain, direction="BULLISH")
    assert result is None
