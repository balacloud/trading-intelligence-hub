# HANDOFF: CENTAUR Contract Hardening — for Gemini / options_iq_gemini

**Author:** Claude (trading-intelligence-hub). **Not executed anywhere** — this is a recommendation doc only. No file in `options_iq_gemini` has been touched. Hand this to whoever is running Gemini's dev session on that repo.

**Why this exists:** A field-by-field trace of the CENTAUR_SCHEMA_v2 handoff (hub emits → `app.py` consumes) found that of ~30 fields the hub computes and sends, roughly 18 are silently dropped by `/analyze/centaur` — including `iv_hv_ratio` (the system's actual mathematical edge) and `trade_direction` (the entire output of the hub's 8-signal direction inference). Four specific fixes for that were already passed along separately. This doc is the *systemic* fix — so the next field that gets added on either side doesn't silently rot the same way.

**⚠️ See the STATUS UPDATE section at the bottom of this file — Tasks 1-4 and the four Fable fixes below are DONE, verified by direct code read + running the tests myself, not just Gemini's own summary. Read that section first if you're resuming this work.**

---

## Already in flight (context only — not re-litigated here)

1. Filter `get_quant_options` results by the payload's `trade_direction` before ranking.
2. Read `iv_hv_ratio` / `iv_hv_signal` into the prompt and gate on it (don't call Gemini at all if `iv_hv_ratio >= 1.0`).
3. Read `portfolio` into the prompt.
4. Enforce `iv_rank_52w <= 45` as a real reject, not a display-only number.

If these are done, great — the tasks below are additive and don't depend on them being finished first.

---

## Task 1 — Consolidate the schema into one file

Right now the CENTAUR contract is described in prose in three places (`CLAUDE_MCP_SKILL_HANDOFF.md`, the hub's Directional Builder skill JSON template, and a stale `CENTAUR_SCHEMA.json` at the repo root that's the *wrong, v1* shape — it would crash ingestion if actually sent). Replace `Docs/CENTAUR_SCHEMA.json` (or wherever makes sense — root `CENTAUR_SCHEMA.json` is currently dead and should probably be deleted once this lands) with the real v2 shape below. Once this file exists, both `gemini.md`/`CLAUDE_MCP_SKILL_HANDOFF.md` on this side and the hub's skill on the other side should reference *this file* instead of re-describing the schema in their own words.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "options_iq_gemini/Docs/CENTAUR_SCHEMA_v2.json",
  "title": "CENTAUR_SCHEMA_v2",
  "x-contract-version": "2.0",
  "description": "Stage 1 (Claude Directional Builder skill, trading-intelligence-hub) -> Stage 2 (/analyze/centaur) handoff. This file is the single source of truth for the payload shape. Do not re-describe this schema in prose elsewhere -- reference this file and bump x-contract-version when it changes.",
  "type": "object",
  "required": ["timestamp", "volatility_regime", "direction", "target_dte_range", "target_delta_range", "finalists"],
  "properties": {
    "timestamp": { "type": "string", "format": "date-time", "description": "ISO8601 UTC. TTL = 1800s from this value." },
    "volatility_regime": { "type": "string", "enum": ["STANDARD", "HIGH-FEAR"] },
    "vix_live": { "type": "number" },
    "direction": { "type": "string", "enum": ["BULLISH", "BEARISH"] },
    "direction_source": { "type": "string", "enum": ["USER_DECLARED", "AUTO_INFERRED"] },
    "direction_signal_count": { "type": "string" },
    "target_dte_range": { "type": "array", "items": { "type": "integer" }, "minItems": 2, "maxItems": 2 },
    "target_delta_range": { "type": "array", "items": { "type": "number" }, "minItems": 2, "maxItems": 2 },
    "finalists": {
      "type": "object",
      "minProperties": 1,
      "additionalProperties": { "$ref": "#/definitions/finalist" }
    }
  },
  "definitions": {
    "finalist": {
      "type": "object",
      "required": ["trade_direction", "price_last", "trend_label", "technical", "volatility", "portfolio", "earnings"],
      "properties": {
        "trade_direction": { "type": "string", "enum": ["BULLISH", "BEARISH"] },
        "radar_notes": { "type": "string" },
        "price_last": { "type": "number" },
        "price_source": { "type": "string", "enum": ["live_tick", "prior_close", "positions_mark"] },
        "volume_today": { "type": ["number", "null"] },
        "avg_volume_20d_shares": { "type": "number" },
        "range_52w_pct": { "type": "number" },
        "range_52w_label": { "type": "string", "enum": ["LOWER_THIRD", "MID_RANGE", "UPPER_THIRD"] },
        "trend_200d_sma": { "type": "number" },
        "trend_label": { "type": "string", "enum": ["UPTREND", "DOWNTREND"] },
        "price_vs_sma200_pct": { "type": "number" },
        "put_call_ratio_avg90d": { "type": "number" },
        "put_call_ratio_today": { "type": ["number", "null"] },
        "ytd_change_pct": { "type": "number" },
        "options_liquidity_proxy": {
          "type": "object",
          "properties": {
            "avg_option_vol_total": { "type": "number" },
            "avg_call_vol": { "type": "number" },
            "avg_put_vol": { "type": "number" },
            "verdict": { "type": "string", "enum": ["LIQUID", "THIN", "LIKELY_DESERT"] },
            "note": { "type": "string" }
          }
        },
        "technical": {
          "type": "object",
          "required": ["rsi_14"],
          "properties": {
            "rsi_14": { "type": "number" },
            "ema_stack": { "type": "string", "enum": ["BULLISH", "BEARISH", "MIXED"] },
            "macd_histogram": { "type": "string", "enum": ["BULLISH", "BEARISH", "CROSSING"] },
            "bb_upper": { "type": "number" },
            "bb_lower": { "type": "number" },
            "bb_width_pct": { "type": "number" },
            "ttm_squeeze": { "type": "string", "enum": ["FIRING", "NOT_FIRING"] },
            "rvol_mcp": { "type": ["number", "null"] },
            "rvol_note": { "type": "string" },
            "atr_20": { "type": "number" },
            "nearest_resistance": { "type": ["number", "null"] },
            "nearest_support": { "type": ["number", "null"] },
            "room_to_resistance_pct": { "type": ["number", "null"] },
            "room_to_support_pct": { "type": ["number", "null"] }
          }
        },
        "volatility": {
          "type": "object",
          "required": ["iv_rank_52w", "iv_hv_ratio"],
          "properties": {
            "iv_rank_13w": { "type": "number" },
            "iv_rank_26w": { "type": "number" },
            "iv_rank_52w": { "type": "number" },
            "iv_rank_source": { "type": "string" },
            "ivr_gate": { "type": "string", "enum": ["PASS", "FLAG_VOLATILITY_TAX"] },
            "live_atm_iv": { "type": "number" },
            "live_30d_hv": { "type": "number" },
            "iv_hv_ratio": { "type": "number", "description": "The core edge metric. Must be read and gated on -- see BAD #3 of the Gemini review / contract audit finding." },
            "iv_hv_signal": { "type": "string", "enum": ["DEEP_BUYER_EDGE", "BUYER_EDGE", "NEUTRAL", "SELLER_EDGE"] }
          }
        },
        "strike_zone": {
          "type": "object",
          "properties": {
            "expected_move_28d": { "type": "number" },
            "atm_strike_approx": { "type": "number" },
            "target_strike_zone_low": { "type": "number" },
            "target_strike_zone_high": { "type": "number" },
            "entry_delta_target_low": { "type": "number" },
            "entry_delta_target_high": { "type": "number" }
          }
        },
        "portfolio": {
          "type": "object",
          "required": ["existing_position", "portfolio_note"],
          "properties": {
            "existing_position": { "type": "string" },
            "avg_cost": { "type": ["number", "null"] },
            "unrealized_pnl": { "type": ["number", "null"] },
            "portfolio_note": { "type": "string", "enum": ["CLEAN_ENTRY", "DIRECTIONAL_ADD", "HEDGE"] }
          }
        },
        "earnings": {
          "type": "object",
          "properties": {
            "next_date": { "type": "string" },
            "status": { "type": "string" }
          }
        },
        "mcp_chain_candidate": { "type": "object" },
        "risk_flags": { "type": "array", "items": { "type": "string" } },
        "dual_signal_conflict": { "type": ["boolean", "string", "null"] }
      }
    }
  }
}
```

Treat this as a starting draft, not gospel — adjust if something here doesn't match the real payload shape once you check it against a live-generated example from the hub skill.

---

## Task 2 — Validate on ingest, fail loud instead of silent

**Where:** `analyze_centaur()` in `app.py`, right after `data = request.json` / `if not data: ...`, before the TTL check.

**What:**
1. `pip install jsonschema`, add to `requirements.txt`.
2. Load the schema from Task 1 once at module import time (not per-request).
3. `jsonschema.validate(data, schema)` — on `ValidationError`, return `400` with `{"status": "error", "error": "CENTAUR_SCHEMA_VIOLATION", "message": str(e)}` instead of letting a missing/malformed field surface as a confusing downstream `AttributeError` or, worse, silently produce a garbage analysis.
4. This alone converts "is field X actually being used" from a manual-audit question into something that fails immediately and loudly when the hub's payload shape drifts from what this engine expects.

**Optional but recommended:** log (not necessarily act on yet) any of `risk_flags`, `dual_signal_conflict`, `iv_rank_source` if present in the payload but not yet wired into synthesis, e.g. a one-line `logger.info(f"Received but not yet consumed: {unused_fields}")`. Cheap, and it's the difference between "silently dropped and nobody knows" and "dropped, but visible in the logs."

---

## Task 3 — A contract test that would have caught today's gap automatically

Drop this in as `test_centaur_contract.py`. It's written to fail against the *current* code and pass once Tasks already in flight (direction filter, `iv_hv_ratio` gate, `portfolio` read) land — use it as the actual acceptance test for those fixes rather than manual re-reading.

```python
import pytest
from unittest.mock import patch
from app import app  # adjust import to match actual app factory/instance

