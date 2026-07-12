---
name: options-trade-validator
description: "Analyze and validate specific single-leg options trades (calls and puts) on US and Canadian underlyings (equities and ETFs/indices). Trigger this skill whenever the user describes an options trade setup, asks to validate a call or put, mentions strike/expiry/premium details, or asks if an options trade is good. Also trigger when the user pastes ticker + strike + date + cost details, asks about entry/exit for options, or wants a risk/reward breakdown on a call or put. Always run the full analysis: technical setup, fundamentals, macro regime, options flow, Greeks, P&L table, and trade verdict. Never skip the two required output tables."
---

# Options Trade Validator v3.1

Single-leg stock calls and puts — US and Canadian underlyings. Three modes depending on what the user needs. Read the prompt carefully to detect the mode. Default mode is always Mode 1 unless the user explicitly asks for more.

---

## MODE DETECTION

**Mode 1 — Default Verdict** (use this unless told otherwise)
Trigger: any of the following —
- user pastes an **Options IQ Gemini Centaur trade-plan briefing** (`# INSTITUTIONAL BRIEFING: [TICKER] OPTIONS SYNTHESIS`) — the primary use case: an independent second opinion on Gemini's own recommendation
- user pastes trade details from the Options Research Terminal (maintenance-mode HTML tool)
- user just describes a trade in plain text ("NFLX $93 PUT Jun 18 at $4.72") — the ad-hoc / Canadian-stock case
Output: one structured card, ~150 words, all exit rules as hard numbers. No headers, no phases, no tables.

**Mode 2 — Deep Dive** (user says "deep dive" or "full analysis")
Trigger: user replies "deep dive" after a Mode 1 verdict, or explicitly asks for full analysis.
Output: full 6-phase analysis with both mandatory P&L tables.

**Mode 3 — Comparison** (user pastes two different options)
Trigger: user provides two trade setups and asks which is better.
Output: side-by-side comparison, single recommendation with one decisive reason.

---

## MODE 1 — DEFAULT VERDICT

### What to do first: web search
Before writing anything, always search for:
1. `[TICKER] stock price today` — confirm current price matches the trade details
2. `[TICKER] earnings date 2026` — confirm or fill in earnings date (terminal may already provide it in TREND & CONTEXT section)
3. `[TICKER] analyst price target 2026` — directional consensus
4. `[TICKER] IV rank` — IV Rank (IVR): where is current IV vs its 52-week range? **Known dead end (Session 12 research, confirmed again here):** Market Chameleon, Barchart's IV rank page, and Barchart's core API are all JS-rendered or return 401 to a plain web search — none of them will return real data this way. If the search doesn't return a genuine numeric IVR from a page that actually rendered, **do not fabricate one.** State "IVR not available via web search — no reliable free public source" and fall back to whatever IV vs HV30 comparison the input already gives you (orthogonal signal, still usable on its own).

Use these results to inform the catalyst statement and conviction score. Never estimate what you can look up.

**IVR interpretation:**
- IVR < 30 → IV historically cheap — supports buying premium
- IVR 30–70 → IV in normal range — neutral signal
- IVR > 70 → IV historically expensive — consider spread or wait for compression

### Required inputs — three input shapes, not all fields available from every one

**If pasted from a Gemini Centaur briefing** — this is the primary use case, an independent second opinion on Gemini's own pick. Two sub-cases, read `app.py` if you need to confirm which one produced a given paste: the **deterministic fallback** (Gemini API down) always uses the exact header `# INSTITUTIONAL BRIEFING: [TICKER] OPTIONS SYNTHESIS` with fixed sections `📊 Setup Analysis` / `🎯 Recommended Contract` / `🛡️ Trade Execution Plan`; the **real Gemini LLM path** is told to "format as a professional institutional briefing" but is otherwise freeform prose — expect the same underlying fields (entry, 50% target, 30% stop, delta, theta, trend, RSI) but don't assume identical headers or field order. Either way, Gemini's briefing does **not** contain everything the HTML terminal does:

| Field | Where it comes from in a Gemini briefing |
|-------|-------------------------------------------|
| Underlying price | `Current Stock Price` — trust it |
| Strike, expiry | `Strike` + `Expiration` under Recommended Contract. **DTE isn't stated — compute it** (expiry − today) |
| Entry / mid price | `Limit Price (Mid)` under Trade Execution Plan |
| Target / stop | `Profit Target (50% TP)` / `Stop Loss (30% SL)` — Gemini's own mechanical rule, not yours to re-derive |
| Delta, Theta | Given directly. **Gamma, Vega, IV% are NOT in the briefing** — do not invent plausible-looking values for them. Say "not provided by Gemini" and drop those rows from any table, don't leave a fabricated number in their place |
| Breakeven | Not stated — **compute it** from strike ± mid premium (call: strike + mid; put: strike − mid) |
| HV30 vs IV | Only present if `iv_rank` isn't the `IBKR PRE-VERIFIED` sentinel and a numeric IV value was given — Gemini's own briefing doesn't carry HV30 at all. If absent, say so; don't estimate |
| Terminal score (0–100) | Does not exist in this flow — Gemini has no such score. Skip this line entirely rather than inventing one |
| Trend | `Trend (200-SMA)` — use directly |
| Earnings date | In `⚡ Active Warning Flags` if within window, otherwise web search |

