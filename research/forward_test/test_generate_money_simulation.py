"""
Tests for generate_money_simulation.py -- the 1-contract dollar-simulation
generator behind the "What Real Money Would Look Like" artifact. Uses a small
synthetic CSV so the numbers are hand-verifiable, not the real (large, moving)
forward_test_log.csv.
"""
import csv
import json
import os
import tempfile

import generate_money_simulation as gms

CSV_HEADER = [
    "entry_date", "group", "ticker", "failed_gate", "failed_value", "ivr", "iv_hv_pct",
    "dollar_vol_ok", "vix_regime", "squeeze", "rvol", "trend_200d", "dte", "strike",
    "entry_premium_mid", "underlying_entry", "target", "stop", "rr_ratio",
    "resolve_date", "resolution", "exit_premium_mid", "ret_pct", "notes",
]


def _row(**kw):
    row = {k: "" for k in CSV_HEADER}
    row.update(kw)
    return row


def _write_csv(rows):
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="")
    writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
    writer.writeheader()
    writer.writerows(rows)
    f.close()
    return f.name


def test_resolved_trade_dollar_math():
    path = _write_csv([
        _row(entry_date="2026-07-15", group="SURVIVOR", ticker="CCJ",
             entry_premium_mid="5.1", resolve_date="2026-07-17", resolution="TARGET",
             exit_premium_mid="8.825", ret_pct="73.0"),
    ])
    resolved, open_pos = gms.load_real_trades(path)
    assert len(resolved) == 1 and len(open_pos) == 0
    trades = gms.build_trades(resolved)
    t = trades[0]
    assert t["cost"] == 510.0       # 5.1 * 100
    assert t["proceeds"] == 882.5   # 8.825 * 100
    assert t["pnl"] == 372.5
    assert t["running_pnl"] == 372.5


def test_builder_mixed_and_earnings_hard_skip_excluded_no_money_on_table():
    """These outcomes never had a contract built -- entry_premium_mid is blank
    in the real CSV for both. Must never appear as a simulated trade."""
    path = _write_csv([
        _row(entry_date="2026-07-22", group="REJECT", ticker="PATH",
             entry_premium_mid="", resolution="BUILDER_MIXED"),
        _row(entry_date="2026-07-27", group="REJECT", ticker="TRP",
             entry_premium_mid="", resolution="EARNINGS_HARD_SKIP"),
    ])
    resolved, open_pos = gms.load_real_trades(path)
    assert resolved == [] and open_pos == []


def test_open_position_shows_cost_only_never_a_guessed_pnl():
    path = _write_csv([
        _row(entry_date="2026-07-28", group="SURVIVOR", ticker="BAH",
             entry_premium_mid="4.65", resolution="OPEN"),
    ])
    resolved, open_pos = gms.load_real_trades(path)
    open_trades = gms.build_open_trades(open_pos)
    assert len(open_trades) == 1
    assert open_trades[0]["cost"] == 465.0
    assert "pnl" not in open_trades[0]


def test_running_pnl_accumulates_in_resolve_date_order_not_entry_date_order():
    """A trade entered later but resolved earlier must come first in the
    running total -- the equity curve replays resolution order, not entry order."""
    path = _write_csv([
        _row(entry_date="2026-07-20", group="SURVIVOR", ticker="A",
             entry_premium_mid="1.0", resolve_date="2026-07-25", resolution="TARGET",
             exit_premium_mid="2.0", ret_pct="100.0"),
        _row(entry_date="2026-07-15", group="REJECT", ticker="B",
             entry_premium_mid="1.0", resolve_date="2026-07-16", resolution="STOP",
             exit_premium_mid="0.5", ret_pct="-50.0"),
    ])
    resolved, _ = gms.load_real_trades(path)
    trades = gms.build_trades(resolved)
    assert [t["ticker"] for t in trades] == ["B", "A"]  # B resolved first
    assert trades[0]["running_pnl"] == -50.0
    assert trades[1]["running_pnl"] == 50.0


def test_summary_group_split_matches_manual_sum():
    path = _write_csv([
        _row(entry_date="2026-07-15", group="SURVIVOR", ticker="A", entry_premium_mid="1.0",
             resolve_date="2026-07-16", resolution="STOP", exit_premium_mid="0.5", ret_pct="-50.0"),
        _row(entry_date="2026-07-15", group="REJECT", ticker="B", entry_premium_mid="1.0",
             resolve_date="2026-07-16", resolution="TARGET", exit_premium_mid="2.0", ret_pct="100.0"),
    ])
    resolved, open_pos = gms.load_real_trades(path)
    trades = gms.build_trades(resolved)
    summary = gms.build_summary(trades, gms.build_open_trades(open_pos))
    assert summary["by_group"]["SURVIVOR"]["pnl"] == -50.0
    assert summary["by_group"]["REJECT"]["pnl"] == 100.0
    assert summary["total_pnl"] == 50.0
    assert summary["roi_pct"] == 25.0  # 50 / 200 total cost * 100


def test_render_produces_valid_json_and_injects_into_template():
    path = _write_csv([
        _row(entry_date="2026-07-15", group="SURVIVOR", ticker="CCJ", entry_premium_mid="5.1",
             resolve_date="2026-07-17", resolution="TARGET", exit_premium_mid="8.825", ret_pct="73.0"),
    ])
    out = tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False).name
    dataset = gms.render(out, csv_path=path)
    with open(out) as f:
        html = f.read()
    assert "__DATA_JSON__" not in html  # placeholder fully replaced
    assert "CCJ" in html
    assert dataset["summary"]["total_resolved"] == 1


def test_render_raises_loud_on_a_template_missing_the_placeholder():
    bad_template = tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False)
    bad_template.write("<html>no placeholder here</html>")
    bad_template.close()
    path = _write_csv([_row(entry_date="2026-07-15", group="SURVIVOR", ticker="X",
                             entry_premium_mid="1.0", resolution="OPEN")])
    out = tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False).name
    try:
        gms.render(out, csv_path=path, template_path=bad_template.name)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "placeholder" in str(e)


def test_real_trade_with_unrecognized_resolution_fails_loud_not_silently_dropped():
    """Real gap found Session 37 in a Pass-2 review: a row with a genuine
    entry_premium_mid but a resolution value outside TARGET/STOP/OPEN would
    previously vanish from both buckets with no warning -- real capital
    silently missing from the simulation's totals. Must raise, not swallow."""
    path = _write_csv([
        _row(entry_date="2026-07-15", group="SURVIVOR", ticker="WEIRD",
             entry_premium_mid="1.0", resolution="SOME_UNKNOWN_STATE"),
    ])
    try:
        gms.load_real_trades(path)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "WEIRD" in str(e)
        assert "SOME_UNKNOWN_STATE" in str(e)
