# psc-monitor AGENTS.md appendix relocation plan

Date: 2026-06-18  
Read-only exploration — no target-repo files modified.

---

## Task 1 — psc-monitor/AGENTS.md section map

Total: **707 lines**.

### Span/role taxonomy

| Role | Description |
|---|---|
| (i) Mandatory preamble | Synced span1: `> **MANDATORY` → just before `## Project context` |
| (ii) Roles/workflow | Synced span2: `## Roles` → end of `## After reading this file` |
| (iii) Project context | Per-repo preserved block |
| (iv) Appendix | TAIL: everything from first `---` after `## After reading this file` onward |
| (v) Title | Line 1 — per-repo preserved |

### Section map

| # | Section | Lines | ~Size | Category |
|---|---|---|---|---|
| 1 | `# psc-monitor` (title) | 1 | 1 | (v) title — preserved |
| 2 | `> **MANDATORY...` preamble blockquote | 3–34 | 32 | (i) synced span1 |
| 3 | `## Cross-agent compatibility` | 36–64 | 29 | (i) synced span1 |
| 4 | `## Project context` | 66–83 | 18 | (iii) preserved — **relocation target updates here** |
| 5 | `## Roles` | 84–120 | 37 | (ii) synced span2 |
| 6 | `## OpenSpec workflow` | 122–145 | 24 | (ii) synced span2 |
| 7 | `## Change tiers` | 148–173 | 26 | (ii) synced span2 |
| 8 | `## State, write discipline, and the archive-as-handoff rule` | 175–211 | 37 | (ii) synced span2 |
| 9 | `## Working process` | 213–270 | 58 | (ii) synced span2 |
| 10 | `## Web research convention` | 272–281 | 10 | (ii) synced span2 |
| 11 | `## After reading this file` | 282–292 | 11 | (ii) synced span2 — terminal anchor |
| 12 | `---` tail separator | 293–295 | 3 | tail boundary — preserved by sync |
| 13 | `# Project reference (durable — stable across sessions)` | 296–707 | **412** | **(iv) inlined reference appendix — relocation target** |

### Appendix subsections (lines 296–707)

| Sub-section | Lines | ~Size | Always-needed? |
|---|---|---|---|
| `## What is this?` | 298–309 | 12 | No — config.yaml `context:` already covers it |
| `## Dependency source of truth` | 313–315 | 3 | Yes (2-liner; stays) |
| `## Production domain layout` | 319–325 | 7 | No — ops task only |
| `## Stack` | 329–342 | 14 | No — fully covered by config.yaml `context:` |
| `## Repository layout` | 344–415 | 72 | No — on-demand orientation |
| `## Setup` + `### .env variables` | 417–457 | 41 | No — setup/onboarding only |
| `## Daily operations` | 459–484 | 26 | No — ops task only |
| `### Loading historical snapshots` | 486–509 | 24 | No — ops task only |
| `## Database schema` | 511–546 | 36 | No — on-demand for DB work |
| `## Matcher logic` | 548–581 | 34 | No — on-demand; already cites code + docs |
| `## API` | 583–611 | 29 | No — on-demand for API work |
| `## Core code patterns` | 613–640 | 28 | Partly — pitfalls (JSONB, postcode, `?` placeholders) are load-bearing |
| `## Testing` | 642–662 | 21 | Partly — `autocommit=True` pitfall is load-bearing |
| `## Known issues / technical debt` | 664–675 | 12 | No — already points to `plans/open-issues.md` |
| `## Forward plans` | 677–697 | 21 | No — pointers only; discoverable |
| `## Do not do` | 699–707 | 9 | Partly — 2 unique items; rest duplicate always-loaded sections |

**Appendix lines that are genuinely always-needed (load-bearing orientation):**

- `## Do not do` items 1 and 4: "Do not use `sys.path.insert` hacks" and "Do not use `ON COMMIT DROP` on temp tables in test code" — unique constraints, not covered in synced spans.
- `## Core code patterns`: the `?`→`%s` translation pitfall, JSONB/`json.loads` trap, and postcode normalisation rule — these bite agents silently in every backend change.
- `## Testing`: `autocommit=True` on `pg_conn` and the `DATABASE_URL` override at top of `conftest.py` — both cause mysterious test failures if violated.

