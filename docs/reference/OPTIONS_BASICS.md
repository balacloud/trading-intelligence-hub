# Options Basics — Reference

> Saved Aug 2, 2026 (Session 40 continuation), from a review of Bala's own beginner options-trading lesson (Infosys worked example). This is **execution mechanics** — how to structure a trade cheaply and correctly once you already have a market view. It is **not edge** — nothing here tells you whether your market view is right more often than a coin flip. See the closing note; that distinction is the whole point of saving this doc.

---

## 1. The four basic views → four basic actions

| Market view | Action | What you're betting |
|---|---|---|
| Extremely bullish | Buy call | Price rises significantly |
| Extremely bearish | Buy put | Price falls significantly |
| Neutral to bearish | Sell call | Price stays below a level (resistance) |
| Neutral to bullish | Sell put | Price stays above a level (support) |

**Important correction to a common beginner mix-up:** calls are not "for bullish traders" and puts are not "for bearish traders." Both can be bought *or* sold — it's the combination of (call/put) × (buy/sell) that sets the view, not the option type alone.

| | Buy | Sell |
|---|---|---|
| **Call** | Bullish | Neutral to bearish |
| **Put** | Bearish | Neutral to bullish |

## 2. Debit vs. credit

- **Buying an option = debit.** You pay the premium up front. You hold a right, not an obligation.
- **Selling an option = credit.** You collect the premium up front. You accept an obligation if exercised/assigned.
- Every contract has a buyer and a seller on the other side — it's a matched agreement, not something created from nothing.

## 3. You don't have to hold to expiry

Most positions are closed by doing the opposite transaction before expiration — bought a call → sell the same call; sold a put → buy back the same put. The closing trade must match on underlying, strike, expiry, and call/put type. A lot of beginners wrongly assume they must wait until expiry or exercise.

## 4. Intrinsic value and extrinsic value

**Call intrinsic value** = `max(Spot − Strike, 0)`
**Put intrinsic value** = `max(Strike − Spot, 0)`

Intrinsic value answers: *"what would this be worth if it expired right now?"* It can never be negative — that's what the `max(..., 0)` does.

**Extrinsic value** = `Option premium − Intrinsic value`

Extrinsic value is everything the market is paying for that isn't already-locked-in value: time remaining, implied volatility, expected events, uncertainty. It trends toward zero as expiry approaches (**theta decay**), all else held equal — "all else equal" is doing real work in that sentence; the underlying moving, IV changing, or an event landing can all move premium too.

## 5. ITM / ATM / OTM

- **In the money (ITM):** has intrinsic value (call: spot > strike; put: spot < strike)
- **At the money (ATM):** strike ≈ current price — little/no intrinsic value, high extrinsic value, high sensitivity to time and volatility
- **Out of the money (OTM):** no intrinsic value at all (call: strike > spot; put: strike < spot)

**Trade-off, not a rule:** ITM costs more but is less purely a time-value bet. ATM/OTM is cheaper with more leverage but decays faster and is more binary. Neither is universally "correct" for buyers or sellers — it depends on premium, probability, delta, and how much directional risk you actually want.

## 6. Implied volatility (IV) — what it actually is

IV is **inferred from the option's market price**, not computed directly from a list of events. The real process: observe the market price → plug known inputs (spot, strike, time to expiry, rate, dividends) into a pricing model → solve for the volatility value that makes the model price match the market price → that solved number is IV.

Events (earnings, M&A, macro shocks) don't get typed into an IV formula — they change *demand and uncertainty*, which moves the option's *price*, and IV is the number you back out of that price afterward. Worth being precise about this distinction; it's easy to say "IV is high because of earnings" as if IV is the cause rather than the readout.

## 7. Expiry selection — sellers vs. buyers, with the caveat left in

- **Shorter expiry for sellers:** decays faster (more theta collected sooner) — but also carries **more gamma risk**, less time to recover from an adverse move, and more gap/event risk. Not automatically "safer."
- **Longer expiry for buyers:** more time for the thesis to play out, gentler daily theta — but costs more premium and ties up capital longer.

Neither rule is a guarantee. They describe a trade-off, not a law.

## 8. Worked example — Infosys

Spot ₹1,713, resistance ~₹1,789, support ~₹1,664.

| Contract | Premium | Intrinsic | Extrinsic | Breakeven at expiry |
|---|---:|---:|---:|---:|
| Buy 1660 CE (extremely bullish) | ₹64.05 | ₹53.00 | ₹11.05 | Strike + premium = ₹1,724.05 |
| Buy 1800 PE (extremely bearish) | ₹85.00 | ₹87.00* | — | Strike − premium = ₹1,715.00 |
| Sell 1800 CE (neutral to bearish) | ₹3.40 | ₹0 | ₹3.40 | Strike + premium = ₹1,803.40 |
| Sell 1660 PE (neutral to bullish) | ₹6.70 | ₹0 | ₹6.70 | Strike − premium = ₹1,653.30 |

*\*Flagged in the original review: a premium of ₹85 quoted against a calculated intrinsic value of ₹87 is an inconsistency under normal market conditions (an option shouldn't trade materially below its own intrinsic value except for stale quotes/timing/bid-ask noise). Treat this specific pair of numbers as illustrative of the formula, not as a verified real market snapshot — the formula is right, the two input numbers don't reconcile.*

**The short-call risk this example didn't spell out, and should:** "sell the call above resistance" is not automatically low-risk just because resistance is a sensible level. Resistance can fail. An uncovered short call carries theoretically unlimited loss above the breakeven — the technical level supports the *thesis*, it does not *cap the risk*.

## 9. What this lesson doesn't cover yet — needed before trading real size

- **Max profit / max loss / breakeven** stated explicitly for every position, not just breakeven.
- **Naked vs. covered calls, cash-secured vs. naked puts** — same "sell a call" instruction means very different risk depending on whether shares are actually held or margin is backing it.
- **Lot size.** Quoted premium × lot size = real cost/credit. A ₹64.05 premium is not a ₹64.05 trade.
- **Assignment and settlement** — cash vs. physical, automatic exercise rules.
- **The Greeks** — delta (directional sensitivity), theta (time decay), vega (volatility sensitivity), gamma (rate of change of delta), rho (rate sensitivity).
- **Real transaction costs** — brokerage, fees, taxes, slippage, bid/ask spread. These quietly eat any small edge that exists.

---

## The one thing worth remembering above all the mechanics

This document teaches **how to execute a market view** cheaply and correctly. It does not tell you **whether your market view is right** more often than random. Support and resistance are visible to every other trader looking at the same chart — if "buy calls at support" reliably worked just because it's a sensible-sounding rule, it would already be priced away. Knowing intrinsic value, extrinsic value, IV, and strike selection perfectly prevents unforced execution errors — it does not, by itself, create edge.

The actual answer to "how do I make good decisions without a proven edge" is downstream of this doc, not inside it: **position sizing, defined risk, and honest outcome tracking** — trade small and consistent, use defined-risk structures instead of naked exposure, and let real results (not a well-argued story) decide when to size up. This is the same discipline the hub's own forward test, kill-switch, and bounded-pilot design already exist to enforce — see `FORWARD_TEST_PROTOCOL.md`'s Path to Live section and `TRADER_LENS.md`.