**If pasted from the Options Research Terminal** (maintenance-mode HTML tool) — the original, fuller field set:
- Underlying price (live from Tradier — trust it, do not second-guess)
- Strike, expiry, DTE
- Premium (ask), mid price, breakeven
- Live Greeks: delta, gamma, theta, vega, IV%
- HV30 vs IV assessment (if provided — use it directly, do not re-estimate)
- Terminal score (0–100) — acknowledge it but form your own conviction independently
- **Trend direction** (if provided in TREND & CONTEXT section) — use directly, confirms or contradicts the trade direction
- **Earnings date** (if provided in TREND & CONTEXT section) — use directly, web search only if shown as "Not available"

**If it's just a plain-text trade description** (ad-hoc idea, tip, Canadian stock) — none of the above is guaranteed. Pull underlying price, IV, and Greeks yourself via web search before writing the verdict; state plainly which fields you couldn't confirm rather than guessing.

**Rule that applies across all three:** never fabricate a field that isn't in the input. A missing Gamma/Vega/HV30/terminal-score is "not provided," never a plausible-looking estimate presented as real data.

### Output format — exactly this structure, no deviation

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[TICKER] $[STRIKE] [CALL/PUT] · [MONTH DAY] · [DTE] DTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VERDICT:   [BUY ✅ / AVOID ❌ / WAIT ⏳]
Conviction: [X]/10

ENTRY:     $[mid price] limit  (not market — never pay the ask)
TARGET:    $[price] → close at [+X%] gain
STOP:      $[price] → close if [TICKER] drops below $[level]
TIME STOP: Close by [specific date] if flat — do not hold through theta grind

IV vs HV:  [cheap / fair / expensive] — [one sentence using the HV30 data if provided]
IVR:       [X]% — [historically cheap / normal / expensive] — [one sentence]
TREND:     [UPTREND / DOWNTREND] — trading [with / AGAINST] trend ⚠ if against

CATALYST:  [One specific reason the stock moves in the next DTE days]
           OR: No near-term catalyst — pure technical/momentum play ⚠

