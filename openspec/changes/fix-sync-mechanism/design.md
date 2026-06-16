## Context

This change builds the scaffold→downstream sync mechanism. It **supersedes** the frozen
`openspec/changes/scaffold-sync` plan, which a principal review found unsafe to apply as written
(`scaffold-sync/principal-review.md`): the guard used a non-blocking exit code, and the AGENTS.md
"DO NOT EDIT" header was re-inserted on every sync (non-idempotent — the second sync corrupts the file).
No mechanism files exist on disk yet — `scripts/` currently holds only `_convergence.py`, `fetch_clean.py`,
`test_convergence.py`, `test-gate.sh`. W1 builds the mechanism for the first time with the review's fixes
folded in; it does **not** patch existing code.

**AGENTS.md span structure** (per-repo title + shared spans + per-repo sections), confirmed by inspection
of the scaffold and downstream files:

```
# <repo-name>                          ← title (per-repo, line 1; preserved verbatim)
> **MANDATORY — read before …**        ← shared span 1 begins
## Cross-agent compatibility           ← shared span 1 continues
## Project context                     ← per-repo (preserved verbatim; sits between the spans)
## Roles                               ← shared span 2 begins
## After reading this file             ← shared span 2 ends
---  /  # Project reference            ← psc-monitor only; tail, preserved verbatim
```

**Constraints:** scaffold-only; no downstream propagation (W6); the blocking convention is exit `2` for a
Claude Code `PreToolUse` hook (verified in W0 via the commit-test-gate live smoke; `scripts/test-gate.sh`
uses the same code).

### External-API surface

**None.** All four files use only the Python standard library (`re`, `subprocess`, `sys`, `pathlib`,
`filecmp`) and the `git` CLI already required by the repo. There is no new library, constructor kwarg, or
client option, so the propose-phase **Live Probe is not applicable** (zero external-API surface).

## Goals / Non-Goals

**Goals:**
- Build `sync_scaffold.py`, `scaffold_manifest.txt`, `scaffold_check.py`, `test_sync_scaffold.py` in scaffold.
- Copy manifest-listed files **byte-identical** scaffold→target; handle `AGENTS.md` via span-replace that
  preserves each repo's `## Project context` and tail.
- Provide a `--check` drift report (diagnostic, exit `1` on drift) and a commit-time guard (blocking, exit `2`).
- Make repeated sync **idempotent** and cover the algorithm with unit tests.

**Non-Goals:**
- Propagation to extrends/psc-monitor, `.claude/settings.json` hook wiring, and per-repo `scripts/test-cmd`
  creation — all **W6**.
- Any "DO NOT EDIT" header injection (cut — see D4).
- Touching app code or per-repo/volatile state files.
- Automating sync (operator-triggered only).

## Decisions

### D1 — Python sync script, scaffold-only

`scripts/sync_scaffold.py <target-repo-path> [--check]`. Python (not shell) because the AGENTS.md
span-replace needs multi-line regex; matches the repo convention (`_convergence.py`, `fetch_clean.py`). The
script is a scaffold-only tool — it is **not** itself listed in the manifest and is never copied downstream.
Downstream repos receive the manifest and `scaffold_check.py` (the guard needs them), not the sync script.

### D2 — Manifest: plaintext, `#` comments, self-listed

`scripts/scaffold_manifest.txt` — one repo-relative path per line; `#` lines and blank lines are skipped.
The manifest lists **itself** and `scaffold_check.py` (downstream hooks depend on both). It excludes
per-repo/volatile state: `STATUS.md`, `ai-docs/decisions.md`, `ai-docs/open-questions.md`,
`ai-docs/improvement-roadmap.md`, `ai-docs/archive/**`, `.claude/settings.json`, `scripts/test-cmd`, and
`scripts/sync_scaffold.py` (scaffold-only). The leading comment is **ordinary file content** copied verbatim
(it is not the cut header subsystem — the script injects nothing). Initial contents:

```
# scaffold-managed inventory — edit files in openspec-scaffold, then run scripts/sync_scaffold.py.
# One repo-relative path per line; '#' and blank lines are ignored.

# Agent definitions (.claude)
.claude/agents/apply-executor.md
.claude/agents/archive-executor.md

# Skills (.claude)
.claude/skills/openspec-apply-change/SKILL.md
.claude/skills/openspec-archive-change/SKILL.md
.claude/skills/openspec-explore/SKILL.md
.claude/skills/openspec-onboard/SKILL.md
.claude/skills/openspec-propose/SKILL.md
.claude/skills/openspec-sync-specs/SKILL.md
.claude/skills/openspec-verify-change/SKILL.md

# Agent definitions (.opencode)
.opencode/agents/apply-executor.md
.opencode/agents/archive-executor.md
.opencode/agents/openspec-reviewer.md
.opencode/agents/openspec-verifier.md

# AI docs
ai-docs/fast-track-workflow.md
ai-docs/research-fetch-convention.md

# Scripts
scripts/_convergence.py
scripts/fetch_clean.py
scripts/scaffold_check.py
scripts/scaffold_manifest.txt
scripts/test-gate.sh
scripts/test_convergence.py

# AGENTS.md — span-replace, not wholesale copy (see D3)
AGENTS.md
```

**The manifest lists only files that exist in the scaffold golden source at apply time.** Verified against
disk: every path above exists in scaffold. `ai-docs/opencode-delegation-notes.md` (present in the downstream
repos, **absent** in scaffold) is intentionally **not** listed in W1 — a manifest entry with no scaffold
source would trip the D7 missing-source abort. That doc is promoted into scaffold (and added to the manifest)
in a later change (dedup / propagation); downstream repos already have it, so deferring it propagates nothing
incorrectly. The apply executor re-confirms each listed path exists in scaffold before writing the manifest.

### D3 — AGENTS.md: span-replace, header-free

The script replaces only the two shared spans, preserving the title, `## Project context`, and tail. This is
the prior D3 algorithm **with the `HEADER` insertion removed** — which is exactly what eliminates the B2
non-idempotency (the title region is preserved as-is, so re-syncing cannot accrete header lines).

```python
import re

def sync_agents_md(scaffold_text: str, target_text: str) -> str:
    # Scaffold anchors
    s_mandatory = re.search(r'^> \*\*MANDATORY', scaffold_text, re.M)
    s_roles     = re.search(r'^## Roles\b',      scaffold_text, re.M)
    s_after     = re.search(r'^## After reading this file', scaffold_text, re.M)
    if not all([s_mandatory, s_roles, s_after]):
        raise ValueError("scaffold AGENTS.md missing required section anchor")

    # Invariant: scaffold must not carry a tail after '## After reading this file'
    if re.search(r'\n(---\s*\n|^# )', scaffold_text[s_after.start():], re.M):
        raise ValueError("scaffold AGENTS.md has unexpected tail — update sync_scaffold.py")

    s_proj_ctx = re.search(r'^## Project context', scaffold_text, re.M)
    span1_end  = (s_proj_ctx or s_roles).start()
    span1 = scaffold_text[s_mandatory.start():span1_end]
    span2 = re.sub(r'\s+$', '\n', scaffold_text[s_roles.start():])

    # Target anchors
    t_mandatory = re.search(r'^> \*\*MANDATORY', target_text, re.M)
    t_proj_ctx  = re.search(r'^## Project context', target_text, re.M)
    t_roles     = re.search(r'^## Roles\b',         target_text, re.M)
    t_after     = re.search(r'^## After reading this file', target_text, re.M)
    if not all([t_mandatory, t_roles, t_after]):
        raise ValueError("target AGENTS.md missing required section anchor")

    t_title  = target_text[:t_mandatory.start()]          # preserved verbatim — NO header prepend
    proj_ctx = target_text[t_proj_ctx.start():t_roles.start()] if t_proj_ctx else ''

    after_start = t_after.start()
    tail_match  = re.search(r'\n(---\s*\n|# \w)', target_text[after_start:], re.M)
    if tail_match:
        tail = target_text[after_start + tail_match.start():]
    else:
        if len(target_text.splitlines()) > 300:
            raise ValueError("target AGENTS.md is long but no tail-separator found — check anchors")
        tail = ''

    return t_title + span1 + proj_ctx + span2 + tail
```

