# Review log — shared-lint-layer (portfolio Change C, MEDIUM)

## Deepseek review waiver (2026-07-03)

The operator instructed "skip the deepseek direction review for this change." Per that instruction,
the deepseek `openspec-reviewer` pass (normally the MEDIUM tasks.md pro review) is **waived**. The
orchestrator's own self-review below is the propose-phase review of record. Direction was already
premise-vetted upstream: the portfolio explore-brief carried **PREMISE: AGREE** (direction gate,
2026-07-03) and tiers were operator-confirmed (C: MEDIUM).

## Round 1 — orchestrator self-review (2026-07-03)

Reviewed notes.md (acceptance criteria + design record), the three delta specs, and tasks.md against
the live codebase. Findings raised and resolved by the orchestrator:

- **[fixed] Spec validation — SHALL on the requirement's first line.** The knowledge-lint
  `broken-citation-skips` requirement was hard-wrapped so its first physical line lacked SHALL;
  `openspec validate --strict` rejected it. Reworded so `SHALL NOT` leads the statement. Change now
  validates clean (`--type change --strict`, exit 0).
- **[fixed] check.sh missing-tool degradation was unspecified.** `ruff` is declared nowhere today
  (user-global). A gate that hard-blocks when ruff is absent would brick every fresh clone. Added an
  explicit spec scenario + notes decision: a missing lint/format tool is a config error → warn +
  skip + continue (mirrors test-gate.sh's existing unresolvable-executable branch); provisioning is
  install-tools/dev-extras/CI's job, not the local hook. Reflected in tasks 2.2 and the
  shared-lint-gate spec.
- **[fixed] status_lint has no `collect_findings`.** Grounding showed `status_lint.py` exposes only
  `main(argv)` (knowledge_lint/scaffold_lint expose `collect_findings`). The live-tree gate test
  therefore asserts `status_lint.main([...]) == 0` rather than an empty findings list. Captured in
  notes.md and task 8.1.
- **[decided] E501 vs. the formatter.** The scaffold backlog is dominated by long-line errors, but
  `ruff format` does not reflow comments/strings/docstrings, so E501 would fight the formatter. Set
  `select = E,F,I,B` + `ignore = ["E501"]`, formatter `line-length = 100`. Flagged to the operator
  as marginally narrower than a literal "all of E" (ratchet back later). Task 1.1 + notes decision.
- **[verified] All referenced paths exist:** apply skill at `.claude/skills/openspec-apply-change/`,
  both reference docs (`exit-codes.md`, `new-repo-bootstrap.md`), both executor bodies, `test-gate.sh`,
  the manifest, and the knowledge_lint internals cited in tasks (skip-ladder, `collect_findings`).

**Scope note (surfaced to operator, not a defect):** C grew to include citation-matcher hardening
(discovered via a live extrends `knowledge_lint` run) because promoting the linter to a hard gate
without it would false-positive-block downstream. This keeps C a chunky-but-cohesive MEDIUM; operator
was given the option to split the matcher-hardening into a separate SMALL and chose to proceed
as one change (pending confirmation).

## Freeze

No 🔴 defects outstanding after the self-review fixes. Direction premise settled upstream (AGREE).
Artifacts frozen: `notes.md`, `specs/shared-lint-gate/`, `specs/commit-test-gate/`,
`specs/knowledge-lint/`, `tasks.md`. Ready for apply on operator request.
