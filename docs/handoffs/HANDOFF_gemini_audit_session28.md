# HANDOFF: Gemini — Hub Audit Findings (Session 28, Jul 17 2026)

> **Status:** DRAFTED, not yet relayed to Gemini's dev session.
> **Source:** `HUB_AUDIT_FRAMEWORK.md` — one Fable agent, `AUDIT.md`'s own 3-pillar checklist + a spot-check of the July 15 (Session 23) "AUDIT PASSED" entry's RESOLVED claims. The spot-check finding (S3 below) was independently re-verified by the hub session directly against `app.py`.

## The headline finding — a self-reported clean bill of health has drifted

**`last_gamma` is silently reset to 0.0 on every manual `PUT /journal/update`, contradicting the July 15 AUDIT PASSED claim that it's "preserved through DB updates."**

`app.py:1091` computes `last_gamma`, but the `database.update_trade` call that follows (`app.py:1093-1106`) never passes it — so the SQL write falls through to `database.py`'s default of `0.0` (`database.py:107,123`). It's only genuinely preserved via the monitor's own separate write path (`app.py:1011`, `update_gamma_surge_state`). Net effect: one poll of gamma-velocity blindness (velocity reads as 0, the 5% trailing-stop tighten never fires) after any manual trade edit through the journal update endpoint.

*Fix:* add `last_gamma` to the field list in the `database.update_trade` call at `app.py:1093-1106`, mirroring how `gamma_surge_active` and `high_water_mark` are already preserved there.

## Other real findings

**1. `analyze_centaur` can 500 a single-finalist payload.** `app.py:754-759` — the `continue` for a missing/zero `price_last` sits under the *outer* `if not last_price:` check, so a finalist gets skipped even when the Tradier fallback fetch actually succeeded (and no error is recorded in that case). Masked today because the schema currently requires `price_last` — but the schema load itself is fail-open (finding #3 below), so this isn't as protected as it looks.

**2. The earnings-date gate can never actually veto a real date.** `get_earnings_date` (`app.py:138`) always returns `EARNINGS_UNKNOWN` because the Tradier fundamentals endpoint 404s on this account tier — and the fallback explicitly does *not* veto on "unknown" (`app.py:328-330`). `KNOWN_ISSUES.md`'s framing ("safely caught to prevent TBLA exploits") describes a warn-only behavior; the veto itself has never been reachable. `history.md:103` already correctly labels this "(Unverified)" — worth promoting that honesty into `KNOWN_ISSUES.md` directly.

**3. Schema validation loads from a relative path — fails open outside the expected CWD.** `app.py:19-24` loads `"Docs/CENTAUR_SCHEMA_v2.json"` relatively; launched from any other working directory, `CENTAUR_SCHEMA` becomes `None` and validation silently skips (`app.py:688`). Already acknowledged in-code (`app.py:811-813`) but still a real fail-open path, not just a comment.

**4. AUDIT.md's own edge-violation description is stale.** `AUDIT.md:53` says the schema enforces "IV/HV >= 1.0" — the actual threshold is `>= 100.0` in percent-units (`app.py:743`), matching `STATE_HANDOFF.md:51`. The gates themselves are procedural in `analyze_centaur`, not schema-level as AUDIT.md implies. Also: a **missing** `iv_hv_ratio` silently skips the gate entirely (`is not None` check, `app.py:743`) — there's no `MISSING_IVHV` analogue to the existing `MISSING_IVR` fail-loud pattern.

**5. Undocumented live endpoints.** `gemini.md`'s API surface (lines 32-43) doesn't list `GET /discover` (`app.py:482`), `POST /journal/log` (`app.py:908` — the write path `KNOWN_ISSUES.md:4`'s FWD_TEST exclusion rule depends on), or `PATCH /journal/resolve` (`app.py:1127`, commit `cab7527`, built for the hub's own forward-test tooling this session).

**6. Two carried-forward FABLE_5_REVIEW findings are still open, not superseded:** the Senior Partner Rule violation — the Gemini prompt still asks for computed Entry/Target/Stop values (`app.py:460`) with a Python fallback that can diverge (`app.py:362-365`) — and the counter-trend fallback swap (`app.py:286-289`), both unchanged since the original review.

**7. Plain `GET /analyze` bypasses direction enforcement.** Both the centaur and universal-scan paths correctly filter calls/puts by direction, but the older `GET /analyze` route still calls `get_quant_options(ticker)` with no direction filter (`app.py:492`), handing Gemini a mixed call/put set.

## Lower-severity / doc-only

Sieve 1's documented "Option Volume >= 10,000" (`gemini.md:22`) is an orphaned variable, never actually gated (`app.py:555`, single assignment, never re-read). Sieve 4's documented "RVOL >= 1.5" doesn't match the live `rvol_broad=1.2` in `scan_queries.py:19` (1.5 only survives in `volume_breakout`, `quant_math.py:107-112`). `GET /scan` drops the `is_simulated` flag from its response, serving simulated data unlabeled. `Inertia warning at >5 days` actually fires at exactly 5 (`app.py:1031`, doc says "&gt;5"), and compares a UTC DB timestamp to a local `datetime.now()` — a timezone skew in `days_open`. Dead v1 `CENTAUR_SCHEMA.json` still present, unused. Cache still keyed by ticker only, so a centaur synthesis and a plain analyze can cross-serve within the 60-minute window.

## Confirmed clean

pandas vectorization, API key stripping, `datetime.now()` prompt injection, null-quote per-row isolation, `MISSING_IVR` fail-loud, Gamma Surge 10%→5% trailing-stop math itself, `0.25` delta kill-switch backend flag, Liquidity Gravity's Ask>3×Bid rejection with 50-lot noise floor, `quant_math.py`'s test suite (11 defined cases, not re-run this pass), the √252 annualization in the Universal Scanner's TV-to-IV translation.
