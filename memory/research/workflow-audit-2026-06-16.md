# Principal Engineer Audit — agent workflow, rules & OpenSpec surface (2026-06-16)

Reviewer hat: Principal SWE. Brutally honest, simplicity/maintainability-biased, allergic to
over-engineering. Assumed everything was written by untrustworthy juniors; verified falsifiable claims
against the files. Scope: `AGENTS.md`, `openspec/config.yaml`, `ai-docs/*`, all 7 `.claude/skills/openspec-*`,
all 6 agents (`.claude/agents`, `.opencode/agents`), all 6 promoted specs, `scripts/_convergence.py`,
`scripts/test-gate.sh`, `.claude/settings.json`. Companion doc: `openspec/changes/scaffold-sync/principal-review.md`
(reviews the in-flight change).

**Overall:** a genuinely strong, unusually coherent workflow — the separate-model review discipline,
the archive checkpoint/recovery, and the phase gates are well above average. But it has four
co-equal classes of problem, none subordinate to the others:

1. **Correctness** — the deterministic convergence helper is weaker than its decision text claims, and the
   commit gate has a silent-disable path. (§A)
2. **Over-engineering** — the two hottest skills bury the happy path under exception walls, and the
   multi-model verify gate isn't tier-scaled. (§B)
3. **Duplication** — the entire `opencode run` delegation harness is copy-pasted across four skills and
   is already drifting; this is the largest maintainability liability and is mostly *not* addressed by
   the planned "change 2". (§C)
4. **What's missing** — there is no simplicity/quality gate at all, and the live hook-wiring is still
   unverified. (§E)

Plus a handful of concrete coherency drifts (§D). Nothing here is architectural rework — these are
sharpening cuts. Severity: 🔴 blocker · 🟠 major · 🟡 should-fix · 💡 nit.

---

## A. Correctness / will-bite (real code)

### 🟡 A1 — `_convergence.py` has no absolute attempt ceiling; oscillating failures escape the "declared stop" guarantee
Rule (a) fires only on a **consecutive** signature match: `if last_sig is not None and last_sig == signature and attempts >= 2` (`_convergence.py:197`). `attempts` increments every call (`:192`) but is never an independent cap. A failure whose signature oscillates (S1→S2→S1…) never trips (a); if `--editing` rotates files or is omitted, (b) (`:209`) never trips either. The only backstop is the outer `timeout -k 30 600` → exit 124 → "operational crash" → retry/Sonnet. So the oscillating case yields a **10-minute wall-clock timeout, not a `### NON-CONVERGENCE BLOCKER`** — against the stated intent ("a declared stop, not a wall-clock timeout", `apply-convergence-guard` spec `:110`; `decisions.md:122`). Fix: add an absolute attempts ceiling per test id, independent of signature churn.

### 🟡 A2 — rule (a)'s signature is computed over the WHOLE test output, so unrelated churn defeats it
`signature = _normalize_signature(raw_output)` normalizes the **entire** stdin (`:271`), not the failing test's traceback. As the executor edits code, unrelated lines shift — pass/fail summary counts, reordered other failures, warnings — changing the signature even when the targeted test fails identically, so (a) silently won't match across iterations on any non-trivial suite. (Also: `test_id` is used raw as the state key, `:185`/`:264`, with no normalization — a node-id format change between runs splits the key and resets accumulation.) Fix: scope the signature (and key) to the failing test's section.

### 🟡 A3 — rule (b) still depends on the unreliable executor to self-report `--editing` every iteration
The helper exists because "flash is unreliable … at carrying exact state across many tool calls" (`decisions.md:62-64`). But (b)'s file-touch count is only as good as the `--editing <file>` the executor passes — shown as **optional** (`[--editing …]`, `apply-executor.md:47`). A flash executor that omits it defeats (b). The *counting* is deterministic; the *input* is still flash's self-report, so the determinism is half-delivered. Fix: derive edited files from `git diff --name-only` inside the helper (fully deterministic), or make `--editing` mandatory and assert it.

### 🟡 A4 — `_normalize_signature` strips paths so aggressively it can collapse distinct failures → false STOP:a (premature stop)
`text = re.sub(r'/\S+', ' <PATH> ', text)` runs first and replaces *any* `/`-led non-whitespace run (`:101`). Two genuinely different errors that differ only in path-ish content collapse to the same signature → rule (a) trips early and declares non-convergence on a failure that was actually progressing. A2 makes (a) too *lax*; A4 makes it too *eager* — both stem from signature quality. Worth a couple of unit tests pinning "distinct errors stay distinct" and "cosmetic-only diffs collapse" (the spec already asserts both, `apply-convergence-guard` `:47-53`, but there is no test).

