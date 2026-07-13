# Research — ratchet and verify contracts (for correctness-audit-skill / OW-5)

Distilled from two frozen-but-unapplied OpenSpec changes:
- `openspec/changes/lesson-check-ratchet/` (OW-2, the finding-closure ratchet) — propose
  complete, paused at apply.
- `openspec/changes/verify-stack-redirect/` (OW-3, verify lens redirect) — propose
  complete, paused at apply.

Both are apply-pending: none of their scripts, lint checks, or skill-text edits exist in
the live tree yet. Everything below is the *frozen contract text*, not yet-observable
behavior.

---

## 1. OW-2 ratchet contract

**Core rule.** A *generalizable* finding (a defect class that could recur in sibling
code — not a one-off instance) is not "closed" until `knowledge/ratchet-log.md` records
exactly one disposition for its class. Five dispositions exist, with a normative
preference ordering **check > frozen test > waiver**; `open` is a temporary deferral
state, `grandfathered` is legal only for pre-ratchet legacy lessons.

**Disposition ledger.**
- File: `knowledge/ratchet-log.md` (new, scaffold-bootstrapped, lint-guarded on
  existence — absent file lints clean, same shape as `_check_audit_log`).
- Line format (registry-line, `·`-separated, same shape class as `knowledge/audit-log.md`):
  ```
  - **YYYY-MM-DD** · <kebab-class-slug> · <disposition> — <essence / source refs>
  ```
- Allowed `<disposition>` values (exactly one per line):
  | Disposition | Form | Lint verification |
  |---|---|---|
  | check | `check:<pointer>` | pointer resolves — `check:checks/<file>.py` (per-repo invariant) or `check:<script>.py::<name>` (named function/registry entry, verified by grepping the name in that file) |
  | frozen test | `test:<path>[::<name>]` | file exists; if `::<name>` present it must appear textually in the file (bare path = existence only) |
  | waiver | `waiver:review-by YYYY-MM-DD` | reason (essence) present; valid ISO calendar date; flagged once past |
  | open | `open:since YYYY-MM-DD` | valid ISO date; flagged once older than the configured age threshold |
  | grandfathered | `grandfathered` | format only — no liveness/date checks at all |

  All dates must be real ISO 8601 calendar dates (`2026-13-01` / `not-a-date` are lint
  findings, not silently skipped). `test:` pointers SHOULD (not MUST) include `::<name>`.

**Per-repo invariant-detector registration framework** — the "cheap enforcement slot" a
`check:` disposition points at:
- New stdlib-only runner `scripts/repo_lint.py`. Discovers checks via a flat, sorted,
  non-recursive `checks/*.py` glob — the sibling convention to `data_lint.py`'s
  `checks/*.sql` glob, sharing the same `checks/` directory with disjoint extensions.
- Check-file contract: one file = one invariant; invoked as `<python> <file> <repo-root>`
  in a subprocess (per-check timeout, default 120s, `--timeout` override); the script
  prints a JSON array of findings `[{"path", "line", "message"}]` to stdout (empty array
  = pass) and exits 0. Any nonzero exit / unparseable stdout / timeout = infra failure;
  the runner **stops at the FIRST infra failure** (later sorted files do not run) and
  exits 3.
- Exit codes: **0 clean / 2 findings / 3 infra** — byte-consistent with `data_lint.py`.
- JSON artifact `repo_lint.json`: `generated_by` + per-check `{name, status, findings,
  sample}`, `sample` capped by `--max-sample` (default 5), `findings` holds full count.
- `scripts/checks.py` registration: new registry entry **`repo-lint`** (tier `floor`,
  kind `delegate`, family `check`), placed directly after `data-lint`. Auto-detect
  trigger: `_autodetect_defaults()` extended to return True when any `checks/*.py`
  exists (separate glob from the existing `*.sql` `has_checks` gate). Config section
  **`[checks.repo-lint]`** in `checks.toml`: `enabled` (bool override) and `paths` (first
  entry = checks dir; a second entry is an explicit INFRA-FAIL, the `data-lint` rule).
  Invocation: `checks.py` imports `repo_lint.main()` and calls it in-process with
  `--json <out>/repo_lint.json` and `--checks-dir <dir>`, then reads the JSON artifact
  for aggregate count/status — same pattern as `data-lint`. Findings are **NOT** merged
  into the aggregate `findings.json`.
