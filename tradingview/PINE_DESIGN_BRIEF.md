# Gemini Edge Scanner — Pine Script v2 Design Brief
# Context document for Opus model

---

## What This Is

A TradingView Pine Script indicator that serves as **Claude's eyes on the chart** for the
Options IQ Gemini trading pipeline. When a user pastes a TradingView screenshot into Claude
alongside a ticker, Claude reads the chart to infer directional bias (BULLISH / BEARISH / NEUTRAL)
and extract key levels — all of which feed into a structured JSON handoff for the Gemini backend.

**The chart is not for the human to read in isolation. It is designed so Claude can extract
structured signals from a screenshot.** This means every signal must have a clear text label,
not just a color.

---

## Hard Constraints

- **Pine Script v5 only**
- **1 indicator slot** (user has max 2 total; this script uses 1)
- **Daily chart, 1–2 year view** — NOT 5-min. 5-min is execution timing; this is selection.
- **Overlay indicator** (`overlay=true`) — everything on the price chart, no separate pane
- **No `request.security()` multi-timeframe** — keep it simple for iterative testing
- **TradingView plan unknown** — start conservative: `max_lines_count=20`, `max_boxes_count=20`,
  `max_labels_count=50`. User will test and we'll expand if their plan supports it.

---

## What the Script Must Show

