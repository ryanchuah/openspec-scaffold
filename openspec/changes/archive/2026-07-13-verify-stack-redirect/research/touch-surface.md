# Touch-surface inventory — verify-stack-redirect (OW-3)

Purpose: every file/line-range in this repo that encodes, describes, or depends on the
verify-phase multi-model chain (orchestrator self-review → `deepseek-v4-pro` verifier pass →
`deepseek-v4-flash` verifier pass, same checklist on all three), so OW-3 (redirect the freed
third pass into a lens the stack lacks, e.g. OW-1 test-quality or OW-4 data-scale) can touch
every encoding without leaving drift. Compiled 2026-07-10. Read-only research artifact; no
files outside this doc were modified while compiling it.

All line numbers below are exact at time of writing (git HEAD, uncommitted tree otherwise
clean). Re-check line numbers after any edit lands before citing them elsewhere.

---

## 1. `.claude/skills/openspec-verify-change/SKILL.md` — primary chain definition

This is the skill body itself; it is the single most load-bearing file for OW-3.

- **L14-15** — MANDATORY preamble: self-review is Steps 4-8, non-delegable; explicitly says
  "Defect-handling detail, and the multi-model / simplicity / security gates, are in the
  reference subsections immediately below this preamble."
- **L35-53** — "Multi-model passes (independent verification gates)" section header + body:
  - **L37** tier gate: `"This skill and its multi-model passes apply to MEDIUM and COMPLEX
    changes only. A SMALL change does its own verification per AGENTS.md and does not invoke
    this skill, its multi-model passes, or the verify phase-gate."`
  - **L41-44** platform branch (the exact text OW-3 must rewrite to drop/redirect a pass):
    ```
    - **Claude Code orchestrator:** self-review (you, above) → `deepseek/deepseek-v4-pro`
      verifier pass → `deepseek/deepseek-v4-flash` verifier pass. Three independent views...
    - **OpenCode orchestrator:** self-review (you, above) → `deepseek/deepseek-v4-flash`
      verifier pass only. ...
    ```
    NOTE: this text is *already* stale vs. the `tier-review-tightening` decision
    (`knowledge/decisions/INDEX.md` L35, see §7) which states OpenCode MEDIUM/COMPLEX now
    runs **self→pro→flash**, same as Claude. The invocation section below (L75-93) reflects
    the *updated* pro+flash-for-both-platforms behavior, but this summary paragraph at L41-44
    was never updated to match — an existing, pre-OW-3 drift OW-3 will pass through anyway.
  - **L46** verifier agent pointer: `"The verifier agent is defined in
    .opencode/agents/openspec-verifier.md (default model: deepseek/deepseek-v4-flash;
    bash: a destructive-command denylist (catch-all allow), edit: deny)."`
  - **L48-53** verdict format block (`## Verify Pass — <model-id>` / `VERDICT: READY|NEEDS
    REVISION` / `### Defects` with `- None` sentinel).
- **L55-73** "Claude Code invocation (two passes)" — the two `opencode run` command blocks
  (pro at L61-64, flash at L68-71), each `timeout -k 15 780 ... --agent openspec-verifier
  --model deepseek/deepseek-v4-<tier> ...` — these are the literal command lines the
  `budget-agreement` scaffold_lint check parses (see §9/§11).
- **L75-93** "OpenCode invocation (pro + flash, same chain as Claude Code)" — mirror pair of
  command blocks, explicit line: `"both platforms now run the identical pro → flash chain."`
  (L78-79).
- **L95-100** "Assert the real verifier ran" — cites delegation-harness §b.
- **L102-104** "Judge findings from disk" — overrule-with-rationale rule.
- **L106-114** "Gate semantics and recovery" — hard-gate + rerun-failed-and-after + loop bound
  (3 cycles) — the recovery ladder OW-3 must preserve if it keeps two passes, or simplify if it
  drops to one.
- **L116-123** "Simplicity/quality gate (MEDIUM/COMPLEX)" — runs **after** verifier passes
  return READY, **before** artifact/spec checklist. Positional dependency: if OW-3 changes
  which pass is "last", this gate's "after the verifier passes" anchor must still resolve.
- **L125-132** "Security review (conditional)" — same positional relationship, hard gate for
  COMPLEX on sensitive surfaces.
- **L134** PHASE GATE — STOP after verification (unaffected by pass count, but references the
  verification report which records per-pass verdicts).
- **L193-203** Steps 9-11 in the numbered procedure: Step 9 "Run the independent multi-model
  verification passes (MEDIUM/COMPLEX only)" (L193-195), Step 10 simplicity gate (L197-199),
  Step 11 security review (L201-203) — each explicitly says "Do NOT duplicate ... point to the
  section," i.e. these are just pointers back into L35-132; the substantive edit surface is
  the sections above, not these step stubs.
