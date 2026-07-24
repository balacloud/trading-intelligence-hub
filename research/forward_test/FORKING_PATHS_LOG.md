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