Everything else in the appendix is valid reference content but only needed when the agent is in the specific area.

---

## Task 2 — relocation plan

### Principle

Extrends model: `## Project context` carries the project's unique hard constraints (~30 lines), config.yaml carries the prompt-injection summary, and `ai-docs/` carries on-demand reference. No tail.

### Split

#### A. Stay in AGENTS.md — expand `## Project context`

The preserved `## Project context` block (currently 18 lines) should absorb:
- The 2 unique items from `## Do not do` (sys.path.insert, ON COMMIT DROP)
- The `## Dependency source of truth` 2-liner (pyproject.toml only)
- A brief note on the core code pitfalls currently buried in `## Core code patterns`:
  - `_PGConn` translates `?`→`%s`; never f-strings in SQL
  - JSONB columns auto-deserialise; do NOT call `json.loads()` on them
  - Postcodes: `.upper().replace(" ", "")` both sides before compare
  - `pg_conn` is `autocommit=True`; `ON COMMIT DROP` silently drops temp tables immediately

Updated `## Project context` becomes ~30 lines (vs 18 now). The existing hard constraints (Python 3.13, raw SQL, no sudo, data scale) stay where they are. The reference to "the `# Project reference` body at the end of this file" changes to "the on-demand `ai-docs/` files listed in `## On-demand references`."

#### B. New tail: `## On-demand references` (~15 lines)

Replace the 412-line `# Project reference` body with a minimal pointer section:

```markdown
---

## On-demand references

Load the relevant file when you need it — do not preload.

| What | File |
|---|---|
| Full schema (7 tables, columns, indexes) + matcher logic | `ai-docs/schema-reference.md` |
| API routes table | `ai-docs/api-reference.md` |
| Repository layout (directory tree) | `ai-docs/repo-layout.md` |
| Dev setup, .env vars, daily ops make targets, backfill | `ai-docs/ops-runbook.md` |
| What is this product, target market, differentiators | `openspec/config.yaml` (`context:`) |
| Forward plans index | `plans/` |
| Known issues | `plans/open-issues.md` |
```

This is ~15 lines. Combined with the expanded `## Project context` (~30 lines) and the unchanged synced spans (~290 lines), the resulting AGENTS.md is **~335 lines** — a 53% reduction from 707.

#### C. New `ai-docs/` files

**`ai-docs/schema-reference.md`** (~70 lines)
- Source: `## Database schema` (lines 511–546) + `## Matcher logic` (lines 548–581)
- Contents: 7-table schema with key columns/indexes, signal-counting matcher table, tier rules, backfill passes
- When to load: any DB work, any change touching matcher/alerts/watchlist

**`ai-docs/api-reference.md`** (~32 lines)
- Source: `## API` (lines 583–611)
- Contents: base URL, auth rules, full routes table with method/path/notes
- When to load: any API or frontend work

**`ai-docs/repo-layout.md`** (~75 lines)
- Source: `## Repository layout` (lines 344–415)
- Contents: directory tree with file annotations
- When to load: initial orientation; exploring unfamiliar subsystem

**`ai-docs/ops-runbook.md`** (~100 lines)
- Source: `## Production domain layout` (319–325) + `## Setup` + `.env variables` (417–457) + `## Daily operations` (459–484) + `### Loading historical snapshots` (486–509)
- Contents: deployment topology, make targets, .env table, backfill procedure, CSV/zip pipeline notes
- When to load: ops, deployment, or pipeline-debugging tasks

#### D. Drop / consolidate

- `## What is this?` — redundant with config.yaml `context:`; drop entirely.
- `## Stack` table — already in config.yaml `context:`; drop.
- `## Testing` detail (lines 642–662) — the pitfall notes move into `## Project context`; CI instructions fold into `ai-docs/ops-runbook.md` or `ai-docs/schema-reference.md` test section.
- `## Known issues / technical debt` — already just a pointer to `plans/open-issues.md`; drop.
- `## Forward plans` — drop; on-demand references table covers this concisely.
- `## Do not do` — drop as a section; unique items migrate into `## Project context`.

