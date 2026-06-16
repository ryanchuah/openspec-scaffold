<!-- Apply-phase implementation ONLY. Doc reconciliation (ai-docs/decisions.md,
     ai-docs/open-questions.md) is archive work, not apply — see notes.md for what the
     archive-executor must reconcile. Sections 1–2 and 3–4 are independent; do any order.
     Within §3, run 3.1 → 3.2 → 3.3 → 3.4 in order (each depends on the prior). -->

## 1. Harden delegated agent permissions (frontmatter)

- [x] 1.1 In `.opencode/agents/openspec-reviewer.md` frontmatter `permission:`, add `external_directory: allow`. Acceptance: the key is present; existing read/edit/bash/etc. unchanged. (~5m)
- [x] 1.2 In `.opencode/agents/apply-executor.md` frontmatter `permission:`, add an `external_directory` object with the catch-all FIRST (opencode is last-match-wins):
  ```yaml
  external_directory:
    "*": deny
    "/tmp/**": allow
  ```
  Acceptance: `"*": deny` precedes `"/tmp/**": allow`; existing keys unchanged. (~5m)
- [x] 1.3 In `.opencode/agents/archive-executor.md` frontmatter `permission:`, add the SAME `external_directory` object as 1.2 (catch-all first). Acceptance: block identical to apply-executor's. (~5m)

## 2. Harden delegated invocations (skills)

- [x] 2.1 In `.claude/skills/openspec-propose/SKILL.md`, the reviewer `opencode run` block: add `--dir <repoRoot>`, append `< /dev/null` after the stdout/stderr redirects, and add a one-line rationale note (stdin closed + `--dir` so a non-interactive permission prompt cannot hang the call — see the `noninteractive-delegation-safety` spec). Acceptance: the block contains `--dir`, `< /dev/null`, AND the rationale note. (~10m)
- [x] 2.2 In `.claude/skills/openspec-apply-change/SKILL.md`, the apply-executor `opencode run` block (Step 6): same three edits as 2.1. Acceptance: `--dir`, `< /dev/null`, and the rationale note all present. (~10m)
- [x] 2.3 In `.claude/skills/openspec-archive-change/SKILL.md`, the archive-executor `opencode run` block: same three edits as 2.1. Acceptance: all three present. (~5m)
- [x] 2.4 In `.claude/skills/openspec-verify-change/SKILL.md`, the fix-executor invocation snippet (the `timeout … opencode run …` line): add `--dir <repoRoot>` and `< /dev/null` EXPLICITLY (not only by reference to the apply skill), plus the rationale note. Suggested form: `timeout -k 15 300 opencode run --agent apply-executor --model deepseek/deepseek-v4-flash --dir <repoRoot> … < /dev/null`. Acceptance: the verify snippet itself contains `--dir`, `< /dev/null`, and the note. (~10m)

## 3. Rebuild the non-convergence canary (non-gameable)

- [x] 3.1 Create `docs/test/canary-non-convergence/canary_impl.py` with an editable function `def add(a, b):` returning `a + b`. Acceptance: importable module exposing `add`. (~5m)
- [x] 3.2 Rewrite `docs/test/canary-non-convergence/test_canary.py` to import the impl and assert a self-contradiction the impl cannot satisfy, with a header comment marking the file FROZEN / do-not-edit:
  ```python
  # FROZEN — do not edit. The impossibility is structural (see README); edit canary_impl.py only.
  from canary_impl import add
  def test_canary():
      result = add(1, 1)                    # call once, capture the single value
      assert result == 2 and result == 3    # one int cannot equal both — impossible for any impl
  ```
  Acceptance: the impossibility lives here (importing the editable impl), NOT as an assertion the executor is told to edit; `add` is called ONCE and the single captured value is tested against both predicates (so a stateful impl returning 2-then-3 cannot game it); the header marks the file frozen. (~10m)
- [x] 3.3 Update `docs/test/canary-non-convergence/tasks.md`: keep the single task "make `test_canary` pass" but list ONLY `canary_impl.py` under "Files affected", and add an explicit line that `test_canary.py` is FROZEN — do not edit. Acceptance: the editable surface is `canary_impl.py` only; `test_canary.py` is explicitly named as frozen. (~5m)
- [x] 3.4 Update `docs/test/canary-non-convergence/README.md` to describe the impl-module + frozen-test structure, why it is non-gameable (the only editable file cannot satisfy the frozen test), and that the expected outcome is a declared `### NON-CONVERGENCE BLOCKER` (trigger a, b, or c — a declared stop), not green and not a timeout. Acceptance: README matches the new structure. (~10m)

## 4. Commit-test-gate smoke fixture and procedure

- [x] 4.1 Add `docs/test/commit-gate-smoke/README.md` with a runnable snippet that exercises `scripts/test-gate.sh`'s five script-layer branches against a temp `test-cmd`. Acceptance: the README contains a runnable snippet that produces the five documented exits — absent → 0; empty → 0; unresolvable → 0 (warning); failing → 2 (blocked); passing → 0. (~20m)
- [x] 4.2 In that same README, document the gated-session HOOK-WIRING smoke procedure: in a Claude session whose project dir carries `.claude/settings.json` + a real `scripts/test-cmd`, confirm (a) a failing test-cmd blocks a `git commit`, (b) a passing test-cmd permits it, (c) `$CLAUDE_PROJECT_DIR` expands correctly. Acceptance: the three wiring checks are documented as a repeatable, operator-run gated-session procedure. (~15m)
