# Notes — checks-facts-split

**Tier:** MEDIUM (tasks.md only; acceptance criteria live here per AGENTS.md).
**Direction:** portfolio change A of `plans/day-to-day-tooling/explore-brief.md`
(direction gate PREMISE: AGREE, 2026-07-03). Operator-confirmed 2026-07-03.

## Acceptance criteria (verified at verify, results appended below)

1. **Vocabulary is enforced by entry points, not prose:** `facts.py` exposes no
   tag/log/baseline surface and cannot run a detector; `checks.py --floor` runs no
   fact-family check. (Live: run both `--list`s and one cross-family `--check` misuse,
   expect usage error.)
2. **Preflight turns serial discovery into one informed report:** in a tmp repo with two
   enabled-but-missing floor binaries, one `--floor` run reports BOTH with
   install-or-disable guidance including the coverage cost, executes nothing, exits 3.
3. **Facts are cache-semantics:** `facts.py` in a tmp git repo exits 0 with radon absent,
   writes undated `output/facts/inventory.json` containing `audit_anchor` (null-tag case
   and tagged case both correct).
4. **Ceremony unchanged:** `audit_scope.py tag`/`log-line` behave as before;
   `log-line` on a repo without `knowledge/audit-log.md` prints the first-run hint on
   stderr with stdout byte-identical.
5. **No stale surface:** repo-wide grep for `audit_bundle`, `audit.toml`, `output/audit`
   finds hits only under `openspec/changes/archive/`, `knowledge/research/`, and
   historical registry lines in `knowledge/decisions/INDEX.md`.
6. **Gates green:** full suite, `scaffold_lint` (manifest completeness + no-conflict with
   the old filenames on the removed list), and `sync_scaffold.py --check-refs` against
   this repo.
7. **Skill/CLI consistency:** every command string in `.claude/skills/run-audit/SKILL.md`
   parses against the real CLIs (`--help` smoke for each documented invocation).

## Decisions log (running)

- Families assigned in-registry (`check` vs `fact`) rather than splitting the registry:
  one engine, two thin surfaces — keeps `--report` (ceremony) able to run everything.
- No `audit.toml` fallback: zero repos have one (verified 2026-07-03), so a fallback
  would be dead compatibility code.
- `audit_scope.py`, `audit/<date>` tags, and `knowledge/audit-log.md` deliberately keep
  the audit name — they ARE the audit ceremony.
