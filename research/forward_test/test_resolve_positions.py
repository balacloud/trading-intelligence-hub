"""
Regression tests for resolve_positions.py, written during Session 34's
three-pass code review. No test file existed for this module before -- a
real gap on its own, given it's the only script allowed to write real
resolutions to Gemini's journal and the CSV.
"""
import csv

import pytest

import resolve_positions as rp


def test_decide_resolution_stop():
    trade = {"timestamp": "2026-07-01 09:00:00", "occ_symbol": "BB260814C00008500",
              "stop_loss": 1.0, "target_price": 3.0}
    import datetime
    outcome, dte = rp.decide_resolution(trade, mid=0.5, today=datetime.date(2026, 7, 10))
    assert outcome == "STOP"
    assert dte == (datetime.date(2026, 8, 14) - datetime.date(2026, 7, 1)).days


def test_decide_resolution_target():
    trade = {"timestamp": "2026-07-01 09:00:00", "occ_symbol": "BB260814C00008500",
              "stop_loss": 1.0, "target_price": 3.0}
    import datetime
    outcome, dte = rp.decide_resolution(trade, mid=3.5, today=datetime.date(2026, 7, 10))
    assert outcome == "TARGET"


def test_decide_resolution_open_when_in_range():
    trade = {"timestamp": "2026-07-01 09:00:00", "occ_symbol": "BB260814C00008500",
              "stop_loss": 1.0, "target_price": 3.0}
    import datetime
    outcome, dte = rp.decide_resolution(trade, mid=2.0, today=datetime.date(2026, 7, 5))
    assert outcome is None
    assert dte == 44  # Jul 1 -> Aug 14


def test_occ_expiry_date_parses_correctly():
    assert rp.occ_expiry_date("BB260814C00008500").isoformat() == "2026-08-14"


def test_occ_expiry_date_raises_on_malformed_symbol():
    with pytest.raises(ValueError, match="Cannot parse expiry"):
        rp.occ_expiry_date("not-a-real-occ-symbol")


CSV_HEADER = (
    "entry_date,group,ticker,failed_gate,failed_value,ivr,iv_hv_pct,dollar_vol_ok,vix_regime,"
    "squeeze,rvol,trend_200d,dte,strike,entry_premium_mid,underlying_entry,target,stop,"
    "rr_ratio,resolve_date,resolution,exit_premium_mid,ret_pct,notes\n"
)


def _write_csv(path, rows):
    with open(path, "w", newline="") as f:
        f.write(CSV_HEADER)
        csv.writer(f).writerows(rows)


def test_update_csv_disambiguates_same_ticker_same_strike_different_dte(tmp_path, monkeypatch):
    # Regression test for the real Session 34 finding: two CSV rows sharing a
    # ticker AND a strike (plausible -- same name logged on different days at
    # the same round strike) used to be indistinguishable to update_csv's
    # matching logic, which only checked ticker+strike. The fix adds dte as a
    # second match key. This fixture deliberately constructs exactly that
    # collision -- same ticker "AAAA", same strike 10.0, different dte (21 vs
    # 28) -- and confirms the resolution lands on the correct row.
    csv_path = tmp_path / "forward_test_log.csv"
    rows = [
        ["2026-07-01", "SURVIVOR", "AAAA", "NONE", "NONE", 20, 80, "Y", "STANDARD",
         "NOT_FIRING", "NA", "UPTREND", 21, 10.0, 1.0, 9.5, 1.6, 0.7, "1.60", "", "OPEN", "", "", "row1"],
        ["2026-07-05", "SURVIVOR", "AAAA", "NONE", "NONE", 25, 85, "Y", "STANDARD",
         "NOT_FIRING", "NA", "UPTREND", 28, 10.0, 1.2, 9.8, 1.92, 0.84, "1.60", "", "OPEN", "", "", "row2"],
    ]
    _write_csv(csv_path, rows)
    monkeypatch.setattr(rp, "CSV_PATH", str(csv_path))

    resolutions = [{
        "id": 999, "ticker": "AAAA", "occ_symbol": "AAAA260805C00010000",
        "mid": 1.9, "resolution": "TARGET", "ret_pct": 58.3,
        "dte_at_entry": 28,  # matches row2 specifically, not row1
    }]
    rp.update_csv(resolutions, "2026-07-25", dry_run=False)

    with open(csv_path, newline="") as f:
        result_rows = list(csv.reader(f))
    row1_result, row2_result = result_rows[1], result_rows[2]
    assert row1_result[19] == ""  # resolve_date -- row1 (dte=21) must stay untouched
    assert row2_result[19] == "2026-07-25"  # row2 (dte=28) is the one that should resolve
    assert row2_result[20] == "TARGET"


def test_update_csv_does_not_double_match_same_occ_to_two_rows(tmp_path, monkeypatch):
    # A single resolution should claim at most one CSV row, even if (somehow)
    # more than one row could otherwise satisfy ticker+strike+dte.
    csv_path = tmp_path / "forward_test_log.csv"
    rows = [
        ["2026-07-01", "SURVIVOR", "AAAA", "NONE", "NONE", 20, 80, "Y", "STANDARD",
         "NOT_FIRING", "NA", "UPTREND", 21, 10.0, 1.0, 9.5, 1.6, 0.7, "1.60", "", "OPEN", "", "", "row1"],
        ["2026-07-01", "REJECT", "AAAA", "SOME_GATE", "1.0", 20, 80, "Y", "STANDARD",
         "NOT_FIRING", "NA", "UPTREND", 21, 10.0, 1.0, 9.5, 1.6, 0.7, "1.60", "", "OPEN", "", "", "row1-dup"],
    ]
    _write_csv(csv_path, rows)
    monkeypatch.setattr(rp, "CSV_PATH", str(csv_path))

    resolutions = [{
        "id": 999, "ticker": "AAAA", "occ_symbol": "AAAA260805C00010000",
        "mid": 1.9, "resolution": "TARGET", "ret_pct": 58.3, "dte_at_entry": 21,
    }]
    rp.update_csv(resolutions, "2026-07-25", dry_run=False)

    with open(csv_path, newline="") as f:
        result_rows = list(csv.reader(f))
    resolved_count = sum(1 for r in result_rows[1:] if r[19] == "2026-07-25")
    assert resolved_count == 1  # only the first-matching row, never both
