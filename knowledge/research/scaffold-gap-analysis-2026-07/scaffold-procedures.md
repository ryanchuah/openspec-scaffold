# Scaffold procedures — gate ledger + existing deterministic checks

Scope note: `checks.toml` **does not exist** in this repo (`find` confirms no file at repo
root). `scripts/checks.py --list` confirms the fallback: `_load_config` returns
`({}, "defaults")` and `_autodetect_defaults` derives the registry from file-presence
triggers (`pyproject.toml` → ruff/deptry, `.git/` → gitleaks/scope, lockfile → osv-scanner,
`checks/*.sql` → data-lint). Live `--list` output in this repo:

```
scope        floor    fact   enabled   available
ruff         floor    check  disabled  available
gitleaks     floor    check  enabled   unavailable
osv-scanner  floor    check  disabled  unavailable
deptry       floor    check  disabled  unavailable
data-lint    floor    check  disabled  available
radon        heavy    fact   disabled  unavailable
jscpd        heavy    check  disabled  unavailable
vulture      heavy    check  disabled  available
index-coverage heavy  fact   disabled  available
outstanding  snapshot fact   enabled   available
inventory    snapshot fact   enabled   available
```
No `pyproject.toml` exists here, so `ruff`/`deptry` show `disabled` despite being "parsed"
checks — the registry is real, but most of it is switched off in this repo's own tree.

## Per-tier gate ledger

Legend for **invoker**: *orchestrator-self* = in-context, same conversation, no separate
process; *deepseek-pro* / *deepseek-flash* = `opencode run` subprocess; *sonnet-fallback* =
`Agent` tool subagent, only on deepseek operational/quality failure; *skill-subagent* =
Claude Code skill invocation (`/code-review`, `security-review`), model unspecified by the
SKILL text (assume Sonnet-class).

### SMALL (skips full OpenSpec lifecycle)

