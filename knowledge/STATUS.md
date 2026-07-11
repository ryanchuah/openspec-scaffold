# Status

## Current state
Project initialised from openspec-scaffold. Delegated-work governance hardened: the apply-executor now stops and reports on non-convergence instead of looping, the reviewer has a raised budget with incremental output and partial-salvage on timeout, and a Claude `PreToolUse` commit-test-gate deterministically blocks commits when tests are not green. Instruction surface hardened: a tier-confirmation gate prevents non-autonomous agents from self-classifying and executing without operator confirmation, and six stale/hazardous instruction sites were reconciled to shipped behavior. Delegation robustness hardened: all delegated `opencode run` invocations now close stdin to prevent permission-prompt hangs, per-agent permissions contain write-capable executors, the non-convergence canary is rebuilt as a non-gameable impl-module+frozen-test, and the commit-test-gate ships a smoke fixture with documented hook-wiring procedure. Verify hardened: independent multi-model verification passes (platform-specific chains; Claude self→pro→flash, OpenCode self→flash) now run as hard gates after the orchestrator's self-review, layered before the artifact checklist, so the final release-quality gate is never decided by a single model's blind spots. The shared `opencode run` delegation harness (invocation hardening, assert-real-agent-ran, surgical-kill, EXIT-sentinel completion detection, timeout budgets) is now single-sourced in `.claude/skills/_shared/delegation-harness.md`, with the four delegating skills reduced to citations plus per-phase specifics — extraction, not redesign, with all behavior and budgets preserved byte-for-byte. The verify gate is tier-scaled: multi-model passes apply to MEDIUM/COMPLEX only; a simplicity/quality gate and a conditional security gate (for sensitive-surface changes) were added, layered after the verifier passes; the archive-executor bodies were hardened to handle RENAMED spec requirements; and a new `scripts/test_executor_body_agreement.py` guard byte-compares each `.claude`/`.opencode` executor-pair body, failing when the two drift. The `knowledge/questions/INDEX.md` always-loaded surface is now bounded by a horizon split: it holds ONLY active items (blockers, operator-decision items, in-flight backlogs); the deferred/monitored long tail lives in the Parked section of `knowledge/questions/` (with per-item files for individual items). Instruction-surface rule-restatements single-sourced: five rule-families previously duplicated 3–5× across the instruction surface each assigned one canonical home with all other sites reduced to per-context specifics + a citation — extraction, not redesign, with every rule preserved verbatim. The canonical homes and the cite-don't-restate convention live in `knowledge/lessons.md` §2. The
scaffold's own `knowledge/` tree now passes `scripts/knowledge_lint.py` clean under a live-tree
pytest gate (shared-lint-layer), with the `openspec-onboard` teaching-skill removed as a standing
drift risk. A shared lint layer (`ruff.toml` with E,F,I,B + enforced format, `scripts/check.sh` as
the single green gate) is now scaffold-managed.

## Latest change — outstanding-work-collector SHIPPED (2026-07-09)

Shipped a deterministic outstanding-work gather: a `facts.py` fact (`outstanding`) enumerates
every configured source — `knowledge/questions/` Active+Parked, open `tasks.md` checkboxes, live
`plans/`, non-closed roadmap entries, and audit `FINDINGS*` files — into one
`output/facts/outstanding.{md,json}` snapshot with `source:line` provenance and a separate
untriaged-findings bucket. Extractors handle both bullet and table-form `INDEX.md` files. The fact
regenerates on use (never stale) and degrades on malformed input rather than crashing (D2). Three
new `knowledge_lint.py` drift checks — duplicate-block detection, closed-but-unpruned flagging, and
untriaged-age accumulation — catch rot automatically via the existing live-tree gate. A pull-only
`outstanding-work-review` skill drives LLM judgment from the snapshot. All scaffold-managed, zero
boot-context cost. Verify: self-review + pro + flash multi-model passes READY, all behavioral
contracts confirmed on fixtures, full suite green including scaffold SEAL and live-tree lint gate.
Decisions in `knowledge/decisions/INDEX.md`; follow-ons parked in `knowledge/questions/`. Archive:
`openspec/changes/archive/2026-07-09-outstanding-work-collector/`.

## Prior change — shared-lint-layer SHIPPED (2026-07-03)

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

## Immediate next action
Four changes are **propose-complete and deliberately paused at apply** (operator-mandated batching):
`lesson-check-ratchet` (OW-2), `verify-stack-redirect` (OW-3), `correctness-audit-skill` (OW-5),
`composition-audit-cadence` (OW-6). Next session (Opus orchestrator) applies them in hard order
OW-2→3→5→6, then works the remaining backlog per
`knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md` (single source: OW-1..13
items, routing, session order). The Fable-tier design backlog is closed (2026-07-11 workflow audit:
`knowledge/research/workflow-audit-2026-07-11/AUDIT.md`); everything remaining is Opus-tier.
Earlier portfolios (succession-hardening; day-to-day tooling A/B/C) are fully shipped.

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
