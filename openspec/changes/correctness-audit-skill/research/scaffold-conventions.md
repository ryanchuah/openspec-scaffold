# Scaffold conventions a `correctness-audit` skill must follow

Research pass for the `correctness-audit-skill` OpenSpec change. Covers: skill-file
conventions, propagation mechanics, existing capability-spec inventory, delegation-harness
obligations, and the output-location contract for FINDINGS files. All citations are
`file:line` against the state of this repo at commit `3f18fe7`.

---

## 1. Skill-file conventions (frontmatter, structure, tone, operator-gating)

All three existing audit-family skills — `.claude/skills/run-audit/SKILL.md`,
`.claude/skills/knowledge-drift-review/SKILL.md`, `.claude/skills/outstanding-work-review/SKILL.md`
— share one shape. A new `correctness-audit` skill should match it exactly; deviating in
frontmatter shape or tone is what `scaffold_lint.py` and the manifest are built to catch.

**Frontmatter** (identical field set across all three, `run-audit/SKILL.md:1-10`,
`knowledge-drift-review/SKILL.md:1-10`, `outstanding-work-review/SKILL.md:1-10`):
```yaml
---
name: <skill-name>              # matches the .claude/skills/<name>/ dir exactly
description: <one sentence>     # states WHAT it does, WHEN to invoke, and its gating word
license: MIT
compatibility: Requires openspec CLI.
metadata:
  author: openspec
  version: "1.0"
  generatedBy: "1.4.1"
---
```
No other frontmatter keys are used (no `tags`, no `trigger`, no `argument-hint`). The
`description` line is the single most load-bearing sentence — it is what the harness/operator
sees when deciding to invoke the skill, and it is scanned by `scaffold_lint.py`'s
`dangling-skill-refs` check indirectly (via cross-references elsewhere, see §2).

**Length norm:** run-audit is 117 lines, knowledge-drift-review is 105 lines,
outstanding-work-review is 87 lines. All are single-file, no sub-resources. A wave-fanning
`correctness-audit` skill doing more (multiple LLM audit waves) can run longer, but should stay
a single self-contained `SKILL.md` unless it genuinely needs shared sub-docs (see the
`_shared/` pattern in §4).

**Structure norm — every skill body follows this exact shape:**
1. One-paragraph restatement of the frontmatter description (not verbatim, but rephrased with
   the specific mechanism named), e.g. `run-audit/SKILL.md:12-14`, `knowledge-drift-review/SKILL.md:12-13`.
2. A cadence/scope callout in **bold-lead** style — `**Ceremony vs day-to-day.**`
   (`run-audit/SKILL.md:16`), `**Cadence — operator-invoked / periodic, NOT every archive.**`
   (`knowledge-drift-review/SKILL.md:15`), `**Pull-only.**` (`outstanding-work-review/SKILL.md:18`).
   This is where the skill states its own boundary before any steps are given.
3. **Interpreter convention** block, verbatim boilerplate in run-audit and
   outstanding-work-review (`run-audit/SKILL.md:23-28`, `outstanding-work-review/SKILL.md:21-26`):
   resolve `<py>` via try-order (repo `audit-*` task-runner target → `.venv/bin/python` →
   `python3` → `python`). knowledge-drift-review inlines the same try-order as a one-line note
   instead of a named block (`knowledge-drift-review/SKILL.md:29`) — both forms are accepted by
   the lint surface (it is prose, not mechanically checked), but reusing the named-block form is
   the closer match to two of three precedents.
