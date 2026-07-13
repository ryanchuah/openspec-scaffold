# SMALL plan — outstanding-work discovery + continuity-file lint hardening

**Tier:** MEDIUM (revised up from SMALL after the flash premise pass — see "Tier note").
Bundles Q1 (canonical handoff/continuity file, strictly enforced) and Q2 (outstanding-work
discovery + residual LLM sweep) into one coherent scaffold-hardening pass, per operator
direction 2026-07-13. **Premise verdict: AGREE** (flash reviewer, `premise-review.md`
equivalent inline in this session) — direction sound; the one blind spot it caught (a
governed spec delta this change owes) is now folded in below.

> Filename note: this plan is deliberately **not** named `*handoff*` — under the rule it
> ships, the `handoff`/`handover` filename token is reserved for `knowledge/HANDOFF.md`
> alone, and the widened live-tree lint would flag a plan file that used it. The plan
> proving its own rule is the point.

## Problem statement

Three related gaps, all in already-shipped mechanisms:

1. **The canonical continuity file is under-enforced.** The scaffold already decided
   (`knowledge-handoff-file`, 2026-07-03) that `knowledge/HANDOFF.md` is the *single*
   sanctioned ephemeral mid-session handoff. But its lint guard
   (`knowledge_lint._check_root_handoff_files`) only inspects the **repo root** and only
   matches `startswith(("HANDOFF","HANDOVER"))`. So `plans/*-handoff.md`,
   `tmp/*handoff*.md`, `knowledge/research/*handoff*.md` — the exact places downstream
   repos accumulate them — are invisible to it. extrends has ~27 such floating files and
   psc-monitor an empty `plans/session-handoffs/` dir; with no lifecycle marker it is
   "hard to tell if a given one has already been run."

2. **Outstanding-work discovery is not signposted.** The deterministic gather
   (`facts.py --check outstanding` → `outstanding.py`) and its `outstanding-work-review`
   skill exist, but AGENTS.md never names them as *the* answer to "what work is left?".
   An agent finds them only by scanning the skill registry for the right phrase — which
   is how a recent session ended up hand-rolling a crawl instead.

3. **The residual LLM sweep is undocumented.** The deterministic gather deliberately
   no-ops in-code TODO scanning and enumerates prose files *point-only* (path + first
   heading, never body). Deciding "is this brief consumed or live?", catching orphaned
   research docs, and reading stray inline comments is a real, recurring manual pass that
   no skill names as a step — so it reads as ad-hoc when it is actually the documented
   gap.

## Proposed approach / fix

Three edits, all in scaffold-managed files (they propagate — see out-of-scope for the
propagation carve-out):

### 1. Widen the continuity-file lint (`scripts/knowledge_lint.py`)
- Rename `_check_root_handoff_files` → `_check_handoff_files`; keep the finding slug
  `root-handoff-file`? **No** — rename the slug to `handoff-file` (root-only is no longer
  accurate). Update the message to: `handoff-named file <rel>; the only sanctioned
  handoff file is knowledge/HANDOFF.md`.
- Walk the **whole repo** (respecting `is_ignored`, like the other repo-wide checks —
  skip gitignored paths so `.venv`/`output/` etc. are not flagged), not just
  `root.iterdir()`.
- Match `handoff` **or** `handover` as a **case-insensitive substring** of the filename
  (catches `wave4-remediation-handoff.md`, not just `HANDOFF*`).
- Exempt exactly one path: `knowledge/HANDOFF.md`. Nothing else — strict reservation.
- Wire the renamed check into `collect_findings` with the `is_ignored` arg. Signature
  follows the other repo-wide checks: `_check_handoff_files(root, is_ignored)` (currently
  called as `_check_root_handoff_files(root)` at ~line 945).