### 🟡 A5 — the commit gate silently no-ops if the hook's cwd isn't the repo root
`test-gate.sh` resolves `CMD_FILE` from `SCRIPT_DIR` (absolute, good — `:21-22`) but then runs the command **relative to the current directory**: `command -v "$EXECUTABLE"` (`:41`) and `if $CMD` (`:49`) with `EXECUTABLE`/`CMD` = `.venv/bin/pytest`. If the `PreToolUse` hook fires with cwd ≠ repo root, `command -v .venv/bin/pytest` fails → the script treats it as a config error and **exits 0 (gate disabled), not 2** (`:41-45`). So the gate's enforcement quietly depends on an unstated cwd invariant. Either resolve the test command against the repo root explicitly, or assert cwd. (This compounds D2 — the wiring was never live-smoked, so this would not have surfaced.)

---

## B. Over-engineering / convolution

### 🟡 B1 — apply & verify bury the happy path under stacked exceptions ("M7", self-logged, deferred)
apply Step 6.1 is ~30 lines dominated by completion-detection *don'ts* (`openspec-apply-change/SKILL.md:120-148`); verify's MANDATORY blockquote is ~20 dense lines (`openspec-verify-change/SKILL.md:14-34`). These are the two most-executed skills, and a resuming/low-context executor must wade through "NEVER poll with pgrep… never judge from a mid-run snapshot…" to find the one-line happy path — convolution that itself raises the odds of the mis-detection the caveats guard against. Flagged as "M7" (`open-questions.md:28`) and deferred; I'd raise it over the cosmetic dedup. Fix: lead each with a 3-line happy path, then a separated "Failure modes" subsection.

### 🟡 B2 — the multi-model verify gate is not tier-scaled; a one-line SMALL change pays the full 3-pass cost
The verify passes branch **only on platform**, never on change tier (`openspec-verify-change/SKILL.md:42-43` — no SMALL/MEDIUM/COMPLEX anywhere in the skill). So under Claude every change that reaches verify gets self-review + a pro verifier pass + a flash verifier pass — three independent behavioral reviews, two of them 780s `opencode run` invocations — even a trivial SMALL change. Meanwhile AGENTS.md's SMALL tier says merely "do your own verification" (`:138-140`), which reads far lighter. Either the gate is disproportionate for SMALL, or SMALL silently skips it — and which one is true is undefined (see D-coherency below). Decide and tier-scale it: SMALL → self-review (+ maybe one flash pass); reserve the full chain for MEDIUM/COMPLEX.

### 💡 B3 — timeout budgets are magic numbers scattered across 4 files
apply 600s (`apply:97`), fix-executor 300s (`verify:27`), verifier 780s (`verify:60,67`), reviewer 780s (`propose:113`), archive 600s (`archive:137`). Only the reviewer's 780s is canonicalized (in a spec). Tuning any other means hunting across files, and the `.claude`/`.opencode` copies can drift unguarded. (This is also a duplication symptom — see §C.)

---

## C. Duplication (largest maintainability liability)

### 🟠 C1 — the entire `opencode run` delegation harness is copy-pasted across all four delegating skills, and is already drifting
Every delegating skill (propose, apply, verify, archive) carries its own inline copy of the same delegation boilerplate:
- the **hardened invocation** (`< /dev/null` + `--dir <repoRoot>` + "see `noninteractive-delegation-safety`") — present in all 4 skills (`apply:92`, `verify:27`, `propose:110`, `archive:132`);
- the **"assert the real agent ran"** block (grep `Falling back to default agent`, extract `part.text`, confirm format) — all 4 skills (`apply:150`, `propose:139`, `archive:164`, `verify:84`);
- the **"Bounded wait + surgical kill / never `pkill opencode`"** paragraph — 3 skills (`apply:120`, `propose:127`, `archive:156`);
- the **EXIT-sentinel completion-detection** caveats — apply + verify (`apply:132`, `verify:28`).