- **L277-279** "Generate Verification Report" → "Multi-model passes" reporting instruction:
  record each pass's verdict, model, and defects; re-run pairs get both verdicts recorded.
- **L315-358** Step 17 checkpoint-to-notes.md — field 3 explicitly says "attributed to the
  pass/model that surfaced it (self-review, pro pass, or flash pass)" (L328) — this phrase
  hard-codes "pro pass, or flash pass" and must change if the second pass becomes lens-diverse
  rather than same-checklist-different-model.

**Net for OW-3:** essentially the entire "Multi-model passes" section (L35-132) plus the
Step 16/17 reporting language (L277-279, L328) are direct rewrite targets.

---

## 2. `.claude/skills/_shared/delegation-harness.md` — timeout budgets, invocation contract

- **L58-73** "(d) EXIT-sentinel completion detection" — L60-61 scope note: *"Applies only to
  `opencode run` calls launched with `run_in_background: true` — apply executor, verify's
  fix-executor, and verify's verifier passes"* (plural "passes" — becomes singular if OW-3
  drops to one pass per platform).
- **L83-98** "(e) Timeout budget table" — the authoritative budget table. Two rows name the
  verifier passes explicitly:
  ```
  | verify | verifier (pro pass)   | `-k 15 780` | 780 | 15s | Independent verification pass; both platforms use this budget. |
  | verify | verifier (flash pass) | `-k 15 780` | 780 | 15s | Same as pro pass; both platforms. |
  ```
  (These are the literal table rows at the lines starting with `| verify | verifier (pro
  pass)` and `| verify | verifier (flash pass)` — L90 and L91 respectively in the file as
  read.) **This table is the sanctioned-pairs source for `scaffold_lint.py`'s
  `budget-agreement` check** (see §9) — if OW-3 removes a pass, retitles it (e.g. "verifier
  (lens pass)"), or changes its budget, this table's rows must be edited in lockstep with every
  `timeout -k 15 780 ...` invocation line in the verify skill, or `budget-agreement` will flag
  an "embedded pair not in the sanctioned set" or a stale/unused row.
  - **L96-98** explicit note: *"The budgets above are extraction-faithful — this table is the
    single authoritative source for all phase timeout values."*
- **L102-107** "Carve-out: verify's in-process self-review" — explicitly distinguishes the
  self-review (Task-tool spawn, exempt from hardening) from *"the delegated verifier passes
  (pro + flash, both platforms) [which] use `opencode run` and are NOT exempt"* — L107 names
  "pro + flash" explicitly; would need updating if the pass identity/count changes.

**Net for OW-3:** the §e table (2 rows) and the two "pro + flash" / "passes" mentions above
must track whatever the new pass count/identity becomes.

---

## 3. `AGENTS.md` — verify-chain narrative, roles, SMALL rule

- **L125-136** — the `openspec-verifier` role paragraph (full text, load-bearing):
  > "The `openspec-verifier` (deepseek, read-only, bash-capable) is an independent multi-model
  > verification pass invoked during verify for all changes: SMALL changes run a single flash
  > pass outside the verify skill; MEDIUM and COMPLEX changes run pro + flash via the verify
  > skill (layered after the orchestrator's self-review and before the artifact/spec mapping
  > checklist). ... The pass chain is identical on both platforms: Claude Code orchestrator →
  > self → pro → flash; OpenCode orchestrator → self → pro → flash. Both platforms invoke the
  > verifier via hardened `opencode run --agent openspec-verifier` (two invocations:
  > `--model deepseek/deepseek-v4-pro` then `--model deepseek/deepseek-v4-flash`)."
  Every clause here ("pro + flash", "self → pro → flash" x2, "two invocations") is a literal
  chain-shape assertion OW-3 must rewrite.
- **L147** — OpenSpec workflow step 4: *"verify — deep behavioral review by the orchestrator,
  followed by independent multi-model verification passes (the `openspec-verifier`) and the
  simplicity/quality gate as hard gates before the artifact/spec mapping checks."* (generic
  enough it may survive unchanged, but "multi-model verification passes" plural should be
  sanity-checked against the new shape.)
