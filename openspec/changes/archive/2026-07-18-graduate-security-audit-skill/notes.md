# Notes — graduate-security-audit-skill

## Acceptance criteria

1. `openspec/specs/security-audit/spec.md` exists as an ADDED-Requirements delta with the
   `security-audit` capability (8 requirements, each with WHEN/THEN-SHALL
   scenarios), promoted to `openspec/specs/` at archive.
2. `.claude/skills/security-audit/SKILL.md` exists with convention frontmatter, cites the normative
   spec + the delegation harness, and covers every AP-1 session lesson (empirical-probe-first;
   SAST-is-a-floor; confirm-the-negatives; flash-refuter recipe; supply-chain reachability triage;
   surface-money-races; lockfile-is-a-tool-choice; per-repo custom-detector archetypes).
3. The skill is registered in `scripts/scaffold_manifest.txt` (so `scaffold_lint`
   manifest-completeness passes and it propagates byte-identical downstream).
4. `knowledge/reference/security-scanners.md` no longer claims "two scanners".
5. `OW-17 · security-audit` recorded SHIPPED in OUTSTANDING-WORK.md.
6. Deterministic gates clean: `scaffold_lint`, `knowledge_lint`, `sync_scaffold.py --check-refs`,
   and the scaffold pytest suite for affected scripts.

## Assumptions (recorded defaults — non-blocking, batch-surface at next operator gate)

- **A1. Skill+spec split, not a self-contained skill.** Every scaffold audit skill carries a matching
  `openspec/specs/<name>/spec.md` and the SKILL.md adds operational detail. Followed that pattern
  (matches product-audit / composition-audit / correctness-audit). Alternative (self-contained skill,
  no spec) rejected — it would be the only audit skill without a normative home.
- **A2. Dossier model (lane-split, resumable, liveness), not single-session.** The AP-1 run was
  multi-session by design (audit-plan Q8: "splitting is a correctness requirement"). Modeled
  security-audit on correctness-audit's resumable-dossier + liveness discipline rather than
  product-audit's single-session shape, because a full security audit spans lanes/sessions and the
  AP-1 concern was exactly silent-wave-drop.
- **A3. No mandatory per-session lessons log in the standing skill.** The `session-lessons.md`
  discipline was a one-time *bootstrap* to feed THIS graduation (graduate-after-first-run). The
  standing skill captures the METHOD the lessons taught, not the obligation to write a lessons file.
- **A4. Ships no per-repo detectors.** The route-authz snapshot / auth-coverage gate / custom Semgrep
  rules are repo-shaped; the skill recommends the *archetypes* only. This mirrors the S0 lesson that
  those detectors were psc-specific implementations of reusable patterns.
- **A5. Scanner floor already wired.** bandit/semgrep landed in `checks.py` via
  `2026-07-18-graduate-sast-scanners`; this change touches no tooling code — only the skill/spec/docs.

## Apply plan

Orchestrator-applied (not delegated). The deliverables are judgment-heavy graduation prose whose
quality depends on holding the AP-1 run context; a fresh delegated executor would have to re-read the
entire AP-1 dossier to match. All prose, no code paths altered → no apply/verify code-behavior risk.

## VERIFY outcome

See `review-log.md`. Deterministic gates + orchestrator self-review; independent delegated review
best-effort (recorded there).

## Downstream propagation — DEFERRED + operator-gated

Per AGENTS.md phase-auto-advance, **downstream propagation is an operator-named gate** that halts
auto-advance even under an autonomy grant. This change is archived + committed to scaffold `main`
locally (NO push). Propagation to psc-monitor + any other downstream repo (`sync_scaffold.py <repo>`
→ review → commit) and pushing either repo are handed to the operator. The new skill + spec do not
reach any downstream repo until that step runs.
