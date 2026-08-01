"""
Tests for run_scan.py's build_scan_rows() -- the orchestrator function that
replaces what was, until Session 37, always done by hand: read a paste's Sieve
survivors/rejects off a printed result and re-type them into a small CSV for
build_and_log.py --input. These tests cover the classification logic (which
names become SURVIVOR-arm, REJECT-arm, or neither), not build_and_log.py's own
network calls, which are already covered by test_build_and_log.py.
"""
import sieves as s
from run_scan import build_scan_rows

PATH_A_HEADER = (
    "Instrument    Average Option Volume    Opt. Implied Volatility %    Implied Vol./Hist. Vol %    "
    "52 Week IV Rank    Market Cap    Put/Call Volume    Last    Change    Change %    Volume    "
    "Average Volume    P/E    Open    High    Low    52 Week High    52 Week Low    Bid Price    Ask Price\n"
)

PATH_B_HEADER = (
    "Instrument      Last     Change %     Bid     Ask     Volume     Opt. Imp. Vol. Change     "
    "Price/EMA(50)     Opt. Volume Change %     Put/Call Volume     52 Week Low     52 Week High     "
    "Price/EMA(200)     Opt. Volume     Option Open Interest     Hist. Vol. Close %     "
    "Opt. Implied Volatility %     Implied Vol./Hist. Vol %     52 Week IV Rank    Underlying Price\n"
)


def test_path_a_finalist_and_reject_and_purge_all_classified_correctly():
    # AVAV: clean finalist (IVR 40, IV/HV 72.8%, Gate A/C both clear).
    # XLF-like NEAR: passes every gate but IV/HV just over 100% -- REJECT arm.
    # GIL-like: fails Gate C liquidity -- neither arm, must not appear in scan_rows.
    # HOT: fails Sieve 1 (IVR > 45) -- neither arm either.
    text = PATH_A_HEADER + (
        "AVAV\nAEROVIRONMENT INC\n"
        "22.5K    72.4%    72.8%    40    7.821B    0.55    154.54    +0.30    0.19%    411K    1.65M        "
        "151.81    155.12    147.18    417.86    135.20    154.07    154.80\n"
        "ZNEAR\nNEAR MISS CO\n"
        "5.0K    36%    101.0%    36    9.0B    0.70    10.5    +0.1    1.0%    2.12M    12.82M    "
        "10.4    10.6    10.3    12.0    9.0    10.4    10.5\n"
        "GILLIQ\nTHIN LIQUIDITY CO\n"
        "3.2K    44.9%    75.6%    32    9.584B    0.60    51.64    +0.96    1.89%    228K    1.55M    21    "
        "51.40    51.82    50.89    73.38    45.42    51.62    51.67\n"
        "ZHOT\nHIGH IVR CO\n"
        "4.0K    60%    80.0%    60    5.0B    0.50    20.0    +0.1    0.5%    500K    5.0M        "
        "19.9    20.1    19.8    30.0    10.0    19.95    20.05\n"
    )
    scan_rows, fmt, vix, all_results = build_scan_rows(text)
    assert fmt == "PATH_A"
    assert len(all_results) == 4

    by_ticker = {r["ticker"]: r for r in scan_rows}
    assert by_ticker["AVAV"]["group"] == "SURVIVOR"
    assert by_ticker["AVAV"]["failed_gate"] == "NONE"
    assert by_ticker["ZNEAR"]["group"] == "REJECT"
    assert by_ticker["ZNEAR"]["failed_gate"] == "SIEVE2B_IVHV"
    assert by_ticker["ZNEAR"]["failed_value"] == "101.0"
    # GILLIQ fails Gate C, ZHOT fails Sieve 1 -- neither belongs to either arm
    assert "GILLIQ" not in by_ticker
    assert "ZHOT" not in by_ticker
    assert len(scan_rows) == 2


def test_path_b_curation_asserted_gates_never_produce_a_third_arm():
    """PATH B rows have no Market Cap/dollar-vol columns -- Gate A/C never fire,
    so every non-purged name lands in either SURVIVOR or REJECT, never silently
    dropped as some third, unhandled case."""
    text = PATH_B_HEADER + (
        "NFLX\nNETFLIX INC\n"
        "73.08    +3.81%    73.08    73.09    21.8M    -0.085    -5.47%    46.187%    0.30    "
        "65.08    126.71    -18.49%    274K    5.45M    51.724%    33.4%    64.6%    27    —\n"
        "ZFAR\nFAR MISS ETF\n"
        "48.36    -7.76%    48.34    48.35    57.4M    1.382    -15.05%    86.198%    0.27    "
        "26.14    81.32    —    385K    2.38M    115.857%    101.9%    136.6%    42    —\n"
    )
    scan_rows, fmt, vix, all_results = build_scan_rows(text)
    assert fmt == "PATH_B"
    by_ticker = {r["ticker"]: r for r in scan_rows}
    assert by_ticker["NFLX"]["group"] == "SURVIVOR"
    assert by_ticker["ZFAR"]["group"] == "REJECT"
    assert by_ticker["ZFAR"]["failed_value"] == "136.6"
    assert len(scan_rows) == 2  # both accounted for, no silent third bucket


