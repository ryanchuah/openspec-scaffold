# Open Questions

## Active

<!-- No current scaffold blockers. (rename-memory-to-knowledge push/merge to all 3 mains: DONE 2026-06-19.) -->

## Parked

- Growth-trigger (restructure-project-knowledge follow-on) → `knowledge/questions/restructure-growth-trigger.md`

- Harden-delegation follow-ons → `knowledge/questions/harden-delegation-follow-ons.md`
- Harden-delegation-robustness follow-ons → `knowledge/questions/harden-delegation-robustness-follow-ons.md`
- Verify-multimodel-gate follow-ons → `knowledge/questions/verify-multimodel-gate-follow-ons.md`
- Fix-sync-mechanism follow-ons → `knowledge/questions/fix-sync-mechanism-follow-ons.md`
- Dedup-scaffold (W2) follow-ons → `knowledge/questions/dedup-scaffold-follow-ons.md`
- Lifecycle-gates (W4) follow-ons → `knowledge/questions/lifecycle-gates-follow-ons.md`
- Fix-convergence-guard (W3) follow-ons → `knowledge/questions/fix-convergence-guard-follow-ons.md`
- Propagate-baseline (W6) follow-ons → `knowledge/questions/propagate-baseline-follow-ons.md`
- Lean-boot-context follow-ons → `knowledge/questions/lean-boot-context-follow-ons.md`
- Instruction-surface cleanup items → `knowledge/questions/parked-instruction-surface.md`
- State-bounding items → `knowledge/questions/parked-state-bounding.md`
- Sync-mechanism items → `knowledge/questions/parked-sync-mechanism.md`
- psc-monitor items → `knowledge/questions/parked-psc-monitor.md`
- Premise-review-gate follow-ons → `knowledge/questions/premise-review-gate-follow-ons.md`
- Deterministic-tooling-layer follow-ons → `knowledge/questions/deterministic-tooling-layer-follow-ons.md`
- Knowledge-lint follow-ons → `knowledge/questions/knowledge-lint-follow-ons.md`
- Mechanize-invariants follow-ons → `knowledge/questions/mechanize-invariants-follow-ons.md`
- Delegated-agent-safety follow-ons → `knowledge/questions/delegated-agent-safety-follow-ons.md`
- clarify-audit-tooling propagation follow-on — RESOLVED 2026-07-04: lint-knowledge tombstone mechanized in `scaffold_manifest_removed.txt` (auto-deletes on sync); applied to extrends + psc-monitor (commit 0485daa). Rationale recorded in `knowledge/decisions/INDEX.md` (`lint-knowledge-tombstone`, `clarify-audit-tooling-surface`); detail file pruned once executed.
- run-audit never exercised end-to-end (no wired audit layer in scaffold; monitored, not blocking) → `knowledge/questions/run-audit-untested.md`
- scaffold_lint removed non-openspec-name blind spot (D2 trade-off; revisit if skill set grows or rename recurs) → `knowledge/questions/scaffold-lint-removed-name-blindspot.md`
- Audit-skill frontmatter `compatibility` boilerplate is inaccurate for both run-audit and knowledge-drift-review → `knowledge/questions/audit-skill-metadata-cleanup.md`
- checks-facts-split follow-ons (cosmetic UX/wording, dead-code prune, engine-refactor additions) → `knowledge/questions/checks-facts-split-follow-ons.md`
- Shared-lint-layer follow-ons → `knowledge/questions/shared-lint-layer-follow-ons.md`
- data_lint.py SQLite backend (extrends ask; premise unconfirmed — app DB is Postgres) → `knowledge/questions/data-lint-sqlite-backend.md`
- Security-scanner provisioning gaps (install-tools gitleaks version; GOPATH/bin non-interactive PATH) → `knowledge/questions/scanner-provisioning-gaps.md`
- Outstanding-work-collector follow-ons → `knowledge/questions/outstanding-work-collector-follow-ons.md`
- Handoff-file lint downstream cleanup (extrends ~27 + psc-monitor handoff-named files; coupled to sync_scaffold.py propagation, operator-gated) → `knowledge/questions/continuity-file-downstream-cleanup.md`
- plans/ gather scope: keep recursive, align spec+lint (buried, unexecuted handoff — SMALL, ready to run) → `plans/plans-scope-alignment.md`
- lessons.md prescriptions never wired in (reviewer read-only preamble; git-worktree convention) → `knowledge/questions/lessons-md-implementation-gaps.md`
- research-industry-standards-2026-06 Tier-3 items — no closing APPLY/DROP verdict (low priority) → `knowledge/questions/research-synthesis-tier3-residue.md`
- lesson-check-ratchet follow-ons (outstanding.py `open:` surfacing deferral; OW-1 detector-packaging deferral; OW-2 downstream propagation + adoption seeds) → `knowledge/questions/lesson-check-ratchet-follow-ons.md`
- ratchet-lint-cleanup (knowledge_lint.py/repo_lint.py code-quality follow-on, behavior-preserving, low priority) → `knowledge/questions/ratchet-lint-cleanup.md`
- Correctness-audit-skill follow-ons → `knowledge/questions/correctness-audit-skill-follow-ons.md`
- Composition-audit-cadence follow-ons → `knowledge/questions/composition-audit-cadence-follow-ons.md`
- Instruction-surface PostToolUse hook (OW-14 item c, deferred — Claude-only, needs own carve-out) → `knowledge/questions/instruction-surface-posttooluse-hook.md`
- Instruction-surface content checklist (OW-9, deferred — low-yield) → `knowledge/questions/instruction-surface-content-checklist.md`
- Defect-prevention per-rule toggle v2 (notes.md A3, deferred — observed from downstream noise first) → `knowledge/questions/per-rule-toggle-v2.md`
- repo_lint.py no_fetchall docstring example (notes.md A2, low — wording only) → `knowledge/questions/repo-lint-fetchall-docstring.md`
- Delegation-wrapper-telemetry follow-ons (OW-7, shipped 2026-07-13) → `knowledge/questions/delegation-wrapper-follow-ons.md`
- skill-debloat-gates follow-ons (OW-11, mechanized half shipped 2026-07-14; residual de-bloat + 3 low-priority items) → `knowledge/questions/skill-debloat-gates-follow-ons.md`
- verify-adversarial-fixtures follow-ons (rules.verify registry row; verifier verdict-block adherence, monitored) → `knowledge/questions/verify-adversarial-fixtures-follow-ons.md`
- knowledge-surface-bounding-2 follow-ons (OW-13, shipped 2026-07-14; decisions/INDEX.md year-split, budget/threshold tuning, boot_surface WARN visibility) → `knowledge/questions/knowledge-surface-bounding-2-follow-ons.md`
- delegated-context-caching follow-ons (OW-8, shipped 2026-07-14): B — AGENTS.md-injection strip blocked on opencode env-var coupling, revisit on per-agent instruction-scoping / AGENTS.md split; C-drop lint idea → `knowledge/questions/delegated-context-caching-follow-ons.md`
