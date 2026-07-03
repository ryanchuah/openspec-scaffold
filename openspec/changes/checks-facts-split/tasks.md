# Tasks — checks-facts-split

Context for the executor: `plans/day-to-day-tooling/explore-brief.md` (direction, PREMISE:
AGREE) defines this change (portfolio change A). The engine being split is
`scripts/audit_bundle.py`; its registry is at `_REGISTRY` (~line 170), availability at
`_tool_status`/`_availability_for_check` (~315-357), multi-run control flow at `_mode_multi`
(~1114-1247), config load at `_load_config` (~220), output-dir literal at ~1304.
Naming contract: **checks** = findings-capable detectors (gate/record semantics, dated
output); **facts** = can't-fail repo snapshots (cache semantics, undated output,
regenerate-on-use); **audit** = the operator ceremony (unchanged `audit_scope.py` tag/log
+ `run-audit` skill + `knowledge/audit-log.md` — these keep the audit name).

## 1. Engine rename and family split

- [ ] 1.1 `git mv scripts/audit_bundle.py scripts/checks.py`. Update the module docstring
      to the checks/facts/audit trichotomy. Change every stdout/stderr summary prefix
      `audit_bundle:` → `checks:`. Do NOT change any behavior in this task beyond the
      rename (later tasks do that); get the suite compiling again by updating imports in
      any file that imports `audit_bundle` (grep for it — includes the test file's own
      `import audit_bundle` at test_audit_bundle.py:28, which becomes `import checks`;
      the file itself is renamed later in task 5.1).
- [ ] 1.2 Add a `family` field to every `_REGISTRY` entry: `"check"` for ruff, gitleaks,
      osv-scanner, deptry, data-lint, jscpd, vulture; `"fact"` for scope, radon,
      index-coverage, inventory. Registry order and tiers stay unchanged. Note the
      deliberate behavioral change this enables: `scope` (tier floor, family fact) stops
      running under `--floor` in task 1.3 — intentional per the explore-brief; it moves
      to the facts surface (task 3.1).
- [ ] 1.3 In `scripts/checks.py`, scope the run modes by family: `--floor` selects
      floor-tier entries with `family == "check"` only; `--report` keeps running ALL
      enabled checks (both families — the audit ceremony wants everything, dated);
      `--check <name>` keeps its current semantics for any name; `--list` keeps its
      current shape but gains a FAMILY column.

## 2. Preflight and self-explaining failures (checks.py)

- [ ] 2.1 Add per-check metadata to `_REGISTRY` entries that need an external binary:
      `trigger` (human string, e.g. ".git present" / "pyproject.toml present" /
      "lockfile present") and `coverage_note` (what disabling loses, e.g. "disabling
      drops secret scanning" for gitleaks, "drops known-vulnerability scanning" for
      osv-scanner, "drops dependency-hygiene checking" for deptry).
- [ ] 2.2 Preflight in `_mode_multi` (`--floor`/`--report`): BEFORE executing any check,
      compute availability for every selected+enabled entry with `family == "check"`
      (fact-family entries are exempt — they keep today's graceful degradation, e.g.
      radon absent never fails a run); if one or more are `unavailable` or
      `version-mismatch`, print one self-explaining line per tool to stderr in the shape
      `checks: INFRA-FAIL — <name>: <not on PATH|version mismatch (expected X, found Y)>
      (enabled by trigger: <trigger>). Install <name> <pinned-version-if-pinned>, or
      disable in checks.toml: [checks.<name>] enabled = false — <coverage_note>.`,
      record each as an INFRA-FAIL entry in `run-manifest.json`, run NOTHING, exit 3.
- [ ] 2.3 Keep stop-on-first-failure for infra failures that arise mid-run (a binary that
      passed preflight but crashes/times out); extend those messages with the same
      install-or-disable tail. Findings still never abort (exit 2 accumulation unchanged).
- [ ] 2.4 `--list`: after the listing, when any enabled check-family entry is
      unavailable/mismatched, print a one-line summary: `checks: N enabled check(s)
      unavailable — --floor/--report will fail preflight until installed or disabled.`
      Exit stays 0.

## 3. The facts surface (after the engine changes it depends on)

