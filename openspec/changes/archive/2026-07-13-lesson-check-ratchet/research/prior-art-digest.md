# Prior-art and constraints digest — `lesson-check-ratchet`

Subagent-produced input for change design. Dated 2026-07-10. Not authored by the
designer; verify quoted lines against source before relying on them for anything
load-bearing.

---

## 1. `openspec/changes/archive/2026-07-02-mechanize-invariants/`

No `proposal.md`/`design.md` exist in this archived dir — only `notes.md`,
`tasks.md`, `review-log.md` (this change was tasks.md-only MEDIUM per AGENTS.md
tiering; `notes.md` carries the acceptance criteria and decisions).

**What it mechanized:** converted four prose-only scaffold invariants into a
deterministic commit-time linter (`scripts/scaffold_lint.py`) + a live-repo pytest
test, armed the (previously dormant) commit-test gate so the suite actually blocks
commits, and added a sync-time advisory warning for repos missing the
`scaffold_check.py` hook wiring. The four invariants: AGENTS.md span-merge anchor
uniqueness, config.yaml rules-block-last ordering, dangling skill references, and
budget-agreement between the delegation-harness §e table and embedded `timeout -k`
literals.

**Decisions (as recorded in notes.md, no D-numbers assigned in this change — it
uses prose bullet decisions, not D1/D2/etc.):**
- Enforcement wiring: `scaffold_lint.py` is a standalone CLI; enforcement is via a
  live-repo pytest test, gated once `test-gate.sh` is armed. No hook changes.
- Budget check parses numeric `timeout -k G B` pairs (narrow regex) rather than
  reducing embedded blocks to citations, to preserve copy-paste executability.
- `scaffold_lint.py` + its test are **authoring-side, scaffold-only** — never
  manifest-listed, never synced downstream (same status as `sync_scaffold.py`).
- **Manifest tombstone explicitly NOT folded in** — deleting a manifest-listed file
  upstream still orphans it downstream silently; deferred to a later "prune"
  change, to be handled manually per repo.
- The known dangling `openspec-continue-change` skill reference was fixed as part
  of this change because the live-repo lint test couldn't pass otherwise.

**Explicitly rejected/deferred (from "Out of scope" + field-5 forward-looking
items):** portfolio changes 2–4 (instruction repairs, knowledge pruning, delegated-
agent safety) were out of scope; manifest deletion tombstones deferred; adding
`scaffold_lint.py` to the manifest rejected (deliberately golden-source-only);
downstream applicability of `scaffold_lint` checks (dangling-refs, budget-
agreement) left as a "consider later" item, not resolved.

**Did it consider lesson→check conversion?** Not explicitly — this change's own
subject matter (four specific prose invariants → checks) is a **direct precedent**
for the ratchet's mechanism, but the change itself never frames a general "every
finding needs a check" rule. It converts specific named invariants only. No
mention of `knowledge/lessons.md` or a general ratcheting policy anywhere in
`notes.md` or `review-log.md`.

One relevant aside (field 5, forward-looking, routed to
`knowledge/questions/mechanize-invariants-follow-ons.md`): a "cross-cutting
observation... route to the right home at archive" flagged that
`knowledge_lint.py`'s `DEFAULT_RETIRED_PATHS` baked in a personal path from "one
downstream incident" — i.e., an incident became a hardcoded default rather than a
generalized, reviewed convention. This was later resolved by `prune-knowledge`
(2026-07-03) by removing the personal path. This is the closest existing example
of "an incident produced ad hoc enforcement, and it was later cleaned up" — but it
was not treated as an instance of a missing formal ratchet.

---

## 2. `openspec/changes/archive/2026-07-02-deterministic-tooling-layer/`

No `proposal.md`/`design.md` either. The design carrier for this MEDIUM change is
`explore-brief.md` (direction-gated `PREMISE: AGREE`, 2026-07-02); decisions D1–D9
live there. `notes.md` has "Design decisions (beyond the brief's D1–D9)" plus
scope/non-goals/acceptance criteria/verify checkpoint.

**D-numbered decisions (verbatim/paraphrased from `explore-brief.md` §3):**

- **D1 — Same analyses, two delivery shapes.** Report-shaped for the periodic
  audit vs. query-shaped for everyday agents. "No standing generated prose" —
  precomputed structure is high-value because scripts made it; LLM narrations are
  what an auditor must distrust anyway.
