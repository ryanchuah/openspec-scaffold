# Status

## Current state
Project initialised from openspec-scaffold. Delegated-work governance hardened: the apply-executor now stops and reports on non-convergence instead of looping, the reviewer has a raised budget with incremental output and partial-salvage on timeout, and a Claude `PreToolUse` commit-test-gate deterministically blocks commits when tests are not green. Instruction surface hardened: a tier-confirmation gate prevents non-autonomous agents from self-classifying and executing without operator confirmation, and six stale/hazardous instruction sites were reconciled to shipped behavior. Delegation robustness hardened: all delegated `opencode run` invocations now close stdin to prevent permission-prompt hangs, per-agent permissions contain write-capable executors, the non-convergence canary is rebuilt as a non-gameable impl-module+frozen-test, and the commit-test-gate ships a smoke fixture with documented hook-wiring procedure. Verify hardened: independent multi-model verification passes (platform-specific chains; Claude self→pro→flash, OpenCode self→flash) now run as hard gates after the orchestrator's self-review, layered before the artifact checklist, so the final release-quality gate is never decided by a single model's blind spots. The shared `opencode run` delegation harness (invocation hardening, assert-real-agent-ran, surgical-kill, EXIT-sentinel completion detection, timeout budgets) is now single-sourced in `.claude/skills/_shared/delegation-harness.md`, with the four delegating skills reduced to citations plus per-phase specifics — extraction, not redesign, with all behavior and budgets preserved byte-for-byte. The verify gate is tier-scaled: multi-model passes apply to MEDIUM/COMPLEX only; a simplicity/quality gate and a conditional security gate (for sensitive-surface changes) were added, layered after the verifier passes; the archive-executor bodies were hardened to handle RENAMED spec requirements; and a new `scripts/test_executor_body_agreement.py` guard byte-compares each `.claude`/`.opencode` executor-pair body, failing when the two drift. The `knowledge/questions/INDEX.md` always-loaded surface is now bounded by a horizon split: it holds ONLY active items (blockers, operator-decision items, in-flight backlogs); the deferred/monitored long tail lives in the Parked section of `knowledge/questions/` (with per-item files for individual items). Instruction-surface rule-restatements single-sourced: five rule-families previously duplicated 3–5× across the instruction surface each assigned one canonical home with all other sites reduced to per-context specifics + a citation — extraction, not redesign, with every rule preserved verbatim. The canonical homes and the cite-don't-restate convention live in `knowledge/lessons.md` §2. The
scaffold's own `knowledge/` tree now passes `scripts/knowledge_lint.py` clean under a live-tree
pytest gate (shared-lint-layer), with the `openspec-onboard` teaching-skill removed as a standing
drift risk. A shared lint layer (`ruff.toml` with E,F,I,B + enforced format, `scripts/check.sh` as
the single green gate) is now scaffold-managed.

## Latest change — shared-lint-layer SHIPPED (2026-07-03)

Shipped a shared lint/green layer: a scaffold-managed `ruff.toml` (selects E,F,I,B + enforced format;
E501 ignored) and `scripts/check.sh` as the single definition of green (ruff check + `ruff format
--check` + per-repo `scripts/test-cmd`), with `test-gate.sh` rewired to call `check.sh` so
hook/CI/human share one gate; `knowledge_lint`'s citation matcher hardened plus a
`<!-- lint:planned -->` opt-out marker; doc-lints (`knowledge_lint`/`status_lint`) now gated on the
live tree via pytest; a new root-handoff-file check; the commit-hook matcher tightened to fire only
on real commits; and security-scanner provisioning descoped to a `go install` helper +
`knowledge/reference/security-scanners.md` reference (CI = official actions, per-repo D1/D2).
Verify: self-review + behavioral verify READY, multi-model passes operator-waived, suite green.
Archive: `openspec/changes/archive/2026-07-03-shared-lint-layer/`. Decisions in
`knowledge/decisions/INDEX.md`; forward items parked in `knowledge/questions/`.

## Prior change — checks-facts-split SHIPPED (2026-07-03)

Split the deterministic audit engine into a checks/facts/audit trichotomy: `audit_bundle.py`
renamed to `scripts/checks.py` (findings-capable detectors, preflight-gated, dated `--report` output)
alongside a new `scripts/facts.py` (cache-semantics snapshots — undated, regenerate-on-use, never
fails), sharing one engine/registry via a `family` field. Preflight turns serial tool-discovery into
one informed report: before any check-family tool runs, `--floor`/`--report` compute availability for
every enabled entry and, on any gap, print one self-explaining line per tool (trigger, install-or-disable
guidance, coverage-loss note), record an INFRA-FAIL, run nothing, exit 3; fact-family tools keep today's
graceful per-tool degradation. Config renamed `audit.toml` → `checks.toml`. Inventory gained an
`audit_anchor` (latest audit tag + commits-since) for staleness-cadence signalling; `audit_scope.py`'s
ceremony is unchanged. Verify: self-review passed in full (multi-model passes waived by operator
instruction); suite green. A commit-test-gate hook misfire was discovered live during apply and parked,
not fixed here. Decisions in `knowledge/decisions/INDEX.md`; forward items parked in `knowledge/questions/`.
Archive: `openspec/changes/archive/2026-07-03-checks-facts-split`.

