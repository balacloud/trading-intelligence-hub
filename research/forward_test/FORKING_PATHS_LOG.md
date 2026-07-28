# Forking Paths Log — Forward Test Exploratory Analyses

> Every exploratory question asked of the forward-test data gets an entry here, whether or not it turns out to look interesting. Purpose: at the confirmatory pass (n≈30/group), this is the record that separates "predicted in advance" from "found by looking." See `FORWARD_TEST_PROTOCOL.md`'s Interpretation Guardrails section for the rules governing this log.

**Format per entry:** date, n at the time (resolved per group), the question, the answer, and whether it should feed a specific hypothesis for the confirmatory pass.

---

## 2026-07-21 — Entry 1 (logged retroactively — asked before this log existed)

**n at the time:** 11 resolved (6 SURVIVOR, 5 REJECT — excludes 1 `BUILDER_MIXED` non-event), 7 open.

**Question:** Interim win rate comparison — is REJECT outperforming SURVIVOR, and if so does that mean the gates are backwards?

**Answer:** REJECT win rate 60% (3/5) vs SURVIVOR 50% (3/6) at this n. Labeled MONITORING-state initially, then discussed with causal framing before this guardrail section existed — a real instance of exactly the failure mode this log is meant to prevent. No action taken (no threshold changed), but the discussion ran ahead of what n=11 supports.

**Feeds a hypothesis for n=30:** Not on its own — the raw win-rate gap at n=11 is statistical noise per the pre-registered power analysis (detects only large effects at n=30, and n=11 is well short of that). Retained here only as a timestamp of when the question was first asked, not as a standing hypothesis.

---

## 2026-07-21 — Entry 2 (logged retroactively — asked before this log existed)

**n at the time:** same as Entry 1 — 11 resolved, plus the 9 REJECT rows logged to date (7 IV/HV-gate misses, 2 liquidity-gate misses).

**Question:** What gate did each REJECT actually fail, and how close to the threshold was it? Does "near-miss margin" explain the REJECT group's performance?

**Answer:** Of 7 REJECTs that failed the IV/HV<100% gate, 4 (URA 100.4%, XLF 101.7%, INFQ 100.0%, JD 102.1%) missed by under 2 points — essentially indistinguishable from a qualifying survivor on that metric alone. The other 3 (MP 108.3%, OKLO 109.8%, NIO 113.0%) missed by a wider margin. The 2 HIVE REJECTs and the 1 UUUU REJECT didn't fail the IV/HV gate at all (91.1%, 93.9%, 92.2% — all genuinely sub-100%) — they were excluded on liquidity or earnings-timing instead, unrelated to the pricing edge.

**Feeds a hypothesis for n=30:** Yes — this is a genuine candidate hypothesis worth testing formally once powered: **the IV/HV<100% cutoff may behave as a smooth gradient near the boundary rather than a sharp discontinuity**, meaning near-miss rejects (say, 100–105%) may perform statistically indistinguishably from just-qualifying survivors (say, 95–100%), while far-miss rejects (>110%) may show a real gap. This was NOT specified in the original pre-registered criterion (which treats REJECT as one undifferentiated group).

**RESOLVED same day (Jul 21, 2026):** locked as a pre-registered secondary test in `FORWARD_TEST_PROTOCOL.md` ("Pre-registered secondary test — IV/HV near-miss margin"), buckets fixed at NEAR (<2pts) / MID (2–10pts) / FAR (>10pts), before any further resolved trades accumulated. This hypothesis has graduated from exploratory to confirmatory-pending-power — future references to it should cite the protocol section, not this log entry, as the source of truth.

---

## 2026-07-24 — Entry 3 (Session 33 close)

**Process note first:** this file existed on disk since Session 30 (Jul 21) but was never `git add`ed or committed — three session closes went by citing it as authoritative without it ever entering version control. Found while adding this entry, not by going looking for it. Committing it for real as part of this session's close.

**n at the time:** 10 resolved SURVIVOR (3 TARGET / 7 STOP), 8 resolved REJECT (5 TARGET / 3 STOP) — real positions only, `BUILDER_MIXED` excluded.

