# Notes — shared-lint-layer (portfolio Change C)

**Tier:** MEDIUM (tasks.md only; acceptance criteria + design decisions live here per AGENTS.md).
**Direction:** portfolio change **C** of `plans/day-to-day-tooling/explore-brief.md` §C
(direction gate PREMISE: AGREE, 2026-07-03; portfolio tiers operator-confirmed 2026-07-03 —
B: SMALL, A: MEDIUM, **C: MEDIUM**, D1/D2: SMALL). Banked research:
`plans/day-to-day-tooling/c-lint-layer-research.md`.
**Depends on:** B (sync deletion manifest) SHIPPED, A (checks-facts-split) SHIPPED. Any reference
to audit tooling uses the post-A names (`checks.py`/`facts.py`/`checks.toml`).
**Review waiver:** deepseek direction/review pass **waived by operator instruction (2026-07-03)** —
the orchestrator's own self-review is the propose-phase review of record (logged in `review-log.md`).

## Scope discovery that shapes this change (2026-07-03)

A live `knowledge_lint.py` run against the extrends knowledge tree (done while planning C) surfaced
that the broken-citation matcher **false-positives on legitimate citation notation**: brace-expansion
patterns, literal `YYYY-Www` placeholders, `file.py::symbol` node-ids, and `file.py:N-M` line ranges
all get flagged even though the underlying file exists (or the token is a deliberate pattern), plus
concrete `output/` artifacts (gitignored/regenerated) flag as unresolved. This is inert **today**
(the linter only runs on demand) but becomes load-bearing the moment C promotes it to a live commit
gate — an un-hardened matcher would false-positive-block every downstream repo. **Therefore C hardens
`_check_broken_citations` as part of wiring the gate** (AC#3). This is scope the §C brief did not
name; it is folded in here rather than deferred, because a gate that false-positives is not "green."

## Acceptance criteria (verified at verify; results appended below)

1. **One shared definition of green:** `scripts/check.sh` runs `ruff check` + `ruff format --check`
   + delegates to per-repo `scripts/test-cmd`, exiting nonzero if any stage fails. `test-gate.sh`
   invokes `check.sh` (not pytest directly). Live: a lint violation, a format drift, and a failing
   test each make `check.sh` exit nonzero; an all-clean tree exits 0.
2. **ruff.toml enforces the agreed ruleset:** a standalone scaffold-managed `ruff.toml` (no
   pyproject) selects **E, F, I, B** and enforces `ruff format`. Live: `ruff check` and
   `ruff format --check` both exit 0 on scaffold HEAD after the baseline reformat.
3. **Citation matcher stops false-positiving on legitimate notation:** `knowledge_lint.py`'s
   broken-citation check SKIPS (a) brace-expansion `{a,b}` / `{a..b}`, (b) `YYYY-Www` and
   `{placeholder}` templates, (c) `file::symbol` node-ids — resolved by checking the file and
   ignoring the `::suffix`, (d) `file:N-M` line ranges — resolved by checking the file, and (e)
   `output/` as an ephemeral prefix. Live: a fixture doc with one of each resolves clean; a
   genuinely-missing `src/…/gone.py` still flags. Each class has a unit test.
4. **Doc-lints gated on the live tree:** the pytest suite runs `knowledge_lint.py` and
   `status_lint.py` against the real repo (mirroring `scaffold_lint.py`'s live-tree test), so a
   drift introduced into a knowledge doc turns the suite red → the commit gate blocks it. Live:
   inject a broken citation → suite red; revert → green.
5. **No root handoff files:** a deterministic check fails when a root-level `HANDOFF*` / `HANDOVER*`
   file exists (mechanizes the knowledge-handoff-file decision). `knowledge/HANDOFF.md` (the
   sanctioned ephemeral mid-session handoff) is exempt. Live: create `./HANDOFF-x.md` → check fails;
   remove → passes.
6. **Executor autofix habit, in lockstep:** both `.claude/agents/apply-executor.md` and
   `.opencode/agents/apply-executor.md` gain the `ruff check --fix` + format-on-touched-files
   instruction, byte-identical bodies (`test_executor_body_agreement.py` green). The apply SKILL
   gains the matching autofix-before-done line.
7. **Hook fires only on real commits:** the `.claude/settings.json` PreToolUse gate no longer
   misfires on complex non-commit Bash (the parked reproduction — a harmless `true` payload with
   file redirections + an EXIT-sentinel echo — runs ungated); a genuine `git commit` with a red
   suite still blocks. A regression probe is added to the commit-test-gate smoke fixture.
8. **install-tools.sh provisions scanners:** scaffold-managed `scripts/install-tools.sh` installs
   pinned gitleaks + osv-scanner (deptry via dev extras), idempotent, documented in
   `new-repo-bootstrap.md`. (CI *enforcement* of scanners is per-repo D1/D2 — C ships the mechanism,
   not the downstream CI wiring.)
9. **Scaffold-managed + propagating:** `ruff.toml`, `scripts/check.sh`, `scripts/install-tools.sh`
   are on `scripts/scaffold_manifest.txt`; `scaffold_lint` (manifest completeness + no-conflict)
   green. `checks.toml` stays **per-repo** (never manifest), per A's seed convention.
10. **Gates green at commit:** full pytest suite + `scaffold_lint` SEAL + live-tree `knowledge_lint`
    (self) + `sync_scaffold.py --check-refs` all green.
11. **Reference docs updated:** `knowledge/reference/exit-codes.md` (check.sh exit convention) and
    `knowledge/reference/new-repo-bootstrap.md` (install-tools step) reflect the new surface.

## Design decisions (this is the MEDIUM change's design record — no separate design.md)

- **ruff config placement:** standalone `ruff.toml` at repo root, NOT `pyproject.toml`. The scaffold
  has no pyproject; downstream repos keep their pyproject lint-config-free (ruff prefers `ruff.toml`
  when both exist). Ruleset **E, F, I, B + enforced format** (operator decision; ratchet wider later).
  Per-file-ignores (if any) live in the shared `ruff.toml` — unmatched paths there are harmless, so
  one file serves all repos.
- **Line-length / E501 (decision + operator flag):** select `E, F, I, B` but **`ignore = ["E501"]`**,
  with formatter `line-length = 100`. Rationale: `ruff format` reflows *code* but NOT long
  comments/strings/docstrings, so E501 would leave un-reflowable residue that fights the formatter —
  the scaffold's prose-heavy `scripts/` backlog is dominated by exactly these. When the formatter is
  authoritative for width, disabling E501 is the conventional pairing. **Operator flag:** this is
  marginally narrower than a literal "all of E" (the confirmed ruleset) — surfaced for awareness;
  ratchet E501 back on later if a manual reflow pass is ever done. All other E checks stay on.
- **check.sh is the single green:** ruff check → `ruff format --check` → `bash scripts/test-cmd`.
  Exit convention documented in `exit-codes.md`. `test-gate.sh` (scaffold-managed, hook-invoked) is
  rewired to call `check.sh` so the Claude commit hook, CI, and humans all run the identical gate.
- **Missing-tool degradation (matches existing test-gate philosophy):** a missing/unresolvable
  `ruff` is a **config error → warn + skip lint/format, still run tests, do not hard-block** — same
  as test-gate.sh's current unresolvable-executable branch. A local hook that bricked every fresh
  clone lacking user-global ruff would be hostile. The forcing function that makes ruff actually
  present is: add `ruff` to the scaffold's `dev-requirements.txt` (currently absent) + `install-tools`
  + CI provisioning (D1/D2). CI has no excuse to skip; the local hook degrades gracefully.
- **status_lint has no `collect_findings`** (only `main()`), unlike knowledge_lint/scaffold_lint. Its
  live-tree gate test invokes `status_lint.main([...])` and asserts exit 0; knowledge_lint's asserts
  `collect_findings(REPO_ROOT) == []`. (Optionally add a `collect_findings` to status_lint for
  symmetry — decide at apply; not required.)
- **Citation-matcher hardening (AC#3):** extend the existing skip-ladder in
  `_check_broken_citations` (it already skips URLs, absolute paths, globs, placeholders, non-path
  tokens, first-segment-not-a-real-dir, and `EPHEMERAL_PATHS`). Add: brace-expansion detection,
  `YYYY-Www`-style placeholder detection, `::`-suffix stripping (then existence-check the file),
  `:N-M`-suffix stripping (then existence-check the file), and treat `output/` as an ephemeral
  prefix. Each addition is narrow and unit-tested for both the skip and the still-catches-real-drift
  case, so hardening does not blind the check to genuine drift.
- **Doc-lint live-tree gate:** add a pytest test that calls `knowledge_lint.collect_findings` (and
  the `status_lint` equivalent) against the real repo root and asserts zero findings — the exact
  pattern `scaffold_lint.py`'s test already uses. This converts the doc-lints from memory-invoked to
  gate-enforced without changing their detection logic (beyond AC#3).
- **Root-handoff check:** implement as a new finding in the doc-lint layer (so it rides the same
  live-tree gate), globbing repo-root `HANDOFF*`/`HANDOVER*` and exempting `knowledge/HANDOFF.md`.
- **Hook-matcher fix:** tighten the `.claude/settings.json` PreToolUse `if:` so the gate fires only
  on a genuine `git commit` argv (not on arbitrary Bash carrying `git commit` as a substring in a
  redirection/echo). Add the parked reproduction to the smoke fixture as a must-not-gate probe.
  Full evidence: `plans/day-to-day-tooling/c-lint-layer-research.md` §hook-matcher-bug and the
  parked `knowledge/questions/commit-test-gate-hook-misfire.md`.
- **Scaffold's own baseline lands green in THIS change:** run `ruff check --fix` + `ruff format`
  over the scaffold, commit the baseline, so the new gate is green on HEAD before it is wired.

## Delta-spec surface (capabilities this change modifies)

- `knowledge-lint` — citation-matcher hardening (AC#3) + live-tree gate (AC#4) + root-handoff
  check (AC#5).
- `commit-test-gate` — `test-gate.sh` → `check.sh` rewire (AC#1) + hook-matcher fix (AC#7).
- A new capability for the shared lint/green layer (`ruff.toml` + `check.sh` + `install-tools.sh`)
  OR fold into `commit-test-gate` — decide at spec-authoring; prefer a dedicated capability if the
  green-definition surface reads cleanly on its own.

## Discoveries (running)

- (2026-07-03) Extrends citation false-positives (see "Scope discovery" above) — the taxonomy is
  being independently confirmed by the parallel extrends knowledge-drift burn-down session, which
  writes a linter-gap report to `/tmp/extrends-lint-gap-report.md`. C's AC#3 does not block on that
  report; the report is corroboration, and C's fix propagates the cure downstream via D1/D2.
