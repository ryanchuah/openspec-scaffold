# Tier-1 edit plan — openspec-scaffold (APPLIED 2026-06-13)

**STATUS: APPLIED in scaffold commit `85cd257`** (main, unpushed). Landed: A1 + A2 (AGENTS.md) and
A3/A4/A5 (decisions.md seeds). Dropped per review: T1-1, T1-6, T1-8. T1-3 settled — EARS label
dropped (the format is BDD/Gherkin-style, not EARS). Optional R1: not done. Each item's verdict and
reasoning are below; checked against the *actual* current text (see `edit-sites-dossier.md`):

- **APPLY** — solid, precise, source-traceable, constraint-compatible. Exact wording below.
- **REFRAME** — the idea is OK but the synthesis put it in the wrong place / wrong form; corrected here.
- **HOLD** — depends on an unresolved question; don't apply blind.
- **DROP** — redundant, cosmetic, or its anchor doesn't exist.

**Headline of the review:** of the 10 Tier-1 candidates, **5 are worth applying**, **1 optional reframe**,
and **4 should be held/dropped** — the dossier showed they were based on a surface reading. The review
also caught an **actual under-reference bug** in AGENTS.md (the skill-file glob). Net result is a much
tighter, defensible change than mechanically applying all 10. All edits touch only AGENTS.md +
`ai-docs/decisions.md`; none touch the normal-workflow autonomy/phase-gates; commit to `main`, unpushed.

---

## APPLY

### A1 (was T1-9) — Harness-neutral skill wording + fix the skill-glob under-reference — `AGENTS.md:80-83`
**Why it grew in value:** the dossier found the glob `openspec-*-change/SKILL.md` matches only
apply/verify/archive — it **silently excludes `openspec-explore`, `-onboard`, `-propose`, `-sync-specs`**.
That's a real inaccuracy in the golden source, not just wording.

Current:
```
**Phase-specific procedural rules live in the skill files, not here.**
The agent invokes the appropriate skill (via the Skill tool) when a phase is entered.
AGENTS.md carries only cross-cutting rules that span multiple phases.
Skill files: `.claude/skills/openspec-*-change/SKILL.md`.
```
Proposed:
```
**Phase-specific procedural rules live in the skill files, not here.**
The agent invokes the appropriate skill (via its harness's skill mechanism) when a phase is
entered. AGENTS.md carries only cross-cutting rules that span multiple phases.
Skill files: `.claude/skills/openspec-*/SKILL.md` (discovered by both harnesses — see
`ai-docs/decisions.md`).
```
**Source:** opencode.ai/docs/skills + verified bundle scan (VERIFY-opencode-claims.md). **Constraint:** agent-neutral ✓.

### A2 (was T1-7) — "When NOT to delegate" guardrail — `AGENTS.md:126-129`
Current bullet ends `…survives interruption.` Append:
```
  **Do not fan out cohesive, dependency-laden work** (e.g. the apply phase's sequential
  tasks): concurrent writers on one working tree corrupt each other — which is exactly why
  apply uses a single sequential executor. Delegation saves time/cost only when the subtasks
  are genuinely independent.
```
**Source:** B-R5 (Akitaonrails 2026 benchmark) + the scaffold's own apply-skill concurrent-writers
rationale (`openspec-apply-change/SKILL.md:124-144`). **Constraint:** ✓ (reinforces an existing design choice).

