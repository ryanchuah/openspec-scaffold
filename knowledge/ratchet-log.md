# Ratchet Log — Finding-Closure Registry

Format per entry (registry-line, one per finding-class):

```
- **YYYY-MM-DD** · <kebab-class-slug> · <disposition> — <essence>
```

Disposition is one of:
- `check:<pointer>` — enforcing deterministic check (file path, optionally `::name`)
- `test:<path>[::<name>]` — frozen regression test linkage
- `waiver:review-by YYYY-MM-DD` — domain-judgment-only, re-review triggered
- `open:since YYYY-MM-DD` — enforcement deferred (age-flagged at threshold)
- `grandfathered` — pre-ratchet legacy lesson, format only

Preference ordering: check > frozen test > waiver; `open` is temporary.

See `openspec/specs/finding-closure-ratchet/spec.md` for the full requirement.

- **2026-07-10** · ratchet-ledger-format · check:scripts/knowledge_lint.py::_check_ratchet_log — self-referential bootstrap; the ledger's own format check.
- **2026-07-10** · delegation-timeout-budget-drift · check:scripts/scaffold_lint.py::budget-agreement — pre-existing exemplar of lesson→check conversion (mechanize-invariants, 2026-07-02).
- **2026-07-10** · repo-invariant-runner-contract · test:scripts/test_repo_lint.py::test_stops_on_first_infra_failure — the runner's load-bearing fail-loud behavior, pinned by name.
- **2026-07-13** · touch-surface-omits-readme · waiver:review-by 2026-07-31 — a role/chain vocabulary change (OW-3) left root `README.md` stale because the touch-surface inventory scanned skills/agents/AGENTS.md/specs but not the human-facing README; future vocabulary/role-shape changes MUST inventory root `README.md` by hand. No clean deterministic detector (semantic cross-prose consistency); re-review after the OW-5/OW-6 batch confirms whether the by-hand discipline held.
- **2026-07-13** · skill-template-parser-roundtrip · open:since 2026-07-13 — an inlined skill template consumed by a deterministic parser (OW-5: correctness-audit CENSUS/FINDINGS templates ↔ `knowledge_lint._check_audit_dossier`) can drift from its parser with no deterministic catch; manifested at verify as a census-delimiter prose/parser mismatch. Concrete enforcement is a test that extracts the fenced template block and asserts it lints clean (see `knowledge/questions/correctness-audit-skill-follow-ons.md` #2); deferred, not yet built.
- **2026-07-13** · skill-delegates-write-to-readonly-agent · open:since 2026-07-13 — a skill step delegated a file WRITE to a read-only (`edit: deny`) agent (OW-6: the composition-audit pre-digest step told `openspec-reviewer` to write `pre-digest.md`); the read-only reviewer/verifier agents cannot write, so the step fails at runtime. Fixed by having the agent EMIT the shortlist as text and the orchestrator write the checkpoint. Enforcement idea: a lint scanning `.claude/skills/*/SKILL.md` delegation blocks that invoke `--agent openspec-reviewer|openspec-verifier` with a prompt instructing a file write; heuristic, not yet built.
- **2026-07-13** · medium-change-spec-delta-unvalidated · open:since 2026-07-13 — `openspec validate <name>` discovers changes via `proposal.md`, so a MEDIUM change (tasks.md-only) and its spec deltas are never CLI-validated (prints "Unknown item", exit 0). Re-manifested in `instruction-surface-coherence`: the `tier-confirmation-gate` delta's SHALL-not-on-first-line error would have shipped had it not been caught by the pro review + manual inspection. Enforcement path: a `scaffold_lint`/`checks.py` check that discovers changes by DIR presence and structurally validates `openspec/changes/*/specs/**/spec.md` deltas (ADDED/MODIFIED/REMOVED/RENAMED headers, normative SHALL on the requirement's first physical line, `#### Scenario:` WHEN/THEN). Candidate to fold into OW-11 (mechanized gates). Source: `OUTSTANDING-WORK.md` finding 2.
- **2026-07-13** · detector-filewalker-scans-hidden-dirs · test:scripts/test_checks.py::test_hidden_dir_skipped — a new AST file-walking detector (`checks.py:_iter_py_files`, OW-1/OW-4) scanned INTO hidden dirs (`.claude/worktrees/`, `.git`-adjacent) because it excluded only an explicit `{.venv,.git,__pycache__}` set; caught at verify (inflated self-findings 24→13). Fixed by skipping any path component starting with `.`, pinned by a frozen test. Generalizable to any future file-walking detector in `checks.py`/`checks/*.py`; no clean deterministic cross-detector check (semantic — can't statically prove an `os.walk`/`rglob` excludes hidden dirs), so the disposition is the pinned instance + this convention note for future detectors.
