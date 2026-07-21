"""
Regression tests for sieves.py, using the real 20-ticker CORE watchlist scan
run live via IBKR MCP on 2026-07-21 (Session 30) -- including AVGO's actual
missing-implied_vol_underlying case, and confirming the same single survivor
(NVDA) that was found by eye that session.
"""
import sieves as s

# ticker -> (ivr_52w_pct, iv_annual_pct, hv_30d_pct, dollar_vol_usd)
# Values as read from get_price_snapshot on 2026-07-21. AVGO's iv_annual_pct
# is None because implied_vol_underlying was entirely absent from its
# snapshot response -- a real, live MCP_DATA_UNAVAILABLE case, not a
# synthetic one.
CORE_SCAN_2026_07_21 = {
    "NVDA": (40.64, 38.15, 39.64, 32_460_149_549),
    "AMD": (98.80, 85.99, 87.40, 19_027_050_999),
    "MU": (92.43, 100.78, 119.86, 50_055_059_733),
    "MRVL": (84.86, 90.02, 113.13, 8_859_261_129),
    "AVGO": (74.90, None, 55.76, 10_147_501_685),  # implied_vol_underlying missing
    "GEV": (98.01, 67.88, 66.31, 3_119_927_201),
    "VRT": (97.61, 82.35, 78.12, 1_855_775_039),
    "PWR": (99.60, 58.00, 45.60, 812_831_153),
    "ALB": (52.59, 61.62, 54.84, 264_369_333),
    "HIVE": (60.16, 119.25, 114.42, 88_197_726),  # dollar vol also sub-$100M, purged on IVR first
    "MARA": (90.44, 98.82, 105.14, 542_443_685),
    "RIOT": (95.22, 101.34, 94.22, 363_719_039),
    "COIN": (94.82, 77.78, 73.38, 1_546_521_694),
    "MSTR": (89.24, 83.58, 92.94, 2_101_772_712),
    "PLTR": (94.82, 67.43, 58.13, 5_647_280_942),
    "CRWD": (96.02, 62.59, 56.50, 849_624_768),
    "BABA": (78.88, 47.42, 48.01, 1_487_960_063),
    "PDD": (57.77, 37.84, 33.02, 759_086_707),
    "PYPL": (51.79, 38.43, 55.80, 955_292_790),
    "TSLA": (72.11, 48.63, 48.72, 18_620_897_735),
}


def _build_inputs():
    return [
        s.SieveInput(
            ticker=ticker, ivr_52w=ivr, ivr_source="mcp_percentile",
            iv_annual_pct=iv, hv_30d_pct=hv, dollar_vol_usd=dv,
        )
        for ticker, (ivr, iv, hv, dv) in CORE_SCAN_2026_07_21.items()
    ]


def test_nvda_is_sole_finalist():
    finalists, all_results = s.run_sieve_stack(_build_inputs())
    assert [f.ticker for f in finalists] == ["NVDA"]


def test_finalist_promotion_reflects_in_all_results_too():
    """finalists and all_results share the same SieveResult objects (not
    copies) -- promoting NVDA to outcome='FINALIST' must be visible via
    all_results as well, not just the finalists list, or a caller building
    a PURGE LOG from all_results alone would show it as a plain SURVIVOR."""
    finalists, all_results = s.run_sieve_stack(_build_inputs())
    nvda_in_all_results = next(r for r in all_results if r.ticker == "NVDA")
    assert nvda_in_all_results.outcome == "FINALIST"
    assert nvda_in_all_results is finalists[0]  # genuinely the same object, not an equal copy


def test_nvda_iv_hv_matches_session30():
    finalists, _ = s.run_sieve_stack(_build_inputs())
    nvda = finalists[0]
    assert round(nvda.iv_hv_pct, 1) == 96.2  # 38.15/39.64*100, matches the live CENTAUR payload sent that session