#### E. No changes needed to `openspec/config.yaml`

The existing `context:` block already covers: project purpose, tech stack, testing philosophy, data scale, web research note. Adding the target-market detail ("UK accountancy firms, £50–150/month") is optional but low-value for prompt injection. Recommended: leave config.yaml as-is.

---

## Task 3 — extrends comparison and sync impact

### Extrends arrangement

`extrends/AGENTS.md`: exactly 299 lines, **zero tail** — ends at `## After reading this file`.

`extrends/openspec/config.yaml` `context:` block (~10 lines): project name, purpose (1 sentence), tech stack (1 line), testing philosophy (2 lines), scope rule (1 line), style (1 line), web research (1 line). Tight — just what fits usefully in a prompt-injection block.

`extrends/ai-docs/` files: decisions.md, open-questions.md, parked-follow-ons.md, fast-track-workflow.md, delegation-harness.md, research-fetch-convention.md, improvement-roadmap.md, opencode-delegation-notes.md, workflow-lessons.md. No "reference" files — extrends is a smaller, CLI-only project with no schema or API surface, so domain knowledge lives in code.

**Target shape for psc-monitor:** same as extrends (no "reference" files needed in extrends because it has no complex schema/API) but psc-monitor DOES have a non-trivial schema, API, and ops surface. The 5 new `ai-docs/` files above are the psc-monitor equivalent of extrends' reliance on the code itself.

### Sync mechanism impact

**`sync_scaffold.py` — no changes required.**

The tail detection at line 87–95 of sync_scaffold.py is:
```python
tail_match = re.search(r'\n(---\s*\n|# \w)', target_text[after_start:], re.M)
if tail_match:
    tail = target_text[after_start + tail_match.start():]
else:
    if len(target_text.splitlines()) > 300:
        raise ValueError("target AGENTS.md is long but no tail-separator found")
    tail = ''
```

After the relocation, psc-monitor's AGENTS.md will still have a `---` separator after `## After reading this file` (the new `## On-demand references` section starts with `---`). The tail detection finds that `---`, captures everything from there onward as the tail, and preserves it verbatim. The algorithm is unchanged; the tail is just ~15 lines instead of ~412. The 300-line guard does not fire (the slimmed file is ~335 lines).

**`scaffold_manifest.txt` — no changes required.**

The 5 new `ai-docs/` files are psc-monitor-specific (not scaffold-managed). They should NOT be added to the manifest — they're project-unique domain files, not scaffold boilerplate. The manifest syncs shared workflow files only.

**`--check` mode — no changes required.** The AGENTS.md span-replace check still works identically; the preserved `## Project context` and tail are different content but same mechanism.

**`--check-refs` — impact assessment.**

The refs gate (check_references) verifies:
1. `ai-docs/*.md` path citations in synced files exist in the target repo.
2. `AGENTS.md §"..."` and `ai-docs/* §"..."` citations anywhere in tracked markdown resolve.

