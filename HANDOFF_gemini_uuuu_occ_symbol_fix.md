# HANDOFF — one malformed occ_symbol silently breaking a position's daily marks

**Written:** July 22, 2026 (Session 31, trading-intelligence-hub, in progress)
**For:** Options IQ Gemini's own dev session (`options_iq_gemini`, separate repo — nothing has been edited there from this handoff)
**Severity:** LOW-MEDIUM — isolated to a single row, doesn't block anything else, but that row can never auto-resolve until fixed.

---

## What was found

Bala noticed `UUUU` (journal id 33, a `FWD_TEST:REJECT` position logged Session 30) shows nothing in the dashboard's live monitor view. Checked directly rather than assumed:

1. Pulled `/journal/history` — the row itself is intact (status OPEN, entry $1.485, target $2.376, stop $1.0395, contract "UUUU Aug 14 '26 13 Put").
2. Pulled `/journal/monitor` — 12 rows returned, id 33 is the only OPEN position missing from it.
3. Pulled UUUU's option quote directly from Tradier (`UUUU260814P00013000`) — it's live right now: bid $1.25 / ask $1.45, OI 233, real greeks returned. **Not a market-data gap.**
4. Compared `occ_symbol` across rows: every other position (ids 18, 22, 35, 39, etc.) stores the compact Tradier format, e.g. `NFLX260821P00070000` — root immediately followed by the date, no gap. **id 33 alone stores `'UUUU  260814P00013000'`** — two literal space characters between the root and the date (the OCC 6-character-padded convention, not Tradier's compact one).

## Why this breaks silently instead of erroring

`journal_monitor()` (`app.py:960-1038`) batches `occ_symbol` straight into a Tradier `/markets/quotes` query, then does `if not quote: continue` when a symbol doesn't come back in the response (Session 21 hardening — one bad quote must skip one row, never 500 the whole monitor). That skip logic is correct and shouldn't change. The problem is purely the input: Tradier never matches the padded symbol to anything, so it returns no quote, and the row silently drops out of the monitor view every time — indistinguishable from "genuinely no live quote" unless someone checks Tradier directly, which is what surfaced this.

**Same failure mode hits the hub's own `resolve_positions.py`:** it also keys quote lookups by `occ_symbol` verbatim. When it runs today's close-of-day check, it will report UUUU as `NO_QUOTE` — a false negative, not a real illiquidity finding — and will keep doing so every day until this is fixed.

## Proposed fix

A one-time, single-row data correction, not a code or schema change:

```sql
UPDATE trades SET occ_symbol = 'UUUU260814P00013000' WHERE id = 33;
```

Worth a quick check while in there: grep `trades.db` for any other `occ_symbol` values containing internal whitespace (`WHERE occ_symbol LIKE '% %'` or equivalent) — id 33 was only caught because Bala happened to look at the dashboard for this specific name. It's plausible other rows (FWD_TEST or not) constructed the same way have the same problem and just haven't been noticed yet.

## Not proposing

Any change to `journal_monitor`'s skip-on-missing-quote behavior — that's correct, intentional design (Session 21), and should stay exactly as-is. This is purely about one bad stored value, not the code that handles missing data.

## Verification once fixed

Standard practice for this project — we'll check the live result, not the summary:
1. `GET /journal/history`, confirm id 33's `occ_symbol` is now `UUUU260814P00013000` and every other field (entry_price, target_price, stop_loss, setup_context, contract_details) is untouched.
2. `GET /journal/monitor`, confirm id 33 now appears with real live Greeks/price.
3. Re-run `resolve_positions.py` and confirm it no longer reports `NO_QUOTE` for UUUU (it may report an actual STOP/TARGET/TIME/open — any of those is fine, the point is it gets a real answer instead of a false negative).
