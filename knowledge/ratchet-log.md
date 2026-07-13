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

See `openspec/changes/lesson-check-ratchet/specs/finding-closure-ratchet/spec.md` for the full requirement. <!-- lint:planned -->

- **2026-07-10** · ratchet-ledger-format · check:scripts/knowledge_lint.py::_check_ratchet_log — self-referential bootstrap; the ledger's own format check.
- **2026-07-10** · delegation-timeout-budget-drift · check:scripts/scaffold_lint.py::budget-agreement — pre-existing exemplar of lesson→check conversion (mechanize-invariants, 2026-07-02).
- **2026-07-10** · repo-invariant-runner-contract · test:scripts/test_repo_lint.py::test_stops_on_first_infra_failure — the runner's load-bearing fail-loud behavior, pinned by name.