**Idempotency:** because `t_title` is copied through untouched and nothing is injected, `sync_agents_md`
applied to its own output returns the same string. This is asserted by a unit test (sync twice → `--check` 0).

### D4 — "DO NOT EDIT" header subsystem: CUT

The prior plan injected a format-specific header into every synced file and stripped it back out before
diffing in `--check`. That subsystem is removed entirely:
- The sync script injects **nothing**; synced files are byte-identical to scaffold (AGENTS.md spans included).
- `--check` for regular files is a **plain byte compare** (`filecmp`/string equality) — no strip-before-diff
  inverse to keep correct.
- The single human-facing "scaffold-managed — edit upstream" note lives once in `AGENTS.md` (`## After reading
  this file` already directs editors to scaffold) and as the ordinary leading comment in the manifest.

**Alternative considered:** one uniform header + a single-regex filter in `--check`. Rejected — even one
header reintroduces an insert/strip round-trip to keep idempotent and exact, for an advisory string whose
real enforcement is the hook. The editors are overwhelmingly agents, gated by the guard.

### D5 — Commit guard `scaffold_check.py`: manifest ∩ staged, exit `2`

```python
#!/usr/bin/env python3
import subprocess, sys
from pathlib import Path

def main() -> int:
    # Resolve the manifest relative to THIS file, not cwd — the prior plan read it relative to
    # cwd, which breaks when the hook fires from a subdirectory. git diff --cached --name-only
    # returns repo-root-relative paths regardless of cwd, so the intersection stays correct as
    # long as the manifest entries are repo-relative.
    manifest = Path(__file__).resolve().parent / "scaffold_manifest.txt"
    with open(manifest) as f:
        managed = {l.strip() for l in f if l.strip() and not l.startswith('#')}
    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"]).decode().split()
    hits = sorted(managed & set(staged))
    if hits:
        print("BLOCKED: scaffold-managed files staged for direct commit:")
        print("\n".join(f"  {f}" for f in hits))
        print("Edit these in openspec-scaffold, then run scripts/sync_scaffold.py for each repo.")
        print("Deliberate scaffold-managed change (e.g. applying a new sync, or reverse-promoting an")
        print("improvement back to scaffold): git commit --no-verify.")
        return 2
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

Exit `2` is the only Claude Code `PreToolUse` code that **blocks** the tool; any other non-zero is
non-blocking (this is the B1 fix — the prior plan's `exit(1)` was a silent no-op). Exit `0` when nothing
scaffold-managed is staged. The guard resolves the manifest relative to its own file (D5 code), so it needs
no scaffold path and makes no cwd assumption.

**Coverage limit (M1) — documented, not engineered around.** As a Claude Code `PreToolUse` hook, the guard
only intercepts commits Claude makes through its Bash tool. Operator-terminal commits and opencode/deepseek
executor commits bypass it; `git commit --no-verify` is the sanctioned escape for deliberate scaffold-managed
edits. A repo-wide `core.hooksPath` / `.git/hooks/pre-commit` was considered and **rejected for W1**: it adds
a per-repo install step and machinery for a guard whose purpose is catching Claude's accidental edits, which
this already does. The limitation is stated in `scaffold_check.py`'s module docstring and in the spec.

### D6 — `--check` mode: byte compare (regular) / span compare (AGENTS.md), exit `1` on drift

`sync_scaffold.py --check <target>` reports `IDENTICAL` / `DIFFERS` / `MISSING` per manifest file and exits
`1` if any file is not `IDENTICAL`, else `0`. It is a diagnostic CLI, **not** a blocking hook, so it uses
exit `1` (distinct from the guard's `2`).
- Regular files: compare the target file's bytes against scaffold's source bytes (no header to strip — D4).
- `AGENTS.md`: compare the **current** target against `sync_agents_md(scaffold_text, target_text)` (what it
  would be post-sync). This compares only the shared-span *content* — a differing `## Project context` or tail
  is reproduced verbatim into the expected output from the target itself, so its content does not count as
  drift. Caveat: the byte compare runs on the full reconstructed string, so a formatting mismatch at the
  span2/tail *join boundary* (e.g. the target's tail began with a tight `\n---` but the join yields `\n\n---`)
  can cause a **one-time** AGENTS.md `DIFFERS` on the first `--check`; running `sync_scaffold.py` once
  normalizes it, after which `--check` is idempotently clean. This is cosmetic, not a correctness bug.

### D7 — Abort guards (no partial writes)

`sync_scaffold.py` aborts non-zero with a clear message and makes **no** changes when: the target path does
not exist or has no `.git`; a manifest-listed source file is missing in scaffold; `AGENTS.md` is missing a
`## Roles` or `## After reading this file` anchor (`ValueError` from D3); scaffold's `AGENTS.md` carries an
unexpected tail (D3 invariant); or a >300-line target `AGENTS.md` yields no tail match (the M2 mis-slice
guard). Writes happen only after all manifest files are validated.

### Carried forward to W6 (not built here)

D7 settings.json two-entry `PreToolUse` insertion, D8 per-repo `scripts/test-cmd`, and D10 pre-execution
drift-check-then-STOP are **W6** execution responsibilities. W1's mechanism supports them; W1 does not run
them.

## Risks / Trade-offs

- **[R1] AGENTS.md span mis-slice could drop a per-repo section** → D3 preserves title / project-context /
  tail independently; the >300-line no-tail guard (D7) aborts rather than truncating; a unit test exercises a
  psc-monitor-like long tail (`# Project reference` after `## After reading this file`) and asserts it is
  preserved byte-for-byte (covers minor M2). Known low-risk trade-off: the span boundaries are line-anchored
  regex (`^## Roles`, `^## After reading this file`), so a downstream `## Project context` that itself
  contained a line `## Roles` would mis-slice; project context is short and hand-curated, so this is accepted
  and noted rather than guarded.
- **[R2] Guard bypassed by non-Claude commits (M1)** → accepted and documented (D5); `--no-verify` is the
  sanctioned escape. The W6 manual diff is the backstop against silent drift.
- **[R3] Manifest goes stale (a new shared file is not listed)** → manifest is self-managed and updated when a
  shared file is added; W6's drift check is the catch. Out of W1's automated scope.
- **[R4] `--check` AGENTS.md comparison could mask real span drift if anchors move** → the same anchor set
  drives sync and check, so a missing anchor aborts both rather than silently passing; covered by the
  missing-anchor abort test.

## Migration Plan

New files only; nothing to migrate or roll back in scaffold. The frozen `openspec/changes/scaffold-sync` plan
stays on disk as source material and is deleted once W1 + W6 land. Rollback = delete the four new files.

## Verification

Change-specific acceptance criteria (the generic verify procedure lives in the verify skill; results land in
`notes.md`). W1 is complete when:

1. `python scripts/test_sync_scaffold.py` (or the repo's pytest) passes, covering: **idempotency** (sync a
   fixture target twice → `--check` exits 0), **tail preserved verbatim** (psc-monitor-like long tail),
   **`## Project context` preserved verbatim**, **no-`## Project context` case** (extrends-like), and the four
   D7 aborts (bad target, missing source, missing AGENTS.md anchor, scaffold-tail invariant; plus the >300-line
   no-tail guard).
2. `sync_scaffold.py --check` exits **1** when any manifest file differs/Missing, **0** when all are IDENTICAL.
3. `scaffold_check.py` returns **2** (blocks) when a manifest-listed file is in `git diff --cached --name-only`,
   and **0** when none is staged. (Verified at the unit/behavioral level here; the live `git commit` hook smoke
   in downstream repos is W6, riding the W0-verified mechanism.)
4. The sync script injects **no** "DO NOT EDIT" header text into any output file (grep the synced fixture
   output for the header string → absent).
5. A self-check is sane: after syncing a constructed fixture target, `--check <fixture>` exits 0; after a
   one-byte edit to a synced file in the fixture, `--check` exits 1 and names that file.

## Open Questions

None. The header-cut, exit-code, and guard-scope decisions are settled (proposal + explore-brief); manifest
membership is confirmed against scaffold at apply time.
