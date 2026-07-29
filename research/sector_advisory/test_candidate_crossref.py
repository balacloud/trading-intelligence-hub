from candidate_crossref import crossref_open_positions, load_open_rows, parse_direction


def test_parse_direction_extracts_bullish():
    notes = "Built via build_and_log.py. Direction=BULLISH 3/4 scored (YTD 83.5%, ...)"
    assert parse_direction(notes) == "BULLISH"


def test_parse_direction_extracts_bearish():
    notes = "Built via build_and_log.py. Direction=BEARISH 4/5 scored, trend=DOWNTREND"
    assert parse_direction(notes) == "BEARISH"


def test_parse_direction_none_when_absent():
    assert parse_direction("TBLA earnings gate: earnings 2026-08-03 inside window") is None
    assert parse_direction("") is None
    assert parse_direction(None) is None


def test_load_open_rows_excludes_non_open_and_no_contract_rows(tmp_path):
    csv_text = (
        "entry_date,group,ticker,failed_gate,failed_value,ivr,iv_hv_pct,dollar_vol_ok,"
        "vix_regime,squeeze,rvol,trend_200d,dte,strike,entry_premium_mid,underlying_entry,"
        "target,stop,rr_ratio,resolve_date,resolution,exit_premium_mid,ret_pct,notes\n"
        '2026-07-27,SURVIVOR,DRAM,NONE,NONE,41,88.1,Y,STANDARD,,,,25,51.0,5.6,50.94,8.96,3.92,1.60,,OPEN,,,"Built via build_and_log.py. Direction=BULLISH 2/2 scored"\n'
        '2026-07-24,SURVIVOR,NFLX,NONE,NONE,27,66.1,Y,STANDARD,,,,30,70,2.535,70.11,4.056,1.7745,1.6,2026-07-28,STOP,1.365,-46.15,"resolved already"\n'
        '2026-07-28,REJECT,OKLO,SIEVE2B_IVHV,124.0,29,124.0,Y,STANDARD,,,,,,,,,,1.60,,EARNINGS_HARD_SKIP,,,"no contract built"\n'
    )
    p = tmp_path / "forward_test_log.csv"
    p.write_text(csv_text)
    rows = load_open_rows(str(p))
    assert [r["ticker"] for r in rows] == ["DRAM"]


def test_crossref_flags_bullish_against_weakening_quadrant():
    open_rows = [{
        "ticker": "DRAM", "group": "SURVIVOR", "entry_date": "2026-07-27",
        "notes": "Built via build_and_log.py. Direction=BULLISH 2/2 scored",
    }]
    quadrants = {"Memory/Storage": {"quadrant": "Weakening", "rs_ratio": 98.2, "momentum_pct": -3.1}}
    out = crossref_open_positions(open_rows, quadrants)
    assert len(out) == 1
    assert out[0]["cluster"] == "Memory/Storage"
    assert out[0]["direction"] == "BULLISH"
    assert out[0]["flagged"] is True


def test_crossref_does_not_flag_bullish_against_leading_quadrant():
    open_rows = [{
        "ticker": "NVDA", "group": "SURVIVOR", "entry_date": "2026-07-27",
        "notes": "Built via build_and_log.py. Direction=BULLISH 4/4 scored",
    }]
    quadrants = {"Semis": {"quadrant": "Leading", "rs_ratio": 105.0, "momentum_pct": 2.0}}
    out = crossref_open_positions(open_rows, quadrants)
    assert out[0]["flagged"] is False


def test_crossref_no_flag_when_no_proxy_cluster():
    open_rows = [{
        "ticker": "HIVE", "group": "REJECT", "entry_date": "2026-07-27",
        "notes": "Built via build_and_log.py. Direction=BULLISH 3/3 scored",
    }]
    out = crossref_open_positions(open_rows, {})  # no cluster has a computed quadrant
    assert out[0]["cluster"] == "Crypto"
    assert out[0]["quadrant"] is None
    assert out[0]["flagged"] is False


def test_crossref_no_flag_when_direction_unparseable():
    open_rows = [{
        "ticker": "DRAM", "group": "SURVIVOR", "entry_date": "2026-07-27",
        "notes": "some note with no Direction= field at all",
    }]
    quadrants = {"Memory/Storage": {"quadrant": "Lagging", "rs_ratio": 90.0, "momentum_pct": -5.0}}
    out = crossref_open_positions(open_rows, quadrants)
    assert out[0]["direction"] is None
    assert out[0]["flagged"] is False
