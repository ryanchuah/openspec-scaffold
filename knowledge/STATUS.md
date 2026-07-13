# Status

## Current state
Project initialised from openspec-scaffold. Delegated-work governance hardened: the apply-executor now stops and reports on non-convergence instead of looping, the reviewer has a raised budget with incremental output and partial-salvage on timeout, and a Claude `PreToolUse` commit-test-gate deterministically blocks commits when tests are not green. Instruction surface hardened: a tier-confirmation gate prevents non-autonomous agents from self-classifying and executing without operator confirmation, and six stale/hazardous instruction sites were reconciled to shipped behavior. Delegation robustness hardened: all delegated `opencode run` invocations now close stdin to prevent permission-prompt hangs, per-agent permissions contain write-capable executors, the non-convergence canary is rebuilt as a non-gameable impl-module+frozen-test, and the commit-test-gate ships a smoke fixture with documented hook-wiring procedure. Verify hardened: independent multi-model verification passes (tier-keyed, platform-uniform chain — MEDIUM self→pro behavioral, COMPLEX self→pro→flash lens) now run as hard gates after the orchestrator's self-review, layered before the artifact checklist, so the final release-quality gate is never decided by a single model's blind spots. The shared `opencode run` delegation harness (invocation hardening, assert-real-agent-ran, surgical-kill, EXIT-sentinel completion detection, timeout budgets) is now single-sourced in `.claude/skills/_shared/delegation-harness.md`, with the four delegating skills reduced to citations plus per-phase specifics — extraction, not redesign, with all behavior and budgets preserved byte-for-byte. The verify gate is tier-scaled: multi-model passes apply to MEDIUM/COMPLEX only; a simplicity/quality gate and a conditional security gate (for sensitive-surface changes) were added, layered after the verifier passes; the archive-executor bodies were hardened to handle RENAMED spec requirements; and a new `scripts/test_executor_body_agreement.py` guard byte-compares each `.claude`/`.opencode` executor-pair body, failing when the two drift. The `knowledge/questions/INDEX.md` always-loaded surface is now bounded by a horizon split: it holds ONLY active items (blockers, operator-decision items, in-flight backlogs); the deferred/monitored long tail lives in the Parked section of `knowledge/questions/` (with per-item files for individual items). Instruction-surface rule-restatements single-sourced: five rule-families previously duplicated 3–5× across the instruction surface each assigned one canonical home with all other sites reduced to per-context specifics + a citation — extraction, not redesign, with every rule preserved verbatim. The canonical homes and the cite-don't-restate convention live in `knowledge/lessons.md` §2. The
scaffold's own `knowledge/` tree now passes `scripts/knowledge_lint.py` clean under a live-tree
pytest gate (shared-lint-layer), with the `openspec-onboard` teaching-skill removed as a standing
drift risk. A shared lint layer (`ruff.toml` with E,F,I,B + enforced format, `scripts/check.sh` as
the single green gate) is now scaffold-managed.

## Latest change — apply-throughput-resume SHIPPED (2026-07-14)

Shipped green-path targeted-test cadence in both apply-executor bodies (byte-synced): per-task
scope-narrowed check using the same test tool, then the full documented suite once before
completion — replacing the old unconditional full-suite-per-task. Added a four-point
fresh-executor resume contract to the apply skill's failure ladder (skip `[x]` tasks, resume at
first `[ ]`, reconcile the in-flight task, carry distilled state). Promoted a MODIFIED
apply-convergence-guard delta: scope-narrowing the same tool is permitted; the full suite gates
before completion; two new scenarios. Verify: self-review PASS → pro behavioral READY; check.sh
green. Decisions: `knowledge/decisions/INDEX.md`; follow-ons: `knowledge/questions/INDEX.md`.
Archive: `openspec/changes/archive/2026-07-14-apply-throughput-resume/`.

## Prior change — delegation-wrapper-telemetry SHIPPED (2026-07-13)

Shipped the ingest wrapper (`scripts/opencode_delegate.py`) that mechanizes post-processing across 8 delegation sites — fallback detection, text extraction, status classification, verdict capture, and marker assertion — without altering the literal `timeout … opencode run … < /dev/null` invocation at any site, so the budget-agreement and delegation-safety guards remain fully intact. Each post-processed run appends one telemetry line to an untracked ledger (`output/delegation-log.jsonl`) with a pinned minimum schema, feeding the two scheduled evidence-gated decisions (premise-gate downgrade at ~50 reviews, MEDIUM pro-pass downgrade at ~20 verifies). Promoted the new `delegation-wrapper` capability. Verify: self-review PASS → pro behavioral READY; wrapper dogfooded on the verifier run. Decisions: `knowledge/decisions/INDEX.md`; follow-ons: `knowledge/questions/INDEX.md`. Archive: `openspec/changes/archive/2026-07-13-delegation-wrapper-telemetry/`.

