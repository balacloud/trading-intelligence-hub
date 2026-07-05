"""
OPTIONS IQ GEMINI — Proxy Backtest v2 (rigorous rework)
========================================================

Standalone, more rigorous rework of
/Users/balajik/projects/options_iq_gemini/options_edge_backtest.py.
Does NOT modify the original or anything in swing-trade-analyzer
(simulate_trade is imported read-only).

What this version fixes vs. the original:
  1. Universe   : the hub's actual CORE watchlist (20 names), not 5 cherry-
                  picked mega-caps. NOTE: this list STILL carries survivorship
                  bias — it is a hand-curated "known volatile/liquid" list.
  2. Time range : 2019-01-01 .. 2024-12-31, segmented into 5 market regimes,
                  each reported separately (never just one pooled number).
  3. IV/HV      : a clearly-labeled REALIZED-vol proxy for the stated core
                  edge (IV/HV < 1.0 and IVR <= 45), tested WITH and WITHOUT
                  the kinetic-timing signal. This is NOT real historical
                  implied volatility. See VOL PROXY notes below.
  4. Payoff     : Black-Scholes approximation of a 28-DTE ~0.50-delta long
                  call, revalued at the actual exit day/price, with an IV
                  transition model (partial mean-reversion toward the 90d
                  baseline plus a post-move crush haircut) + spread/commission
                  costs. Full return DISTRIBUTION reported (median, std, IQR),
                  not a bare average, plus IV-scenario sensitivity.
  5. Rigor      : Wilson 95% binomial CI on win rates, per-trade and
                  annualized Sharpe-like ratios, max drawdown on a fixed-
                  fraction equity curve, explicit n= everywhere, and TWO
                  random-entry controls (pure random, and random restricted
                  to price > 200 SMA so the trend filter's contribution can
                  be separated from the squeeze/RVOL timing).
  6. Look-ahead : v2 enters at the NEXT day's OPEN. The original filled at
                  the signal day's close even though the signal needs that
                  day's full closing volume (RVOL) and close (squeeze/SMA200)
                  — i.e., unknowable-at-fill information. simulate_trade()'s
                  own exit logic was audited and contains no look-ahead
                  (details in the report footer).

VOL PROXY (read this before quoting any IV/HV result)
-----------------------------------------------------
We do not have historical implied volatility. As a stand-in:
  * "HV-like baseline"  = 90-day annualized realized vol (RV90)
  * "IV-like current"   = 20-day annualized realized vol (RV20)
  * IV/HV < 1.0 proxy   -> RV20 / RV90 < 1.0   (short-term vol compressed
                            vs. the name's own longer baseline)
  * IVR <= 45 proxy     -> RV20 percentile rank within trailing 252d <= 0.45
A day is "vol-compressed" only if BOTH hold. This measures realized vol
compression, which correlates with — but is NOT — cheap implied vol.
Options are priced with RV20 as the IV input, which is a further
approximation. Treat every "vol" number below as a realized-vol proxy.

Circularity warning: the IV-exit model mean-reverts vol toward the RV90
baseline, which mechanically flatters compressed-vol entries (their vol
reverts UP). That is the thesis being tested, so a FROZEN-IV and a
PESSIMISTIC-CRUSH scenario are also reported; conclusions should lean on
those, not only the reversion scenario.

Run:  python3 options_edge_backtest_v2.py
Requires internet (yfinance). Writes trades CSV next to this script.
"""

import math
import os
import sys
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import yfinance as yf

# Borrow simulate_trade READ-ONLY from swing-trade-analyzer (same engine the
# original proxy backtest used, so results stay comparable).
SWING_ANALYZER_PATH = "/Users/balajik/projects/swing-trade-analyzer/backend"
sys.path.append(SWING_ANALYZER_PATH)
from backtest.trade_simulator import simulate_trade  # noqa: E402

# ─── Configuration ───────────────────────────────────────────────────────────

