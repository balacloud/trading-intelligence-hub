# HANDOFF — `iv_hv_ratio` units mismatch between the hub's Directional Builder skill and Centaur ingestion

**Written:** July 15, 2026 (Session 26, trading-intelligence-hub)
**For:** Options IQ Gemini's own dev session (`options_iq_gemini`, separate repo — nothing has been edited there from this handoff)
**Severity:** High — silently breaks every real Centaur submission that follows the skill's own documented convention.

---

## The finding

`options_iq_gemini/app.py:762` (inside `analyze_centaur`):

```python
iv_hv_ratio = vol_data.get("iv_hv_ratio")
if iv_hv_ratio is not None and float(iv_hv_ratio) >= 1.0:
    return jsonify({
        "error": "EDGE_VIOLATION",
        "message": f"Stand down. {ticker} IV/HV ratio is {iv_hv_ratio} (>= 1.0). Options are structurally overpriced."
    }), ...
```

This check expects `iv_hv_ratio` as a **decimal fraction** (0.67 = 67%). Confirmed by your own test suite, `test_centaur_contract.py`:
- Line 45: `"iv_hv_ratio": 0.67, "iv_hv_signal": "DEEP_BUYER_EDGE"` — a passing case
- Line 104: `payload["finalists"]["TEST"]["volatility"]["iv_hv_ratio"] = 1.35` — deliberately triggers the stand-down

But `trading-intelligence-hub/skill-options-directional-builder.md`'s documented formula, and the value the skill actually emits in the CENTAUR JSON, is a **percentage-style number** — e.g. `71.40` for "71.40%" IV/HV. This matches:
- The skill's own display table (`< 70% DEEP BUYER EDGE`, `70–100% BUYER EDGE`, `100–115% NEUTRAL`, `> 115% SELLER EDGE`)
- How `iv_rank` is handled *elsewhere in the same `app.py`* — `app.py:605` checks `iv_rank >= 45`, also percentage-style, not a fraction.

**Net effect:** any real payload following the skill's documented convention has `iv_hv_ratio` expressed as a number that is essentially always ≥ 1.0 (any real percentage above 1%). The `>= 1.0` check therefore fires on *every* submission, regardless of whether the real edge is excellent (e.g. 30%) or terrible (e.g. 150%) — it cannot distinguish them, because both are ≥ 1.0 as raw percentage-style numbers.

## How this was caught

Session 26 ran the first real end-to-end round-trip of a live Directional Builder payload through `/analyze/centaur` — a name (AVAV) with a genuinely good edge (IV/HV 71.4%, well inside the 70–100% BUYER_EDGE band) was rejected with `EDGE_VIOLATION`. Prior sessions' Centaur testing either used mocked/synthetic payloads (which happened to use fraction-style values, matching your code) or stood down before reaching this specific gate for other reasons (squeeze not firing, OI desert) — so this specific mismatch was never exercised with real data until now.

**Not a one-off** — the same fix was applied and confirmed for two more names (WOLF, ECHO) in the same session; all three correctly reached chain resolution once the units were corrected, and all three then stood down for a real, separate reason (no contract cleared the OI/spread/delta/Liquidity Gravity gates) — a legitimate result, not another instance of this bug.

## Immediate workaround (already applied hub-side, not a fix)

For Session 26's live calls, the hub sent `iv_hv_ratio` as a decimal fraction (divided the skill's percentage-style number by 100) to unblock testing. This is a sending-side compatibility patch for one session, not a fix — the skill's own file and documentation still describe and compute the percentage-style convention, and every other consumer of that value (the skill's own display, `OPTIONS_SIEVE_SPEC.md`, etc.) still expects percentage-style. If nothing changes, this same false-rejection will recur the next time a Directional Builder payload is sent following the skill's actual documented behavior.

## Decision needed (Gemini's call)

Two ways to close this permanently — pick whichever is more consistent with the rest of your codebase:

1. **Change `app.py:762`'s threshold** from `>= 1.0` to `>= 100`, treating `iv_hv_ratio` as percentage-style — consistent with how `iv_rank` is already handled in the same file (`>= 45`, not `>= 0.45`). This also matches `CENTAUR_SCHEMA_v2.json`'s field description ("The core edge metric") with no stated units, and the skill's own table.
2. **Change the hub's skill** to always divide by 100 before emitting `iv_hv_ratio`, matching your existing `>= 1.0` fraction convention. This is a one-line change in `skill-options-directional-builder.md`'s Step 4 computation, but it makes `iv_hv_ratio` inconsistent in style with `iv_rank` (which stays percentage-style) inside the same JSON payload — worth weighing against option 1's consistency argument.

Whichever you pick, please also update `test_centaur_contract.py`'s comments/fixtures if the convention changes, and confirm the CENTAUR_SCHEMA_v2.json description gets a units note (`"iv_hv_ratio": { "type": "number", "description": "... expressed as a decimal fraction, not a percentage" }` or the equivalent) so this doesn't silently drift again — the schema currently specifies no units at all, which is exactly how this went undetected through a JSON-schema-valid payload for as long as it did.

## Verification once fixed

Per this hub's own `skill-cross-repo-fix-verification.md` standard: we'll re-run a live Centaur POST with a percentage-style `iv_hv_ratio` (no fraction workaround) and confirm it reaches chain resolution rather than falsely stand down — not just read the diff.
