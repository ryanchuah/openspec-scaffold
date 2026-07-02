# Review log — knowledge-lint

Artifact reviews by `@openspec-reviewer` (deepseek-v4-pro via `opencode run`). One block per round.

---

## proposal.md — Round 1 (2026-07-02) — PASS, PREMISE: AGREE

Reviewer: deepseek-v4-pro. Exit 0, real agent confirmed (no fallback), format asserts passed
(`## Review Round` heading, severity markers, `PREMISE:` line present).

**Verdict: PASS — zero 🔴. Frozen.** Three 🟡 + 3 💡, all explicitly deferred to `design.md` by the
reviewer ("should be resolved during design, not now"). D10 drift-check clean (no reframed problem,
ruled-out approach, or unvetted scope expansion vs. the explore-brief).

Carried into design.md (must be resolved there):
- **🟡1 archive "re-check" vs "fix":** does the widened archive-time sweep only *detect/flag* stale
  claims, or does the archive-executor *correct* them? Must be settled explicitly — "reconciliation"
  historically implies correction, but the linter is detect-only.
- **🟡2 boundary with `sync_scaffold.py --check-refs`:** state the division of labor explicitly.
  Reviewer's read: `--check-refs` = scaffold-rule compliance (narrow, `knowledge/*.md` citations in
  synced files only); `knowledge_lint.py` = drift detection (broad, any repo-relative path in any
  tracked prose). Coexist-not-replace.
- **🟡3 scope of "bodies" in archive sweep is vague:** enumerate the exact files/dirs
  (`knowledge/reference/`, `knowledge/roadmap.md`, the review-backlog / `questions/INDEX.md` Parked, …)
  so the implementer sweeps neither too broadly (per-archive perf hit) nor too narrowly (missed drift).

💡 (design.md should resolve):
- Confirm BOTH `scripts/knowledge_lint.py` and `scripts/test_knowledge_lint.py` land in the manifest.
- State the coexist boundary (💡 overlaps 🟡2).
- Retired-path token list: hardcoded vs per-repo config. Explore-brief open item; premise review
  recommended per-repo config. Resolve in design.

Full review text: `scratchpad/review-proposal.txt` (round 1). Verdict line: "PASS — ready to freeze
and move to design.md."

<details>
<summary>Round 1 review — verbatim</summary>

### Summary

The proposal is coherent, well-structured, and faithfully carries forward the verified explore-brief.
The problem (per-repo knowledge rots because no mechanism systematically re-checks it) is
well-characterized with four concrete drift classes. The two-layer solution (deterministic
`knowledge_lint.py` + LLM `lint-knowledge` skill) covers all four classes. Scope is appropriately
bounded to detection/reconciliation *machinery* only. No conflicts with existing specs
(`knowledge-organization`, `scaffold-sync-mechanism`) — modifications are additive. D10 clean.

### 🔴 Blocking Issues
None.

### 🟡 Should Fix
1. Archive-step "re-check" vs "fix" ambiguity — settle in design.md whether the wider body sweep
   detects/flags only or also corrects prose.
2. Boundary with `sync_scaffold.py --check-refs` unresolved — draw the division explicitly.
3. Scope of "bodies" in archive sweep is vague — enumerate exact files/dirs in design.md.

### 💡 Suggestions
- Confirm both script and test file are added to the manifest.
- State the coexist boundary explicitly in design.md.
- Resolve retired-path token list: hardcoded vs per-repo config (reviewer/premise recommend config).

### Premise Verdict
PREMISE: AGREE (root not symptom ✅; solution targets root ✅; scope right-sized ✅; one blind spot =
archive detect-vs-fix, the 🟡1 above).

### Verdict
PASS — ready to freeze and move to design.md. Resolve the three 🟡 during design, not now.

</details>

---

## specs/ — Round 1 (2026-07-02) — PASS, frozen

Reviewer: deepseek-v4-pro. Exit 0, real agent confirmed, format asserts passed. Reviewed both deltas
(`knowledge-lint` NEW, `knowledge-organization` ADDED).

**Verdict: PASS — zero 🔴.** Reviewer confirmed the deltas faithfully encode the proposal contract and
design decisions, the `knowledge-organization` delta is correctly additive, scenarios testable. Three 🟡
+ 2 💡 (all testability tightenings) — **all applied before freeze** (no 🔴 → no re-review required):
- 🟡1 broken-citation scenario now states the conservative extraction window (backtick-wrapped,
  repo-relative, not-URL, not-absolute; bare mentions/URLs/abs excluded).
- 🟡2 judgment-layer requirement + new `deterministic-pass-runs-first` scenario now encode
  "run `knowledge_lint.py` first, then the LLM sweeps" (D7 ordering).
