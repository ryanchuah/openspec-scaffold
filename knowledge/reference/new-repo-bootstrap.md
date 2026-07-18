# New-repo bootstrap checklist

Scaffold-local, on-demand reference — NOT manifest-listed, so it never syncs to a downstream repo.
Consult it *here* (in the scaffold) when standing up a fresh downstream repo. `scripts/sync_scaffold.py
<target>` copies the manifest-listed files, but it does not perform the manual per-repo wiring below —
each step verified against the real repo.

1. **Wire the git-native commit-test gate: run `bash scripts/setup-hooks.sh` once per clone.** Sets
   `git config --local core.hooksPath scripts/githooks` (idempotent, conflict-safe — see the script's
   header comment) so git runs `scripts/githooks/pre-commit` on every `git commit`, which execs
   `scripts/check.sh`. This is the **primary, agent-neutral** enforcement layer — it fires on every
   commit spelling (`git commit`, `cd repo && git commit`, `git -C repo commit`, `env FOO=bar git
   commit`, ...) and every harness (Claude / OpenCode / operator terminal), skipped only by the visible
   `--no-verify` opt-out. `core.hooksPath` is `.git/config` state, not tracked/cloned, so this step is
   per-clone, not one-time-per-repo.
2. **Wire the commit-test gate `PreToolUse` hooks in `.claude/settings.json` (Claude-only fallback).**
   Two hook entries on `Bash(git commit*)`: `scripts/test-gate.sh` (runs the per-repo test command;
   fail-safe **defers** to the git-native hook from step 1 when it is confirmed wired and the commit is
   not `--no-verify` — see D3 in `git-native-commit-gate`'s design) and
   `python3 scripts/scaffold_check.py` (blocks direct commits to scaffold-managed files). Both scripts
   are manifest-synced; only the `.claude/settings.json` wiring itself is manual — confirmed live in
   `psc-monitor`'s `.claude/settings.json`. If this wiring is missing, `sync_scaffold.py` already warns
   about it on stderr at sync/`--check` time (`_warn_if_hook_unwired`) — that warning is exactly this
   gap; treat it as the reminder to come do this step.
3. **Arm the commit-test gate itself: create `scripts/test-cmd`.** A one-line file containing the
   repo's test invocation (e.g. `.venv/bin/python -m pytest -q`). Absent or empty/whitespace-only means
   the gate is a no-op (`check.sh`, run by both the git-native hook and `scripts/test-gate.sh`, verified
   in its own header comment). After creating it, confirm the gate actually runs it (e.g. trigger a
   commit and watch for the `check: running '<cmd>'...` line).
4. **Fill per-repo identity: `AGENTS.md` `## Project context` and `openspec/config.yaml` `context:`
   block.** These are the two per-repo blocks `sync_agents_md`/`sync_config_yaml` deliberately preserve
   (never overwritten by a sync) — a fresh repo needs them written once. Keep `openspec/config.yaml`'s
   `context:` as the single short source (project, tech stack, testing philosophy); do not duplicate it
   at length in `AGENTS.md`.
5. **Seed `knowledge/STATUS.md` and `knowledge/questions/INDEX.md`.** These are the two mandatory
   per-repo boot reads beyond `AGENTS.md` itself (the mid-session handoff file is the third boot read,
   but only when present — its normal state is absent, so it needs no seeding). A fresh repo needs at
   least a minimal current-state preamble in `STATUS.md` and an empty (or genuinely-empty) Active
   section in `questions/INDEX.md`.
6. **Run the two lint gates clean.** `python3 scripts/scaffold_lint.py` (AGENTS.md anchors, dangling
   skill refs, budgets) and `python3 scripts/knowledge_lint.py` (orphan/duplicate canonical files,
   retired-path tokens, broken prose citations, dangling archive pointers) must both exit `0` before the
   repo is considered bootstrapped.
7. **Provision pinned security scanners.** See `knowledge/reference/security-scanners.md` for the two
   scanners (`gitleaks` for secrets, `osv-scanner` for dependency CVEs), their pinned versions, and the
   recommended provisioning per environment. For **CI**, wire the official actions
   (`gitleaks/gitleaks-action`, `google/osv-scanner-action`) — per-repo wiring, deferred to D1/D2. For
   **local development**, run `bash scripts/install-tools.sh`, which `go install`s the pinned scanners
   when the Go toolchain is present (both tools are Go binaries) and otherwise warns + points to the
   reference doc without hard-failing. `deptry` comes via dev extras (pip), not a binary install.
8. **Install ruff (dev dependency).** `ruff` is pinned in `dev-requirements.txt` (repo root) and is the
   lint + format engine behind `scripts/check.sh`. Install it as part of your Python environment:
   `.venv/bin/python -m pip install -r dev-requirements.txt` or the equivalent for your
   environment. Without ruff, `check.sh` runs a degraded mode (warns, skips lint/format, still runs
   tests).

**Provenance stamp:** after the first real `sync_scaffold.py <target>` run (not `--check`), the target
repo carries `.scaffold-version` at its root — a non-manifest beacon recording the scaffold HEAD short
SHA, that commit's committer date, and its subject line. It is the durable "which scaffold commit was I
last synced from" marker a fresh repo carries going forward; see the `scaffold-sync-mechanism` spec
delta (`sync-stamps-scaffold-provenance`) for its exact contract.

Out of scope here: this is a checklist, not a handbook — for the mechanics of *why* each block is
preserved across a sync, see `sync_scaffold.py`'s own docstrings and the `scaffold-sync-mechanism`
capability spec.
