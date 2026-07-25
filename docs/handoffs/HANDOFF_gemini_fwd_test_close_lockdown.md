# HANDOFF — lock FWD_TEST position closes to the hub's resolve endpoint only

**Written:** July 16, 2026 (Session 27, trading-intelligence-hub, in progress)
**For:** Options IQ Gemini's own dev session (`options_iq_gemini`, separate repo — nothing has been edited there from this handoff)
**Severity:** MEDIUM — not a data-safety bug (see below), but a real experiment-integrity gap that already fired once today.

---

## What happened

Today's forward test closed its first two real positions — but not through the hub's resolution path. `backend.log` shows:

```
127.0.0.1 - - [16/Jul/2026 15:16:04] "PUT /journal/close/8 HTTP/1.1" 200 -
127.0.0.1 - - [16/Jul/2026 15:16:21] "PUT /journal/close/15 HTTP/1.1" 200 -
```

Someone closed AFRM (id 8) and AVAV (id 15) from the dashboard's own Close/"STOP HIT" button. That's `/journal/close/<id>` → `database.close_trade` — working exactly as designed, no bug there (confirmed by reading it: it only touches `status`/`exit_price`/`final_pl`, same narrow-update shape as the `resolve_trade` function built earlier today, so no null-overwrite risk either).

The problem is specific to the **forward test's methodology**, not to Gemini's code: `FORWARD_TEST_PROTOCOL.md` requires resolution on a **bid/ask mid, pulled independently by the hub, evaluated at close-of-day** — never touch-based, stated explicitly so "nobody 'improves' it mid-test." The dashboard's Close button uses whatever `/journal/monitor` shows as `current_price` (that's `quote.get("last")`, confirmed in `app.py:978`) — the *last trade price*, not mid — and it fires whenever someone clicks it, not at a defined checkpoint. Both closes today landed on exactly the `last` values from an earlier intraday snapshot, not a fresh close-of-day mid.

Bala's call: accept these two exits as the real recorded outcome (a human took a real action — that's not something to paper over), but lock down the mechanism going forward so this doesn't quietly become the normal way forward-test positions resolve.

## The ask

Guard **any endpoint that can set a trade's `status` to `CLOSED`** against rows tagged `FWD_TEST:` in `setup_context` — specifically:

1. **`PUT /journal/close/<id>`** (`app.py:1117`, calls `database.close_trade`)
2. **`PUT /journal/update/<id>`** (`app.py:1080`, calls `database.update_trade` — can also set `status`)

For both: before calling the database function, fetch the existing row (`database.get_trade_by_id`, same pattern already used in `journal_update` for `gamma_surge`/`hwm`) and check `setup_context.startswith("FWD_TEST:")`. If true and the request would set `status="CLOSED"`, reject with `403` and a message like `"FWD_TEST positions can only be resolved via PATCH /journal/resolve/<id> by hub automation."` Non-`FWD_TEST` rows (real trades) are unaffected — the dashboard's Close button keeps working normally for those.

**Leave `PATCH /journal/resolve/<id>` unguarded** — that's the one path this is meant to funnel everything through, and it's the endpoint the hub's own resolution script (see below) now calls.

**Optional, not required:** if it's a quick change, disabling/hiding the frontend's Close/"STOP HIT" button specifically for rows whose `setup_context` starts with `FWD_TEST:` would stop this at the UI layer too, before it even reaches the backend. Not asking for this today — the backend guard is authoritative regardless of what the UI shows, and the UI change is a separate (React) piece of work.

## What the hub is building on its side, for context

A script (`research/forward_test/resolve_positions.py`) that runs the actual close-of-day check: pulls Tradier mid for every open `FWD_TEST` row, compares against each row's own stored `stop_loss`/`target_price`, and calls `PATCH /journal/resolve/<id>` for anything that should close — mark ≤ stop → STOP, mark ≥ target → TARGET, held ≥ DTE×0.60 → TIME. This is the "hub automation" the guard message above refers to.

## Verification once fixed

Per `skill-cross-repo-fix-verification.md`: we'll test by attempting `PUT /journal/close/<id>` on a scratch `FWD_TEST:` row and confirming it 403s, then confirming a real (non-`FWD_TEST`) trade can still be closed normally through the same endpoint.
