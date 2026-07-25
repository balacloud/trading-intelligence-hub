#!/usr/bin/env python3
"""
Generates GEMINI_STATE_HANDOFF.md -- the hub's synthesized state for an
Options IQ Gemini session to read at session start. Mirrors the design of
options_iq_gemini/scripts/generate_handoff.py (path-anchored, fail-loud,
nothing hardcoded that actually changes over time).
"""
import os
import re
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)

SKILL_FILES = [
    "docs/skills/skill-options-ibkr-radar.md",
    "docs/skills/skill-options-scanner.md",
    "docs/skills/skill-options-directional-builder.md",
    "docs/skills/skill-options-trade-validator.md",
]


def read_lines(relpath):
    full_path = os.path.join(REPO_ROOT, relpath)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"generate_gemini_handoff.py: source file missing: {full_path}")
    with open(full_path, "r") as f:
        return f.readlines()


def get_skill_versions():
    """Each skill file's H1 title line (first line starting with '# ') carries its version."""
    versions = []
    for skill_file in SKILL_FILES:
        lines = read_lines(skill_file)
        title = next((l.strip() for l in lines if l.startswith("# ")), None)
        if title is None:
            raise ValueError(
                f"generate_gemini_handoff.py: no H1 title line found in {skill_file} -- "
                f"can't confirm its version. Check the file wasn't corrupted."
            )
        versions.append(f"- `{skill_file}`: {title.lstrip('# ').strip()}")
    return "\n".join(versions)


def get_latest_session():
    """Find the highest '### ... -- Session N' header in CLAUDE_CONTEXT.md, return that section."""
    lines = read_lines("CLAUDE_CONTEXT.md")
    session_pattern = re.compile(r"^### .*—\s*Session\s+(\d+)\s*$")
    sessions = []
    for i, line in enumerate(lines):
        m = session_pattern.match(line.strip())
        if m:
            sessions.append((int(m.group(1)), i))
    if not sessions:
        raise ValueError(
            "generate_gemini_handoff.py: no '### ... — Session N' headers found in "
            "CLAUDE_CONTEXT.md -- the Session History format may have changed."
        )
    sessions.sort(key=lambda t: t[0])
    _, latest_idx = sessions[-1]
    content = [lines[latest_idx]]
    for line in lines[latest_idx + 1:]:
        if line.startswith("### "):
            break
        content.append(line)
    return "".join(content).strip()


def get_cross_repo_known_issues():
    """
    Known Issues table rows tagged 'cross-repo'. Zero matches is a VALID state (no
    current cross-repo issues) -- only raise if the table header itself is missing,
    since that means the table structure changed, not that there's nothing to report.
    """
    lines = read_lines("CLAUDE_CONTEXT.md")
    header_idx = next((i for i, l in enumerate(lines) if l.strip().startswith("| Priority")), None)
    if header_idx is None:
        raise ValueError(
            "generate_gemini_handoff.py: Known Issues table header ('| Priority | Item | Notes |') "
            "not found in CLAUDE_CONTEXT.md -- table structure may have changed."
        )
    rows = []
    i = header_idx
    while i < len(lines) and lines[i].strip().startswith("|"):
        row = lines[i]
        priority_field = row.split("|")[1].strip().upper() if row.count("|") >= 2 else ""
        if "cross-repo" in row.lower() and not priority_field.startswith("RESOLVED"):
            rows.append(row.rstrip())
        i += 1
    if not rows:
        return "No open cross-repo Known Issues rows as of this generation. (Valid state, not an extraction failure.)"
    return "\n".join(rows)


def generate():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        skill_versions = get_skill_versions()
        latest_session = get_latest_session()
        cross_repo_issues = get_cross_repo_known_issues()
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ ABORTED — GEMINI_STATE_HANDOFF.md NOT overwritten: {e}")
        sys.exit(1)

    content = f"""# TRADING-INTELLIGENCE-HUB → OPTIONS IQ GEMINI STATE HANDOFF
> **Auto-generated:** {timestamp}
> **Purpose:** What changed on the hub side that's relevant to Options IQ Gemini. Read this
> at session start alongside your own STATE_HANDOFF.md -- that file covers your own repo's
> state; this one covers the upstream skill/contract side you don't otherwise see.
> **Canonical references (not duplicated here -- go to the source, don't trust a stale copy):**
> `Docs/CENTAUR_SCHEMA_v2.json` (your own copy is authoritative) and the hub's own
> `docs/specs/OPTIONS_SIEVE_SPEC.md` if you need to understand *why* a payload looks the way it does.

---

## 1. Current skill versions (the things that produce your CENTAUR JSON)
{skill_versions}

---

## 2. Latest hub session (may or may not be Gemini-relevant -- read for context, not everything here concerns you)
{latest_session}

---

## 3. Open cross-repo Known Issues (from the hub's Known Issues table, filtered to rows tagged "cross-repo")
{cross_repo_issues}
"""
    out_path = os.path.join(REPO_ROOT, "GEMINI_STATE_HANDOFF.md")
    with open(out_path, "w") as f:
        f.write(content)

    print(f"✅ GEMINI_STATE_HANDOFF.md generated at {timestamp}.")


if __name__ == "__main__":
    generate()