- **D2 — Three-level prep pyramid:** free scripts → cheap-model pre-digestion
  (labeled unverified claims/leads, never ground truth) → human/Fable judgment.
- **D3 — Everything check-only; detectors never write.** No `--fix`, no
  formatters in any shared workflow — a scheduled auto-fixer is "a second silent
  writer" that invalidates other agents' stale-file models and poisons diffs.
- **D4 — Data quality is the headline missed category.** "Start with a plain-SQL
  invariant runner (orphans, dupes, nulls, referential integrity, sane ranges) —
  ~5 deliberate checks per repo, grown from incidents; noise stays near zero
  because each check is intentional. Frameworks (pandera/Soda) only if it
  outgrows plain SQL." This is the direct ancestor of `scripts/data_lint.py`.
- **D5 — Dead code/duplication/complexity promoted**, delivered as ONE triage
  campaign, deliberately **not** a CI gate ("gates on these metrics cause endless
  bikeshedding").
- **D6 — First cycle is a full re-audit**; delta-scoping only pays off from cycle
  2 onward.
- **D7 — Scaffold is the home.** Shared scripts are scaffold-managed (synced via
  `sync_scaffold.py`); **per-repo configs/checks/CI wiring are follow-on SMALL
  changes downstream** — i.e., the framework ships centrally, the invariants
  themselves are added per-repo.
- **D8 — Agent-consumption contract:** one discovery surface (task-runner
  namespace + `--list`), bounded output (full JSON to disk, one-line stdout
  summary), tiered drill-down, baseline diffing to kill the "wall" after cycle 1.
- **D9 — Drift-prevention posture:** the tooling itself is scaffold-managed and
  drift-checked by existing sync machinery; generated outputs are disposable
  per-audit artifacts; per-repo prose about the tooling is covered by the
  knowledge-lint change. `knowledge/audit-log.md` was explicitly designed as a
  "lintable one-line registry format... so the knowledge linter can check it for
  free" — a direct precedent for building new tracked registries lint-friendly
  from day one.

**Locked tool-roster line (§4 table):** `Data linting | DIY runner + per-repo
checks/*.sql | D4 above`.

**Conventions locked for `data_lint.py` (from its own module docstring,
`scripts/data_lint.py` lines 1–64, and consistent with D4):**
- Checks live in a **flat directory** (default `checks/`), **no recursion** —
  "matches the ~5-checks D4 scale."
- **One file = one check.** Each file is exactly one `SELECT` returning the
  VIOLATING rows for that invariant.
- **Zero rows returned = pass, any rows returned = fail.**
- Checks run in **sorted filename order**, one at a time; a broken check aborts
  the whole run immediately (infra failure, exit 3) — "a broken check must fail
  loudly, never be silently skipped."
- Backend dispatch by db-url scheme (`postgresql://`/`postgres://` → `psql`
  subprocess with server-enforced `PGOPTIONS
  default_transaction_read_only=on`; `sqlite:///` → stdlib `sqlite3` opened
  `mode=ro` — added later by `data-lint-sqlite-backend`, see §7 below). Read-only
  is a **hard guarantee per engine**, not a convention.
- Exit codes: 0 = clean/not-adopted, 2 = findings, 3 = infra failure (this is the
  scaffold-wide "shared exit-code triple" convention, also documented in
  `deterministic-tooling-layer`'s notes.md: "0 = clean, 2 = findings, 3 = infra
  failure... findings are results, not failures").

**Custom checks / per-repo extension (from `deterministic-tooling-layer` non-
goals + later realized in `scripts/checks.py` via the `checks-facts-split`
change):** the original brief explicitly said "No per-repo configs/wiring —
`audit.toml`, `checks/*.sql`, task-runner `audit-*` targets, CI jobs, dev-extras
tool pins are follow-on SMALL changes in each downstream repo" and "No dedicated
parsers for eslint/tsc/sqlfluff/... — downstream repos wire these as
`[checks.custom.*]` generic commands. Parser surface upstream stays limited to
tools with stable machine output the executor can fixture-test." As actually
implemented in `scripts/checks.py` (post `checks-facts-split` rename
`audit.toml`→`checks.toml`): `[checks.custom.<name>]` is a generic non-parsed
check taking a `command`; "a custom check's presence in `checks.toml` IS the
opt-in" (no separate `enabled` key for customs — the digest of `checks.py` around
line 1151 confirms this, and `checks-facts-split-follow-ons.md` flags the
disable-hint message as cosmetically wrong for that one check kind). D3 caveat
documented in `checks.py`: "the engine cannot prevent a custom `command` from
writing to the repo — keeping a custom check check-only is repo-trusted config by
documented design," not enforced.

**AGENTS.md footprint convention (still current, `AGENTS.md` lines 340–360,
`## Deterministic audit tooling`):** three named surfaces — Detectors
(`checks.py`, gated by preflight, `checks.toml` per-check `enabled`), Snapshots
(`facts.py`, regenerate-on-use, never fails), Ceremony (`run-audit` skill:
`checks.py --report` → triage → `audit_scope.py tag` (sole repo-state mutation) →
append to `knowledge/audit-log.md`). "Audit tooling detects and reports — it never
writes to or fixes code."

---

## 3–8. `knowledge/questions/*-follow-ons.md` and related parked items

All items below are **Parked**, not Active blockers (confirmed against
`knowledge/questions/INDEX.md` lines 25–37 — none of the six files are cited
under an Active heading).

**`mechanize-invariants-follow-ons.md`:** hook-wiring warning is substring-based/
advisory (monitored limitation); `sync_scaffold._read_manifest` is root-
hardcoded (small follow-on to parameterize/dedupe); manifest deletion/tombstone
gap (still open, owned by a future "prune" change, deletions handled manually per
repo); scaffold_lint golden-source-only, "consider... downstream later" (open);
`DEFAULT_RETIRED_PATHS` personal-path item — RESOLVED 2026-07-03.

**`deterministic-tooling-layer-follow-ons.md`:** first-downstream-run risk for
web-verified-only parsers (gitleaks/osv-scanner/deptry/jscpd); `data_lint.py`
live-DB validation pending at the time (now partially addressed — see SQLite
backend below); `data_lint.py` credential hygiene — db-url rides in psql argv,
"downstream convention should prefer PG env vars / pgpass over URL-embedded
credentials" (still open, relevant if a new framework also shells out with
credentials); index_coverage CTE/alias gaps; a deferred structure refactor;
**"knowledge-lint tie-in": a still-unbuilt idea to detect count-recording
patterns ("N tests pass"-style tallies) in tracked docs — this is the closest
existing precedent for "a repeated failure mode should get a mechanized check,"
tracked further in `knowledge-lint-follow-ons.md`** (see below); downstream
wiring of `checks.toml`/`checks/*.sql` per repo (~5 deliberate invariants each,
"grown from incidents per D4") is explicitly still frozen pending an operator
sync go-ahead.