UNIVERSE = [
    "NVDA", "AMD", "MU", "MRVL", "AVGO", "GEV", "VRT", "PWR", "ALB", "HIVE",
    "MARA", "RIOT", "COIN", "MSTR", "PLTR", "CRWD", "BABA", "PDD", "PYPL",
    "TSLA",
]

TEST_START = "2019-01-01"
TEST_END = "2024-12-31"
BUFFER_START = "2017-06-01"   # warm-up for 200 SMA + 252d vol-rank window

RVOL_THRESHOLD = 1.5
COOLDOWN_EXTRA = 5            # same as original: cooldown = days_held + 5
MIN_BARS_AHEAD = 16           # need i+1 entry + up to 15-day hold

# Vol-compression proxy thresholds (mirror stated edge IV/HV<1.0, IVR<=45)
VOL_RATIO_MAX = 1.0           # RV20 / RV90 < 1.0
VOL_RANK_MAX = 0.45           # RV20 rank in trailing 252d <= 45th pct

# Options payoff model
DTE_ENTRY = 28                # midpoint of the system's 21-35 DTE band
RISK_FREE = 0.04
IV_FLOOR = 0.10
SPREAD_PCT = 0.03             # pay 3% of premium each way (single-name spreads)
COMMISSION_PER_SHARE = 0.0065  # $0.65/contract
IV_REVERT_FRACTION = 0.50     # exit IV: 50% mean-reversion toward RV90 base
IV_CRUSH_HAIRCUT = 0.90       # ...then a 10% post-move crush haircut
IV_CRUSH_PESSIMISTIC = 0.85   # sensitivity scenario: flat -15% IV at exit

# Random baselines
RANDOM_SEED = 42
RANDOM_ENTRY_PROB = 1.0 / 12  # ~1 candidate entry per 12 eligible days

EQUITY_FRACTION = 0.10        # 10% of equity per trade for the DD curve

REGIMES = [
    ("2019_pre_covid", "2019-01-01", "2020-02-19"),
    ("2020_covid",     "2020-02-20", "2020-12-31"),
    ("2021_bull",      "2021-01-01", "2021-12-31"),
    ("2022_bear",      "2022-01-01", "2022-12-31"),
    ("2023_24_recov",  "2023-01-01", "2024-12-31"),
]

IV_SCENARIOS = ("revert", "frozen", "crush")


# ─── Math helpers ────────────────────────────────────────────────────────────

def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bs_call(S, K, T, r, sigma):
    """Black-Scholes European call. Falls back to intrinsic at expiry."""
    if T <= 0 or sigma <= 0:
        return max(S - K, 0.0)
    sq = sigma * math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / sq
    d2 = d1 - sq
    return S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)