- Trust model: check files are repo-trusted code, same class as `[checks.custom.*]`
  commands — check-only is the *configuring repo's* responsibility, not enforced by a
  sandbox. Admission bar (Tricorder criteria): near-zero false positives + an obvious,
  actionable fix; noisy checks get tuned or demoted to a ledger waiver. Target scale:
  D4, ~5–15 intentional invariants per repo, grown from incidents — not a general lint
  suite. Graduation path if a repo outgrows bespoke stdlib checks: an external engine
  (ast-grep named specifically) via the existing `[checks.custom.*]` escape hatch —
  external scanners are deliberately never a scaffold dependency (stdlib-only is a hard
  constraint: `openspec/config.yaml` pins scaffold scripts to Python 3.13,
  stdlib-only, no third-party runtime deps).

**Scaffold files OW-2's tasks touch** (from `tasks.md`):
- New: `scripts/repo_lint.py`, `scripts/test_repo_lint.py`, `knowledge/ratchet-log.md`
  (bootstrapped with 3 literal entries).
- Modified: `scripts/checks.py` (registry entry + `_autodetect_defaults()`),
  `scripts/test_checks.py`, `scripts/knowledge_lint.py` (new `_check_ratchet_log`,
  `CANONICAL_MAP` + `EPHEMERAL_PATHS` additions, `ratchet_open_max_age_days` added to
  `_load_knowledge_lint_config()`'s return dict, default 30), `scripts/test_knowledge_lint.py`.
- Docs/skills: `knowledge/README.md` (Reference taxonomy row gains `ratchet-log.md`
  alongside `audit-log.md`, no new row), `AGENTS.md` (one bullet in `## Working process`,
  inside the synced span, citing `finding-closure-ratchet` as canonical),
  `scripts/scaffold_manifest.txt` (adds `repo_lint.py` + `test_repo_lint.py`, placed
  adjacent to the `data_lint.py` / `test_data_lint.py` siblings, no reordering).
- Skills: `.claude/skills/openspec-archive-change/SKILL.md` (Step 6, new sub-bullet
  **between** "Quality check" and "Lint before committing"), `.claude/skills/run-audit/SKILL.md`
  (Step 3, Triage), `.claude/skills/knowledge-drift-review/SKILL.md` (Step 2 / Class B,
  one bullet: spot-check `check:`/`test:` entries whose artifact exists but no longer
  exercises the recorded class — the semantic-drift residue the deterministic liveness
  check cannot see).
- Explicitly NOT synced (per-repo content): `knowledge/ratchet-log.md` content,
  `checks/` contents, `checks.toml`.

**Out of scope (explicit, from proposal.md § Out of Scope):**
- OW-1's generic test-quality detectors and OW-4's generic data-scale detector (separate
  upstream changes; natural first tenants of the framework, not built here).
- **OW-5 `correctness-audit` and OW-6 composition-audit skills — "they consume this
  change's routing interface later," not built here.**
- Retroactive remediation of the extrends/psc-monitor audit backlogs (downstream work).
- Back-filling ledger entries for every existing `lessons.md` entry (legacy entries are
  `grandfathered`; a one-time triage sweep is parked as follow-on).
- Auto-wiring downstream repos' invariants or config (D7: downstream repos land their
  own invariants/config as follow-on SMALL changes).

**Hooks OW-2 defines for future audit skills (the OW-5 integration point).** This is the
single most load-bearing paragraph for OW-5, quoted from proposal.md:

> **Close-out routing:** the two existing finding close-out points each gain one bounded
> ratchet-triage step — the **archive** skill (bugs found+fixed during a change) and the
> **run-audit** skill's triage step (deterministic findings judged real). The step is a
> ≤3-question classification producing one ledger line plus the enforcing artifact or
> waiver. **Future audit skills (OW-5 correctness-audit, OW-6 composition-audit) route
> into this same interface; they are not built here.**