- **L169-174** — SMALL tier bullet, single-flash-pass rule (verbatim): *"SMALL does not invoke
  the verify skill, is not subject to its multi-model passes or verify phase-gate STOP, and
  SHALL run a single `deepseek/deepseek-v4-flash` verifier pass (same invocation shape as in
  the verify skill's flash pass)."* — cites "the verify skill's flash pass" by name; if OW-3
  renames/redirects the flash pass identity in the verify skill, this cross-reference must
  still resolve correctly (SMALL's own pass should very likely stay the same-checklist flash
  pass even if MEDIUM/COMPLEX's second pass becomes lens-diverse — needs an explicit design
  decision, flagged here as a design question, not assumed).
- **L213-217** — MEDIUM / COMPLEX tier bullets: *"Runs the verify skill (including its
  multi-model passes and phase-gate STOP)"* (both tiers, L215 and L217) — generic phrasing,
  low risk but should be scanned.
- **L392-409** — "After reading this file" acknowledgment checklist, item (2): *"verify is
  your deep behavioral review, followed by independent multi-model verification passes (the
  `openspec-verifier`) and the simplicity/quality gate..."* (L395-396) — same generic phrasing
  as L147, likely survives, but is another literal occurrence of "multi-model verification
  passes" to sanity-check post-edit.

**Net for OW-3:** L125-136 is the hard rewrite target (every clause encodes the exact
self→pro→flash / two-invocation shape); L169-174 (SMALL rule) needs an explicit decision on
whether it stays untouched; L147/L215/L217/L395-396 are generic-enough mentions to re-scan but
likely don't need substantive rewording.

---

## 4. `openspec/config.yaml` — rules block

