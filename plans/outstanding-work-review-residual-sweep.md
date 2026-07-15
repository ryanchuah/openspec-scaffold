# SMALL plan — document a repeatable residual-sweep step in outstanding-work-review

**Source:** downstream psc-monitor session, 2026-07-15 — first real-world run of the
`outstanding-work-review` skill, followed by an operator-requested manual crawl (5 parallel
subagents, one per blind-spot category) to check whether the deterministic collector
(`scripts/outstanding.py`) misses real work due to its point-only / heading-only enumeration
choices. It does. This plan turns that one-off crawl into the repeatable step the skill's own text
already asks for (see `SKILL.md` step 3, "Residual sweep" bullet: *"Convert the occasional human/LLM
sweep of these residual sources into a documented, repeatable step here — do not change what the
deterministic collector enumerates."*). The concrete findings from the source run are reproduced
below (§ Concrete findings) precisely so the agent implementing T1 has real calibration examples
instead of only the abstracted category descriptions — repo-specific *disposition* of those findings
(the actual tracker edits) happened in psc-monitor's own `knowledge/questions/INDEX.md`, not here;
what's reproduced here is the method (how each was found) and the mechanism (why the collector
structurally can't see it), which generalize.

## Problem

`scripts/outstanding.py` is deliberately partial by design (see its own docstrings): it captures
*point-level* entries for `plans/*.md` and `knowledge/questions/*.md` per-item files (filename +
first heading only, never body content), only extracts `## ` *heading text* from
`knowledge/roadmap.md` (never the body beneath), no-ops in-code TODO/FIXME scanning entirely, and
never touches `knowledge/decisions/`, `knowledge/reference/` (or repo-specific reference/compliance
dirs), or non-`tasks.md` files inside `openspec/changes/<name>/`. These are reasonable engineering
trade-offs (full prose parsing would be brittle/expensive to do deterministically) — but the skill
currently gives the orchestrator no concrete procedure for compensating with judgment. In practice
this means real, uncaptured work quietly accumulates outside `knowledge/questions/INDEX.md` and
`knowledge/roadmap.md`, discoverable only by an ad-hoc full-repo crawl nobody schedules.

A live test of this on psc-monitor (175 collector-tracked items, 52 flagged "untriaged") found:
zero of the 52 untriaged findings were real gaps (all were either nested evidence-citations under
an already-tracked parent finding ID, or a single regex false-positive on a hash-name string) —
but the residual crawl of prose bodies surfaced ~13 genuinely uncaptured items the collector
structurally cannot see, including one case where 14 of 18 individually-actionable findings in a
`plans/` doc were invisible because only 4 were named in the tracker's one-line pointer, and a
tracker pointer that read as "fully closed" when 17 items inside the linked file were still
explicitly marked OPEN.

## Concrete findings from the source run (calibration evidence)

Each subagent worked one category blind, cross-referencing against `knowledge/questions/INDEX.md`
and `knowledge/roadmap.md` to avoid re-reporting already-tracked work. Findings and the specific
collector mechanism that hid each are below.

**1. In-code markers.** 147 tracked files across `api/`, `pipeline/`, `scripts/`, `frontend/src/`,
`migrations/`, `tests/` (excl. `tests/fixtures`) swept for TODO/FIXME/HACK/XXX/"not
implemented"/NotImplementedError/"for now"/"temporary"/"workaround", then a broadened second pass
for "not yet"/"stub"/"placeholder"/"unimplemented"/"deferred"/"kludge"/"shortcut". **Zero genuine
findings** — every hit was `tempfile.TemporaryDirectory`, test-double vocabulary in the audit
harness's own test suite (naming its mock/stub binaries), a template string the tool itself writes
into *generated* docs, or `outstanding.py`'s own comment explaining the no-op this sweep was
verifying. *Why not caught:* not applicable here — `_enumerate_todo_code` unconditionally no-ops
this category by design; the sweep's job was validating that the no-op is currently safe, which it
is. Expect this category to usually report nothing; don't force findings.

**2. Questions/decisions/lessons body sweep.** Read all 11 non-`INDEX.md`
`knowledge/questions/*.md` files, `decisions/INDEX.md`, `lessons.md`, `ratchet-log.md` in full.
Found: (a) a per-item file with 17 rubric-level test-quality findings explicitly marked OPEN, while
`INDEX.md`'s one-line pointer to that file said the backlog was "CLOSED," reading as fully resolved;
(b) a per-item file describing a fully-specified, ready-to-execute fix batch bundled alongside an
unrelated pending decision — `INDEX.md`'s Active bullet named only the pending decision, not the
ready batch; (c) a per-item file whose two concrete fix recommendations were never named in
`INDEX.md`'s terse one-line pointer, only discoverable by opening the file; (d) **a direct
contradiction between two per-item files** — one framed an order-dependent test flake as
hypothetical ("benign on current evidence"), while a *different* file documented that the exact
trigger condition had already occurred and been confirmed by two independent verifiers; the first
file was never updated to reflect it; (e) a per-item file's item was stale — framed as an open
tuning question, but superseded by a decision recorded elsewhere in the same tracker; (f) the
ratchet-log file was completely empty despite a real history of closed findings the repo's own
finding-closure-ratchet rule says belong there. *Why not caught:* `_enumerate_prose_files` records
only `[status] filename — first-heading` per file (point-only) — body content, sub-item lists, and
cross-file contradictions are structurally invisible. `decisions/INDEX.md`, `lessons.md`,
`ratchet-log.md` aren't in the source list at all — zero coverage, not partial.

**3. Plans body sweep.** Read all 45 `plans/**/*.md` (excl. `plans/archive/`) in full. Found: (a)
**the single biggest gap** — two related planning docs contained 18 individually-numbered,
individually-actionable findings; only ~7 were named individually in `INDEX.md`, the rest existed
only inside one aggregate "bundled into a future batch" pointer, shaped exactly like the
`FINDINGS*.md` ledgers the collector *does* structurally parse, just under a different filename
pattern; (b) a coverage-review doc named a concrete data-integrity defect (a dedup constraint with
an uncovered NULL-corner case) under a section heading that happened to reuse a label already used
elsewhere in `INDEX.md` for an unrelated item — **a label collision that could mislead a naive
keyword-based check**; worth flagging explicitly in the checklist so agents read enough context to
disambiguate, not just grep for the label string; (c) two small-plan docs revealed a cleanup task
was only half-done, with the remainder mentioned solely in a reference doc, never in a tracker; (d)
a doc-drift-analysis doc named two specific drift items from an earlier lint pass that were flagged
but never actually fixed; (e) two `explore-brief.md` files (pre-propose planning docs, a step before
formal change artifacts exist) each contained one real open item — an orphaned-ownership flag and an
unresolved operator question — neither promoted into the tracker. *Why not caught:* same point-only
mechanism as category 2 — every `plans/*.md` gets `[status] filename — first-heading` regardless of
whether its body is a single paragraph or an 18-item findings ledger. The collector's
`findings_globs` config only matches `knowledge/research/**/FINDINGS*.md`; a findings-shaped doc
anywhere else is invisible to the untriaged-ID mechanism entirely, not just soft-missed.

**4. Reference/compliance/roadmap-body sweep.** Grepped ~19 `knowledge/reference/*.md` +
~9 repo-specific compliance docs for TBD-class markers; read `roadmap.md` in full. Found: (a) a
non-closed roadmap heading had 5 numbered items with real, specific detail underneath (concrete
deferred features/epics) that exist nowhere else in structured form — the collector had only ever
surfaced the heading text; (b) a reference doc's body named 4 specific pending corrections, while
every other tracker reference to that work used only a generic "doc batch" label; (c) **a doc-drift
finding, a different defect class from an uncaptured task** — three compliance documents each
independently asserted a mechanism was "not yet built," but grepping the actual codebase showed it
was implemented and wired into 4 production call sites; this one turned out to already be tracked
via a differently-worded tracker bullet, but the codebase spot-check step is what caught the drift
and is worth keeping in the checklist regardless. *Why not caught:* `knowledge/reference/` and the
compliance dir aren't in `outstanding.py`'s source list at all (zero coverage). `roadmap.md`
coverage is `## `-heading-only by explicit design (`_enumerate_roadmap` only regexes heading lines).

**5. Change-dir prose + specs + untriaged-dedup sweep.** Read `proposal.md`/`design.md`/`notes.md`
for all 3 non-archived `openspec/changes/<name>/` dirs (not just `tasks.md`); skimmed all 7
`openspec/specs/*/spec.md` (zero TBD markers — clean); did the untriaged-findings dedup. Found: (a)
every one of the 3 change dirs' `notes.md` files contained real open items with no `tasks.md`
checkbox — forward-looking pointers for future sessions, non-blocking operator decisions,
archive-phase actions, and an apply-time staleness re-check instruction; (b) the untriaged-findings
dedup: of 52 flagged IDs, 51 were child evidence-citations nested *inside* parent finding sections
in a `FINDINGS.md` file — not free-standing findings at all. Tracing each to its parent ID showed
every parent was already dispositioned (scheduled into a batch, refuted, or closed) in two other
tracker files, just never cited by the *child* ID string anywhere under `knowledge/questions/`. The
52nd ID was a pure regex artifact — a hash-algorithm name mention, not a finding ID. *Why not
caught:* `_enumerate_tasks` only extracts `- [ ]` lines from `tasks.md`; sibling files in the same
directory aren't in its glob. The untriaged-findings regex has no concept of ID hierarchy — every
match is treated as a standalone finding, so nested child citations and coincidental hash-shaped
strings both false-positive identically.

## Proposed approach

Add a concrete "Residual sweep checklist" to `SKILL.md` step 3, as five parallelizable sweep
categories an orchestrator can hand to subagents (mirrors what actually worked downstream):

1. **In-code markers** — grep tracked source dirs (exclude generated/vendored/test-fixture data)
   for TODO/FIXME/HACK/XXX/NotImplementedError/"not implemented"/"for now"/"temporary"/"workaround".
   Judge each hit: genuine deferred-work marker vs. stylistic/explanatory comment or test-double
   vocabulary (mock/stub naming). Report only genuine candidates — this category is usually clean
   and expected to stay clean; don't force findings.
2. **Questions/decisions/lessons body sweep** — read every `knowledge/questions/*.md` (excluding
   `INDEX.md`) in full, plus `knowledge/decisions/INDEX.md`, `knowledge/lessons.md`, and
   `knowledge/ratchet-log.md` (or repo-equivalent). Cross-reference against `INDEX.md`'s own
   Active/Parked summaries: flag content that (a) isn't reflected as a one-line pointer at all, or
   (b) contradicts/supersedes what the pointer currently says (staleness, not just omission).
3. **Plans body sweep** — read every `plans/**/*.md` (excluding `plans/archive/`) in full,
   prioritizing files shaped like findings/ledgers (multiple individually-numbered items, a
   findings register, an attack list, evidence docs) since those are most likely to hide
   individually-trackable work behind one aggregate pointer. Cross-reference against
   `knowledge/questions/INDEX.md` and `knowledge/roadmap.md`.
4. **Reference/compliance/roadmap-body sweep** — grep `knowledge/reference/*.md` and any
   repo-specific regulatory/compliance dir for TBD/"not yet built"/"not drafted"/"PROVISIONAL"/
   "pending" markers; read `knowledge/roadmap.md` in full (not just headings). For any "not yet
   built" claim, spot-check the claim against the actual codebase — if the feature now exists,
   that's a **doc-drift finding** (a different defect class from an uncaptured task) and should be
   reported separately.
5. **Change-dir prose + specs + untriaged-dedup sweep** — for each non-archived
   `openspec/changes/<name>/`, read `proposal.md`/`design.md`/`notes.md` (not just `tasks.md`) for
   open questions/deferred items with no corresponding checkbox. Skim `openspec/specs/*/spec.md`
   for TBD markers. For the untriaged-findings bucket specifically: before promoting an ID, check
   whether it's actually a citation *nested inside* a different, already-tracked parent finding ID
   (a known false-positive shape when `finding_id_pattern` is permissive) rather than a
   free-standing finding — this alone accounted for 51 of 52 "untriaged" hits in the live test.

Also record, as a **separate observation** (not a scope item for this plan): the untriaged-findings
regex can false-positive on nested evidence-citation IDs and incidental hash-shaped tokens (e.g. a
literal "SHA-256" mention). Repos with a two-tier ID scheme (parent finding ID + child evidence
citations sharing the same shape) may want a tighter `finding_id_pattern` in `checks.toml`, or to
document the dedup-by-parent-ID judgment call from sweep category 5 above as the standard
disposition. This plan does not change `outstanding.py`'s regex or defaults — config-tuning is a
per-repo decision, not a scaffold default change.

## Design alternative — split into two skills (operator decision needed)

The source-run cost profile was lopsided: the deterministic gather (`facts.py --check outstanding`)
runs in under a second and needs no judgment beyond the untriaged-bucket dedup; the residual sweep
spawned 5 parallel subagents that each read a dozen-plus full files and took 1–8 minutes /
tens-of-thousands of tokens apiece. Folding the checklist into the *existing* `outstanding-work-review`
skill (the T1–T5 tasks below) means every invocation — even a quick "what's open right now?" check —
now implicitly invites that much heavier sweep, or forces the orchestrator to remember to skip it.

**Option A (this plan's default, T1–T5 below):** one skill, deterministic gather + judge always,
residual sweep as an explicit optional step the orchestrator chooses per invocation. Minimal change,
but the cost/scope split lives only in the orchestrator's judgment each time, not in the tool
surface — easy to forget to run the deep sweep periodically, easy to accidentally trigger it on a
quick check.

**Option B (recommended instead — mirrors this repo's own existing pattern):** split into two
skills, matching the deterministic-detector-vs-deep-LLM-audit separation `AGENTS.md`'s "Deterministic
audit tooling" section already establishes for `checks.py`/`facts.py` vs. `correctness-audit`:
- **`outstanding-work-review`** (keep the name, narrow the scope) — steps 1/2/4 only: gather, read,
  verify, plus the untriaged-bucket dedup-by-parent-ID judgment (cheap, always relevant, no full-repo
  read). Safe to run every session; this is the "what's open right now" check.
- **`outstanding-work-deep-sweep`** (new skill) — runs `outstanding-work-review` first, then fans out
  the five-category residual sweep (subagents per category, as demonstrated in the source run) and
  triages results into the trackers. Explicitly pull-only, like `correctness-audit` and
  `composition-audit` — invoked periodically (e.g. before a launch/deploy gate, before a large
  archive batch, or on a fixed cadence the operator sets), not every session. Could optionally grow
  a due-signal later (mirroring `composition_audit`'s commits/archived-changes threshold in
  `outstanding.py`) so the skill can tell the orchestrator when a deep sweep is overdue, but that's a
  separate follow-on, not required for the initial split.

Option B costs more upfront (a new skill file, manifest entry, downstream sync) but keeps the cheap
path cheap by construction instead of relying on orchestrator discipline every time. If the operator
picks Option B, T1 below becomes "create `outstanding-work-deep-sweep`" instead of "expand the
existing skill," and `outstanding-work-review`'s own `SKILL.md` step 3 residual-sweep bullet should
be removed/pointed at the new skill instead of inlined.

## Tasks (implement top to bottom, check each off)

**T1 depends on an operator pick between Option A and Option B above — resolve that first (SMALL
premise pass or a direct operator ask), then implement whichever T1 variant applies.**

- [ ] **T1-A (if Option A)** In `.claude/skills/outstanding-work-review/SKILL.md`, expand the
  existing "Residual sweep" bullet under step 3 into the five-category checklist above (condense the
  prose; keep it scannable — this is a skill file read by agents, not a report). Explicitly keep the
  existing "do not change what the deterministic collector enumerates" instruction.
- [ ] **T1-B (if Option B)** Narrow `outstanding-work-review/SKILL.md` step 3 to just the
  untriaged-bucket dedup-by-parent-ID judgment (drop the "read prose bodies" scope), and create
  `.claude/skills/outstanding-work-deep-sweep/SKILL.md`: step 1 invokes `outstanding-work-review`;
  step 2 is the five-category checklist above, run as parallel subagents; step 3 triages results into
  `knowledge/questions/INDEX.md`/`knowledge/roadmap.md` exactly as this skill's own step 3 already
  does today. Mark it pull-only, same guardrails as `correctness-audit`.
- [ ] **T2** Add one sentence to the checklist's category 5 flagging the nested-evidence-citation
  false-positive shape for the untriaged-findings bucket, so orchestrators check *disposition of
  the parent ID* before promoting a child citation into `knowledge/questions/INDEX.md`.
- [ ] **T3** Bump `metadata.version` in the `SKILL.md` frontmatter (currently `"1.0"`) per this
  repo's normal versioning convention for skill content changes — check sibling skill files for the
  exact convention if `"1.0"` → `"1.1"` isn't it.
- [ ] **T4** Sync to at least psc-monitor (`python3 scripts/sync_scaffold.py psc-monitor`) and any
  other downstream repos with `outstanding-work-review` in `scripts/scaffold_manifest.txt`; verify
  with `--check` before syncing for real.
- [ ] **T5** Confirm `scripts/scaffold_check.py`'s pre-commit guard still passes in each synced
  downstream repo (no accidental hand-edit drift introduced by this change).

## Out of scope

- Changing `scripts/outstanding.py`'s enumeration logic, `finding_id_pattern` defaults, or adding
  automated prose-body parsing — the whole point of this plan is documenting the *human/LLM*
  judgment step, not automating it away.
- The actual tracker edits from the psc-monitor session that prompted this (those landed directly in
  psc-monitor's own `knowledge/questions/INDEX.md`, not here) — only the generalizable method and
  mechanism are reproduced above in § Concrete findings.
- Wiring this skill into any auto-run path — it stays pull-only per its existing guardrail.

## Verification

- `SKILL.md` still parses as valid frontmatter + markdown (no tooling changes needed to check this
  beyond a visual diff review).
- Re-run `python3 scripts/sync_scaffold.py --check <repo>` for each downstream repo after sync;
  exit 0 = converged.
