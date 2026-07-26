import pytest

from paste_parser import ParseError, parse_paste

PATH_A_HEADER = (
    "Instrument    Opt. Implied Volatility %    Implied Vol./Hist. Vol %    52 Week IV Rank    "
    "Market Cap    Last    Change    Change %    Volume    Average Volume    P/E    Open    High    "
    "Low    52 Week High    52 Week Low    Bid Price    Ask Price\n"
)

PATH_B_HEADER = (
    "Instrument      Last     Change %     Bid     Ask     Volume     Opt. Imp. Vol. Change     "
    "Price/EMA(50)     Opt. Volume Change %     Put/Call Volume     52 Week Low     52 Week High     "
    "Price/EMA(200)     Opt. Volume     Option Open Interest     Hist. Vol. Close %     "
    "Opt. Implied Volatility %     Implied Vol./Hist. Vol %     52 Week IV Rank    Underlying Price\n"
)


def test_path_a_row_with_pe():
    text = PATH_A_HEADER + (
        "SOLS\nSOLSTICE ADV MATERIALS INC\n"
        "62%    95.9%    33    9.724B    61.22    +0.34    0.56%    2.12M    2.82M    51.83    "
        "61.14    62.51    60.64    90.80    40.39    61.15    61.29\n"
    )
    fmt, rows, vix = parse_paste(text)
    assert fmt == "PATH_A"
    assert len(rows) == 1
    r = rows[0]
    assert r.ticker == "SOLS"
    assert r.ivr_52w == 33
    assert r.iv_hv_pct == pytest.approx(95.9)
    assert r.opt_implied_vol_pct == pytest.approx(62.0)
    assert r.market_cap_usd == pytest.approx(9.724e9)
    assert r.extra["pe"] == pytest.approx(51.83)
    assert r.dollar_vol_usd == pytest.approx(61.22 * 2.82e6)
    assert r.bid == pytest.approx(61.15)
    assert r.ask == pytest.approx(61.29)


def test_path_a_row_without_pe():
    text = PATH_A_HEADER + (
        "PRAX\nPRAXIS PRECISION MEDICINES I\n"
        "60.1%    87.3%    19    9.08B    325.68    +3.28    1.02%    109K    493K        "
        "322.39    327.50    314.62    366.52    37.19    324.81    326.54\n"
    )
    fmt, rows, vix = parse_paste(text)
    r = rows[0]
    assert r.ticker == "PRAX"
    assert r.extra["pe"] is None
    assert r.ivr_52w == 19
    assert r.extra["open"] == pytest.approx(322.39)
    assert r.ask == pytest.approx(326.54)


def test_path_a_multiple_rows_mixed_pe():
    text = PATH_A_HEADER + (
        "SOLS\nSOLSTICE ADV MATERIALS INC\n"
        "62%    95.9%    33    9.724B    61.22    +0.34    0.56%    2.12M    2.82M    51.83    "
        "61.14    62.51    60.64    90.80    40.39    61.15    61.29\n"
        "PRAX\nPRAXIS PRECISION MEDICINES I\n"
        "60.1%    87.3%    19    9.08B    325.68    +3.28    1.02%    109K    493K        "
        "322.39    327.50    314.62    366.52    37.19    324.81    326.54\n"
    )
    fmt, rows, vix = parse_paste(text)
    assert [r.ticker for r in rows] == ["SOLS", "PRAX"]


def test_path_b_normal_row():
    text = PATH_B_HEADER + (
        "CEG\nCONSTELLATION ENERGY\n"
        "279.20    +1.31%    279.11    279.43    706K    -0.657    4.76%    32.395%    0.48    "
        "228.63    411.70    -3.98%    3.53K    235K    40.280%    48.6%    120.8%    40    -\n"
    )
    fmt, rows, vix = parse_paste(text)
    assert fmt == "PATH_B"
    r = rows[0]
    assert r.ticker == "CEG"
    assert r.ivr_52w == 40
    assert r.iv_hv_pct == pytest.approx(120.8)
    assert r.opt_implied_vol_pct == pytest.approx(48.6)
    assert r.extra["underlying_price"] is None
    assert r.extra["put_call_volume"] == pytest.approx(0.48)
    assert r.market_cap_usd is None  # PATH B never carries this -- pre-satisfied by curation


def test_path_b_vix_row_pulled_out_not_left_as_a_candidate():
    text = PATH_B_HEADER + (
        "VIX\nCBOE Volatility Index\n"
        "17.45    -6.68%    -    -    -    -7.733    -    67.578%    0.54    13.38    35.30    -    "
        "547K    21.9M    124.453%    86.5%    69.5%    24    -\n"
    )
    fmt, rows, vix = parse_paste(text)
    assert rows == []  # VIX must never be left as a tradeable candidate for sieves.py
    assert vix.level == pytest.approx(17.45)
    assert vix.regime == "STANDARD"  # 17.45 <= 25


def test_path_b_vix_row_high_fear_regime():
    text = PATH_B_HEADER + (
        "VIX\nCBOE Volatility Index\n"
        "31.20    +12.4%    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -\n"
        "CEG\nCONSTELLATION ENERGY\n"
        "279.20    +1.31%    279.11    279.43    706K    -0.657    4.76%    32.395%    0.48    "
        "228.63    411.70    -3.98%    3.53K    235K    40.280%    48.6%    120.8%    40    -\n"
    )
    fmt, rows, vix = parse_paste(text)
    assert [r.ticker for r in rows] == ["CEG"]  # VIX excluded, real candidate kept
    assert vix.level == pytest.approx(31.20)
    assert vix.regime == "HIGH-FEAR"  # 31.20 > 25