def wilson_ci(wins, n, z=1.96):
    """95% Wilson score interval for a binomial proportion."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = wins / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def max_drawdown_fixed_fraction(returns_in_date_order, fraction=EQUITY_FRACTION):
    """Max drawdown of an equity curve staking `fraction` of equity per trade,
    trades applied sequentially in entry-date order (overlap ignored —
    disclosed limitation)."""
    equity, peak, mdd = 1.0, 1.0, 0.0
    for r in returns_in_date_order:
        equity *= (1.0 + fraction * r)
        peak = max(peak, equity)
        if peak > 0:
            mdd = max(mdd, (peak - equity) / peak)
    return mdd


# ─── Indicators (all backward-looking; window at i uses data <= i) ───────────

def compute_indicators(df):
    close, high, low, vol = df["Close"], df["High"], df["Low"], df["Volume"]

    out = pd.DataFrame(index=df.index)
    out["sma200"] = close.rolling(200).mean()
    out["rvol"] = vol / vol.rolling(50).mean()

    # TTM squeeze: BB(20,2) fully inside KC(20,1.5*ATR)  <=>  2*std < 1.5*ATR
    std20 = close.rolling(20).std()
    tr = pd.concat(
        [high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()],
        axis=1,
    ).max(axis=1)
    atr20 = tr.ewm(alpha=1 / 20, min_periods=20).mean()
    out["squeeze"] = (2.0 * std20) < (1.5 * atr20)

    # Realized-vol proxies (annualized)
    logret = np.log(close / close.shift(1))
    out["rv20"] = logret.rolling(20).std() * math.sqrt(252)
    out["rv90"] = logret.rolling(90).std() * math.sqrt(252)
    # Percentile rank of today's RV20 within trailing 252 sessions (incl today)
    out["rv_rank"] = out["rv20"].rolling(252).rank(pct=True)
    return out


def regime_of(date):
    for name, lo, hi in REGIMES:
        if pd.Timestamp(lo) <= date <= pd.Timestamp(hi):
            return name
    return "outside"


# ─── Options payoff approximation ────────────────────────────────────────────

def price_option_trade(entry_price, exit_price, days_held, sigma_entry, sigma_base):
    """Approximate P&L of a 28-DTE ~0.50-delta long call.

    Entry : BS with IV = RV20 proxy (floored). Strike set so d1 = 0
            (K = S*exp((r + s^2/2)T)), i.e. BS delta = 0.50 exactly.
    Exit  : revalue at actual exit price with remaining time (trading days
            -> calendar via *7/5) under three IV scenarios.
    Costs : 3% of premium each way + $0.65/contract each way.

    Returns dict of {scenario: net_return} or None if unpriceable.
    """
    if (
        entry_price is None or exit_price is None
        or not np.isfinite(entry_price) or not np.isfinite(exit_price)
        or entry_price <= 0
    ):
        return None
    if sigma_entry is None or not np.isfinite(sigma_entry):
        return None
    sigma0 = max(float(sigma_entry), IV_FLOOR)
    base = float(sigma_base) if (sigma_base is not None and np.isfinite(sigma_base)) else sigma0

    T0 = DTE_ENTRY / 365.0
    K = entry_price * math.exp((RISK_FREE + 0.5 * sigma0 * sigma0) * T0)

    prem = bs_call(entry_price, K, T0, RISK_FREE, sigma0)
    cost = prem * (1 + SPREAD_PCT) + COMMISSION_PER_SHARE
    if cost <= 0.01:  # sub-penny premium: unpriceable/illiquid, skip
        return None

    cal_days = max(1, round(max(days_held, 1) * 7 / 5))
    T1 = max((DTE_ENTRY - cal_days) / 365.0, 1 / 365.0)

    sig_exit = {
        "frozen": sigma0,
        "revert": max(IV_FLOOR * 0.8,
                      (sigma0 + IV_REVERT_FRACTION * (base - sigma0)) * IV_CRUSH_HAIRCUT),
        "crush": max(IV_FLOOR * 0.8, sigma0 * IV_CRUSH_PESSIMISTIC),
    }
    out = {}
    for name, sig in sig_exit.items():
        val = bs_call(exit_price, K, T1, RISK_FREE, sig)
        proceeds = max(val * (1 - SPREAD_PCT) - COMMISSION_PER_SHARE, 0.0)
        out[name] = max(proceeds / cost - 1.0, -1.0)
    return out


# ─── Trade generation ────────────────────────────────────────────────────────

def make_trade_record(ticker, df, ind, i, strategy):
    """Enter at NEXT day's open (i+1) on a signal evaluated at day i's close.
    Uses simulate_trade with entry_idx=i so its stop/ATR/swing-low math only
    sees data through day i (knowable at signal time), while the fill price
    is day i+1's open (knowable at fill time). Day-by-day exit checks then
    begin on day i+1 — the day we are actually in the trade."""
    entry_open = df["Open"].iloc[i + 1]
    if not np.isfinite(entry_open) or entry_open <= 0:
        return None
    result = simulate_trade(df, entry_idx=i, holding_period="standard",
                            entry_price=float(entry_open))

    entry_date = df.index[i + 1]
    rv20 = ind["rv20"].iloc[i]
    rv90 = ind["rv90"].iloc[i]
    rv_rank = ind["rv_rank"].iloc[i]
    ratio = rv20 / rv90 if (np.isfinite(rv20) and np.isfinite(rv90) and rv90 > 0) else np.nan

    if np.isfinite(ratio) and np.isfinite(rv_rank):
        compressed = bool(ratio < VOL_RATIO_MAX and rv_rank <= VOL_RANK_MAX)
    else:
        compressed = None  # proxy not evaluable this day

    opt = price_option_trade(
        entry_price=float(entry_open),
        exit_price=float(result["exit_price"]),
        days_held=result["days_held"],
        sigma_entry=rv20,
        sigma_base=rv90,
    )
    if opt is None:
        return None

    rec = {
        "strategy": strategy,
        "ticker": ticker,
        "entry_date": entry_date,
        "regime": regime_of(entry_date),
        "trend_ok": bool(df["Close"].iloc[i] > ind["sma200"].iloc[i]),
        "vol_compressed": compressed,
        "rv_ratio": round(ratio, 4) if np.isfinite(ratio) else np.nan,
        "rv_rank": round(rv_rank, 4) if np.isfinite(rv_rank) else np.nan,
        "days_held": result["days_held"],
        "exit_reason": result["exit_reason"],
        "underlying_ret_pct": result["return_pct"],
        "mfe_pct": result["max_favorable_excursion"],
        "mae_pct": result["max_adverse_excursion"],
    }
    for sc in IV_SCENARIOS:
        rec[f"opt_ret_{sc}"] = round(opt[sc], 4)
    return rec


def scan_kinetic(ticker, df, ind):
    """Original sieve: TTM squeeze + RVOL>1.5 + close>200SMA, evaluated at
    day i's close; entry next open. Same cooldown scheme as the original."""
    trades, cooldown = [], 0
    start_ts, end_ts = pd.Timestamp(TEST_START), pd.Timestamp(TEST_END)
    for i in range(200, len(df) - MIN_BARS_AHEAD):
        if cooldown > 0:
            cooldown -= 1
            continue
        d = df.index[i]
        if d < start_ts or d > end_ts:
            continue
        if not ind["squeeze"].iloc[i]:
            continue
        rvol = ind["rvol"].iloc[i]
        if not np.isfinite(rvol) or rvol < RVOL_THRESHOLD:
            continue
        sma = ind["sma200"].iloc[i]
        if not np.isfinite(sma) or df["Close"].iloc[i] <= sma:
            continue
        rec = make_trade_record(ticker, df, ind, i, "kinetic")
        if rec is not None:
            trades.append(rec)
            cooldown = rec["days_held"] + COOLDOWN_EXTRA
    return trades