4. **Numbered procedure** (`Steps` or `Cycle steps` heading, or no heading at all before the
   list — knowledge-drift-review omits a heading and just numbers `1.`–`5.` under `**Steps**`,
   `knowledge-drift-review/SKILL.md:25`). Each step is bold-titled
   (`**Discover.**`, `**Run.**`, `**Triage.**`, `**Anchor (operator-gated).**`, `**Log.**` in
   run-audit; `**Gather.**`, `**Read.**`, `**Judge (orchestrator).**`, `**Verify.**` in
   outstanding-work-review). Bash invocations are fenced ` ```bash ` blocks using the `<py>`
   placeholder, never a hardcoded `python3`.
5. An **Output** section with a literal template block when the skill's job is to emit a
   structured report (knowledge-drift-review only, `knowledge-drift-review/SKILL.md:78-97`) —
   run-audit and outstanding-work-review skip this because their artifacts are files, not a
   chat-turn report.
6. A closing **Guardrails** bullet list — every skill ends with this heading
   (`run-audit/SKILL.md:110-116`, `knowledge-drift-review/SKILL.md:99-104`,
   `outstanding-work-review/SKILL.md:78-86`). This is where operator-gating and
   never-do statements live, always as terse bullets, never prose paragraphs.

**Tone:** imperative, second-person-implicit ("Run the linter first", "Do not fix"), no
hedging, no marketing language. Every skill states what it will **never** do as prominently as
what it does (e.g. "Never fixes code" is in run-audit's own frontmatter `description` field,
`run-audit/SKILL.md:3`).

**Operator-gating language patterns** (a new audit skill fanning out LLM waves should reuse
these verbatim phrasings, not invent new ones):
- `"operator-gated"` — used as a parenthetical step qualifier: `**Anchor (operator-gated).**`
  (`run-audit/SKILL.md:58`) — the step only fires "when the operator's invocation explicitly
  asks to ... 'tag' or 'anchor this audit'" (`run-audit/SKILL.md:58-60`).
- `"Operator-invoked"` in the frontmatter `description` itself, e.g.
  `outstanding-work-review/SKILL.md:3` ("Operator-invoked, pull-only"),
  `run-audit/SKILL.md:3` ("Operator-invoked").
- `"Pull-only"` / `"never wired into session boot"` — an explicit sentence stating the skill
  is not auto-triggered: `outstanding-work-review/SKILL.md:18-19` ("This skill is never wired
  into session boot or AGENTS.md. Invoke it explicitly...").
- `"Detect-only"` — states the skill never edits tracked files:
  `knowledge-drift-review/SKILL.md:22-23` and reiterated in its own Guardrails
  (`knowledge-drift-review/SKILL.md:101`).
- **Sole-mutation call-outs**: run-audit explicitly names the *one* repo-state mutation
  (`audit_scope.py tag`, `run-audit/SKILL.md:112-113`) and the *one* tracked-file write
  (`knowledge/audit-log.md` append, `run-audit/SKILL.md:114-115`) — everything else is
  read-only. A wave-fanning correctness-audit skill should adopt the same pattern: name
  exactly what state it is allowed to touch, and assert everything else is read-only.

---

## 2. Propagation mechanics for a new skill

**Manifest entries needed** — `scripts/scaffold_manifest.txt:8-17` lists all `.claude/skills/`
entries **file-by-file**, not by directory:
```
.claude/skills/knowledge-drift-review/SKILL.md
.claude/skills/openspec-apply-change/SKILL.md
...
.claude/skills/outstanding-work-review/SKILL.md
.claude/skills/run-audit/SKILL.md
```
A new `correctness-audit` skill needs exactly one new line:
`.claude/skills/correctness-audit/SKILL.md`. If the skill needs shared sub-resources under
`_shared/` (see §4), each such file also needs its own manifest line — the glob in
`scaffold_lint.py` (`.claude/skills/_shared/*.md`, `scripts/scaffold_lint.py:139`) requires it.

**Lint implications** — `scripts/scaffold_lint.py`'s `manifest-completeness` check
(`scripts/scaffold_lint.py:35-51`, `230-252`) walks the glob
`.claude/skills/*/SKILL.md` and fails the build if `SKILL.md` exists on disk but is not listed
in `scaffold_manifest.txt`, or vice versa. This means: **creating the SKILL.md file without
adding the manifest line is a guaranteed lint failure**, and it is checked both directions
(disk→manifest and manifest→disk).

**`manifest-no-conflict`** (`scripts/scaffold_lint.py:52-58`, `276-294`) — the new path must
not simultaneously appear in `scripts/scaffold_manifest_removed.txt`. Not a risk unless the
skill name collides with a previously-removed entry (current removed entries are
`.claude/skills/openspec-onboard/` and `.claude/skills/lint-knowledge/`,
`scripts/scaffold_manifest_removed.txt:10,20` — no collision expected).

**`dangling-skill-refs`** (`scripts/scaffold_lint.py:84-96`, `358-396`) — scans `AGENTS.md`
plus every `.md` under `.claude/skills/`, `.claude/agents/`, `.opencode/agents/` for tokens
matching `\bopenspec-[a-z][a-z-]*[a-z]\b` or an explicit non-`openspec-` token set
(`_NON_OPENSPEC_SKILL_TOKENS`, currently `{"knowledge-drift-review", "run-audit"}`,
`scripts/scaffold_lint.py:168`). **Because `correctness-audit` does not start with
`openspec-`, any prose reference to it (e.g. from `run-audit/SKILL.md` or `AGENTS.md`) will
NOT be auto-validated unless `correctness-audit` is added to `_NON_OPENSPEC_SKILL_TOKENS`.**
This is a concrete code edit the correctness-audit-skill change needs to make in
`scripts/scaffold_lint.py:168` if any scaffold-managed file cross-references the new skill by
name — otherwise references silently go unchecked (not a lint failure, just unvalidated) unless
they happen to already resolve via the skill-dir-name / agent-file-stem fallback
(`scripts/scaffold_lint.py:379-395`, which DOES also accept any literal skill directory name —
so a bare mention of `correctness-audit` in prose actually **would** resolve correctly via
`_skill_dir_names()` without needing the token set change, since the regex `_TOKEN_RE` only
gates `openspec-*` tokens and `_NON_OPENSPEC_SKILL_TOKENS` is an *additional* opt-in scan, not
a gate on what already resolves). Net: no code change is strictly required for
`dangling-skill-refs` to pass, but if the new skill's name is *referenced* from another
scaffold-managed doc, that reference will resolve via `_skill_dir_names()` once the skill
directory exists — verified by reading `scripts/scaffold_lint.py:362-366,379-395`.

**`budget-agreement`** (`scripts/scaffold_lint.py:97-112`, `398-449`) — if the new skill's
`SKILL.md` embeds any `timeout -k <G> <B>` command (which a wave-fanning skill almost certainly
will, per §4), the exact `(G, B)` pair must already exist in the sanctioned set parsed from
`.claude/skills/_shared/delegation-harness.md`'s §e table (`delegation-harness.md:83-98`). An
unsanctioned pair fails the lint. See §4 for the exact sanctioned pairs.

**SEAL implication** — `scripts/test_scaffold_lint.py:510-533`'s `test_live_repo_lints_clean`
runs `scaffold_lint.collect_findings()` against the real repo tree (not a fixture) and asserts
zero findings; the docstring explicitly frames this as a SEAL: any future instruction-file edit
that introduces a scaffold-lint violation fails the suite by design, and the correct response is
to fix the violating file, never loosen the test (`test_scaffold_lint.py:513-525`). AGENTS.md's
own reference to this (`AGENTS.md:82`) ties `pytest` (including this SEAL) into the commit-test
gate. **Practical consequence: after adding the new SKILL.md + manifest line (+ any
`_shared/` additions), `python3 scripts/test_scaffold_lint.py` (or the full `pytest` suite) must
pass before commit** — this is enforced, not optional.

---

## 3. Existing capability specs inventory + where correctness-audit fits

`openspec/specs/` contains 12 capability directories (each `spec.md` has a `## Purpose` +
`## Requirements` with `### Requirement: <slug>` subheadings):

