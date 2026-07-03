# notes — clarify-audit-tooling-surface

## Acceptance criteria
See `design.md` § Verification (the change-specific acceptance criteria live there).

## Archive-phase instruction (spec Purpose prose — NOT carried by the delta)
The delta at `specs/knowledge-lint/spec.md` carries the two MODIFIED requirement blocks; at archive,
sync-specs merges them into `openspec/specs/knowledge-lint/spec.md`. The delta format cannot carry a
change to the spec's **Purpose** prose (non-requirement). So, when archiving, ALSO edit
`openspec/specs/knowledge-lint/spec.md` Purpose (line ~6): `lint-knowledge` → `knowledge-drift-review`,
and reword the "deterministic linter vs LLM skill" sentence so it no longer leans on the (now removed)
near-mirrored naming. After that + the delta merge, the main spec contains no `lint-knowledge`.

## Deferred follow-on (not this change)
Propagation of this change to extrends + psc-monitor is a separate sync batch, with a downstream
tombstone step (`rm -rf .claude/skills/lint-knowledge/` per repo). Tracked in `knowledge/STATUS.md`.

## Verify checkpoint (2026-07-03)

1. **Verdict:** READY for archive.
2. **Live output eyeballed (behavior, not counts):** probed the real `check_dangling_skill_refs`
   against the live repo — a doc referencing `knowledge-drift-review` and `run-audit` (both real
   dirs) produced NO dangling finding (correctly validated); `openspec-ghost` was flagged; a
   lingering `lint-knowledge` reference was NOT flagged. That last point confirms the documented D2
   trade-off: removed non-`openspec-` names drop out of `_NON_OPENSPEC_SKILL_TOKENS` and are not
   detected — rename-completeness is instead enforced by the grep sweep, which came back clean
   (only the deliberately-excluded main spec + change dir retain `lint-knowledge`). Full suite green;
   the new regression test genuinely exercises detect-then-validate for the generalized set.
3. **Defects found & fixed:** none. (Self-review only; multi-model passes waived by operator
   directive given no uncertainty — recorded here per the reviewer-can-be-wrong / disclosure rule.)
4. **As-built deltas:** implementation matches design/tasks. One cosmetic carryover: both skills'
   frontmatter `compatibility: Requires openspec CLI` is template boilerplate — `run-audit` does not
   actually require the openspec CLI (it drives `audit_bundle.py`/`audit_scope.py`). Not fixed (matches
   the pre-existing knowledge-drift-review boilerplate); noted for a possible future cleanup.
5. **Forward-looking items (fold into `knowledge/questions/INDEX.md` at archive):**
   - **Propagation follow-on:** sync this change (rename + `run-audit` + `scaffold_lint` generalization)
     to extrends + psc-monitor; the rename adds a downstream tombstone (`rm -rf
     .claude/skills/lint-knowledge/`). extrends took the pre-rename state on 2026-07-03.
   - **`run-audit` never exercised end-to-end:** the scaffold has no wired audit layer (no
     `audit.toml`/`checks/`/task targets), so the skill's full cycle is unproven against a real audit
     run; its commands are verified accurate but the first live exercise happens when a downstream
     repo wires the audit layer. Monitored, not blocking.
   - **`scaffold_lint` removed-name blind spot (D2 trade-off):** references to a *removed* non-openspec
     skill are not flagged by `scaffold_lint` (only by a manual grep). Harmless with 2 non-openspec
     skills; revisit if the non-openspec skill set grows or a rename recurs.
   - **Metadata cleanup:** the `compatibility` boilerplate on `run-audit` (and `knowledge-drift-review`).

## Still owned by archive
- Merge the `specs/knowledge-lint/spec.md` delta into `openspec/specs/knowledge-lint/spec.md`
  (2 MODIFIED requirements) **and** apply the Purpose-line rename per the archive instruction above.
- Reconcile `knowledge/STATUS.md`, `knowledge/decisions/INDEX.md` (new decision entry), and
  `knowledge/questions/INDEX.md` (the field-5 forward-looking items).
- Move the change dir to `openspec/changes/archive/2026-07-03-clarify-audit-tooling-surface/`.
- No code cleanup owed.