The triage decision rule (design.md D4), which any future audit skill's close-out step
must reproduce or reuse:
```
Q1  Real defect (not noise/env)?                 no → stop (no entry)
Q2  Generalizable class (sibling could recur)?   no → stop (point fix suffices)
Q3  Mechanically detectable or test-freezable?
      yes → disposition check: / test: (artifact ships with the fix; open: if deferred)
      no  → waiver:review-by <date> — <why domain-judgment-only>
```
Spec requirement `close-out-gates-route-findings-into-the-ledger` codifies this: the
triage is performed by the **orchestrating agent** (judgment work), *never* delegated to
a mechanical executor, and never blocks a change on building a detector (`open` exists
for exactly this deferral). Q1/Q2 = no → **no ledger entry** (the ledger holds classes,
not noise or one-offs) — this is an explicit spec scenario, not an inference.

---

## 2. OW-2 spec requirements (verbatim headers)

### `finding-closure-ratchet` (ADDED Requirements)
1. **`generalizable-findings-close-only-with-a-recorded-disposition`** — a generalizable
   finding SHALL NOT be closed until the ledger records one of check/test/waiver/open/
   grandfathered, preference order check > frozen test > waiver.
   **Known validator issue:** `openspec validate lesson-check-ratchet --strict` still
   errors today — `ADDED "generalizable-findings-close-only-with-a-recorded-disposition"
   must contain SHALL or MUST` — even though the requirement body contains "SHALL NOT."
   This is recorded as finding 1 in
   `knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md` (line ~108-113):
   the fix is noted as "the Opus apply session for OW-2 should make the one-word
   normative fix before delegating apply." Confirmed still failing by direct
   `openspec validate` run during this research pass — treat as a live, unresolved
   defect in OW-2's frozen artifact, not a hypothetical.
2. **`ratchet-ledger-has-a-lintable-registry-format`** — the ledger holds one
   registry-format line per class; disposition keyword and date validity are
   machine-checkable; ledger format is scaffold-defined, content is per-repo.
3. **`enforcement-pointers-are-verified-live-not-declarative`** — the linter verifies
   `check:`/`test:` pointer liveness (file exists; `::<name>` textually present when
   given); stale waivers and aged `open` entries are flagged; `grandfathered` gets
   format-only checking.
4. **`close-out-gates-route-findings-into-the-ledger`** — archive's primary-review step
   and run-audit's triage step each carry the ≤3-question triage; a qualifying finding
   yields one ledger line; Q1/Q2 = no yields no entry; triage is orchestrator judgment,
   never the mechanical executor.

### `repo-invariant-checks` (ADDED Requirements)
1. **`one-dropped-file-registers-a-code-shape-invariant`** — `repo_lint.py` discovers
   invariants via a flat, sorted `checks/*.py` glob; each check is a standalone
   subprocess-invoked script emitting a JSON findings array.
2. **`runner-fails-loud-and-is-time-bounded`** — any nonzero exit / unparseable stdout /
   timeout is an infra failure; the run stops at the first one; exit codes 0/2/3 match
   `data_lint.py`.
3. **`runner-registers-as-a-delegating-check`** — `checks.py` registers `repo-lint` as an
   auto-detected, overridable, delegating check whose findings are not merged into the
   aggregate `findings.json`.
4. **`invariants-are-check-only-and-repo-trusted`** — check files are repo-trusted,
   check-only by documented convention (not sandboxed); admission bar is near-zero-FP +
   actionable fix; graduation path is an external engine via `[checks.custom.*]`; target
   scale ~5–15 invariants per repo.

---

## 3. OW-3 verify-lens contract

**New pass chains per tier** (from `specs/verify-multimodel-gate/spec.md`, MODIFIED
requirement `Verify runs independent multi-model passes after the self-review`):
- **SMALL:** unchanged — a single REQUIRED `deepseek/deepseek-v4-flash` behavioral
  verifier pass, run *outside* the verify skill.