### 1. Trend Structure (Layer 1)
- **EMA 21** (orange, linewidth=1) — short-term momentum
- **EMA 50** (blue, linewidth=2) — intermediate trend
- **EMA 200** (gold #FFD700, linewidth=2) — trend backbone
- **Trend background tint** (very subtle, ~93% transparent):
  - Green: `close > e200 AND e50 > e200 AND e21 > e50`
  - Red: `close < e200 AND e50 < e200 AND e21 < e50`
  - Gray: everything else (mixed/neutral)
- **Trend label** — top-right of chart on last bar, prominent:
  - `"▲  UPTREND"` → green label box, white text, size=normal
  - `"▼  DOWNTREND"` → red label box, white text, size=normal
  - `"◆  NEUTRAL"` → gray label box, white text, size=normal

### 2. S/R Zones (Layer 2) — THE CORE REQUIREMENT

**Use `box.new()` for ZONES, not `line.new()` for lines.**

S/R is not a single price — it's a cluster zone. Zones communicate this better and are
easier for Claude to read from a screenshot.

**Zone height:** ±0.75% of the pivot price level.
Example: pivot at $100.00 → zone top = $100.75, zone bottom = $99.25.

**Zone colors:**
- Resistance (above price): `bgcolor=color.new(color.red, 75)`, `border_color=color.new(color.red, 40)`
- Support (below price): `bgcolor=color.new(color.green, 75)`, `border_color=color.new(color.green, 40)`

**Zone labels** (text inside box, right-aligned):
- `"R  $XX.XX"` for resistance zones
- `"S  $XX.XX"` for support zones

**Filtering logic (CRITICAL — prevents clutter on daily chart):**

```
1. Only show zones where the pivot price is within 30% of current close price
2. Cluster: if a new pivot is within 1.5% of an existing tracked level → skip it (already covered)
3. Hard cap: maximum 3 resistance zones + 3 support zones on screen at any time
4. On each new pivot, check the existing array before drawing a new box
```

Implementation with arrays:
```pine
var array<box>   res_boxes  = array.new<box>()
var array<float> res_levels = array.new<float>()
var array<box>   sup_boxes  = array.new<box>()
var array<float> sup_levels = array.new<float>()
```

On each bar, extend existing boxes to the right:
```pine
for b in res_boxes
    box.set_right(b, bar_index)
for b in sup_boxes
    box.set_right(b, bar_index)
```

**Special levels (always drawn, ignore proximity filter):**
- 52-week high: distinct orange dashed line + label `"52W HIGH  $XX.XX"` (size=small)
- 52-week low: distinct teal dashed line + label `"52W LOW  $XX.XX"` (size=small)
- These are KEY psychological levels. Options traders always watch them.

Pivot detection:
```pine
ph = ta.pivothigh(high, i_pl, i_pr)   // defaults: left=10, right=10
pl = ta.pivotlow(low,   i_pl, i_pr)
```

### 3. Price Action Patterns (Layer 3)

**A. BASE / Consolidation:**
```
atr14    = ta.atr(14)
atr_avg  = ta.sma(atr14, 20)
tight    = atr14 < atr_avg * 0.65
```
- Count consecutive tight bars: `tight_run := tight ? tight_run + 1 : 0`
- `in_base = tight_run >= 5`
- Purple background (87% transparent) while in_base
- Label when base STARTS: `"BASE (Xd)"` where X = tight_run — purple box, white text, below bar
- Update the label text each bar while in base to show growing duration (or just label start)

**B. WEDGE Detection (linear regression approach):**
```pine
res_slope = ta.linreg(high, 20, 0) - ta.linreg(high, 20, 1)   // slope of highs
sup_slope = ta.linreg(low,  20, 0) - ta.linreg(low,  20, 1)   // slope of lows

sym_triangle = res_slope < -0.05 and sup_slope >  0.05         // converging: bearish R, rising S
asc_wedge    = res_slope >  0.05 and sup_slope >  0.05 and sup_slope > res_slope   // both up, S steeper (bearish pattern)
desc_wedge   = res_slope < -0.05 and sup_slope < -0.05 and sup_slope > res_slope   // both down, R steeper (bullish pattern)
```
- Only fire wedge labels when `in_base OR bb_width < bb_avg * 0.8` (consolidation context)
- Labels on last bar:
  - sym_triangle: `"△ TRIANGLE"` (gray label)
  - asc_wedge: `"⌒ WEDGE ▲  bearish"` (orange label)
  - desc_wedge: `"⌣ WEDGE ▼  bullish"` (blue label)

**C. BREAKOUT / BREAKDOWN:**
```pine
var float last_r = na    // most recent pivot high level
var float last_s = na    // most recent pivot low level

if not na(ph) [update last_r]
if not na(pl) [update last_s]

breakout  = not na(last_r) and close > last_r and close[1] <= last_r and hi_vol
breakdown = not na(last_s) and close < last_s and close[1] >= last_s and hi_vol
```
- `plotshape(breakout,  ...)` → lime triangle above bar, text="BREAK↑"
- `plotshape(breakdown, ...)` → red triangle below bar, text="BREAK↓"

**D. FAILED BREAKOUT / FAILED BREAKDOWN:**
```pine
failed_bo = not na(last_r) and high[1] <= last_r and high > last_r and close < last_r
failed_bd = not na(last_s) and low[1]  >= last_s and low  < last_s and close > last_s
```
- `plotshape(failed_bo, ...)` → orange × above bar, text="FAILED↑"
- `plotshape(failed_bd, ...)` → orange × below bar, text="FAILED↓"

### 4. Volume Signals (Layer 4)

No separate volume pane (overlay only). Signal via candle color + label.

```pine
vol_ma = ta.sma(volume, 20)
rvol   = volume / vol_ma
hi_vol = rvol >= 1.5
bull_c = close >= open
```

**Candle color (barcolor):**
- hi_vol + bull → `color.lime` (bright — institutional buying)
- hi_vol + bear → `color.red`  (bright — institutional selling)
- normal bull   → `color.new(color.green, 50)` (dim)
- normal bear   → `color.new(color.red,   50)` (dim)

**RVOL label on last bar** (bottom of bar, small):
```
"RVOL  2.31  ⚡"   (if hi_vol)
"RVOL  0.87"       (if normal)
```
Navy background, white text, style=label.style_label_up

---

## Complete Signal Reading Guide (for Claude)

When Claude sees the screenshot, it extracts:

| Visual element | What Claude reads |
|---|---|
| Top-right label | Trend call: UPTREND / DOWNTREND / NEUTRAL |
| EMA positions | Are EMAs fanning out or converging? Is price above/below 200? |
| Red shaded zones above price | Resistance: price and how close |
| Green shaded zones below price | Support: price and how close |
| "52W HIGH" / "52W LOW" lines | Key psychological ceiling/floor |
| Purple background | BASE forming — duration from label |
| WEDGE / TRIANGLE label | Pattern type + directional implication |
| Lime/red bright candle | High-volume bar — which direction, at what level |
| "BREAK↑" / "BREAK↓" triangle | Confirmed breakout/breakdown with volume |
| "FAILED↑" / "FAILED↓" × | Bull trap / bear trap |
| RVOL label bottom | Current session volume vs 20-day average |

---

## v1 Code (Current — for Opus to review and improve)

```pine
//@version=5
indicator("Gemini Edge Scanner", overlay=true, max_lines_count=30, max_labels_count=100)

i_pl    = input.int(10,    "Pivot Left Bars",           group="S/R",      minval=3)
i_pr    = input.int(10,    "Pivot Right Bars",          group="S/R",      minval=3)
i_e21   = input.int(21,    "EMA Fast",                  group="Trend")
i_e50   = input.int(50,    "EMA Mid",                   group="Trend")
i_e200  = input.int(200,   "EMA Slow (trend backbone)", group="Trend")
i_batr  = input.float(0.65,"Base: ATR < avg ×",        group="Patterns", minval=0.3, maxval=1.0)
i_bbars = input.int(5,     "Base: min tight bars",      group="Patterns", minval=2)
i_vlen  = input.int(20,    "Volume MA length",          group="Volume")
i_rvol  = input.float(1.5, "High-vol RVOL threshold",   group="Volume")

e21  = ta.ema(close, i_e21)
e50  = ta.ema(close, i_e50)
e200 = ta.ema(close, i_e200)

plot(e21,  "EMA 21",  color=color.orange, linewidth=1)
plot(e50,  "EMA 50",  color=color.blue,   linewidth=2)
plot(e200, "EMA 200", color=color.yellow, linewidth=2)

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

ph = ta.pivothigh(high, i_pl, i_pr)
pl = ta.pivotlow(low,   i_pl, i_pr)

var float last_r = na
var float last_s = na

if not na(ph)
    last_r := ph
    line.new(bar_index[i_pr], ph, bar_index, ph,
             color=color.new(color.red, 20), style=line.style_dashed,
             width=1, extend=extend.right)
    label.new(bar_index[i_pr], ph,
              "R  " + str.tostring(ph, format.mintick),
              style=label.style_label_right,
              color=color.new(color.red, 55), textcolor=color.white, size=size.tiny)

if not na(pl)
    last_s := pl
    line.new(bar_index[i_pr], pl, bar_index, pl,
             color=color.new(color.green, 20), style=line.style_dashed,
             width=1, extend=extend.right)
    label.new(bar_index[i_pr], pl,
              "S  " + str.tostring(pl, format.mintick),
              style=label.style_label_right,
              color=color.new(color.green, 55), textcolor=color.white, size=size.tiny)

atr14   = ta.atr(14)
atr_avg = ta.sma(atr14, 20)
tight   = atr14 < atr_avg * i_batr

var int tight_run = 0
tight_run := tight ? tight_run + 1 : 0
in_base   = tight_run >= i_bbars

bgcolor(in_base ? color.new(color.purple, 87) : na, title="Base / Consolidation")

if in_base and not in_base[1]
    label.new(bar_index, low * 0.997, "BASE",
              style=label.style_label_up, color=color.purple,
              textcolor=color.white, size=size.small)

vol_ma = ta.sma(volume, i_vlen)
rvol   = volume / vol_ma
hi_vol = rvol >= i_rvol
bull_c = close >= open

barcolor(hi_vol and bull_c     ? color.lime :
         hi_vol and not bull_c ? color.red  :
         bull_c                ? color.new(color.green, 50) :
                                 color.new(color.red,   50))

if barstate.islast
    rv_str = "RVOL  " + str.tostring(rvol, "#.##") + (hi_vol ? "  ⚡" : "")
    label.new(bar_index, low * 0.993, rv_str,
              style=label.style_label_up,
              color=color.new(color.navy, 50), textcolor=color.white, size=size.tiny)

breakout  = not na(last_r) and close > last_r and close[1] <= last_r and hi_vol
breakdown = not na(last_s) and close < last_s and close[1] >= last_s and hi_vol
failed_bo = not na(last_r) and high[1] <= last_r and high > last_r and close < last_r

plotshape(breakout,  "Breakout",        shape.triangleup,   location.abovebar,
          color.lime,   size=size.small, text="BREAK↑")
plotshape(breakdown, "Breakdown",       shape.triangledown, location.belowbar,
          color.red,    size=size.small, text="BREAK↓")
plotshape(failed_bo, "Failed Breakout", shape.xcross,       location.abovebar,
          color.orange, size=size.small, text="FAILED↑")
```

---

## Known Issues With v1 to Fix in v2

1. **S/R lines instead of zones** — draws a thin dashed line for EVERY pivot. On a 1-year daily
   chart this creates 20+ lines. Cluttered and hard to read in a screenshot.
2. **No clustering** — two pivots at $99 and $101 draw two separate lines 2% apart.
3. **No cap** — all pivots drawn regardless of distance from current price.
4. **No 52-week high/low** — major psychological levels missing.
5. **No wedge detection** — user specifically requested this.
6. **BASE label doesn't show duration** — just "BASE" with no day count.
7. **Failed breakdown missing** — only failed breakout above resistance; need the mirror below support.
8. **max_lines_count=30, max_labels_count=100** — may exceed TradingView free plan. Start lower.

---

## Output Required From Opus

1. Complete, working Pine Script v5 code implementing everything in this brief
2. Comments in code only where logic is non-obvious (no explanatory paragraphs)
3. Conservative resource limits (max_boxes_count=15, max_labels_count=40, max_lines_count=10)
   so it works on the free plan — can increase if user's plan supports it
4. The script should compile cleanly in TradingView Pine Editor with no red errors
5. Brief note on any Pine Script v5 limitations that prevented exact implementation
   of any spec item (e.g. true volume profile is impossible in Pine — confirm this)
