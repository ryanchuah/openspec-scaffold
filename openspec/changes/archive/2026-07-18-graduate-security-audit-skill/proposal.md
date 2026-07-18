# Proposal — graduate-security-audit-skill

**Tier:** MEDIUM (new scaffold-owned skill + normative spec + manifest registration).
**Model note:** authored under Opus. Fable **cannot** run or graduate security-audit work — its
guardrails block the cybersecurity-risk domain (operator-confirmed 2026-07-18 on the psc-monitor
run). Keep this graduation and any future security-audit work off Fable.

## Why

The scaffold's audit family has seven skills, **none owning the classic vulnerability classes**
(authn/session, authz/IDOR, injection, crypto/secrets, payment integrity, supply-chain). The only
security surface is the per-change, diff-scoped security pass inside `openspec-verify-change` — never
a whole-repo adversarial audit. A downstream repo can pass every chartered correctness audit and
still ship an account-takeover misconfiguration, because no correctness charter's universe contains
the security surface (each explicitly excludes it as "separate audit; charter §8 boundary honored"),
and that separate audit had no reusable protocol.

psc-monitor ran the first full-depth adversarial security audit (AP-1) as the proving ground, on the
operator's explicit **run-first, graduate-after** sequencing (the same path `product-audit` took to
become OW-16). Every session recorded lessons as it went. This change consumes those lessons and
extracts the reusable spine into a scaffold-owned `security-audit` skill + normative spec, so every
downstream repo inherits the method instead of re-deriving it.

The deterministic half is **already shipped**: the archived `2026-07-18-graduate-sast-scanners`
change wired `bandit` + `semgrep` into `scripts/checks.py` (joining the pre-existing
`gitleaks`/`osv-scanner`), and `knowledge/reference/security-scanners.md` documents provisioning.
What is missing is the **LLM ceremony** that stands on that floor — the charter → scanner-floor →
per-lane adversarial passes → refuter verification → machine verdict → ratchet close-out contract.

## What Changes

- **New normative spec** `openspec/specs/security-audit/spec.md` (the `security-audit` capability,
  8 requirements) — the single normative home for the ceremony sequence, disposition set, verdict
  values, and liveness/deferral rules. Distilled from the AP-1 method (`plans/security-audit-ap1/audit-plan.md`
  Q1–Q8) and the per-session lessons (`session-lessons.md`).
- **New operator-invoked, pull-only skill** `.claude/skills/security-audit/SKILL.md` — adds
  operational detail on top of the spec: lane menu, the S0 scanner-floor invocation, the
  adversarial-persona + empirical-probe-first + confirm-the-negative discipline, the delegated
  flash-refuter recipe, supply-chain reachability triage, and the recommended per-repo custom
  detectors (route-authz snapshot / auth-coverage gate / SQL-string + error-leak + placeholder-config
  rule archetypes). Structural sibling of `composition-audit` (deterministic sweep → bounded LLM
  judgment → 3-state verdict → ratchet) and `correctness-audit` (lane-split, resumable, liveness).
- **Manifest registration** — `.claude/skills/security-audit/SKILL.md` added to
  `scripts/scaffold_manifest.txt` under `# Skills (.claude)` so it propagates byte-identical to every
  downstream repo (required for `scaffold_lint` manifest-completeness).
- **Doc-drift fix** — `knowledge/reference/security-scanners.md` header still says "two scanners"
  after the SAST change appended two more; corrected to reflect all four.
- **Backlog registration** — a new `OW-17 · security-audit` item recorded in
  `knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md` (the backlog was empty at
  OW-16); marked SHIPPED by this change.

No existing tooling behavior changes; no existing scanner wiring is touched. This is additive — a new
skill file, a new spec, one manifest line, and two knowledge-doc edits.

## Capabilities

### New Capabilities

- `security-audit` — a scaffold-owned, operator-invoked, pull-only, lane-split adversarial
  security-audit ceremony: charter (lane selection + adversarial persona + secrets-exclusion) →
  deterministic scanner floor (front-loaded, SAST-is-a-floor-not-a-finder) → per-lane adversarial
  passes (empirical-probe-first, confirm-the-negatives enumerated) → independent refuter verification
  (delegated flash, money-races surfaced not auto-fixed) → cross-lane completeness critic →
  `SECURITY: CLEAN|FINDINGS-ROUTED|ESCALATE` verdict → finding-closure-ratchet close-out, with
  liveness for multi-session runs and explicit deploy-time deferral for edge lanes.

### Modified Capabilities

None. The `defect-prevention-detectors` / `repo-invariant-checks` scanner wiring is unchanged
(shipped separately); this change only adds the LLM ceremony that consumes it.

## Impact

- **Downstream:** every repo that syncs the scaffold gains the `security-audit` skill (an occasion +
  a method; it ships no per-repo detectors and gates nothing). Propagation to downstream repos is an
  operator-gated step, run from the golden source after this change archives.
- **Tooling:** none touched. The skill is text; it invokes already-shipped `checks.py` security
  checks and the shared delegation harness.
- **Risk:** low — additive skill + spec; no code path altered. The blast radius is that the skill's
  *recommendations* reach every downstream repo, which is the intent of a graduation.
