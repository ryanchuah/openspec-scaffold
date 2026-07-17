# Open Questions

## Active

- `knowledge-lint-gitignored-citation-exempt` is verified and landed (`7f23eda`) but still sits
  unarchived at `openspec/changes/knowledge-lint-gitignored-citation-exempt/` — needs only an
  operator go-ahead to archive-move. Surfaced during `reconcile-parked-backlog` (2026-07-17).

## Parked

- Commit-test-gate bypassable — `if: Bash(git commit*)` matcher is prefix-anchored (compound/`-C`/env-prefixed/bang commits skip it silently); also Claude-only (non-Claude agents never run it). Consider a git-native `core.hooksPath` pre-commit hook. Evidence: psc-monitor `0e5a823`. → `knowledge/questions/commit-gate-bypass.md`
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
- psc-monitor items → `knowledge/questions/parked-psc-monitor.md`
- Premise-review-gate follow-ons → `knowledge/questions/premise-review-gate-follow-ons.md`
- Deterministic-tooling-layer follow-ons → `knowledge/questions/deterministic-tooling-layer-follow-ons.md`
- Knowledge-lint follow-ons → `knowledge/questions/knowledge-lint-follow-ons.md`
- Mechanize-invariants follow-ons → `knowledge/questions/mechanize-invariants-follow-ons.md`
- Delegated-agent-safety follow-ons → `knowledge/questions/delegated-agent-safety-follow-ons.md`
- checks-facts-split follow-ons (cosmetic UX/wording, dead-code prune, engine-refactor additions) → `knowledge/questions/checks-facts-split-follow-ons.md`
- Shared-lint-layer follow-ons → `knowledge/questions/shared-lint-layer-follow-ons.md`
- Security-scanner provisioning gaps (install-tools gitleaks version; GOPATH/bin non-interactive PATH) → `knowledge/questions/scanner-provisioning-gaps.md`
- Outstanding-work-collector follow-ons → `knowledge/questions/outstanding-work-collector-follow-ons.md`
- propagate-scaffold follow-ons (F5 wrapper stale-output hardening, F3 isort-collision guard, F1 sync-summary output, status_lint Step-5 gap) → `knowledge/questions/propagate-scaffold-follow-ons.md`
- lessons.md prescriptions never wired in (reviewer read-only preamble; git-worktree convention) → `knowledge/questions/lessons-md-implementation-gaps.md`
- research-industry-standards-2026-06 Tier-3 items — no closing APPLY/DROP verdict (low priority) → `knowledge/questions/research-synthesis-tier3-residue.md`
- lesson-check-ratchet follow-ons (outstanding.py `open:` surfacing deferral; OW-1 detector-packaging deferral; OW-2 downstream propagation + adoption seeds) → `knowledge/questions/lesson-check-ratchet-follow-ons.md`
- ratchet-lint-cleanup (knowledge_lint.py/repo_lint.py code-quality follow-on, behavior-preserving, low priority) → `knowledge/questions/ratchet-lint-cleanup.md`
- Correctness-audit-skill follow-ons → `knowledge/questions/correctness-audit-skill-follow-ons.md`
- Composition-audit-cadence follow-ons → `knowledge/questions/composition-audit-cadence-follow-ons.md`
- Instruction-surface PostToolUse hook (OW-14 item c, deferred — Claude-only, needs own carve-out) → `knowledge/questions/instruction-surface-posttooluse-hook.md`
- Instruction-surface content checklist (OW-9, deferred — low-yield) → `knowledge/questions/instruction-surface-content-checklist.md`
- Defect-prevention per-rule toggle v2 (notes.md A3, deferred — observed from downstream noise first) → `knowledge/questions/per-rule-toggle-v2.md`
- Delegation-wrapper-telemetry follow-ons (OW-7, shipped 2026-07-13) → `knowledge/questions/delegation-wrapper-follow-ons.md`
- skill-debloat-gates follow-ons (OW-11, mechanized half shipped 2026-07-14; residual RESOLVED 2026-07-14 by skill-debloat-residual; 2 unrelated low-priority items remain) → `knowledge/questions/skill-debloat-gates-follow-ons.md`
- verify-adversarial-fixtures follow-ons (rules.verify registry row; verifier verdict-block adherence, monitored) → `knowledge/questions/verify-adversarial-fixtures-follow-ons.md`
- knowledge-surface-bounding-2 follow-ons (OW-13, shipped 2026-07-14; decisions/INDEX.md year-split, budget/threshold tuning, boot_surface WARN visibility) → `knowledge/questions/knowledge-surface-bounding-2-follow-ons.md`
- delegated-context-caching follow-ons (OW-8, shipped 2026-07-14): B — AGENTS.md-injection strip blocked on opencode env-var coupling, revisit on per-agent instruction-scoping / AGENTS.md split; C-drop lint idea → `knowledge/questions/delegated-context-caching-follow-ons.md`
- correctness-audit-meta-hardening follow-ons (OW-15, shipped 2026-07-14): liveness substring-match false-negative (monitored), Delta-4 ledger should-exist obligation deferred, ledger cell-tolerance decision (monitored), OW-16 is the natural next change → `knowledge/questions/correctness-audit-meta-hardening-follow-ons.md`
- product-audit-skill follow-ons (OW-16, shipped 2026-07-14) → `knowledge/questions/product-audit-skill-follow-ons.md`
- archive-mechanization follow-ons (OW-12, shipped 2026-07-14) → `knowledge/questions/archive-mechanization-follow-ons.md`
- skill-debloat-residual follow-ons (OW-11 residual, shipped 2026-07-14; closes the wave-2 scaffold-hardening backlog) → `knowledge/questions/skill-debloat-residual-follow-ons.md`
- split-outstanding-work-skills follow-ons (shipped 2026-07-16): unarchived-plan.md lingering (operator cleanup) → `knowledge/questions/split-outstanding-work-skills-follow-ons.md`
- Bare (non-backtick) path citations dangle invisibly to `knowledge_lint` (monitored, low priority) → `knowledge/questions/bare-path-citation-blind-spot.md`
- An apply-executor wrote directly to `openspec/specs/`, bypassing archive promotion — task-authoring smell; one instance, no damage (monitored, low priority) → `knowledge/questions/apply-wrote-canonical-spec.md`
- research-exclusion configured-scan-dir leak (same class as the handoff leak `handoff-lint-exempt` fixed; pre-existing, deferred) → `knowledge/questions/research-exclusion-scan-dir-leak.md`
- `opencode_delegate.py` extract_text returns only the last text part, causing intermittent false `marker-missing` escalations (generalizable harness defect, monitored) → `knowledge/questions/opencode-delegate-extract-text-last-part-only.md`