## Prior change — clarify-audit-tooling-surface SHIPPED (2026-07-03)

Renamed the LLM `lint-knowledge` skill to `knowledge-drift-review`, ending near-mirrored-name
confusion with the deterministic `knowledge_lint.py` script. Added a `run-audit` skill as the
deterministic-audit entry point (detects repo interpreter, runs `audit_bundle.py`/`audit_scope.py`,
gracefully handles missing per-repo wiring). Generalized `scaffold_lint.py`'s dangling-skill-ref
detection from a single hardcoded token to an explicit frozenset so both non-openspec skills validate.
Surgical AGENTS.md edits mark the interpreter and `just audit-*` as per-repo/illustrative. Verified:
live probe of the generalized `check_dangling_skill_refs` confirmed correct detection for both skills
and the deliberate D2 trade-off (renamed-name stragglers caught by grep, not the check); in-repo
`grep -rn lint-knowledge` returned only historical lines; suite green, SEAL green, `--check-refs`
green. No code changes to deterministic scripts. Decisions in `knowledge/decisions/INDEX.md`;
forward-looking items parked in `knowledge/questions/`. Archive:
`openspec/changes/archive/2026-07-03-clarify-audit-tooling-surface`.

## Immediate next action
The succession-hardening portfolio is **fully shipped**; the day-to-day-tooling portfolio (A: checks-facts-split, B: sync-deletion-manifest, C: shared-lint-layer) is now **fully shipped** — no proactive build is in flight.

**Downstream propagation — extrends FULLY SYNCED, psc-monitor still frozen.** On 2026-07-04 the operator
authorized propagation to **extrends**, now converged to scaffold HEAD (beacon `a879317`). The full
shared-lint-layer batch — `checks-facts-split` (audit_bundle→checks/facts), `clarify-audit-tooling-surface`
(the lint-knowledge→knowledge-drift-review rename + tombstone), and the C lint layer (`ruff.toml`,
`scripts/check.sh`) — was synced in one pass, and the D1 lint layer was **absorbed**: extrends' own code
brought ruff-clean + format-clean, `knowledge_lint` clean (via a lint:planned marker and relocating 3
transient root handoff files to a handoffs-archive dir). Committed to extrends `main` — **local, unpushed**
(push needs separate authorization). Verified per `knowledge/reference/resync-verification.md`:
`--check`/`--check-refs` converged, `scaffold_lint` structural clean, extrends gate (ruff+format+pytest)
green through its commit hook.

Two scaffold fixes shipped **during** this propagation (see `knowledge/decisions/INDEX.md`): the
lint-knowledge removed-manifest tombstone (9ea6076) and the ruff `target-version=py311` cross-repo
determinism pin (a879317) — the latter fixing a byte-identical-sync break where ruff sorted a
scaffold-managed file differently per repo's inferred Python version.

**Remaining extrends follow-ons** (parked, not blockers): audit-layer wiring (checks.toml, checks/,
task-runner audit-* targets, dev-extras pins, an audit-log seed on first audit); a `knowledge-drift-review`
semantic pass; and operator pruning of the relocated handoffs-archive dir plus the 2 untracked root
handoff files left in place.

**psc-monitor stays explicitly frozen pending operator go-ahead** — do not run `scripts/sync_scaffold.py`
against it until authorized. It owes the entire batch above (now including the target-version pin); its
openspec-onboard + lint-knowledge tombstones are both in the removed-manifest, so the sync now deletes
them automatically. Same re-sync verification applies.

**Scaffold-tooling fix SHIPPED 2026-07-03** — `fix-propagation-tooling-drift` (SMALL, archived at
`openspec/changes/archive/2026-07-03-fix-propagation-tooling-drift/`): found during the extrends
propagation. `sync_scaffold.py` `--check-refs` `_EPHEMERAL_PATHS` was realigned with
`knowledge_lint.EPHEMERAL_PATHS` (adds `knowledge/audit-log.md`, so the scaffold's own `--check-refs`
is green again), and `scaffold_lint.py`'s oneoff exclude glob was broadened `_*_oneoff.py`→`_*_oneoff.*`
(no longer false-positives on `.sh` oneoffs downstream). Both files are authoring-side
(manifest-excluded) — the fix does **not** propagate. Premise AGREE, flash verifier READY.