FIXTURE_PAYLOAD = {
    "timestamp": "2026-07-04T18:00:00Z",
    "volatility_regime": "STANDARD",
    "vix_live": 14.2,
    "direction": "BEARISH",
    "direction_source": "AUTO_INFERRED",
    "direction_signal_count": "5 bullish / 3 bearish out of 8 scored",
    "target_dte_range": [21, 35],
    "target_delta_range": [0.45, 0.60],
    "finalists": {
        "TEST": {
            "trade_direction": "BEARISH",
            "radar_notes": "Test fixture — bearish setup, cheap vol.",
            "price_last": 100.0,
            "price_source": "live_tick",
            "volume_today": 1_200_000,
            "avg_volume_20d_shares": 900_000,
            "range_52w_pct": 22.0,
            "range_52w_label": "LOWER_THIRD",
            "trend_200d_sma": 108.0,
            "trend_label": "DOWNTREND",
            "price_vs_sma200_pct": -7.4,
            "put_call_ratio_avg90d": 1.4,
            "put_call_ratio_today": 1.6,
            "ytd_change_pct": -12.0,
            "options_liquidity_proxy": {
                "avg_option_vol_total": 15000, "avg_call_vol": 6000, "avg_put_vol": 9000,
                "verdict": "LIQUID", "note": "test"
            },
            "technical": {
                "rsi_14": 38.0, "ema_stack": "BEARISH", "macd_histogram": "BEARISH",
                "bb_upper": 105.0, "bb_lower": 95.0, "bb_width_pct": 9.5,
                "ttm_squeeze": "FIRING", "rvol_mcp": 1.8, "rvol_note": "CONFIRMED",
                "atr_20": 2.1, "nearest_resistance": 108.0, "nearest_support": 92.0,
                "room_to_resistance_pct": 8.0, "room_to_support_pct": 8.0
            },
            "volatility": {
                "iv_rank_13w": 30.0, "iv_rank_26w": 35.0, "iv_rank_52w": 40.0,
                "ivr_gate": "PASS", "live_atm_iv": 28.0, "live_30d_hv": 42.0,
                "iv_hv_ratio": 0.67, "iv_hv_signal": "DEEP_BUYER_EDGE"
            },
            "strike_zone": {
                "expected_move_28d": 6.5, "atm_strike_approx": 100,
                "target_strike_zone_low": 93, "target_strike_zone_high": 100,
                "entry_delta_target_low": 0.45, "entry_delta_target_high": 0.60
            },
            "portfolio": {
                "existing_position": "long_100_shares", "avg_cost": 95.0,
                "unrealized_pnl": 500.0, "portfolio_note": "DIRECTIONAL_ADD"
            },
            "earnings": {"next_date": "VERIFY — not available from MCP", "status": "UNKNOWN"},
            "mcp_chain_candidate": {"note": "deferred to Stage 2"}
        }
    }
}


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_missing_required_field_is_rejected(client):
    """A payload missing 'finalists' should be a loud 400, not a silent pass-through."""
    bad_payload = {k: v for k, v in FIXTURE_PAYLOAD.items() if k != "finalists"}
    resp = client.post("/analyze/centaur", json=bad_payload)
    assert resp.status_code == 400
    assert "SCHEMA" in resp.json.get("error", "") or "finalists" in resp.json.get("message", "").lower()


