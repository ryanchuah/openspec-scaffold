# Proposal — lesson-check-ratchet

## Why

Defect classes discovered in repos governed by this scaffold do not durably close: the
instance gets fixed, the class gets recorded as prose (`knowledge/lessons.md`, notes,
audit dossiers), and prose is write-only memory — identical bug shapes re-shipped in both
downstream repos after being found, named, and written down (psc-monitor: B5→CA-W2-05,
F16→CA-W2-02; extrends: W3-E3→W4-M2a one wave apart, the fail-soft-invisible shape 3×,
wrong-boundary mocking rediscovered by two independent audits — see
`knowledge/research/scaffold-gap-analysis-2026-07/SYNTHESIS.md` GAP 1). The scaffold pays
for multi-model review of every diff but provides no mechanism that converts a found bug
class into a permanent deterministic guard, so every future audit pays to re-find old
classes instead of only new ones.

## What Changes

- **New closure rule (the ratchet), enforced by lint, not memory:** a generalizable
  finding is not closed until it has exactly one recorded disposition — an enforcing
  deterministic **check**, a **frozen regression test** linkage, or an explicit **waiver**
  (for domain-judgment-only classes) — with a stated preference ordering
  (check > frozen test > waiver). "Frozen" means the ledger records a permanent pointer to
  an existing pytest test and the lint verifies that pointer stays live (the pointed-at
  test file/node still exists) — it does NOT mean the test becomes immutable; how deep the
  linkage verification goes beyond existence is a design.md decision. Waivers carry a
  reason plus a re-review trigger so they cannot silently become the new write-only
  memory. A **grandfathered** disposition marks legacy pre-ratchet lessons so the lint can
  distinguish "reviewed and deferred" from "never triaged". Rule text lands in AGENTS.md;
  enforcement lands in `knowledge_lint.py`.
- **New tracked ratchet ledger at `knowledge/ratchet-log.md`** (lint-first registry-line
  discipline, same shape class as `knowledge/audit-log.md`): one line per finding-class
  mapping class → disposition → enforcing artifact. Ledger *format* is scaffold-defined;
  ledger *content* is per-repo. The scaffold's own tree adopts it (bootstrap entries
  included) so the mechanism is exercised where it is built.
- **New per-repo invariant framework** generalizing the proven `data-lint` conventions
  sideways to code/repo-shape invariants: a flat per-repo directory slot where one file =
  one invariant, zero findings = pass, read-only, timeout-bounded, executed by a new
  stdlib-only delegating runner registered in `scripts/checks.py` (the `data-lint`
  registry pattern) and auto-enabled when the directory is non-empty. External scanners
  (semgrep/ast-grep and similar) remain available per-repo via the existing
  `[checks.custom.*]` escape hatch — they are deliberately NOT a scaffold dependency
  (scaffold scripts stay stdlib-only).
- **New `knowledge_lint.py` checks:** ratchet-ledger registry-format check (guarded on
  ledger existence, like the audit-log check); missing/invalid disposition; **dangling
  enforcement pointer** — a disposition citing a check file or test that does not exist on
  disk is a lint finding (the `budget-agreement` artifact-vs-artifact cross-check shape);
  stale waiver (re-review trigger passed).
- **Close-out routing:** the two existing finding close-out points each gain one bounded
  ratchet-triage step — the **archive** skill (bugs found+fixed during a change) and the
  **run-audit** skill's triage step (deterministic findings judged real). The step is a
  ≤3-question classification producing one ledger line plus the enforcing artifact or
  waiver. Future audit skills (OW-5 correctness-audit, OW-6 composition-audit) route into
  this same interface; they are not built here.
- **Ergonomics constraints are non-negotiable design inputs, not aspirations:** triage
  classification ≤3 questions; registering a new invariant = 1 dropped file; waiver always
  available but explicit and lintable. If a design choice violates one of these, the
  choice is wrong, not the constraint — a ratchet that costs more than minutes per finding
  gets skipped under pressure and becomes net-negative bureaucracy.
- **Division of responsibility unchanged (D7):** the scaffold ships the framework, rule,
  lint, and skill steps; each downstream repo's actual invariants/config land as follow-on
  SMALL changes in that repo. Nothing here auto-wires downstream checks, and nothing here
  auto-fixes anything (D3: check-only).

No breaking changes: all additions are additive; the new lint checks are guarded on ledger
existence (the `_check_audit_log` skip-silently-when-absent precedent in
`knowledge_lint.py`), so repos that have not adopted the ledger yet lint clean.

## Out of Scope

- OW-1's generic test-quality detectors and OW-4's generic data-scale detector (separate
  upstream changes; natural first tenants of these conventions, not part of this change).
- OW-5 `correctness-audit` and OW-6 composition-audit skills (they consume this change's
  routing interface later).
- Retroactive remediation of the extrends/psc-monitor audit backlogs (downstream work).
- Back-filling ledger entries for every existing `lessons.md` entry in any repo — legacy
  entries are grandfathered; a one-time triage sweep is parked as a follow-on.
- Auto-wiring downstream repos' invariants or config (D7: downstream SMALL changes).

## Capabilities

### New Capabilities
- `finding-closure-ratchet`: the closure contract — dispositions, ledger format, lint
  enforcement, and the archive/audit close-out routing that feeds it.
- `repo-invariant-checks`: the per-repo domain-invariant framework — the flat-dir
  code/repo-shape invariant slot, its stdlib runner, its `checks.py` registration and
  conventions (D4 scale: ~5–15 intentional invariants per repo).

### Modified Capabilities
<!-- none — precedent (outstanding-work-view): a domain capability's lint checks live in
     its own spec; knowledge-lint's existing requirements are untouched and the new checks
     are additive implementation registered under finding-closure-ratchet. -->

## Impact

- **Scripts (scaffold-managed, propagated):** `scripts/checks.py` (one registry entry +
  auto-detect trigger), one new stdlib-only runner script, `scripts/knowledge_lint.py`
  (new guarded checks), plus their pytest coverage (fixture-based, live-tree gate).
- **Skills (scaffold-managed, propagated):** `.claude/skills/openspec-archive-change/SKILL.md`
  and `.claude/skills/run-audit/SKILL.md` gain the bounded triage step.
- **Instruction surface:** `AGENTS.md` (closure-rule text, canonical home),
  `knowledge/README.md` (taxonomy row for the ledger).
- **Manifest:** `scripts/scaffold_manifest.txt` additions for the new runner; ledger
  content and per-repo invariant dirs are per-repo (NOT manifest-synced), mirroring
  `audit-log.md` / `checks.toml` precedent.
- **Downstream repos:** receive the framework on next authorized sync; adopting it
  (writing their first invariants, triaging their audit backlogs into ledgers) is
  follow-on downstream work. Adoption risk is real and accepted: the framework's value
  depends on per-repo execution; the mitigating lever is that OW-5/OW-6 route findings
  into it by construction.
- **Dependencies:** none added. Scaffold scripts remain Python-3.13-stdlib-only.