**`knowledge-lint-follow-ons.md`:** confirms the count-recording-pattern check is
**deferred under an explicit YAGNI rationale**: "Deferred (YAGNI until the rake
recurs)" — i.e., the repo has already articulated and consciously rejected (for
now) a "convention violated twice → build the check" rule for this specific case.
Also: "a general known-absent/allowlist mechanism is NOT added (YAGNI holds)" —
a second explicit YAGNI precedent relevant to how eagerly this design should add
new tracked-registry mechanism.

**`checks-facts-split-follow-ons.md`:** all cosmetic/low-priority (mislabeled
INFRA-FAIL-as-failure UX, `findings.json` not written on preflight-abort, custom-
check disable-hint wording, two dead-code/refactor items folded into the
deterministic-tooling-layer refactor follow-on). Notes that a separate hook-
misfire bug (PreToolUse gate firing on non-commit Bash) was fixed by
`shared-lint-layer` (C), not by this change.

**`data-lint-sqlite-backend.md`:** Parked (not a blocker), raised 2026-07-04.
Key content: adding a SQLite backend to `data_lint.py` was correctly identified
as **"a backend abstraction, not an add"** because the load-bearing property is
the server-enforced read-only guarantee (D3), which a SQLite engine must
reproduce via a different mechanism (`mode=ro` URI / `PRAGMA query_only`) "or
it's a safety regression." Also flagged an open premise question: "Scaffold-
generalize (every repo carries a dual-backend runner) vs. keep Postgres-only? —
justify the cost" before generalizing shared surface for one repo's need. **This
question has since been resolved/shipped** — `scripts/data_lint.py`'s current
docstring (confirmed above) documents both Postgres and SQLite backends as
live, dispatched by db-url scheme, each with its own engine-enforced read-only
guarantee. Relevant precedent for the ratchet design: extending a shared,
scaffold-managed detector framework to a new backend/shape was treated as a
MEDIUM, design-first decision gated on "does the generalization cost pay for
itself," not a bolt-on — the same question will likely apply to generalizing
"detector convention" beyond SQL checks.

