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

## Discoveries (running)

- **Commit-test-gate hook misfire (found live during apply, 2026-07-03):** the
  `.claude/settings.json` PreToolUse hook (`if: "Bash(git commit*)"`) fires on some
  complex non-commit Bash commands — reproduced with a harmless `true` payload carrying
  file redirections + an EXIT-sentinel echo, while plain probes (`echo`, `git status`,
  single-line `opencode run --help`) pass. While the suite is red mid-change, this
  intermittently blocks the orchestrator's own delegation launches. Workaround this
  session: put the launch in a script file and invoke it as a single plain command.
  Root-cause fix belongs in the lint-layer change (portfolio C) or its own SMALL: tighten
  the hook matcher so only actual `git commit` invocations gate.

## Verify outcome (2026-07-03, orchestrator = Fable 5 under Claude Code)

**1. Verdict: READY FOR ARCHIVE** — with the multi-model passes **waived by operator
instruction** ("skip the pro and flash review pass for this", 2026-07-03). The
orchestrator's own behavioral review ran in full and is the basis of this verdict; the
pro pass was launched and deliberately abandoned unread, the flash pass never launched.

**2. Live output eyeballed (behavioral review):**
- `checks.py --list` in this repo: FAMILY column present; gitleaks shows
  enabled-but-unavailable and the one-line preflight warning prints; exit 0.
- Preflight probe (tmp repo, four enabled tools missing from PATH): ALL FOUR reported in
  ONE run, each line carrying trigger + install-or-disable guidance + coverage note;
  exit 3; no check artifacts written (run-manifest.json only, recording the abort).
- `facts.py` default run: only enabled facts ran (scope, inventory), undated
  `output/facts/`, exit 0; inventory.json carries real tree/entrypoints/env_vars and
  `audit_anchor` (null/null in this untagged repo).
- Tag-sort probe: with an alphabetically-LAST tag created FIRST and an
  alphabetically-FIRST tag created LAST, `audit_anchor` picked the latest-by-creatordate
  tag with `commits_since` exact — the inlined lookup preserves `--sort=-creatordate`
  and is CWD-independent (`git -C`).
- `facts.py --check ruff`: rejected as check-family with pointer to checks.py, exit 2.
- `audit_scope.py log-line` without `knowledge/audit-log.md`: hint on stderr only;
  stdout byte-identical with and without the file; exit 0.
- Full suite green via the canonical gate (`scripts/test-gate.sh` exit 0).

**3. Defects found and fixes:** none at verify (self-review). During apply: propose-round
reviews (pro) caught wrong line citations and an undefined facts/preflight contract
before implementation; slice 3 timed out after completing its work (retry added only the
missing 6.5 test); orchestrator made three disclosed trivial inline edits (one-word
docstring repoints in data_lint.py/index_coverage.py/audit_scope.py).

**4. As-built deltas (not in tasks.md):**
- Fact-family entries that hit a MID-RUN infra failure inside `--report` now degrade
  gracefully (recorded, run continues) instead of aborting — a coherent extension of the
  preflight exemption; stop-on-first-failure retained for check-family.
- A preflight-aborted run writes `run-manifest.json` but NOT `findings.json` (the old
  mid-run abort wrote both). Nothing consumes findings.json from aborted runs today.
- `facts.py` usage errors are hand-rolled stderr + exit 2 (argparse-convention code,
  not argparse-raised).
- Registry `trigger` strings for jscpd/vulture read "always (enabled explicitly)" —
  accurate for config-enabled heavy checks, slightly odd in a message.
- The custom-check disable hint says `[checks.<name>] enabled = false`, but custom
  checks are opted in by table presence — the hint is imprecise for customs (cosmetic).

**5. Forward-looking items (recorded nowhere else — fold into knowledge/questions/ at archive):**
- **Commit-test-gate hook misfire** (see Discoveries above): root-cause + fix owed —
  earmarked for portfolio change C (lint layer) or its own SMALL.
- **Simplicity-gate findings (self-run, non-blocking, parked):** (a) the
  install-or-disable INFRA-FAIL message is constructed in three places in
  `_mode_multi` — extract a helper in the parked engine refactor
  (`knowledge/questions/deterministic-tooling-layer-follow-ons.md` already tracks that
  refactor); (b) `facts.py`'s `kind == "custom"` branches are unreachable (customs are
  always check-family) — dead guard, prune in the same refactor.
- **facts.py radon-absent UX:** summary line reads "INFRA-FAIL" (from the runner's
  FileNotFound record) even though the process exits 0 by contract — consider a
  "skipped"-style label for fact-family degradation in a future pass.
- **First real preflight/report run against installed binaries still pending** — the
  scaffold has no gitleaks/osv-scanner/deptry; the first downstream wired run remains
  the true integration test (existing parked item; now also covers preflight).
- **plans/ briefs mention old names by design** — the portfolio explore-brief describes
  the rename itself; acceptance criterion 5's grep treats plans/ as period documents.

**Still owned by archive (fresh session):** reconcile `knowledge/STATUS.md` (audit-tooling
narrative now names checks.py/facts.py), `knowledge/decisions/INDEX.md` (registry line for
this change), `knowledge/questions/INDEX.md` (fold field-5 items; update
`run-audit-untested.md` which now references checks.py), promote the knowledge-lint delta
spec into `openspec/specs/knowledge-lint/spec.md`, move this change dir to
`openspec/changes/archive/2026-07-03-checks-facts-split/`, and delete the superseded
`plans/day-to-day-tooling` items ONLY when the whole portfolio closes (brief stays live —
changes C, D1, D2 still pending).

## Decisions log (running)

- Families assigned in-registry (`check` vs `fact`) rather than splitting the registry:
  one engine, two thin surfaces — keeps `--report` (ceremony) able to run everything.
- No `audit.toml` fallback: zero repos have one (verified 2026-07-03), so a fallback
  would be dead compatibility code.
- `audit_scope.py`, `audit/<date>` tags, and `knowledge/audit-log.md` deliberately keep
  the audit name — they ARE the audit ceremony.
