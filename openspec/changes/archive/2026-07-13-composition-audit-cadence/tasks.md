# Tasks — composition-audit-cadence

Implement in order; groups 1–4 are independent of group 5 but MUST land before group 6.
Normative contracts: `specs/composition-audit/spec.md`, `specs/outstanding-work-view/spec.md`,
`specs/knowledge-lint/spec.md`. How + rationale: `design.md` (D1–D10). Acceptance criteria:
`design.md` §Verification (AC1–AC7). Do not restate the ceremony sequence anywhere — cite the
spec (D10).

## 1. audit_scope.py — composition anchor variant (D1, D2 / AC3)

- [x] 1.1 Add `--kind {plain,composition}` (default `plain`) to the `tag` subparser
      (`scripts/audit_scope.py:393–397`) and the `log-line` subparser (:399–401).
- [x] 1.2 In `cmd_tag` (:309–310): when `--kind composition`, use
      `tag_name = f"audit/{args.date}-composition"`; the plain path stays byte-identical
      (same annotated-tag mechanics, same message shape).
- [x] 1.3 In `cmd_log_line` (print at :363): when `--kind composition`, print
      `- **<date>** · audit/<date>-composition · <short-sha> · <essence>`; plain output
      byte-identical to today.
- [x] 1.4 Tests in `scripts/test_audit_scope.py`: composition tag created as annotated
      `audit/<date>-composition`; plain tag/log-line outputs unchanged; composition
      log-line matches the updated `knowledge_lint` regex (import the compiled regex or
      duplicate the pattern literal in the test).

## 2. knowledge_lint.py — accept the composition registry line (D2 / AC3)

- [x] 2.1 Edit `_AUDIT_LOG_FULL_RE` (`scripts/knowledge_lint.py:147`): change the anchor
      segment `audit/\d{4}-\d{2}-\d{2}` to `audit/\d{4}-\d{2}-\d{2}(?:-composition)?`.
      Update the docstring format note (:51–54) to name both accepted variants.
- [x] 2.2 Tests in `scripts/test_knowledge_lint.py`: composition line accepted; plain
      line still accepted; a foreign suffix (e.g. `audit/2026-07-11-security`) flagged
      malformed.

## 3. checks.py — `--include` one-shot + inventory sibling anchor (D5, D8 / AC2, AC4)

- [x] 3.1 Add repeatable `--include NAME` (`action="append"`) to the CLI (near :1433);
      guard: valid only with `--report`, mirroring the `--baseline` guard at :1439
      (violation → INFRA-FAIL message, exit 3).
- [x] 3.2 Thread the include list into the `--report` path of `_mode_multi`: after the
      config/defaults enabled-merge, force each named check to enabled **for this run
      only**; unknown name → INFRA-FAIL (exit 3) before preflight; already-enabled name
      → no-op (check runs exactly once); included checks participate in preflight
      exactly like enabled checks. No configuration is written anywhere.
- [x] 3.3 In the inventory fact (audit_anchor build at :647–676): add a sibling
      `"composition_anchor": {"tag": <latest audit/*-composition tag or null>,
      "commits_since": <int>}` using the same discovery/count mechanics restricted to
      the `audit/*-composition` glob (full-history count when no tag).
- [x] 3.4 Tests in `scripts/test_checks.py`: AC2 scenario battery — disabled check runs
      under `--report --include` (use a `[checks.custom]` fixture entry, not a heavy
      binary); missing included tool → preflight exit 3 with standard guidance;
      `--include` without `--report` → exit 3; unknown name → exit 3; already-enabled
      include runs the check exactly once; no `--include` → byte-identical behavior.
      AC4 — fixture repo with a plain tag after a composition tag: `audit_anchor`
      reports the plain tag, `composition_anchor` the composition tag; no composition
      tag → `tag: null` + full-history count.
- [x] 3.5 Docstring updates in `scripts/checks.py`: `--include` in the usage block
      (:121 region); **create** a `[facts.outstanding]` section in the config-schema
      docstring (:23–70) — it does not exist yet — documenting all four keys: the two
      existing ones (`findings_globs`, `finding_id_pattern`, defaults sourced from
      `scripts/outstanding.py:28–32`) and the two new thresholds, with a citation that
      the composition-audit spec is normative for the threshold defaults.

