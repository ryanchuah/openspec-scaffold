## Context

Scaffold-managed instruction surface. The change (per the frozen `proposal.md`) renames the
`lint-knowledge` skill to `knowledge-drift-review`, adds a `run-audit` skill, generalizes
`scaffold_lint.py`'s hardcoded `lint-knowledge` special-case, and makes surgical AGENTS.md doc
fixes. No deterministic script behavior changes. Hard constraint: the live-repo SEAL
`scripts/test_scaffold_lint.py::test_live_repo_lints_clean` (runs `collect_findings` against the
real repo root, asserts clean) MUST stay green, and the full `pytest -q` suite MUST stay green.

Current `dangling-skill-refs` detection (`scaffold_lint.py`): `_TOKEN_RE` matches `openspec-*`
tokens; `_LINT_KNOWLEDGE_RE = re.compile(r"\blint-knowledge\b")` is a one-off literal for the only
non-`openspec-` skill. Detected tokens are validated against
`valid_tokens = _skill_dir_names ∪ _agent_file_stems ∪ {"openspec-scaffold"}`.

## Goals / Non-Goals

**Goals:**
- Two unmistakable names: `knowledge_lint.py` (deterministic script) vs `knowledge-drift-review`
  (LLM skill); a discoverable `run-audit` entry point for the audit cycle.
- `scaffold_lint` generalized so any number of non-`openspec-` skills validate without per-name
  hardcoding.
- SEAL + suite stay green; the `knowledge-lint` spec stays internally consistent post-rename.

**Non-Goals:**
- No change to `knowledge_lint.py`, `audit_bundle.py`, `audit_scope.py`, `data_lint.py`,
  `index_coverage.py` behavior.
- No downstream propagation (separate follow-on batch; extrends/psc-monitor unchanged this change).
- No new capability spec for `run-audit` (see D5).
- No per-repo audit-layer wiring built here (`audit.toml`/`checks/`/task targets remain per-repo).

## Decisions