| # | Gate | Invoker | Reads | Guards against | Cost | Overlap |
|---|------|---------|-------|-----------------|------|---------|
| 0 | Direction gate (explore) — **conditional**, only if the change originated via explore mode | deepseek-pro | `explore-brief.md` | bad problem framing before any artifact exists | 1 pro pass, diff-free (reviews prose only) | none at SMALL; is the pre-artifact counterpart of gate 1 |
| 1 | SMALL premise pass | deepseek-flash | the SMALL plan (+ explore-brief if any, for D10 drift) | ungated small change proceeding on a bad premise | 1 flash pass, text-only (no test rerun — plan isn't code yet) | conceptually mirrors propose's premise verdict, but SMALL never gets a pro pass |
| 2 | Apply-executor execution | deepseek-flash (sonnet-fallback on crash/give-up) | the plan | orchestrator writing implementation code itself | 1 full execution pass, cost scales with change size; **not** a review, it's the work | n/a (this is the work being reviewed by 3 and 4) |
| 3 | Orchestrator's own verification | orchestrator-self | diff + rerun tests (implied, not spelled out in AGENTS.md beyond "do your own verification") | executor-introduced defects | in-context, folds into existing session — cheapest of the review-type gates | same method as gate 4, just cheaper venue |
| 4 | SMALL flash verifier pass | deepseek-flash | diff, full suite, real output, live smoke if external API ("same invocation shape as in the verify skill's flash pass") | same defects gate 3 targets, from an independent model | 1 flash pass + **full suite rerun** | **direct overlap with gate 3** — identical procedure, different model only |

SMALL total: gates 1+2+4 = **3 opencode passes** + gate 3's **1 self-review**; no pro-tier
pass anywhere in the tier. Gate 0 adds +1 pro pass only if explore was used.

### MEDIUM (propose emits `tasks.md` only — AGENTS.md override of the propose skill's default 3-artifact sequence)

| # | Gate | Invoker | Reads | Guards against | Cost | Overlap |
|---|------|---------|-------|-----------------|------|---------|
| 0 | Direction gate (explore) — conditional | deepseek-pro | `explore-brief.md` | same as SMALL gate 0 | 1 pro pass, prose-only | pre-artifact counterpart of gate 2 |
| 1 | Propose self-review (tasks.md) | orchestrator-self | tasks.md against template/dependencies | obvious authoring errors before spending a reviewer pass | in-context | none — deliberately the "free" first pass before gate 2 |
| 2 | Propose reviewer pass (tasks.md) | deepseek-pro | tasks.md, explore-brief (D10 drift), specs | bad/incomplete task breakdown; per AGENTS.md this is "**one** deepseek-v4-pro review" for MEDIUM, not the 3-artifact loop COMPLEX gets | 1 pro pass minimum, up to 3 if 🔴 found (mandatory re-review each time) | none within propose (only 1 artifact exists) |
| 3 | Apply-executor execution | deepseek-flash (sonnet-fallback) | tasks.md, design context | orchestrator implementing directly | 1+ execution passes (may be split across task ranges for large changes) | n/a |
| 4 | Verify self-review (steps 4–8) | orchestrator-self | diff, **re-run FULL suite**, real output sample, live smoke if external API | mock-encoded-idealized-API failure mode; "Bugs that logic-reading misses are often visible the instant you render real output" | in-context, but re-runs whole suite | identical method to gates 5–6, cheapest venue |
| 5 | Verify pro pass | deepseek-pro | same as gate 4 — SKILL text: *"It runs the same behavioral review you performed in the self-review (read diffs, re-run the full suite, eyeball real output, run live smoke)"* | defects gate 4 missed | 1 pro pass + **full suite rerun** | **overlaps gate 4 exactly** — see redundancy section |
| 6 | Verify flash pass | deepseek-flash | same as gate 4/5 | defects gates 4–5 missed | 1 flash pass + **full suite rerun** | **overlaps gates 4 and 5** — third identical pass |
| 7 | Simplicity/quality gate | skill-subagent (`/code-review` or `simplify`) | `git diff` only | duplication, single-use abstractions, dead code, over-parameterization — explicitly "does **not** block on pure style nits" | 1 pass, diff-only, **no test rerun** | deliberately differentiated lens from 4–6 (quality, not correctness) |
| 8 | Security gate — **recommended, not hard**, for MEDIUM on sensitive surfaces | skill-subagent (`security-review`) or orchestrator-self checklist | `git diff` only | authn/authz bypass, secret leakage, injection, unsafe deserialization, missing destructive-op guard | 1 pass, diff-only | deliberately differentiated lens; conditional, so often $0 |
| 9 | Archive-executor execution | deepseek-pro (sonnet-fallback) | change dir, notes.md, project docs; also runs `knowledge_lint.py` and re-checks `knowledge/reference/`, `knowledge/roadmap.md`, parked questions (flag-only) | directory move + doc reconciliation not happening, or happening inline in a bloated context | 1 execution pass | n/a |
| 10 | Archive primary review | orchestrator-self | diffs of the 3 reconciled docs; runs `status_lint.py` | fabricated/low-quality reconciliation content landing uncommitted | in-context | none |

MEDIUM baseline (excluding conditional gates 0/8): delegated 2,3,5,6,7,9 = **6**; self-reviews
1,4,10 = **3** → **≈9 total model passes**, more if gate 2's re-review loop (up to 3×) or the
security gate fires.

### COMPLEX / UNCERTAIN (full proposal + design + tasks)

Same skeleton as MEDIUM, with two structural multipliers:

- **Propose runs 3 artifacts, not 1.** Each of `proposal.md`, `design.md`, `tasks.md` gets
  its own self-review (gate 1-equivalent) + its own deepseek-pro reviewer pass (gate
  2-equivalent), each independently re-reviewable up to 3× on a 🔴. `proposal.md`'s pass also
  carries the **premise verdict** (`PREMISE: AGREE|DISSENT`) — this is the "change-itself"
  altitude AGENTS.md distinguishes from explore's "direction" altitude, but both are run by
  the identical agent (`openspec-reviewer`, pro tier) asking a structurally similar question
  ("is this the right thing to build") — see redundancy section.
- **Security gate is a hard gate, not recommended,** when the change touches auth,
  credentials, persisted data, or external API/network surfaces (verify SKILL text: *"This is
  a hard gate for COMPLEX changes on those surfaces and a recommended pass for MEDIUM
  changes"*).

COMPLEX baseline (minimum, security gate firing): delegated = 3 (propose-pro ×3 artifacts) + 1
(apply) + 2 (verify pro+flash) + 1 (simplicity) + 1 (security) + 1 (archive) = **9**;
self-reviews = 3 (propose) + 1 (verify) + 1 (archive) = **5** → **≈14 total model passes
minimum**; worst case (every propose artifact needs its full 3-round re-review loop) pushes
propose alone from 3 to 9 pro passes → **≈20 total model passes**.

## Redundancy / overlap analysis

**The verify stack (self → pro → flash) is the clearest, most load-bearing redundancy in the
whole ledger.** Direct quote from `openspec-verify-change/SKILL.md`:

> "It runs the same behavioral review you performed in the self-review (read diffs, re-run
> the full suite, eyeball real output, run live smoke for external-API changes), but it
> **never modifies files**"

All three passes (self, pro, flash) execute the **identical procedure** — same diff, same
full test suite re-run, same "eyeball real output" step, same live-smoke requirement — three
times over. The SKILL text is explicit that this is by design and states the differentiation
is model diversity, nothing else:

> "Three independent views — a Claude (Anthropic) model gains maximum diversity from both
> deepseek tiers."

and for OpenCode orchestrators, the SKILL text itself concedes the second pro pass is
low-value:

> "An OpenCode orchestrator already runs on deepseek-v4-pro, so a second pro pass adds little
> model diversity; the cheaper flash tier provides the independent second pair of eyes."

**Verdict on real vs. cosmetic differentiation:** the differentiation is **real but narrow** —
different model weights forming an independent opinion — and **not** differentiation of
input, lens, or scope. Nothing in the SKILL text asks flash to look at anything pro didn't
already look at (no "flash checks X that pro doesn't check"); it is the same checklist run
three times, justified purely on "another model might catch what this one missed." This is
the single most expensive redundancy in the ledger because **each** of the 3 passes
independently re-runs the full test suite (see Cost summary below) — for MEDIUM/COMPLEX
that's 3× full-suite execution cost per verify cycle, before counting re-review loops.

**Second-order overlap — two "premise" reviews by the same agent.** AGENTS.md frames this as
deliberate ("two altitudes"): explore's direction gate ("is the problem/direction sound before
any artifact exists") vs. the proposal.md premise verdict ("does the change's own premise
hold," folded into the pro `proposal.md` review for MEDIUM/COMPLEX). Both run the identical
`openspec-reviewer` agent at the identical pro tier, and propose's D10 instruction has the
reviewer re-read the frozen explore-brief and check the new proposal for **drift** against
it — i.e. the mechanism itself narrows the second pass's added value to drift-detection rather
than a fresh premise judgment, because it knows the ground is largely re-litigated. Legitimate,
but thinner than "two independent premise reviews": skip explore and it collapses to one pass;
use explore and the propose pass mostly reconfirms explore's verdict.

**Deliberately differentiated, NOT overlapping:** simplicity/quality gate ("does **not** block
on pure style nits — it targets over-engineering, duplication, and dead code" — a quality lens
the verifier passes don't apply) and the security gate (a fixed 5-item authn/secrets/
injection/deserialization/destructive-op checklist nothing else in the stack asks).

**Which gates re-run the full suite (expensive) vs. read-only:**

| Gate | Re-runs full suite? |
|---|---|
| Verify self-review (step 5) | **Yes** — "Re-run the FULL test suite yourself... A green exit is necessary but not sufficient." |
| Verify pro pass | **Yes** — same behavioral review as self |
| Verify flash pass | **Yes** — same behavioral review as self/pro |
| SMALL flash verifier pass | **Yes** — "same invocation shape as in the verify skill's flash pass" |
| Simplicity/quality gate | No — `git diff` only |
| Security gate | No — `git diff` only |
| Propose/explore/SMALL premise reviewer passes | No — reviews prose artifacts, not code |
| Apply-executor | Runs tests iteratively as part of implementing, not as a discrete "gate" rerun |
| Archive-executor | Runs `knowledge_lint.py` (cheap, deterministic) — not the pytest suite |
| Archive primary review | Runs `status_lint.py` (cheap, deterministic) — not the pytest suite |

## Existing deterministic checks (checks.py / knowledge_lint / other)

From `scripts/checks.py`'s own docstring (self-documenting by design — "this docstring +
`--help` are the ONLY documentation... no standing doc file for a code-derivable schema") and
the module docstrings of each script (first-paragraph read only, per instructions):

**`checks.py` registry (12 entries; `enabled`/`available` per the live `--list` above):**
`scope` (→`audit_scope.py scan`, churn×complexity hotspot ranking since last `audit/<date>`
tag, never gates) · `ruff` (lint, disabled — no `pyproject.toml`) · `gitleaks` (secret
scanning, **enabled but unavailable** — the one preflight failure blocking `--floor`/`--report`
right now) · `osv-scanner` (known-vuln scan vs. lockfiles, disabled) · `deptry`
(dependency-hygiene, disabled) · `data-lint` (→`data_lint.py`: each `checks/*.sql` file is one
`SELECT` returning violating rows, zero=pass; Postgres via read-only `psql`/`PGOPTIONS` or
SQLite via `file:...?mode=ro`, both engine-enforced read-only with a timeout; disabled here) ·
`radon` (complexity fact, disabled/unavailable) · `jscpd` (copy-paste detector, disabled —
**the one built-in mechanism that scans whole-repo accreted duplication, not a single diff**,
but off) · `vulture` (dead-code detector, disabled) · `index-coverage` (→`index_coverage.py`:
regex-based unindexed-column leads, "NEVER gates... for LLM triage only," disabled) ·
`outstanding` (→`outstanding.py`, gathers untriaged findings, always exit 0) · `inventory`
(tracked file tree, entrypoints, env-var names; zero-findings, always "ok").

**Other scripts invoked directly by skills, not in the `checks.py` registry:**
`knowledge_lint.py` — detect-only linter over `knowledge/`: orphan/duplicate canonical files,
retired-path tokens, broken prose path citations, dangling archive pointers, malformed
audit-log lines; zero filesystem writes. `scaffold_lint.py` — 6 checks on this repo's own
mechanized invariants, including **`budget-agreement`**, which cross-checks every embedded
`timeout -k <G> <B>` pair in skill/agent files against the sanctioned table in
`delegation-harness.md` §e (drift between documented and actually-embedded timeout budgets).
`status_lint.py` — `knowledge/STATUS.md` (≤3 sections, ≤150 words each) and
`knowledge/decisions/INDEX.md` (registry-line format) invariants. `outstanding.py` — shared
gather module feeding both `checks.py`'s `outstanding` entry and `knowledge_lint.py`'s
untriaged-age check. `audit_scope.py` — `scan` (hotspot ranking), `tag` (the **sole mutating
operation** in the audit tooling — creates an `audit/<date>` git tag), `log-line` (prints,
never writes). `scaffold_check.py` — pre-commit `PreToolUse` guard blocking staged edits to
scaffold-managed files (Claude-Code-only coverage). `sync_scaffold.py` — scaffold→downstream
sync/check tool (byte-convergence + `--check-refs`). `_convergence.py` — deterministic
CONTINUE/STOP verdict from test output, stopping the apply-executor's fix-loop from spinning
forever on the same failure.

**Explicit answer to the two systemic-failure questions:**

**(a) Does any mechanism convert a discovered bug/lesson into an enforced check on future
diffs? NO.** `knowledge/lessons.md` is a prose file ("Read this file when you are about to
delegate, review, run research, or apply changes") — nothing parses it into a `checks.toml`
entry, a `scaffold_lint.py` check, or any other runnable gate. The "mock-encoded-idealized-API"
failure mode (lessons.md + `apply-executor.md`'s canonical war-story) is handled entirely by a
**prose instruction** to remember to run a live smoke test — no static/dynamic check would
catch a future change that forgets to. The closest thing to lesson→check conversion is
`scaffold_lint.py`'s `budget-agreement` check, but that only cross-validates one internal
artifact (embedded `timeout` values) against another (the harness doc's table) — a
structural-consistency check, not a mechanism that turns an arbitrary "we got burned by X"
lesson into an automated future gate.

**(b) Does any mechanism review the accreted composition of many past changes, rather than a
single diff? PARTIALLY, and not wired into the per-change gate.** Three candidates, none
"run automatically every change": `jscpd`/`vulture` (checks.py, whole-repo scan for
cross-change duplication/dead-code, but **disabled by default**, audit-time only);
`knowledge-drift-review` skill (explicit whole-tree sweep for stale "not yet built" claims,
intra-doc contradictions, buried gates — its own text: "**Not** wired into every
`openspec-archive-change` run... invoke it on operator request or on a recurring cadence,"
pull-only); `audit_scope.py scan` (churn+complexity hotspots since the last `audit/<date>`
tag — genuinely multi-commit, but an informational fact snapshot inside the operator-invoked
`run-audit` cycle, never a gate). The verify skill's simplicity/quality gate is explicitly
scoped OFF from this: "review of **the change's `git diff`**" — single-diff only, by its own
words. Net: the capability exists but lives entirely in the operator-pulled, off-by-default
audit layer, never the mandatory verify/archive path.

## Cost summary

| Tier | Delegated model passes (opencode/skill) | In-context self-reviews | Total (baseline) | Total (worst-case re-review loops) |
|---|---|---|---|---|
| SMALL | 3 (premise-flash, apply-exec-flash, verifier-flash) | 1 | **~4** | ~5 (if premise/verifier need a re-run) |
| MEDIUM | 6 (propose-pro, apply-exec-flash, verify-pro, verify-flash, simplicity, archive-exec-pro) | 3 (propose-self, verify-self, archive-review) | **~9** | ~12+ (propose reviewer up to 3×, + conditional security) |
| COMPLEX | 9 (propose-pro ×3 artifacts, apply-exec-flash, verify-pro, verify-flash, simplicity, security-hard, archive-exec-pro) | 5 (propose-self ×3, verify-self, archive-review) | **~14** | ~20+ (each propose artifact up to 3× re-review) |

This is the token-waste denominator: **3× of every MEDIUM/COMPLEX verify cycle is the
identical full-suite-rerun behavioral review**, repeated for model diversity alone (self →
pro → flash), which is the single largest lever if the reader is looking for where to cut.
