# IBKR Client Portal REST API — Portable Reference

> **For any project integrating IBKR's REST API directly** — written so `swing-trade-analyzer`
> (STA) or `options_iq_gemini` can pick this up without needing context from
> `trading-intelligence-hub`'s own pipeline, forward test, or session history. This is a
> technical reference, not a research log — see `FINDINGS.md` in this same folder for the full
> investigation this was distilled from, if you want the evidence trail.
>
> Everything here was empirically tested against a live account, not assumed from docs (IBKR's
> own field-reference docs are frequently paywalled/incomplete — see Setup Gotchas). Field IDs
> were also cross-checked against [`Voyz/ibind`](https://github.com/Voyz/ibind), an independent
> open-source client library, wherever possible.

---

## What this is

The **Client Portal Gateway** is a small local Java REST proxy IBKR provides — you run it, log
in once via browser, and it exposes `https://localhost:<port>/v1/api/...` for the lifetime of
that session. It's a *different product* from `IB Gateway` (the TWS-style socket gateway) —
don't confuse the two if both show up installed on a machine.

---

## Setup — the parts that aren't in IBKR's own docs

1. **Download:** `clientportal.gw.zip` from IBKR's API page (not `IB Gateway` — different
   product, same-ish name).
2. **Port conflict, real and common on Mac:** the gateway defaults to port 5000, which macOS's
   own AirPlay Receiver already holds by default. Rather than disable a system feature, change
   `root/conf.yaml`'s `listenPort` to something else (we used `5055`) before first start.
3. **No system Java required if you already have `IB Gateway` installed** — it bundles its own
   JRE (found at `<IB Gateway install>/.install4j/jre.bundle/Contents/Home/bin/java` on macOS,
   confirmed OpenJDK 17, well above the gateway's documented Java 8u192+ minimum). Prepend that
   to `PATH` before running `bin/run.sh root/conf.yaml` instead of installing a separate JRE.
4. **Start:** from the gateway's root directory, `bin/run.sh root/conf.yaml` (exact invocation
   per IBKR's own `doc/GettingStarted.md` — don't run from `bin/`, run from the gateway root).
5. **Authenticate:** open `https://localhost:<port>` in a browser (expect a self-signed-cert
   warning, click through it), log in with real IBKR credentials + 2FA. **This step is always
   interactive — cannot be automated or scripted.** Confirm success:
   `GET /iserver/auth/status` → `{"authenticated": true, ...}`.
6. **Sessions time out on idle** (no fixed published duration — we hit a timeout after roughly
   15-20 minutes of inactivity mid-investigation). Call `POST /tickle` periodically during any
   long-running process, or expect to catch `401`s and re-authenticate via browser.

---

## The one bug you will hit if you write your own field sweep — save yourself the debugging

**IBKR's `/iserver/marketdata/snapshot` returns *all currently-subscribed* fields for a conid,
not just the fields requested in that specific call.** Subscriptions accumulate server-side per
conid across calls within a session. If your code only records values for field IDs matching
what it explicitly requested in that call (the obvious, wrong way to write it), you will
silently discard most of the real data and conclude fields are missing when they aren't. Record
every key present in the response, not just the ones your request asked for.

Corollary: the **first** snapshot call for a conid in a session often returns sparse/empty data
— the subscription needs a moment to "warm up." Don't trust a single call; call again (or just
build your accumulator to run several batches, since the accumulation itself does the warming).

---

## Confirmed field ID → meaning

Every mapping below was checked against real, live, freshly-pasted IBKR watchlist data (not
assumed from a name), for tickers spanning a wide range of values — not just one. "Exact" means
the numbers matched to displayed precision at the time of comparison; small drift on "near"
matches is normal price movement between when each side was read, not a real discrepancy.