- **L31-44** `rules.verify:` block. Full text: describes the *self-review* only ("Verify is the
  orchestrator's own substantive behavioral review... read the actual diffs... re-run the FULL
  test suite... eyeball the real output... on any defect, diagnose and scope it, then
  re-delegate the fix..."). **It does NOT mention the pro/flash multi-model passes at all** —
  no `deepseek-v4-pro`, `deepseek-v4-flash`, or `openspec-verifier` token anywhere in this
  file. Confirmed via full-file read and grep.
- **L11 / L45 / L57** other `rules:` keys (`tasks`, `archive`, `research`) — none mention the
  verify chain.

**Net for OW-3:** no edit required here — `openspec/config.yaml` deliberately scopes `rules.verify`
to the non-delegable self-review only; the multi-model passes are documented exclusively in the
verify skill + AGENTS.md, which the config.yaml preamble at the top of the verify skill (L15)
explicitly defers to ("Per AGENTS.md and openspec/config.yaml, verifying a change is the
orchestrator's own substantive behavioral review... Defect-handling detail, and the multi-model
/ simplicity / security gates, are in the reference subsections"). Because the `rules:` block IS
auto-propagated by `sync_scaffold.py` (per AGENTS.md's propagation contract), confirm this
absence stays intentional rather than accidental if the change touches config.yaml for any other
reason.

---

## 5. `.opencode/agents/openspec-verifier.md` + `.claude/agents/` twin + body-agreement coverage

- **File**: `.opencode/agents/openspec-verifier.md` (single file; default
  `model: deepseek/deepseek-v4-flash`, frontmatter L1-70, body L72 onward).
  - Frontmatter L1-4: description explicitly says *"Invoked by the primary agent during the
    verify phase — do not invoke directly."* Generic enough to survive unless the role itself
    (not just invocation count) changes under OW-3.
  - Body L74 (first line of "Your Review"): *"Your job is to perform the same behavioral review
    the self-review performs, but you never modify files."* — describes **what checklist the
    agent runs**, i.e. this file's body IS "the same checklist" that OW-3 wants the freed pass
    to diverge from. If OW-3 redirects the third (or second) pass to a lens (test-quality /
    data-scale) rather than the full behavioral review, this agent's body needs either (a) a
    parameterized/lens-aware body, or (b) a **second agent file** for the lens pass — a design
    decision, not something this inventory should presume.
  - Numbered review steps 1-4 (L79-88 area): git diff read, full suite re-run, real-output
    eyeball, live smoke for external-API surfaces — this is exactly "the same checklist" all
    three passes currently run (per OW-3's stated rationale in OUTSTANDING-WORK.md L51-52,
    §10 below).
  - Verdict format block near end of file (mirrors SKILL.md L48-53 verbatim) — same
    `## Verify Pass — <model-id>` / `VERDICT:` / `### Defects` shape.

- **`.claude/agents/` twin — DOES NOT EXIST.** `.claude/agents/` contains only
  `apply-executor.md` and `archive-executor.md`. There is **no**
  `.claude/agents/openspec-verifier.md`. This is by design: per AGENTS.md L133-136 and the
  verify SKILL.md L46, **both platforms** invoke the verifier via `opencode run --agent
  openspec-verifier` (never via a native Claude subagent), so a single `.opencode/agents/`
  file serves both harnesses — there is no twin to keep in sync.

- **`scripts/test_executor_body_agreement.py` coverage — does NOT cover this agent.** Read in
  full (L1-104): `EXECUTOR_PAIRS` (L28-38) lists exactly two pairs —
  `("apply-executor", .claude/agents/apply-executor.md, .opencode/agents/apply-executor.md)`
  and `("archive-executor", ...)`. `openspec-verifier` is absent from this list (correctly, since
  it has no `.claude/` twin to compare against) and `openspec-reviewer` is likewise absent (same
  reason — reviewer is also `.opencode/`-only). **No test in this repo asserts anything about
  `openspec-verifier.md`'s content, structure, or agreement with any other file.** Confirmed via
  repo-wide grep (`tests/` and `scripts/` — see §9) — the only automated surfaces touching this
  file are `scaffold_lint.py`'s `dangling-skill-refs` (token resolution only) and
  `budget-agreement` (timeout-pair extraction only, and this file itself contains no `timeout
  -k` command — the invocation lines live in the *skill*, not the agent body).

**Net for OW-3:** `.opencode/agents/openspec-verifier.md` body is a direct edit target if the
lens content differs per pass; no `.claude/agents/` twin exists to keep in sync; no executor-
body-agreement test needs updating (it doesn't cover this file today, and won't need to unless
OW-3 deliberately adds a `.claude/` twin, which would be a new design decision, not a drift fix).

---

## 6. Other skills — apply / propose / archive / other `verify-*`

Grepped each skill file for `verif`, `pro pass`, `flash pass`, `deepseek-v4-pro`,
`deepseek-v4-flash`, `openspec-verifier`:

- **`.claude/skills/openspec-apply-change/SKILL.md`** — all hits are generic phase-transition
  mentions of "verify" (e.g. L21 PHASE GATE: *"Say 'verify <name>' when you want me to review
  the implementation"*; L110-139 are the apply-executor's own flash invocation, unrelated to
  the verify chain). **No mention of the pro/flash verifier passes.** No edit needed.
- **`.claude/skills/openspec-propose/SKILL.md`** — hits are all about design.md's
  "Verification" *section* (acceptance criteria written at propose, consumed at verify) and the
  propose-phase `deepseek-v4-pro` **reviewer** (a different agent/role, `openspec-reviewer`, not
  `openspec-verifier`). **No mention of the verify multi-model chain.** No edit needed.
- **`.claude/skills/openspec-archive-change/SKILL.md`** — hits are generic ("verify by reading
  back", "verify the tree holds only this change", knowledge/STATUS.md must record the verify
  *outcome*) plus its own `deepseek-v4-pro` **archive-executor** invocation (different role).
  **No mention of the pro/flash verifier chain.** No edit needed.
- **No other `verify-*` skill exists.** `find .claude/skills -iname '*verify*'` returns only
  `openspec-verify-change/` (dir) and its `SKILL.md`. `openspec-sync-specs/SKILL.md` and
  `openspec-explore/SKILL.md` were also grepped — zero hits for any chain-related token.

**Net for OW-3:** none of the other four lifecycle skills need editing; the entire in-skill
surface is `openspec-verify-change/SKILL.md` (§1) alone.

---

## 7. `knowledge/` tree

### `knowledge/questions/verify-multimodel-gate-follow-ons.md` (full file, 11 lines)
Shipped-2026-06-16 follow-on ledger for the original multi-model gate. Full gist:
- Rerun-failed-and-after residual risk — monitored/accepted trade-off (a late pass isn't
  re-checked by earlier passes).
- OpenCode Task-tool verifier path "not live-probed" (L6) — **this is now stale**: per the
  `tier-review-tightening` decision (below), OpenCode no longer uses the Task-tool path at all
  (it switched to `opencode run --model`), so this open question about a since-abandoned code
  path is moot and should be closed/reworded when OW-3 touches this area.
- `edit: deny` not separately probed (low risk, structurally present).
- Bash destructive-command denylist "deferred" (L8) — **now superseded**: the denylist IS
  implemented today (`.opencode/agents/openspec-verifier.md` frontmatter `bash:` block, §5) per
  the later `noninteractive-delegation-safety` capability (§8) — another stale line.
- "Scaffold has no runnable test suite" (by design).
- Propagation backlog — DONE via W6.

This file is a good candidate for OW-3 to fold into/retire, since two of its five items are
already resolved/superseded by later changes and it directly concerns the chain being
restructured.

### `knowledge/decisions/INDEX.md` — relevant registry lines
- **L28**: `- **2026-06-16** · verify-multimodel-gate · independent multi-model verification
  passes (self→pro→flash) as hard gates layered after self-review →
  openspec/changes/archive/2026-06-16-verify-multimodel-gate/`
- **L31**: `- **2026-06-17** · lifecycle-gates · verify gate tier-scaled (MEDIUM/COMPLEX only);
  simplicity + security gates added; archive-executor handles RENAMED; body-agreement guard
  added → openspec/changes/archive/2026-06-17-lifecycle-gates/`
- **L35**: `- **2026-06-17** · tier-review-tightening · [inline] SMALL changes require a flash
  verifier pass; OpenCode MEDIUM/COMPLEX runs self→pro→flash (same chain as Claude); OpenCode
  verifier uses opencode run --model not the Task tool; fix-executor timeout floor raised to
  600s/-k30 (committed 2e152d4, no change archive)` — **this decision is the one that made
  OpenCode's chain identical to Claude's**, and is why AGENTS.md L133-136 says "identical on
  both platforms" while `noninteractive-delegation-safety/spec.md` still describes the old
  Task-tool path (§8 — pre-existing spec/decision drift, independent of OW-3 but adjacent).
- **L45**: `- **2026-06-26** · pro-agent-flash-delegation · [inline] pro-tier agents
  (openspec-reviewer, openspec-verifier, archive-executor) may offload bulk reading to a new
  read-only explore-flash subagent...` — unrelated to pass *count*, just delegation ergonomics;
  no rewrite needed but worth being aware of when touching the verifier agent body.

OW-3 will add a new decisions/INDEX.md line at archive (not authored now — per AGENTS.md
write-discipline, decisions entries are reconciled at archive by the archive-executor).

### `knowledge/lessons.md`
- **L22**: *"Per-deliverable independent review for info-loss-sensitive work... Gate each
  deliverable behind: ... (3) a deepseek-v4-pro openspec-verifier pass via hardened opencode
  run..."* — a lessons-learned narrative citing the verifier by name/tier; generic enough (about
  *when* to add an extra pro pass for a specific class of work) that it likely survives, but
  should be re-read once OW-3 lands in case "a deepseek-v4-pro openspec-verifier pass" no longer
  cleanly describes the new chain shape.
- No other lines assert the self→pro→flash chain shape itself.

### `knowledge/roadmap.md`
- **L18-19**: the exact roadmap entry that *is* the source motivation for OW-3 (see §10 for full
  quote) — describes the "verify self→pro→flash stack runs the same checklist three times" and
  recommends "redirect the third pass to a lens the stack lacks, not add passes." This is
  prose to be marked resolved/pruned once OW-3 ships (per roadmap.md's own stated convention,
  L3: "Prune entries as they graduate into real changes").

---

## 8. `openspec/specs/` — capability specs that pin the chain

Grep across `openspec/specs/` for `verifier|deepseek-v4-pro|deepseek-v4-flash|multi-model|
multimodel` hits exactly four capability spec files:

### `openspec/specs/verify-multimodel-gate/spec.md` — **THE capability that pins the chain.**
This is the authoritative spec-level pin; **a spec delta against this capability is required**
for OW-3 (this is the answer to "does the change need a spec delta" — yes, unambiguously).
Key requirements (full file read, 119 lines):
- **L7-8** Requirement "Verify runs independent multi-model passes after the self-review" —
  states the exact platform-dependent sequence verbatim: *"a Claude Code orchestrator SHALL run
  self-review → a deepseek/deepseek-v4-pro verifier pass → a deepseek/deepseek-v4-flash
  verifier pass; an OpenCode orchestrator SHALL run self-review → a deepseek/deepseek-v4-flash
  verifier pass only."* (NOTE: this text itself is stale vs. `tier-review-tightening" — it still
  describes OpenCode as flash-only, pre-dating the decision that made both platforms run
  pro+flash. This spec was apparently never re-synced after that inline decision, which is
  itself a finding: **the capability spec is already out of step with AGENTS.md/the skill**, a
  gap OW-3 should close regardless of its own redirect.)
- **L10-21** Scenarios pinning: "A MEDIUM/COMPLEX Claude Code change runs three passes",
  "...OpenCode change runs pro then flash" (contradicts L8's "flash only" prose in the same
  file — internal inconsistency pre-dating OW-3), "A SMALL change runs self-review plus a
  required flash pass."
  **This scenario-vs-prose self-contradiction inside the frozen spec (L8 says OpenCode is
  flash-only; L14-16 scenario says OpenCode runs pro-then-flash) is worth flagging explicitly
  as a pre-existing spec defect uncovered while researching OW-3.**
- **L27-40** Requirement "Each verification pass is a hard gate with rerun-failed-and-after
  recovery" — the fix/re-run/loop-bound semantics (3-cycle escalation), pass-numbering
  implicitly two-or-three deep.
- **L42-51** Requirement "The delegated verifier runs the behavioral review read-only and emits
  a machine-discriminable verdict" — pins "the same behavioral review the self-review
  performs" as THE checklist every pass runs — this is the literal requirement OW-3 must add a
  scenario/requirement to override (a lens-diverse pass performing a *different*, narrower
  review).
- **L64-69** Requirement "A single verifier agent serves both models, invoked via opencode run
  on both platforms" — pins the single-agent-file-two-`--model`-flags architecture (§5). If
  OW-3 introduces a second agent file or a lens-parameterized prompt, this requirement needs a
  delta.
- **L71-80** Requirement "Each pass's verdict and model are recorded" — the reporting
  contract mirrored in SKILL.md §1 L277-279/L328.
- **L82-97** Requirement "Verify runs a simplicity/quality gate (MEDIUM/COMPLEX)" — positional
  dependency on "after the verifier passes return READY."
- **L99-118** Requirement "Verify runs a security review for sensitive-surface changes" — same
  positional dependency.

### `openspec/specs/noninteractive-delegation-safety/spec.md` — heavily entangled, ALSO STALE
- **L6** (Purpose paragraph line 1 of Requirements): *"Every delegated opencode run invocation
  in the OpenSpec workflow — the propose reviewer, the apply executor, the archive executor,
  the verify fix-executor, and the verify verifier passes (under a Claude Code orchestrator, the
  deepseek/deepseek-v4-pro and deepseek/deepseek-v4-flash passes) — SHALL close stdin...**The
  verify verifier pass under an OpenCode orchestrator is spawned in-process via the Task tool
  (subagent_type: openspec-verifier), not via opencode run, and is NOT subject to this
  requirement**..."* — **this is factually stale**: per `tier-review-tightening`
  (decisions/INDEX.md L35) and the verify SKILL.md's own "OpenCode invocation (pro + flash, same
  chain as Claude Code)" section (§1, L75-93), OpenCode's verifier pass moved to `opencode run
  --model` and IS now subject to the stdin/`--dir` hardening. This paragraph, plus the matching
  **Scenario: OpenCode Task-tool verifier spawn is exempt** (L17-19), describe a code path that
  no longer exists in practice.
- **L13** Scenario "Every delegated invocation closes stdin" — *"including the verify verifier
  pro and flash passes"* — generic enough to survive.
- **L22** Requirement "Delegated agents leave no reachable ask-permission on their legitimate
  path" — describes the verifier's `external_directory`/`bash` containment; independent of pass
  *count*, but references "the verify verifier" as a single entity — fine unless OW-3 splits it
  into multiple differently-permissioned agents.
- **L46-165** (requirements "Verify verifier is denied destructive shell commands regardless of
  path" and "Verify verifier prompt carries a data-safety preamble as the judgment layer") —
  entirely about the agent's permission/safety posture, orthogonal to lens content; low risk
  from OW-3 unless a new lens-specific agent file is introduced (then these requirements would
  need to be asserted for the new file too).

**This spec's Task-tool-exemption language (L6, L17-19) is a pre-existing drift, independent of
OW-3's own scope, but since OW-3 is already re-touching the verify chain end-to-end, fixing this
stale scenario in the same change (or filing it as an explicit adjacent follow-on) avoids
leaving two known-stale specs in the tree simultaneously.**

### `openspec/specs/reviewer-budget/spec.md` — tangential, NOT the verifier
- **L12**: *"(openspec-verify-change's behavioral review is the orchestrator's own, not a
  wrapped reviewer call.)"* — this spec governs the **`openspec-reviewer`** (premise/proposal
  reviewer) budget, a distinct agent/role from `openspec-verifier`. The one-line parenthetical
  merely disambiguates the two roles. **No edit needed** — OW-3 does not touch
  `openspec-reviewer` or its budget.

### `openspec/specs/premise-review-gate/spec.md` — tangential, NOT the verifier
Multiple mentions of "verify"/"verified" are all about the premise-review/direction-gate
mechanism (a different capability entirely — pre-implementation, not post-implementation).
**No edit needed.**

**Net for OW-3: YES, a spec delta is required** against `openspec/specs/verify-multimodel-gate/`
(the capability that directly pins the chain shape, gate semantics, and single-agent
architecture) and very likely also against `openspec/specs/noninteractive-delegation-safety/`
(to fix the already-stale OpenCode Task-tool exemption language while the chain is being
re-touched, or explicitly scope that fix out with a documented reason).

---

## 9. Tests / lint — anything asserting the chain

- **`scripts/test_executor_body_agreement.py`** — does NOT cover `openspec-verifier` (§5);
  only asserts `apply-executor`/`archive-executor` `.claude`↔`.opencode` body agreement.
- **`scripts/scaffold_lint.py`** — the **`budget-agreement`** check (docstring L97-112, impl
  `check_budget_agreement` at L433+, called at L468) is the one automated mechanism that
  *would* fail if OW-3 edits invocation `timeout -k <G> <B>` lines in the verify skill without
  updating the §e table in `delegation-harness.md` (or vice versa) — see §2. It extracts every
  `timeout -k (\d+) (\d+)` pair from `AGENTS.md` + all `.claude/skills/**/*.md` +
  `.claude/agents/*.md` + `.opencode/agents/*.md`, and cross-checks against the backtick-quoted
  `-k G B` pairs on every `|`-prefixed table row in `delegation-harness.md`'s §e section — any
  embedded pair not in the sanctioned set is a finding. This is the direct regression gate for
  OW-3's budget-table edits; **run `scripts/scaffold_lint.py` after editing** as part of OW-3's
  own verify phase.
- **`scripts/test_scaffold_lint.py`** — has its own `budget-agreement` unit tests (L466-546,
  e.g. `test_budget_agreement_clean_no_findings`, `test_budget_agreement_embedded_pair_not_
  sanctioned_flagged`, `test_budget_agreement_table_not_found_flagged`,
  `test_budget_agreement_could_not_parse_table_flagged`) — these test the *checker itself*
  against synthetic fixtures, not the real repo files, so they do NOT need editing for OW-3
  (they'd only need touching if OW-3 changed the *regex contract*, e.g. renamed the §e anchor
  or the table-cell format, which is out of scope).
- **`scripts/scaffold_lint.py`**'s **`dangling-skill-refs`** check (L84-95, `_TOKEN_RE`) scans
  for `\bopenspec-[a-z][a-z-]*[a-z]\b` tokens and requires each to resolve to a skill dir or
  agent-file stem. `openspec-verifier` already resolves (agent file exists); if OW-3 introduces
  a second, differently-named lens-agent file (e.g. `openspec-lens-verifier`), that new file
  itself becomes the resolution target and no separate registration step is needed beyond
  creating the file — but any *prose mention* of a not-yet-created agent name would flag.
- **`tests/`** (top-level dir: `canary-non-convergence/`, `commit-gate-smoke/`,
  `skill-enumeration-smoke/`) — grepped for `openspec-verifier|deepseek-v4-pro|deepseek-v4-flash
  |verify.*pass`: **zero hits.** No test in `tests/` asserts anything about the chain.
- **`scripts/knowledge_lint.py`** — grepped for verifier/chain tokens: no hits; its checks are
  generic (STATUS.md cap, decisions/questions INDEX format, ratchet-log format per the pending
  lesson-check-ratchet change) and orthogonal to the verify chain.

**Net for OW-3:** the only automated regression surface is `scaffold_lint.py`'s
`budget-agreement` (must stay green — edit the §e table and invocation lines together) and
`dangling-skill-refs` (trivially satisfied if any new agent file is added). No test file needs
editing to *add* coverage unless OW-3 wants to newly assert the redirected pass's behavior
(there is currently no regression test for the verifier chain's shape at all — worth noting as
a gap, not a blocker).

---

## 10. `openspec/changes/lesson-check-ratchet/` (OW-2, frozen) + OW-1/OW-4 scope wording

### OW-2 (`lesson-check-ratchet`) — summary (≤15 lines)
Status: **propose-complete, paused at apply** (0/14 tasks checked, per `tasks.md`; explicit
pause recorded in `notes.md` "PAUSED AT APPLY per operator instruction"). Deliverables/
contracts it ships once applied:
1. **New closure rule (the ratchet)**: every generalizable finding gets exactly one recorded
   disposition — `check:` / `test:` / `waiver:` / `open:` / `grandfathered:` — preference
   order check > frozen test > waiver, enforced by `knowledge_lint.py`, rule text in AGENTS.md.
2. **New ledger** `knowledge/ratchet-log.md` (registry-line format, same shape class as
   `audit-log.md`); per-repo content, scaffold-format-only.
3. **New per-repo invariant framework**: `checks/*.py` flat-dir slot, one file = one invariant,
   stdlib-only runner `scripts/repo_lint.py`, registered in `checks.py`, auto-enabled when
   non-empty.
4. **New `knowledge_lint.py` checks**: ledger format, missing/invalid disposition, dangling
   enforcement pointer, stale waiver.
5. **Close-out routing**: bounded ratchet-triage step added to the **archive** skill and the
   **run-audit** skill's triage step (NOT the verify skill) — three-question classification.
6. Explicitly out of scope: OW-1's test-quality detectors, OW-4's data-scale detector, OW-5/6
   audit skills (they consume this routing interface later, not built here).

**Does OW-2 add any verify-phase lens/rule that OW-3's freed third pass could point at?**
**No.** OW-2's routing hooks land in **archive** (Step 6, primary's review) and **run-audit**
(Step 3, triage) — explicitly not in the verify skill (design.md "Routing hooks" list, L155-166,
names only those two skills). OW-2 is a *closure/enforcement* mechanism for findings already
surfaced by some other detector; it does not itself surface findings during verify, and is not a
verify lens. It IS, however, the natural **landing framework** for OW-1's/OW-4's detectors once
those exist (via `checks/*.py` + `scripts/checks.py` registration) — so OW-3's redirected pass
would point at OW-1/OW-4's *verify-lens question* (a prompt-level instruction to the redirected
pass), which is a distinct thing from OW-2's *repo-invariant checks* (a deterministic
`checks.py` detector). They are complementary, not overlapping: OW-2 doesn't need to ship before
OW-3, and OW-3 doesn't depend on OW-2's ledger mechanism at all.

### OW-1 / OW-4 verify-lens wording (from `OUTSTANDING-WORK.md`)
- **OW-1** (L14-19): *"Add a verify lens question: 'would this test fail if the behavior
  broke?'"* — this is the literal candidate prompt-lens for OW-3's redirected pass if routed to
  test-quality.
- **OW-4** (L62-66): *"verify rule that a data-path change requires either an at-scale run or a
  recorded bounded-domain argument in notes.md."* — the literal candidate lens if routed to
  data-scale instead.

Neither OW-1 nor OW-4 has been built yet (both are still `OUTSTANDING-WORK.md` line items, no
change dir exists for either). **OW-3 therefore has two textual candidate lenses to draw its
new pass prompt from, but no existing runnable detector/lens artifact to delegate to** — the
"lens the freed pass runs" will need to be authored as part of OW-3 itself (a verifier-prompt
change), not borrowed from a shipped OW-1/OW-4 implementation.

---

## 11. Manifest propagation — `scripts/scaffold_manifest.txt`

Every file identified above as an actual edit target IS listed in the manifest (propagates to
`extrends`/`psc-monitor` on next `sync_scaffold.py` run) **except** the two categories the
manifest explicitly never carries (per its own comments and AGENTS.md's propagation contract):

| File | In manifest? | Manifest line |
|---|---|---|
| `.claude/skills/openspec-verify-change/SKILL.md` | YES | L15 |
| `.claude/skills/_shared/delegation-harness.md` | YES | L27 |
| `AGENTS.md` | YES (span-replace, not wholesale) | L69 |
| `openspec/config.yaml` | YES (`rules:` block only; `context:` preserved per-repo) | L33 |
| `.opencode/agents/openspec-verifier.md` | YES | L24 |
| `.opencode/agents/openspec-reviewer.md` | YES (tangential, unedited) | L23 |
| `.claude/agents/apply-executor.md` / `archive-executor.md` | YES (unedited by OW-3) | L5-6 |
| `scripts/test_executor_body_agreement.py` | YES (unedited by OW-3) | L54 |
| `.claude/skills/openspec-apply-change/SKILL.md` | YES (unedited) | L10 |
| `.claude/skills/openspec-propose/SKILL.md` | YES (unedited) | L13 |
| `.claude/skills/openspec-archive-change/SKILL.md` | YES (unedited) | L11 |
| `scripts/scaffold_lint.py` | **NOT in manifest** (authoring-side tool; explicitly excluded — its own docstring L45-50 and the manifest header both name it as never-synced) | n/a |
| `openspec/specs/verify-multimodel-gate/spec.md` | **NOT in manifest** — `openspec/specs/` is explicitly listed in AGENTS.md (L384) as "NOT auto-propagated — needs a manual per-repo sweep" | n/a |
| `openspec/specs/noninteractive-delegation-safety/spec.md` | **NOT in manifest** (same reason — all of `openspec/specs/`) | n/a |
| `knowledge/*` (questions, decisions, lessons, roadmap) | **NOT in manifest** (AGENTS.md L382-384: per-repo project knowledge, manual sweep only) | n/a |
| `knowledge/README.md` | YES (taxonomy map only) | L30 |

**Practical implication:** the skill/agent/harness/AGENTS.md edits (§1-3, §5) propagate
automatically to downstream repos on the next authorized `sync_scaffold.py` run. The spec delta
(§8) and any per-repo knowledge updates (§7) do **not** propagate automatically — if OW-3's spec
delta matters to downstream repos' own `openspec/specs/` copies, that is separately flagged
manual work, consistent with existing scaffold-sync precedent (nothing new to design here, just
something to remember at archive).

