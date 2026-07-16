# HANDOFF — a safe close path for daily-mark resolution, plus a real landmine in the existing update endpoint

**Written:** July 16, 2026 (Session 27, trading-intelligence-hub, in progress)
**For:** Options IQ Gemini's own dev session (`options_iq_gemini`, separate repo — nothing has been edited there from this handoff)
**Severity:** MEDIUM (feature gap) + HIGH (a real data-corruption risk found while checking the gap)
**Context:** `FORWARD_TEST_PROTOCOL.md` line 29 already specifies "the hub marks positions itself" — that stays unchanged, for the same reason line 19 rejects Gemini-recommended fills: independent verification, not trusting the system under test to grade its own resolution. What's missing is a *safe way for the hub to execute* the resulting close once it's decided a position resolved.

---

## Part 1 — what already works, confirmed live (no change needed)

Read `/journal/monitor` (`app.py:930-1078`) directly. It's genuinely live: every call re-pulls Tradier quotes for all OPEN positions and recomputes P/L, delta, gamma velocity, HWM, and a `stop_loss_hit` flag from scratch. Confirmed two real ones flagged right now in the dashboard: AFRM (-52.99%, STOP LOSS HIT) and AVAV (-38.42%, STOP LOSS HIT).

Also confirmed: this is advisory-only by design. `stop_loss_hit` and `health_status: "SELL TO CLOSE"` are response fields only — the endpoint never writes `status` back to the DB. Both AFRM and AVAV are still `OPEN` in the database with a manual "STOP HIT" button, not auto-resolved. That's correct behavior — matches `PERSONA.md`'s "risk management execution is a human-discipline requirement by design."

So the gap isn't the live quote/flagging — that's solid. The gap is: once the hub independently confirms a `FWD_TEST` position resolved at close-of-day (per the protocol's mechanical rule, using the hub's own Tradier pull, not this endpoint's flag), there's no safe way to actually close it in your journal.

## Part 2 — the landmine: `PUT /journal/update/<id>` is a full-row replace, not a patch

`app.py:1080-1108`:

```python
gamma_surge = data.get("gamma_surge_active", existing_trade.get("gamma_surge_active", 0))
hwm = data.get("high_water_mark", existing_trade.get("high_water_mark", 0.0))
last_gamma = data.get("last_gamma", existing_trade.get("last_gamma", 0.0))

database.update_trade(
    trade_id=trade_id,
    ticker=data.get("ticker"),
    occ_symbol=data.get("occ_symbol"),
    contract_details=data.get("contract_details"),
    entry_price=data.get("entry_price"),
    target_price=data.get("target_price"),
    stop_loss=data.get("stop_loss"),
    exit_price=data.get("exit_price"),
    setup_context=data.get("setup_context"),
    status=data.get("status"),
    ...
```

Only `gamma_surge_active`, `high_water_mark`, and `last_gamma` fall back to the existing row if omitted. `ticker`, `occ_symbol`, `contract_details`, `entry_price`, `target_price`, `stop_loss`, and `setup_context` do not — they default straight to `None` via `data.get(...)`.

**Concretely:** if the hub calls `PUT /journal/update/8` with just `{"status": "CLOSED", "exit_price": 2.75}` to resolve AFRM's stop, `database.update_trade` gets called with `ticker=None, contract_details=None, entry_price=None, ...` and overwrites those columns with `NULL` on a row that's otherwise fine. The position closes, but the record that made it useful — which contract, what entry, what `FWD_TEST:` tag — is gone. Given the plan is to call this once a day, near close, for months, this is exactly the kind of thing that eventually gets hit by a rushed/partial payload.

This isn't hypothetical — it's the natural way anyone (hub script or a human) would try to close a position: send what changed, not the whole row from memory.

## Proposal — a narrow resolve endpoint, not a full-row PUT

Something like:

```
PATCH /journal/resolve/<trade_id>
Body: { "status": "CLOSED", "exit_price": 2.75, "resolution": "STOP" }
```

Internally: fetch the full existing row via `get_trade_by_id` first (same pattern `journal_update` already uses for `gamma_surge`/`hwm`), and only overwrite `status`, `exit_price`, `final_pl` (already computed inside `update_trade` when status=CLOSED and both prices are present) — pass every other field through from `existing_trade`, not from the request body. That structurally makes it impossible to null out `ticker`/`contract_details`/`setup_context` by omission, regardless of what the caller sends.

The `resolution` field (STOP/TARGET/TIME/EXPIRY) doesn't need a new column if that's a bigger lift — appending it to `setup_context` (e.g. `...migrated=NO,resolved=STOP`) is enough for the hub to log it into `forward_test_log.csv` from `/journal/history`.

**Scope this to be safe for non-`FWD_TEST` rows too** if it's easier to build one endpoint than two — the narrower field-preserving behavior is strictly safer than the current full-replace `journal_update` for any caller, not just the forward test.

## Not proposing

An auto-scheduled/cron close-of-day job inside Gemini itself. The protocol's independence argument (hub pulls its own Tradier mark, decides resolution using the mechanical rule, not Gemini's own flag) stays as-is — this handoff is only about giving the hub a safe way to *execute* the close it already decided on, not about moving that decision into Gemini.

## Verification once fixed

Same as always — we'll read the new endpoint's code, not the summary, and do one live test: resolve a real `FWD_TEST` row through it and confirm via `/journal/history` that every other field on that row (ticker, contract_details, entry_price, setup_context) survived untouched.