**`outstanding-work-collector-follow-ons.md`:** parked items from the most
recently archived change (`2026-07-09-outstanding-work-collector`), which is the
direct upstream precedent for "archive-phase / audit-phase finding routing"
touched by this new change. Notable items: a spec/lint alignment gap on
recursive vs. top-level `plans/*.md` scanning (operator chose to keep the as-
built recursive behavior over the written spec — a live example of spec/code
divergence surfacing as a routed follow-on rather than a blocking defect); a
`<!-- lint:dup-ok -->` suppression-marker placement quirk; a config-load
robustness asymmetry between `outstanding.py` (guarded) and
`knowledge_lint.py`'s config reads (unguarded) — relevant if the new ratchet
framework also reads `checks.toml`-style config; a hardcoded `count: 0` in a
delegate-fact report; and a deliberate no-op (`_enumerate_todo_code` returns
`[]` by design, in-code TODO scanning is explicitly out of scope / lowest
priority) — relevant precedent since a lesson-check ratchet could tempt scanning
code comments for unresolved findings.

---

## 9. `knowledge/README.md` — taxonomy

Full taxonomy table (verbatim row set relevant here):

| Type | Question it answers | Home | Load |
|---|---|---|---|
| Decisions | What did we choose, and why? | `knowledge/decisions/INDEX.md` (one line per decision → archive; rationale inline when no archive exists) | on-demand |
| Questions | What is open / parked? | `knowledge/questions/` (Active = boot; Parked + per-item files = on-demand) | split |
| Lessons | What did we learn about how to work? | `knowledge/lessons.md` (single file) | on-demand |
| Reference | Durable facts not in the code (runbook, external-API semantics, empirical findings) | `knowledge/reference/`; `knowledge/audit-log.md` (bounded one-line-per-audit registry ledger, same registry-line discipline as `knowledge/decisions/INDEX.md` — full audit outputs live untracked under `output/checks/<date>/` and are disposable per-audit build artifacts) | on-demand |
| Contracts | What must each subsystem guarantee? | `openspec/specs/` | on-demand |
| Rules | How do agents behave? | `.claude/skills/`, `openspec/config.yaml`, AGENTS standing rules | phase-entry |

**Classification rule (top of file):** "Store knowledge that cannot be recovered
from the source code. Do not store knowledge that merely duplicates or describes
the code — it rots."

**Rules about `lessons.md`:** the taxonomy entry is terse — "single file," on-
demand load — and there is no per-entry format spec (no required fields, no
frontmatter) documented in `knowledge/README.md` itself. The actual file
(`knowledge/lessons.md`) is free-form prose organized into numbered thematic
sections ("1. Subagent and research discipline," "2. Golden-source edit rules,"
"3. Opencode delegation gotchas," ...) with narrative lesson blocks, not a
structured/lintable registry format like `decisions/INDEX.md` or
`audit-log.md`. There is no existing field for "enforcement disposition" (i.e.,
whether a lesson has been converted to a check) anywhere in the current file or
its taxonomy rule.

**Where would a new tracked registry (lesson/finding-class → enforcing
check/test mapping) belong?** Per the taxonomy's own decision logic:
- It is not "Decisions" (not a choice-and-rationale record) or "Lessons" (not a
  process-learning narrative) in the strict sense — it is closer to
  **"Reference"** (a durable, bounded, structured fact ledger, same shape class
  as `knowledge/audit-log.md` and `knowledge/decisions/INDEX.md`) if it is to be
  a registry file. `knowledge/README.md`'s own Reference row explicitly already
  hosts one such bounded one-line-per-entry registry (`audit-log.md`) with
  "same registry-line discipline as `knowledge/decisions/INDEX.md`" — i.e., there
  is a named, reusable pattern for exactly this shape of new tracked file: bounded,
  one line per entry, lintable, home in `knowledge/reference/` (or its own file
  alongside `audit-log.md`), NOT inside `lessons.md` itself (which stays
  prose/narrative) and NOT a new top-level taxonomy row unless the designer
  decides the existing "Reference" row doesn't fit.
