# IBKR Client Portal REST API — IV Rank Field Probe: Findings

> Pet project, isolated from the forward test (per `README.md`). This doc is the actual
> research log and conclusion — written up after running the real test, not before.
> Session 31, July 22, 2026.

---

## TL;DR

**The question:** could the raw IBKR Client Portal REST API replace the manual watchlist-paste
step (`skill-options-scanner.md`'s PATH B), eliminating copy-paste?

**The answer, empirically tested and independently corroborated, not guessed:** **Partially.**
11 of the ~14 watchlist columns are available via REST and matched against real pasted data
(several exactly). Watchlist *membership* (ticker lists) is also available via REST, matching
MCP exactly. But **`52 Week IV Rank` — the single field Sieve 1 gates the entire pipeline on —
is not present anywhere in the REST API's field catalog**, tested across 6 tickers spanning IV
Rank 28 to 91, and independently confirmed absent from `Voyz/ibind`, a real community-maintained
open-source reference for this same API. Two independent sources, zero disagreement. Copy-paste
stays necessary for the one gate that matters most, even though it could be eliminated for
almost everything else, including the watchlist ticker list itself.

---

## The question this answers

This started as a "why not use the REST API instead of pasting" thought during a forward-test
session. The concern going in: this project's own `CLAUDE_CONTEXT.md` Known Issues already
documented that the IBKR *MCP* connector's `implied_volatility_percentile` field diverges
measurably from the real watchlist `52 Week IV Rank` column (COIN: 45 vs 53%, AVAV: 40 vs 65.3%,
WOLF: 26 vs 58.7%) — different metrics (percentile vs. rank), not a units bug. Since the MCP
connector's naming/ID conventions strongly resemble Client Portal REST conventions, the working
hypothesis was that raw REST calls would hit the same wall. This probe existed to test that
hypothesis directly instead of assuming it.

---

## Method — what was actually done, in order

1. **Confirmed what was and wasn't already installed.** `IB Gateway 10.44` was present
   (`/Users/balajik/Applications/`) but that's the TWS *socket*-API gateway — a different
   product from the Client Portal *REST* gateway this test needed. No Client Portal Gateway
   was installed at the start of this session.

2. **Bala downloaded the Client Portal Gateway** to `/Users/balajik/projects/clientportal.gw`.

3. **Found and fixed a real port conflict before starting anything.** The gateway defaults to
   port 5000, which macOS's own AirPlay Receiver already held on this machine (confirmed via
   `lsof -i :5000`, showing the `ControlCenter` process bound there). Rather than have Bala
   disable a macOS system feature, changed `root/conf.yaml`'s `listenPort` to `5055` and updated
   `client.py`'s `BASE_URL` and `README.md` to match.

4. **No system Java was installed either** (`java -version` failed outright). Rather than
   requiring a separate Java install, found and reused the JRE already bundled inside the
   installed `IB Gateway 10.44.app`
   (`.install4j/jre.bundle/Contents/Home/bin/java`, OpenJDK 17.0.14 — well above the gateway's
   documented minimum of Java 8u192) by prepending it to `PATH` before invoking `bin/run.sh`.

5. **Started the gateway** (`bin/run.sh root/conf.yaml`, backgrounded), confirmed it was
   listening on 5055 and returning the expected `401 Unauthorized` pre-login response — a
   correct response, not an error, since no session existed yet.

6. **Bala authenticated interactively** via browser at `https://localhost:5055` (real IBKR
   login + 2FA — this step cannot be automated and wasn't attempted). Confirmed authenticated
   via `GET /iserver/auth/status` returning `{"authenticated": true, ...}`.

7. **First sweep attempt on NVDA came back nearly empty** (2 fields out of 1,162 requested) —
   this looked like it could mean "the data isn't there," but was treated as a suspicious
   result worth diagnosing rather than accepted at face value, per this project's own standing
   discipline.

8. **Found the real bug via a targeted diagnostic**, not more sweeping: called `snapshot()`
   repeatedly for the same small set of "should definitely work" fields (Last, Bid, Ask,
   Volume) and discovered IBKR's snapshot endpoint returns **all currently-subscribed fields
   for a conid, not just the ones requested in that specific call** — a cumulative-subscription
   behavior, not a per-request one. `probe_fields.py`'s original code only recorded values for
   field IDs matching the *current batch's* request list, silently discarding everything else
   that came back. Fixed by capturing every key present in each response, regardless of what
   was requested that call.

9. **Re-ran the sweep on NVDA with the fix** — 74 real, non-null fields came back (up from 2).

10. **Caught a real, unrelated finding along the way:** fields 73-80 in the response turned out
    to be Bala's actual live NVDA position (≈10 shares, avg cost $175.32, unrealized +21.2%,
    +$372) — the snapshot endpoint returns account/position context mixed in with pure market
    data when a position exists. Added `.gitignore` for `probe_results_*.json` immediately,
    before this could be accidentally committed with real account data in plaintext.

