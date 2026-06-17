# Review log — single-source-rules

## Round 1 — tasks.md + notes.md — deepseek-v4-pro (openspec-reviewer) — 2026-06-17

**Verdict: NEEDS REVISION** (1 🔴, 4 🟡, 2 💡). Reviewer ran clean (0 "falling back to default agent").

### 🔴 #1 — config.yaml not manifest-synced; Rule 1 home unreachable downstream
Reviewer flagged that the registry claimed `openspec/config.yaml` is manifest-synced ("yes (manifest)")
— it is not (confirmed: not in `scripts/scaffold_manifest.txt`). Concern: a synced skill citing
`config.yaml rules.tasks` could resolve to a stale/abbreviated downstream config.yaml.
**Disposition — FIXED + verified, home kept.** Verified the substance: `extrends` and `psc-monitor` both
carry the full `rules.tasks` verbatim, and `rules.tasks` is **prompt-injected** into the
`openspec instructions tasks` output locally in every repo — so the rule reaches each proposing agent by
injection regardless of the skill body, and the citation resolves to a present home in every repo.
Corrected the registry fact (row 1 "synced?" cell), added a "Rule 1 downstream delivery" guardrail
explaining the injection delivery, and added acceptance criteria 8/9. Kept `config.yaml rules.tasks` as
the home (it is the irreducible prompt-injection point). Logged the pre-existing per-repo-drift risk as a
parked follow-on (sync the `rules:` block via span-logic) — explicitly out of scope.

### 🟡 #2 — propose skill war-story is a DIFFERENT story; task 5.3's "if" was ambiguous
Reviewer noted propose's live-probe story (constructor-kwarg-assumed-available, crashed on first request)
is a distinct companion to the apply-executor mock-sort story, not a Rule-4 duplicate.
**Disposition — FIXED.** Verified (propose SKILL line 79 = the constructor-kwarg story). Revised task 5.3
to LEAVE it intact (optional "see also" cross-ref only) and corrected registry row 4 (genuine duplication
is apply-body ≈ verify only).

### 🟡 #3 — missing criterion: home actually carries the full rule text / resolves downstream
**Disposition — FIXED.** Added acceptance criterion 8 (each home contains full rule verbatim; per-repo
config.yaml carries rules.tasks in all three; synced homes confirmed by the Phase-2 `--check` gate).

### 🟡 #4 — no info-loss backstop for the apply-phase citation collapses (only archive cleanup had one)
**Disposition — FIXED.** Added task 7.4 (grep-confirm each home retains its rule text verbatim) and
acceptance criterion 9.

### 🟡 #5 — task 7.2 `--model` grep may false-positive on prose mentioning `--model`
**Disposition — FIXED.** Reworded task 7.2 as a conservative tripwire requiring manual adjudication of
each hit (code-block/frontmatter change = defect; prose citation = allowed).

### 💡 #6 — cite by exact path; 💡 #7 — convention home reasoning holds
**Disposition — noted.** Tasks already cite by exact path; no change needed for #7 (reviewer confirmed the
`workflow-lessons.md` choice).

## Round 2 — tasks.md + notes.md (re-review) — deepseek-v4-pro — 2026-06-17

**Verdict: READY** (0 🔴, 0 🟡, 3 💡). Reviewer ran clean (0 fallbacks). Confirmed the 🔴 #1 resolution is
sound (prompt-injection is the primary delivery; the skill citation is a pointer, not the sole source) and
all four 🟡 fixes hold. 3 minor 💡s: (1) task 2.2 drop the "propose-specific wording" conditional — APPLIED;
(2) task 3.2 tighten to "confirm, likely no-op" since AGENTS.md tail already cites the ladder — APPLIED;
(3) criteria 1/8 + task 7.4 overlap on "home carries text" — LEFT AS-IS (deliberate redundancy for
info-loss-sensitive work; reviewer noted it is cheap/not harmful). **Frozen for apply.**