- [ ] 3.1 Create `scripts/facts.py`: a thin CLI importing the engine from
      `scripts/checks.py`. **Contract (explicit):** it does NOT call `_mode_multi` and
      is therefore never subject to preflight; it runs its own loop calling
      `_execute_check` directly for each selected fact, passing
      `out_dir = Path("output") / "facts"` (undated, artifacts overwritten each run).
      Default mode runs all enabled `family == "fact"` entries; `--check <name>`
      runs one fact (a check-family name is a usage error, exit 2 from argparse);
      `--list` filters the engine's listing to the fact family locally (same line
      shape). Exit code: always 0 once arguments parse; per-fact tool degradation
      (e.g. radon absent) is recorded in the artifact JSON as today, never a process
      failure. `facts.py` exposes no tag/log/baseline surface.
- [ ] 3.2 Inventory gains an `audit_anchor` field: `{"tag": <latest audit/* tag or
      null>, "commits_since": <int or null>}`, computed via
      `audit_scope._latest_audit_tag` and `git rev-list <tag>..HEAD --count` (null tag →
      null count). Applies wherever inventory runs (facts.py and checks.py --report).

## 4. Config and output-path renames

- [ ] 4.1 `_load_config` in checks.py: read `checks.toml` instead of `audit.toml`
      (config-source label `"checks.toml"|"defaults"`). No fallback read of
      `audit.toml` — no repo has one.
- [ ] 4.2 `scripts/knowledge_lint.py`: the config read at line 290
      (`config_path = root / "audit.toml"`) moves to `checks.toml`; update the docstring
      prose references at lines 25, 61, and 286. Do NOT touch lines 106/120 — those are
      `audit-log.md` canonical-map/ephemeral-path entries, unrelated to the config file.
      Update the test code at lines 202, 216, and 232 of
      `scripts/test_knowledge_lint.py` (the per-repo config section referencing
      `audit.toml`).
- [ ] 4.3 `--report` output dir in checks.py: `output/audit/<date>/` →
      `output/checks/<date>/` (the literal at ~1304). `--floor`/`--check` CWD default
      unchanged.

## 5. Manifest, removed-paths, and test-file renames

- [ ] 5.1 `git mv scripts/test_audit_bundle.py scripts/test_checks.py`; update imports
      (the self-import from task 1.1 note), summary-prefix regexes (`audit_bundle:` →
      `checks:`), `output/audit` → `output/checks`, and `audit.toml` → `checks.toml`
      fixtures.
- [ ] 5.2 `scripts/scaffold_manifest.txt`: replace `scripts/audit_bundle.py` and
      `scripts/test_audit_bundle.py` with `scripts/checks.py`, `scripts/facts.py`,
      `scripts/test_checks.py` — all three exist by this task. Do NOT add
      `scripts/test_facts.py` here; it is added in task 6.3 together with the file it
      names (manifest completeness must hold at every intermediate state).
