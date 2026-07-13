# Status

## Current state
Project initialised from openspec-scaffold. Delegated-work governance hardened: the apply-executor now stops and reports on non-convergence instead of looping, the reviewer has a raised budget with incremental output and partial-salvage on timeout, and a Claude `PreToolUse` commit-test-gate deterministically blocks commits when tests are not green. Instruction surface hardened: a tier-confirmation gate prevents non-autonomous agents from self-classifying and executing without operator confirmation, and six stale/hazardous instruction sites were reconciled to shipped behavior. Delegation robustness hardened: all delegated `opencode run` invocations now close stdin to prevent permission-prompt hangs, per-agent permissions contain write-capable executors, the non-convergence canary is rebuilt as a non-gameable impl-module+frozen-test, and the commit-test-gate ships a smoke fixture with documented hook-wiring procedure. Verify hardened: independent multi-model verification passes (platform-specific chains; Claude self→pro→flash, OpenCode self→flash) now run as hard gates after the orchestrator's self-review, layered before the artifact checklist, so the final release-quality gate is never decided by a single model's blind spots. The shared `opencode run` delegation harness (invocation hardening, assert-real-agent-ran, surgical-kill, EXIT-sentinel completion detection, timeout budgets) is now single-sourced in `.claude/skills/_shared/delegation-harness.md`, with the four delegating skills reduced to citations plus per-phase specifics — extraction, not redesign, with all behavior and budgets preserved byte-for-byte. The verify gate is tier-scaled: multi-model passes apply to MEDIUM/COMPLEX only; a simplicity/quality gate and a conditional security gate (for sensitive-surface changes) were added, layered after the verifier passes; the archive-executor bodies were hardened to handle RENAMED spec requirements; and a new `scripts/test_executor_body_agreement.py` guard byte-compares each `.claude`/`.opencode` executor-pair body, failing when the two drift. The `knowledge/questions/INDEX.md` always-loaded surface is now bounded by a horizon split: it holds ONLY active items (blockers, operator-decision items, in-flight backlogs); the deferred/monitored long tail lives in the Parked section of `knowledge/questions/` (with per-item files for individual items). Instruction-surface rule-restatements single-sourced: five rule-families previously duplicated 3–5× across the instruction surface each assigned one canonical home with all other sites reduced to per-context specifics + a citation — extraction, not redesign, with every rule preserved verbatim. The canonical homes and the cite-don't-restate convention live in `knowledge/lessons.md` §2. The
scaffold's own `knowledge/` tree now passes `scripts/knowledge_lint.py` clean under a live-tree
pytest gate (shared-lint-layer), with the `openspec-onboard` teaching-skill removed as a standing
drift risk. A shared lint layer (`ruff.toml` with E,F,I,B + enforced format, `scripts/check.sh` as
the single green gate) is now scaffold-managed.

## Latest change — lesson-check-ratchet SHIPPED (2026-07-13)

Shipped the finding-closure ratchet (OW-2): a lint-enforced closure contract so a
generalizable bug class, once found, cannot silently recur. New `knowledge/ratchet-log.md`
registry ledger records exactly one disposition per class (check/frozen-test/waiver/open/
grandfathered, preference check > test > waiver), enforced by guarded `knowledge_lint.py`
checks (dangling pointers, stale waivers, aged `open`, malformed lines). New per-repo
`checks/*.py` invariant framework (stdlib `scripts/repo_lint.py`, sibling of `data_lint.py`),
registered in `checks.py`. Both close-out gates (archive, run-audit) gained the bounded
3-question triage. Verify: full suite green incl. the live-tree lint gate over the
bootstrapped ledger and `scaffold_lint` SEAL; both pro+flash multi-model verifier passes
READY, no defects outstanding. Decisions: `knowledge/decisions/INDEX.md`; follow-ons:
`knowledge/questions/INDEX.md`. Archive:
`openspec/changes/archive/2026-07-13-lesson-check-ratchet/`.

## Prior change — outstanding-and-continuity-hardening SHIPPED (2026-07-13)

Widened the `knowledge_lint.py` handoff-file check from a root-only, case-sensitive
`HANDOFF*`/`HANDOVER*` prefix match to a repo-wide, case-insensitive substring match over the
whole tree, respecting gitignore, with `knowledge/HANDOFF.md` as the sole sanctioned exemption —
closing the gap where nested handoff-named files (e.g. `plans/*-handoff.md`) escaped the
single-canonical-handoff enforcement. AGENTS.md's Working process now signposts the pull-only
`outstanding-work-review` skill as the canonical outstanding-work entry point (deliberately not
boot-wired), and that skill's Judge step names a "Residual sweep" sub-step for what the
deterministic gather can't see (prose bodies, in-code TODOs, orphaned research docs). Verify:
self-review only, ran clean (multi-model pro pass operator-waived). Decisions:
`knowledge/decisions/INDEX.md`; follow-ons: `knowledge/questions/INDEX.md`. Archive:
`openspec/changes/archive/2026-07-13-outstanding-and-continuity-hardening/`.

## Prior change — outstanding-work-collector SHIPPED (2026-07-09)

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

## Immediate next action
`lesson-check-ratchet` (OW-2) is now **SHIPPED**. Three changes remain **propose-complete and
deliberately paused at apply** (operator-mandated batching), applied in this hard order:
`verify-stack-redirect` (OW-3) → `correctness-audit-skill` (OW-5) → `composition-audit-cadence`
(OW-6). Next session (Opus orchestrator) applies them in that order, then works the remaining
backlog per `knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md` (single source:
OW-1..14 items, routing, session order). The Fable-tier design backlog is closed (2026-07-11
workflow audit: `knowledge/research/workflow-audit-2026-07-11/AUDIT.md`); everything remaining is
Opus-tier. Earlier portfolios (succession-hardening; day-to-day tooling A/B/C) are fully shipped.

**lesson-check-ratchet SHIPPED (2026-07-13)** — downstream propagation of its scaffold changes
(`repo_lint.py`, `knowledge_lint.py` ratchet checks, the two skill triage steps) is **operator-gated
and deferred**: the framework arrives INERT on the next authorized sync (no `checks/*.py`, no
per-repo ledger → auto-disabled, lint-guarded), and per-repo adoption is separate downstream SMALL
work. See `knowledge/questions/INDEX.md` Parked.

**outstanding-and-continuity-hardening SHIPPED (2026-07-13)** — scaffold-only; the frozen
OW-3→5→6 batch above remains the stated next work, unchanged by this change. Downstream
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
Next work is unchanged: OW-3 → OW-5 → OW-6.

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
