# Review log — outstanding-work-collector

Concise per-round record (full reviewer transcripts are not retained here — they bloat the log and
distract later reviewer runs). Reviewer: `openspec-reviewer` (deepseek-v4-pro) via `opencode run`.

## Round 1 — proposal.md — PASS
- Verdict: PASS · PREMISE: AGREE · zero 🔴 · no drift from explore-brief.
- 🟡/💡 (all design-phase, non-blocking): completeness-absolute wording; in-code TODO listed as a
  guaranteed source; registry-location imprecision (`checks.toml` vs `_REGISTRY`); name the skill;
  closed-convention undefined; duplicate-scope unspecified; per-repo config surface; output-format.
- Disposition: applied the cheap precision fixes to proposal (qualify completeness, demote TODO,
  correct registry wording, name `outstanding-work-review`); carried the genuine design decisions
  into the proposal's design-inputs list. Frozen on zero 🔴 + AGREE. No re-review (nothing blocking).

## Round 2 — design.md — NEEDS REVISION
- Verdict: NEEDS REVISION · PREMISE: AGREE · **1 🔴** + 4 🟡 + 4 💡.
- 🔴 D1: registered the fact as `kind="custom"`, incompatible with the engine (`_run_custom` expects a
  subprocess `command` + emits `.txt`; `_custom_checks` hardcodes `family="check"`). Must be
  `kind="delegate"` with a `_run_delegate` arm + a `scripts/outstanding.py` module (like
  `scope`/`index-coverage`). Verified against `scripts/checks.py` before accepting.
- 🟡: config keys mis-placed (`duplicate_scan_dirs`/`untriaged_max_age_days` belong under
  `[knowledge_lint]`); D8 untriaged-age impl path unspecified; D3 extraction rules underspecified; new
  `knowledge_lint` funcs not stated as wired into `collect_findings()`. 💡: dual-output mechanics;
  `lint:dup-ok` scope; `checks.toml` absent; D4 scan scope.
- Disposition: rewrote D1 → delegate + `outstanding.py`; split config by consumer (D10); pinned D3
  parse rules; pinned D8 shared-module + git-date age proxy; wired the funcs into `collect_findings`.

## Round 3 — design.md (revised) — PASS
- Verdict: PASS · PREMISE: AGREE · zero 🔴. D1 dispatch fix confirmed against `checks.py`.
- 🟡 (precision, non-blocking): `lint:dup-ok` is window-scoped, not a "mirror" of line-scoped
  `lint:planned`; D8 shared import needs an API surface; `_autodetect_defaults` omits `outstanding`.
  💡: D5 "engine writes" wording.
- Disposition: all applied (explicit dup-ok mechanism; `extract_untriaged(root, config) -> list[dict]`
  API; `"outstanding": True` in `_autodetect_defaults`; D5 "engine provides out_path, delegate fills").
  Frozen.

## Round 4 — specs (delta) — re-run
- First specs review produced no usable verdict (reviewer drowned in the then-1000-line review-log.md
  and ended mid-context-gathering). Re-ran with a bounded prompt (specs + design only; standard
  format). Verdict recorded below on completion.

### Round 4 verdict — specs (re-run) — PASS
PASS, zero 🔴. 2 🟡 (openspec/specs exclusion scenario; roadmap.md path) + 1 💡 (git→mtime scenario) — all applied. Specs frozen.

## Round 5 — tasks.md — PASS
PASS, zero 🔴. 3 🟡 clarifications (5.1 provenance assertion; 5.4 split test_checks vs test_facts; 1.2 mark in-code TODO optional) — all applied. Reviewer confirmed full D1-D10 + spec coverage, apply-phase bounds, and correct ordering. Tasks frozen.

## Round 6 — verify (behavioral review + multi-model passes) — READY
- **Orchestrator self-review:** suite green (ruff + format + full pytest incl. scaffold_lint SEAL and
  live-tree knowledge_lint gate). Eyeballed real output on the live tree and on synthetic fixtures —
  D2 (never-crashes/UNPARSEABLE), D3 (bullet+table), D4 (untriaged↔triaged + per-repo pattern),
  D6 (plans/archive excluded), D7 (duplicate region-merge = one finding/file, research+specs excluded,
  dup-ok/lint:keep suppression, closed-unpruned), D8 (untriaged-age git→mtime) all confirmed.
- **Multi-model passes (both READY, zero defects):** `deepseek/deepseek-v4-pro` and
  `deepseek/deepseek-v4-flash` via `opencode run --agent openspec-verifier`. Both independently
  re-ran the suite, eyeballed real output, and exercised the same D2–D8 edge cases. Neither found a
  behavioral defect.
- **Orchestrator findings the passes did not surface (non-blocking, SHOULD-fix — recorded in notes.md
  fields 4–5):** (1) open-work provenance uses absolute paths while `extract_untriaged` uses relative;
  (2) `_enumerate_prose_files` uses `rglob` (recursive) while the spec/tasks say "top-level `plans/*.md`"
  and the `_check_closed_unpruned` plan scan is top-level `glob` only — the two `plans/` scans disagree.
  Nothing overruled from the verifier passes (they reported no defects); these are additive quality items.
- **Verdict: READY for archive** — zero CRITICAL; two WARNING quality/consistency items surfaced to the
  operator. No fix re-delegated during verify (operator to decide fix-now vs. fold-to-follow-on).

## Round 7 — post-fix re-verify (provenance warning) — READY
- Operator elected to fix WARNING #1 (absolute→relative provenance) before archive. Fix re-delegated to a
  fresh `deepseek/deepseek-v4-flash` apply-executor (real agent confirmed, no fallback): added `_rel(root,
  path)` helper; all 8 open-work `source` assignments now repo-relative; new locking test
  `test_open_work_source_is_repo_relative_not_absolute`.
- **Re-verified:** orchestrator self-review green (suite + eyeball — live output now repo-relative,
  consistent across both buckets). Both multi-model passes re-run on the fixed tree:
  `deepseek/deepseek-v4-pro` READY / no defects, `deepseek/deepseek-v4-flash` READY / no defects.
- WARNING #2 (`plans/` recursive vs top-level) remains an open operator decision — non-blocking either way.
- **Verdict: READY for archive.**