| Capability | Requirement slugs (one-line essence) |
|---|---|
| `apply-convergence-guard` | apply-executor stops on non-convergence; detection is deterministic not in-context judgment; a declared blocker is machine-discriminable from an opaque give-up; recovery from a blocker is the orchestrator's call; ships with a hardened, instruction-gated canary |
| `commit-test-gate` | commits are gated on the project's tests; gate is shared logic with one per-repo value; verify's re-run uses the same per-repo test command; instruction docs acknowledge the hook; ships with a smoke fixture + wiring-smoke procedure; fires only on a genuine `git commit` invocation |
| `knowledge-lint` | deterministic linter detects drift; linter is detect-only; retired-path tokens are per-repo extensible; a judgment-layer skill detects semantic drift (this is the spec `knowledge-drift-review` implements); knowledge-lint tooling is scaffold-managed; broken-citation check skips legit notation; `lint:planned` marker suppresses forward refs; root-level handoff files are flagged; detects duplicate content blocks; detects closed-but-unpruned entries; **detects untriaged-finding accumulation** (this is the `_check_untriaged_age` requirement — directly relevant, see §5) |
| `knowledge-organization` | knowledge classified by recoverability rule; each type has one home; boot files each answer one question; storage stays scalable; single archive; migration preserves not-in-code knowledge; archive step reconciles into new structure; archive step flags wider knowledge drift |
| `noninteractive-delegation-safety` | delegated `opencode` invocations hardened against permission hangs; delegated agents leave no reachable ask-permission path; verify verifier denied destructive shell commands; verifier prompt carries a data-safety preamble |
| `outstanding-work-view` | gather produces a complete never-failing snapshot; structured extraction is format-plural with point-only fallback; **findings are first-class with a separate untriaged bucket** (directly relevant, see §5 and §8); per-repo config with graceful defaults; plans live-vs-archived convention; pull-only agent-neutral invocation |
| `premise-review-gate` | premise-review gate vets direction at two altitudes; reviewer emits a premise verdict orthogonal to severity; reviewer reasons read-only, no empirical-proof claims; proposal freezes only on zero blockers AND premise agreement; premise dissent surfaced, never auto-resolved; SMALL premise pass runs pre-apply, gated at apply; explore skill owns the direction gate; explore brief has a defined home/slug/relocation; direction dissent surfaced and override propagates; drift from a verified brief is concretely defined; explore-altitude review calibrated for an abstract brief |
| `reviewer-budget` | reviewer budgeted for thoroughness, never rushed; review output survives a cutoff; reviewer remains read-only |
| `scaffold-sync-mechanism` | manifest declares shared files; sync script copies files; check-mode reports drift; sync is idempotent; pre-commit guard blocks scaffold-managed edits; AGENTS.md span-replace preserves per-repo sections; config rules-block propagates; sync stamps scaffold provenance |
| `shared-lint-gate` | shared ruff config for every repo; `check.sh` is the single definition of green; doc-lints enforced on the live tree; scaffold documents + provisions pinned security scanners; apply executor autofixes touched files before reporting done; shared lint layer is scaffold-managed |
| `tier-confirmation-gate` | an agent without an autonomy grant confirms the change tier before executing |
| `verify-multimodel-gate` | verify runs independent multi-model passes after self-review; each pass is a hard gate with rerun-failed-and-after recovery; delegated verifier runs behavioral review read-only, emits machine-discriminable verdict; orchestrator asserts the real verifier ran and judges from disk; single verifier agent serves both models via `opencode run` on both platforms; each pass's verdict + model recorded; runs a simplicity/quality gate (MEDIUM/COMPLEX); runs a security review for sensitive-surface changes |