- [ ] 5.3 `scripts/scaffold_manifest_removed.txt` (exists from the sync-deletion-manifest
      change — append, don't create): append `scripts/audit_bundle.py` and
      `scripts/test_audit_bundle.py` (with a dated comment naming this change).
      `scaffold_lint`'s manifest-no-conflict check must stay green.

## 6. Behavior tests

- [ ] 6.1 Rework `MissingBinaryAbortTest`/`ResumeOrderProofTest` (now in test_checks.py)
      to the preflight semantics: (a) preflight failure runs nothing and reports ALL
      missing tools in one run (assert two simultaneously-missing check-family tools
      both appear in stderr and in `run-manifest.json`, and no check executed); (b)
      mid-run stop-on-first-failure is still exercised via a stub binary that exists
      (passes preflight) but exits nonzero/crashes at run time.
- [ ] 6.2 Add preflight-message shape tests: the INFRA-FAIL line carries trigger,
      install-or-disable guidance, and coverage note; a missing fact-family tool (radon)
      does NOT trigger preflight failure in `--report`; `--list` summary line appears
      exactly when an enabled check-family entry is unavailable.
- [ ] 6.3 New `scripts/test_facts.py` — and in the same task add
      `scripts/test_facts.py` to `scripts/scaffold_manifest.txt` (deferred from 5.2 so
      the manifest never names a nonexistent file). Tests: default run writes undated
      `output/facts/*.json`
      and exits 0; a check-family name is rejected by `facts.py --check` (usage error);
      fact names absent from `checks.py --floor` selection; inventory `audit_anchor`
      correct with and without an anchor tag — the tag MUST use the `audit/` prefix
      (e.g. `git tag -a audit/2026-01-01 -m x` in the tmp repo; a non-`audit/*` tag must
      NOT be picked up); radon-absent degradation still exits 0.
- [ ] 6.4 `audit_scope.py` ceremony updates: `cmd_log_line` prints the stderr hint —
      `audit_scope: knowledge/audit-log.md does not exist yet (first audit) — create it
      with a '# Audit log' heading, then append the line below.` — when the file is
      absent at the repo root, stdout unchanged; update `audit_scope.py`'s docstring to
      state it is the audit-ceremony surface (scan/tag/log-line) and that day-to-day
      entry points are `checks.py`/`facts.py`.
- [ ] 6.5 `scripts/test_audit_scope.py`: add log-line first-run-hint test (hint on
      stderr when `knowledge/audit-log.md` absent; no hint when present; stdout line
      byte-identical in both cases).
- [ ] 6.6 Run the full suite (`pytest -q scripts/`) and make it green, including
      `test_scaffold_lint.py` (manifest completeness + no-conflict against the updated
      manifests).

## 7. Instruction surface and spec delta

- [ ] 7.1 `.claude/skills/run-audit/SKILL.md` — mechanical rename pass: every command
      string `audit_bundle.py` → `checks.py`, `audit.toml` → `checks.toml`,
      `output/audit/<date>/` → `output/checks/<date>/` (body and frontmatter
      description).
- [ ] 7.2 `.claude/skills/run-audit/SKILL.md` — prose additions: `--report` runs both
      families dated; the enabled-vs-installed distinction and preflight semantics (all
      missing tools reported at once; install-or-disable is the operator's call —
      disabling a security tool drops that coverage); day-to-day entry points
      (`facts.py` orientation snapshots are not part of the ceremony); a
      staleness-cadence line (trigger an audit from the inventory
      `audit_anchor.commits_since` signal, not a calendar); the annual "re-justify the
      suppression baseline/whitelist" reminder.
- [ ] 7.3 AGENTS.md "Deterministic audit tooling" section: rewrite to the
      checks/facts/audit trichotomy — day-to-day: `facts.py` regenerate-on-use snapshots
      and `checks.py` detectors; ceremony: `run-audit` skill, `audit_scope.py tag`
      anchor, `knowledge/audit-log.md`. Keep the section's existing rules (never writes
      to code; untracked disposable outputs; tag is the sole mutation; registry-line
      format) intact. Keep the edit surgical — this is a shared propagated span.
- [ ] 7.4 Write the delta spec `openspec/changes/checks-facts-split/specs/knowledge-lint/spec.md`
      updating the knowledge-lint capability's `audit.toml` reference to `checks.toml`
      (MODIFIED requirement, delta format as in archived changes).
- [ ] 7.5 Repoint stragglers — this exact live-reference list (verified 2026-07-03),
      plus a confirming `grep -rn "audit_bundle\|audit\.toml\|output/audit"` for
      anything newly added:
      `knowledge/reference/exit-codes.md:9` (audit_bundle.py → checks.py);
      `knowledge/reference/resync-verification.md:60` (audit.toml → checks.toml);
      `knowledge/README.md:16` (output/audit → output/checks);
      `knowledge/questions/run-audit-untested.md` lines 5/7/14 (audit.toml, audit_bundle);
      `knowledge/questions/deterministic-tooling-layer-follow-ons.md:41` (audit.toml);
      `knowledge/questions/audit-skill-metadata-cleanup.md:7` (audit_bundle);
      `openspec/config.yaml:5` (the context-block Purpose line mentioning the audit
      layer — this repo's own per-repo context, safe to update here; do NOT touch the
      Web-research rule at line 9).
      EXCLUDE: `openspec/changes/archive/`, `knowledge/research/`,
      `knowledge/decisions/INDEX.md`, and `knowledge/STATUS.md` (historical records keep
      old names; STATUS.md is reconciled at archive by the archive-executor, not here).