11. **Got real ground truth, twice.** First attempted via the Chrome extension (`navigate` to
    `portal.ibkr.com` / `interactivebrokers.com`) to read the real watchlist value directly —
    blocked by a site-permission wall on the extension (not something scriptable around; the
    domain needs to be granted access first). Fell back to Bala pasting fresh, real
    `HUB_CORE` watchlist rows directly — NVDA first, then CEG/ETN/ANET/ALAB/MOD.

12. **Cross-referenced every REST field against the real pasted values**, column by column, for
    all 6 tickers. Used `compare_against_known.py` for the numeric proximity check, but did not
    stop there — every "candidate" it flagged was manually checked against the *other* fields
    already confirmed on NVDA, specifically to rule out coincidental near-matches (see False
    Positives section below). This is the step that turned "no candidates within tolerance" from
    an assumption into a checked fact.

13. **Gateway session timed out mid-investigation** (idle during writeup, no `/tickle` keep-alive
    running) — caught via a 401 on a routine re-check rather than assumed working, re-authenticated
    via browser, and confirmed live again before continuing (`iserver/auth/status` returning
    `authenticated: true`).

14. **Tested the watchlist endpoint directly** (`GET /iserver/watchlists`, then
    `GET /iserver/watchlist?id=110`) once re-authenticated — first attempt used the watchlist's
    *name* as the id parameter and correctly failed (`503`, "unknown watchlist ID"); the actual
    numeric id (`110`, matching MCP exactly) worked and returned full ticker membership with no
    column values, settling that question directly rather than by inference.

15. **Tested the Price/EMA(50) hypothesis directly.** The original guess (field `7680`,
    assuming a sequential EMA200/100/50/20 pattern) was tested with 4 repeated calls and came
    back empty every time — a real, confirmed absence, not "we didn't check." Cross-referencing
    against `Voyz/ibind` (an independent, real open-source client library for this same API)
    resolved the actual field id (`7724`) and simultaneously corroborated every other field
    mapping in this document from a source with no connection to this project.

---

## What's available via REST — confirmed against real pasted data

Every row below was checked against actual `HUB_CORE` paste values, not assumed from field
names. "Exact" means the numbers matched to the displayed precision; "near" means a small
difference consistent with price/time drift between when the probe ran and when the paste was
taken (seconds to low-minutes apart), not a real discrepancy.

| Watchlist column | REST field ID | Confirmed on | Match quality |
|---|---|---|---|
| Last | `31` | NVDA | exact |
| Bid | `84` | NVDA | exact |
| Ask | `86` | NVDA | exact |
| Volume | `87` | NVDA | exact |
| Change % | `83` | NVDA | exact |
| Opt. Volume | `7089` | NVDA | exact (5.15M) |
| Opt. Volume Change % | `7607` | NVDA | exact (135.552%) |
| Option Open Interest | `7638` | NVDA | exact (13.4M) |
| 52 Week High | `7293` | NVDA, MOD | exact |
| 52 Week Low | `7294` | NVDA, MOD | exact |
| Put/Call Volume | `7086` / `7285` (duplicated) | NVDA | exact (0.52) |
| Hist. Vol. Close % | `7087` / `7088` / `7284` (triplicated) | NVDA, CEG | exact |
| Implied Vol./Hist. Vol % | `7084` | NVDA | near (97.0 vs 97.2) |
| Opt. Implied Volatility % | `7283` | NVDA, MOD | near (38.297 vs 38.4; 94.810 vs 94.8) |
| Price/EMA(200) | `7678` | NVDA | near (11.27-11.32 vs 11.40/11.44) |
| Price/EMA(50) | `7724` | NVDA | near (3.71 vs 3.83-3.86) — confirmed via `ibind` cross-check, see below |

