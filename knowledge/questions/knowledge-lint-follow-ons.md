# knowledge-lint follow-ons

Parked from `openspec/changes/archive/2026-07-02-knowledge-lint/notes.md` (field-5 "Forward-looking
items"). None of these are active blockers — all are deferred, monitored, or gated behind a later
operator/downstream action.

- **Scaffold's own pre-existing knowledge drift** — RESOLVED 2026-07-03 by `prune-knowledge`. All three
  sub-items fixed: the roadmap entry was closed (shipped changes referenced by decision name), the
  lessons.md lesson-archive path was repointed to the archive prefix, and the decisions/INDEX.md
  historical mention was de-slashed. Per-repo content-cleanup follow-on complete.
- **Known-absent-by-design paths** — all concrete instances now addressed: knowledge/audit-log.md is
  handled via the linter's EPHEMERAL_PATHS mechanism (task 1.1); the .opencode/skills/ contrast
  citations and the cross-repo historical-reports.md ref are handled by de-citing (tasks 3.1–3.3).
  OPEN QUESTION resolved: a general known-absent/allowlist mechanism is NOT added (YAGNI holds); the
  residual linter-smarts gap — it cannot natively distinguish contrast / cross-repo / archived-change
  citations from real drift — stays a deferred follow-on.
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