- Two additional precedents to weigh: (a) `deterministic-tooling-layer`'s D9
  explicitly designed `audit-log.md` to be "lintable... so the knowledge linter
  can check it for free" — i.e., new registries in this repo are expected to be
  designed lint-first; (b) `knowledge/README.md`'s "Usage Notes" says
  `knowledge/README.md` itself is scaffold-managed and synced byte-identical to
  every repo, while "All other files under `knowledge/` are per-repo and are
  never synced" — so if the ratchet registry is meant to be a cross-repo
  *taxonomy* concept, its rule belongs in `knowledge/README.md` (synced), but its
  *content* (actual registry entries) is inherently per-repo and un-synced, same
  as `audit-log.md`/`decisions/INDEX.md`/`lessons.md` today.

---

## 10. `knowledge/decisions/INDEX.md` — relevant registry lines (verbatim)

- `- **2026-07-02** · deterministic-tooling-layer · scaffold-managed check-only audit layer (never writes to code) with JSON-to-disk + one-line stdout, shared 0/2/3 exit triple (findings-vs-infra), stdlib-only via \`audit.toml\`/\`tomllib\`, line-number-insensitive baseline fingerprints, server-enforced read-only in \`data_lint.py\`, and an explicit-\`--date\` tag anchor in \`audit_scope.py\` → \`openspec/changes/archive/2026-07-02-deterministic-tooling-layer/\``
- `- **2026-07-02** · knowledge-lint · detect-only two-layer per-repo knowledge-drift detector — stdlib-only \`knowledge_lint.py\` (orphans, retired-path tokens, first-segment-gated broken citations, dangling archive pointers, guarded audit-log format) plus an operator-invoked \`lint-knowledge\` LLM skill for semantic drift, wired into the archive step as a flag-only wider-body sweep → \`openspec/changes/archive/2026-07-02-knowledge-lint/\``
- `- **2026-07-02** · mechanize-invariants · deterministic commit-time scaffold linter (\`scaffold_lint.py\`) with five checks converting prose invariants into machine enforcement, plus armed commit-test gate and sync-time hook-wiring warning → \`openspec/changes/archive/2026-07-02-mechanize-invariants/\``
- `- **2026-07-03** · prune-knowledge · [inline] plan-based SMALL portfolio-closer (no archive dir) drove \`scripts/knowledge_lint.py\` to green via an \`EPHEMERAL_PATHS\` allowlist, de-citing legitimate contrast/cross-repo references, and genuine drift fixes; closed the already-resolved parked question trackers; deleted the \`openspec-onboard\` skill (manual per-repo tombstone deletion owed downstream once the sync freeze lifts) — supersedes the \`harden-instruction-surface\` design decision D6b (...)`
- `- **2026-07-03** · clarify-audit-tooling-surface · clarified the scaffold audit-tooling surface: renamed \`lint-knowledge\` skill to \`knowledge-drift-review\` to end near-mirrored naming with \`knowledge_lint.py\`, added a \`run-audit\` operator entry point for the deterministic-audit cycle, and generalized \`scaffold_lint\`'s dangling-skill-ref detection from a single hardcoded token to an explicit frozenset so non-openspec skills validate without per-name hardcoding → \`openspec/changes/archive/2026-07-03-clarify-audit-tooling-surface/\``
- `- **2026-07-03** · checks-facts-split · deterministic audit engine split by naming contract, not by registry: \`audit_bundle.py\`→\`checks.py\` (findings-capable detectors, gated by a new preflight that reports ALL missing/mismatched check-family tools in one informed pass — trigger + install-or-disable + coverage-loss — before running anything, exit 3) plus a new \`facts.py\` (cache-semantics snapshots, undated, regenerate-on-use, never fails) — one engine/registry shared via a \`family\` field rather than splitting the registry, keeping \`--report\` able to run everything; config renamed \`audit.toml\`→\`checks.toml\` (no fallback, zero repos had one); inventory gained \`audit_anchor\` (latest audit tag + commits-since) for staleness-cadence signalling; \`audit_scope.py\`'s tag/log-line ceremony deliberately keeps the "audit" name → \`openspec/changes/archive/2026-07-03-checks-facts-split/\``
- `- **2026-07-09** · outstanding-work-collector · deterministic gather fact (\`outstanding\`) as a \`kind="delegate"\` fact with shared \`scripts/outstanding.py\` module (D1), \`plans/archive/\` live-vs-archived convention (D6), and three new \`knowledge_lint.py\` drift-detection checks — duplicate-block, closed-unpruned, untriaged-age (D7/D8) — all scaffold-managed → \`openspec/changes/archive/2026-07-09-outstanding-work-collector/\``

