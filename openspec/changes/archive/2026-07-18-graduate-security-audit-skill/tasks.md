# Tasks — graduate-security-audit-skill

Orchestrator-applied (judgment-heavy graduation authorship; not delegated — the author holds the AP-1
run context). Check each off as it lands. Tests-green + deterministic lints clean before commit.

## 1. Normative spec (ORCHESTRATOR-APPLIED)

- [x] 1.1 Author `openspec/changes/.../specs/security-audit/spec.md` as an `## ADDED Requirements`
  delta: the `security-audit` capability, ~8 requirements each with WHEN/THEN-SHALL
  scenarios, distilled from `plans/security-audit-ap1/` (psc-monitor) audit-plan Q1–Q8 + session
  lessons. Requirements: (R1) scaffold-owned/operator-invoked/pull-only/audit-then-fix; (R2)
  charter selects+prunes lanes, adversarial persona, secrets-never-to-external-model; (R3)
  deterministic scanner floor front-loaded, SAST-is-a-floor-not-a-finder + reachability triage +
  coverage caveats; (R4) per-lane adversarial pass, empirical-probe-first, confirm-the-negatives
  enumerated, orchestrator-only severity finalization; (R5) findings adversarially verified
  (delegated refuter), money/abuse races surfaced not auto-fixed; (R6) cross-lane completeness
  critic; (R7) machine verdict `SECURITY: CLEAN|FINDINGS-ROUTED|ESCALATE` + ratchet close-out; (R8)
  multi-session liveness + deploy-time edge deferral.

## 2. The skill (ORCHESTRATOR-APPLIED)

- [x] 2.1 Author `.claude/skills/security-audit/SKILL.md`: convention frontmatter (`name`,
  `description`, `license: MIT`, `metadata`); pull-only / audit-then-fix stance; `<py>` interpreter
  convention; normative-spec citation; hardened-delegation-harness citation; wiring detection; the
  dossier layout + untracked `output/security/`; the recommended lane menu with explicit-prune rule;
  S0 scanner-floor invocation + provisioning note; per-lane adversarial-persona + empirical-probe +
  confirm-the-negative discipline; the flash-refuter delegation recipe; supply-chain
  reachability-triage; the SAST-is-a-floor budgeting rule; the lockfile-is-a-tool-choice rule;
  recommended per-repo custom-detector archetypes; cross-lane completeness critic; verdict +
  ratchet close-out; liveness + deploy-time deferral; `## Guardrails`.

## 3. Registration & doc-drift (ORCHESTRATOR-APPLIED)

- [x] 3.1 Add `.claude/skills/security-audit/SKILL.md` to `scripts/scaffold_manifest.txt` under
  `# Skills (.claude)`, adjacent to the other non-openspec skills.
- [x] 3.2 Fix the stale "two scanners" framing in `knowledge/reference/security-scanners.md` (header
  + intro) now that four scanners are documented (gitleaks/osv-scanner + semgrep/bandit).
- [x] 3.3 Register `OW-17 · security-audit` in
  `knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md` (backlog was empty at
  OW-16), marked SHIPPED by this change; update the "backlog is EMPTY" disposition line.

## 4. Verify (ORCHESTRATOR)

- [x] 4.1 Deterministic gates clean: `python3 scripts/scaffold_lint.py`, `python3
  scripts/knowledge_lint.py`, `python3 scripts/sync_scaffold.py --check-refs <downstream>`
  (reference integrity), and the scaffold pytest suite for affected scripts.
- [x] 4.2 Orchestrator self-review of spec + skill (premise + quality); record in `review-log.md`.
  Independent delegated review attempted (best-effort); outcome recorded.

## 5. Archive (ORCHESTRATOR)

- [x] 5.1 Promote the delta spec to `openspec/specs/security-audit/spec.md`; move change dir to
  `openspec/changes/archive/2026-07-18-graduate-security-audit-skill/`; reconcile scaffold
  `knowledge/STATUS.md` + `knowledge/decisions/INDEX.md` + roadmap.
- [x] 5.2 Commit to scaffold `main` in small reviewed checkpoints. NO push (unauthorized).

## Out of scope (operator-gated — HALT, do not auto-run)

- **Downstream propagation** (`sync_scaffold.py <repo>` into psc-monitor + any other downstream +
  review + commit) — an operator-named gate per AGENTS.md phase-auto-advance. Handed off.
- **Push to remote** (either repo) — requires explicit operator authorization.
- **Live scanner run** — `semgrep`/`bandit` are not installed on this machine; provisioning
  (`bash scripts/install-tools.sh`) is an environment step, not part of authoring the skill.
- **Per-repo custom detectors** (route-authz snapshot, auth-coverage gate, custom Semgrep rules) —
  repo-shaped; the skill recommends the archetypes but ships no per-repo detector code.
