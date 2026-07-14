# Recon — OW-11 (skill de-bloat + mechanized gates)

**Purpose:** read-only fact-gathering to scope/spec OW-11's sub-items precisely. Source design
trigger: `knowledge/research/workflow-audit-2026-07-11/AUDIT.md` finding 5 (lines 116-123) +
the "Are the prompts too tight or too loose?" answer (lines 40-51). Committed-state baseline:
OW-7 (`scripts/opencode_delegate.py` + `output/delegation-log.jsonl` telemetry) is already
landed; this recon reads the **current** files, post-OW-7 and post the 2026-07-13 batch
(OW-1/4, OW-9/14 archived same day — see `openspec/changes/archive/2026-07-13-*`).

No source was edited to produce this document.

---

## 1. Verify steps 12–16 de-bloat (fuzzy inference → deterministic CLI)

File: `.claude/skills/openspec-verify-change/SKILL.md`

Current numbering (post-OW-7; the AUDIT's "steps 13-15" reference has shifted by the step
renumbering that happened when OW-7's multi-model-pass steps 9-11 were inserted before the
artifact/spec-mapping block — the AUDIT's own finding-5 text already uses "steps 12-16" for
this same bundle, which matches today's numbering):

- **Step 12** (`SKILL.md:292-299`) — "Initialize verification report structure": sets up the
  three-dimension (Completeness/Correctness/Coherence) report shell. No fuzziness itself, but
  it exists only to scaffold what 13-16 fill in.
- **Step 13** (`SKILL.md:301-323`) — "Verify Completeness". The fuzzy part, quoted verbatim
  (`SKILL.md:315-320`):
  > - If delta specs exist in `contextFiles.specs`:
  >   - Extract all requirements (marked with "### Requirement:")
  >   - For each requirement:
  >     - Search codebase for keywords related to the requirement
  >     - Assess if implementation likely exists
  >   - If requirements appear unimplemented:
  >     - Add CRITICAL issue: "Requirement not found: <requirement name>"
- **Step 14** (`SKILL.md:325-342`) — "Verify Correctness". Same pattern, quoted
  (`SKILL.md:327-334`):
  > - For each requirement from delta specs:
  >   - Search codebase for implementation evidence
  >   - If found, note file paths and line ranges
  >   - Assess if implementation matches requirement intent
  >   - If divergence detected: Add WARNING...
  > - For each scenario in delta specs (marked with "#### Scenario:"):
  >   - Check if conditions are handled in code
  >   - Check if tests exist covering the scenario
- **Step 15** (`SKILL.md:344-360`) — "Verify Coherence" — design-adherence + pattern-consistency
  checks; also "look for glaring inconsistencies" (soft/judgmental, but this is legitimately
  the coherence-judgment residue, not a duplicate of anything deterministic).
- **Step 16** (`SKILL.md:362-400`) — "Generate Verification Report" — assembles 12-15's findings
  into the scorecard/CRITICAL-WARNING-SUGGESTION report. Purely a formatting step once 13-15 are
  mechanized/trimmed.

**What deterministic CLI already exists that duplicates this:**
- `openspec status --change "<name>" --json` (already invoked at verify Step 2) returns, per
  artifact, `status: "done"|"ready"|"blocked"` and (for `tasks`) is the CLI's own
  source-of-truth for completion — Step 13's **task-completion** half (parsing `- [ ]`/`- [x]`)
  is legitimately manual today (openspec's `status` JSON does not expose per-checkbox state, only
  artifact-level `done`/`blocked`), so that part stays. It is Step 13's **second** half —
  "search codebase for keywords... assess if implementation likely exists" for **spec
  requirements** — that has no CLI backing and is the fuzzy-inference AUDIT flags.
- Confirmed **`openspec status --json` exists** and I ran it live
  (`openspec status --change "apply-throughput-resume" --json`): it returns
  `changeRoot`, `artifactPaths` (with `existingOutputPaths` per artifact), `applyRequires`,
  `isComplete`, and an `artifacts` array of `{id, outputPath, status}` — e.g. `tasks` had
  `status: "done"`. It does **not** parse requirement-level detail (no per-requirement or
  per-scenario status) — it is change/artifact-shaped, not spec-shaped.
- **What CLI is missing** (so "replace 13-14 with deterministic CLI" needs a companion, not just
  reuse of `status`): a way to structurally enumerate `### Requirement:` / `#### Scenario:`
  headers out of the delta spec files under `contextFiles.specs` and confirm each is *present*
  (structural existence, not "implementation likely exists" semantic inference). That is
  mechanizable (regex/markdown-header scan — same primitive item 7 below needs), but the
  **semantic** "does the implementation satisfy this requirement" judgment is NOT mechanizable
  and should stay LLM (this matches the AUDIT's own "Correctly LLM — do not script" list: it does
  NOT list requirement-semantic-matching as scriptable, only "notes.md five-field presence" and
  "freeze-eligibility parsing").

**Recommended shape for OW-11:** replace Steps 13's "search codebase for keywords / assess if
implementation likely exists" clause with (a) a deterministic structural check — every
`### Requirement:` and `#### Scenario:` header in the delta specs is enumerated by script/grep
and cross-referenced against `tasks.md` checkbox completion (already CLI-backed) — CRITICAL only
fires on a structural gap (a requirement with zero referencing task, not "keyword not found in
code"); (b) fold the semantic-match judgment (currently Step 14's "assess if implementation
matches requirement intent") into a **short coherence note** the orchestrator writes from its
own Steps 4-8 behavioral review (which it already did and already has real evidence for) instead
of re-deriving it via keyword search. This is what the AUDIT's finding 5 phrase "replace verify
steps 12-16 with deterministic CLI coverage + a short coherence note" means concretely.

---

## 2. Verify step 18 ritual → `notes_lint.py`

Two steps are involved (the AUDIT's "step 18" phrasing bundles both; today's file separates
them):

- **Step 17** (`SKILL.md:402-445`, 44 lines) — "Checkpoint verify findings to the change dir" —
  mandates appending **five required fields** to `notes.md`:
  1. **verdict** (ready for archive / needs revision) — `SKILL.md:409`
  2. **what you confirmed by eyeballing live output** (behavior, not counts) — `SKILL.md:410-413`
  3. **any defect found and how it was fixed** (and who — re-delegated vs trivial inline),
     attributed to the pass that surfaced it — `SKILL.md:414-415`
  4. **any as-built delta discovered during verify** not already recorded — `SKILL.md:416`
  5. **forward-looking items for the project docs** — open questions / tuning items / deferred
     scope / follow-ons "recorded nowhere else" — `SKILL.md:417-429` (this field alone is ~13
     lines of exhaustive-enumeration prose: "tune after real runs" items, live-eyeball
     observations implying a future question, scope deferrals, anything said "out of scope" —
     `SKILL.md:423-429`).
  Plus a "Still owned by archive" pointer list (`SKILL.md:432-436`) and an 8-line "why this is
  mandatory" rationale paragraph (`SKILL.md:438-445`).
- **Step 18** (`SKILL.md:447-469`, 23 lines) — "Verbally acknowledge documentation persistence" —
  mandates an **echo/checklist ritual** after writing notes.md, quoted in full
  (`SKILL.md:453-463`):
  > Use exactly this shape (fill in the real content; do not paraphrase the labels away):
  > ```
  > ✅ Documentation persisted to <changeRoot>/notes.md:
  >   1. Verdict — <ready for archive / needs revision>
  >   2. Live output eyeballed — <one-line pointer to the real sample recorded>
  >   3. Defects + fixes — <summary, or "none">
  >   4. As-built deltas — <summary, or "none">
  >   5. Forward-looking open-questions / tuning items / follow-ons — <explicit list, or "none + why">
  >   Still owned by archive — <knowledge/STATUS.md, knowledge/decisions/INDEX.md, knowledge/questions/INDEX.md, spec promotion, cleanup>
  > ```
  This is a **forcing-function-by-prose**: it exists because "stating it out loud catches the
  silent-omission failure that field 5 is most prone to" (`SKILL.md:451-452`) — i.e. the skill
  distrusts its own Step 17 instruction enough to add a second, redundant, human-readable-echo
  step rather than a machine check.

**The five fields, confirmed against real archived notes.md** (`I` read two examples):
- `openspec/changes/archive/2026-07-13-lesson-check-ratchet/notes.md:104-140` has the literal
  heading `### Verify checkpoint (mandatory 5 fields + archive handoff)` followed by
  `**1. Verdict:**`, `**2. Live output eyeballed...**`, `**3. Defects found + how fixed
  (attributed):**`, `**4. As-built deltas not already in the artifacts:**` — this is a COMPLEX
  change and the format is followed precisely.
- **Surprise / drift observed:** two other 2026-07-13 archived MEDIUM changes
  (`defect-prevention-detectors`, `instruction-surface-coherence`) do **not** have this 5-field
  block in `notes.md` at all — their "Verify —" narrative instead landed in `review-log.md`
  (e.g. `openspec/changes/archive/2026-07-13-defect-prevention-detectors/review-log.md:75-89`,
  under a plain `## Verify — 2026-07-13` heading, no field numbering). So the mandatory-ritual
  prose is not reliably followed even now — which is itself evidence FOR mechanizing rather than
  trusting the echo: a `notes_lint.py` that fails when the five numbered fields are absent from
  `notes.md` would have caught this.

**Deterministic replacement:** a `notes_lint.py` (or a `checks.py` builtin, see item 9) that
parses a change's `notes.md` for the five required field markers (by heading/number, tolerant of
exact wording drift) and fails/flags if any is missing or empty-without-a-"none + why" — this
replaces BOTH the ~40-line field-5 belaboring prose in Step 17 (keep the *substance*, the fields
themselves are real and load-bearing per the AUDIT's own "notes.md five-field presence" scriptable
item) and the entire Step 18 verbal-echo step, whose only job is compensating for the checker that
doesn't exist yet.

---

## 3. `freeze-check` script (review-verdict parsing)

Freeze-eligibility is decided in `.claude/skills/openspec-propose/SKILL.md` step 4c, "Shared
freeze ladder" (`SKILL.md:112-137`), quoted:

> - If 🔴 blocking issues exist → fix them in the artifact → **re-review is MANDATORY**
>   (return to the platform-specific invocation step for a fresh pass)... Only a review round
>   that comes back with zero 🔴 can freeze it. (Max 3 reviewer passes total...)
> - If no 🔴 issues → the freeze condition depends on the artifact:
>   - **`design.md` / `tasks.md`**: the artifact is frozen; move to the next one (unchanged).
>   - **`proposal.md`**: check the premise verdict:
>     - `PREMISE: AGREE` → the artifact is frozen; move to the next one.
>     - `PREMISE: DISSENT` → **Stop the freeze loop.** Present ... via **AskUserQuestion**...

**The review-verdict format the reviewer emits** (confirmed by 2 sources):
1. The `opencode_delegate.py` post-processing call the propose skill itself specifies
   (`SKILL.md:194-201`, `213`): `--require-marker "## Review Round" --require-marker
   "(🔴|🟡|💡)"` and, for `proposal.md` only, `--verdict-regex "PREMISE: (AGREE|DISSENT)"`.
2. A real archived `review-log.md`
   (`openspec/changes/archive/2026-07-13-lesson-check-ratchet/review-log.md:5,53,107,175`) shows
   the literal headings `## Review Round 1 — proposal.md`, `## Review Round 1 — design.md`, etc.,
   and a verdict line like `**Verdict: PASS — zero 🔴, zero 🟡. PREMISE: AGREE.**` (round 3) or
   `**Verdict:** NEEDS REVISION (one NEW 🔴). **Premise:** AGREE.` (round 2, freeform label
   variant — "Verdict:" vs "Verdict —" is not perfectly standardized across rounds).

**So the parseable contract is:** a `## Review Round <n> — <artifact>` heading, a body containing
zero-or-more `🔴`/`🟡`/`💡` markers (freeze needs a scan for ANY 🔴 in the round's own findings
section, not just a hand-written verdict line — the current archived examples show the verdict
line is a human/LLM-composed summary, not a strictly-templated token line, e.g. "zero 🔴, zero 🟡"
is prose, not `RED_COUNT: 0`), and — for `proposal.md` only — a `PREMISE: (AGREE|DISSENT)` token
(this one IS already a strict regex-matched token per the wrapper's `--verdict-regex`).

**Complexity note:** the 🔴-count is the harder half to parse reliably — today's reviewer prompt
doesn't mandate a machine-countable summary line (unlike the verifier's `VERDICT: READY|NEEDS
REVISION` token in the verify skill, `SKILL.md:63`, which IS already strictly templated). A
`freeze-check` script would either (a) count literal 🔴 glyphs in the round's own findings block
(fragile if 🔴 appears in prose/examples elsewhere) or (b) require the reviewer prompt to be
tightened to emit a `FREEZE: <artifact> — READY|BLOCKED` token, mirroring the verifier's
`VERDICT:` line — the latter is more robust and cheap (one prompt-template edit) and should
probably be bundled into this OW-11 sub-item rather than trying to regex-count emoji reliably.

---

## 4. explore→propose slug-match warning

**Explore sets the slug** in `.claude/skills/openspec-explore/SKILL.md:20`:
> **Write `plans/<slug>/explore-brief.md`** — derive `<slug>` as kebab-case from the exploration
> topic (e.g. "add user auth" → `add-user-auth`), using the same convention the propose skill
> uses. Create `plans/<slug>/` with `mkdir -p` on first write. If the slug collides with an
> existing entry, append a short disambiguator (e.g. `-1`).

The premise review is written to `plans/<slug>/premise-review.md` (`SKILL.md:53`).

**Propose picks it up** in `.claude/skills/openspec-propose/SKILL.md` step 2 ("Relocate explore
artifacts (D8)", `SKILL.md:44-56`), quoted:
> If a `plans/<name>/` directory exists (matching the change name as the slug), move the explore
> brief and its premise review into the change dir... ```if [ -d "plans/<name>" ]; then mv
> plans/<name>/explore-brief.md ... ```
> Best-effort skip when no matching `plans/<name>/` exists — the change may have been proposed
> without a prior explore phase, **and the silence is intentional**.

**Where the mismatch orphans silently:** `<name>` in propose is whatever kebab-case the user (or
the "derive a kebab-case name" step 1, `SKILL.md:29-36`) typed for the **change**, independently
derived from the user's propose-time description — it is NOT read back from any explore-time
record (there's no pointer file linking a change to its originating explore slug). If the
operator's propose-time wording produces a different kebab-case than explore's slug (e.g. explore
crystallized as `improve-caching`, but the operator says "propose the caching thing" and the
orchestrator derives `caching-improvements`), `[ -d "plans/<name>" ]` is false, the `mv` block is
skipped, and — because "the silence is intentional" by design — **nothing tells the operator a
`plans/<other-slug>/` with a real premise review still exists**. The brief and its AGREE/DISSENT
verdict are permanently orphaned in `plans/`, never merged into the change dir, and never
resurface (nothing in propose or later phases re-scans `plans/` for near-misses).

**Mechanization for OW-11:** a warning step in propose — after step 2's exact-match check, if no
exact match, list `plans/*/` directories and flag near-matches (e.g. simple token-overlap or
Levenshtein-adjacent kebab-case comparison) so the operator gets an explicit
"did you mean plans/<other-slug>/?" prompt instead of silent skip. This is a small, self-contained
addition to propose step 2; no new script needed (a few lines of shell/glob comparison inline in
the skill, or a tiny `scripts/` helper if the fuzzy-match logic gets non-trivial).

---

## 5. Concurrent COMPLEX verifier passes

Current sequencing, `.claude/skills/openspec-verify-change/SKILL.md`:
- The pass order is stated as an arrow chain (`SKILL.md:55`): "**COMPLEX:** self-review →
  `deepseek/deepseek-v4-pro` behavioral verifier pass → `deepseek/deepseek-v4-flash` lens
  verifier pass."
- The invocation section (`SKILL.md:68-84`) presents them as **two separate bash blocks** under
  one "Invocation (both platforms)" heading — "Behavioral pro pass (MEDIUM and COMPLEX)" then
  "Lens pass (COMPLEX only)" — with no instruction to launch both before waiting on either; each
  is documented with its own `opencode_delegate.py` post-processing call read immediately after
  its own invocation (`SKILL.md:149-170`), which only makes sense if the orchestrator waits for
  pass 1's result before even constructing pass 2's prompt (the lens pass's prompt selection, in
  fact, doesn't depend on pass 1's outcome, but the skill text never says to fire them together).
- The gate-recovery rule (`SKILL.md:187`) reinforces sequential framing: "**COMPLEX:** if the pro
  pass fails, fix, re-run pro then the lens pass; if the lens pass fails, fix, re-run just the
  lens pass" — i.e. today pro fully resolves (including any fix/re-run cycle) before lens even
  starts.
- Step 9 (`SKILL.md:280-282`) says "run the passes... here" (singular pass-sequence, no
  parallelism language).
- `delegation-harness.md:88-92` confirms both ARE background-launchable (`run_in_background:
  true` applies to "verify's verifier passes (behavioral pro pass + COMPLEX-only lens flash
  pass)"), so the infrastructure (EXIT-sentinel, non-blocking background launch) already supports
  concurrency — nothing here requires new plumbing, only a skill-prose change: launch pro AND
  lens in the same turn (both are read-only on a frozen tree per AUDIT's own framing, "read-only
  on a frozen tree" — `AUDIT.md:121`), then poll/collect both exit-sentinels, and only serialize
  the fix→re-run loop if either comes back NEEDS-REVISION.

**Confirmed: currently sequential** (by skill prose and worked example), not concurrent, despite
the underlying harness already supporting background launches. OW-11's "run them concurrently"
ask is a real, currently-unrealized win (AUDIT's own estimate: "saves ~13 min wall-clock",
`AUDIT.md:121`), and — because both are independent `opencode run` background calls against an
already-frozen (not-being-edited) tree — this is a low-risk skill-prose change, not a new
mechanism: launch both, wait for both exit-files, THEN apply the existing gate-recovery step 2
rule (fix + re-run only the failing pass and everything after it) unchanged.

---

## 6. Model-ID agreement lint

**Occurrence counts** (excluding `openspec/changes/archive/` and `knowledge/research/`, which are
historical/frozen and not meaningfully "live" instruction surface; also excluding an untracked,
irrelevant `.claude/worktrees/analyze/` directory found during the grep — see Surprises below):

- **Narrow scan** (mirroring `scaffold_lint.py`'s existing `_scan_file_set`: `AGENTS.md` +
  `.claude/skills/**/*.md` + `.claude/agents/*.md` + `.opencode/agents/*.md`) — **59 occurrences
  across 14 files**:
  `AGENTS.md`, `.claude/agents/archive-executor.md`, `.claude/skills/composition-audit/SKILL.md`,
  `.claude/skills/openspec-apply-change/SKILL.md`, `.claude/skills/openspec-archive-change/SKILL.md`,
  `.claude/skills/openspec-explore/SKILL.md`, `.claude/skills/openspec-propose/SKILL.md`,
  `.claude/skills/openspec-verify-change/SKILL.md`, `.claude/skills/_shared/delegation-harness.md`,
  `.opencode/agents/apply-executor.md`, `.opencode/agents/archive-executor.md`,
  `.opencode/agents/explore-flash.md`, `.opencode/agents/openspec-reviewer.md`,
  `.opencode/agents/openspec-verifier.md`.
  (The AUDIT's "44× across 13 files", `AUDIT.md:122-123`, is close but stale by 2 days/several
  archived changes — `composition-audit/SKILL.md` didn't exist yet at audit time; today's true
  count on this same scan surface is 59/14.)
- **Broad scan** (also including `knowledge/`, `openspec/config.yaml`, `openspec/specs/`,
  `plans/`, `README.md` — i.e. everything live and tracked, still excluding archive/research) —
  **106 occurrences across 26 files**.
- **Exact spellings found** (live surface): `deepseek-v4-pro` (bare, 201×), `deepseek-v4-flash`
  (bare, 83×), `deepseek/deepseek-v4-pro` (model-flag form, 123×), `deepseek/deepseek-v4-flash`
  (model-flag form, 124×) — counts are on the broad scan and overlap (bare counts include
  occurrences that are part of the `deepseek/deepseek-v4-*` form too, since the narrower regex is
  a substring). No other spelling variants (no `-v4pro`, no version-number drift) were found —
  the spelling itself is consistent; there is simply no lint asserting it stays that way.
- **No existing model-id lint**: confirmed via grep — nothing in `scripts/` or
  `openspec/specs/` mentions `model-id` or `model_id`.

**`budget-agreement` as the template** (`scripts/scaffold_lint.py:409-455`):
- **Sanctioned set**: `_sanctioned_pairs()` (`scaffold_lint.py:409-436`) parses the **single
  source of truth table**, `.claude/skills/_shared/delegation-harness.md`'s `## (e) Timeout
  budget table` (`delegation-harness.md:141-152`) — it requires a line starting with `## (e)`,
  then extracts every `` `-k <digits> <digits>` `` cell via `_TABLE_CELL_PAIR_RE = re.compile(r"` -k
  (\d+) (\d+)`")` (`scaffold_lint.py:180`) from any markdown table row (`line.startswith("|")`).
- **Scan set**: `check_budget_agreement()` (`scaffold_lint.py:439-455`) re-uses the SAME
  `_scan_file_set()` (`scaffold_lint.py:188-202`: `AGENTS.md` + `rglob("*.md")` under
  `_SCAN_BASE_DIRS = (".claude/skills", ".claude/agents", ".opencode/agents")`,
  `scaffold_lint.py:162-166`) that `dangling-skill-refs` also uses, and for every embedded
  `timeout -k <n> <m>` invocation (`_EMBEDDED_PAIR_RE = re.compile(r"timeout\s+-k\s+(\d+)\s+(\d+)")`,
  `scaffold_lint.py:179`) found in those files, flags it if the `(n, m)` pair is not in the
  sanctioned set.
- This is a clean, directly-reusable template: a `model-id-agreement` check would (a) declare a
  sanctioned model-id set somewhere canonical, (b) scan the same `_scan_file_set()` file
  population (or a superset — the 14-vs-26-file gap above is a real scoping decision) for any
  `deepseek[-/]v4[-a-z]*`-shaped token, and (c) flag any token not in the sanctioned set (typo,
  version drift, an accidentally-introduced `deepseek-v3`, etc.).

**Where the sanctioned list would live:** `AGENTS.md`'s `## Roles` section already carries the
literal marker `<!-- CANONICAL: model-assignment-matrix — cite, do not restate -->`
(`AGENTS.md:93`) and is where every model-tier assignment (apply-executor=flash,
archive-executor=pro, reviewer=pro, verifier tier-keyed, haiku/Sonnet rungs) is already declared
prose-form (`AGENTS.md:91-148`). This is the natural, already-marked canonical home — same
pattern `budget-agreement` uses (`## (e)` marker in `delegation-harness.md`). A `model-id-
agreement` check would need ONE new small, parseable list added under/near that marker (today
the model-ids appear only embedded in role-description prose, not as a standalone enumerable
list — unlike the budget table, which is already a clean markdown table the regex can walk row by
row). That's the one piece of NEW structure this check needs (a short literal list or table of
sanctioned model-ids), not present today.

**Where `scaffold_lint.py` itself sits:** it is NOT in `scripts/scaffold_manifest.txt` (confirmed
— grep returned nothing) and there is an explicit, repeated design decision on record
(`knowledge/decisions/INDEX.md:59`, `knowledge/questions/mechanize-invariants-follow-ons.md:24`,
and 4+ archived-change docs) that **`scaffold_lint.py` is deliberately golden-source-only** — it
polices the scaffold repo's OWN instruction-surface invariants and is never propagated downstream.
A `model-id-agreement` check belongs here for the same reason `budget-agreement` does (it is
enforcing an invariant on the scaffold's own prompt surface, not a per-repo runtime concern).

---

## 7. Ratchet item `medium-change-spec-delta-unvalidated`

Ledger entry: `knowledge/ratchet-log.md:26`, quoted:
> `openspec validate <name>` discovers changes via `proposal.md`, so a MEDIUM change
> (tasks.md-only) and its spec deltas are never CLI-validated (prints "Unknown item", exit 0).
> Re-manifested in `instruction-surface-coherence`: the `tier-confirmation-gate` delta's
> SHALL-not-on-first-line error would have shipped had it not been caught by the pro review +
> manual inspection. Enforcement path: a `scaffold_lint`/`checks.py` check that discovers changes
> by DIR presence and structurally validates `openspec/changes/*/specs/**/spec.md` deltas
> (ADDED/MODIFIED/REMOVED/RENAMED headers, normative SHALL on the requirement's first physical
> line, `#### Scenario:` WHEN/THEN). Candidate to fold into OW-11 (mechanized gates).

**Live confirmation of the gap** (I reproduced it, did not just read about it):
- `openspec/changes/apply-throughput-resume/` is a real, currently-open MEDIUM change with
  `tasks.md` + `specs/apply-convergence-guard/spec.md` but **no `proposal.md`**.
- `openspec validate apply-throughput-resume --strict` → `Unknown item 'apply-throughput-resume'`
  (exit 1, but for the wrong reason — "doesn't exist" rather than "structurally invalid").
- `openspec validate --changes` (bulk) → `No items found to validate.` (both currently-open
  changes, `apply-throughput-resume` and `knowledge-surface-bounding-2`, lack `proposal.md`, so
  the bulk validator sees **zero** active changes — the entire MEDIUM-lane surface is invisible).

**Root cause, confirmed by reading the installed CLI's source**
(`/usr/local/lib/node_modules/@fission-ai/openspec/dist/utils/item-discovery.js`):
```js
export async function getActiveChangeIds(root = process.cwd()) {
  ... for (const entry of entries) {
    if (!entry.isDirectory() || entry.name.startsWith('.') || entry.name === 'archive') continue;
    const proposalPath = path.join(changesPath, entry.name, 'proposal.md');
    try { await fs.access(proposalPath); result.push(entry.name); }
    catch { /* skip directories without proposal.md */ }
  }
```
`dist/commands/validate.js` calls exactly this (`getActiveChangeIds()`) for both the interactive
picker and `validateDirectItem`/bulk `--changes` paths — there is no code path in the shipped CLI
that validates a change by directory presence alone. This is an upstream CLI design choice
(proposal.md = "this is a real active change"), not a bug scaffold introduced — it just doesn't
fit the MEDIUM lane, which (`AGENTS.md:244-245`) deliberately emits **only** `tasks.md`
("**MEDIUM** — run the OpenSpec lifecycle, except **propose** emits only `tasks.md`... change-
specific acceptance criteria go in the change's `notes.md`").

Contrast: `openspec list --json` (used by the verify/propose skills' Step 1) does NOT require
`proposal.md` — it lists `apply-throughput-resume` and `knowledge-surface-bounding-2` fine (both
show up with task counts). So change **discovery** for everyday orchestrator use is unaffected;
only **structural validation** (`openspec validate`) is blind to proposal-less changes.

**What a change's spec delta looks like structurally** (read a real, current example —
`openspec/changes/apply-throughput-resume/specs/apply-convergence-guard/spec.md`):
```
# Delta — apply-convergence-guard (apply-throughput-resume)

## MODIFIED Requirements

### Requirement: The apply-executor stops on non-convergence
The apply-executor SHALL continue healthy `write → test → fix` iteration, but SHALL stop
editing and report a blocker when... [SHALL clause starts the requirement's first physical line]

#### Scenario: Stalled failure (rule a)
- **WHEN** the same test fails with the same normalized error signature after 2 consecutive
  fix attempts
- **THEN** the executor stops editing and emits a structured blocker
```
i.e. exactly the shape the ratchet entry describes: a top-level `## ADDED|MODIFIED|REMOVED|
RENAMED Requirements` header, per-requirement `### Requirement: <name>` with its normative
`SHALL`/`MUST` on line 1 of the requirement body (this is the SAME rule `openspec validate
--strict` already enforces for proposal.md-bearing changes — confirmed by the propose skill's own
step 4f, `SKILL.md:284-299`, which cites exactly this failure mode: "a requirement whose normative
`SHALL`/`MUST` is not on its first physical line"), and `#### Scenario:` blocks with `- **WHEN**`
/ `- **THEN**` bullets.

**Where this check would live:** NOT `scaffold_lint.py` (golden-source-only, per item 6/9 —
this check needs to run in every downstream repo working any MEDIUM change, not just police the
scaffold's own prompt surface). The natural home is **`scripts/checks.py`**, following the exact
precedent OW-1/OW-4 already set (`test-quality` and `data-scale` builtins, `checks.py:974,1117` —
both registered as `family="check"`, `tier="floor"`, enabled-by-default, AST/regex-based,
in-process, no external tool). A new builtin (e.g. `spec-delta-structure`) would: (a) discover
change dirs by presence alone (`openspec/changes/*/` excluding `archive/`), (b) for each,
glob `specs/**/spec.md`, (c) apply the same three structural rules the CLI's own validator
applies to full specs — header keyword present, SHALL/MUST on the requirement's first physical
line, `#### Scenario:` has at least one WHEN/THEN pair — entirely re-implemented in Python (this
CANNOT simply shell out to `openspec validate`, because the CLI's validator only ever operates on
either a registered active **change** (proposal.md-gated) or a promoted **spec**
(`openspec/specs/<name>/spec.md`) — a change's pre-archive delta spec file is neither, so there is
no existing CLI entry point to proxy to; this is a genuine re-implementation, not a wrapper).

**Complexity: moderate**, not trivial — it needs its own small structural parser (mirroring a
subset of openspec's own validation rules) since there's no CLI hook to delegate to.

---

## 8. Bloat sizing

Current line counts (`wc -l`, current committed state):

| Skill | Lines |
|---|---|
| `.claude/skills/openspec-verify-change/SKILL.md` | 494 |
| `.claude/skills/openspec-explore/SKILL.md` | 339 |
| `.claude/skills/openspec-propose/SKILL.md` | 333 |
| (for scale) `.claude/skills/openspec-apply-change/SKILL.md` | 336 |
| (for scale) `.claude/skills/openspec-archive-change/SKILL.md` | 340 |

**Explore's stance/gallery-prose sample** (AUDIT says "~85% stance/ASCII-gallery prose" —
`AUDIT.md:48-49`; my own read of the file structure finds the mechanized phase-gate content is
concentrated in lines 1-68 and 129-182 (~120 lines total: the "Explore mode" intro, the
PHASE-GATE mechanics for writing `explore-brief.md` + running the premise reviewer, and the
"OpenSpec Awareness" section's `openspec list --json` / `openspec status --json` calls), while
lines 69-128 and 183-337 (~215 lines, ~63% of the file) are stance/gallery/example prose with no
mechanized effect — e.g. this ASCII block (`SKILL.md:104-120`):
```
**Visualize**
┌─────────────────────────────────────────┐
│     Use ASCII diagrams liberally        │
├─────────────────────────────────────────┤
│                                         │
│      ┌────────┐         ┌────────┐      │
│      │ State  │────────▶│ State  │      │
...
```
and the ~100-line "Handling Different Entry Points" section (`SKILL.md:196-297`) walking four
full worked dialogues (vague idea / specific problem / stuck mid-implementation / comparing
options), each with its own multi-line ASCII diagram. My own count (~63%) is somewhat lower than
the AUDIT's "~85%" — possibly the AUDIT counted differently (e.g. also charging the "What You
Might Do" / "What You Don't Have To Do" list sections, or the file had different content 2 days
ago) — but by either count, a clear majority of the file is re-injected-every-invocation prose
with no mechanized function. **Per the task brief, this trim is explicitly secondary to OW-11's
mechanized-gate priority** — flagged here for completeness, not proposed as the lead item.

---

## 9. Scaffold-managed files (propagation check)

Checked against `scripts/scaffold_manifest.txt`:

| File | In manifest? |
|---|---|
| `.claude/skills/openspec-verify-change/SKILL.md` | **Yes** (line: `.claude/skills/openspec-verify-change/SKILL.md`) |
| `.claude/skills/openspec-explore/SKILL.md` | **Yes** |
| `.claude/skills/openspec-propose/SKILL.md` | **Yes** |
| `.claude/skills/_shared/delegation-harness.md` | **Yes** |
| `AGENTS.md` | **Yes** (span-replace, not wholesale — per manifest's own comment "AGENTS.md — span-replace, not wholesale copy (see D3)") |
| `scripts/checks.py` | **Yes** |
| `scripts/scaffold_manifest.txt` | **Yes** (self-referential — the manifest lists itself) |
| `scripts/scaffold_lint.py` | **No** — confirmed absent from the manifest, and confirmed by an explicit, repeated decision record (`knowledge/decisions/INDEX.md:59` et al.) that it is deliberately golden-source-only and never propagates. |
| A new `notes_lint.py` / `freeze-check` script (if implemented as standalone scripts rather than `checks.py` builtins) | **Not automatically** — would need an explicit new manifest line; nothing propagates by default. |

**Conclusion:** the three skills (verify/explore/propose) ARE scaffold-managed and DO propagate
via `scripts/sync_scaffold.py` to downstream repos (extrends, psc-monitor) once edited here — so
OW-11's skill-prose trims automatically reach both downstream repos on the next
`propagate-scaffold` run. Any **new lint script** must be added to `scaffold_manifest.txt`
explicitly to propagate — UNLESS it is implemented as a new `checks.py` builtin check (which
already propagates, since `scripts/checks.py` itself is manifest-listed) — this is the same
"ships as a builtin vs. a bespoke script" fork item 7 already resolves in favor of `checks.py`.
A `model-id-agreement` check added to `scaffold_lint.py` (item 6) will, by contrast, correctly
**stay scaffold-local** (consistent with the golden-source-only precedent) and will NOT reach
downstream repos automatically — which is fine, since it enforces an invariant on THIS repo's own
prompt surface, not a per-repo runtime concern (same reasoning as `budget-agreement` today).

---

## Surprises worth flagging

1. **`.claude/worktrees/analyze/`** — an untracked (not in `git ls-files`), apparently leftover
   git-worktree directory containing a near-complete duplicate of the repo tree (including its own
   copies of `AGENTS.md`, skills, archived changes, etc.) sits inside `.claude/worktrees/`. It
   inflated my first broad grep's file/occurrence counts substantially and is almost certainly a
   stale isolated-agent worktree from a prior session that was never cleaned up. It is NOT part of
   the live instruction surface (untracked, outside any manifest) and I did not touch it, but a
   `scaffold_lint.py`-based scan (or any file-walking check) should exclude `.claude/worktrees/`
   the same way `checks.py`'s `_iter_py_files` had to learn to skip hidden dirs after the
   `detector-filewalker-scans-hidden-dirs` ratchet entry (`knowledge/ratchet-log.md:27`) — worth a
   one-line note in whichever OW-11 sub-item adds a new file-walking check.
2. **Verify's 5-field notes.md ritual is already inconsistently followed** even before any lint
   exists (see item 2) — two of the three most-recent MEDIUM archived changes skip the exact
   field-numbered format the skill mandates, landing equivalent content in `review-log.md`
   instead. This strengthens the case for `notes_lint.py` (a check would have caught the drift;
   the verbal-echo Step 18 clearly did not).
3. **The AUDIT's "44× across 13 files" model-ID count is already stale** (today: 59×/14 files on
   the same narrow scan, 106×/26 on a broad scan) — model-ID references keep accreting with every
   new skill/agent file (e.g. `composition-audit/SKILL.md` didn't exist at audit time), which is
   exactly the "worth checking forever" argument for landing the lint sooner rather than later —
   the drift is actively still happening.
4. **`openspec validate --changes` reports zero active changes right now** (both open changes lack
   `proposal.md`) — item 7's gap is not a hypothetical, it is the LIVE state of this exact repo
   today. Any change made under the MEDIUM lane between now and OW-11 landing is unvalidated.
5. **`openspec list --json`** (unaffected by the proposal.md gate) is the right tool for
   change-discovery-by-dir generally — worth reusing its output shape/convention (`{name,
   completedTasks, totalTasks, lastModified, status}`) as a model for how a new "discover changes
   by dir" check should enumerate changes, rather than reinventing directory-walking logic.

---

## Summary table (one line per sub-item)

| # | Sub-item | Current state | Proposed mechanization | Est. complexity |
|---|---|---|---|---|
| 1 | Verify steps 12-16 de-bloat | Steps 13-14 instruct fuzzy "search codebase for keywords / assess if implementation likely exists"; no CLI backs requirement-level status (only artifact-level via `status --json`) | Structural requirement/scenario-header enumeration (script) cross-checked against `tasks.md` completion + a short LLM coherence note, replacing the semantic keyword-search instruction | Moderate (needs a small structural scanner; semantic-match judgment stays LLM) |
| 2 | Step 18 ritual → `notes_lint.py` | Step 17 (44 lines) mandates 5 notes.md fields; Step 18 (23 lines) mandates a separate verbal echo as a distrust-forcing-function; both fields are already inconsistently followed in real archived changes | `notes_lint.py`/`checks.py` builtin asserting the 5 fields are present (by heading/marker) in `notes.md`; delete Step 18 entirely, trim Step 17 to the substance | Trivial-to-moderate (markdown heading/field presence check; already-precedented shape) |
| 3 | `freeze-check` script | Freeze ladder in propose is prose (`SKILL.md:112-137`); reviewer emits `## Review Round`, 🔴/🟡/💡 markers, `PREMISE: AGREE\|DISSENT` (verdict line itself is NOT strictly templated for 🔴-count today) | Script parsing `## Review Round` + counting 🔴 (or, better, tighten reviewer prompt to also emit a `FREEZE: READY\|BLOCKED` token like the verifier's `VERDICT:` line) + `PREMISE:` regex → FREEZE-OK/BLOCKED | Moderate (the 🔴-count parse is the fragile part; may require a companion prompt-template tightening) |
| 4 | explore→propose slug-match warning | Exact-match only (`[ -d "plans/<name>" ]`); mismatch is a documented "intentional silence" — brief + premise review orphan permanently, nothing re-scans `plans/` | Add a near-match warning step in propose (list `plans/*/`, flag close kebab-case matches, prompt operator) | Trivial (a few lines of shell/glob logic inline in the skill) |
| 5 | Concurrent COMPLEX verifier passes | Currently sequential by skill prose (arrow-chain, two separate invocation blocks, sequential gate-recovery rule); harness already supports background launch for both | Launch both `opencode run` calls in the same turn, wait for both exit-sentinels, THEN apply existing (unchanged) fix/re-run gate logic only on the failing pass | Trivial (skill-prose reordering only; no new plumbing needed) |
| 6 | Model-ID agreement lint | 59 occurrences/14 files (narrow scan) or 106/26 (broad); zero drift in spelling today but zero guard against future drift; `budget-agreement` in `scaffold_lint.py` is a directly reusable template; no canonical enumerable model-id list exists yet (only prose) | New `scaffold_lint.py` check reusing `_scan_file_set` + a new sanctioned-list added near `AGENTS.md`'s existing `model-assignment-matrix` canonical marker | Trivial-to-moderate (mirrors an existing check almost exactly; only new piece is the canonical list itself) |
| 7 | `medium-change-spec-delta-unvalidated` | Confirmed live: `openspec validate` (any form) sees zero of the 2 currently-open changes (both lack `proposal.md`) because the CLI's `getActiveChangeIds()` is proposal.md-gated by design; no CLI entry point exists for pre-archive delta specs | New `checks.py` builtin (`spec-delta-structure`): discover change dirs by presence, structurally validate `specs/**/spec.md` deltas (ADDED/MODIFIED/REMOVED/RENAMED header, SHALL-on-first-line, Scenario WHEN/THEN) — re-implemented, not proxied (no CLI hook exists to delegate to) | Moderate (genuine re-implementation of a validation subset; not a thin wrapper) |
| 8 | Bloat sizing | verify 494 / explore 339 / propose 333 lines; explore majority (~63% by my count, AUDIT says ~85%) is stance/ASCII-gallery prose with no mechanized effect | Trim explore's worked-dialogue/gallery sections; explicitly secondary to the mechanized-gate items | Trivial to execute, but out of scope priority-wise per the task brief |
| 9 | Scaffold-managed propagation | verify/explore/propose SKILL.md + delegation-harness.md ARE manifest-listed (propagate automatically); `scaffold_lint.py` is deliberately NOT manifest-listed (golden-source-only, per recorded decision); a new standalone lint script needs an explicit manifest line, but a new `checks.py` builtin propagates for free | No new mechanism needed — just route each new check to the right host (checks.py for cross-repo-relevant checks like items 1/2/7; scaffold_lint.py for scaffold-prompt-only checks like item 6) and remember the manifest line for anything else | N/A (routing decision, not a build item) |

**Worth doing vs. deferring (my read, given effort):**
- **Do now, cheap, high-value:** #5 (concurrent COMPLEX passes — pure prose reorder, real
  wall-clock win, zero new mechanism), #4 (slug-match warning — a few lines), #6 (model-id lint —
  near-exact template reuse), #2 (`notes_lint.py` — precedented shape, and real evidence of drift
  it would have caught).
- **Do, moderate effort, clearly load-bearing:** #7 (spec-delta validation — the ratchet-log entry
  already escalated a real near-miss; needs its own small parser but the shape is well-understood
  from openspec's own validator rules) and #3 (`freeze-check` — moderate because the 🔴-count
  parse is fragile without a prompt-template tightening alongside it).
- **Do, but the harder/fuzzier one:** #1 (verify steps 12-16) — the deterministic half (structural
  requirement/scenario enumeration) is clean, but deciding exactly how much of the semantic
  "does implementation satisfy this requirement" judgment to keep vs. fold into a shorter note
  needs a design call, not just a mechanical swap.
- **Defer / secondary per the task brief itself:** #8 (explore bloat trim) — real, but explicitly
  told to treat as secondary to the mechanized gates.
- **Not a build item:** #9 — it's the routing/propagation answer that the other 8 already need,
  not an independent deliverable.
