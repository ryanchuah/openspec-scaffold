# lean-boot-context — notes

MEDIUM-tier change. Covers two priorities from `ai-docs/explore-agent-context-infra-2026-06-18.md`:
- **P3 (§7.3)** — bound the mutable Layer-3 state files by tightening conventions in their
  canonical home + enforcing at archive, propagated to both downstream repos. **Forward-only**
  (no risky retroactive summarization by the flash executor); the win materializes as changes
  archive. One exception: a single *verbatim* mechanical fix of extrends' current over-cap
  STATUS entry.
- **P2 (§7.2)** — relocate psc-monitor's ~412-line inlined AGENTS.md reference appendix into
  on-demand `ai-docs/` files (psc-monitor only).

## Scope caveat (flagged deliberately)
OpenSpec scopes this change's `allowedEditRoots` to the scaffold repo, but tasks 3–8 reach into
the sibling repos `psc-monitor` and `extrends`. This is intentional and matches the established
scaffold→downstream workflow: P3 propagation (task 3) is a sanctioned **script run**
(`sync_scaffold.py`), and the P2/extrends edits are made fully prescriptive (verbatim copy-move +
exact snippets) to keep them flash-safe. Downstream commits use `git commit --no-verify` per the
propagation convention ([[project_propagation_refs_gate]]).

## Acceptance criteria
1. **Canonical single-sourcing:** the three new state-file rules live ONLY in
   `AGENTS.md §"State, write discipline…"` (P3); the archive-executor **cites** that section, does
   not restate the numeric budgets. The new decisions.md rule has a `CANONICAL:` marker.
2. **Executor agreement:** `test_executor_body_agreement.py` passes after the archive-executor edits.
3. **Convergence + refs:** for BOTH downstream repos, `sync_scaffold.py --check` and `--check-refs`
   are green; `test_sync_scaffold.py` passes.
4. **No data loss (P3):** the archive-executor enforcement includes the "verify the change archive
   holds the rationale before trimming STATUS prose" safety check; task 4 moves the over-cap
   extrends entry **verbatim** (no summarization).
5. **psc-monitor appendix relocated losslessly:** all four `ai-docs/` files exist and non-empty;
   EVERY appendix section has a recorded disposition (task 6.5) — promoted to Project context,
   moved verbatim to an `ai-docs/` file, or explicitly dropped-as-redundant — with NO load-bearing
   constraint silently deleted; no appendix heading remains in `AGENTS.md`; `AGENTS.md` ≈ 330–360
   lines; every appendix `AGENTS.md §` citation found in 5.1 is repointed to a real destination (no
   citation maps to a dropped section); schema unique-index detail + full API routes table survive
   verbatim.
6. **Sync mechanism untouched:** no edits to `sync_scaffold.py` or `scaffold_manifest.txt`; the new
   psc-monitor `ai-docs/` files are NOT added to the manifest (they are project-unique); the
   preserved-tail span-merge still works (psc-monitor `--check` green after 7.3).

## As-built deviations (apply phase, 2026-06-18)
- **Slice A (P3, tasks 1–4) ran on the opencode DEFAULT agent, not the apply-executor role.** Cause:
  invoked with `--dir /home/pang/Projects` (parent) for cross-repo reach, which broke `.opencode/agents/`
  discovery (`agent "apply-executor" not found. Falling back to default agent`). It still ran
  deepseek-v4-flash with a detailed brief; all deterministic gates pass. Operator accepted Slice A
  as-is. Slice B (P2) runs with `--dir psc-monitor` so the apply-executor role loads.
- **Sync >300-line guard bumped to 350** (`scripts/sync_scaffold.py`, not manifest-synced): propagating
  the new state rules pushed lean `extrends/AGENTS.md` 299→302 lines, tripping the "long file, no
  tail-separator" guard. Operator chose to raise the threshold and remove the executor's `---`
  workaround rather than keep the band-aid.
- Cosmetic fixes to the synced span (re-propagated to both repos): decisions-rule paragraph
  re-indented; 3c executor bullet de-double-bolded.

## psc-monitor citation repoint map (Slice B as-built)
Appendix sections → destinations:
- `## Database schema` + `## Matcher logic` → `ai-docs/schema-reference.md` (72 ln, verbatim; `uniq_active_appt_self_link` preserved)
- `## API` → `ai-docs/api-reference.md` (32 ln; ~20-row routes table preserved)
- `## Repository layout` → `ai-docs/repo-layout.md` (73 ln)
- `## Production domain layout` + `## Setup`/`.env` + `## Daily operations` + `### Loading historical snapshots` + entire `## Testing` → `ai-docs/ops-runbook.md` (130 ln)
- `## Known issues / technical debt` + `## Forward plans` → `ai-docs/project-reference.md` (36 ln, catch-all)
- `## What is this?`, `## Stack` → DROPPED (duplicated `openspec/config.yaml` `context:`; not cited)
- `## Dependency source of truth`, `## Core code patterns`, `## Do not do` → PROMOTED into AGENTS.md `## Project context` (pitfalls + constraints: no sudo, no load-to-memory, no commit-without-pytest, no TRUNCATE/DROP without guard)

Citations repointed (refs gate green): `ai-docs/decisions.md`, `docs/00-codebase-map.md`, `docs/07-errors.md`, `docs/08-performance.md`, `docs/09-synthesis.md`, `plans/a2-backup-script.md`, `plans/ci.md`, `plans/home-server-deploy.md`, `plans/open-issues.md` → the new `ai-docs/` files.

