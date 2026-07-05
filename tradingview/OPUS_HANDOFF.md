# Opus Handoff — Gemini Edge Scanner Pine Script Review

> ⚠️ **Note:** The v2 code block further down this file is the ORIGINAL Sonnet handoff (Pine v5).
> The live script is now **v6** at `gemini-edge-scanner.pine`. Review that file, not the block below.

---

## Live-Test Findings — Session 17 (2026-07-03, v6)

Tested v6 on NVDA, ECHO, PURR, AFRM (daily). Prior fixes held (RVOL uses last completed bar; no red zones below price). Two new bugs found:

### Bug A — NaN EMA200 on short-history names forces a false BLOCK/BLOCK  ✅ FIXED (Session 18)
**Seen on:** PURR (Hyperliquid Strategies — listed ~Jan 2026, < 200 daily bars).
**Symptom:** `EMA 200` reads `-- NaN%`; Trend shows NEUTRAL; **both** `CALL (buy)` and `PUT (buy)` show BLOCK; `52W Low` also reads `--`.
**Cause:** With < 200 bars, `e200 = na`. The trend/gate expressions (`close > e200`, `close < e200`) are then `na` → false, so `gate_call`/`gate_put` both fall through to their `BLOCK` branch. It looks like a real "no trade" verdict but it is a data gap, not structure.
**Fix:** Guard on `na(e200)`. When true, render `Trend: INSUFFICIENT HISTORY (<200 bars)` and set the buyer gates to `N/A (no 200 EMA)` rather than BLOCK. Same guard for the `52W Low` cell (it should still show the lowest available bar; investigate why it returned `--`).

### Bug B — On parabolic movers, S/R collapses to the 52W extremes  ✅ FIXED (Session 18 — role reversal)
**Seen on:** ECHO (R1 = $147.25 = 52W High; S1 = $26.04 = 52W Low; R2/S2 = `--` — nothing between). Also present milder on NVDA.
**Cause:** A near-vertical run + sharp reversal means few intermediate pivots ever formed, and the per-bar pruning deletes any level price closed through. After a reversal those broken levels are gone permanently (pivots are one-shot historical events), so the arrays empty out and the "Key Levels" rows just echo the 52W H/L.
**Consequence:** Misleading — ECHO's real next support is the Oct–Nov shelf (~$68–75), but the table implies an air pocket down to $26.
**This needs a design call before coding — options:**
  1. **Re-arm broken levels after a reversal** — keep a "broken levels" archive; when price closes back below a broken resistance (or above a broken support), restore it as fresh S/R.
  2. **Fallback to nearest surviving historical pivot** when the proximity-filtered array is empty (widen `i_prox` dynamically until ≥1 level is found).
  3. **Flag the empty state** — if R/S array is empty, label `NO INTERMEDIATE S/R (parabolic) — using 52W H/L` so the reader knows the levels are extremes, not structure.
  (Recommend 3 as the immediate safety label + 1 as the real fix.)

---

## What this is

A TradingView Pine Script indicator ("Gemini Edge Scanner") that acts as **Claude's eyes on a
chart** for the Options IQ Gemini trading pipeline. When the user pastes a TradingView screenshot
into Claude alongside a ticker name, Claude reads the chart to infer directional bias
(BULLISH / BEARISH / NEUTRAL) and extract key S/R levels — all feeding into a CENTAUR JSON
handoff for the Gemini options backend.

**Critical design constraint:** Every signal must have a clear text label, not just a color.
Claude reads this from a screenshot — it cannot hover over elements.

---

## What Sonnet already built

Pine Script v2 is written and saved at:
`/Users/balajik/projects/trading-intelligence-hub/tradingview/gemini-edge-scanner.pine`

### What v2 implements (vs v1 which it replaces):

| Feature | v1 (old) | v2 (built by Sonnet) |
|---|---|---|
| S/R | `line.new()` — thin dashed lines, cluttered | `box.new()` — shaded zones, clustered, max 3+3 |
| S/R labels | `R $XX` at pivot bar | `R $XX.XX` inside zone box, right-aligned |
| S/R filtering | None — all pivots drawn | Within 25% of price, 1.5% cluster radius, 3-zone cap |
| 52W levels | Missing | Orange dashed `52W HIGH` + teal dashed `52W LOW` |
| BASE label | `BASE` (no duration) | `BASE (Xd)` with day count |
| Wedge detection | None | Linear regression slopes + BB narrowing context filter |
| Failed breakdown | Missing | `FAILED↓` added (mirror of `FAILED↑`) |
| Resource limits | max_labels=100 (may exceed free plan) | max_boxes=15, max_labels=40, max_lines=10 |