WRONG IF:  [The single price level or event that invalidates the thesis]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Reply "deep dive" for full 6-phase analysis
```

### Rules for Mode 1

**VERDICT rules:**
- BUY ✅ — thesis is valid, IV is not expensive, catalyst exists or technical setup is strong, breakeven is reachable within historical ATR × DTE
- WAIT ⏳ — setup is good but entry timing is wrong (stock at resistance, IV elevated, no catalyst yet). State what to wait for.
- AVOID ❌ — thesis is weak, breakeven requires unrealistic move, IV is expensive, or macro is a direct headwind

**CONVICTION rules (be honest — never inflate):**
- 8–10: Strong catalyst + cheap IV + clean technical breakout + sector tailwind
- 6–7: Good setup, 1–2 concerns that are manageable
- 4–5: Mixed signals — something meaningful is wrong
- 1–3: Do not trade this. State why clearly.

**ENTRY rule:**
Always recommend the mid price as the limit order. Never tell the user to pay the ask. State: "$[mid] limit — if not filled in 5 minutes, reassess."

**TARGET rule:**
- For calls/puts with delta 0.35–0.50: target 75–100% gain on premium (2x is ideal)
- State as an exact dollar premium AND the underlying stock price that achieves it
- Example: "Close at $2.75 premium (ALLY hits ~$47.50)"

**STOP rule:**
- Never state stop as just a % of premium
- Always state the underlying stock price that signals thesis failure
- Example: "Close if premium drops to $0.70 OR ALLY closes below $42.00 — whichever comes first"

**TIME STOP rule:**
- Calculate: entry date + (DTE × 0.60) = time stop date
- Example: entered May 7, 42 DTE → time stop = June 2
- After this date, theta accelerates. If flat or down: close, do not wait for a miracle.

**CATALYST rule:**
- Must name a specific, near-term reason for price movement
- Acceptable catalysts: earnings (if within DTE), analyst day, product launch, sector catalyst, momentum continuation after key breakout, post-earnings mean reversion
- If no catalyst: flag it explicitly and reduce conviction by 1.5 points. Pure technical plays have lower probability of hitting the breakeven in time.

**WRONG IF rule:**
- One sentence. One price level or one event.
- Not "if the market falls" — too vague
- Good: "If ALLY fails to close above $45.00 within 10 trading days, the breakout thesis is dead — exit."

**Canadian underlyings:**
- Flag if TSX options are illiquid (wide spread > 15% of mid)
- Recommend USD-listed equivalent if available and more liquid
- State premium clearly in CAD

---

## MODE 2 — DEEP DIVE

Triggered by: user says "deep dive", "full analysis", "walk me through it", or similar.

Always start with: "Running full 6-phase analysis on [TICKER] $[STRIKE] [CALL/PUT] · [EXPIRY]"

### Phase 1 — Technical Setup
Search for current chart data before writing. Assess:
- **200-day SMA trend** (from terminal TREND & CONTEXT if provided): state direction and % above/below SMA. If trading against the trend, flag explicitly.
- Trend structure: higher highs/lows (calls) or lower highs/lows (puts)
- Key support and resistance levels relative to the strike
- RSI(14): overbought >70, oversold <30
- ADX: <20 = ranging/no trend, >25 = trending — state which and what it means for this trade
- Volume confirmation of recent moves
- Regime texture: **grinding trend** (bad for long calls — theta kills) vs **breakout** (great for calls) vs **relief rally** (IV crush risk)
- Distance from 52-week high/low
- Earnings within DTE window? (Yes = binary risk, No = clean window ✅)
- **Verdict**: Strong / Moderate / Weak / Against-trend + one sentence explanation

### Phase 2 — Fundamentals
Search for recent earnings and analyst data. Assess:
- Most recent EPS vs. estimate (beat/miss/inline)
- Revenue trend (accelerating/decelerating)
- Guidance (raised/maintained/cut)
- Analyst consensus: # of Buy/Hold/Sell ratings + average price target
- Implied upside from current price to consensus PT — is the option direction aligned?
- For Canadian tickers: CAD/USD exposure, commodity correlation, TSX sector leadership
- **Verdict**: Strongly Bullish / Bullish / Neutral / Bearish / Strongly Bearish

### Phase 3 — Macro Regime
Assess broader context:
- SPY/QQQ regime: bull trend, bear trend, or choppy/ranging?
- VIX level and direction: <15 (complacent), 15–25 (normal), >25 (fearful/volatile)
- Rate environment: Fed stance and expected path within DTE window
- Sector context: is the underlying's sector leading or lagging SPY?
- For Canadian tickers: BOC policy, CAD strength, commodity regime
- **Verdict**: Tailwind / Neutral / Headwind — one sentence

### Phase 4 — Options Flow & IV Analysis
Use live data from the prompt. Assess:
- **IV vs HV30**: If provided, state clearly: cheap/fair/expensive with the exact ratio
- **IV direction**: Post-earnings crush (IV deflating) vs. pre-event expansion
- **Open interest at strike**: High OI = watched level, potential pinning near expiry. If terminal shows OI delta (▲ BUILDING / ▼ UNWINDING), use it directly — it reflects change vs previous session.
- **IVR** (from web search): state percentile. IVR < 30 = historically cheap, IVR > 70 = historically expensive. Use alongside HV30 — they are orthogonal signals.
- **Volume today**: High = active positioning, Low = thin — flag if volume < 20 contracts
- **Bid-ask spread quality**: < 8% of mid = tight ✅, > 15% = wide ⚠
- **Naked vs. Spread decision**: State explicitly —
  - If IV < HV30 (cheap): naked debit call/put is correct
  - If IV > HV30 × 1.10 (expensive): consider debit spread to reduce vega exposure
- **Verdict**: Supportive / Neutral / Cautionary

### Phase 5 — Greeks Analysis
Use live Greeks from the prompt — do not re-estimate. Build the table:

| Greek | Live Value | $ Impact | Interpretation |
|-------|-----------|----------|----------------|
| Delta | [value] | $[X] per $1 move | Directional exposure |
| Gamma | [value] | Delta +[X] per $1 | Acceleration near strike |
| Theta | [value] | $[X]/day | Time decay cost |
| Vega | [value] | $[X] per 1% IV | IV sensitivity |
| Rho | ~est | Negligible | Rates stable |

Also state:
- Moneyness: ITM / ATM / OTM + % distance from strike
- Breakeven at expiry: $[price] ([X]% move required)
- Intrinsic value: $[X] (or $0 if OTM)
- Extrinsic/time value: $[X] ([X]% of premium)
- Theta as % of daily premium: if theta > 2% of premium/day, flag as aggressive decay
- Weekly theta bleed: theta × 5 = $[X]/week
- Total theta to expiry (flat stock): theta × DTE = $[X] ([X]% of total premium)

### Phase 6 — P&L Tables (MANDATORY — never skip)

#### Table 1 — Risk/Reward Summary

| Metric | Value |
|--------|-------|
| Entry premium (ask) | $[X] / share = $[X × 100 × contracts] total |
| Recommended entry | $[mid] limit |
| Max gain | Unlimited (calls) / Down to $0 (puts) |
| Max loss | $[premium × 100 × contracts] — 100% of cost |
| Breakeven at expiry | $[X] ([X]% move from current) |
| Delta | [X] |
| Theta/day | $[X] |
| Weekly theta | $[X] |
| Total theta to expiry | $[X] ([X]% of premium) |
| Vega | $[X] per 1% IV |
| IV at entry | [X]% |
| HV30 | [X]% (or N/A) |
| IV vs HV | Cheap / Fair / Expensive |
| DTE | [X] days |
| Profit target | $[X] premium = [X]% gain |
| Stop loss | $[X] premium OR [TICKER] < $[level] |
| Time stop | [date] |

#### Table 2 — P&L Grid (Price × Time)

Use Black-Scholes approximation. IV constant. 1 contract = 100 shares.
Show P&L vs. entry cost.

Price points: underlying × (0.90, 0.95, 1.00, 1.025, 1.05, 1.10)
Time points: Today · Halfway (DTE/2) · At expiry

| Underlying Price | Today | Halfway | At Expiry |
|-----------------|-------|---------|-----------|
| $[−10%] | −$[X] | −$[X] | −$[X] |
| $[−5%] | −$[X] | −$[X] | −$[X] |
| $[current] | $0 | −$[X] | −$[X] |
| $[+2.5%] | +$[X] | +$[X] | −$[X] |
| $[+5%] | +$[X] | +$[X] | +/−$[X] |
| $[breakeven] | +$[X] | +$[X] | **$0** ✓ |
| $[+10%] | +$[X] | +$[X] | +$[X] |

Mark the breakeven row. Mark profit target row with ★.

### Deep Dive Verdict

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TRADE VERDICT: [STRONG BUY / BUY / WAIT / AVOID / STRONG AVOID]
Conviction: [X]/10
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ENTRY:      $[mid] limit
TARGET:     $[premium] when [TICKER] hits ~$[price]
STOP:       $[premium] OR [TICKER] < $[price]
TIME STOP:  [date]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STRENGTHS
• [bullet — specific, not generic]
• [bullet]

RISKS
• [bullet — specific, not generic]
• [bullet]

ADJUSTMENTS (if any)
• [Alternative strike or expiry with rationale]
• [Spread alternative if IV is expensive]

SIZING
• [X]% of options allocation — [tier: core / tactical / speculative]
• Max [X] contracts given account size considerations
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## MODE 3 — COMPARISON

Triggered by: user provides two options setups and asks which is better.

### Output format

```
COMPARING
  A: [TICKER] $[STRIKE] [CALL/PUT] · [EXPIRY] · $[PREMIUM]
  B: [TICKER] $[STRIKE] [CALL/PUT] · [EXPIRY] · $[PREMIUM]

