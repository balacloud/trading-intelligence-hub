# HANDOFF RESOLUTION — `iv_hv_ratio` units mismatch

**Written:** July 15, 2026 (Options IQ Gemini dev session)
**For:** trading-intelligence-hub

## Resolution
We have reviewed `HANDOFF_gemini_iv_hv_units.md` and have chosen **Option 1**.

1. **`app.py:762` threshold changed**: We updated the check from `>= 1.0` to `>= 100.0`. `iv_hv_ratio` is now treated as a percentage-style number (e.g., 71.4 for 71.4%) natively in our backend, making it consistent with `iv_rank_52w`.
2. **Test suite updated**: All fixtures in `test_centaur_contract.py` and `test_session21_relay.py` have been updated to use percentage-style integers/floats. Tests pass successfully.
3. **Schema updated**: `Docs/CENTAUR_SCHEMA_v2.json` was updated to explicitly specify the units:
   `"description": "The core edge metric. Must be read and gated on... Expressed as a percentage-style number (e.g., 71.4 for 71.4%), not a decimal fraction."`

The hub can continue sending `iv_hv_ratio` as a percentage-style number per the original documented behavior. You are clear to verify with a live Centaur POST (without the fraction workaround).
