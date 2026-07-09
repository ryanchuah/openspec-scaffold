# Handoff — align `plans/` scope (keep recursive) across gather, lint, and spec

**For the next agent. Self-contained. Follow-on to the shipped `outstanding-work-collector`
change, archived at `openspec/changes/archive/2026-07-09-outstanding-work-collector/`.**

## Decision already made — do NOT re-litigate

The outstanding-work gather (`scripts/outstanding.py`, `_enumerate_prose_files`) enumerates
`plans/` **recursively** (`plans_dir.rglob("*.md")`, excluding `plans/archive/`). The operator
decided (2026-07-09) to **keep the recursive behavior**: this repo genuinely nests live plans in
subdirectories (`plans/day-to-day-tooling/`, `plans/succession-hardening/`,
`plans/sync-deletion-manifest/`), so recursive is what keeps the snapshot honest — its whole
promise is "never silently skip a source."

## Problem — three places disagree on what "a plan" is

1. **Gather** — `scripts/outstanding.py` `_enumerate_prose_files` — **recursive** (`rglob`, excludes
   `plans/archive/`). ✅ This is the desired behavior; **leave it as-is**.
2. **Spec text** — design D6 / tasks §1.3 (archived) *and* the promoted capability spec
   `openspec/specs/outstanding-work-view/spec.md` (requirement `plans-live-vs-archived-convention`)
   say **"top-level `plans/*.md`"**. ❌ Stale — must be updated to describe recursive enumeration.
3. **Lint** — `scripts/knowledge_lint.py` `_check_closed_unpruned` scans **top-level only**
   (`plans_dir.glob("*.md")`). ❌ Inconsistent: a *nested* plan marked DONE/COMPLETE is listed as
   live work by the gather but is never flagged for archival by the lint.

## The fix

- **`scripts/knowledge_lint.py` — `_check_closed_unpruned`:** change the `plans/` scan from
  `plans_dir.glob("*.md")` to `plans_dir.rglob("*.md")`, excluding `plans/archive/**` (mirror the
  gather's exclusion in `_enumerate_prose_files`). Keep the `README.md` exemption and the
  `<!-- lint:keep -->` opt-out.
- **`openspec/specs/outstanding-work-view/spec.md`:** update the `plans-live-vs-archived-convention`
  requirement/scenarios so the wording says the gather enumerates plans **recursively under `plans/`,
  excluding `plans/archive/`** (not "top-level `plans/*.md`").
- **Tests:**
  - `scripts/test_outstanding.py` — add/extend a test asserting a **nested** non-archive plan
    (e.g. `plans/sub/foo.md`) IS enumerated point-only, while `plans/archive/**` stays excluded.
    (The existing `test_plans_archive_excluded_top_level_listed` only plants top-level + archive
    files, so it passes under either `glob` or `rglob` — it does not pin the recursive behavior.)
  - `scripts/test_knowledge_lint.py` — add a test asserting a **nested** closed plan
    (`plans/sub/shipped.md` with `**Status:** DONE`) IS flagged by `_check_closed_unpruned`, and NOT
    flagged under `<!-- lint:keep -->`.

## Acceptance

- `scripts/check.sh` green end-to-end (ruff + `ruff format --check` + full pytest incl. the
  `scaffold_lint` SEAL and the live-tree `knowledge_lint` gate).
- `python3 scripts/facts.py --check outstanding` still lists nested live plans; a nested closed plan
  now trips `_check_closed_unpruned`.
- Gather, lint, and the canonical spec all agree: **recursive under `plans/`, excluding
  `plans/archive/`.**

## Scope / process notes

- `scripts/outstanding.py`, `scripts/knowledge_lint.py`, and their test files are **scaffold-managed**
  (`scripts/scaffold_manifest.txt`). Edit them **only here in openspec-scaffold**; downstream
  propagation to `extrends` + `psc-monitor` via `scripts/sync_scaffold.py` is **operator-gated** and
  out of scope for this change itself.
- **Tier:** likely **SMALL** (a scoped, mostly-mechanical alignment: one `glob`→`rglob`, a spec
  wording fix, two tests). Confirm the tier + plan with the operator before executing per AGENTS.md; if
  the spec change feels load-bearing, treat as MEDIUM.
- **Full rationale / as-built context:** archived `notes.md` fields 4–5 at
  `openspec/changes/archive/2026-07-09-outstanding-work-collector/notes.md`, and the parked pointer in
  `knowledge/questions/outstanding-work-collector-follow-ons.md`.