def test_no_vix_row_present_yields_none_not_a_guess():
    text = PATH_B_HEADER + (
        "CEG\nCONSTELLATION ENERGY\n"
        "279.20    +1.31%    279.11    279.43    706K    -0.657    4.76%    32.395%    0.48    "
        "228.63    411.70    -3.98%    3.53K    235K    40.280%    48.6%    120.8%    40    -\n"
    )
    fmt, rows, vix = parse_paste(text)
    assert vix is None


def test_two_vix_rows_raises_ambiguous():
    text = PATH_B_HEADER + (
        "VIX\nCBOE Volatility Index\n"
        "17.45    -6.68%    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -\n"
        "VIX\nCBOE Volatility Index (duplicate)\n"
        "18.00    -6.68%    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -\n"
    )
    with pytest.raises(ParseError, match="found 2 VIX rows"):
        parse_paste(text)


def test_path_b_real_em_dash_placeholder_not_ascii_hyphen():
    # Regression test for a real Pass-2 finding: IBKR's actual paste uses an EM DASH
    # (U+2014, "—") for missing cells, not the plain ASCII hyphen "-" (U+002D)
    # every other fixture in this file uses for convenience. The original _num()
    # only recognized the ASCII character, so it would have raised ParseError on
    # every real PATH B row with a blank cell (e.g. "Underlying Price", blank on
    # every real row observed this session) instead of returning None.
    dash = "—"  # EM DASH -- deliberately not typed as a literal "—" glyph in source,
    # so a future editor normalizing "weird" Unicode in this file can't silently undo the point.
    text = PATH_B_HEADER + (
        f"DRAM\nROUNDHILL MEMORY ETF\n"
        f"55.18    -5.35%    55.17    55.19    44.1M    -3.950    -4.12%    39.379%    0.60    "
        f"26.14    81.32    {dash}    181K    2.50M    115.270%    98.7%    85.7%    39    {dash}\n"
    )
    fmt, rows, vix = parse_paste(text)
    r = rows[0]
    assert r.ticker == "DRAM"
    assert r.extra["price_ema200_pct"] is None  # the em-dash cell
    assert r.extra["underlying_price"] is None  # the em-dash cell
    assert r.ivr_52w == 39  # a real value on the same row parsed fine either way


def test_split_triples_raises_clear_error_on_malformed_missing_data_line():
    # Two ticker-shaped lines back to back with no data line for the first --
    # simulates a paste that lost a row's data during copy. Should raise a specific,
    # immediate error rather than cascading into a confusing field-count mismatch
    # several calls downstream (the failure mode before this Pass-2 fix).
    text = PATH_A_HEADER + "SOLS\nCIB\nGRUPO CIBEST SA-ADR\n"
    with pytest.raises(ParseError, match="expected a data line"):
        parse_paste(text)


def test_ambiguous_format_raises():
    # Neither format's markers present
    text = "Instrument   Last   Bid   Ask\nAAPL\nApple Inc\n100  99  101\n"
    with pytest.raises(ParseError, match="could not confidently detect"):
        parse_paste(text)


def test_wrong_field_count_raises():
    text = PATH_A_HEADER + "SOLS\nSOLSTICE ADV MATERIALS INC\n62%    95.9%    33\n"
    with pytest.raises(ParseError, match="expected 16.*or 17"):
        parse_paste(text)


def test_wrong_field_count_raises_path_b():
    text = PATH_B_HEADER + "CEG\nCONSTELLATION ENERGY\n279.20    +1.31%    279.11\n"
    with pytest.raises(ParseError, match="expected 19"):
        parse_paste(text)


def test_expected_format_mismatch_raises():
    text = PATH_A_HEADER + (
        "SOLS\nSOLSTICE ADV MATERIALS INC\n"
        "62%    95.9%    33    9.724B    61.22    +0.34    0.56%    2.12M    2.82M    51.83    "
        "61.14    62.51    60.64    90.80    40.39    61.15    61.29\n"
    )
    with pytest.raises(ParseError, match="expected PATH_B but"):
        parse_paste(text, expected_format="PATH_B")


def test_truncated_paste_raises():
    text = PATH_A_HEADER + "SOLS\nSOLSTICE ADV MATERIALS INC\n"
    with pytest.raises(ParseError, match="truncated"):
        parse_paste(text)


def test_no_rows_at_all_raises():
    with pytest.raises(ParseError, match="no \\(TICKER"):
        parse_paste(PATH_A_HEADER)


def test_ui_chrome_lines_skipped_not_consumed():
    text = (
        "HUB_EXTENDEDHUB_CORE Options_Scanner_WS AI Supply Chain ETF Space More All My Lists\n"
        "65 Symbols | Last Modified Jul 22, 2026\n"
        + PATH_B_HEADER +
        "CEG\nCONSTELLATION ENERGY\n"
        "279.20    +1.31%    279.11    279.43    706K    -0.657    4.76%    32.395%    0.48    "
        "228.63    411.70    -3.98%    3.53K    235K    40.280%    48.6%    120.8%    40    -\n"
        "Generated at 12:59:31 PM EDT\n"
        " | \n | \n | \n | \n"
    )
    fmt, rows, vix = parse_paste(text)
    assert len(rows) == 1
    assert rows[0].ticker == "CEG"