**No existing capability spec covers "audit" as a concept in the OpenSpec-contract sense.**
`run-audit`, `knowledge-drift-review`, and `outstanding-work-review` are all **skills**
(`.claude/skills/`) with no corresponding `openspec/specs/*/spec.md` capability of their own —
they are implemented as skill prose plus the `checks.py`/`knowledge_lint.py`/`outstanding.py`
scripts, which in turn ARE covered by capability specs (`knowledge-lint`, `outstanding-work-view`
respectively — note `run-audit` itself has no dedicated capability spec; it composes
`checks.py`'s check/fact engine, which likewise has no capability spec of its own, only its
CLI docstring `scripts/checks.py:1-40` as documentation).

**Implication for OW-5 (correctness-audit-skill):** this is a **new capability**, not a
modification of an existing one. There is no `deterministic-audit-tooling`,
`verify-multimodel-gate`-adjacent, or `outstanding-work-view`-adjacent spec that already
describes "run N LLM audit waves over the codebase and produce FINDINGS." The closest
precedent in *shape* (multi-pass LLM review with verdicts recorded, delegation via `opencode
run`) is `verify-multimodel-gate` — worth reading as a structural template (independent passes,
hard-gate-with-recovery, machine-discriminable verdict, verdict+model recorded) even though its
subject (verifying an implementation against change artifacts) differs from correctness-audit's
subject (auditing existing code for defects). If `correctness-audit` needs its own
`openspec/specs/correctness-audit/spec.md`, model its Requirements section on
`verify-multimodel-gate`'s slug style: `<subject>-<verb-phrase>` in kebab-case, one Purpose
paragraph, one Requirement per invariant, each with `#### Scenario:` sub-blocks
(see `openspec/specs/verify-multimodel-gate/spec.md:7-13` for the exact scenario format).