AGENTS.md: 707 → **317 lines** (appendix removed; `## On-demand references` table added). All gates green.

### Verify-time follow-ups flagged by executor
- `plans/historical-reports.md` lines 185/199/217/228 still reference `AGENTS.md` (as a file-update target in a completed plan, NOT `§`-citations to removed sections) — left as-is; `--check-refs` confirms not dangling. Confirm at verify whether to repoint.
- AGENTS.md landed at 317 lines (under the ~330–360 estimate) — more reduction than projected; harmless. (Now 321 after verify restored 4 bullets — see Verify field 3.)

## Verify (2026-06-18)

**1. Verdict:** READY for archive. Self-review (primary) found 2 defects → fixed → re-clean; then deepseek-v4-pro pass = READY (no defects), deepseek-v4-flash pass = READY (no defects). Simplicity gate PASS; security gate N/A (no auth/cred/network/external-API surface).

**2. Live output eyeballed (behavior, not counts):** Read the rendered new psc-monitor `AGENTS.md` `## Project context` + `## On-demand references` table and the 5 new `ai-docs/` files — the appendix relocation reads coherently and is **lossless**: the schema unique-index `uniq_active_appt_self_link`, the full API routes table, the `.env` table, the matcher tier rules, and every code pitfall are present in the new files; the dropped `## What is this?`/`## Stack` are covered by `openspec/config.yaml` `context:`. The On-demand pointer targets (`plans/`, `plans/open-issues.md`) exist. extrends `STATUS.md` now holds the 3 most-recent change entries with the oldest moved **verbatim** to `ai-docs/archive/status-log.md`. The 3 new state rules render correctly in `AGENTS.md §"State…"` and the archive-executor `3a/3b/3c` bullets **cite** that section (byte-identical across `.claude`/`.opencode`). All scaffold tests green; all four convergence/refs gates green.

**3. Defects found + how fixed (who):** Both surfaced by the **primary self-review** (the pro/flash passes came back clean *after* the fixes). No re-delegation/Sonnet needed — both fixes were within the primary's allowed scope and are disclosed:
- **(A) Test regression** — the operator-directed guard bump (`sync_scaffold.py` 300→350) broke `test_300_line_no_tail_aborts` (fixture was ~320 lines, no longer > guard). Fixed **inline by primary** (the one-line code exception): fixture `range(310)→range(360)` + comment/name/docstring → 350. Suite now green (sync 32 / convergence 28 / executor-agreement 2).
- **(B) P2 content loss** — the appendix relocation dropped 3 load-bearing items not covered by config.yaml: the Postgres `TEXT[]` empty-array pitfall, the `normalise()`/typeahead-uses-raw behavior, and the `TRUNCATE`/`DROP` confirmation-guard rule (+ "No Docker/Celery"). Restored **inline by primary** as a quick doc edit into psc-monitor `AGENTS.md §"Project context"` (now 321 lines, still < 350).

**4. As-built deltas (not in frozen tasks.md):** (a) the `sync_scaffold.py` 300→350 guard bump + its test update — arose because propagating the new rules pushed lean `extrends/AGENTS.md` over 300 lines (already in the as-built section above); (b) Slice A ran on the opencode **default-agent fallback** (above); (c) task 6.5 created a **5th** ai-docs file `project-reference.md` (catch-all for Known issues + Forward plans) beyond the 4 named in tasks 6.1–6.4.

**5. Forward-looking items to fold into `ai-docs/open-questions.md` (and where noted, `decisions.md`) at archive:**
- **Enforcement is untested against a live archive.** The 3 state-bounding rules are **forward-only** — existing over-budget entries are NOT retroactively trimmed; they bound at each repo's *next* archive. Watch the next real archive to confirm the archive-executor actually applies the ≤150-word STATUS budget, the open-questions parking+pointer-stub, and the decisions Date/Status+≤300-word cap.
- **extrends STATUS remaining entries unchecked.** Only the single over-cap entry was moved (verbatim, by design); the 3 retained entries' word budgets were not enforced this change — they bound at next archive.
- **Sync guard `350` is a new magic number.** If the synced span keeps growing, lean repos could approach 350 again → revisit the threshold or adopt an explicit empty-tail convention for lean repos. (Record rationale in `decisions.md`.)
- **`plans/historical-reports.md`** keeps 4 plain `AGENTS.md` file-references (not `§`-citations; refs gate confirms not dangling) — decide whether to repoint.
- **Minor intentional drops** from the psc-monitor appendix (target-customer market sizing; `nameparser`/`rapidfuzz` lib names; the `requirements.txt`-deleted historical note) — judged low-value/discoverable; recorded here in case they're wanted back.

**Still owned by archive:** reconcile `STATUS.md` (a "Latest change" entry for `lean-boot-context`) + `ai-docs/decisions.md` (the P2 relocation + P3 bounding + the 350-guard decisions) + `ai-docs/open-questions.md` (fold field-5 items) in the **scaffold**; decide how the two downstream repos record this propagation (per the scaffold-source-of-truth convention); **no delta-spec promotion** (this MEDIUM change has no `specs/`); commit all three repos (still local/uncommitted; downstream commits use `--no-verify`).
