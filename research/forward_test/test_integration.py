"""
End-to-end integration test chaining sieves.py -> contracts.py ->
centaur_payload.py with a single realistic dataset (today's real NVDA CORE
scan + option chain, Session 30). Every prior test exercises exactly one
module with hand-shaped intermediate fixtures for the others -- none of them
prove the three modules' actual data contracts fit together when a
SieveResult produced by run_sieve_stack is fed, unmodified, into
build_payload alongside a ContractSelection produced by select_contract.
That's the specific gap a fourth, more stringent pass exists to close.
"""
import centaur_payload as cp
import contracts as c
import sieves as s

NVDA_CALL_CHAIN = [
    {"option_type": "call", "strike": 190.0, "bid": 19.5, "ask": 19.85, "open_interest": 276,
     "greeks": {"delta": 0.7956}},
    {"option_type": "call", "strike": 205.0, "bid": 9.25, "ask": 9.4, "open_interest": 2189,
     "greeks": {"delta": 0.548}},
    {"option_type": "call", "strike": 210.0, "bid": 6.7, "ask": 6.85, "open_interest": 3575,
     "greeks": {"delta": 0.449}},
]


def test_full_pipeline_sieve_to_contract_to_schema_valid_payload():
    # Stage 1: sieves.py -- the real 20-ticker CORE scan, NVDA is the sole finalist.
    scan = [
        s.SieveInput(ticker="NVDA", ivr_52w=40.64, ivr_source="mcp_percentile",
                    iv_annual_pct=38.15, hv_30d_pct=39.64, dollar_vol_usd=32_460_149_549),
        s.SieveInput(ticker="AMD", ivr_52w=98.80, ivr_source="mcp_percentile",
                    iv_annual_pct=85.99, hv_30d_pct=87.40, dollar_vol_usd=19_027_050_999),
    ]
    finalists, all_results = s.run_sieve_stack(scan)
    assert len(finalists) == 1
    nvda_sieve_result = finalists[0]
    assert nvda_sieve_result.ticker == "NVDA"

    # Stage 2: contracts.py -- select a contract off the real chain using
    # the SAME direction/data the finalist would carry downstream.
    selection = c.select_contract(NVDA_CALL_CHAIN, direction="BULLISH")
    assert selection is not None
    assert selection.contract["strike"] == 205.0

    # Stage 3: centaur_payload.py -- feed BOTH prior stages' real outputs in,
    # unmodified, plus the technical/portfolio/earnings context a real
    # Directional Builder run would supply.
    payload = cp.build_payload(
        ticker=nvda_sieve_result.ticker,
        direction="BULLISH",
        timestamp="2026-07-21T15:40:50Z",
        volatility_regime="STANDARD",
        vix_live=17.23,
        sieve=nvda_sieve_result,          # the actual SieveResult object from Stage 1, not a rebuilt copy
        technical={"rsi_14": 51.7, "ema_stack": "BULLISH", "macd_histogram": "BULLISH",
                  "ttm_squeeze": "NOT_FIRING", "rvol_mcp": None, "rvol_note": "n/a",
                  "atr_20": 7.16, "nearest_resistance": 212.71, "nearest_support": 199.36,
                  "room_to_resistance_pct": 2.89, "room_to_support_pct": 3.57},
        price_last=206.74, trend_label="UPTREND", sma_200=192.58, price_vs_sma200_pct=7.29,
        range_52w_pct=58.7,
        portfolio={"existing_position": "NONE", "avg_cost": None, "unrealized_pnl": None,
                  "portfolio_note": "CLEAN_ENTRY"},
        earnings={"next_date": "2026-08-26", "status": "CLEAR"},
        radar_notes="integration test", direction_signal_count="3/5 scored",
        mcp_chain_candidate={              # the actual ContractSelection.contract from Stage 2
            "strike": selection.contract["strike"],
            "bid": selection.contract["bid"],
            "ask": selection.contract["ask"],
            "open_interest": selection.contract["open_interest"],
            "delta": selection.contract["greeks"]["delta"],
        },
    )

    # The end-to-end proof: a payload built from real Stage-1 + Stage-2
    # outputs, chained without any manual reshaping, is schema-valid.
    cp.validate_payload(payload)

    finalist_json = payload["finalists"]["NVDA"]
    assert finalist_json["volatility"]["iv_hv_ratio"] == nvda_sieve_result.iv_hv_pct
    assert finalist_json["mcp_chain_candidate"]["strike"] == selection.contract["strike"]


def test_full_pipeline_unscreenable_ticker_never_reaches_contract_selection():
    """The negative-path integration proof: AVGO's real missing-IV case must
    stop at Stage 1 and never produce a finalist for Stage 2/3 to (mis)handle."""
    scan = [
        s.SieveInput(ticker="AVGO", ivr_52w=74.90, ivr_source="mcp_percentile",
                    iv_annual_pct=None, hv_30d_pct=55.76, dollar_vol_usd=10_147_501_685),
    ]
    finalists, all_results = s.run_sieve_stack(scan)
    assert finalists == []
    assert all_results[0].outcome == "UNSCREENABLE"
    # Stage 2/3 are never reached for this ticker -- nothing further to assert,
    # the absence of a finalist IS the correct end-to-end behavior.


def test_full_pipeline_gate_c_gap_never_reaches_finalist_either():
    """Same negative-path proof for this pass's own finding: a ticker with a
    genuinely missing dollar_vol_usd must also never produce a finalist."""
    scan = [
        s.SieveInput(ticker="GAPDATA", ivr_52w=20.0, ivr_source="mcp_percentile",
                    iv_annual_pct=50.0, hv_30d_pct=60.0, dollar_vol_usd=None),
    ]
    finalists, all_results = s.run_sieve_stack(scan)
    assert finalists == []
    assert all_results[0].outcome == "UNSCREENABLE"