- **MEDIUM:** self-review → one `deepseek/deepseek-v4-pro` **behavioral** verifier pass.
  (The old third same-checklist flash pass is dropped — "the recorded three-repo history
  showed zero non-trivial defects uniquely caught by a same-checklist third pass.")
- **COMPLEX:** self-review → `deepseek/deepseek-v4-pro` behavioral pass →
  `deepseek/deepseek-v4-flash` **lens** pass.
- The sequence is identical on both orchestrator platforms (Claude Code and OpenCode).

**What a "lens" is:** a fixed *prompt* (a different checklist), not a detector and not a
different model or agent. Per the ADDED requirement `The COMPLEX third pass runs a lens
the behavioral stack lacks`: "a fixed prompt asking questions the behavioral checklist
does not ask, rather than a third run of the same behavioral checklist." Both the
behavioral pass and the lens pass are served by the **same single agent file**
(`.opencode/agents/openspec-verifier.md`) — the invocation's fixed prompt is the only
parameterization point; no second agent, no new permission surface. Both pass types emit
the **identical verdict block**: `## Verify Pass — <model>` heading, `VERDICT: READY` /
`VERDICT: NEEDS REVISION` line, `### Defects` section (always present, `- None` when
clean) — this is explicit design intent so "the orchestrator's gate mechanics need no
per-lens handling."

**Lens selection rule.** The orchestrator selects the lens **per change** and records the
selection with a one-line rationale in `review-log.md`:
- **Test-quality / adversarial-oracle lens — the default.** For each added/modified
  test: would it fail if the behavior broke (name the tripping assertion)? Flags
  tautological/forced-green asserts, empty test bodies, self-mocking of the module under
  test, discarded return values/flags, unfrozen clocks.
- **Data-scale lens — for data-path-dominant changes.** Which input domains are
  unbounded in production; full materialization of unbounded queries (`fetchall()` et
  al.); at-scale-run need or a recorded bounded-domain argument.
- MEDIUM changes MAY opt into a lens pass under the same contract when risk warrants it
  (not mandatory at MEDIUM).
- The lens pass is **diff-scoped**: no mandatory full-suite rerun (the pro pass already
  did that); targeted probes are allowed.

**Where lens prompts live:** inlined as fenced blocks directly in
`.claude/skills/openspec-verify-change/SKILL.md` — task 1.3/1.4 explicitly *remove* both
occurrences of "the fixed verifier prompt from design D5" / "the verifier prompt from
design D5" so the skill no longer points into an archived change's `design.md`.

**Files OW-3 touches** (from `tasks.md`):
`.claude/skills/openspec-verify-change/SKILL.md` (core rewrite: pass-sequence prose,
invocation subsection, inlined behavioral + lens prompts, gate-semantics recovery
ladder, attribution vocabulary sweep), `.claude/skills/_shared/delegation-harness.md`
(§e verifier row renames — `verifier (behavioral pass, pro)` /
`verifier (lens pass, flash — COMPLEX only)` — budgets **unchanged**, `780`/`-k 15`,
because `scaffold_lint.py`'s budget-agreement check byte-compares embedded timeout pairs
against this table), `AGENTS.md` (verifier-role bullet in `## Roles`; chain mentions in
workflow step 4, tier bullets, "After reading this file"; one surgical parenthetical fix
in the SMALL bullet so it doesn't dangle), `.opencode/agents/openspec-verifier.md` (body
generalized to run either prompt type; `description:` updated; `permission:` block
untouched), spec deltas for `verify-multimodel-gate` and `noninteractive-delegation-safety`,
and (verified-no-op) `knowledge/lessons.md` (review round 1 found no chain-shape
assertion to fix — task reworded to conditional). `knowledge/STATUS.md`'s historical
chain vocabulary is explicitly **not** an apply-time edit (archive-reconciled instead).

**What OW-3 says about future lenses / audit skills.** The ADDED requirement's closing
sentence is the literal detector-handoff hook: "A prompt-based lens is a stepping stone
with lower precision than a deterministic detector; when a corresponding detector ships
(e.g. a test-quality or data-scale check), the lens prompt SHALL direct the verifier to
run and confirm the detector's findings rather than rediscover them." `research/touch-surface.md`
§10 in OW-3 directly analyzes the OW-2/OW-3 relationship (see § 5 below for the
synthesis) and names the OW-1 (`"would this test fail if the behavior broke?"`) and OW-4
(`"at-scale run or recorded bounded-domain argument"`) candidate lens texts verbatim —
but notes neither OW-1 nor OW-4 exists yet as a change, so OW-3's lens prompts had to be
authored fresh rather than borrowed. **OW-5/OW-6 are not named as lens candidates
anywhere in OW-3's artifacts** — the v1 lens menu is exactly two entries (test-quality,
data-scale); OW-3's own success criteria describe it as extensible ("Lens prompts
inline, canonical, and cite-able by OW-1/OW-4 when their detectors land") but does not
commit to a third lens slot for a correctness-audit-shaped prompt.