This is the biggest duplicated mass in the repo, it is **safety-critical** (it's the anti-hang / anti-false-success machinery), and it is **already drifting**: the timeouts differ per copy (B3), the completion-detection caveats are spelled out in full in apply but abbreviated elsewhere, and the failure ladders diverge (apply has the convergence-blocker triage that the others only gesture at). A fix or hardening to this logic must today be made in four places, by hand, with no check they agree — the exact recipe for one copy silently lagging a security-relevant fix. Fix: extract the invocation/assert-ran/kill/sentinel contract into one referenced doc (the way `noninteractive-delegation-safety` is referenced) and have each skill cite it with only its per-phase specifics (agent name, model, budget, prompt).

### 🟡 C2 — the same *rules* are restated 3–5× across the instruction surface (partly logged)
- "tasks.md = apply-phase only": `config.yaml` rules.tasks (`:20-29`), `openspec-propose` guardrail (`:258`), verify note (`:158`), apply (implicit). ~4×.
- Model-assignment matrix ~5×: AGENTS.md Roles (`:72-101`) + Change tiers (`:138-147`) + config.yaml rules + each of apply/verify/archive restating "deepseek-flash via opencode run / Sonnet fallback" + agent frontmatter (`open-questions.md:27`).
- "Never record test/doc/row counts" ~5×: AGENTS.md (`:193-198`), config.yaml context (`:7`), verify (`:261`), archive (`:241`), archive-executor agents (`:63`/`:52`).
- War-story (mock-encoded-idealized-API) ~3–4×: apply-executor bodies (`:92`/`:81`), verify (`:24`), propose live-probe rationale (`:80-87`) (`open-questions.md:26`).
- Web-research convention 2× and **already drifted**: AGENTS.md §"Web research convention" (`:227-238`) vs `ai-docs/research-fetch-convention.md` (whole file) (`open-questions.md:24`).

### 🟡 C3 — the planned "change 2" (scaffold-sync) only deduplicates *two* of these
Per `single-source-plan` + `open-questions.md:24-27`, scaffold-sync single-sources the **war-story** and **model-matrix** and makes the web copies *agree* — it does **not** dedup the delegation harness (C1), the "tasks.md = apply-only" rule, the "no counts" rule, or the web-research convention. So the dominant duplication (C1) survives change 2. Flag explicitly whether that's acceptable or in scope.

### 🟡 C4 — executor *body* prompts are duplicated between `.claude/` and `.opencode/` with no agreement guard — a principle you already applied elsewhere
`apply-executor` and `archive-executor` each exist as two files whose **bodies** are near-identical and hand-synced. The `verify-multimodel-gate` decision explicitly rejected a second verifier file *because* of "duplicated body prompt that must be kept in sync" (`decisions.md:134`) — yet apply/archive carry exactly that. The two-file split is justified (formats/models differ, `decisions.md:48`), but nothing checks the prose halves agree. Add a check, or a shared-body include.

---

## D. Coherency drift (untrustworthy-junior hunt)

### 🟡 D-i — the archive-executor agent silently drops RENAMED spec requirements
The archive **skill** assesses "adds, modifications, removals, **or renames**" (`openspec-archive-change/SKILL.md:81`), and `openspec-sync-specs` handles RENAMED (`:74`). But the **archive-executor agent** that actually performs the delegated sync is told only to "Apply additions, modifications, and **removals**" (`.opencode/agents/archive-executor.md:48`, `.claude/agents/archive-executor.md:36` — both omit renames). A change that RENAMEs a requirement, synced via archive, can have the rename dropped. (Two divergent "sync delta specs" implementations — primary-driven in sync-specs vs delegated in archive — is itself a drift hazard; this is a concrete instance.) Fix: add RENAMED to both archive-executor bodies.

### 🟡 D-ii — it is undefined whether phase gates and the multi-model verify gate apply to SMALL changes
The skills' phase gates are unconditional "hard rules" (STOP after apply, wait for explicit "verify", etc.) and the verify skill always runs the multi-model passes (B2). But AGENTS.md's SMALL tier says "skip the full OpenSpec lifecycle … do your own verification" (`:138-140`), implying a lighter, gate-free flow. Nothing reconciles the two: does a SMALL change invoke the verify skill (and thus its phase gate + 3-pass chain) or not? Underspecified — and it determines both the safety and the cost of every small change. Resolve it explicitly in the Change-tiers section.

### 💡 D-iii — promoted spec files have inconsistent headers
`verify-multimodel-gate/spec.md:1` opens with an H1 title; the other five specs start directly at `## Purpose`. The sync-specs/archive promotion path should normalize this.

---

## E. What's missing (the gap lens)

### 🟠 E1 — there is NO simplicity/quality gate, and `simplify`/`code-review` are never invoked (grep-confirmed)
The lifecycle has excellent *correctness* gates — separate-model reviewer at propose, multi-model verifiers + behavioral self-review at verify. It has **nothing** that reviews the implementation for over-engineering, duplication, or dead code. The implementer is deepseek-**flash** (cheapest tier, most prone to verbose/over-built output), and verify's "Coherence" dimension explicitly says "don't nitpick style" (`verify:323`). So flash-written code flows apply → correctness-verify → archive with no pass asking "is this the simplest correct implementation?" The built-in `simplify` and `code-review` skills exist for exactly this and are referenced nowhere. Cheapest fix: the orchestrator runs `simplify` (or `/code-review`) on the change's diff during verify, before declaring READY. (Dogfooding note: this instruction surface is itself duplication-riddled — §C — the workflow would benefit from the gate it lacks.)

### 🟠 E2 — the commit-test-gate hook wiring is STILL unverified (self-logged BLOCKING) and is about to be compounded
`open-questions.md:13` marks the live hook-wiring smoke `[REQUIRED]` / **BLOCKING**, still pending: nobody has confirmed in a gated session that the `PreToolUse` hook fires on `git commit`, that exit 2 blocks, and that `$CLAUDE_PROJECT_DIR` expands. The companion `scaffold-sync` review found the *new* guard (`scaffold_check.py`) exits **1**, while the proven blocker convention is exit **2** (`test-gate.sh:9,55`) — so it likely won't block at all. Both rest on the same unproven wiring assumption (and A5 adds a third unverified assumption — cwd). One live gated-session smoke must cover all of it before either gate is relied on.

### 🟡 E3 — no security gate for app-code changes
extrends/psc-monitor handle real data, Postgres, external APIs, credentials. No lifecycle step considers security, and the `security-review` skill is never referenced. At minimum: a COMPLEX-tier prompt to run `security-review` when a change touches auth/data/external surfaces.

### 💡 E4 — no rollback / "shipped change was wrong" lifecycle branch
The lifecycle ends at archive. There's robust recovery for a *botched archive run* (`archive:212-227`), but nothing for "we archived and later found the change is wrong." Likely "git revert + new change," but it's an unstated branch the operator will eventually hit.

### 🟡 E5 — the dual-harness load-bearing claims are version-pinned to a one-time check, with no smoke
The architecture rests on "OpenCode ≥1.16 auto-discovers `.claude/skills`" (`decisions.md:24`) and "opencode discovers agents only from `.opencode/agents`" (`decisions.md:51`), each verified once against opencode 1.17.4 on 2026-06-14. An opencode upgrade could silently stop cross-loading skills (the whole skill layer vanishes for the OpenCode harness) with zero signal. Add a one-line smoke (does `opencode` enumerate the openspec skills?) to the wiring-smoke procedure.

---

## F. What's right (keep — don't "fix" these)

- **Archive pre-handoff checkpoint + scoped recovery** (`archive:95-119, 212-227`): `-a` not `-A`, path-scoped `git clean`, never `stash`, baseline-before-retry. Genuinely careful.
- **Separate-model review discipline** is consistent end to end: reviewer at propose, verifier at verify, "reviewer/verifier can be wrong → judge from disk → record overrule rationale." Read-only permission boundaries match the specs.
- **Deterministic convergence helper** is the right instinct (offload normalization/state from flash) even with the A1–A4 soft spots.
- **Spec ↔ skill ↔ agent coherency is high** overall — `noninteractive-delegation-safety`, `reviewer-budget`, `verify-multimodel-gate` match their implementations and agent frontmatter.
- **Phase gates** (hard STOP between phases) are enforced uniformly in every skill.
- **"Never record test/doc/row counts"** is unusual but internally consistent and well-propagated.

---

## Suggested priority order
1. **E2 / scaffold-sync exit-code / A5** — one gated-session hook-wiring smoke covering exit-2-blocks, `$CLAUDE_PROJECT_DIR`, and cwd (unblocks reliance everywhere). 🟠/🔴
2. **E1** — add a simplicity/quality pass (invoke `simplify`/`code-review` in verify). 🟠
3. **C1** — single-source the `opencode run` delegation harness (largest duplication; safety-critical drift). 🟠
4. **A1–A4** — close the convergence-helper holes (attempt ceiling; test-scoped signature/key; derive edits from git; signature-quality tests). 🟡
5. **B2 / D-ii** — define and tier-scale verify (and resolve phase-gate-vs-SMALL). 🟡
6. **D-i** — add RENAMED to the archive-executor bodies. 🟡
7. **B1** — restructure apply/verify happy-path-first. 🟡
8. The rest (B3/C2/C3/C4/D-iii/E3/E4/E5) as cleanup.
