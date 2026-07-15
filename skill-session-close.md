---
name: session-close
description: "Close out a Trading Intelligence Hub session: update Known Issues, append a Session History entry, refresh Immediate Next Steps, sync SKILL_MAP.md if any skill changed, regenerate GEMINI_STATE_HANDOFF.md when required, rewrite the header summary, and commit. Trigger when the user says something like 'close the session', 'let's wrap up', 'document everything', or 'end of session' — never run automatically just because a task finished; this is an explicit, user-invoked ritual, not something to infer from context."
---

# Session Close

You are closing out a working session on `CLAUDE_CONTEXT.md`'s own terms — the file states at its own bottom: *"Update this file at the end of every session before closing VS Code."* This skill exists because that ritual grew into a real multi-step checklist over 26 sessions, executed from memory each time. Encode the checklist; stop reconstructing it by pattern-matching prior closes.

**Never fabricate what happened this session.** Reconstruct it from what's actually true — the conversation, `git diff`, and `git status` — not from what a typical session close looks like.

---

## Step 1 — Establish what actually changed this session

Before writing anything, gather facts:

```bash
git status
git diff --stat
```

Cross-check against the conversation: which skills were touched (and did their version number actually change)? Which Known Issues rows got resolved, newly found, or need a status correction? Was anything cross-repo (touches `options_iq_gemini` or `options-iq`)? Did the forward test (or any research artifact) get new data?

If nothing changed (a pure Q&A session, no file edits), say so plainly and skip to Step 6 — do not manufacture a Session History entry for a session that didn't touch anything.

## Step 2 — Update Known Issues / Active Debt

For every finding resolved this session: flip its priority to `RESOLVED` (or `RESOLVED (cross-repo)` / `RESOLVED (superseded)` as appropriate) and rewrite its note to state what was verified and how — not just "fixed." For every new finding: add a row with an honest priority (`HIGH (finding, active)`, `MEDIUM`, etc.) and enough detail that a future session doesn't have to re-derive it.

**Rule inherited from the project:** never write "resolved" or "fixed" without having verified it directly (read the live code, ran the test, saw the live data) — same standard `skill-cross-repo-fix-verification.md` holds Gemini's claims to. Hold your own session's claims to the same bar.

## Step 3 — Append a Session History entry

Add a new `### [Month Day, Year] — Session N` block immediately above the current top entry (newest first). Determine `N` by reading the last entry's number and incrementing — never hardcode it.

Format: a bolded one-line theme, then prose paragraphs (this project's established style — dense, specific, evidence-bearing, not a bullet-point status report). Include: what was checked and what it showed (not just what was done), any finding that surprised you, any decision the user made explicitly (attribute it — "per Bala's call" — don't launder a user decision into an unattributed fact), and any blocker hit plus how it was resolved or why it wasn't.

## Step 4 — Refresh Immediate Next Steps

Rename the most recent `### Fresh from Session N` block to the session that just closed, and write its contents fresh — don't just carry forward stale items. For items resolved this session: either delete them or mark `[x] ~~...~~ — done (Session N): ...` per the existing convention. For items still open: restate them with current status, not the status they had when first written.

## Step 5 — Sync skill infrastructure, if touched

- If any skill's version, name, triggers, or role changed: regenerate the relevant section of `SKILL_MAP.md` from the live skill files (not patched by hand — read the actual files, same discipline as the last full regeneration).
- If a skill needs a web re-upload (manifest unchanged, content changed): add it to the "Web skill re-uploads" queue in Next Steps if not already there.

## Step 6 — Regenerate `GEMINI_STATE_HANDOFF.md`, if required

Per `CLAUDE_CONTEXT.md`'s own trailing rule: run this if the session touched a skill's version, the Session History, or a cross-repo-tagged Known Issues row.

```bash
python3 scripts/generate_gemini_handoff.py
```

It fails loud (non-zero exit, no file overwrite) if a source file or expected header is missing — don't ignore that message; fix the underlying cause before proceeding, don't route around it.

## Step 7 — Rewrite the header summary (line 3)

`CLAUDE_CONTEXT.md` line 3 is a running chain: `Last updated: [date] (Session N, closed — [summary]. Prior: Session N-1 ... Prior: Session N-2 ...)`. **Prepend, never delete.** Write the new session's summary, then `Prior: ` followed by the entire existing line 3 content verbatim (which already contains its own chain of priors). Update the date at the front to today's actual date — anchor it with the wall-clock rule (`python3 -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc)...)"`), never approximate.

## Step 8 — Review, stage, and commit

```bash
git status
git diff --stat
```

Confirm the changed-file list matches what you actually intended to touch this session — no stray files swept in. Stage by name (never `git add -A`):

```bash
git add <file1> <file2> ...
```

Commit with a message in this project's established style: a short title (`Close Session N — <one-line theme>`), then 2–4 sentences of body covering the real substance, ending with the standard co-author trailer. Use a heredoc for the message. Never `--amend`, never force-push, never skip hooks.

## Step 9 — Confirm to the user

State plainly: what was closed, the commit hash, and anything genuinely left open or requiring the user's action (a Bala-decision item, a pending web re-upload, a blocked retry for next time). Keep it to a few lines — the file itself now has the detail.

---

## Rules

1. **Only run this when explicitly invoked.** "Close the session," "let's wrap up," "document everything," "end of session" — not "the task is done" or an inferred stopping point. Closing is a user decision, not a model inference.
2. **Verify before writing "resolved."** Same standard as `skill-cross-repo-fix-verification.md`. A note that says "fixed" without evidence is exactly the failure mode this hub has caught repeatedly in *Gemini's* reports — don't reproduce it in your own.
3. **Attribute user decisions explicitly.** If Bala made a judgment call mid-session (keep a drifted gate, choose a fallback data source, cut a watchlist name), the Session History and any downstream doc should say so by name, not present it as an autonomous conclusion.
4. **Never commit files you don't recognize.** If `git status` shows something unexpected, stop and ask before staging it — don't assume it's fine because it's untracked or because the diff looks small.
5. **A no-op session is a valid outcome.** If nothing changed, say so and don't invent a Session History entry to fill the ritual.