### D1 — Rename `lint-knowledge` → `knowledge-drift-review`
`git mv .claude/skills/lint-knowledge .claude/skills/knowledge-drift-review`; set the SKILL.md
frontmatter `name: knowledge-drift-review`; update the manifest line. The skill BODY prose that
describes cadence/steps is unchanged except: line ~30's `python scripts/knowledge_lint.py` gains
the interpreter note (see D3's convention, applied consistently). Full occurrence sweep to update
(from the grep audit): `scaffold_manifest.txt`, `scaffold_lint.py` (D2), `test_scaffold_lint.py`
fixtures (the `_LINT_KNOWLEDGE_SKILL` fixture name + the two references at ~line 96/109 + the
manifest fixture lines ~126/134), the `knowledge-lint` spec (per S-delta below), and per-repo prose
`knowledge/STATUS.md`, `knowledge/reference/resync-verification.md`,
`knowledge/questions/knowledge-lint-follow-ons.md`. NOT touched: `knowledge/decisions/INDEX.md`
historical line and archived change dirs (immutable records). The FILENAME
`knowledge-lint-follow-ons.md` stays as-is — it uses the *concept* name `knowledge-lint`, not the
skill name; only its content refs update. The `test_scaffold_lint.py` `_SKILL_CLEAN` fixture line
(~96) `... and \`lint-knowledge\` for the knowledge linter.` becomes
`... and \`knowledge-drift-review\` for the knowledge linter.`

**Alternative rejected:** rename the script instead — no; `knowledge_lint.py` is correct within the
`*_lint.py` family (status_lint, data_lint, scaffold_lint). The skill is the outlier.

### D2 — Generalize `scaffold_lint` non-`openspec-` skill detection
Replace `_LINT_KNOWLEDGE_RE` with a named constant set and detect each member:
```python
# Non-openspec skills have no shared prefix to pattern-match, so police them by
# explicit name. Keep in step with the actual .claude/skills/ non-openspec dirs.
_NON_OPENSPEC_SKILL_TOKENS: frozenset[str] = frozenset(
    {"knowledge-drift-review", "run-audit"}
)
```
In `check_dangling_skill_refs`, after collecting `_TOKEN_RE` matches, add each token in
`_NON_OPENSPEC_SKILL_TOKENS` found in the text (word-boundary `re.search(rf"\b{re.escape(t)}\b", text)`)
to the set-to-validate. Validation against `valid_tokens` is unchanged: both new skills exist as
dirs, so they resolve → SEAL stays green; a reference to a *removed* one of them would still flag
(detect-then-validate preserved). Update the docstring's `dangling-skill-refs` description (line ~80)
to describe the set instead of the single literal token.

The frozen proposal's wording ("resolves *any* non-`openspec-` skill token against the actual skill
directory names") reads as auto-deriving the detection set from live skill dirs; this design
deliberately **refines** that to an explicit frozenset for the reason below.
**Alternative rejected (the proposal's literal reading):** derive the detection set from live skill
dirs — loses the ability to flag a dangling reference to a *removed* non-openspec skill (the removed
name would drop out of the derived set). The explicit set keeps that property. **Alternative rejected:** two hardcoded regexes — just
swaps one hardcode for two; the set is the honest generalization. A lingering `lint-knowledge`
straggler is caught by the tasks-phase grep sweep, not by this check (acceptable: rename-completeness
is a one-time migration check, not a standing invariant).

### D3 — `run-audit` skill design
New `.claude/skills/run-audit/SKILL.md`, modeled on the `knowledge-drift-review` (ex-lint-knowledge)
SKILL.md structure (frontmatter + Steps + Output + Guardrails). Content:
- **Frontmatter:** `name: run-audit`; description triggering on "run an audit / audit this repo /
  deterministic audit cycle", noting it's operator-invoked and writes report artifacts + the
  audit-log line only.
- **Interpreter convention (fixes bare-`python`):** a short try-order the agent follows —
  prefer a repo task-runner `audit-*` target if one exists; else `.venv/bin/python` if present;
  else `python3`; else `python`. State it once; use `<py>` as the placeholder in the steps.
- **Step 0 — pre-check:** confirm `scripts/audit_bundle.py` and `scripts/audit_scope.py` exist and
  run under `<py>` before entering the cycle; a missing/unrunnable base script fails fast with a
  clear message (don't discover it mid-cycle).
- **Cycle steps:** (1) `<py> scripts/audit_bundle.py --list` to see the registry;
  (2) `--floor` (quick) or `--report --date <YYYY-MM-DD>` (full → `output/audit/<date>/`);
  (3) triage findings from the JSON artifacts (judgment — the skill's LLM value);
  (4) `<py> scripts/audit_scope.py tag --date <date>` — the one repo-state mutation, **tagged ONLY
  when the operator's invocation explicitly asks to "tag" / "anchor this audit"; otherwise the cycle
  runs read-only and reports findings without tagging**; (5) `<py> scripts/audit_scope.py log-line
  --date <date> --essence "..."` and append its printed line to `knowledge/audit-log.md`.
- **Error handling:** stop the cycle on the first non-zero script exit and report it (do not proceed
  to later steps); if `output/audit/<date>/` already exists, report it and do NOT overwrite or
  re-run without explicit operator direction.
- **Wiring-detection branch:** before running, check for the per-repo layer; if `audit.toml` /
  `checks/` / a task-runner `audit-*` target are absent, say so and point at what each is
  (concise inline guidance) rather than failing opaquely — but do NOT auto-create them (per-repo,
  operator-directed).
- **Guardrails:** `audit_bundle.py` writes reports only; `audit_scope.py tag` is the sole
  repo-state mutation and is operator-gated; the audit-log.md append is the sole tracked-file
  write and is operator-reviewed; never fix code from this skill.

### D4 — AGENTS.md surgical edits (bounded scope — resolves 🟡3)
Keep the 4-paragraph "Deterministic audit tooling" section structure; make three surgical edits, no
structural rewrite: (a) note the interpreter is per-repo (`python` shown illustratively; use the
repo's interpreter / `run-audit` handles this); (b) reword the `just audit-floor` example so it
reads as an *if-defined* per-repo convention, not a promise a fresh repo has it; (c) add one
sentence naming the `run-audit` skill as the entry point and distinguishing `knowledge_lint.py`
(deterministic) from `knowledge-drift-review` (LLM). This section is in the AGENTS.md shared span,
so the edits propagate.

### D5 — `run-audit` gets NO capability spec
Consistent with the `deterministic-tooling-layer` precedent (audit contract lives in code docstrings
+ AGENTS.md, not a spec). The skill's existence, manifest-listing, and single-path integrity are
enforced by `scaffold_lint` (manifest-completeness + dangling-skill-refs) — no spec needed. Only the
`knowledge-lint` spec changes, because it already spec'd the renamed skill.

### S-delta — `knowledge-lint` spec (all `lint-knowledge` occurrences — 7; requirement body line 93 carries both the skill name and the path)
MODIFIED requirements `judgment-layer-skill-detects-semantic-drift` and
`knowledge-lint-tooling-is-scaffold-managed`, plus the Purpose prose:
- Purpose line 6: reword the "deterministic linter vs LLM skill" sentence to use the now-distinct
  names (drop the near-mirrored-names framing; name `knowledge-drift-review` explicitly).
- Req `judgment-layer-…` body (line 93): `A \`lint-knowledge\` skill SHALL exist at
  \`.claude/skills/lint-knowledge/SKILL.md\`` → `knowledge-drift-review` + new path.
- Scenario `deterministic-pass-runs-first` (line 105): `the \`lint-knowledge\` skill` → new name.
- Scenario `skill-ships-single-path-detect-only` (line 122): path → new path.
- Req `knowledge-lint-tooling-is-scaffold-managed` body (line 127) + scenario
  `manifest-lists-linter-tooling` (line 134): `.claude/skills/lint-knowledge/SKILL.md` → new path.
All SHALL semantics (single path, no `.opencode/` copy, manifest-listed, detect-only) unchanged.
**Split note:** the 6 requirement-body/scenario occurrences ride the delta (`specs/knowledge-lint/spec.md`)
and merge into the main spec at archive; the 7th — the Purpose prose (line ~6) — cannot be carried by
the delta format and is an explicit archive-phase edit (see `notes.md`).

## Risks / Trade-offs

- **Missed rename occurrence leaves a dangling reference** → the tasks phase runs a final
  `grep -rn 'lint-knowledge'` over the non-archive tree; only the intentional
  `knowledge/decisions/INDEX.md` historical line and `openspec/changes/archive/**` may remain.
- **SEAL false-negative if `_NON_OPENSPEC_SKILL_TOKENS` omits a real skill** → under-detection, not
  a break; the SEAL still passes. Mitigated by both new names being in the set from the start.
- **Downstream drift until propagated** → extrends/psc-monitor keep the old skill name until the
  follow-on sync batch; explicitly deferred, tracked in STATUS.

## Migration Plan

In-repo only: rename (git mv), edit, verify. Rollback = `git revert` the change commit(s).
Downstream tombstone (`rm -rf .claude/skills/lint-knowledge/`) happens in the later propagation
batch, not here.

## Verification (acceptance criteria)

1. `python3 scripts/scaffold_lint.py` → `scaffold-lint: clean`; `pytest -q` green (incl.
   `test_live_repo_lints_clean` and a NEW dangling-skill-refs test). Test construction: a fixture
   tree where `knowledge-drift-review`'s skill dir EXISTS but `run-audit`'s does NOT, with a scanned
   doc referencing both → `knowledge-drift-review` validates (dir present) while `run-audit` is
   flagged (it's in `_NON_OPENSPEC_SKILL_TOKENS` so detected, but has no dir so it's absent from
   `valid_tokens`) — proving detect-then-validate holds for the generalized set.
2. `.claude/skills/knowledge-drift-review/SKILL.md` and `.claude/skills/run-audit/SKILL.md` exist;
   `.claude/skills/lint-knowledge/` is gone; all three manifest deltas applied;
   `python3 scripts/sync_scaffold.py --check-refs .` → exit 0.
3. `grep -rn 'lint-knowledge'` over the tree returns only the `knowledge/decisions/INDEX.md`
   historical line + `openspec/changes/archive/**` (no live instruction-surface or spec hit).
4. `openspec/specs/knowledge-lint/spec.md` contains no `lint-knowledge` and references
   `knowledge-drift-review` at the new path; the spec reads consistently.
5. AGENTS.md "Deterministic audit tooling" retains its structure with the three surgical edits;
   `run-audit` is named as the entry point.