No registry line mentions "lessons," "ratchet," or "mechanize" as a general
policy — every hit is either a specific named tooling change or the specific
`mechanize-invariants` change (which mechanized four *particular* invariants, not
a general lesson→check rule).

---

## 11. `scripts/knowledge_lint.py` — docstring + check registry (not full file)

Module docstring identifies it as joining "the scaffold-managed linter family
(`status_lint.py`, `data_lint.py`, `scaffold_check.py`)," stdlib-only,
detect-only, git-optional filesystem walk.

**Check functions (grep for `^def _check`), in file order:**
1. `_check_orphan_duplicate` (line 351) — canonical single-home file map
   (`STATUS.md`, `lessons.md`, `roadmap.md`, `audit-log.md`) flags a copy living
   outside its home or a second copy.
2. `_check_retired_paths` (line 384) — per-line substring scan for retired-path
   tokens (built-in defaults + optional per-repo `checks.toml` extension).
3. `_check_broken_citations` (line 407) — broken prose path citations, with a
   documented first-segment gate and several exclusion heuristics (URLs, `~`-
   paths, template placeholders, globs).
4. `_check_dangling_archive_pointers` (line 474).
5. `_check_audit_log` (line 499) — guarded on `knowledge/audit-log.md` existing;
   checks its registry-line format.
6. `_check_root_handoff_files` (line 526).
7. `_check_duplicate_blocks` (line 639) — the outstanding-work-collector-added
   duplicate-block detector.
8. `_check_closed_unpruned` (line 783) — outstanding-work-collector-added.
9. `_check_untriaged_age` (line 894) — outstanding-work-collector-added.

**Positioning implication for a new "lesson entry must carry an enforcement
disposition" check:** the existing checks are entirely **structural/drift**
checks over already-canonical files (orphans, stale citations, format of a
bounded registry, duplication, staleness-by-age) — none of them currently
inspect the *semantic content* of `lessons.md` entries (there is no per-entry
schema to check against). A new check enforcing "every lesson/finding entry
names an enforcing check or is marked accepted-risk" would be a new category
(content-shape validation of a specific tracked file, similar in spirit to
`_check_audit_log`'s guarded registry-format check, i.e. guarded on the relevant
file/section existing) rather than an extension of any current check. The
`_check_untriaged_age` precedent (age-based drift on an unresolved item) is the
closest existing shape for a "was this finding actioned within some bound" check.

---

## 12. `scripts/scaffold_lint.py` — module docstring only

"stdlib-only, detect-only linter over this repo's own mechanized invariants."
**Authoring-side tool** (like `sync_scaffold.py`) — deliberately NOT in
`scaffold_manifest.txt`, never syncs downstream. Exit codes: 0 = no findings, 1 =
findings (note: this differs from the checks.py/data_lint.py 0/2/3 triple — this
linter uses the plain `sync_scaffold.py`/`knowledge_lint.py` 0/1 drift-diagnostic
convention instead). "All six checks run even after an earlier one has produced
findings... reports everything in one pass." One of its six checks,
**`budget-agreement`**, is the docstring-confirmed precedent for
**artifact-vs-artifact cross-checking** (comparing the delegation-harness §e
budget table against embedded `timeout -k` literals scattered across instruction
files) — i.e., a check whose job is to catch two independently-edited artifacts
drifting apart, the same shape of problem a "lesson claims X is fixed, but no
check/test enforces X" ratchet would need to detect (an assertion in
`lessons.md`/a finding write-up vs. the actual presence of an enforcing
check/test in the codebase).

---

# END DIGEST