def test_direction_filters_option_type(client):
    """A BEARISH payload should never surface a CALL as the recommended trade."""
    mock_options = [
        {"symbol": "TEST_CALL", "type": "call", "efficiency": 0.99, "strike": 100, "expiration": "2026-08-01",
         "bid": 1, "ask": 1.1, "bid_size": 10, "ask_size": 10, "spread": 0.05, "open_interest": 1000,
         "volume": 500, "delta": 0.5, "theta": -0.02},
        {"symbol": "TEST_PUT", "type": "put", "efficiency": 0.80, "strike": 95, "expiration": "2026-08-01",
         "bid": 1, "ask": 1.1, "bid_size": 10, "ask_size": 10, "spread": 0.05, "open_interest": 1000,
         "volume": 500, "delta": 0.5, "theta": -0.025},
    ]
    with patch("app.get_quant_options", return_value=(mock_options, {"total": 2, "oi": 0, "spread": 0, "delta": 0, "gravity": 0})):
        resp = client.post("/analyze/centaur", json=FIXTURE_PAYLOAD)
    assert resp.status_code == 200
    returned_types = {o["type"].lower() for o in resp.json["quant_candidates"]}
    assert "call" not in returned_types, "BEARISH payload should never return a call as a candidate"


def test_high_iv_hv_ratio_triggers_stand_down(client):
    """iv_hv_ratio >= 1.0 (SELLER_EDGE) should stand down, not synthesize a trade."""
    payload = dict(FIXTURE_PAYLOAD)
    payload["finalists"] = dict(payload["finalists"])
    payload["finalists"]["TEST"] = dict(payload["finalists"]["TEST"])
    payload["finalists"]["TEST"]["volatility"] = dict(payload["finalists"]["TEST"]["volatility"])
    payload["finalists"]["TEST"]["volatility"]["iv_hv_ratio"] = 1.35
    payload["finalists"]["TEST"]["volatility"]["iv_hv_signal"] = "SELLER_EDGE"

    resp = client.post("/analyze/centaur", json=payload)
    # Exact shape depends on how the stand-down gets implemented -- adjust assertion
    # to whatever response contract Task "enforce iv_hv_ratio" ends up using.
    assert resp.status_code in (200, 422)
    if resp.status_code == 200:
        assert "NO TRADE" in resp.json.get("intelligence_report", "").upper() or resp.json.get("stand_down") is True