| Field ID | Meaning | Confirmed via |
|---|---|---|
| `31` | Last Price | direct match |
| `55` | Symbol | direct match |
| `70` / `71` | Today's High / Low | direct match |
| `82` / `83` | Change $ / Change % | direct match |
| `84` / `85` | Bid / Bid Size | direct match |
| `86` / `88` | Ask / Ask Size | direct match |
| `87` | Volume | direct match |
| `6070` | Security Type | direct match |
| `7051` | Company Name | direct match |
| `7084` | **Implied Vol./Hist. Vol %** (IV/HV ratio) | exact, cross-checked `ibind` |
| `7085` | Put/Call Interest | named in `ibind`, not independently value-checked |
| `7086` | **Put/Call Volume** | exact match, cross-checked `ibind` |
| `7087` | Hist. Vol. % (30-day) | exact, cross-checked `ibind` |
| `7088` | **Hist. Vol. Close %** | exact, cross-checked `ibind` |
| `7089` | Opt. Volume | exact match |
| `7283` | **Opt. Implied Volatility %** | near match, cross-checked `ibind` |
| `7284` | duplicate of `7087`/`7088` (same value observed) | exact match |
| `7285` | **Put/Call Ratio** (distinct metric from `7086`, can coincidentally read the same value) | cross-checked `ibind` |
| `7293` / `7294` | 52 Week High / Low | exact match |
| `7607` | **Opt. Volume Change %** | exact match, cross-checked `ibind` |
| `7633` | Implied Vol. % (per-strike, option-level) | named in `ibind`, not independently value-checked |
| `7638` | Option Open Interest | exact match |
| `7674` / `7675` / `7676` / `7677` | Raw EMA levels: EMA(200) / EMA(100) / EMA(50) / EMA(20) | cross-checked `ibind` |
| `7678` | **Price/EMA(200) %** | near match, cross-checked `ibind` |
| `7679` | Price/EMA(100) % | cross-checked `ibind` |
| `7681` | Price/EMA(20) % | cross-checked `ibind` |
| `7724` | **Price/EMA(50) %** (not sequential with the others — don't assume `7680`) | near match, cross-checked `ibind` |
| `7308`-`7311` | Option Greeks: delta / gamma / theta / vega | named in `ibind`, not independently value-checked here — this project sources Greeks from Tradier instead |

**Confirmed empty/nonexistent:** `7680` (tested directly, 4 repeated calls, always absent — do
not assume it's EMA(50)'s ratio field just because it sits between confirmed neighbors).

## Confirmed NOT available via this API at all

**`52 Week IV Rank`** — the standard `(current IV − 52wk low IV) / (52wk high IV − 52wk low IV)
× 100` metric, as displayed in TWS/Client Portal's own watchlist UI. Tested directly across 6
tickers spanning real IV Rank values 28-91; no field anywhere in the documented snapshot field
catalog (~1,150 IDs swept across the ranges where every sibling volatility metric lives)
correlates with it. Independently confirmed absent from `ibind`'s reference too — two unrelated
sources, same negative result.

**Update (Session 35, Jul 26 2026): the field ID itself is now known — `fix_tag: 7195`.**
A third community source, `areed1192/interactive-broker-python-api` (an unofficial Python
client library explicitly for *this same Client Portal Web API*, not the separate TWS socket
API — verified by reading its own README), documents field 7195 as "52 Week IV Rank" with the
exact calculation formula matching. This ID **was inside the swept range** (`7000-7900`) and
**was genuinely requested** in the original sweep — confirmed by re-checking the saved raw
response JSON (`probe_results_*.json`) for 5 tickers with known real IV Rank values (CEG 40,
ETN 86, ANET 85, ALAB 75, MOD 88): field `7195` does not appear in any raw batch response at
all, not even as a null value — IBKR's snapshot endpoint omits fields it has no data for rather
than returning them as null, so this is consistent with either "doesn't exist for this account"
or "exists but gated behind an entitlement this account didn't have on Jul 22, 2026."

This changes what's actually still open: **it's no longer "no candidate field was ever found" —
it's "the real field ID is known, was queried, and came back empty on that day's subscription
state."** Bala's current Market Data Subscriptions (checked live, Jul 26 2026) include a paid
**US Equity and Options Add-On Streaming Bundle (NP)** — not confirmed whether this was active
on Jul 22 when the probe ran, or whether it's even the right bundle for field 7195 specifically.
Worth a direct question to IBKR support rather than re-guessing, and worth an actual re-probe
(`fields=7195` specifically) once the local gateway is running again — cheaper and more
conclusive than either.

**Why the metric is hard to expose generally (still likely true, independent of the entitlement
question):** IV Rank requires a full 52-week *history* of daily IV readings to compute, and
neither this REST API's other endpoints nor Tradier's API (also checked, see below) expose
historical implied volatility as a time series — both only expose current/snapshot IV. If field
7195 turns out to be genuinely inaccessible via REST regardless of subscription, this remains
the likely structural reason why.

**Also checked and same result: Tradier's API.** `bid_iv` / `mid_iv` / `ask_iv` / `smv_vol` are
real, current per-contract IV (via ORATS) — same category of data as IBKR's REST fields, not a
rank. No `iv_rank` field in Tradier's documented options-chain schema either.

**Watchlist membership works, but doesn't help here either:** `GET /iserver/watchlists` (list)
and `GET /iserver/watchlist?id=<numeric id>` (contents) both work cleanly — real ticker lists,
richer metadata than most MCP-style wrappers give you. But watchlist membership and watchlist
*column display values* are different parts of IBKR's data model. Getting the list doesn't get
you any of the columns above, IV Rank included.

---

## For `options_iq_gemini` specifically

Your own `app.py:651` sentinel comment on `GET /scan/universal` (`"iv_rank": 0, # Sentinel:
Manual verification needed via Hub`) — this reference confirms *why*, with direct evidence, not
just an assumption written at the time: IV Rank genuinely isn't available through IBKR's REST
API by any field this probe or `ibind`'s independent reference could find. Wiring a real IVR
check into that endpoint would need a different data source entirely (a paid vol-data provider
like ORATS' own IV Rank product, or accumulating your own daily-IV history) — not just more
careful use of IBKR's existing REST/MCP surface. If you pursue a fix, that's the actual
constraint to design around.

## For `swing-trade-analyzer` specifically

If STA's own IBKR REST integration proposal (reviewed the same day this probe was run) moves
forward: the field IDs above are directly reusable for STA's `Broker.get_snapshot()` /
`get_price_history()` implementation — no need to re-discover them. The cumulative-subscription
gotcha above will bite STA's own sweep code identically if not designed around from the start.
And if STA's own filter criteria ever wants IV Rank specifically (none of its documented 10
SEPA/CAN SLIM filters currently do, as of this writing) — this doc already has the answer: it
isn't available this way, budget for an alternative source from the start rather than
discovering the gap after building around it.