---

## 4. Delegation-harness obligations for a wave-fanning skill

`.claude/skills/_shared/delegation-harness.md` is the **shared contract** cited (not
duplicated) by the four delegating skills — propose/apply/verify/archive
(`delegation-harness.md:3-4`). A new `correctness-audit` skill that fans out LLM audit waves via
`opencode run` should cite this doc the same way rather than re-deriving its own rules. Its
five clauses:

- **(a) Hardened invocation** (`delegation-harness.md:9-13`) — every `opencode run` closes
  stdin (`< /dev/null`) and passes `--dir <repoRoot>`. Cites the `noninteractive-delegation-safety`
  capability spec for rationale.
- **(b) Assert the real agent ran** (`delegation-harness.md:16-42`) — `opencode run` exits 0
  even on silent agent fallback, so before trusting any wave's output: grep the stderr log for
  `"Falling back to default agent"`; confirm the jsonl output is non-empty/parseable and extract
  the completion text via `grep '"type":"text"' ... | jq -r '.part.text'`; confirm the extracted
  text carries the expected phase-specific output format. **Cross-repo `--dir` gotcha**: if a
  correctness-audit wave needs to run against a *different* repo's code while the agent
  definition lives in the scaffold, `--dir` must point at whichever repo actually contains
  `.opencode/agents/<agent>.md` — Bash calls inside the agent are not `--dir`-restricted, so a
  per-repo `--dir` with absolute-path Bash calls still works; one run per repo, never a shared
  parent dir (`delegation-harness.md:30-42`).
- **(c) Bounded wait + surgical kill** (`delegation-harness.md:46-54`) — every delegated
  `opencode run` wrapped in `timeout -k <grace> <budget>`; never `pkill opencode`/`killall
  opencode` (kills unrelated concurrent runs); exit 124/137 = operational crash, not silent
  failure.
- **(d) EXIT-sentinel completion detection** (`delegation-harness.md:58-80`) — applies only to
  `run_in_background: true` launches. Append `; echo "EXIT=$?" > /tmp/<phase>-out.exit`; detect
  completion via the exit-file or the harness's background-completion notification. **Never**
  poll with `until ! pgrep -f "<pattern>"` (self-matching false-exit bug) and never judge a
  run from a mid-execution jsonl snapshot (long-running models can legitimately run >5 min).
- **(e) Timeout budget table** (`delegation-harness.md:83-98`) — this is the sanctioned-pairs
  source `scaffold_lint.py`'s `budget-agreement` check parses (§2 above). Current sanctioned
  `(grace, budget)` pairs:

  | Phase | Call | flags | Budget(s) | Grace |
  |---|---|---|---|---|
  | apply | apply-executor | `-k 30 600` | 600 | 30s |
  | archive | archive-executor | `-k 30 600` | 600 | 30s |
  | verify | fix-executor | `-k 30 600` | 600 | 30s |
  | verify | verifier (pro) | `-k 15 780` | 780 | 15s |
  | verify | verifier (flash) | `-k 15 780` | 780 | 15s |
  | propose | reviewer | `-k 15 780` | 780 | 15s |
  | explore | direction gate (pro) | `-k 15 780` | 780 | 15s |
  | SMALL | premise reviewer (flash) | `-k 15 780` | 780 | 15s |

  **A new correctness-audit wave using a novel `(grace, budget)` pair will fail
  `budget-agreement` lint** unless that pair is added as a new row to this table AND the skill
  cites the row. The two existing distinct pairs are `-k 30 600` (600s budget, used for
  executor-class multi-step work) and `-k 15 780` (780s budget, used for single-pass
  review/verification work) — a correctness-audit wave doing read-only LLM review across a
  codebase is structurally closer to the `-k 15 780` review-pass class; reusing that exact pair
  avoids a table edit. If waves genuinely need a different budget (e.g. longer for large-repo
  sweeps), a new row must be added and justified.
- **Carve-out** (`delegation-harness.md:102-107`): an **in-process** self-review pass (Task-tool
  spawn, not `opencode run`) is exempt from (a) and (c) — no separate process, no TTY-stdin. If
  correctness-audit's waves are implemented as in-process subagent Task calls rather than
  `opencode run` delegation, this exemption applies and the harness's hardening rules do not.