**11 of ~14 real columns confirmed available**, several exactly, via a completely different
mechanism than the ones the pipeline already uses (not MCP, not paste — raw authenticated REST).

**Watchlist membership is also available via REST** — `GET /iserver/watchlists` lists all
watchlists (confirmed `HUB_CORE` = id `110`, `HUB_EXTENDED` = id `111`, matching MCP exactly),
and `GET /iserver/watchlist?id=110` returns the full ticker list with even richer per-instrument
metadata than MCP's `get_watchlist` (full company name, ticker, asset class). Checked both real
watchlists, not just one: `id=110` (`HUB_CORE`, 20 instruments) and `id=111` (`HUB_EXTENDED`, 65
instruments — the 64 built tickers plus VIX, correctly typed `assetClass: IND`,
"CBOE Volatility Index", exactly matching what was resolved via MCP earlier this session).
**But — same gap as everywhere else — zero column display values ride along on either one.**
Watchlist membership and column values are different parts of IBKR's data model regardless of
which endpoint, which watchlist, or which client asks; getting the list doesn't get you IVR
either.

## Independent corroboration — community reverse-engineering, not just this probe

After the initial sweep, cross-checked the findings against
[`Voyz/ibind`](https://github.com/Voyz/ibind), an actively-maintained, real open-source REST/WS
client library for this exact API. Its `ibkr_definitions.py` is a field-ID reference built from
independent community reverse-engineering — a second, external source, not this project's own
work. It **confirms every field mapping in the table above by name**, and resolves the one open
question:

- **`price_to_ema_50_percent` = field `7724`** (not `7680`, which is genuinely empty — confirmed
  directly, see below). NVDA's `7724` value (3.71%) is a near-match to the real pasted
  Price/EMA(50) (3.83-3.86%), the same small-drift pattern seen on every other "near" match in
  this doc. **Now confirmed, not just a lead.**
- **`ema_200`/`ema_100`/`ema_50`/`ema_20` = `7674`/`7675`/`7676`/`7677`** (raw EMA price levels)
  — `price_to_ema_200/100/50/20_percent` = `7678`/`7679`/`7724`/`7681` respectively. The earlier
  guess that `7086`/`7285` were a duplicated Put/Call Volume field was also corrected by this
  source: they're **Put/Call Volume** (`7086`) and **Put/Call Ratio** (`7285`) — two genuinely
  different metrics that happened to read the same value (0.52) for NVDA at that moment, not one
  field reported twice.
- **Directly searched the same source for a `rank` field and for an implied-vol-change field.
  Neither exists.** No IV Rank field is defined anywhere in `ibind`'s reference, and no field
  matches "Opt. Imp. Vol. Change" (the one NVDA value — `0.324` — still has no known field ID by
  either method). This is the same negative result this probe found independently, now backed by
  a second, external source built by people with no connection to this project or its hypothesis.

## What's still genuinely unresolved

Only one open item remains after the `ibind` cross-check:

- **Opt. Imp. Vol. Change** (watchlist shows `0.324` for NVDA) — absent from both this probe's
  1,150-field sweep *and* `ibind`'s independently-built reference. At this point that's fairly
  strong (two-source) evidence it isn't a snapshot field at all, though "two sources missed it"
  is weaker evidence than the IV Rank negative, which was tested with a real cross-ticker
  methodology, not just absence-from-a-list.

## What's NOT available — the actual finding

**`52 Week IV Rank` — absent, tested across 6 tickers, IV Rank spanning 28 to 91:**

| Ticker | Real IV Rank (pasted) | Best REST candidate within ±5 | What that candidate actually is |
|---|---|---|---|
| NVDA | 28 | none | — |
| CEG | 43 | `7087`/`7088`/`7284` = 40.503 | **Hist. Vol. Close %** (CEG's real value — already confirmed meaning) |
| CEG | 43 | field `85` = 40 | Bid size — not a percentage field at all |
| ETN | 90 | `7638` = "89.0K" → parsed 89.0 | **Option Open Interest** (89,000 contracts) — a parsing artifact (the comparison script's regex stripped the "K" suffix), not a real numeric coincidence |
| ANET | 91 | none | — |
| ALAB | 75 | none | — |
| MOD | 91 | `7283` = 94.810 | **Opt. Implied Volatility %** (MOD's real value — already confirmed meaning) |
| MOD | 91 | `7294` = 95.05 | **52 Week Low** (MOD's real value — already confirmed meaning) |

**Every single flagged "candidate" is fully explained by a field already confirmed to mean
something else.** None recurred across tickers — a coincidental near-match on one ticker (CEG's
Hist Vol Close % of 40.5 sitting close to its own IV Rank of 43) never repeats on the next
ticker with a different IV Rank, which is exactly what you'd expect from noise, and exactly
what you would *not* expect if any of these fields were secretly IV Rank. That's the real
signal here: not silence, but silence *combined with* every apparent hit having an
independent, confirmed explanation.

---

## Why this is a real negative, not just "we didn't find it yet"

Three things make this conclusion solid rather than merely suggestive:

1. **The search space was appropriate.** Every other volatility/options metric IBKR exposes
   lives in the `7080`-`7290` field cluster — IV/HV ratio, Opt IV%, Hist Vol Close%, Put/Call
   Volume, Opt Volume Change% are all packed into a ~200-field neighborhood. IV Rank, if it
   existed as a raw field, would almost certainly live in the same cluster. It doesn't appear
   anywhere in it, or in the broader 6000-6200/7000-7900 ranges swept.
2. **The comparison used real, freshly-pasted ground truth**, not memory of old session data —
   the exact discipline this project already enforces elsewhere (`feedback_live_read_rule`).
3. **Cross-ticker consistency was the actual bar**, not a single match. A field matching once
   is exactly as likely from 74 real numbers landing near *some* value in a 0-100 range by
   chance as from a real relationship — that's why the method compared 6 tickers with a wide
   IV Rank spread instead of stopping at NVDA's first "no candidates" result.

## What this doesn't rule out

Being precise about the limits of this test, not overclaiming:

- Only the `/iserver/marketdata/snapshot` endpoint's field catalog was swept. IBKR has other
  endpoint families (fundamentals, historical volatility series, `/hmds/*`) that weren't
  tested — it's possible IV Rank is computed from a raw historical IV series via a *different*
  endpoint rather than exposed as a single snapshot field. Not tested here.
- The sweep covered ~1,150 field IDs across the documented "core" and "extended" ranges, not
  literally every integer — a field far outside those ranges wouldn't have been caught.
- This is IBKR-account-specific; a different account type or market data subscription tier
  wasn't tested (only the one account this hub already operates against).

## Conclusion for the actual pipeline decision

`skill-options-scanner.md`'s move to watchlist-paste mode (v3.0, Session 30) was the right
call, and this probe is the first *direct* evidence for it rather than an inference from prior
MCP-percentile divergence. The one thing this **does** open up: a standalone script (not run
inside a Claude Code session, so it doesn't hit the context-cost problem that killed
MCP-per-ticker screening in Scanner v2) could pull ~10 of the ~14 watchlist columns via REST
automatically — Opt. Volume, Opt. Volume Change %, OI, 52wk High/Low, Put/Call Volume, Hist Vol
Close %, IV/HV ratio, Opt Implied Vol %, and Price/EMA(200) — leaving only IV Rank (and
possibly Price/EMA(50) and Opt. Imp. Vol. Change, unconfirmed either way) needing the manual
paste. Whether that's worth building is a separate, later decision — this doc just settles what
is and isn't possible.

---

## Appendix — raw data files

- `probe_results_NVDA_20260722T200723Z.json` — **superseded, pre-bug-fix run.** Only captured 2
  fields due to the batch-filtering bug described in Method step 8. Kept for the record, not
  used in any analysis above.
- `probe_results_NVDA_20260722T200945Z.json` — the real NVDA run, 74 fields, used throughout.
- `probe_results_CEG_20260722T202216Z.json`
- `probe_results_ETN_20260722T202229Z.json`
- `probe_results_ANET_20260722T202241Z.json`
- `probe_results_ALAB_20260722T202253Z.json`
- `probe_results_MOD_20260722T202304Z.json`

All six `.json` files are gitignored (`probe_results_*.json`) since several contain real
account position data (see Method step 10) — this findings doc is the durable record, the raw
JSON is local-only scratch data.