def test_vix_row_extracted_never_appears_in_scan_rows():
    text = PATH_B_HEADER + (
        "NFLX\nNETFLIX INC\n"
        "73.08    +3.81%    73.08    73.09    21.8M    -0.085    -5.47%    46.187%    0.30    "
        "65.08    126.71    -18.49%    274K    5.45M    51.724%    33.4%    64.6%    27    —\n"
        "VIX\nCBOE Volatility Index\n"
        "18.04    -3.37%    —    —    —    -3.029    —    63.905%    1.45    "
        "13.38    35.30    —    561K    22.8M    124.226%    87%    70.0%    24    —\n"
    )
    scan_rows, fmt, vix, all_results = build_scan_rows(text)
    assert vix.level == 18.04
    assert vix.regime == "STANDARD"
    assert all(r["ticker"] != "VIX" for r in scan_rows)
    assert all(r.ticker != "VIX" for r in all_results)


def test_no_survivors_or_rejects_yields_empty_scan_rows():
    """A paste where every name fails Sieve 1 must yield an empty scan_rows,
    not an error -- 'zero candidates today' is a real, valid result."""
    text = PATH_A_HEADER + (
        "ALLHOT\nALL NAMES RUN HOT\n"
        "4.0K    60%    80.0%    60    5.0B    0.50    20.0    +0.1    0.5%    500K    5.0M        "
        "19.9    20.1    19.8    30.0    10.0    19.95    20.05\n"
    )
    scan_rows, fmt, vix, all_results = build_scan_rows(text)
    assert scan_rows == []
    assert len(all_results) == 1
    assert all_results[0].outcome == "PURGED_IVR"


def test_format_built_summary_has_no_bare_note_gap():
    """Regression test for the real gap found Session 37: build_position()'s
    BUILT branch sets no 'note' key at all, so the old print loop
    (result.get('note', '')) printed nothing for a position about to go live --
    forcing a separate ad hoc inspection script before trusting a build. This
    must never go bare again."""
    from run_scan import format_built_summary

    fake_built = {
        "ticker": "CAG", "direction": "BEARISH", "bull_n": 2, "bear_n": 3, "scored_n": 5,
        "direction_info": {"trend_200d": "DOWNTREND"},
        "strike": 15.5, "expiry": "2026-08-21", "dte": 24, "is_overshoot": False,
        "mid": 0.65, "bid": 0.6, "ask": 0.7, "target": 1.04, "stop": 0.455,
        "entry_greeks": {"delta": -0.4858, "gamma": 0.31353, "theta": -0.0088,
                         "vega": 0.0158, "mid_iv": 0.3329},
        "earnings": type("E", (), {"status": "CLEAR", "next_date": "2026-09-29"})(),
        "migration_note": None,
    }
    summary = format_built_summary(fake_built)
    assert summary != ""
    assert "BEARISH" in summary
    assert "3/5" in summary
    assert "DOWNTREND" in summary
    assert "15.5 Put" in summary
    assert "delta=-0.4858" in summary
    assert "CLEAR" in summary


def test_path_a_missing_market_cap_is_unscreenable_not_silently_passed():
    """Real gap found Session 37 while stress-testing run_scan.py: a PATH A row
    with a blank/dash Market Cap silently fell through Gate A as if it were PATH
    B's legitimate curation-asserted None -- letting a genuine data gap masquerade
    as a pre-cleared name. Must be UNSCREENABLE, excluded from both arms, and
    visible in the purge log -- never silently promoted to SURVIVOR/REJECT."""
    text = PATH_A_HEADER + (
        "ZCAP\nMICRO CO WITH NO CAP DATA\n"
        "6.0K    40%    80.0%    30    -    0.45    20.0    +0.1    0.5%    500K    12.0M        "
        "19.9    20.1    19.8    30.0    10.0    19.95    20.05\n"
    )
    scan_rows, fmt, vix, all_results = build_scan_rows(text)
    assert fmt == "PATH_A"
    assert len(all_results) == 1
    assert all_results[0].ticker == "ZCAP"
    assert all_results[0].outcome == "UNSCREENABLE"
    assert "market_cap_usd" in all_results[0].reason
    assert scan_rows == []  # never silently promoted


def test_path_a_missing_dollar_vol_is_also_unscreenable():
    """Same gap, the other trigger: PATH A's dollar_vol_usd is Last x Average
    Volume -- if either half fails to parse, it's None even on PATH A, and must
    get the same UNSCREENABLE treatment, not Gate C's PATH-B-only skip."""
    text = PATH_A_HEADER + (
        "ZVOL\nMICRO CO WITH NO VOLUME DATA\n"
        "6.0K    40%    80.0%    30    5.0B    0.45    20.0    +0.1    0.5%    500K    -        "
        "19.9    20.1    19.8    30.0    10.0    19.95    20.05\n"
    )
    scan_rows, fmt, vix, all_results = build_scan_rows(text)
    assert all_results[0].outcome == "UNSCREENABLE"
    assert "dollar_vol_usd" in all_results[0].reason
    assert scan_rows == []


def test_path_b_none_market_cap_and_dollar_vol_are_unaffected_by_the_path_a_check():
    """Contrast case: the exact same None values on a real PATH B row must NOT
    trigger the new UNSCREENABLE path -- that's the documented, intentional
    curation-asserted design, untouched by this fix."""
    text = PATH_B_HEADER + (
        "NFLX\nNETFLIX INC\n"
        "73.08    +3.81%    73.08    73.09    21.8M    -0.085    -5.47%    46.187%    0.30    "
        "65.08    126.71    -18.49%    274K    5.45M    51.724%    33.4%    64.6%    27    —\n"
    )
    scan_rows, fmt, vix, all_results = build_scan_rows(text)
    assert all_results[0].outcome == "FINALIST"
    assert by_ticker_group(scan_rows, "NFLX") == "SURVIVOR"


def by_ticker_group(scan_rows, ticker):
    return next(r["group"] for r in scan_rows if r["ticker"] == ticker)