def test_avgo_is_unscreenable_not_silently_dropped():
    """The AVGO case: implied_vol_underlying was absent from its live
    snapshot. Must appear as UNSCREENABLE in the full results (visible in
    the purge log), never silently omitted and never defaulted to a passing
    value (GOLDEN_RULES: return null, not a plausible fake)."""
    _, all_results = s.run_sieve_stack(_build_inputs())
    avgo = next(r for r in all_results if r.ticker == "AVGO")
    assert avgo.outcome == "UNSCREENABLE"
    assert avgo.iv_hv_pct is None
    assert "implied_vol_underlying" in avgo.reason or "iv_annual_pct" in avgo.reason


def test_19_of_20_purged_on_ivr():
    _, all_results = s.run_sieve_stack(_build_inputs())
    purged = [r for r in all_results if r.outcome == "PURGED_IVR"]
    assert len(purged) == 18  # 20 total - 1 NVDA finalist - 1 AVGO unscreenable


def test_all_20_tickers_accounted_for():
    _, all_results = s.run_sieve_stack(_build_inputs())
    assert len(all_results) == 20
    assert {r.ticker for r in all_results} == set(CORE_SCAN_2026_07_21.keys())


def test_fewer_than_three_finalists_is_not_padded():
    finalists, _ = s.run_sieve_stack(_build_inputs())
    assert len(finalists) == 1
    assert len(finalists) < s.FINALIST_COUNT


def test_cheap_ivr_trap_fires_correctly():
    assert s.cheap_ivr_trap(ivr=10, iv_hv_pct=165) is True  # WBD canonical example
    assert s.cheap_ivr_trap(ivr=40.64, iv_hv_pct=96.2) is False  # NVDA doesn't trip it
    assert s.cheap_ivr_trap(ivr=None, iv_hv_pct=None) is False  # never fabricate a trap on missing data


def test_missing_dollar_vol_is_unscreenable_not_a_silent_gate_c_skip():
    """dollar_vol_usd is NOT curation-asserted the way market_cap_usd can be
    (OPTIONS_SIEVE_SPEC.md: Gate C is pulled live from MCP on PATH B, a real
    per-run check). Before this fix, a missing dollar_vol_usd silently
    skipped Gate C entirely and let the name through as a SURVIVOR --
    exactly the class of bug GOLDEN_RULES' 'return null, not a plausible
    fake' rule targets. Found on a third, more stringent re-verification
    pass; no real fixture from today's CORE scan happened to be missing
    this specific field (only AVGO's IV field was missing), so the earlier
    passes never exercised this path."""
    item = s.SieveInput(ticker="GAPDATA", ivr_52w=20.0, ivr_source="mcp_percentile",
                        iv_annual_pct=50.0, hv_30d_pct=60.0, dollar_vol_usd=None)
    finalists, all_results = s.run_sieve_stack([item])
    assert all_results[0].outcome == "UNSCREENABLE"
    assert "dollar_vol_usd" in all_results[0].reason
    assert all_results[0] not in finalists


def test_missing_market_cap_is_fine_curation_asserted_not_unscreenable():
    """Contrast case: market_cap_usd=None is the documented, intentional
    PATH B behavior (curation already asserts >$1B) -- must NOT be treated
    the same as the dollar_vol_usd gap above."""
    item = s.SieveInput(ticker="CURATED", ivr_52w=20.0, ivr_source="mcp_percentile",
                        iv_annual_pct=50.0, hv_30d_pct=60.0, dollar_vol_usd=200_000_000,
                        market_cap_usd=None)
    finalists, all_results = s.run_sieve_stack([item])
    assert all_results[0].outcome != "UNSCREENABLE"
    assert all_results[0].outcome in ("SURVIVOR", "FINALIST")


def test_gate_a_market_cap_purge():
    item = s.SieveInput(ticker="MICROCAP", ivr_52w=20.0, ivr_source="paste_rank",
                        iv_annual_pct=50.0, hv_30d_pct=60.0, dollar_vol_usd=200_000_000,
                        market_cap_usd=500_000_000)
    finalists, all_results = s.run_sieve_stack([item])
    assert all_results[0].outcome == "ELIM_GATE_A"


