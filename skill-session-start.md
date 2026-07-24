---
name: session-start
description: "Open a Trading Intelligence Hub session: read CLAUDE_CONTEXT.md, PERSONA.md, and TRADER_LENS.md, check whether the mandatory cross-repo verification applies, anchor the wall-clock date and market status, and give the user a short orientation instead of making them ask 'where are we.' Trigger at the start of a session — the user's first message, or an explicit ask like 'let's start' / 'catch me up' / 'where are we.' Read-only: no edits, no commits."
---

# Session Start

You are orienting yourself and the user at the start of a session, not performing work yet. This mirrors `CLAUDE_CONTEXT.md`'s own instruction ("Read CLAUDE_CONTEXT.md and PERSONA.md — continuing Trading Intelligence Hub session") plus the steps that instruction implies but doesn't spell out.

---

## Step 1 — Read the three source-of-truth files

Read `CLAUDE_CONTEXT.md` in full (or at minimum: header, Known Issues, the most recent Session History entry, and Immediate Next Steps), `PERSONA.md`, and `TRADER_LENS.md`. Don't answer from memory of a prior conversation — this project's own live-read rule exists because summaries go stale (a session once caught a 5min→30min TTL error this way). If any of the three was touched very recently in this same conversation, a fresh re-read is still cheap insurance, not wasted effort.

`PERSONA.md`'s Alex and `TRADER_LENS.md`'s veteran trader are two different lenses, not duplicates — Alex judges code and design, `TRADER_LENS.md` judges whether a result or a proposed threshold change is actually justified by the data. Both apply through the whole session, not just at open.

## Step 2 — Check whether cross-repo verification is mandatory

Scan the Known Issues table for any row tagged `cross-repo` that isn't `RESOLVED`. If one exists, this is **mandatory, not optional**: invoke `skill-cross-repo-fix-verification.md` against Gemini's own `STATE_HANDOFF.md` / `KNOWN_ISSUES.md` before trusting the hub's row status. Gemini can fix a hub-reported finding independently with no report-back mechanism — Session 23 caught a 4-day-stale row this exact way. Don't skip this because the table "looks current."

## Step 3 — Anchor the wall-clock date and market status

```bash
python3 -c "from datetime import datetime, timezone; import zoneinfo; now=datetime.now(timezone.utc).astimezone(zoneinfo.ZoneInfo('America/New_York')); print(now, now.strftime('%A'))"
```

Note the day of week and whether US markets are plausibly open (weekday, roughly 9:30–16:00 ET) — this has mattered repeatedly (Saturday closes blocking live runs, pre-market snapshots returning empty option quotes). Don't assume; check.

## Step 4 — Give a short orientation, not a re-read of the whole file

Summarize for the user in a few sentences: what the last session closed with, what's at the top of Immediate Next Steps in priority order, and any open blocker that would gate today's likely work. This is what lets the user say "yes, keep going" instead of having to ask "where are we" themselves — that question showed up as its own Session (22) once; the point of this step is to make asking it unnecessary.

## Step 5 — Stop. Don't start executing next-step items yet.

Session start is orientation only. If the user's next message is a specific task, do that task. If they say "keep going" or equivalent, proceed to the top Next Steps item — but that's a new instruction to act on, not something this skill decides on its own.

---

## Rules

1. **Read-only.** This skill never edits a file, runs a script with side effects, or commits. If Step 2's cross-repo check is needed, that's a read/verify pass (per its own skill's rules), not a fix applied unilaterally.
2. **Don't skip Step 2 because it's inconvenient.** The whole reason it's mandatory is that skipping it is exactly how staleness has slipped through before.
3. **Keep the orientation short.** The user has the file; don't paste it back at them. A few sentences of "here's where we are" beats a restated wall of context.
4. **If nothing is stale and nothing is blocked,** say so plainly — a clean orientation ("last session closed clean, nothing blocking, top of the queue is X") is a complete and correct Step 4, not an under-delivery.
