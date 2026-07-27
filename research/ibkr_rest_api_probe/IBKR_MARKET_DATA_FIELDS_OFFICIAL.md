# IBKR Web API — Official Market Data Fields Reference

> **Source:** https://ibkrcampus.com/docs/web-api/web-api-v-1-0-documentation/endpoints/market-data/market-data-fields
> (append `.md` to any ibkrcampus.com docs URL for clean Markdown; full doc index at https://ibkrcampus.com/docs/llms.txt; MCP server at https://ibkrcampus.com/docs/_mcp/server)
> **Saved:** July 27, 2026 (Session 36) — pasted verbatim by Bala from IBKR's own canonical page, after IBKR support (Steve D., human agent) pointed at this exact URL to confirm which fields are actually documented for `research/ibkr_rest_api_probe/`'s IV Rank investigation.
> **Purpose:** Raw reference copy of IBKR's documented field table, kept locally so future sessions don't need a live fetch to check a field ID. This is the primary-source list — see `IBKR_REST_API_REFERENCE.md` for this hub's own probe results, findings, and the IV Rank investigation built on top of it. **Not necessarily the full table** — this is what was pasted into the session, not a guaranteed complete re-fetch of every field IBKR documents on that page.

---

# Market Data Fields

| Field | Return Type | Value | Description |
| ----- | ----------- | ----- | ----------- |
| 31 | string | Last Price | The last price at which the contract traded. May contain one of the following prefixes: C – Previous day's closing price. H – Trading has halted. |
| 55 | string | Symbol | |
| 58 | string | Text | |
| 70 | string | High | Current day high price |
| 71 | string | Low | Current day low price |
| 73 | string | Market Value | The current market value of your position in the security. Market Value is calculated with real time market data (even when not subscribed to market data). |
| 74 | string | Avg Price | The average price of the position. |
| 75 | string | Unrealized PnL | Unrealized profit or loss. Unrealized PnL is calculated with real time market data (even when not subscribed to market data). |
| 76 | string | Formatted position | |
| 77 | string | Formatted Unrealized PnL | |
| 78 | string | Daily PnL | Your profit or loss of the day since prior close. Daily PnL is calculated with real time market data (even when not subscribed to market data). |
| 79 | string | Realized PnL | Realized profit or loss. Realized PnL is calculated with real time market data (even when not subscribed to market data). |
| 80 | string | Unrealized PnL % | Unrealized profit or loss expressed in percentage. |
| 82 | string | Change | The difference between the last price and the close on the previous trading day |
| 83 | string | Change % | The difference between the last price and the close on the previous trading day in percentage. |
| 84 | string | Bid Price | The highest-priced bid on the contract. |
| 85 | string | Ask Size | The number of contracts or shares offered at the ask price. |
| 86 | string | Ask Price | The lowest-priced offer on the contract. |
| 87 | string | Volume | Volume for the day, formatted with 'K' for thousands or 'M' for millions. For higher precision volume refer to field 7762. |
| 88 | string | Bid Size | The number of contracts or shares bid for at the bid price. |
| 201 | string | Right | Returns the right of the instrument, such as P for Put or C for Call. |
| 6004 | string | Exchange | |
| 6008 | integer | Conid | Contract identifier from IBKR's database. |
| 6070 | string | SecType | The asset class of the instrument. |
| 6072 | string | Months | |
| 6073 | string | Regular Expiry | |
| 6119 | string | Marker for market data delivery method (similar to request id) | |
| 6457 | integer | Underlying Conid. Use /trsrv/secdef to get more information about the security | |
| 6508 | string | Service Params. | |
| 6509 | string | Market Data Availability. The field may contain three chars. First char defines: R = RealTime, D = Delayed, Z = Frozen, Y = Frozen Delayed, N = Not Subscribed, i – incomplete, v – VDR Exempt (Vendor Display Rule 603c). Second char defines: P = Snapshot, p = Consolidated. Third char defines: B = Book. RealTime | Data is relayed back in real time without delay, market data subscription(s) are required. Delayed – Data is relayed back 15-20 min delayed. Frozen – Last recorded data at market close, relayed back in real time. Frozen Delayed – Last recorded data at market close, relayed back delayed. Not Subscribed – User does not have the required market data subscription(s) to relay back either real time or delayed data. Snapshot – Snapshot request is available for contract. Consolidated – Market data is aggregated across multiple exchanges or venues. Book – Top of the book data is available for contract. |
| 7051 | string | Company name | |
| 7057 | string | Ask Exch | Displays the exchange(s) offering the SMART price. A=AMEX, C=CBOE, I=ISE, X=PHLX, N=PSE, B=BOX, Q=NASDAQOM, Z=BATS, W=CBOE2, T=NASDAQBX, M=MIAX, H=GEMINI, E=EDGX, J=MERCURY |
| 7058 | string | Last Exch | Displays the exchange(s) offering the SMART price. A=AMEX, C=CBOE, I=ISE, X=PHLX, N=PSE, B=BOX, Q=NASDAQOM, Z=BATS, W=CBOE2, T=NASDAQBX, M=MIAX, H=GEMINI, E=EDGX, J=MERCURY |
| 7059 | string | Last Size | The number of unites traded at the last price |
| 7068 | string | Bid Exch | Displays the exchange(s) offering the SMART price. A=AMEX, C=CBOE, I=ISE, X=PHLX, N=PSE, B=BOX, Q=NASDAQOM, Z=BATS, W=CBOE2, T=NASDAQBX, M=MIAX, H=GEMINI, E=EDGX, J=MERCURY |
| 7084 | string | Implied Vol./Hist. Vol % | The ratio of the implied volatility over the historical volatility, expressed as a percentage. |
| 7085 | string | Put/Call Interest | Put option open interest/call option open interest for the trading day. Only available for Underlying contracts. |
| 7086 | string | Put/Call Volume | Put option volume/call option volume for the trading day. |
| 7087 | string | Hist. Vol. % | 30-day real-time historical volatility. |
| 7088 | string | Hist. Vol. Close % | Shows the historical volatility based on previous close price. |
| 7089 | string | Opt. Volume | Option Volume |
| 7094 | string | Conid + Exchange | |
| 7184 | string | canBeTraded | If contract is a trade-able instrument. Returns 1(true) or 0(false). |
| 7219 | string | Contract Description | |
| 7220 | string | Contract Description | |
| 7221 | string | Listing Exchange | |
| 7280 | string | Industry | Displays the type of industry under which the underlying company can be categorized. |
| 7281 | string | Category | Displays a more detailed level of description within the industry under which the underlying company can be categorized. |
| 7282 | string | Average Volume | The average daily trading volume over 90 days. |
| 7283 | string | Option Implied Vol. % | A prediction of how volatile an underlying will be in the future. At the market volatility estimated for a maturity thirty calendar days forward of the current trading day, and based on option prices from two consecutive expiration months. To query the Implied Vol. % of a specific strike refer to field 7633. |
| 7284 | string | Historical volatility % | Deprecated, see field 7087 |
| 7285 | string | Put/Call Ratio | |
| 7292 | string | Cost Basis | Your current position in this security multiplied by the average price and multiplier. |
| 7293 | string | 52 Week High | The highest price for the past 52 weeks. |
| 7294 | string | 52 Week Low | The lowest price for the past 52 weeks. |
| 7295 | string | Open | Today's opening price. |
| 7296 | string | Close | Today's closing price. |
| 7308 | string | Delta | The ratio of the change in the price of the option to the corresponding change in the price of the underlying. |
| 7309 | string | Gamma | The rate of change for the delta with respect to the underlying asset's price. |
| 7310 | string | Theta | A measure of the rate of decline the value of an option due to the passage of time. |
| 7311 | string | Vega | The amount that the price of an option changes compared to a 1% change in the volatility. |
| 7607 | string | Opt. Volume Change % | Today's option volume as a percentage of the average option volume. |
| 7633 | string | Implied Vol. % | The implied volatility for the specific strike of the option in percentage. To query the Option Implied Vol. % from the underlying refer to field 7283. |
| 7635 | string | Mark | The mark price is, the ask price if ask is less than last price, the bid price if bid is more than the last price, otherwise it's equal to last price. |
| 7636 | string | Shortable Shares | Number of shares available for shorting. |
| 7637 | string | Fee Rate | Interest rate charged on borrowed shares. |
| 7638 | string | Option Open Interest. Available for Underlyings and Call & Put options. | |
| 7639 | string | % of Mark Value | Displays the market value of the contract as a percentage of the total market value of the account. Mark Value is calculated with real time market data (even when not subscribed to market data). |
| 7644 | string | Shortable | Describes the level of difficulty with which the security can be sold short. |
| 7671 | string | Dividends | This value is the total of the expected dividend payments over the next twelve months per share. |
| 7672 | string | Dividends TTM | This value is the total of the expected dividend payments over the last twelve months per share. |
| 7674 | string | EMA(200) | Exponential moving average (N=200). |
| 7675 | string | EMA(100) | Exponential moving average (N=100). |
| 7676 | string | EMA(50) | Exponential moving average (N=50). |
| 7677 | string | EMA(20) | Exponential moving average (N=20). |
| 7678 | string | Price/EMA(200) | Price to Exponential moving average (N=200) ratio -1, displayed in percents. |
| 7679 | string | Price/EMA(100) | Price to Exponential moving average (N=100) ratio -1, displayed in percents. |
| 7724 | string | Price/EMA(50) | Price to Exponential moving average (N=50) ratio -1, displayed in percents. |
| 7681 | string | Price/EMA(20) | Price to Exponential moving average (N=20) ratio -1, displayed in percents. |
| 7682 | string | Change Since Open | The difference between the last price and the open price. |
| 7683 | string | Upcoming Event | Shows the next major company event. Requires Wall Street Horizon subscription. |
| 7684 | string | Upcoming Event Date | The date of the next major company event. Requires Wall Street Horizon subscription. |
| 7685 | string | Upcoming Analyst Meeting | The date and time of the next scheduled analyst meeting. Requires Wall Street Horizon subscription. |
| 7686 | string | Upcoming Earnings | The date and time of the next scheduled earnings/earnings call event. Requires Wall Street Horizon subscription. |
| 7687 | string | Upcoming Misc Event | The date and time of the next shareholder meeting, presentation or other event. Requires Wall Street Horizon subscription. |
| 7688 | string | Recent Analyst Meeting | The date and time of the most recent analyst meeting. Requires Wall Street Horizon subscription. |
| 7689 | string | Recent Earnings | The date and time of the most recent earnings/earning call event. Requires Wall Street Horizon subscription. |
| 7690 | string | Recent Misc Event | The date and time of the most recent shareholder meeting, presentation or other event. Requires Wall Street Horizon subscription. |
| 7694 | string | Probability of Max Return | Customer implied probability of maximum potential gain. |
| 7695 | string | Break Even | Break even points |
| 7696 | string | SPX Delta | Beta Weighted Delta is calculated using the formula; Delta x dollar adjusted beta, where adjusted beta is adjusted by the ratio of the close price. |
| 7697 | string | Futures Open Interest | Total number of outstanding futures contracts |
| 7698 | string | Last Yield | Implied yield of the bond if it is purchased at the current last price. Last yield is calculated using the Last price on all possible call dates. It is assumed that prepayment occurs if the bond has call or put provisions and the issuer can offer a lower coupon rate based on current market rates. The yield to worst will be the lowest of the yield to maturity or yield to call (if the bond has prepayment provisions). Yield to worse may be the same as yield to maturity but never higher. |
| 7699 | string | Bid Yield | Implied yield of the bond if it is purchased at the current bid price. Bid yield is calculated using the Ask on all possible call dates. It is assumed that prepayment occurs if the bond has call or put provisions and the issuer can offer a lower coupon rate based on current market rates. The yield to worst will be the lowest of the yield to maturity or yield to call (if the bond has prepayment provisions). Yield to worse may be the same as yield to maturity but never higher. |
| 7700 | string | Probability of Max Return | Customer implied probability of maximum potential gain. |
| 7702 | string | Probability of Max Loss | Customer implied probability of maximum potential loss. |
| 7703 | string | Profit Probability | Customer implied probability of any gain. |
| 7704 | string | Organization Type | |
| 7705 | string | Debt Class | |
| 7706 | string | Ratings | Ratings issued for bond contract. |
| 7707 | string | Bond State Code | |
| 7708 | string | Bond Type | |
| 7714 | string | Last Trading Date | |
| 7715 | string | Issue Date | |
| 7720 | string | Ask Yield | Implied yield of the bond if it is purchased at the current offer. Ask yield is calculated using the Bid on all possible call dates. It is assumed that prepayment occurs if the bond has call or put provisions and the issuer can offer a lower coupon rate based on current market rates. The yield to worst will be the lowest of the yield to maturity or yield to call (if the bond has prepayment provisions). Yield to worse may be the same as yield to maturity but never higher. |
| 7741 | string | Prior Close | Yesterday's closing price |
| 7762 | string | Volume Long | High precision volume for the day. For formatted volume refer to field 87. |
| 7768 | string | hasTradingPermissions | if user has trading permissions for specified contract. Returns 1(true) or 0(false). |
| 7920 | string | Daily PnL Raw | Your profit or loss of the day since prior close. Daily PnL is calculated with real-time market data (even when not subscribed to market data). |
| 7921 | string | Cost Basis Raw | Your current position in this security multiplied by the average price and and multiplier. |

---

## Notes relevant to this hub's own investigation

- **No IV Rank / IV Percentile field appears in this table** — consistent with the WebFetch-independent check run in Session 36 and IBKR support's own confirmation. `7195`-`7212`, `7245`-`7249`, `7263`, `7613`, `7634` (the field IDs this hub's probe tried) are genuinely absent, not merely unreturned by this account's subscriptions.
- **`7283` (Option Implied Vol. %)** — confirmed live and correct for this hub's "Opt. Implied Volatility %" need (`IBKR_REST_API_REFERENCE.md`, Session 35). Its own description here explicitly says it's the *underlying's* prediction, and points to `7633` for a specific strike.
- **`7633` (Implied Vol. %, per-strike)** — **resolved Session 36 (Jul 27, 2026).** Confirmed real and correct against an actual NVDA option conid (Aug 21 2026 197.5 Call/Put) — 42.8% both sides, sitting inside Tradier's own bid/mid/ask IV band. Session 35's empty result was exactly the hypothesized cause: querying the underlying's stock conid instead of an option-contract conid.
- **`7282` (Average Volume, 90-day)** vs the MCP tool's `avg_90d_usd_volume` — worth a side-by-side check if Gate C's dollar-volume computation is ever revisited; not yet cross-referenced.
- **`7638` (Option Open Interest)** — documented as available for both Underlyings and Call & Put options; relevant to this hub's OI ≥ 500 gate if a REST path is ever built for it instead of the current paste/MCP sources.
- **Delta/Gamma/Theta/Vega (`7308`-`7311`) and Break Even/Profit Probability (`7695`/`7703`)** — resolved Session 36 against the same real option conid, all cross-checked against Tradier's live Greeks for the identical contract and landing within normal cross-provider tolerance. Available, but this hub still sources Greeks from Tradier by design (unchanged).
- **`7694` (Probability of Max Return) — available but mislabeled.** Returns `∞` for a long call and a large finite number for a long put, reproduced on two independent contract pairs. Despite the documented "0-100% probability" description, this behaves like a max theoretical return percentage, not a probability. Not used by this pipeline.
- **`7700`/`7702` (the duplicate Probability-of-Max-Return ID, and Probability of Max Loss)** — confirmed genuinely absent even against a correctly-resolved option conid, not a methodology artifact. Low priority, not used by this pipeline.
- **A real bug was caught, not just a field result:** `/iserver/secdef/info` with a bare month (e.g. `"AUG26"`) returns *every* expiry in that calendar month, not one contract — an early pass took the first result and silently resolved to a ~7 DTE weekly instead of the intended ~25 DTE monthly. Caught by cross-checking the resolved premium against Tradier's live quote for the same nominal contract, not by the API returning an error. `research/ibkr_rest_api_probe/client.py`'s `option_conid()` now requires filtering to an explicit `maturityDate`.