def test_gate_b_iv_anomaly_purge():
    item = s.SieveInput(ticker="DISTRESSED", ivr_52w=20.0, ivr_source="paste_rank",
                        iv_annual_pct=180.0, hv_30d_pct=60.0, dollar_vol_usd=200_000_000)
    finalists, all_results = s.run_sieve_stack([item])
    assert all_results[0].outcome == "ELIM_GATE_B"


def test_gate_c_liquidity_purge():
    item = s.SieveInput(ticker="THIN", ivr_52w=20.0, ivr_source="paste_rank",
                        iv_annual_pct=50.0, hv_30d_pct=60.0, dollar_vol_usd=50_000_000)
    finalists, all_results = s.run_sieve_stack([item])
    assert all_results[0].outcome == "ELIM_GATE_C"


def test_finalist_ranked_ascending_by_iv_hv():
    items = [
        s.SieveInput(ticker="A", ivr_52w=20.0, ivr_source="paste_rank",
                    iv_annual_pct=90.0, hv_30d_pct=100.0, dollar_vol_usd=200_000_000),  # IV/HV 90
        s.SieveInput(ticker="B", ivr_52w=20.0, ivr_source="paste_rank",
                    iv_annual_pct=70.0, hv_30d_pct=100.0, dollar_vol_usd=200_000_000),  # IV/HV 70
        s.SieveInput(ticker="C", ivr_52w=20.0, ivr_source="paste_rank",
                    iv_annual_pct=95.0, hv_30d_pct=100.0, dollar_vol_usd=200_000_000),  # IV/HV 95
    ]
    finalists, _ = s.run_sieve_stack(items)
    assert [f.ticker for f in finalists] == ["B", "A", "C"]


def test_boundary_ivr_exactly_at_max_passes():
    """IVR_MAX=45.0. Spec: 'IVR > 45 -> PURGE', so exactly 45.0 must SURVIVE
    (strict greater-than, not >=). The off-by-one line every threshold hides
    behind -- worth testing explicitly, not inferring from nearby values."""
    item = s.SieveInput(ticker="X", ivr_52w=45.0, ivr_source="paste_rank",
                        iv_annual_pct=50.0, hv_30d_pct=60.0, dollar_vol_usd=200_000_000)
    _, results = s.run_sieve_stack([item])
    assert results[0].outcome != "PURGED_IVR"


def test_boundary_ivr_just_over_max_purges():
    item = s.SieveInput(ticker="X", ivr_52w=45.01, ivr_source="paste_rank",
                        iv_annual_pct=50.0, hv_30d_pct=60.0, dollar_vol_usd=200_000_000)
    _, results = s.run_sieve_stack([item])
    assert results[0].outcome == "PURGED_IVR"


def test_boundary_iv_anomaly_exactly_at_max_passes():
    """IV_ANOMALY_MAX=150.0. 'IV > 150 -> ELIMINATE' -- exactly 150.0 survives."""
    item = s.SieveInput(ticker="X", ivr_52w=20.0, ivr_source="paste_rank",
                        iv_annual_pct=150.0, hv_30d_pct=60.0, dollar_vol_usd=200_000_000)
    _, results = s.run_sieve_stack([item])
    assert results[0].outcome != "ELIM_GATE_B"


def test_boundary_iv_anomaly_just_over_max_eliminates():
    item = s.SieveInput(ticker="X", ivr_52w=20.0, ivr_source="paste_rank",
                        iv_annual_pct=150.01, hv_30d_pct=60.0, dollar_vol_usd=200_000_000)
    _, results = s.run_sieve_stack([item])
    assert results[0].outcome == "ELIM_GATE_B"


def test_boundary_dollar_vol_exactly_at_floor_passes():
    """DOLLAR_VOL_FLOOR=$100M. 'dollar vol < $100M -> eliminate' -- exactly
    $100M survives (not a strict inequality trap in the other direction)."""
    item = s.SieveInput(ticker="X", ivr_52w=20.0, ivr_source="paste_rank",
                        iv_annual_pct=50.0, hv_30d_pct=60.0, dollar_vol_usd=100_000_000)
    _, results = s.run_sieve_stack([item])
    assert results[0].outcome != "ELIM_GATE_C"


