# HANDOFF — stale hub skill-file references in three of your own docs

**Written:** July 25, 2026 (Session 34, trading-intelligence-hub, in progress)
**For:** Options IQ Gemini's own dev session (`options_iq_gemini`, separate repo — nothing has been edited there from this handoff)
**Severity:** LOW — cosmetic/navigational only, doesn't affect anything at runtime. Purely a "next person who tries to follow this path gets a 404" problem.

---

## What was found

Session 34 reorganized this hub's root-level docs into `docs/{handoffs,skills,specs,planning}/` (skill files specifically moved to `docs/skills/`). While sweeping for anything referencing the old paths, three of your own files turned up:

1. **`PROTOCOL.md`** (lines 44-45):
   > `skill-ibkr-radar`: Located in external repository `/Users/balajik/projects/trading-intelligence-hub/skill-ibkr-radar.md`...
   > `skill-directional-builder`: Located in `/Users/balajik/projects/trading-intelligence-hub/skill-directional-builder.md`.

2. **`.agents/AGENTS.md`** (line 50):
   > ...you must first read and verify the actual skill source file inside the `trading-intelligence-hub` project (e.g., `/Users/balajik/projects/trading-intelligence-hub/skill-directional-builder.md`)...

3. **`Docs/CLAUDE_MCP_SKILL_HANDOFF.md`** (lines 15-16): a table mapping `skill-ibkr-radar` / `skill-directional-builder` to the same old absolute paths.

## Two separate problems, not one

**(a) The path moved.** All of this hub's skill files now live under `docs/skills/`, not at repo root. Every path above needs a `docs/skills/` segment inserted.

**(b) The filenames were already wrong, independent of the move.** All three docs say `skill-ibkr-radar.md` and `skill-directional-builder.md` — but the actual files (both before and after this session's move) are named `skill-options-ibkr-radar.md` and `skill-options-directional-builder.md`, per this hub's naming convention standardized June 30, 2026 (`skill-[engine]-[purpose].md`, filename stem equals the manifest `name:`). These three references predate that standardization and were never updated — this hub's own reorg just surfaced it, didn't cause it.

**Corrected paths, for reference:**
- `docs/skills/skill-options-ibkr-radar.md` (not `skill-ibkr-radar.md`)
- `docs/skills/skill-options-directional-builder.md` (not `skill-directional-builder.md`)

## Not proposing

No code change, no behavior change — this doesn't touch anything `/analyze/centaur` or any runtime path reads. It's exclusively about three doc files' own prose being accurate enough that a future dev session (yours or a fresh one) can actually follow the pointer instead of hitting a stale path.

## Why this hub isn't fixing it directly

Per this hub's own cross-repo convention: read-only across all three engine repos, no edits inside `options_iq_gemini/` ever from this side — and `PROTOCOL.md` specifically is documented as Gemini's own SOD, read-only for Claude even for a one-line path fix. This handoff exists so the correction happens on your side, in your own commit.

## Verification once fixed

Same standard this hub holds its own claims to — re-read the three files live and confirm the corrected paths resolve to real files, not just that the text was edited.
