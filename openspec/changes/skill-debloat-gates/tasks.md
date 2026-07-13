# tasks — mechanized-verify-propose-gates (OW-11, scoped)

Apply-phase edits only. Design + scope + acceptance: `notes.md`; anchors + current text:
`recon-ow11.md`. Spec deltas authored under `specs/` (MODIFIED `defect-prevention-detectors` for #7,
MODIFIED `verify-multimodel-gate` for #5) — implement to match; do NOT re-author them. **Re-grep every
anchor before editing** (OW-7 + OW-10 shifted the skill files). **Tests pin behavior.**

checks.py detector architecture (from the OW-1/OW-4 precedent — see
`openspec/changes/archive/2026-07-13-defect-prevention-detectors/tasks.md` for the exact pattern):
`_REGISTRY` dicts; in-process builtins register in `_BUILTIN_RUNNERS` + `_PARSERS` (value MUST be
CALLABLE, e.g. `lambda _stdout: []`) + special-case `_availability_for_check` (always-available) +
`_autodetect_defaults` (enabled). Adding a registry entry REQUIRES updating `test_checks.py`
`ListModeTest.expected_names` + `AutodetectTest` + `SummaryLineFormatTest`.

## Group 1 — #7: `spec-delta-structure` detector (closes ratchet `medium-change-spec-delta-unvalidated`)

- [ ] **T1 — Registry + dispatch wiring.** In `scripts/checks.py` add a `spec-delta-structure`
  detector, mirroring `test-quality`/`data-scale` EXACTLY: a `_REGISTRY` entry
  (`{"name":"spec-delta-structure","tier":"floor","kind":"builtin","family":"check","trigger":"openspec change deltas present","coverage_note":"disabling drops MEDIUM spec-delta structural validation"}`);
  special-case `_availability_for_check` → always `available` (in-process, no external tool);
  `_autodetect_defaults` → `True` (enabled); register in `_BUILTIN_RUNNERS`
  (`spec-delta-structure → _run_spec_delta_structure`) and `_PARSERS`
  (`"spec-delta-structure": lambda _stdout: []`). The runner returns the outcome dict shape the
  builtin `else` branch expects, INCLUDING a `"findings"` list (see the OW-1/OW-4 T4 note).

- [ ] **T2 — `_run_spec_delta_structure` (the parser).** Discover change dirs by presence:
  `<repo_root>/openspec/changes/*/` **excluding** any dir named `archive`. For each, glob
  `specs/**/spec.md`. (Scan is rooted at `openspec/changes/` so it never reaches the `.claude/`
  worktree duplicate — but still skip any path containing `/archive/` or a `.`-prefixed segment, per
  the `detector-filewalker-scans-hidden-dirs` ratchet lesson.) For each delta `spec.md`, parse and
  emit a finding (stable `rule` slug) per violation:
  - `missing-delta-header` — the file has ≥1 `### Requirement:` but no `## (ADDED|MODIFIED|REMOVED|RENAMED) Requirements` section header. msg: "spec delta lacks an `## ADDED|MODIFIED|REMOVED|RENAMED Requirements` header".
  - `shall-not-first-line` — for each `### Requirement:` under an **ADDED or MODIFIED** section, the FIRST non-blank physical line of its body (the line after the `### Requirement:` header) does NOT contain `SHALL` or `MUST`. msg: "requirement `<name>`: normative SHALL/MUST not on the first physical line (openspec validate --strict fails at archive)". (Skip REMOVED/RENAMED requirement bodies — they name the requirement, not restate it.)
  - `requirement-no-scenario` — an ADDED/MODIFIED `### Requirement:` block with zero `#### Scenario:` sub-headings before the next `### Requirement:`/`##`/EOF. msg: "requirement `<name>`: no `#### Scenario:` block".
  Line = the offending header's `lineno`. One finding per site. Findings are ADVISORY (surface in the
  audit report; do NOT fail `check.sh`) — same contract as test-quality/data-scale.

- [ ] **T3 — Tests (`test_checks.py`).** Update `ListModeTest.expected_names` (+`spec-delta-structure`),
  `AutodetectTest` (enabled by default), and the `SummaryLineFormatTest` startswith tuple
  (`"spec-delta-structure:"`). Add finding tests: write a temp `openspec/changes/demo/specs/cap/spec.md`
  with (a) a MODIFIED requirement whose SHALL is on line 2 (clean) → no `shall-not-first-line`; (b) a
  requirement whose first body line is prose and SHALL is on line 3 → `shall-not-first-line`; (c) a
  requirement with no scenario → `requirement-no-scenario`; (d) a delta file with a Requirement but no
  `## ... Requirements` header → `missing-delta-header`. NEGATIVE: a well-formed delta yields ZERO
  findings; a dir under `openspec/changes/archive/` is NOT scanned.

- [ ] **T4 — Verify-skill wiring (make it enforcing).** In `.claude/skills/openspec-verify-change/SKILL.md`,
  in the Completeness/artifact-mapping area (recon §1, Steps 12-16), add ONE line: when the change has
  spec deltas (`specs/**/spec.md`), the orchestrator SHALL run
  `checks.py --check spec-delta-structure` and resolve any finding BEFORE advancing to archive (this
  is the deterministic replacement for hand-checking SHALL-on-first-line, which caught nothing
  automatically before). Do NOT rewrite the fuzzy Steps 13-14 keyword-search prose — that de-bloat is
  DEFERRED (notes "DEFERRED #1"); this task only ADDS the detector-run line.
  **Ordering:** apply T7 (the larger verify-skill prose reorder) BEFORE this one-line add, then
  re-grep this anchor — T7 may shift the Steps 12-16 line numbers.

