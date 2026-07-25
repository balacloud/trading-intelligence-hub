---
name: cross-repo-fix-verification
description: "Verify a claimed fix, change, or new feature reported from a coordinating project (e.g., Options IQ Gemini, or any repo this hub coordinates with) before accepting it as true. Trigger this skill whenever the user reports that an external agent has 'fixed', 'resolved', 'implemented', 'built', or 'deployed' something — especially when the report uses confident language like 'fully resolved', 'mathematically proved', 'airtight', 'completely automated', or 'guaranteed'. Never accept a summary at face value. Read the live code, run any test suite that exists, and actually execute claimed scripts/behaviors rather than just reading them."
---

# Cross-Repo Fix Verification

You are verifying a claim, not summarizing one. The report you were given describes what someone *intended* to do or *believes* they did — your job is to check what the code actually does.

**Why this exists:** this project has caught the same class of error repeatedly — a doc says "resolved" when the fix was never tested against live data, a backtest says "mathematically proved" when it tested a different signal than claimed, an "automated" script silently writes broken output with a success message if run from the wrong directory. Every one of these was only caught by actually reading and running the code, not by reading the summary describing it.

---

## Step 1 — Read the live files directly, not the summary

Read the actual file(s) the report claims were changed. Get line numbers, exact strings, exact logic — not paraphrase. If the report names specific functions or line numbers, go to them. If it doesn't, find them yourself (`grep`/`Read`).

## Step 2 — If a test suite exists, run it. Don't take "tests pass" on faith.

`pytest`, or whatever the project uses. A claimed "3/3 pass" is a fact to confirm, not a fact to relay.

## Step 3 — Actually execute claimed behavior, don't just read the code that implements it

Reading code tells you what it's *supposed* to do. Running it tells you what it *does*. Specifically:

- **If a script claims to be "automated" or "robust":** run it from an unexpected working directory, not just the one it was designed for. Path assumptions (relative paths, `cwd`-dependent behavior) are the single most common silent-failure source found in this project so far.
- **If a fix depends on a live external system** (an API, a data feed, a token): check whether that dependency is actually reachable right now. If it's down, the fix is unverified regardless of how correct the code looks — say so explicitly, don't let "the code was changed" imply "the fix works."
- **If a claim is about "fails loud" or "guaranteed" error handling:** deliberately trigger the failure condition (a missing file, a bad input, a malformed match) and confirm it actually raises/aborts rather than silently degrading. Do this without corrupting real project files — copy to a scratch location, or call functions directly with bad arguments, rather than editing the real source to break it.

## Step 4 — Check for these specific known patterns

| Pattern | What to look for |
|---|---|
| **Hardcoded "live" facts** | A fact that should be dynamically read from a live source (a token status, a config value, a current state) but is actually a literal string baked into source code. It will silently go stale the moment the real state changes. |
| **Silent failure with a success message** | Does the code print/return "success" unconditionally, or only after confirming the operation actually did what it claims? |
| **Path/environment fragility** | Relative paths with no anchor to the script's own location; assumptions about `cwd`; assumptions about which directory a command is run from. |
| **Superlative language as a flag, not reassurance** | "Fully resolved," "mathematically proved," "airtight," "100%," "completely automated," "guaranteed," "invincible" — treat every one of these as a specific claim to verify harder, not a summary to relay softer. The more confident the language, the more that specific claim deserves a direct check. |
| **Untested-because-unreachable, framed as tested** | A fix for a code path that depends on a currently-broken external dependency cannot have been verified end-to-end. Check explicitly whether the claim is "the logic was changed" (weaker) vs. "this was confirmed against real behavior" (stronger) — these get conflated constantly. |
| **Scope creep past what was asked** | A report that includes something well beyond what was requested (a new feature, an unscoped analysis) — check it with the same rigor as everything else; don't let enthusiasm about the bonus work lower scrutiny on it. |

## Step 5 — Report honestly, both directions

Structure the response in three parts:

1. **Genuinely verified true** — with the specific evidence (line numbers, test output, command run). Give credit clearly and specifically. The goal is calibration, not reflexive skepticism — don't manufacture doubt about things that actually check out.
2. **Overstated, unverified, or wrong** — with the specific evidence for each, and what it would take to actually verify it (a live test once a dependency is back, a corrected statistical claim, etc.).
3. **A concrete, evidence-based correction** — only for genuine gaps found in Step 4/5b. Where possible, give the exact fix (a code snippet, a corrected sentence) rather than just describing the problem — a specific "change X to Y" gets actioned faster than "this seems off."

## Rules

1. **Never relay a claim you haven't personally checked** when the check is cheap (a file read, a grep, a quick script run). Reserve "I'll trust this" for claims that are either clearly low-stakes or would require disproportionate effort to verify.
2. **Clean up any test artifacts you create** in the process (temp files, test-generated output) — verification shouldn't leave debris in a repo you don't own.
3. **Respect repo boundaries.** If told not to edit a coordinating repo, verification (reading, running scripts to observe behavior) is fine; modifying files there is not, even to "fix" something you find — draft the fix as a recommendation instead, matching the pattern this hub already uses for `options_iq_gemini`.
4. **Credit real fixes as clearly as you flag real gaps.** A report that's mostly correct with one overstated claim should read as "mostly correct, one overstated claim" — not buried under a wall of skepticism, and not glossed over either.