---

## 4. OW-3 spec requirements (verbatim headers)

### `verify-multimodel-gate` (MODIFIED unless marked ADDED)
1. **`Verify runs independent multi-model passes after the self-review`** (MODIFIED) —
   tier-keyed, platform-uniform pass sequence (MEDIUM 2 passes, COMPLEX 3, SMALL
   unchanged); no pass is a third run of the same behavioral checklist.
2. **`Each verification pass is a hard gate with rerun-failed-and-after recovery`**
   (MODIFIED) — fix → re-run the failed pass and every pass after it (never before);
   3-cycle non-convergence escalates to the operator.
3. **`The delegated verifier runs the behavioral review read-only and emits a
   machine-discriminable verdict`** (MODIFIED) — behavioral pass = full self-review
   equivalent (diff, full suite, real-output eyeball, live smoke); lens pass = the lens
   checklist instead; verifier never edits files; shared verdict-block contract.
4. **`A single verifier agent serves both models, invoked via opencode run on both
   platforms`** (MODIFIED) — one agent file, `--model` flag per pass overrides the
   frontmatter default (`deepseek/deepseek-v4-flash`).
5. **`Each pass's verdict and model are recorded`** (MODIFIED) — report/`notes.md`
   record model, verdict, lens + rationale (when applicable), and which pass surfaced
   each fixed defect.
6. **`The COMPLEX third pass runs a lens the behavioral stack lacks`** (ADDED) — the v1
   lens menu (test-quality default, data-scale for data-path changes), diff-scoped,
   detector-handoff sentence, MEDIUM opt-in, same hard-gate/recovery semantics.

### `noninteractive-delegation-safety` (MODIFIED)
1. **`Delegated opencode invocations are hardened against permission hangs`** (MODIFIED)
   — every delegated `opencode run` (propose reviewer, apply executor, archive executor,
   verify fix-executor, and **both** verifier passes — pro behavioral and, for COMPLEX,
   flash lens) SHALL close stdin (`< /dev/null`) and pass `--dir <repoRoot>`; removes the
   stale abandoned-OpenCode-Task-tool exemption language; permission posture itself is
   untouched — the lens pass reuses the same agent, so all existing containment
   requirements apply unchanged.

---

## 5. Integration surface for OW-5

**Two distinct, non-overlapping plug-in points exist — pick based on how OW-5 runs:**

1. **If OW-5 (`correctness-audit`) runs as a verify-phase pass** — extending the v1 lens
   menu that OW-3's ADDED requirement `The COMPLEX third pass runs a lens the behavioral
   stack lacks` establishes. A correctness-audit lens would be a third fixed prompt
   (inlined in `.claude/skills/openspec-verify-change/SKILL.md` alongside the
   test-quality/data-scale prompts), selected by the orchestrator with a recorded
   one-line rationale in `review-log.md`, sharing the identical `## Verify Pass — <model>`
   / `VERDICT:` / `### Defects` verdict-block contract so the gate mechanics need no
   special-casing. This is a lens-menu extension, not a new mechanism.