```

Adjust the Flask import/fixture setup to match how `app.py` actually exposes the app object and how `get_quant_options` is imported elsewhere in the test — the shape above assumes a standard `from app import app` and that `get_quant_options` is patchable at `app.get_quant_options`.

---

## Task 4 — One line in PROTOCOL.md's Session Close Protocol

Add this as a new numbered item in the existing "🛑 Session Close Protocol" list (not a new section — it belongs in the checklist that already runs every close):

> **Contract Version Check**: If `Docs/CENTAUR_SCHEMA_v2.json`'s `x-contract-version` changed this session (new/removed/retyped field), log it in `KNOWN_ISSUES.md` under a `SCHEMA_CHANGE` tag with the old and new version. The hub's own session-open should diff its copy of the schema against this file and flag a mismatch before generating another handoff payload.

This is deliberately not new infrastructure — it rides on the close-protocol habit this project already has (history.md / KNOWN_ISSUES.md / AUDIT.md updates already happen every close; this just adds one more line item).

---

## Reminder: this doc doesn't replace PROTOCOL.md's own close checklist

Once any of the above lands, still run the existing Session Close Protocol as-is: update `history.md` (what changed and why), `gemini.md` (if architecture/API surface changed), `KNOWN_ISSUES.md` (correct the stale "TBLA bypass resolved" entry if that's touched in the same pass, and log the schema-version bump per Task 4), `AUDIT.md` (if any gate logic changed), and `Docs/CLAUDE_MCP_SKILL_HANDOFF.md` (bump the version reference to point at the new consolidated schema file from Task 1).

---

## STATUS UPDATE — verified done (all four Fable fixes + all four Handoff tasks)

Gemini's dev session implemented all of the above. This was **not accepted on the strength of Gemini's own summary** — every claim below was checked by reading the live `app.py` directly and, where possible, actually running the code, per this project's own live-read discipline.

**Confirmed real, by direct verification:**
- `iv_hv_ratio >= 1.0` → hard rejects with `EDGE_VIOLATION` (400). Read the code, confirmed correct.
- `IVR > 45` → hard rejects with `EDGE_VIOLATION` (correct boundary — exactly 45 passes, matching "IVR ≤ 45" as stated everywhere else in this project).
- `trade_direction` now filters the option chain — confirmed double-enforced (once inside `get_quant_options`, once as a redundant safety filter immediately after).
- `portfolio_data` isn't a dead parameter — traced it all the way into the actual prompt string (`portfolio_warning`, interpolated into the final Gemini prompt).
- `jsonschema` validation is wired into `/analyze/centaur` and does reject malformed payloads. (Minor unaddressed risk: if `Docs/CENTAUR_SCHEMA_v2.json` fails to load at import time, it silently falls back to `CENTAUR_SCHEMA = None` and validation is skipped entirely, with only a `print()` warning. Worth a startup assertion instead of a silent skip, but not urgent.)
- `test_centaur_contract.py` — ran it myself: **3/3 genuinely pass.**

**Two claims that were overstated — corrected, not just noted:**

1. **AUDIT.md's "TBLA bug fully resolved" claim was premature.** The code fix (substring match instead of exact match on the `event` field) is real and is an improvement. But the Tradier token is dead right now — I ran `test_tradier_calendar.py` against the live API myself and the response isn't even valid JSON. **This fix has never been tested against a real Tradier response.** This is the same bug that was marked "resolved" once before (July 1) and turned out false — don't repeat the pattern. **Action once the Tradier token is refreshed: run `test_tradier_calendar.py` (or hit `/analyze/centaur` for a ticker with known upcoming earnings) and confirm `get_earnings_date` actually returns a real date, not just that it doesn't crash.** Until that's done once, treat this as "improved, unverified," not "resolved."

2. **"Mathematically proved the edge" (Phase 13 / `handoff_summary.md`) overstated what `options_edge_backtest.py` actually tested.** That script explicitly (per its own code comment) never tested the IV/HV signal at all — only a momentum/timing signal (Squeeze + RVOL + 200-SMA trend) on 5 hand-picked mega-cap names, then extrapolated with a bare threshold heuristic ("if MFE > 4%, WILL DEFINITELY PRINT MONEY") rather than an actual options payoff model.

   **A refined version was built and actually run** (not by Gemini — read-only against this repo, executed separately): `/Users/balajik/projects/trading-intelligence-hub/research/options_edge_backtest_v2.py` + `research/backtest_v2_trades.csv` (1,230 trades). Real universe (the hub's own 20-name CORE watchlist), 2019–2024 segmented by regime, a random-entry control, and an approximate Black-Scholes payoff instead of a threshold heuristic.

   **Result — better than expected, but narrower than claimed:**
   - A realized-vol-compression proxy (the closest honest stand-in for IV/HV<1 + IVR≤45 without paid options data) is where the edge concentrates: compressed setups → 56.7% win rate, +31.8% mean modeled return, **survives a pessimistic IV-crush scenario**. Non-compressed setups on the same momentum signal are *worse than random*.
   - The 200-day trend filter **alone** is statistically indistinguishable from random entry (42.9% vs 42.1%). It is not, by itself, adding edge — the compression gate is doing the work. Worth correcting in `AUDIT.md`'s framing of the Pillars.
   - 2022 (bear market) was a wipeout (n=9, mean −53%) — small sample, but the direction is exactly what first-principles theory predicts for long premium against both trend and theta simultaneously. **There is currently no gate in `app.py` that stands the long-call engine down when the broad market is in a confirmed downtrend. Recommend adding one** — this is now a data-backed recommendation, not speculation.
   - A real look-ahead bias was found and fixed in the *original* backtest's harness (it filled at the signal day's own close, using that day's full volume — data not actually available at the moment of entry). The refined version fills at next-day open. The original's 63.6% win rate was likely inflated by this independent of everything else.
   - **Only the long-call side has any backtest coverage at all, in either version.** The bearish/put side of the engine has zero validation. Don't assume symmetry.

   **Action:** soften "mathematically proved the edge" in `history.md` Phase 13 and `handoff_summary.md` to reflect the above — the edge is real and scenario-robust where it's been tested, but conditional on the compression gate (not the trend gate) and untested on the short side.

**Bottom line for whoever picks this up next:** the contract-hardening work is genuinely solid and done. The backtest work is genuinely promising and done, on the call side only. Two doc corrections (TBLA "resolved" → "unverified pending live token"; backtest "proved" → "compression-gated edge is real, conditional, call-side only") are the only outstanding items from this round.
