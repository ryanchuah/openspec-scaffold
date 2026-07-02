# knowledge-lint follow-ons

Parked from `openspec/changes/archive/2026-07-02-knowledge-lint/notes.md` (field-5 "Forward-looking
items"). None of these are active blockers — all are deferred, monitored, or gated behind a later
operator/downstream action.

- **Scaffold's own pre-existing knowledge drift the linter now surfaces** (out-of-scope to fix in the
  knowledge-lint change itself, but real): `knowledge/roadmap.md` still recommends the retired
  `ai-docs/` path; `knowledge/lessons.md` cites `openspec/changes/fix-convergence-guard/` without its
  `archive/2026-06-17-` prefix; `knowledge/decisions/INDEX.md` (line 38) mentions `ai-docs/` (judgment
  call — may be legitimate historical context). Per-repo content-cleanup follow-on.
- **Known-absent-by-design paths still flag as forward-references:** `knowledge/audit-log.md` (created
  per-repo once audits run), `scripts/test-cmd` (per-repo, legitimately absent in the scaffold),
  `.opencode/skills/` (deliberately absent per the `skills-in-dot-claude-only` decision), and a
  cross-repo `plans/historical-reports.md` cited in `knowledge/questions/parked-psc-monitor.md`. OPEN
  QUESTION: add a known-absent/allowlist mechanism to drive these to zero, or keep
  enumerate-and-judge? Deliberately NOT added now (simplicity/YAGNI) — revisit only if the noise grows.
- **Downstream propagation burn-down (follow-on):** once `knowledge_lint.py` + the `lint-knowledge`
  skill propagate to extrends/psc-monitor via `sync_scaffold.py`, each repo should run a first
  `lint-knowledge` pass to burn down its own drift backlog — a separate per-repo follow-on. Propagation
  itself is frozen pending operator go-ahead (see `knowledge/STATUS.md`), joining the
  `deterministic-tooling-layer` pending-propagation queue.
- **Latent check, untested against real data:** the audit-log registry-format check is guarded on
  `knowledge/audit-log.md` existence; the scaffold has none yet, so the check is unexercised against a
  real file until a repo grows one — monitor when `deterministic-tooling-layer` wiring produces the
  first `audit-log.md`.
- **Possible new linter check (unbuilt):** `knowledge_lint.py` could grow a check for count-recording
  patterns ("N tests pass"-style tallies) in tracked docs — the `never-record-counts` rule is today
  enforced only by convention/review. Surfaced from the deterministic-tooling-layer session, which hit
  that rake via a verbatim-appended verifier evidence block. Deferred (YAGNI until the rake recurs).
- **Simplicity suggestion (non-blocking):** a few token-exclusion predicates in `knowledge_lint.py`
  (`_is_url`, `_is_absolute_system_path`, `_has_whitespace`) are now partly redundant behind the
  first-segment gate; left as belt-and-suspenders, could be pruned in a future pass. The
  `lint-knowledge` skill also uses `python` not `python3` (mixed convention repo-wide; agents adapt) —
  minor.