### A3 / A4 / A5 (was T1-2 / T1-10 / T1-5) — Seed `ai-docs/decisions.md`
The file is an empty template with a defined format. Add these three entries **after the `---`** (they
document the cross-agent invariants whose *rationale* lives nowhere today, AND double as worked examples
of the entry format — covering D-R2's "seed an example"):

```markdown
## Decision: All project state in tracked, agent-neutral files — no harness-native memory
**Date:** 2026-06-13
**Decision:** Project state lives only in tracked files (AGENTS.md, ai-docs/, openspec/). Agents must not rely on harness-native memory (Claude memory, OpenCode session memory, etc.).
**Rationale:** This repo is worked by both Claude Code and OpenCode/DeepSeek agents; only tracked files are visible to both. A harness-native store would be invisible to the other harness and break cross-agent continuity.
**Alternatives considered:** Anthropic's native memory tool (reported ~39% agentic-search gain / ~84% token reduction in its Sept-2025 benchmark — figures per Anthropic, not independently verified) was rejected: Claude-only, no OpenCode equivalent, so it cannot be the shared state store. Revisit only if the dual-harness requirement is dropped.

## Decision: Workflow skills live only under `.claude/skills/` (not duplicated to `.opencode/`)
**Date:** 2026-06-13
**Decision:** The OpenSpec workflow skills are a single copy under `.claude/skills/openspec-*/SKILL.md`; they are NOT duplicated into an `.opencode/skills/` directory.
**Rationale:** OpenCode ≥ 1.16 auto-discovers `.claude/skills/**/SKILL.md` (gated by `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS`, default false), so both harnesses load the same files. Duplicating them would risk two copies drifting apart. Verified 2026-06-13 against opencode 1.17.4 (binary carries the `claude/skills/` scan path; the disable flag is unset).
**Alternatives considered:** A second `.opencode/skills/` copy or a symlink — rejected as redundant given the cross-load, and a divergence risk.

## Decision: No lifecycle hooks in the scaffold
**Date:** 2026-06-13
**Decision:** The scaffold ships no harness hooks (e.g. Claude Code `settings.json` hooks).
**Rationale:** Hooks are Claude-Code-only with no OpenCode equivalent; depending on them would couple workflow behavior to one harness, violating cross-agent compatibility. Policy is enforced in agent definitions and skills, which both harnesses honor.
**Alternatives considered:** Claude Code hooks for guardrails — rejected for the template; an instantiated project MAY add them if it accepts the harness coupling.
```
**Source:** D-R4 / C-R5 / the verified cross-load. **Constraint:** ✓. **⇒ Decision point D-1 below.**

---

## REFRAME (optional)

### R1 (was T1-4) — Name the "separate-model adversarial reviewer" pattern — **AGENTS.md Roles, not the verify skill**
**Correction:** the synthesis said put this in the verify skill — but the dossier shows `@openspec-reviewer`
is **not** in the verify skill at all; it's defined in `AGENTS.md:63-66` and used at propose. The verify
skill's "don't delegate, do it yourself" is a *different* idea (orchestrator's own behavioral review).
So if we name the adversarial-reviewer pattern, it belongs as a short phrase on the reviewer's role in
AGENTS.md. **Low value, optional** — I'd do it only if you want the vocabulary. Exact wording pending a
look at AGENTS.md:50-68.

---

## HOLD / DROP (with reasons — override me if you disagree)

### T1-1 — Rename EXIT sentinel → "liveness sentinel" + promote disk end-state — **DROP (mostly already done; name would collide)**
The apply skill **already** separates the two concepts: completion *detection* via the exit-file
sentinel (`:124-144`) vs. success *judged from disk* — "every task in `tasks.md` is `[x]`" (`:157-165`).
And `:124` already says *"never poll **process liveness**"* (pgrep) — so renaming the exit-file thing to
"liveness sentinel" would **collide** with the existing meaning of "liveness." Also: the archive skill has
**no** sentinel at all, so this would be *adding* machinery, not renaming. Net: the conceptual point B
raised is already implemented; the specific rename is wrong. **Recommend drop.**

### T1-3 — Name the scenario format "EARS" — **HOLD (likely a mislabel)**
The format is literally `#### Scenario: / WHEN / THEN / AND` (`openspec-propose/SKILL.md:279-298`). That is
**Gherkin/BDD** scenario style (When/Then), *not* canonical EARS (whose event-driven form is "WHEN <trigger>
the <system> **shall** <response>"). Labeling it "EARS" in the golden source would propagate a probably-wrong
term, violating source-traceability. The skill already says *"This format—WHEN/THEN/AND—makes requirements
testable,"* which gives the teachability without a contested label. **Recommend hold** unless you want me to
verify the correct notation name first and then label it accurately.

### T1-6 — Promote fold-fix to a cross-cutting AGENTS.md rule — **DROP (it's apply-specific)**
Fold-fix ("fold the scoped fix as the first item of slice N+1's brief") is correct **only during multi-slice
apply** — it exists to avoid concurrent writers (`apply:140-144`). At **verify**, a found defect is fixed by
spawning a **fresh** executor run (a *separate* run) — the opposite of "fold into the next brief." Promoting
fold-fix to a universal AGENTS.md rule would mis-apply it to verify. It's correctly placed where it is.
**Recommend drop** (or, if you want, a one-line pointer — low value).

### T1-8 — Name AGENTS.md the "constitution" in the onboard skill — **DROP (anchor doesn't exist + cosmetic)**
The onboard skill is a **human user tutorial**; it has no passage that walks an *agent* through AGENTS.md, so
there's nowhere to add the framing. The de-facto "constitution" is AGENTS.md's MANDATORY preamble (`:1-22`) +
cross-agent block (`:24-34`), which already say "starting source of truth… override your training data." Adding
the word "constitution" is a cosmetic relabel. **Recommend drop.**

---

## Decision points for you
- **D-1 (gates A3/A4/A5): seed the template's `ai-docs/decisions.md` with the 3 scaffold-invariant entries?**
  My recommendation: **yes** — they fit the file's stated purpose ("non-obvious choice + rationale a future
  agent would re-litigate"), capture rationale that lives nowhere today, and serve as format examples every
  project inherits. The only mild oddity is they're scaffold-level rather than project-specific. Alternative:
  keep decisions.md empty and put these in a scaffold-only notes file. (I lean strongly: seed them.)
- **D-2 (T1-3): EARS label** — drop the label (my lean), or have me verify EARS-vs-Gherkin/BDD and then name
  it correctly?

## Net change set if you approve my recommendations
- `AGENTS.md`: A1 (wording + glob fix), A2 (delegation guardrail) — 2 edits.
- `ai-docs/decisions.md`: A3/A4/A5 — 3 seeded entries.
- (Optional R1 in AGENTS.md Roles.)
- **Held/dropped:** T1-1, T1-3, T1-6, T1-8.