2. **If OW-5 runs as a standalone audit cycle** (the shape `OUTSTANDING-WORK.md`
   actually describes it as — "standardizing the wave/charter/census shape" like
   `run-audit`, not a verify-phase pass) — its close-out step plugs directly into OW-2's
   **`close-out-gates-route-findings-into-the-ledger`** interface, the same way
   `run-audit`'s Step 3 triage does: findings judged real by OW-5's own audit logic are
   then run through the shared Q1(real?)/Q2(generalizable?)/Q3(detectable/test-freezable?)
   triage and land as `knowledge/ratchet-log.md` registry lines. This is the
   explicitly-named consumption path from OW-2's proposal.md ("Future audit skills (OW-5
   correctness-audit, OW-6 composition-audit) route into this same interface; they are
   not built here.").

   `OUTSTANDING-WORK.md`'s own OW-5 entry frames it this second way: "a skill
   standardizing the wave/charter/census shape that **routes every generalizable finding
   into OW-2's ratchet** on close." Treat plug-in point 2 as primary; plug-in point 1 is
   a secondary option only if OW-5 is redesigned to also produce a verify-time prompt
   pass (not indicated by current backlog text).

**Vocabulary/formats OW-5 must reuse to avoid drift** (do not invent parallel spellings):
- Ledger line format, verbatim: `- **YYYY-MM-DD** · <kebab-class-slug> · <disposition> — <essence>`.
- Disposition keywords, verbatim: `check:<pointer>`, `test:<path>[::<name>]`,
  `waiver:review-by YYYY-MM-DD`, `open:since YYYY-MM-DD`, `grandfathered`.
- The 3-question triage, verbatim order: Q1 real defect? → Q2 generalizable class? → Q3
  mechanically detectable or test-freezable?
- If OW-5 ever runs as a verify pass: the verdict-block contract, verbatim: `## Verify
  Pass — <model>` heading, `VERDICT: READY` / `VERDICT: NEEDS REVISION`, `### Defects`
  section always present.
- `checks.toml` config surface pattern (if OW-5 ever needs a config knob): the
  `[knowledge_lint]` table precedent (`ratchet_open_max_age_days`) and the
  `[checks.<name>]` table precedent (`enabled`, `paths`) — both are the established
  shapes; do not invent a third config dialect.

**Sequencing constraints:**
- **OW-2 and OW-3 are mutually independent** — OW-3's own research explicitly settles
  this (`research/touch-surface.md` §10, verify-stack-redirect): "OW-2 doesn't need to
  ship before OW-3, and OW-3 doesn't depend on OW-2's ledger mechanism at all." They are
  complementary (OW-2 = closure/enforcement mechanism for findings already surfaced
  elsewhere; OW-3 = a verify-time prompt lens) but do not gate each other.
- **OW-5 is different: it has an explicit, one-directional dependency on OW-2.**
  `OUTSTANDING-WORK.md`'s OW-5 entry states `Deps: land after OW-2 so findings have
  somewhere to go` — this is an **apply-order** dependency, not merely a propose-order
  one: OW-5's close-out step needs `knowledge/ratchet-log.md`'s format, `_check_ratchet_log`
  lint, and the archive/run-audit triage text to be **live in the repo**, not just frozen
  as spec-delta text in an unapplied change directory. Since OW-2 is currently paused at
  apply (propose complete, artifacts frozen, apply not yet run), **OW-5's own apply
  should not land before OW-2's apply completes** — OW-5's design/propose work can
  proceed now (citing OW-2's frozen contracts, as this document does), but its
  implementation would have nothing live to route findings into until OW-2 ships.
- **Pre-apply spec cross-referencing is safe; pre-apply behavioral dependency is not.**
  Both OW-2 and OW-3 are frozen-text (proposal/design/spec/tasks all written and
  reviewed) but neither is applied — none of `scripts/repo_lint.py`,
  `knowledge_lint.py`'s ratchet checks, `knowledge/ratchet-log.md`, or the verify SKILL's
  inlined lens prompts exist in the live tree yet. OW-5's design can reference and rely
  on the *frozen contract text* of both changes (as this research file does) for
  planning purposes, but cannot assume any of these mechanisms are runnable until each
  change's `tasks.md` is actually executed. If OW-5's design work finishes before OW-2
  applies, that's fine (propose/design don't need live mechanisms); OW-5's **apply**
  phase is what is gated on OW-2's apply.
- **No stated dependency of OW-5 on OW-3.** Unless OW-5 is redesigned to plug into the
  verify-phase lens menu (plug-in point 1 above), it has no sequencing requirement
  relative to OW-3's apply status.
