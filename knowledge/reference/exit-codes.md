# Exit-code conventions — deterministic tooling

Agent-neutral reference for the scaffold's check scripts. Convention: `0` = clean/ran, a
findings/violations code, and `3` = infrastructure failure (where applicable). Verified from
source; if a script changes its codes, update this table.

| Script | Exit codes | Meaning |
|---|---|---|
| `checks.py` | 0 / 2 / 3 | clean / findings present / infra failure or abort |
| `data_lint.py` | 0 / 2 / 3 | pass (or no checks) / violating rows / infra failure |
| `repo_lint.py` | 0 / 2 / 3 | pass (or no `checks/*.py`) / check findings / infra failure (nonzero exit, non-JSON, or timeout — stops on the FIRST one) |
| `audit_scope.py` | 0 / 3 | ran clean or tag created / git-or-radon failure (or tag exists). **Never 2** |
| `index_coverage.py` | 0 / 3 | ran (leads are informational, never gate) / infra failure. **Never 2** |
| `knowledge_lint.py` | 0 / 1 | no findings / drift found (1, not 2, to stay distinct from argparse's own exit 2) |
| `scaffold_lint.py` | 0 / 1 | no findings / one+ findings |
| `sync_scaffold.py --check` | 0 / 1 | converged (all identical) / drift (any differs or missing) |
| `sync_scaffold.py --check-refs` | 0 / 1 | no dangling refs / dangling refs found |
| `sync_scaffold.py` (sync mode) | 0 / 1 | synced / preflight validation failure (target missing, no .git, missing scaffold source) |
| `status_lint.py` | 0 / 2 | clean / hard violations |
| `check.sh` | 0 / non-zero | all stages pass (ruff check + format --check + test-cmd) / a named stage failed (stderr names which). Missing-tool degradation: absent ruff → warn+skip lint/format, proceed to tests. Absent/empty test-cmd → no-op (exit 0) |
| `test-gate.sh` | 0 / 2 | allow commit (delegates to `check.sh`, maps 0→0) / block commit (maps check.sh non-zero→2). Unresolvable tool / no test-cmd → no-op exit 0 (preserved from pre-check.sh behavior) |
| `_convergence.py` | verdict on **stdout** | prints `CONTINUE` or `STOP:<a\|b\|c>:<detail>`; `main()` always returns 0 — the exit code is NOT the signal |

Notes:
- All Python scripts use `argparse`, so an invalid CLI flag yields argparse's standard exit `2`
  regardless of the script's own convention.
- `_convergence.py`'s header docstring advertises an "exit 1 — no parseable verdict" that the code
  never returns; the unparseable case prints `STOP:c:…` and returns 0. Read the verdict from stdout.