## Prior change — defect-prevention-detectors SHIPPED (2026-07-13)

Shipped two universal in-process defect-prevention detectors in `scripts/checks.py` (OW-1 + OW-4,
MEDIUM): `test-quality` — six AST-based rules flagging forced-green assertions, empty test bodies,
self-mocks, unfrozen clocks, and discarded return flags in test files; `data-scale` —
unbounded `.fetchall()` detection on non-test source. Both are enabled-by-default, FP-safe (advisory
surface, operator-triaged, no CI-gate impact). Verify lens/rule wiring: the existing
verify-multimodel-gate lens forward-compat clause is now concrete (detectors ship, lens prompts
delegate to `checks.py --check`), and a new data-path recording rule enforces the "Mind data scale"
rule at verify. Verify: full MEDIUM gate green — orchestrator independent exercise PASS (built own
fixtures, confirmed real detection not forced-green), pro behavioral READY, 2 🟡 fixed inline, zero
Sonnet fallback. One real defect (hidden-dir scan in `_iter_py_files`) found and re-delegated.
Decisions: `knowledge/decisions/INDEX.md`; follow-ons: `knowledge/questions/INDEX.md`. Archive:
`openspec/changes/archive/2026-07-13-defect-prevention-detectors/`.

## Immediate next action
`apply-throughput-resume` (OW-10) is now **SHIPPED**, joining `delegation-wrapper-telemetry` (OW-7),
`defect-prevention-detectors` (OW-1 + OW-4), and `instruction-surface-coherence` (OW-9 + OW-14, all
SHIPPED earlier this session). The frozen OW-2→3→5→6 batch and the paired OW-9/14 sweep are both
complete. There is no proactive build in flight. The wave-2 remainder — OW-11 → OW-8 → OW-13 → OW-12
(in-progress order) — plus the late additions OW-15 and OW-16 are still open; work is in progress this
session. Single source:
`knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md`. The Fable-tier design
backlog is closed (2026-07-11 workflow audit:
`knowledge/research/workflow-audit-2026-07-11/AUDIT.md`); everything remaining is Opus-tier.
Earlier portfolios (succession-hardening; day-to-day tooling A/B/C) are fully shipped.

**correctness-audit-skill SHIPPED (2026-07-13)** — scaffold-only; downstream propagation of the
new skill/lint files is **operator-gated and deferred**, not synced without fresh authorization
(arrives INERT on the next sync: the marker-gated dossier lint no-ops until a repo authors a
marked dossier). `composition-audit-cadence` (OW-6) has since shipped 2026-07-13, completing the
frozen batch; see the wave-2 backlog in "Immediate next action" above.

**verify-stack-redirect SHIPPED (2026-07-13)** — scaffold-only; downstream propagation of the
edited manifest-tracked skill/agent/AGENTS.md files is **operator-gated and deferred**, not
synced without fresh authorization. Root `README.md` (not scaffold-managed) was also reconciled
directly during verify and needs no downstream sweep. OW-5 and OW-6 have since both shipped,
completing the frozen batch.

**lesson-check-ratchet SHIPPED (2026-07-13)** — downstream propagation of its scaffold changes
(`repo_lint.py`, `knowledge_lint.py` ratchet checks, the two skill triage steps) is **operator-gated
and deferred**: the framework arrives INERT on the next authorized sync (no `checks/*.py`, no
per-repo ledger → auto-disabled, lint-guarded), and per-repo adoption is separate downstream SMALL
work. See `knowledge/questions/INDEX.md` Parked.

**outstanding-and-continuity-hardening SHIPPED (2026-07-13)** — scaffold-only; the frozen
OW-3→5→6 batch (now complete) was the stated next work at the time, unchanged by this change. Downstream
propagation of the widened handoff-file lint is **deliberately DEFERRED and operator-gated**: it
is coupled to a downstream cleanup (extrends' ~27 and psc-monitor's handoff-named files must be
renamed/archived first), since syncing the widened lint before that cleanup would redden both
repos' pytest gates. See `knowledge/questions/continuity-file-downstream-cleanup.md`.

