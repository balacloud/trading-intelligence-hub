# Parked Ideas — Forward Test

> Ideas discussed, evaluated honestly, and deliberately not pursued yet — not because they're
> bad, but because they're not the right thing to build right now. Documented so a future
> session doesn't have to re-derive the reasoning, and doesn't accidentally re-litigate a
> decision without knowing it was already made.

---

## Idea 1 — A second forward-test branch: real IBKR paper-account order execution

**Proposed:** Jul 23, 2026 (Session 32 continuation). Bala's framing, worth stating precisely
since the first-pass analysis got it wrong: not "replace the current methodology," but **a
second, parallel branch** running alongside the existing one — real orders placed into an actual
IBKR paper trading account via the REST API (order placement confirmed to exist and work,
`POST /iserver/account/{accountId}/orders`, per `research/ibkr_rest_api_probe/`), not the live
account. Not a live-trading proposal.

### What it would genuinely fix

The protocol's own Guardrail 3(b) already documents a real artifact: because resolution only
checks once daily, realized outcomes systematically overshoot the nominal targets — confirmed
average TARGET hit is +76% not +60%, average STOP is -42% not -30%. Real IBKR paper bracket
orders would fire the instant price actually touches a level, not up to a day late. That's a
genuine, specific fix to a genuine, specific, already-documented problem.

### Why a *parallel* branch changes the analysis from a straight "no"

An earlier framing of this idea (same conversation, before Bala clarified it was meant as a
second branch) was evaluated as if it would *replace* the current methodology mid-experiment —
under that framing, it fails hard: the current test is at 15 SURVIVOR / 15 REJECT logged, and
switching resolution methodology partway through breaks the apples-to-apples comparison the
pre-registered statistical test depends on (the exact failure mode Session 27's real off-protocol
close incident already proved out). **A genuinely separate, parallel branch doesn't have this
problem** — it doesn't touch the existing data at all.

It also reframes a second objection from a weakness into a potential feature: paper-account
fills aren't obviously "more real" than the current mid-price-at-log-time assumption — broker
paper engines are a known, common source of over-optimistic fills (no real counterparty, no real
market impact). Run as a second branch instead of a replacement, that stops being a flaw and
becomes a genuine cross-check: if both branches point the same direction, that's stronger
evidence than either alone; if they diverge, *that itself* is a real, useful finding about how
much resolution methodology matters — something nobody currently knows.

### Why it's still parked, not built

Two things a parallel-branch framing does **not** fix:

1. **Doesn't touch the actual bottleneck.** The forward test's real constraint on reaching
   Checkpoint A (n≈30/group) is candidate-generation rate, not resolution mechanics — established
   directly with Bala the prior session. A second execution branch doesn't generate a single new
   candidate faster. It also inherits the exact same IVR-data gap the REST probe already proved
   out — Sieve 1 selection still needs the watchlist paste either way, regardless of how
   resolution happens downstream.
2. **Real added operational overhead**, for a project currently run through solo Claude Code
   sessions. A live paper-trading bot needs reliable order-placement, order-confirmation-reply
   handling (IBKR's REST order flow requires an additional confirmation-reply step, not just a
   fire-and-forget POST), position/order lifecycle tracking, and the same session-management
   burden the REST probe already hit firsthand (port conflicts, bundled-JRE workaround, ~15-20
   minute idle timeouts needing a `/tickle` loop) — but now needing to run reliably enough not to
   miss a fill or leave an orphaned order. Maintaining two live systems in parallel is a real cost
   that could slow the *primary* branch down by competing for the same limited session time,
   rather than speeding the overall test up.

**Where this actually belongs, if picked back up:** `FORWARD_TEST_PROTOCOL.md`'s existing
"Path to Live" section already lists "a real stop-loss mechanism" and "continuous risk
monitoring" as pre-live requirements, explicitly gated on Checkpoint A passing first. This idea
is essentially that work, arriving early. The natural trigger to revisit it: **after Checkpoint A**
(n≈30/group primary result), as part of the already-planned live-readiness track — not before.

**Verdict:** genuinely defensible design, wrong sequencing. Revisit post-Checkpoint-A, not before.