**Rule (1) impact:** The new `## On-demand references` table in the tail cites the 4 new `ai-docs/` files. Since the tail is PRESERVED (not synced), it is not scanned by rule (1) — rule (1) only applies to synced files (AGENTS.md spans and synced ai-docs/*.md). The new AGENTS.md's updated `## Project context` (preserved) also cites the new files — same: preserved text, not in the synced spans. Synced span content does NOT cite the new files. **Net: no new rule (1) violations.**

**Rule (2) impact:** Any tracked markdown file anywhere in psc-monitor that currently uses `AGENTS.md §"Database schema"`, `AGENTS.md §"Matcher logic"`, `AGENTS.md §"API"`, etc. would become dangling after those sections are removed. These headings currently exist as valid anchors; removing them without repointing citations breaks the refs gate.

**Pre-implementation action required:** Run `grep -r 'AGENTS.md §' /home/pang/Projects/psc-monitor/` (excluding `openspec/changes/`, `ai-docs/archive/`, `docs/reviews/`) to enumerate all `§`-citations targeting the appendix sections. Repoint any found to the new `ai-docs/` files (e.g., `AGENTS.md §"Database schema"` → `ai-docs/schema-reference.md §"<section>"`). The working process CANONICAL markers (`<!-- CANONICAL: model-assignment-matrix -->`, `<!-- CANONICAL: never-record-counts -->`) reference the synced spans (Roles, Working process) — those are unaffected.

**Anchor preservation risk:** The heading `# Project reference (durable — stable across sessions)` is currently a valid H1 anchor. Any `AGENTS.md §"Project reference"` citation would break. Grep should catch this.

---

## Task 4 — recommendation

### Recommended split

**Five new `ai-docs/` files** (totalling ~277 lines of migrated content):

| File | Source (psc-monitor/AGENTS.md lines) | Size |
|---|---|---|
| `ai-docs/schema-reference.md` | 511–581 (schema + matcher) | ~70 lines |
| `ai-docs/api-reference.md` | 583–611 (API routes) | ~32 lines |
| `ai-docs/repo-layout.md` | 344–415 (directory tree) | ~75 lines |
| `ai-docs/ops-runbook.md` | 319–325, 417–509 (domain, setup, ops, backfill) | ~100 lines |

**No new config.yaml changes** — existing `context:` is sufficient.

**Expand `## Project context`** (~18→30 lines):
- Add: `_PGConn` translates `?`→`%s`; never f-strings in SQL
- Add: psycopg2 auto-deserialises JSONB; do NOT call `json.loads()` on results
- Add: postcodes: normalise both sides `.upper().replace(" ", "")` before compare
- Add: `pg_conn` fixture is `autocommit=True`; `ON COMMIT DROP` drops immediately — use plain `CREATE TEMP TABLE`
- Add: `pyproject.toml` is the only dependency manifest
- Update: remove "The detailed reference is the `# Project reference` body at end of this file — keep it" sentence; replace with "Detailed technical reference lives in on-demand `ai-docs/` files (see `## On-demand references`)"

**Replace 412-line tail** with a 15-line `## On-demand references` table pointing to the 4 new files + config.yaml + plans/ + plans/open-issues.md.

**Drop entirely:** `## What is this?`, `## Stack`, `## Testing` (pitfall lines migrate; CI note folds into ops-runbook), `## Known issues / technical debt`, `## Forward plans`, `## Do not do` (unique items migrate).

**Result:** ~707 lines → ~335 lines (53% reduction; close to extrends' 299).

### Sync changes needed

- `sync_scaffold.py`: **none**
- `scaffold_manifest.txt`: **none**
- `--check` / `--check-refs`: **no changes to the tools**, but:
  - Run `grep -rn 'AGENTS.md §"' /home/pang/Projects/psc-monitor/` to enumerate any citations targeting appendix-section anchors
  - Repoint found citations to the appropriate new `ai-docs/` file

### Top risks

1. **Dangling `AGENTS.md §"..."` refs (highest risk).** If any skill file, change artifact, or ai-docs file in psc-monitor contains `AGENTS.md §"Database schema"`, `AGENTS.md §"Matcher logic"`, `AGENTS.md §"API"`, `AGENTS.md §"Core code patterns"`, etc., removing those sections breaks `--check-refs`. The grep above MUST precede the edit. If citations exist, repoint them to the new `ai-docs/` files before removing the appendix sections.

2. **`## Project context` update is per-repo, not synced** — the prose currently says "keep [the Project reference body]." If that line isn't updated it silently contradicts the new structure. Easy to miss if not itemised explicitly in the tasks list.

3. **Content accuracy on extraction** — the new `ai-docs/` files should be verbatim copies of the appendix sections, not rewrites. Rewrites risk silently dropping constraints (e.g., the unique-index `uniq_active_appt_self_link` detail in `## Database schema`). Copy-move, then only prune the 2-line redundancies.

4. **No file existence gate on the preserved tail** — the refs gate's rule (1) only scans SYNCED files (AGENTS.md span content, synced ai-docs). The pointer table in the PRESERVED tail is invisible to rule (1). The 4 new `ai-docs/` files will therefore NOT be automatically checked by `--check-refs` for existence. Mitigation: run a manual existence check as part of the implementation task, or add a note in the change's `notes.md` as an ongoing discipline reminder.