**lifecycle-skill-hardening SHIPPED (2026-07-13)** — scaffold-only (SMALL): fixed three defects
found live during the OW-2 session in the propose/apply/archive lifecycle skills — propose now
gates on `openspec validate --strict` before freeze, apply's non-convergence check now greps the
extracted completion report instead of the raw jsonl (which false-positived on the skill's own
doc heading), and archive's pre-commit lint step now also runs `knowledge_lint` and repoints any
moved-dir citation. Archive: `openspec/changes/archive/2026-07-13-lifecycle-skill-hardening/`.
OW-3, OW-5, and OW-6 have since all shipped, completing the frozen batch.

**Downstream propagation — extrends AND psc-monitor FULLY SYNCED.** On 2026-07-04 the operator
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

**extrends audit layer now WIRED** (extrends b7280f6/2887f59: checks.toml, deptry, justfile audit-*
targets; gitleaks enabled via the pinned *release* binary; `knowledge-drift-review` pass ran, 2000e40).
Still-open extrends follow-ons (parked, not blockers): **data-lint stays off** — repo DB is SQLite, blocked
on the upstream data_lint SQLite backend (`knowledge/questions/data-lint-sqlite-backend.md`); and operator
pruning of the relocated handoffs-archive dir plus the 2 untracked root handoff files.

**psc-monitor PROPAGATED 2026-07-04** (operator go-ahead given) — converged to scaffold HEAD (beacon
`511843b`), committed to psc-monitor `main` as `0485daa` — **local, unpushed** (push needs separate
authorization). The whole batch synced in one pass (openspec-onboard tombstone auto-deleted from the
removed-manifest) and was **absorbed to green**: psc-monitor is a **FastAPI** app, so the shared `ruff.toml`
gained a `flake8-bugbear extend-immutable-calls` carve-out (`fastapi.Depends/Query/…`) upstream first —
committed `511843b`, decisions `ruff-fastapi-immutable-calls`, re-synced — dropping 30 B008 false-positives;
then psc's own code was ruff-autofixed + hand-fixed (21: B904/F841/B017/E402, plus a test that re-exported
the `settings` singleton through `run_pipeline`) + `ruff format`; 69 `knowledge_lint` citation findings in
psc's own knowledge tree were resolved (repoint / de-path retired historical plans / colon-fix live refs);
and psc's per-repo `## On-demand references` AGENTS.md appendix was relocated out of the banned post-`After
reading` tail into the Project-context zone. Verified per `knowledge/reference/resync-verification.md`:
`--check` converged, `scaffold_lint` 4 structural clean, `knowledge_lint`/`status_lint` clean, psc gate
(`check.sh`: ruff+format+tests) green. **psc-monitor audit layer now WIRED** (psc b33d05a/f5ba85f:
checks.toml, `checks/` with 4 Postgres data-lint invariants live, Makefile audit-* targets, gitleaks
enabled; `knowledge-drift-review` pass ran, ebe06fe). Still idle by choice (parked, not blockers):
osv-scanner (no root lockfile) and deptry (no pip dev-extra).

**Scaffold-tooling fix SHIPPED 2026-07-03** — `fix-propagation-tooling-drift` (SMALL, archived at
`openspec/changes/archive/2026-07-03-fix-propagation-tooling-drift/`): found during the extrends
propagation. `sync_scaffold.py` `--check-refs` `_EPHEMERAL_PATHS` was realigned with
`knowledge_lint.EPHEMERAL_PATHS` (adds `knowledge/audit-log.md`, so the scaffold's own `--check-refs`
is green again), and `scaffold_lint.py`'s oneoff exclude glob was broadened `_*_oneoff.py`→`_*_oneoff.*`
(no longer false-positives on `.sh` oneoffs downstream). Both files are authoring-side
(manifest-excluded) — the fix does **not** propagate. Premise AGREE, flash verifier READY.

**New scaffold gaps reported (parked, not scheduled)** — surfaced while extrends/psc enabled their
scanners; see `knowledge/questions/scanner-provisioning-gaps.md`: (1) `install-tools.sh` installs gitleaks
via `go install`, which embeds no version → fails `checks.py`'s version pin (both repos worked around it
with the official release binary; re-running install-tools re-breaks it); (2) `$(go env GOPATH)/bin` is
not on non-interactive PATH — root cause is the `~/.bashrc` interactivity guard sitting before the go PATH
export (re-sourcing does not help), so cron/CI/`opencode run` hit `checks.py` preflight exit 3 unless PATH
is set explicitly. A deterministic-audit runbook now lives at `knowledge/reference/audit-runbook.md`.