def test_boundary_dollar_vol_one_dollar_under_floor_eliminates():
    item = s.SieveInput(ticker="X", ivr_52w=20.0, ivr_source="paste_rank",
                        iv_annual_pct=50.0, hv_30d_pct=60.0, dollar_vol_usd=99_999_999)
    _, results = s.run_sieve_stack([item])
    assert results[0].outcome == "ELIM_GATE_C"


def test_boundary_market_cap_exactly_at_floor_passes():
    item = s.SieveInput(ticker="X", ivr_52w=20.0, ivr_source="paste_rank",
                        iv_annual_pct=50.0, hv_30d_pct=60.0, dollar_vol_usd=200_000_000,
                        market_cap_usd=1_000_000_000)
    _, results = s.run_sieve_stack([item])
    assert results[0].outcome != "ELIM_GATE_A"


def test_boundary_iv_hv_exactly_100_does_not_qualify_as_finalist():
    """IVHV_FINALIST_MAX=100.0. Spec: 'All 3 finalists must have IV/HV < 100%'
    -- strict less-than, so a name landing exactly on 100.0 must NOT qualify,
    even though it isn't eliminated by any purge gate (it's a SURVIVOR, just
    not a FINALIST). This is the boundary this whole forward test's edge
    hypothesis hinges on -- worth being exactly right, not approximately."""
    item = s.SieveInput(ticker="X", ivr_52w=20.0, ivr_source="paste_rank",
                        iv_annual_pct=100.0, hv_30d_pct=100.0, dollar_vol_usd=200_000_000)
    finalists, results = s.run_sieve_stack([item])
    assert results[0].iv_hv_pct == 100.0
    assert results[0].outcome == "SURVIVOR"  # not FINALIST
    assert finalists == []


def test_boundary_iv_hv_just_under_100_qualifies():
    item = s.SieveInput(ticker="X", ivr_52w=20.0, ivr_source="paste_rank",
                        iv_annual_pct=99.99, hv_30d_pct=100.0, dollar_vol_usd=200_000_000)
    finalists, results = s.run_sieve_stack([item])
    assert len(finalists) == 1
    assert finalists[0].outcome == "FINALIST"


def test_boundary_cheap_ivr_trap_exactly_at_thresholds_does_not_fire():
    """TRAP_IVR_MAX=20.0, TRAP_IVHV_MIN=120.0. Both are strict inequalities
    (< 20, > 120) -- exactly on either line must NOT trip the trap."""
    assert s.cheap_ivr_trap(ivr=20.0, iv_hv_pct=165.0) is False  # ivr not < 20
    assert s.cheap_ivr_trap(ivr=10.0, iv_hv_pct=120.0) is False  # iv_hv not > 120
    assert s.cheap_ivr_trap(ivr=19.99, iv_hv_pct=120.01) is True  # just past both


def test_provisional_flag_travels_with_mcp_percentile_source():
    """PATH B (MCP percentile) passes must carry provisional=True; PATH A
    (pasted watchlist Rank) passes must not -- guards the AFRM
    Rank-34-vs-percentile-18.3 class of confidence-mislabeling bug."""
    mcp_item = s.SieveInput(ticker="X", ivr_52w=20.0, ivr_source="mcp_percentile",
                            iv_annual_pct=50.0, hv_30d_pct=60.0, dollar_vol_usd=200_000_000)
    paste_item = s.SieveInput(ticker="Y", ivr_52w=20.0, ivr_source="paste_rank",
                              iv_annual_pct=50.0, hv_30d_pct=60.0, dollar_vol_usd=200_000_000)
    _, results = s.run_sieve_stack([mcp_item, paste_item])
    assert next(r for r in results if r.ticker == "X").provisional is True
    assert next(r for r in results if r.ticker == "Y").provisional is False