---

## Hard constraints Opus must preserve

- **Pine Script v5 only**
- **overlay=true** — everything on the price chart, no separate pane
- **1 indicator slot** — user has max 2 slots total; this uses 1
- **Daily chart, 1–2 year view** — NOT 5-min (that's execution timing)
- **Conservative resource limits** — `max_boxes_count=15, max_labels_count=40, max_lines_count=10`
  (user's TradingView plan is unknown; start conservative, iterate)
- **No `request.security()`** — keep single-timeframe for simplicity

---

## What Claude reads from the screenshot (don't break these)

| Visual element | What Claude extracts |
|---|---|
| Top-right label | UPTREND / DOWNTREND / NEUTRAL |
| EMA lines (orange/blue/gold) | Trend strength, fanning vs converging |
| Red shaded zones above price | Resistance levels with `R $XX.XX` |
| Green shaded zones below price | Support levels with `S $XX.XX` |
| Orange dashed line | `52W HIGH $XX.XX` |
| Teal dashed line | `52W LOW $XX.XX` |
| Purple background | `BASE (Xd)` — consolidation with duration |
| Pattern shapes/labels | BREAK↑ / BREAK↓ / FAILED↑ / FAILED↓ / WEDGE / TRIANGLE |
| Bright candles | RVOL ≥ 1.5 (lime = bull, red = bear) |
| RVOL label bottom | `RVOL X.XX ⚡` |

---

## Opus task: review, test, and improve

Sonnet wrote the logic but has not run it in TradingView (cannot execute Pine Script).
Opus should:

1. **Review the v2 code** for Pine Script v5 correctness — syntax, function signatures, array ops
2. **Identify any bugs** — especially in:
   - `box.new()` / `box.set_right()` usage and loop extension logic
   - `f_res_clustered()` / `f_sup_clustered()` — can Pine v5 functions access outer-scope `var` arrays?
   - `ta.linreg()` wedge slope calculation and normalization
   - `barstate.islast` label deletion/redrawing for 52W lines
3. **Fix any issues found** and output the corrected complete script
4. **Note any Pine Script v5 limitations** that prevent exact spec implementation
   (e.g., true volume profile is impossible in Pine — confirm)

---

## The v2 code to review

```pine
//@version=5
indicator("Gemini Edge Scanner", overlay=true,
          max_boxes_count=15, max_labels_count=40, max_lines_count=10)

// ─── INPUTS ──────────────────────────────────────────────────────────────────
i_pl      = input.int(10,    "Pivot Left Bars",           group="S/R",      minval=3)
i_pr      = input.int(10,    "Pivot Right Bars",          group="S/R",      minval=3)
i_zone    = input.float(0.75,"Zone half-width (%)",       group="S/R",      minval=0.1, maxval=3.0)
i_cluster = input.float(1.5, "Cluster radius (%)",        group="S/R",      minval=0.5, maxval=5.0)
i_prox    = input.float(25.0,"Price proximity filter (%)",group="S/R",      minval=5.0, maxval=50.0)
i_e21     = input.int(21,    "EMA Fast",                  group="Trend")
i_e50     = input.int(50,    "EMA Mid",                   group="Trend")
i_e200    = input.int(200,   "EMA Slow",                  group="Trend")
i_batr    = input.float(0.65,"Base: ATR ratio threshold", group="Patterns", minval=0.3, maxval=1.0)
i_bbars   = input.int(5,     "Base: min tight bars",      group="Patterns", minval=2)
i_vlen    = input.int(20,    "Volume MA length",          group="Volume")
i_rvol    = input.float(1.5, "High-vol RVOL threshold",   group="Volume")

// ─── TREND EMAs ───────────────────────────────────────────────────────────────
e21  = ta.ema(close, i_e21)
e50  = ta.ema(close, i_e50)
e200 = ta.ema(close, i_e200)

plot(e21,  "EMA 21",  color=color.orange, linewidth=1)
plot(e50,  "EMA 50",  color=color.blue,   linewidth=2)
plot(e200, "EMA 200", color=#FFD700,      linewidth=2)

// ─── TREND STRUCTURE ─────────────────────────────────────────────────────────
uptrend   = close > e200 and e50 > e200 and e21 > e50
downtrend = close < e200 and e50 < e200 and e21 < e50

bgcolor(uptrend   ? color.new(color.green, 93) :
        downtrend ? color.new(color.red,   93) :
                    color.new(color.gray,  96), title="Trend Tint")

if barstate.islast
    txt = uptrend   ? "▲  UPTREND"   :
          downtrend ? "▼  DOWNTREND" : "◆  NEUTRAL"
    col = uptrend   ? color.green :
          downtrend ? color.red   : color.gray
    label.new(bar_index, ta.highest(high, 50), txt,
              style=label.style_label_down, color=col,
              textcolor=color.white, size=size.normal)

// ─── S/R ZONE ARRAYS ─────────────────────────────────────────────────────────
var array<box>   res_boxes  = array.new<box>()
var array<float> res_levels = array.new<float>()
var array<box>   sup_boxes  = array.new<box>()
var array<float> sup_levels = array.new<float>()

// Clustering check: returns true if price is within cluster radius of any tracked level
f_res_clustered(price) =>
    result = false
    if array.size(res_levels) > 0
        for i = 0 to array.size(res_levels) - 1
            if math.abs(array.get(res_levels, i) - price) / price < i_cluster / 100.0
                result := true
                break
    result

f_sup_clustered(price) =>
    result = false
    if array.size(sup_levels) > 0
        for i = 0 to array.size(sup_levels) - 1
            if math.abs(array.get(sup_levels, i) - price) / price < i_cluster / 100.0
                result := true
                break
    result

// ─── ZONE EXTENSION — run every bar to keep zones current ────────────────────
if array.size(res_boxes) > 0
    for i = 0 to array.size(res_boxes) - 1
        box.set_right(array.get(res_boxes, i), bar_index)
if array.size(sup_boxes) > 0
    for i = 0 to array.size(sup_boxes) - 1
        box.set_right(array.get(sup_boxes, i), bar_index)

// ─── PIVOT DETECTION & ZONE DRAWING ──────────────────────────────────────────
ph = ta.pivothigh(high, i_pl, i_pr)
pl = ta.pivotlow(low,   i_pl, i_pr)

var float last_r = na
var float last_s = na

if not na(ph)
    last_r := ph
    within_range  = ph < close * (1 + i_prox / 100) and ph > close * (1 - i_prox / 100)
    not_clustered = not f_res_clustered(ph)
    under_cap     = array.size(res_boxes) < 3
    if within_range and not_clustered and under_cap
        zt = ph * (1 + i_zone / 100)
        zb = ph * (1 - i_zone / 100)
        b  = box.new(bar_index[i_pr], zt, bar_index, zb,
                     border_color=color.new(color.red,   40),
                     bgcolor     =color.new(color.red,   75),
                     text        ="R  $" + str.tostring(ph, format.mintick),
                     text_size   =size.tiny,
                     text_color  =color.white,
                     text_halign =text.align_right,
                     text_valign =text.align_center)
        array.push(res_boxes,  b)
        array.push(res_levels, ph)

if not na(pl)
    last_s := pl
    within_range  = pl < close * (1 + i_prox / 100) and pl > close * (1 - i_prox / 100)
    not_clustered = not f_sup_clustered(pl)
    under_cap     = array.size(sup_boxes) < 3
    if within_range and not_clustered and under_cap
        zt = pl * (1 + i_zone / 100)
        zb = pl * (1 - i_zone / 100)
        b  = box.new(bar_index[i_pr], zt, bar_index, zb,
                     border_color=color.new(color.green, 40),
                     bgcolor     =color.new(color.green, 75),
                     text        ="S  $" + str.tostring(pl, format.mintick),
                     text_size   =size.tiny,
                     text_color  =color.white,
                     text_halign =text.align_right,
                     text_valign =text.align_center)
        array.push(sup_boxes,  b)
        array.push(sup_levels, pl)

// ─── 52-WEEK HIGH / LOW ───────────────────────────────────────────────────────
high_52w = ta.highest(high, 252)
low_52w  = ta.lowest(low,  252)

var line l_52h = na
var line l_52l = na

if barstate.islast
    line.delete(l_52h)
    line.delete(l_52l)
    l_52h := line.new(bar_index - 252, high_52w, bar_index, high_52w,
                      color=color.orange, style=line.style_dashed, width=1)
    l_52l := line.new(bar_index - 252, low_52w,  bar_index, low_52w,
                      color=color.teal,  style=line.style_dashed, width=1)
    label.new(bar_index, high_52w,
              "52W HIGH  $" + str.tostring(high_52w, format.mintick),
              style=label.style_label_up,
              color=color.new(color.orange, 30), textcolor=color.white, size=size.small)
    label.new(bar_index, low_52w,
              "52W LOW  $" + str.tostring(low_52w, format.mintick),
              style=label.style_label_down,
              color=color.new(color.teal, 30), textcolor=color.white, size=size.small)

// ─── BASE / CONSOLIDATION ────────────────────────────────────────────────────
atr14   = ta.atr(14)
atr_avg = ta.sma(atr14, 20)
tight   = atr14 < atr_avg * i_batr

var int tight_run = 0
tight_run := tight ? tight_run + 1 : 0
in_base   = tight_run >= i_bbars

bgcolor(in_base ? color.new(color.purple, 87) : na, title="Base / Consolidation")

if in_base and not in_base[1]
    label.new(bar_index, low * 0.995,
              "BASE (" + str.tostring(tight_run) + "d)",
              style=label.style_label_up, color=color.purple,
              textcolor=color.white, size=size.small)

// ─── WEDGE DETECTION ─────────────────────────────────────────────────────────
res_slope = (ta.linreg(high, 20, 0) - ta.linreg(high, 20, 1)) / close
sup_slope = (ta.linreg(low,  20, 0) - ta.linreg(low,  20, 1)) / close

bb_mid    = ta.sma(close, 20)
bb_width  = 4.0 * ta.stdev(close, 20) / bb_mid
narrowing = bb_width < ta.sma(bb_width, 40) * 0.85
wedge_ctx = in_base or narrowing

sym_tri   = wedge_ctx and res_slope < -0.0005 and sup_slope >  0.0005
asc_wedge = wedge_ctx and res_slope >  0.0005 and sup_slope >  0.0005 and sup_slope > res_slope * 0.5
dsc_wedge = wedge_ctx and res_slope < -0.0005 and sup_slope < -0.0005 and sup_slope > res_slope

if barstate.islast
    if sym_tri
        label.new(bar_index, ta.highest(high, 20) * 1.002, "△  TRIANGLE",
                  style=label.style_label_down,
                  color=color.gray, textcolor=color.white, size=size.small)
    else if asc_wedge
        label.new(bar_index, ta.highest(high, 20) * 1.002, "⌒  WEDGE ▲  bearish",
                  style=label.style_label_down,
                  color=color.orange, textcolor=color.white, size=size.small)
    else if dsc_wedge
        label.new(bar_index, ta.highest(high, 20) * 1.002, "⌣  WEDGE ▼  bullish",
                  style=label.style_label_down,
                  color=color.blue, textcolor=color.white, size=size.small)

// ─── VOLUME SIGNALS ───────────────────────────────────────────────────────────
vol_ma = ta.sma(volume, i_vlen)
rvol   = volume / vol_ma
hi_vol = rvol >= i_rvol
bull_c = close >= open

barcolor(hi_vol and bull_c     ? color.lime :
         hi_vol and not bull_c ? color.red  :
         bull_c                ? color.new(color.green, 50) :
                                 color.new(color.red,   50),
         title="Volume-Colored Candles")

if barstate.islast
    rv_str = "RVOL  " + str.tostring(math.round(rvol, 2), "#.##") + (hi_vol ? "  ⚡" : "")
    label.new(bar_index, low * 0.989, rv_str,
              style=label.style_label_up,
              color=color.new(color.navy, 50), textcolor=color.white, size=size.tiny)

// ─── BREAKOUT / BREAKDOWN / FAILED ───────────────────────────────────────────
breakout  = not na(last_r) and close > last_r and close[1] <= last_r and hi_vol
breakdown = not na(last_s) and close < last_s and close[1] >= last_s and hi_vol
failed_bo = not na(last_r) and high[1] <= last_r and high > last_r and close < last_r
failed_bd = not na(last_s) and low[1]  >= last_s and low  < last_s and close > last_s

plotshape(breakout,  "Breakout",         shape.triangleup,   location.abovebar,
          color.lime,   size=size.small, text="BREAK↑")
plotshape(breakdown, "Breakdown",        shape.triangledown, location.belowbar,
          color.red,    size=size.small, text="BREAK↓")
plotshape(failed_bo, "Failed Breakout",  shape.xcross,       location.abovebar,
          color.orange, size=size.small, text="FAILED↑")
plotshape(failed_bd, "Failed Breakdown", shape.xcross,       location.belowbar,
          color.orange, size=size.small, text="FAILED↓")
```

---

## Specific questions for Opus to resolve

1. **Can Pine v5 functions access outer-scope `var` arrays?**
   `f_res_clustered()` and `f_sup_clustered()` reference `res_levels`, `sup_levels`, `i_cluster`
   from the outer scope. Is this valid in Pine v5, or does it require passing them as arguments?

2. **`box.new()` text parameters** — are `text_halign` and `text_valign` valid in Pine v5?
   If not, what's the correct way to add a label inside a box?

3. **52W line redraw on `barstate.islast`** — `line.delete(l_52h)` before redrawing each tick.
   Is this the correct pattern, or will it cause flickering on realtime updates?

4. **`for i = 0 to array.size() - 1` when size = 0** — in Pine v5, does `for i = 0 to -1`
   execute or skip? Confirm whether the `if array.size() > 0` guard is needed.

5. **`format.mintick` in `str.tostring()`** — valid for any numeric value, or only for price
   series values? Will this work correctly for `ph` (a pivot level)?

6. **True volume profile** — confirm this is impossible in Pine Script v5 (no volume-at-price
   data available). The current RVOL + candle coloring approach is the best Pine can do.

---

## Directional Builder skill — what Sonnet already updated

`skill-options-directional-builder.md` was updated to v1.2 this session alongside the Pine Script.
Opus must keep this skill in sync with any Pine Script changes.

### What changed in the skill (v1.1 → v1.2)

1. **Manifest description** — now mentions TradingView chart screenshot as an accepted input
2. **INPUT table** — new row: `TradingView chart screenshot | No | Optional`
3. **New `CHART INPUT` section** (added between INPUT table and STEP 1) — full reading guide:
   - How to read each Pine Script signal from a screenshot
   - S/R zones (boxes) vs old lines description
   - All pattern labels including new: `FAILED↓`, `△ TRIANGLE`, `⌒ WEDGE ▲`, `⌣ WEDGE ▼`
   - 52W HIGH / 52W LOW as special levels Claude should read
   - Priority rules table (chart wins for S/R/trend; MCP wins for IV/HV/IVR)
4. **STEP 6 direction scoring table** — two new chart-signal rows added:
   - Chart trend label `▲ UPTREND` → +1 bullish; `▼ DOWNTREND` → +1 bearish
   - Chart pattern `BREAK↑` → +1 bullish; `BREAK↓` or `FAILED↑` → +1 bearish
   - Note: `BASE` pattern = 0 (neutral, wait for resolution)
5. **OUTPUT FORMAT** — new `CHART ANALYSIS` block added at top of output section
6. **Rule 11** — chart beats MCP for trend and S/R; MCP always wins for IV/HV and IVR

### What Opus must do if it changes any Pine Script signal

If Opus renames, removes, or adds any labeled signal in the Pine Script, it **must** update the
corresponding entry in `skill-options-directional-builder.md` under the `CHART INPUT` section.
The skill and the Pine Script are a matched pair — Claude reads the chart using the skill's
reading guide. A signal that exists in Pine but isn't in the skill's guide will be invisible
to Claude. A guide entry that no longer matches the Pine output will mislead Claude.

Specifically: if label text changes (e.g., `"BASE (Xd)"` → something else), update the skill.
If a new pattern is added (e.g., a divergence signal), add it to the skill's pattern list and
the direction scoring table.

---

## Files in this repo relevant to context

- `tradingview/gemini-edge-scanner.pine` — the v2 Pine Script to review and fix
- `skill-options-directional-builder.md` — Claude skill v1.2; CHART INPUT section must stay in sync with Pine
- `CLAUDE_CONTEXT.md` — full project context (hub serves 3 trading engines)
- `WEB_SYNC_STATUS.md` — web skill sync status (skill needs re-upload after any changes)
