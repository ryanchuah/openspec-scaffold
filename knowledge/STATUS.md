# Status

## Current state
Project initialised from openspec-scaffold. Delegated-work governance hardened: the apply-executor now stops and reports on non-convergence instead of looping, the reviewer has a raised budget with incremental output and partial-salvage on timeout, and a Claude `PreToolUse` commit-test-gate deterministically blocks commits when tests are not green. Instruction surface hardened: a tier-confirmation gate prevents non-autonomous agents from self-classifying and executing without operator confirmation, and six stale/hazardous instruction sites were reconciled to shipped behavior. Delegation robustness hardened: all delegated `opencode run` invocations now close stdin to prevent permission-prompt hangs, per-agent permissions contain write-capable executors, the non-convergence canary is rebuilt as a non-gameable impl-module+frozen-test, and the commit-test-gate ships a smoke fixture with documented hook-wiring procedure. Verify hardened: independent multi-model verification passes (tier-keyed, platform-uniform chain — MEDIUM self→pro behavioral, COMPLEX self→pro→flash lens) now run as hard gates after the orchestrator's self-review, layered before the artifact checklist, so the final release-quality gate is never decided by a single model's blind spots. The shared `opencode run` delegation harness (invocation hardening, assert-real-agent-ran, surgical-kill, EXIT-sentinel completion detection, timeout budgets) is now single-sourced in `.claude/skills/_shared/delegation-harness.md`, with the four delegating skills reduced to citations plus per-phase specifics — extraction, not redesign, with all behavior and budgets preserved byte-for-byte. The verify gate is tier-scaled: multi-model passes apply to MEDIUM/COMPLEX only; a simplicity/quality gate and a conditional security gate (for sensitive-surface changes) were added, layered after the verifier passes; the archive-executor bodies were hardened to handle RENAMED spec requirements; and a new `scripts/test_executor_body_agreement.py` guard byte-compares each `.claude`/`.opencode` executor-pair body, failing when the two drift. The `knowledge/questions/INDEX.md` always-loaded surface is now bounded by a horizon split: it holds ONLY active items (blockers, operator-decision items, in-flight backlogs); the deferred/monitored long tail lives in the Parked section of `knowledge/questions/` (with per-item files for individual items). Instruction-surface rule-restatements single-sourced: five rule-families previously duplicated 3–5× across the instruction surface each assigned one canonical home with all other sites reduced to per-context specifics + a citation — extraction, not redesign, with every rule preserved verbatim. The canonical homes and the cite-don't-restate convention live in `knowledge/lessons.md` §2. The
scaffold's own `knowledge/` tree now passes `scripts/knowledge_lint.py` clean under a live-tree
pytest gate (shared-lint-layer), with the `openspec-onboard` teaching-skill removed as a standing
drift risk. A shared lint layer (`ruff.toml` with E,F,I,B + enforced format, `scripts/check.sh` as
the single green gate) is now scaffold-managed.

## Latest change — composition-audit-cadence SHIPPED (2026-07-13)

Shipped the composition-audit cadence (OW-6, COMPLEX): a deterministic, advisory
composition-audit due-signal (archived-changes and commits since the last composition
anchor, OR co-fire) surfaced in the `outstanding` fact, plus an operator-invoked
`composition-audit` skill — a one-shot heavy-detector sweep (`checks.py --include`) plus
a bounded LLM composition pass over top-ranked hotspots — yielding a machine-
discriminable verdict (`COMPOSITION: CLEAN | FINDINGS-ROUTED | ESCALATE`) whose close-out
routes findings into the OW-2 ratchet. A new composition-anchor tag family
(`audit/<date>-composition`, a superset of plain `audit/*`) is the sole event resetting
the cadence clock. Three specs promoted: `composition-audit` (new), `outstanding-work-view`
and `knowledge-lint` (modified). Verify: full gate green — self-review, pro behavioral,
and flash test-quality lens passes all READY; self-review defects found and fixed (chiefly a missing-tag
commits-since gap); no Sonnet fallback anywhere. Downstream propagation is
operator-gated and DEFERRED (scaffold-only ship). Decisions: `knowledge/decisions/INDEX.md`;
follow-ons: `knowledge/questions/INDEX.md`. Archive:
`openspec/changes/archive/2026-07-13-composition-audit-cadence/`.

## Prior change — correctness-audit-skill SHIPPED (2026-07-13)

Shipped the deep-audit protocol (OW-5, COMPLEX) as one scaffold-owned, operator-invoked/
pull-only `correctness-audit` skill: charter/census/FINDINGS artifact contract, refuter-
overrule graduation discipline, per-wave-gate triage-file append, and close-out routing
into OW-2's finding-closure ratchet. New marker-gated `_check_audit_dossier` in
`knowledge_lint.py` (fires only on a `format: correctness-audit/v1` charter) plus fixture
tests. Two specs promoted: `correctness-audit` (new) and `knowledge-lint` (modified).
Verify: full gate green — self-review, pro behavioral, and flash lens passes all READY;
4 pro-pass warnings and 2 simplicity cleanups folded in, no Sonnet fallback used anywhere.
Downstream propagation is operator-gated and DEFERRED (scaffold-only ship). Decisions:
`knowledge/decisions/INDEX.md`; follow-ons: `knowledge/questions/INDEX.md`. Archive:
`openspec/changes/archive/2026-07-13-correctness-audit-skill/`.

## Prior change — verify-stack-redirect SHIPPED (2026-07-13)

Shipped the verify-stack redirect (OW-3, MEDIUM): the multi-model verify gate is now
tier-keyed and platform-uniform — MEDIUM runs self-review then one pro behavioral pass;
COMPLEX adds a third pass that is a **lens** (test-quality/adversarial-oracle default, or
data-scale for data-path-dominant changes) instead of a third same-checklist pass, closing
the zero-yield redundancy the empirical evidence showed. One `openspec-verifier` agent now
serves both the behavioral and lens prompts via prompt/`--model` selection. Two specs
promoted: `verify-multimodel-gate`, `noninteractive-delegation-safety` (dropped the
abandoned OpenCode Task-tool exemption). As-built delta: root `README.md`'s stale
verify-chain description was also reconciled directly (not scaffold-managed, no downstream
sweep owed). Verify: full gate green from disk; self-review and pro behavioral pass both
READY, no defects. Decisions: `knowledge/decisions/INDEX.md`; follow-ons:
`knowledge/questions/INDEX.md`. Archive:
`openspec/changes/archive/2026-07-13-verify-stack-redirect/`.

## Immediate next action
`composition-audit-cadence` (OW-6) is now **SHIPPED** — the frozen **OW-2→3→5→6 batch is
COMPLETE**. There is no proactive build in flight. Next is the wave-2 backlog: no session is yet
proposed for it (each item needs its own tier+plan confirmation) per
`knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md` (single source: OW-1..14
items, routing, session order), plus two late additions that slot in anywhere after the frozen
batch — `OW-15` (amends OW-5's capability; its gate is now clear) and `OW-16` (chain-independent,
greenfield). The Fable-tier design backlog is closed (2026-07-11 workflow audit:
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
