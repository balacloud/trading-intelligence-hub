"""
Forward test dashboard — a visual control panel for resolve_positions.py and
build_and_log.py. Scoped deliberately: it executes the two automated scripts
(with a dry-run preview -> explicit confirm step, same safety shape the CLI
already has), and visualizes current state. It does NOT run the Scan step —
that needs a live IBKR MCP session and can't be a button here.

Localhost only, no auth, matches the trust model of options_iq_gemini's own
Flask app (port 5002) and options-iq's (port 5051). This one runs on 5055
(5060 was tried first — Chrome hardblocks it as ERR_UNSAFE_PORT, it's the
SIP protocol port on Chrome's fixed blocklist, unrelated to what's actually
running there).

Usage:
    python3 app.py
    open http://localhost:5055
"""
import csv
import json
import os
import sys
from datetime import datetime, timezone

from flask import Flask, render_template, request, redirect, url_for

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import resolve_positions as rp
import build_and_log as bl

app = Flask(__name__)


def load_all_fwd_test_trades():
    import requests
    resp = requests.get(f"{rp.GEMINI_BASE_URL}/journal/history", timeout=10)
    resp.raise_for_status()
    trades = resp.json()
    return [t for t in trades if (t.get("setup_context") or "").startswith("FWD_TEST:")]


def group_of(trade):
    sc = trade.get("setup_context") or ""
    try:
        return sc.split("|")[0].split(":")[1]
    except IndexError:
        return "UNKNOWN"


@app.route("/")
def index():
    trades = load_all_fwd_test_trades()
    open_trades = [t for t in trades if t["status"] == "OPEN"]
    closed_trades = [t for t in trades if t["status"] == "CLOSED"]

    mids = {}
    if open_trades:
        try:
            token = rp.load_tradier_token()
            mids = rp.fetch_live_mids([t["occ_symbol"] for t in open_trades], token)
        except Exception as e:
            mids = {"__error__": str(e)}

    open_rows = []
    for t in open_trades:
        mid = mids.get(t["occ_symbol"]) if "__error__" not in mids else None
        unrealized_pct = round((mid - t["entry_price"]) / t["entry_price"] * 100, 2) if mid else None
        open_rows.append({
            "id": t["id"], "ticker": t["ticker"], "group": group_of(t),
            "entry": t["entry_price"], "mid": mid, "stop": t["stop_loss"], "target": t["target_price"],
            "unrealized_pct": unrealized_pct,
        })

    closed_rows = sorted(
        [{"id": t["id"], "ticker": t["ticker"], "group": group_of(t),
          "entry": t["entry_price"], "exit": t["exit_price"], "final_pl": t["final_pl"]}
         for t in closed_trades],
        key=lambda r: r["id"], reverse=True,
    )

    wins = sum(1 for r in closed_rows if (r["final_pl"] or 0) > 0)
    losses = sum(1 for r in closed_rows if (r["final_pl"] or 0) <= 0)
    survivor_closed = [r for r in closed_rows if r["group"] == "SURVIVOR"]
    reject_closed = [r for r in closed_rows if r["group"] == "REJECT"]

    return render_template(
        "index.html",
        open_rows=open_rows, closed_rows=closed_rows,
        wins=wins, losses=losses,
        survivor_closed=survivor_closed, reject_closed=reject_closed,
        mids_error=mids.get("__error__"),
    )


@app.route("/resolve/preview", methods=["POST"])
def resolve_preview():
    today = datetime.now(timezone.utc).date()
    report_rows, resolutions = rp.compute_resolutions(today)
    return render_template(
        "resolve_preview.html",
        report_rows=report_rows, resolutions=resolutions,
        resolutions_json=json.dumps(resolutions), today_str=today.isoformat(),
    )


@app.route("/resolve/confirm", methods=["POST"])
def resolve_confirm():
    resolutions = json.loads(request.form["resolutions_json"])
    today_str = request.form["today_str"]
    rp.apply_resolutions(resolutions, today_str)
    return redirect(url_for("index"))


@app.route("/build")
def build_page():
    return render_template("build.html", results=None)


@app.route("/build/preview", methods=["POST"])
def build_preview():
    csv_text = request.form["scan_csv"]
    reader = csv.DictReader(csv_text.strip().splitlines())
    scan_rows = list(reader)
    today = datetime.now(timezone.utc).date()
    results = bl.compute_builds(scan_rows, today)
    return render_template(
        "build.html", results=results,
        results_json=json.dumps(results), today_str=today.isoformat(),
    )


@app.route("/build/confirm", methods=["POST"])
def build_confirm():
    results = json.loads(request.form["results_json"])
    today_str = request.form["today_str"]
    today = datetime.strptime(today_str, "%Y-%m-%d").date()
    bl.apply_builds(results, today)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(port=5055, debug=True)