def scan_random(ticker, df, ind, rng):
    """Control: enter on random eligible days (no signal), same exit engine,
    same cooldown scheme, same next-open fill, same option payoff model."""
    trades, cooldown = [], 0
    start_ts, end_ts = pd.Timestamp(TEST_START), pd.Timestamp(TEST_END)
    for i in range(200, len(df) - MIN_BARS_AHEAD):
        if cooldown > 0:
            cooldown -= 1
            continue
        d = df.index[i]
        if d < start_ts or d > end_ts:
            continue
        if rng.random() >= RANDOM_ENTRY_PROB:
            continue
        rec = make_trade_record(ticker, df, ind, i, "random")
        if rec is not None:
            trades.append(rec)
            cooldown = rec["days_held"] + COOLDOWN_EXTRA
    return trades


# ─── Reporting ───────────────────────────────────────────────────────────────

def describe(trades, scenario="revert"):
    """Summary stats for a list of trade dicts under one IV scenario."""
    n = len(trades)
    if n == 0:
        return None
    rets = np.array([t[f"opt_ret_{scenario}"] for t in trades], dtype=float)
    u_rets = np.array([t["underlying_ret_pct"] for t in trades], dtype=float)
    wins = int((rets > 0).sum())
    lo, hi = wilson_ci(wins, n)
    q25, q75 = np.percentile(rets, [25, 75])
    std = rets.std(ddof=1) if n > 1 else float("nan")
    sharpe_trade = rets.mean() / std if (n > 1 and std > 0) else float("nan")

    dates = [t["entry_date"] for t in trades]
    span_years = max((max(dates) - min(dates)).days / 365.25, 0.5)
    tpy = n / span_years
    sharpe_ann = sharpe_trade * math.sqrt(tpy) if np.isfinite(sharpe_trade) else float("nan")

    order = np.argsort(np.array(dates, dtype="datetime64[ns]"))
    mdd = max_drawdown_fixed_fraction(rets[order])

    return {
        "n": n,
        "opt_win": wins / n, "ci_lo": lo, "ci_hi": hi,
        "mean": rets.mean(), "median": float(np.median(rets)),
        "std": std, "iqr_lo": q25, "iqr_hi": q75,
        "sharpe_trade": sharpe_trade, "sharpe_ann": sharpe_ann,
        "mdd": mdd,
        "u_win": float((u_rets > 0.5).mean()),
        "u_mfe": float(np.mean([t["mfe_pct"] for t in trades])),
        "u_mae": float(np.mean([t["mae_pct"] for t in trades])),
    }