### 2. MODIFIED spec delta — `openspec/specs/knowledge-lint/spec.md`
The requirement **"Root-level handoff files are flagged"** (lines 202–214) names root-only
scope and `HANDOFF*`/`HANDOVER*` prefix matching — both of which this change replaces. It
MUST be updated via a change-dir RENAMED+MODIFIED delta promoted at archive — **not** a direct
edit to the promoted spec (rename → "Handoff-named files are flagged"; restate as repo-wide,
case-insensitive `handoff`/`handover` substring; exempt only `knowledge/HANDOFF.md`; update
both scenarios). Separately, the two overview-prose cross-references (spec lines 11 + 22,
"root-handoff-file check") are NOT requirement text, so no delta carries them — they are fixed
by a scoped direct edit at apply (see notes.md "Disclosed direct-edit exception").

### 3. Update tests (`scripts/test_knowledge_lint.py §7.1`)
- Keep: `knowledge/HANDOFF.md` not flagged; clean tree → no findings.
- Add: a **nested** `plans/foo-handoff.md` **is** flagged; a nested `docs/HANDOVER.md`
  is flagged; a gitignored `output/x-handoff.md` is **not** flagged (respects ignore).
- Update the slug `root-handoff-file` → `handoff-file` at **all three** call sites
  (lines 742, 759, 771 — not two).
- `scripts/test_doc_lint_gate.py` needs no change — the scaffold tree has only
  `knowledge/HANDOFF.md`, so the live-tree gate stays green.

### 4. Signpost discovery + name the residual sweep
- **AGENTS.md** ("Working process" section): add one line — to enumerate outstanding
  work, invoke the `outstanding-work-review` skill (pull-only; never boot-wired). Shared
  span, so it propagates to downstreams too.
- **`.claude/skills/outstanding-work-review/SKILL.md`** ("Judge" step 3): add a named
  **"Residual sweep"** sub-step that states exactly what the deterministic gather does
  NOT cover — prose *bodies* (open each enumerated `plans/` + `questions/*.md` file and
  classify consumed / live / orphaned), in-code TODO/FIXME (deliberate no-op), and stray
  research docs — so the manual pass is a documented, repeatable step rather than ad-hoc.

## Acceptance criteria
- One MODIFIED spec delta (`knowledge-lint`), `openspec validate --strict` clean, promoted
  at archive.
- `python3 scripts/knowledge_lint.py` (or `check.sh`) green on the scaffold live tree.
- New/updated unit tests pass; full `pytest` suite green including the doc-lint live-tree
  gate and the scaffold SEAL.
- A nested `plans/x-handoff.md` fixture is flagged; `knowledge/HANDOFF.md` is not.
- AGENTS.md names the outstanding-work entry point; the skill's Judge step names the
  residual sweep and its explicit non-coverage.

## Out of scope (explicit)
- **Downstream cleanup + propagation.** Renaming/archiving extrends' ~27 and
  psc-monitor's handoff-named files, and running `sync_scaffold.py` to push the widened
  lint, are a **separate operator-gated** follow-on. They are *coupled*: syncing the
  widened lint before the downstream files are cleaned turns those repos' pytest gates
  red. This change ships the mechanism in the scaffold only; propagation waits for an
  explicit operator go + a per-repo cleanup pass.
- **The frozen OW-2→3→5→6 apply batch** — untouched; `knowledge/HANDOFF.md` stays.
- **`outstanding.py` gather-scope changes** (e.g. the parked `plans-scope-alignment`
  SMALL) — not folded in here.
- Any change to *what* the gather enumerates; we only signpost + document, not re-scope
  the deterministic collector.

## Known strict-reservation trade-off (operator chose STRICT)
A case-insensitive substring rule also flags legitimate *content-word* filenames
(`handoff-protocol.md`, `incident-handover-checklist.md`). Under strict reservation those
must be renamed. No opt-out marker is added now (a filename check can't read an in-file
`<!-- lint:... -->` marker anyway); if a real downstream collision appears, park a
path-allowlist follow-on rather than weakening the rule.

## Tier note
**MEDIUM.** The flash premise pass (AGREE) caught that this modifies a governed capability
spec (`knowledge-lint`, the root-handoff requirement) — a spec delta reviewed before freeze
is exactly the MEDIUM contract (tasks.md + delta + notes.md acceptance criteria, pro review,
verify skill). The code footprint is still small, but a behavior change to a promoted spec
+ a propagating enforced gate warrants the delta-and-promote path over a direct SMALL edit.