**Question (Bala's observation, candid, mid-session-close):** "The losers which are in loss should have taken the opposite call" — i.e., would the opposite-direction contract (put instead of call, or vice versa) on the same underlying have won?

**Answer, checked against today's 4 real STOP-outs specifically:**

| ticker | direction taken | entry underlying | underlying now | moved |
|---|---|---|---|---|
| PL | CALL (bullish) | $22.21 | $20.59 | down 7.3% |
| DRAM | CALL (bullish) | $58.51 | $53.28 | down 8.9% |
| POET | CALL (bullish) | $8.015 | $6.885 | down 14.1% |
| CAG | PUT (bearish) | $14.24 | $14.76 | up 3.7% |

All 4 underlyings genuinely moved against their bet's direction — verified live via Tradier quotes. Literally: the opposite side would have gained on all 4 of today's specific losers.

**The catch:** this is close to tautological. A losing directional option position means, by definition, the underlying moved against the bet — checking only the STOP-outs (never the TARGET-hitters, which moved *with* their bet) is a selection-biased way to ask whether direction-inference itself is systematically backwards. The real, non-tautological question is: **across all resolved positions including wins, does the direction call (technicals.py's SMA/EMA-based BULLISH/BEARISH vote) do better or worse than chance — or than its own inverse?** That's genuinely testable but hasn't been computed at all yet, in either arm, and isn't answerable from today's 4-name slice.

**Feeds a hypothesis for n=30:** Yes, a real candidate — a future confirmatory pass could split all resolved positions by direction-inference agreement/disagreement with the eventual price move and check whether direction quality itself is better than a coin flip. Not locked as a secondary test yet (unlike Entry 2's margin-bucket hypothesis) — needs a larger resolved sample before locking is even meaningful, and locking prematurely on a 4-name slice would be exactly the kind of goalpost-moving Guardrail 1 exists to block.

---

## 2026-07-24 — Entry 4 (same-day follow-up to Entry 3, full resolved-set check)

**n at the time:** 18 total resolved (10 SURVIVOR: 3 TARGET/7 STOP; 8 REJECT: 5 TARGET/3 STOP).

**Question:** Entry 3 only checked today's 4 STOP-outs, which is tautological (a losing directional bet means the underlying moved against it, by definition). The non-tautological version: across the **full resolved set, wins included**, does the direction call (bullish call / bearish put) actually predict the outcome, or would the opposite direction have done better on average?

**Answer:** Split by `trend_200d` (a proxy for the direction taken — UPTREND rows are bullish/call bets, DOWNTREND rows are bearish/put bets):
- `UPTREND`: n=5, **0 TARGET / 5 STOP** (0% win rate).
- `DOWNTREND`: n=11, **7 TARGET / 4 STOP** (64% win rate).
- `INSUFFICIENT_HISTORY`: n=2, 1 TARGET / 1 STOP (not attributable either way).

Every single bullish/call position resolved has lost; bearish/put positions have won nearly two-thirds of the time. This is the real, denominator-complete version of Bala's original observation — not just "losers moved against their bet" (tautological) but "calls have actually underperformed puts across the whole resolved sample so far, wins included."

**A second, related pattern surfaced in the same pass:** TARGET-hitters averaged **97.9%** IV/HV at entry vs. STOP-outs' **92.2%** — winners were priced *closer* to the buying-edge ceiling, not cheaper, the opposite of what the core IV/HV-compression thesis would predict. This lines up with `FORWARD_TEST_PROTOCOL.md` Guardrail 3a's already-documented suspicion (from Gemini's own Phase 17 note) that the kinetic-timing signal (squeeze/RVOL) might be doing the real work, not the IV/HV edge itself.

**Feeds a hypothesis for n=30:** Yes, now a stronger candidate than Entry 3's version — a future confirmatory pass should test direction (call vs. put) as its own factor, independent of the SURVIVOR/REJECT split, alongside an IV/HV-level-at-entry split for TARGET vs. STOP. Still **not locked** as a secondary test: n=5 for the UPTREND bucket is small enough that an all-STOP result has a real (~3-6%) chance under pure noise, and locking a bucket split now, right after noticing it looks interesting, would be exactly the "the interim number is already convincing" failure mode Guardrail 1 exists to block. Revisit once resolved counts are meaningfully larger — this entry exists so that if the pattern holds, it counts as predicted in advance, not found by looking after the fact.

---

## 2026-07-27 — Entry 5 (independent cross-source convergence with Entry 4, via Gemini's own Stage-2 review)

**n at the time:** 18 resolved (10 SURVIVOR: 3 TARGET/7 STOP; 8 REJECT: 5 TARGET/3 STOP) — unchanged from Entry 4, since nothing has resolved between Jul 24 and today; today's session only added new OPEN positions (MXL, DRAM #2, MSM, ALV, LW, XPEV, HPE, LI).

**Question:** Gemini's own dev session, acting as "Senior Partner" reviewing recent closed trades independently (not prompted by this hub's Entry 4, which it doesn't appear to have seen), asked essentially the same question cold: are we too strict, or are we getting direction wrong? It walked four named positions — PATH (REJECT, IV/HV 101% barely over the ceiling, BEARISH 3/5, TARGET +74.48%), CAG (SURVIVOR, BEARISH 3/5 downtrend-aligned, STOP -37.5%), PL (SURVIVOR, downtrend, but a narrow BULLISH 3/5 vote bought a Call into it, STOP -45.56%), and DRAM's Jul 22 entry (SURVIVOR, `INSUFFICIENT_HISTORY`, mechanical rule forced a BULLISH call anyway, STOP -37.99%) — and proposed: don't loosen the IV/HV ceiling, and start heavily scrutinizing any narrow mechanical vote that contradicts the SMA200 primary trend, without changing any code today.

**Verification, not accepted on the summary alone:** every number Gemini cited was checked directly against `forward_test_log.csv` before treating any of it as reliable — all four confirmed exact or near-exact (PL/DRAM percentages rounded to one decimal, everything else exact). Genuinely accurate, not overstated.

**Answer:** This converges with Entry 4's own finding — "respect the primary trend" is the same underlying signal as Entry 4's UPTREND/DOWNTREND split (0/5 vs. 7/11) — but from an independent source (Gemini's own qualitative review of 4 named trades) reaching a compatible conclusion to a quantitative split-by-direction check run three days earlier on the full resolved set. Two independent methods landing on the same read is a real point in its favor, not just a repeat of the same look. **One thing Gemini's clean story doesn't explain: CAG.** CAG's vote *was* trend-aligned (bearish put, confirmed downtrend) and it still stopped out -37.5% — "respect the trend" would not have saved CAG. The rule as proposed would have avoided PL and the Jul-22 DRAM loss, but trend-alignment alone isn't sufficient to avoid a loss either.

**Feeds a hypothesis for n=30:** Yes — the same one Entry 4 already flagged (direction as its own factor), now with an independent qualitative confirmation on top of the quantitative split. Still **not locked**, for the same reason as Entry 4: n=5 in the smallest bucket is too small to rule out noise. Gemini's own proposed action (heavier judgment-layer scrutiny of trend-contradicting votes, no code or gate change) matches this hub's own stance on Entry 4 exactly — log it, apply it as soft judgment, don't lock it into a rule until the confirmatory sample supports it.

---

## 2026-07-28 — Entry 6 (Session 37: the split regressed toward noise the moment n grew, and Gemini repeated its Entry-5 review without seeing this)

**n at the time:** 25 resolved (13 SURVIVOR: 3 TARGET/10 STOP; 12 REJECT: 7 TARGET/5 STOP) — up from Entry 5's 18, via a `resolve_positions.py` batch run Jul 27 that was sitting uncommitted in `forward_test_log.csv` when this session opened.

**Context:** Bala relayed the same Gemini "Senior Partner" review already logged as Entry 5 (PATH/CAG/PL/DRAM, propose "respect the SMA200 trend, scrutinize narrow votes against it"). Before crediting it again, re-ran Entry 4's UPTREND/DOWNTREND split against the now-larger resolved set, since Entry 5 explicitly flagged the smallest bucket (UPTREND, n=5) as too small to trust.

**Answer:** The split moved a lot in one resolution batch:
- `UPTREND` (calls): was 0/5 (0%) at Entry 4 → now **2/9 TARGET (22%)**. The 2 new wins: XLF +75.96% (resolved 2026-07-27, entered 2026-07-23) and LW +69.23% (resolved same-day it was entered, 2026-07-27 — a same-day TARGET hit on a fresh entry, flagged below as worth a sanity check, not yet verified independently).
- `DOWNTREND` (puts): was 7/11 (64%) at Entry 4 → now **7/13 TARGET (54%)**. The 2 new losses are exactly the two names Entry 5 already discussed: a second PATH Put (entered 2026-07-24, trend-aligned BEARISH 2/2, STOP -55.38%) and a second CAG Put (entered 2026-07-24, trend-aligned BEARISH 2/3, STOP -50.0%) — both fully aligned with "respect the trend" and both still lost.

**Why this matters more than a routine update:** Entry 4/5's persuasiveness leaned hard on UPTREND's clean 0-for-5 — exactly the kind of extreme-looking split `TRADER_LENS.md` says to distrust more, not less, the cleaner it looks. One resolution batch cut that gap roughly in half (0% vs 64% → 22% vs 54%). The direction (puts outperforming calls) still holds, but it's now a much softer signal, and it moved this much on 7 new data points — a concrete demonstration of exactly how far a "compelling" small-n split can still be from a stable one. Separately, the two new DOWNTREND losses are trend-aligned trades that still stopped out — not a new counter-example, but a second and third confirmation of the same gap Entry 5 already named for CAG: respecting the trend would not have saved either one.

**Not yet independently checked:** LW's same-day entry-to-TARGET resolution (a ~69% option-premium move in one session) — plausible if the underlying gapped hard, but fast+large is exactly the shape TRADER_LENS says to verify before trusting, not after. Worth a live Tradier quote/news check next session, low urgency (doesn't gate anything, `resolve_positions.py` pulls its own independent quote same as every other resolution).

**Feeds a hypothesis for n=30:** Same standing hypothesis as Entry 4/5 (direction as its own factor) — this entry doesn't add a new one, it updates the evidence behind it and records that the update moved the needle materially. Still **not locked**. Gemini's proposed posture (soft judgment-layer scrutiny, no gate change) remains the right call, but its own write-up should be told the UPTREND side of its argument is weaker than it was three days ago, not stronger.