def fmt_row(label, s):
    if s is None:
        return f"  {label:<26} n=0    (no trades — no conclusion possible)"
    return (
        f"  {label:<26} n={s['n']:<4d} "
        f"win {s['opt_win']*100:5.1f}% (95% CI {s['ci_lo']*100:.0f}-{s['ci_hi']*100:.0f}%) | "
        f"mean {s['mean']*100:+7.1f}% med {s['median']*100:+7.1f}% "
        f"sd {s['std']*100:6.1f}% IQR [{s['iqr_lo']*100:+.1f}%,{s['iqr_hi']*100:+.1f}%] | "
        f"Shp/tr {s['sharpe_trade']:+.2f} ann~{s['sharpe_ann']:+.2f} MDD {s['mdd']*100:.1f}%"
    )


def subset(trades, regime=None, compressed=None, trend=None):
    out = trades
    if regime is not None:
        out = [t for t in out if t["regime"] == regime]
    if compressed is not None:
        out = [t for t in out if t["vol_compressed"] is compressed]
    if trend is not None:
        out = [t for t in out if t["trend_ok"] is trend]
    return out


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print("=" * 100)
    print("OPTIONS IQ GEMINI — PROXY BACKTEST v2 (regime-segmented, vol-proxy, "
          "BS payoff, random controls)")
    print("=" * 100)
    print(f"Universe : {', '.join(UNIVERSE)}")
    print(f"Window   : {TEST_START} .. {TEST_END} (entries; data buffered from {BUFFER_START})")
    print(f"Signal   : TTM squeeze + RVOL>{RVOL_THRESHOLD} + close>200SMA, fill at NEXT open")
    print(f"Exit     : swing-trade-analyzer simulate_trade('standard') — unmodified, imported")
    print(f"Vol proxy: RV20/RV90 < {VOL_RATIO_MAX} AND RV20 252d-rank <= {VOL_RANK_MAX} "
          "(REALIZED-vol stand-in, NOT implied vol)")
    print(f"Payoff   : BS long call, {DTE_ENTRY} DTE, delta 0.50 strike, IV=RV20, "
          f"costs {SPREAD_PCT*100:.0f}%/side + ${COMMISSION_PER_SHARE*100:.0f}c/contract")
    print()

    rng = np.random.default_rng(RANDOM_SEED)
    kinetic, random_trades = [], []
    coverage_notes, per_ticker_n = [], {}

    for ticker in UNIVERSE:
        try:
            df = yf.download(ticker, start=BUFFER_START, end="2025-01-01",
                             progress=False, auto_adjust=True)
        except Exception as e:
            coverage_notes.append(f"{ticker}: download FAILED ({e}) — not tested")
            continue
        if df is None or df.empty:
            coverage_notes.append(f"{ticker}: no data returned — not tested")
            continue
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna(subset=["Close", "Open", "High", "Low", "Volume"])
        if getattr(df.index, "tz", None) is not None:
            df.index = df.index.tz_localize(None)

        if len(df) < 200 + MIN_BARS_AHEAD:
            coverage_notes.append(
                f"{ticker}: only {len(df)} bars (first {df.index[0].date()}) — "
                "insufficient for 200SMA warm-up, not tested")
            continue
        first_eligible = df.index[200].date()
        if first_eligible > pd.Timestamp(TEST_START).date():
            coverage_notes.append(
                f"{ticker}: data starts {df.index[0].date()}; first eligible entry "
                f"~{first_eligible} (missing earlier regimes)")

        ind = compute_indicators(df)
        kt = scan_kinetic(ticker, df, ind)
        rt = scan_random(ticker, df, ind, rng)
        kinetic.extend(kt)
        random_trades.extend(rt)
        per_ticker_n[ticker] = len(kt)
        print(f"  {ticker:<6} bars={len(df):<5} kinetic signals={len(kt):<4} random entries={len(rt)}")

    all_trades = kinetic + random_trades
    if not kinetic:
        print("\nNo kinetic signals found anywhere — nothing to evaluate.")
        return

    # Persist raw trades for audit
    out_csv = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "backtest_v2_trades.csv")
    pd.DataFrame(all_trades).to_csv(out_csv, index=False)

    strategies = [
        ("KINETIC (all)",            subset(kinetic)),
        ("KINETIC + vol-compressed", subset(kinetic, compressed=True)),
        ("KINETIC, NOT compressed",  subset(kinetic, compressed=False)),
        ("RANDOM (pure control)",    subset(random_trades)),
        ("RANDOM > 200SMA (trend)",  subset(random_trades, trend=True)),
    ]

    print("\n" + "=" * 100)
    print("POOLED RESULTS — option returns under the REVERT IV scenario "
          "(50% reversion to RV90 base, then -10% crush)")
    print("=" * 100)
    for label, trs in strategies:
        print(fmt_row(label, describe(trs)))

    print("\n" + "=" * 100)
    print("PER-REGIME RESULTS (revert scenario) — a signal that only works in "
          "one regime is a different animal")
    print("=" * 100)
    for regime, lo, hi in REGIMES:
        print(f"\n-- {regime}  ({lo} .. {hi}) --")
        for label, trs in strategies:
            print(fmt_row(label, describe(subset(trs, regime=regime))))

    print("\n" + "=" * 100)
    print("UNDERLYING-ONLY VIEW (what the original backtest measured) — "
          "kinetic vs random, pooled")
    print("=" * 100)
    for label, trs in strategies:
        s = describe(trs)
        if s:
            print(f"  {label:<26} n={s['n']:<4d} stock win {s['u_win']*100:5.1f}% | "
                  f"avg MFE +{s['u_mfe']:.2f}% | avg MAE -{s['u_mae']:.2f}%")

    print("\n" + "=" * 100)
    print("IV-SCENARIO SENSITIVITY (pooled mean / median option return) — "
          "the revert scenario partially assumes the thesis;")
    print("if the sign of the edge flips under FROZEN or CRUSH, the result is "
          "model-dependent, not robust")
    print("=" * 100)
    header = f"  {'strategy':<26} " + "".join(f"{sc:>22}" for sc in IV_SCENARIOS)
    print(header)
    for label, trs in strategies:
        if not trs:
            continue
        cells = []
        for sc in IV_SCENARIOS:
            r = np.array([t[f"opt_ret_{sc}"] for t in trs])
            cells.append(f"{r.mean()*100:+7.1f}%/{np.median(r)*100:+6.1f}%")
        print(f"  {label:<26} " + "".join(f"{c:>22}" for c in cells))

    print("\n" + "=" * 100)
    print("SAMPLE SIZES")
    print("=" * 100)
    print("  Kinetic signals per ticker: " + ", ".join(
        f"{t}={n}" for t, n in sorted(per_ticker_n.items(), key=lambda x: -x[1])))
    nc_none = len([t for t in kinetic if t["vol_compressed"] is None])
    print(f"  Kinetic signals where vol proxy was not evaluable (insufficient "
          f"rank history): {nc_none}")
    print("  Kinetic n per regime: " + ", ".join(
        f"{r}={len(subset(kinetic, regime=r))}" for r, _, _ in REGIMES))

    print("\n" + "=" * 100)
    print("DATA COVERAGE / MISSING HISTORY")
    print("=" * 100)
    for note in coverage_notes or ["  (all tickers had full-window data)"]:
        print(f"  {note}")

    print("\n" + "=" * 100)
    print("METHOD DISCLOSURES (do not quote results without these)")
    print("=" * 100)
    print("""\
  1. SURVIVORSHIP BIAS: the universe is the hub's own hand-curated CORE list
     of known volatile/liquid names. It is NOT a neutral universe. Several
     names (MARA, RIOT, MSTR, PLTR, COIN, NVDA...) are on the list BECAUSE
     they already had historic runs. All absolute return numbers are inflated
     by this; the random-entry control on the SAME universe is the honest
     yardstick, since it shares the same bias.
  2. VOL PROXY: 'vol-compressed' means realized-vol compression (RV20 vs
     RV90 / 252d rank), not cheap implied vol. Real IV/HV and IVR gates
     remain UNTESTED historically. Option pricing uses RV20 as IV — actual
     entry premiums for these names would usually be richer (IV > RV),
     which would make real option returns WORSE than modeled here.
  3. PAYOFF MODEL: European BS, flat 4% rate, no skew, no term structure,
     no earnings-date IV dynamics, delta-0.50 strike assumed always
     available, 3%/side spread. Approximation, not execution-grade.
  4. LOOK-AHEAD AUDIT of simulate_trade() (read-only, unmodified):
       - No look-ahead found in exit logic. The 10/21 EMA trail is computed
         with adjust=False (recursive), so its value at bar j uses only data
         through bar j. Stops/targets/swing-low/ATR use data through the
         entry index. Same-day stop+target collisions resolve to the STOP
         (conservative).
       - Residual optimism (not look-ahead): stop exits fill exactly AT the
         stop price even when the day gapped below it; real fills on gap
         days would be worse. Applies equally to signal and control.
       - Fixed in v2 harness: the ORIGINAL backtest filled at the signal
         day's own close although RVOL/squeeze/SMA need that day's full
         session to compute. v2 evaluates the signal at day i's close and
         fills at day i+1's OPEN.
  5. DD/SHARPE CAVEATS: equity curve stakes 10% per trade sequentially and
     ignores overlapping positions across tickers; annualized Sharpe is a
     per-trade ratio scaled by sqrt(trades/year). Directional indicators
     only.
  6. LONG-CALL ONLY: the sieve requires price > 200 SMA, so only the debit-
     CALL side of the engine is testable here; the put side has zero
     backtest coverage in v1 and v2 alike.
  7. Cooldown (days_held + 5) after each entry matches the original; the
     random control uses the same cooldown so trade density is comparable.""")
    print(f"\n  Raw trades written to: {out_csv}")


if __name__ == "__main__":
    main()