## Group 2 — #6: `model-id-agreement` scaffold_lint check (golden-source-only)

- [ ] **T5 — Canonical sanctioned model-id list.** In `.claude/skills/_shared/delegation-harness.md`,
  add a new section `## (f) Sanctioned delegation model IDs` with a small markdown table listing the
  ONLY sanctioned deepseek model-id spellings (as they appear in `--model` flags and prose):
  `deepseek/deepseek-v4-pro`, `deepseek/deepseek-v4-flash`, and their bare forms `deepseek-v4-pro`,
  `deepseek-v4-flash`. One row per id, in a `` `id` `` code cell the lint can regex (mirror the §(e)
  budget table's cell shape). Add a one-line note that this is the single source of truth for the
  `model-id-agreement` scaffold_lint check.

- [ ] **T6 — `model-id-agreement` check (`scripts/scaffold_lint.py`).** Add a check that mirrors
  `check_budget_agreement`/`_sanctioned_pairs` (recon §6, `scaffold_lint.py:409-455`): parse the
  §(f) table for the sanctioned id set; scan the SAME `_scan_file_set()` population (AGENTS.md +
  `.claude/skills/**` + `.claude/agents/*` + `.opencode/agents/*`) for any `deepseek[-/]v4[-\w]*`-shaped
  token; flag any token NOT in the sanctioned set (typo, version drift, `deepseek-v3`, a bare
  `deepseek-v4` with no tier, etc.). **Membership MUST be an EXACT-string match** of the captured
  token against the sanctioned set (like `budget-agreement`'s `pair in sanctioned` tuple-membership —
  NOT a substring check, or `deepseek-v4-pro-plus` would wrongly pass). Wire it
  into `collect_findings`. Add its test to `scripts/test_scaffold_lint.py` (a sanctioned id passes; an
  injected `deepseek-v4-preview` in a fixture is flagged; the §(f)-table-missing case is reported like
  `budget-agreement`'s "§e table not found"). Exclude `.claude/worktrees/` from the scan if
  `_scan_file_set` doesn't already (recon Surprise 1). `scaffold_lint.py` is golden-source-only (NOT
  in the manifest) — correct; the check polices the scaffold's own prompt surface.

## Group 3 — #5: concurrent COMPLEX verifier passes (verify prose)

- [ ] **T7 — Concurrent launch.** In `.claude/skills/openspec-verify-change/SKILL.md`, update the
  COMPLEX pass sequencing prose (recon §5 anchors ~`:55`, `:68-84`, `:187`, `:280-282`) so that on a
  COMPLEX change the orchestrator **MAY** launch both the pro behavioral pass AND the flash lens pass
  concurrently (both `run_in_background: true` on the frozen tree — the harness already supports it;
  default to concurrent, fall back to sequential if the harness cannot), waits for BOTH exit-sentinels,
  THEN applies the EXISTING hard-gate rerun-failed-and-after recovery (unchanged) — only the
  NEEDS-REVISION fix→re-run serializes. (Matches the spec delta's "MAY be launched concurrently".) Match the MODIFIED
  `verify-multimodel-gate` delta. MEDIUM (single pass) is unchanged. Keep each pass's
  `opencode_delegate.py` post-processing call (OW-7) intact — just note both are read after both
  complete.

## Group 4 — #4: explore→propose slug-match warning (propose prose)

- [ ] **T8 — Near-match warning.** In `.claude/skills/openspec-propose/SKILL.md` step 2 (recon §4,
  "Relocate explore artifacts (D8)", ~`:44-56`), after the exact-match `[ -d "plans/<name>" ]` check,
  add a warning: if NO exact match, list `plans/*/` and flag any near-match kebab-case slug (simple
  token-overlap — shares ≥1 hyphen-delimited token, or is Levenshtein-close) so the operator gets an
  explicit "did you mean `plans/<other-slug>/`? (it has an explore-brief + premise-review that will
  be orphaned)" prompt instead of the current silent skip. A few lines of inline shell/glob logic; no
  new script.

## Group 5 — Gate + ratchet closure

- [ ] **T9 — Green gate + ratchet.** `ruff check --fix` + `ruff format` on edited `.py`
  (`checks.py`, `scaffold_lint.py`, the two test files). `bash scripts/check.sh` → exit 0. Run
  `/usr/bin/python3 scripts/checks.py --check spec-delta-structure` on THIS repo and confirm the two
  open changes' deltas (this change's own MODIFIED deltas + any other) report clean (fix any
  `shall-not-first-line` it surfaces — dogfood). In `knowledge/ratchet-log.md`, mark
  `medium-change-spec-delta-unvalidated` CLOSED with the `check` disposition (the
  `spec-delta-structure` detector), dated 2026-07-14. Do NOT commit. Report: the exact `check.sh`
  result, the `spec-delta-structure` self-run output, and confirmation that `model-id-agreement`
  passes on the live tree.