---

## 5. Output-location contract: where FINDINGS should live

**No `FINDINGS*` file currently exists anywhere in this repo** (`find . -iname "FINDINGS*"`
returns nothing) — the outstanding/knowledge_lint machinery for findings is fully built and
tested but has zero live instances yet in this scaffold. A new correctness-audit skill would be
the **first real producer** of files matching this pattern here.

**Exact glob/pattern the `outstanding` fact and `knowledge_lint`'s untriaged-age check use**
(both consume the same shared module, `scripts/outstanding.py`):
- Default findings glob: `DEFAULT_FINDINGS_GLOBS = ["knowledge/research/**/FINDINGS*.md"]`
  (`scripts/outstanding.py:29`), overridable per-repo via `checks.toml`'s
  `[facts.outstanding].findings_globs` (`scripts/outstanding.py:47-48`). This repo has **no**
  `checks.toml` at all (`checks.toml` does not exist at repo root — confirmed by direct read
  attempt), so the default glob is what's live.
- Default finding-ID pattern: `DEFAULT_FINDING_ID_PATTERN = r"\b[A-Z]{2,}(?:-[A-Z0-9]+)?-\d+\b"`
  (`scripts/outstanding.py:32`) — i.e. two-or-more uppercase letters, optional
  `-<TOKEN>` segment, trailing `-<digits>`. Examples that match: `CA-3`, `CA-W1-12`, `OW-5`.
  Overridable via `[facts.outstanding].finding_id_pattern`.

**Consequence for the correctness-audit skill's output layout:** if its FINDINGS files are
written under `knowledge/research/**/FINDINGS*.md` and finding IDs inside them match the
default pattern (e.g. `CA-1`, `CA-2` for "correctness-audit"), they are picked up
**automatically** by:
1. `scripts/outstanding.py`'s `extract_untriaged()` (`scripts/outstanding.py:409-472`) — feeds
   both `output/facts/outstanding.json` and `.md` (via `facts.py --check outstanding` /
   `outstanding-work-review` skill).
2. `scripts/knowledge_lint.py`'s Check 9, `_check_untriaged_age`
   (`scripts/knowledge_lint.py:894-924`) — flags any untriaged finding older than
   `[knowledge_lint].untriaged_max_age_days` (default **14 days**,
   `scripts/knowledge_lint.py:341`) as a `untriaged-finding-stale` finding, causing
   `knowledge_lint.py` to exit 1. This is a CI-visible drift signal, not just an
   informational note — it fires automatically once the finding crosses 14 days without being
   referenced under `knowledge/questions/`.

**Untriaged bucket logic exactly:** a finding is "untriaged" iff its extracted ID appears in a
matched FINDINGS file but does **not** appear anywhere under `knowledge/questions/` — scanned
across both `knowledge/questions/INDEX.md` and every `knowledge/questions/*.md` per-item file
(`scripts/outstanding.py:449-472`, mirrored in the capability spec
`openspec/specs/outstanding-work-view/spec.md:56-70`). "Triaging" a finding means writing a
reference to its exact ID string somewhere under `knowledge/questions/` (INDEX or per-item
file) — the match is a simple pattern search, not a structured cross-reference field, so the ID
string alone appearing in prose is sufficient to move it out of the untriaged bucket.

