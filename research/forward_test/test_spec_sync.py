"""
Guards the dual-computation-path risk named in PLAN_deterministic_pipeline_formalization.md
Section 3: OPTIONS_SIEVE_SPEC.md (prose, human-readable) and sieves.py (code,
authoritative) describe the same thresholds. If someone changes a constant in
one without the other, this test fails the build instead of the two silently
drifting apart -- the exact disease OPTIONS_SIEVE_SPEC.md was originally
built to cure between skill-options-ibkr-radar.md and skill-options-scanner.md.
"""
import os
import re

import yaml

import sieves as s

SPEC_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "OPTIONS_SIEVE_SPEC.md"
)


def _load_spec_sync_block() -> dict:
    with open(SPEC_PATH) as f:
        content = f.read()
    match = re.search(r"```yaml\n# SPEC_SYNC_BLOCK.*?\n(.*?)```", content, re.DOTALL)
    assert match, "SPEC_SYNC_BLOCK not found in OPTIONS_SIEVE_SPEC.md -- did the banner get removed?"
    return yaml.safe_load(match.group(1))


def test_spec_sync_block_matches_sieves_py_constants():
    spec_values = _load_spec_sync_block()
    code_values = {
        "IVR_MAX": s.IVR_MAX,
        "IV_ANOMALY_MAX": s.IV_ANOMALY_MAX,
        "DOLLAR_VOL_FLOOR": s.DOLLAR_VOL_FLOOR,
        "MARKET_CAP_FLOOR": s.MARKET_CAP_FLOOR,
        "IVHV_FINALIST_MAX": s.IVHV_FINALIST_MAX,
        "TRAP_IVR_MAX": s.TRAP_IVR_MAX,
        "TRAP_IVHV_MIN": s.TRAP_IVHV_MIN,
        "FINALIST_COUNT": s.FINALIST_COUNT,
    }
    assert spec_values == code_values, (
        f"OPTIONS_SIEVE_SPEC.md's SPEC_SYNC_BLOCK has drifted from sieves.py's constants. "
        f"Spec: {spec_values}  Code: {code_values}  -- edit both in the same commit."
    )