WINNER: [A or B] ✅

DECISIVE REASON: [One sentence. Not a list. The single most important difference.]

WHY NOT [loser]:
[One sentence on the loser's critical flaw]

ENTRY (winner): $[mid] limit
TARGET: $[X]
STOP:   $[X] OR [TICKER] < $[level]
TIME:   Close by [date] if flat
```

Do not write a full analysis for both options. Pick one, justify clearly, move on.

---

## UNIVERSAL RULES (apply to all modes)

1. **Always use the live underlying price from the prompt** — never assume or re-estimate the stock price
2. **Never pay the ask** — always recommend the mid as the limit order entry
3. **Exit rules are mandatory in every mode** — entry without exit is not a trade plan
4. **Canadian tickers**: flag illiquid options, recommend USD equivalent if better liquidity
5. **Web search is required** — always search for current price confirmation and earnings date before responding in Mode 1 or 2
6. **HV30 data**: if provided in the prompt (from terminal), use it directly as stated — do not override with estimates
7. **Terminal score**: acknowledge it but state your own conviction independently — they may differ
8. **Honesty over optimism** — a conviction score of 4/10 is more valuable than an inflated 7/10
9. **One invalidation trigger** — every verdict must state the single price or event that proves the trade wrong
10. **Time stop is non-negotiable** — every trade has an expiry for the thesis, not just the option