**Where FINDINGS should NOT live, per the taxonomy:** `knowledge/README.md:16-17` splits
`knowledge/reference/` (durable facts, on-demand) from `knowardge/research/` (hard-won
synthesized investigation, indexed via `knowledge/research/INDEX.md`). The FINDINGS-glob
default explicitly targets `knowledge/research/**/`, not `knowledge/reference/` or
`output/`. Writing FINDINGS under `output/checks/<date>/` (the disposable per-audit artifact
home used by `run-audit`'s cycle, `run-audit/SKILL.md:52`) would make them invisible to both
`outstanding.py` and the untriaged-age check, since `output/` is untracked/ephemeral by
convention and not in the default glob — confirmed separately by `knowledge_lint.py`'s own
broken-citation check treating `output/` as ephemeral and skipping existence checks under it
(`scripts/knowledge_lint.py:441-444`).

**Research-dir naming convention within `knowledge/research/`** (from
`knowledge/research/INDEX.md` and the directory listing): mix of flat dated files
(`<slug>-YYYY-MM-DD.md`, e.g. `consolidation-plan-2026-06-16.md`) and dated multi-file
directories (`<slug>-YYYY-MM[-DD]/`, e.g. `research-industry-standards-2026-06/`,
`scaffold-gap-analysis-2026-07/`). Every entry is indexed with a one-line registry entry in
`knowledge/research/INDEX.md` (`- **YYYY-MM-DD** · <slug> · <one-line description> →
<path>`). **If correctness-audit's FINDINGS files should be discoverable via this index too**
(separately from the `outstanding` fact's glob-based discovery), a dated directory like
`knowledge/research/correctness-audit-<date>/FINDINGS.md` following this exact convention,
with a matching `INDEX.md` line, is the closest fit — and it also satisfies the default
`knowledge/research/**/FINDINGS*.md` glob without any `checks.toml` changes.

**Contrast: within an active `openspec/changes/<name>/` dir**, the convention is different —
`research/<topic-slug>.md` flat files, no dates (see
`openspec/changes/lesson-check-ratchet/research/{prior-art-digest,tooling-research}.md` and
`openspec/changes/verify-stack-redirect/research/{touch-surface,pass-yield-evidence}.md`). This
report itself (`openspec/changes/correctness-audit-skill/research/scaffold-conventions.md`)
follows that in-change convention — it is change-scoped research, not the audit tool's runtime
FINDINGS output, and should NOT be confused with the `knowledge/research/**/FINDINGS*.md` glob
target the shipped skill will write into.

---

## 6. `checks.py` surface (check/fact registry)

`python3 scripts/checks.py --list` output (`scripts/checks.py`'s `_CHECKS` registry table,
lines 180-231):

| name | tier | kind | family | enabled (this repo) | available |
|---|---|---|---|---|---|
| ruff | floor | check | disabled | available |
| gitleaks | floor | check | enabled | **unavailable** |
| osv-scanner | floor | check | disabled | unavailable |
| deptry | floor | check | disabled | unavailable |
| data-lint | floor | check | disabled | available |
| radon | heavy | fact | disabled | unavailable |
| jscpd | heavy | check | disabled | unavailable |
| vulture | heavy | check | disabled | available |
| index-coverage | heavy | fact | disabled | available |
| outstanding | snapshot | fact | enabled | available |
| inventory | snapshot | fact | enabled | available |

(Current run reports: "1 enabled check(s) unavailable — `--floor`/`--report` will fail preflight
until installed or disabled" — `gitleaks` is enabled but not installed in this environment; not
directly relevant to correctness-audit but explains the exit-3 preflight semantics documented in
`run-audit/SKILL.md:73-79`.)

**The checks/facts/audit trichotomy** (`scripts/checks.py:1-13`): **checks** = findings-capable
detectors with gate/record semantics and dated output (ruff, gitleaks, osv-scanner, deptry,
data-lint, jscpd, vulture); **facts** = can't-fail repo snapshots, undated, regenerate-on-use
(scope, radon, index-coverage, inventory, outstanding); **audit** = the operator ceremony
(`audit_scope.py` tag/log + `run-audit` skill + `knowledge/audit-log.md`). `outstanding` is
registered `kind: delegate` (`scripts/checks.py:230`), meaning it's a thin dispatch to
`outstanding.py`'s `run()` function (`scripts/checks.py:990-993`) rather than a builtin
inline implementation — the same `kind: delegate` pattern used by `data-lint` and
`index-coverage`. **This is the exact integration pattern a correctness-audit check/fact would
follow if it registers into `checks.py` itself** rather than staying purely a skill-driven
process: add a `{"name": "correctness-audit", "tier": ..., "kind": "delegate", "family": ...}`
entry and a dispatch branch mirroring `scripts/checks.py:990-993` (`if name == "outstanding":
... outstanding.run(root, config, out_path)`). Whether that registration is actually needed
depends on the design (the existing `run-audit`/`knowledge-drift-review` skills do NOT register
themselves into `checks.py` — they compose `checks.py`'s output, they aren't check-registry
entries themselves; a correctness-audit skill fanning out LLM waves is more likely to follow
that same non-registered, composing pattern than to become a new registry row).

`knowledge_lint.py` has no CLI flag for FINDINGS files specifically — it exposes untriaged-age
via `_check_untriaged_age` (Check 9, `scripts/knowledge_lint.py:894-924`), which is fully
covered in §5 above (default threshold 14 days, per-repo override via
`[knowledge_lint].untriaged_max_age_days`).

---

## 7. Anything else a new scaffold skill author would trip over

- **No `checks.toml` exists in this repo.** All `[facts.outstanding]` and `[knowledge_lint]`
  config is running on hardcoded defaults (`DEFAULT_FINDINGS_GLOBS`,
  `DEFAULT_FINDING_ID_PATTERN`, `untriaged_max_age_days = 14`). If correctness-audit's finding
  ID scheme doesn't naturally match `\b[A-Z]{2,}(?:-[A-Z0-9]+)?-\d+\b` (e.g. it wants lowercase
  or a different delimiter), a `checks.toml` needs to be created — and note `checks.toml` is
  explicitly **per-repo config, never scaffold-managed**
  (`scripts/knowledge_lint.py:61-65`), so it would NOT propagate via `sync_scaffold.py` to
  downstream repos; each repo adopting the correctness-audit skill would need its own
  `checks.toml` if it wants a non-default pattern/glob/threshold.
- **`scaffold_lint.py` is itself never synced downstream** — it's authoring-side tooling for
  *this* repo only (`scripts/scaffold_lint.py:2-8`, exclusion list at
  `scripts/scaffold_lint.py:145-155`). Its checks only protect the scaffold repo's own
  instruction-file hygiene; they do not run in a downstream repo that receives the synced
  skill. Downstream repos rely on `sync_scaffold.py --check` (a different tool) to detect drift
  from the scaffold's manifest.
- **`_NON_OPENSPEC_SKILL_TOKENS` is a manually maintained set** (`scripts/scaffold_lint.py:168`)
  that currently only lists `knowledge-drift-review` and `run-audit`. It exists so
  `budget-agreement`/`dangling-skill-refs` explicitly recognize non-`openspec-`-prefixed skill
  names when they appear as bare tokens outside a resolvable context; per §2's analysis this is
  belt-and-suspenders on top of the dir-name fallback, but the comment
  (`scripts/scaffold_lint.py:167`, "Keep in step with actual .claude/skills/ non-openspec
  dirs") signals the maintainers' intent to keep it current — adding `correctness-audit` to it
  is the conservative, convention-following move even if not strictly lint-required today.
- **Every audit-family skill is pull-only / operator-gated — none are wired into
  `AGENTS.md` boot reads or `openspec-archive-change`.** `knowledge-drift-review/SKILL.md:18-20`
  explicitly says it is deliberately NOT run on every archive to avoid burning LLM tokens
  re-litigating unrelated drift; archive instead runs only the cheap deterministic
  `knowledge_lint.py` plus a narrow just-shipped-change re-check. A wave-fanning
  correctness-audit skill fits the same mold: expect it to be periodic/on-demand, not
  auto-triggered, and to say so explicitly in its own frontmatter `description` and body,
  matching the "Operator-invoked" / "Pull-only" phrasing precedent (§1).
- **Guardrail-list convention**: every skill's closing Guardrails section explicitly lists
  files it must NOT edit (e.g. outstanding-work-review names `scripts/outstanding.py`,
  `scripts/checks.py`, `facts.py`, and the `knowledge_lint` drift checks as off-limits,
  `outstanding-work-review/SKILL.md:83-84`). A correctness-audit skill should do the same for
  whatever scripts it depends on/wraps, and should state plainly whether it is allowed to write
  tracked files at all (run-audit's answer: only `knowledge/audit-log.md`, and only on explicit
  operator tag request) or is fully read-only (knowledge-drift-review's answer: never).
- **The `run-audit` skill already has a "wiring-detection branch"**
  (`run-audit/SKILL.md:101-108`) that checks whether `checks.toml`/`checks/`/an `audit-*`
  task-runner target exist before running, and gives inline guidance rather than
  auto-provisioning them. If correctness-audit needs its own per-repo wiring (e.g. a config
  block, a prompt template dir), the same detect-and-explain-don't-auto-create pattern should
  be followed rather than silently scaffolding files into a downstream repo from inside a
  skill invocation.
