# Quick note — `STATE_HANDOFF.md`'s "Hard Gates" line is hardcoded, not live

**Written:** July 16, 2026 (Session 27, trading-intelligence-hub)
**Severity:** LOW — cosmetic/stale-doc, not a code bug. Nice-to-fix, not urgent.

All three Phase 16 close fixes verified good (AUDIT.md claim removed, `history.md` reordered, real commit `d649ad5`). One small leftover found while checking the regeneration:

`STATE_HANDOFF.md` still prints `Hard Gates: iv_hv_ratio >= 1.0 (Edge Violation)` even after a fresh regen — because that line is a **hardcoded literal in `scripts/generate_handoff.py:91`**, not read from `app.py` (which is actually `>= 100.0` now, per the earlier units fix). It'll keep printing the wrong threshold on every future regen until the script itself is edited.

Fix: either read the threshold from `app.py` dynamically, or just update the literal on line 91 to `>= 100.0`. Whenever's convenient.