## 4. outstanding.py — composition_audit due-signal block (D3, D4 / AC1)

- [x] 4.1 Extend `_load_config` (`scripts/outstanding.py:40–51`) with
      `composition_change_threshold` (default 10) and `composition_commit_threshold`
      (default 100) from `[facts.outstanding]`.
- [x] 4.2 Implement `_composition_signal(root, config) -> dict` per
      `specs/composition-audit/spec.md` `composition-cadence-trigger-semantics`:
      anchor = latest `audit/*-composition` tag (`git tag --list --sort=-creatordate`);
      `archived_changes_since` via `git diff --name-only --diff-filter=A
      <anchor>..HEAD -- openspec/changes/archive/` (dedupe first path component under
      `archive/`; no anchor → count all top-level archive dirs);
      `commits_since` via `git rev-list --count`; `due` = OR of the two thresholds;
      degradations: git failure → `status:"no-git"`, `due:false`; unreachable anchor
      commit → no-anchor semantics with the cause in `reason`; block carries
      `computed_from: "git"`.
- [x] 4.3 Wire the block into `run()`'s payload (:569–607) as top-level
      `"composition_audit"` and into the rendered markdown via `_render_md` (:497;
      insertion-point logic slots into the line-building loop starting ~:508):
      `## Composition audit` section directly under the snapshot header when `due`,
      at the bottom otherwise.
- [x] 4.4 Tests in `scripts/test_outstanding.py` on fixture git repos (AC1 battery):
      no anchor + archives ≥ threshold → due (extrends-shape); **plain `audit/<date>`
      tag laid after a composition anchor does NOT reset the composition counts**
      (the premise-review 🟡1 scenario, kept as a frozen regression test); composition
      anchor at HEAD → counts reset to zero; thresholds honored from config; OR co-fire
      (commits trip with sparse archives); post-archive edit to an existing archived
      dir does NOT inflate `archived_changes_since` (diff-filter=A); no-git degradation
      renders cleanly; unreachable-anchor degrades to no-anchor with reason.

## 5. composition-audit skill + manifest (D7, D9, D10 / AC5)

- [x] 5.1 Write `.claude/skills/composition-audit/SKILL.md`: frontmatter per house
      skill conventions (operator-invoked, pull-only — use
      `.claude/skills/outstanding-work-review/SKILL.md:1–9` as the canonical
      frontmatter template); body cites
      `openspec/specs/composition-audit/spec.md` for the ceremony sequence and default
      K (never restates them), and carries only per-step operational detail: run-audit's
      wiring-detection branch shape; the exact sweep command line (`--report --include
      jscpd --include vulture --include radon` + `--baseline
      output/checks/composition-baseline.json` when present); INFRA-FAIL → surface
      preflight guidance verbatim and stop; pre-digest delegated to a cheap model via
      `.claude/skills/_shared/delegation-harness.md` patterns; verdict written to
      `<report-dir>/composition-verdict.md`; close-out procedure with
      orchestrator-performed ratchet triage (cite the finding-closure-ratchet spec),
      `log-line --kind composition`, operator-gated `tag --kind composition`, and the
      baseline copy; the honest-limits positioning paragraph (detectors catch the
      mechanical slice; judgment pass + ESCALATE carry the rest); the cost bound; the
      D8 residual attention-dependence note + 30-day revisit trigger; the D9
      knowledge-drift-review recommendation.
- [x] 5.2 Add `.claude/skills/composition-audit/SKILL.md` to
      `scripts/scaffold_manifest.txt` — Skills section, between
      `knowledge-drift-review/SKILL.md` (line 9) and `openspec-apply-change/SKILL.md`
      (line 10).

## 6. Green gate (AC6)

- [x] 6.1 Run `scripts/check.sh` — ruff, format, full pytest suite (scaffold SEAL,
      live-tree lint gates, and all new tests) green. Fix regressions before reporting
      done; do not commit (the orchestrator commits).