- 🟡3 `archive-runs-deterministic-linter` scenario now states findings are surfaced but **do not block
  archive completion** (flag-only; pre-existing unrelated drift must not halt archive).
- 💡1 drift exit code pinned to exactly `1` (matches `sync_scaffold.py --check`).
- 💡2 orphan scenario now enumerates the canonical set (`STATUS.md`, `lessons.md`, `roadmap.md`).

`openspec validate` green after edits. Full review text: `scratchpad/review-specs.txt`.

---

## design.md — Round 1 (2026-07-02) — PASS, frozen

Reviewer: deepseek-v4-pro. Exit 0, real agent confirmed, format asserts passed.

**Verdict: PASS — zero 🔴.** Reviewer confirmed the design resolves all five deferred proposal items with
concrete, implementable decisions; every decision maps to a spec requirement; `audit.toml` convention
verified established. Four 🟡 + 2 💡 — **all applied before freeze** (no 🔴 → no re-review), verified
against the source rather than taken on trust:
- 🟡1 canonical basename map enumerated (`STATUS.md`, `lessons.md`, `roadmap.md`, `audit-log.md`);
  `INDEX.md`/`README.md` **excluded** (multi-home → would false-positive — corrects reviewer's suggestion
  to include them).
- 🟡2 (real bug) `knowledge_lint.py` now excludes `knowledge/research/` from the content checks — verified
  `sync_scaffold.py` has `_REF_SCAN_EXCLUDE = ("openspec/changes/", "knowledge/research/")` because
  research holds period-correct analyses. Added to D2 + a spec scenario + VC2b.
- 🟡3 per-repo config key named explicitly: `[knowledge_lint].retired_paths` (array, merged with
  defaults). D5 + spec.
- 🟡4 archive Parked sweep clarified to cover individual `knowledge/questions/<item>.md` bodies, not
  just INDEX one-liners. D8 + knowledge-organization delta.
- 💡5 VC2 chicken-and-egg resolved by the 🟡2 research exclusion (scaffold self-lints clean).
- 💡6 exit code: **kept `1`** (not `2`) with rationale — verified `status_lint.py` returns `2` but so does
  `argparse` on bad flags; `1` matches `sync_scaffold.py --check` and keeps "found drift" distinct from
  "bad invocation." Documented in D2.

`openspec validate` green after edits. Full review text: `scratchpad/review-design.txt`.

---

## tasks.md — Rounds 1–2 (2026-07-02) — PASS, frozen  [Sonnet subagent, per operator]

Reviewer: **Sonnet subagent** (Agent tool, `model: sonnet`) — operator directed this session's tasks.md
review to Sonnet instead of the deepseek `openspec-reviewer`.

**Round 1: NEEDS REVISION — zero 🔴, two 🟡 + two 💡.** Both 🟡 were real and applied (within the frozen
design's D8 scope):
- 🟡A missing negative-citation test → added task 2.9 (bare mention / URL / absolute path NOT flagged).
- 🟡B task 4.2 underspecified the archive-skill edit → verified `openspec-archive-change/SKILL.md` has two
  platform branches (Claude Code `opencode run` prompt string @L124+; OpenCode `@archive-executor`
  Task-tool "Pass:" list @L194+); reworded 4.2 to require updating BOTH delegation payloads.
- 💡 orphan duplicate sub-case folded into task 2.8. (💡 split-1.1 declined — minor granularity.)

**Round 2: PASS — zero 🔴/🟡/💡.** Sonnet re-review confirmed both 🟡 closed, branch names verified against
the real file, no new contradictions, format intact, no verify/archive-phase leakage. `openspec validate`
green.

## Propose phase complete
proposal (deepseek R1) · specs (deepseek R1) · design (deepseek R1) · tasks (Sonnet R1–2) — all frozen.

---

## VERIFY — behavioral review (2026-07-02) — defect found → artifacts amended → fix re-delegated

Orchestrator self-review (read diffs, ran the full suite — green, eyeballed real linter output).
**Defect:** the broken-prose-path-citation check was dominated by false positives against real prose (on
the scaffold's own `knowledge/`: bare filenames `tasks.md`/`SKILL.md`, cross-repo `extrends/AGENTS.md`,
GitHub shorthand `sst/opencode`, non-paths `WHEN/THEN/AND`), and the orphan walk scanned a git-ignored
vendored `OpenSpec/` clone. Green tests missed it (fixtures ≠ messy real prose) — exactly what verify
exists to catch.

**Artifacts amended (pre-archive, disclosed):** design.md D2 (added first-segment gate + git-ignore skip)
+ VC2/2c/2d; specs/knowledge-lint (broken-citation scenario tightened; two scenarios added). `openspec
validate` green. Fix re-delegated to a **Sonnet** apply-executor (per operator's code-updates→Sonnet
instruction), not deepseek.
