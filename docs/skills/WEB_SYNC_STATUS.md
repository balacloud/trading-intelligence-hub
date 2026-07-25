# WEB_SYNC_STATUS.md — Claude Web Skill Sync Audit

> Tracks drift between local `skill-*.md` files and what is actually uploaded to claude.ai (Customize → Skills).
> **Cadence: biweekly.** Last audit: **June 30, 2026 (Audit #2 — all ✅)** · Next audit due: **July 14, 2026**
> Owner: Bala (re-uploads are manual — Claude cannot push to claude.ai).

---

## How to run this audit

1. In claude.ai → Customize → Skills, **Export** every uploaded skill (downloads a `.skill` zip each).
2. Drop them all into `Validate_ClaudeWeb_Skill/` in this repo (Downloads is sandbox-blocked — must live inside the project).
3. Tell Claude: *"run the web skill sync audit"*. Claude unzips each `.skill` (they contain `<name>/SKILL.md`), diffs the body against the matching local file, and updates the status table below.
4. Re-upload any skill flagged 🔴/🟠/⚫. Re-export afterward to confirm it lands ✅.

**Diff method:** strip frontmatter (`name:`/`description:`/`---`) from both sides, then `diff`. The `.skill` export wraps the file in an extra frontmatter block — that wrapper is benign and ignored.

---

## Skill ownership map

| Web skill (`name:`) | Owner | Local source of truth |
|---------------------|-------|-----------------------|
| `options-ibkr-radar` | Hub | `skill-options-ibkr-radar.md` |
| `options-trade-validator` | Hub | `skill-options-trade-validator.md` |
| `options-directional-builder` | Hub | `skill-options-directional-builder.md` |
| `options-scanner` | Hub | `skill-options-scanner.md` |
| `ibkr-scan` | ETF engine | `../options-iq/skills/ibkr-scan.md` (filename = manifest; not renamed) |
| `skill-creator` | Anthropic default | n/a — Claude's built-in skill-authoring skill. **Ignore in audits**, do not delete. |
| `catalyst-check` | ETF engine | `../options-iq/skills/catalyst-check.md` |
| `chartreview` | ETF engine | `../options-iq/skills/chartreview.md` |

> ⚠️ Name collision: the ETF engine's `ibkr-scan` is distinct from the hub's in-design STA `skill-sta-ibkr-scan.md` (which is not yet a file and not uploaded). Don't conflate them.

### Naming standardization — June 30, 2026
All hub skills now use the engine-prefixed scheme: **filename stem == manifest `name:`**, family prefix `options-*` (Gemini) / future `sta-*` (STA). Local files renamed `skill-ibkr-radar.md`→`skill-options-ibkr-radar.md`, `skill-directional-builder.md`→`skill-options-directional-builder.md`, `skill-trade-validator.md`→`skill-options-trade-validator.md` (scanner already conformed). Manifests: only `directional-trade-builder` → `options-directional-builder` changed (the other three manifests were already `options-*`).

> **Claude Web identity = manifest `name:`, NOT filename.** Renaming a local file alone does not require a re-upload — web never sees the filename. Only the *directional* skill's **manifest** changed, so it gets a new web entry and the old `directional-trade-builder` entry must be **deleted** to avoid a duplicate. The other three keep their existing web identity.

---

## Current status — Audit June 30, 2026 (Audit #2)

| Skill | Local ver | Web ver | Body diff | Status | Action |
|-------|:---------:|:-------:|:---------:|:------:|--------|
| `options-trade-validator` | v3 | v3 | 0 lines | ✅ Aligned | none |
| `options-ibkr-radar` | v2 | v2 | 0 lines | ✅ Aligned | none (re-uploaded Audit #2 — Sieve 1.5 now live) |
| `options-directional-builder` | **v1.4** | v1.1 | drift | 🟠 Stale | **Re-upload** — local bumped to v1.4 in Session 16 (chart-screenshot input + dashboard-table read model + options-liquidity pre-screen). Manifest unchanged → replace, no delete. |
| `options-scanner` | v2 | v2 | 0 lines | ✅ Aligned | none (first upload — PATH B now live on web) |
| `ibkr-scan` (ETF) | — | — | 0 lines* | ✅ Aligned | none |
| `catalyst-check` (ETF) | — | — | 0 lines* | ✅ Aligned | none |
| `chartreview` (ETF) | — | — | 0 lines* | ✅ Aligned | none |

*ETF skills each have 1 leading blank line in the web export — artifact of the export wrapper, not real drift.

Legend: ✅ aligned · 🟠 minor drift · 🔴 major drift · ⚫ missing from web

---

## Open drift detail

### ✅ All clean as of Audit #2 (June 30, 2026)

No open drift items. All 4 hub skills confirmed 0-line diff against fresh web exports.

**Resolved in Audit #2:**
- `options-ibkr-radar` — re-uploaded. Sieve 1.5 (Gates A/B/C) is now live on web. Micro-cap purge active.
- `options-directional-builder` — uploaded as new entry. Old `directional-trade-builder` deleted. TTL now correct (30 min / 1800s) on web.
- `options-scanner` — first upload. PATH B (autonomous scan) is now live on web.

---

## Claude Web inventory snapshot — June 30, 2026 Audit #2 (from screenshot)

Personal skills actually present in claude.ai at audit time (7):
`options-scanner` (hub ✅), `options-ibkr-radar` (hub ✅), `options-directional-builder` (hub ✅), `chartreview` (ETF ✅), `catalyst-check` (ETF ✅), `ibkr-scan` (ETF ✅), `options-trade-validator` (hub ✅).

`directional-trade-builder` (OLD) — **confirmed deleted**. `skill-creator` — Anthropic default, not visible in screenshot, ignore.

**All pending actions from Audit #1 completed by Bala. No pending actions.**

---

## Audit log

| Date | Auditor | Findings | Notes |
|------|---------|----------|-------|
| 2026-06-30 (Audit #1) | Claude (Session 15) | 4 aligned, Radar 🔴, Directional 🟠, Scanner ⚫ missing | First web-vs-local audit. Fixed Directional title v1→v1.1. Standardized hub skill naming (engine-prefixed; filename stem == manifest). Re-uploads + old-entry deletion pending (Bala). |
| 2026-06-30 (Audit #2) | Claude (Session 16) | 7/7 ✅ Aligned | All pending Audit #1 actions completed by Bala. Radar Sieve 1.5 live. Directional TTL fixed (30 min). Scanner PATH B live. Old `directional-trade-builder` deleted. Zero diff across all hub skills. |
| 2026-07-01 (Session 16 post-audit) | Claude | `options-directional-builder` bumped v1.1 → v1.3 locally (chart-screenshot + dashboard-table read model) | Re-upload pending. All other 6 skills remain ✅. Not a full audit — logged so next audit catches the drift. |

---

*Update the status table + audit log every audit. Move a skill to ✅ only after a fresh export confirms zero body diff.*
