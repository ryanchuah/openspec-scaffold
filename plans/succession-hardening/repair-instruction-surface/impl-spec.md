# Implementation spec — repair-instruction-surface (SMALL)

You are the apply-executor for a SMALL change. Implement the three sub-scopes below **in order**,
check each box as it lands, and do NOT commit (the orchestrator reviews and commits). This is a
**content-preserving** change: sub-scope (a) is a reorganization — you must preserve every rule,
caveat, code block, timeout budget, and severity label **verbatim**; only headings, step numbers,
and the one preamble's framing may change. Invent no new normative content except the exact fill
text given for (b) and (c) below.

**Hard invariant for the whole change:** after your edits, `python3 scripts/scaffold_lint.py` MUST
print `scaffold-lint: clean` (exit 0) and `pytest -q` MUST be green. The `scaffold_lint`
`budget-agreement` and `dangling-skill-refs` checks run against the edited verify skill via the
live-repo SEAL test — if you accidentally alter a `timeout -k G B` number or break a skill
reference, the suite goes red. Run both before you finish; if either is red, fix the file you
touched (never loosen a test).

---

## Sub-scope (a) — restructure `.claude/skills/openspec-verify-change/SKILL.md`

**Problem:** the file has TWO procedures — the mandatory behavioral review as a blockquote
*preamble* (currently lines ~14–41), then a separately numbered **"Steps 1–10"** artifact/spec
checklist. Smaller models pattern-match on "Steps 1–N" as *the* procedure and skip the behavioral
half. Fix: make the behavioral review numbered Steps INSIDE the single `**Steps**` procedure, and
shrink the MANDATORY blockquote to a short pointer preamble (exactly mirroring how
`.claude/skills/openspec-apply-change/SKILL.md` uses a MANDATORY preamble that points into its
Step 6).

### Exact target structure (top to bottom)

1. **Frontmatter** — unchanged.
2. **Intro line** ("Verify that an implementation matches the change artifacts…") — unchanged.
3. **MANDATORY preamble (REWRITTEN, short — this is the only prose you rewrite).** Replace the old
   blockquote's opening/closing framing (old lines ~14–15 and ~23) with a 3–5 sentence blockquote
   that points INTO the Steps. It MUST say, in your own concise words but preserving every claim:
   - Verifying a change is the orchestrator's **own** substantive behavioral review of the
     apply-executor's work — not a checklist rubber-stamp, and not delegated.
   - **Steps 4–8 below ARE that behavioral review and are the core of verify.** They are mandatory
     and non-delegable. Do NOT skip to the artifact/spec mapping checks (Steps 12–18) or treat the
     numbered checklist as the whole job.
   - Do not trust the executor's completion summary — trust the code, tests, and real output.
   - If the behavioral review (Steps 4–8) fails, the verdict is **NEEDS REVISION** regardless of the
     checklist.
   - Defect-handling detail, and the multi-model / simplicity / security gates, are in the
     reference subsections immediately below this preamble.
4. **`### On a defect / failure modes`** — a `###` subsection carrying the OLD blockquote's
   "#### On a defect / failure modes" body **verbatim** (old lines ~25–41: the caveats on the 5
   steps, the "Fix-redelegation mechanics (Claude Code)" bullets, the "Escalation rungs" bullets).
   Keep every `timeout … opencode run …` line, every budget, every `§` citation byte-for-byte.
   Change only the heading level (`####` → `###`) and, if a bullet says "the 5 self-review steps",
   keep it — it now refers to Steps 4–8.
5. **`### Multi-model passes (independent verification gates)`** — verbatim (old lines ~43–122),
   including the SMALL-tier-exclusion note, the pass sequence, all `timeout -k 15 780 opencode run`
   blocks, assert/judge/gate-semantics subsections. Unchanged.
6. **`### Simplicity/quality gate (MEDIUM/COMPLEX)`** — verbatim (old ~124–131). Unchanged.
7. **`### Security review (conditional — sensitive-surface changes)`** — verbatim (old ~133–140).
   Unchanged.
8. **PHASE GATE note** — keep the `**PHASE GATE — STOP after verification.**` paragraph (old ~142)
   verbatim, in this position.
9. **`**Input**`** — verbatim (old ~144).
10. **`**Steps**`** — the SINGLE numbered procedure. Renumber to exactly this 18-step order. Each
    step's BODY is the verbatim body of its source; only the number/heading changes:
    - **1. Select the change** — old Step 1 body (verbatim).
    - **2. Check status to understand the schema** — old Step 2 body (verbatim).
    - **3. Get planning context and load artifacts** — old Step 3 body (verbatim).
    - **4. Read the actual diffs and changed files** — old blockquote behavioral step 1 body
      (verbatim). Add a short lead marking Steps 4–8 as "Behavioral review — mandatory, do not
      delegate, do not trust the executor's summary."
    - **5. Re-run the FULL test suite yourself** — old blockquote behavioral step 2 body (verbatim).
    - **6. Eyeball the real output the code produces** — old behavioral step 3 body (verbatim).
    - **7. If the change touches an external API / network service, run its live smoke** — old
      behavioral step 4 body (verbatim).
    - **8. On any defect** — old behavioral step 5 body (verbatim), ending with a pointer:
      "See **On a defect / failure modes** above for the fix-redelegation mechanics and escalation
      rungs."
    - **9. Run the independent multi-model verification passes (MEDIUM/COMPLEX only)** — a short
      step whose body says: MEDIUM/COMPLEX changes run the passes in **Multi-model passes** above
      (SMALL does not); run them here, after the behavioral review and before the mapping checks.
      Do NOT duplicate the invocations — point to the section.
    - **10. Run the simplicity/quality gate (MEDIUM/COMPLEX only)** — short step pointing to the
      **Simplicity/quality gate** section above.
    - **11. Run the security review (conditional)** — short step pointing to the **Security review**
      section above; note it is a hard gate for COMPLEX on sensitive surfaces, recommended for
      MEDIUM.
    - **12. Initialize verification report structure** — old Step 4 body (verbatim).
    - **13. Verify Completeness** — old Step 5 body (verbatim).
    - **14. Verify Correctness** — old Step 6 body (verbatim).
    - **15. Verify Coherence** — old Step 7 body (verbatim).
    - **16. Generate Verification Report** — old Step 8 body (verbatim).
    - **17. Checkpoint verify findings to the change dir** — old Step 9 body (verbatim).
    - **18. Verbally acknowledge documentation persistence** — old Step 10 body (verbatim).
11. **Verification Heuristics / Graceful Degradation / Output Format** — verbatim (old ~356–379),
    including the final PHASE GATE reminder bullet.

**Fidelity check before you finish (a):** the only substantive prose you rewrote is the MANDATORY
preamble (item 3). Every other moved chunk is byte-identical to its source except heading level and
step number. Steps 9–11 are new *pointer* steps that add no new rules — they only sequence sections
that already exist. Confirm no rule/budget/severity/code-block was dropped.

- [x] (a) verify skill restructured per the exact target structure; scaffold_lint clean; suite green.

---

## Sub-scope (b) — fill the golden-source identity (per-repo, non-propagating)

### (b1) `AGENTS.md` line 1

Replace:
```
# <FILL: project name>
```
with:
```
# openspec-scaffold
```

### (b2) `AGENTS.md` `## Project context` section

Keep the existing first paragraph (the pointer to `openspec/config.yaml` `context:`). Replace the
`<FILL: 2-4 sentences …>` block with this exact text:

> This repository **is** the `openspec-scaffold` golden source: it defines the OpenSpec agent
> workflow — the skills, agents, lifecycle, delegation harness, and deterministic audit +
> scaffold-lint tooling — and propagates it to downstream project repos (currently `extrends` and
> `psc-monitor`) via `scripts/sync_scaffold.py`. Scaffold-managed files are edited **here and only
> here**; downstream repos receive them by sync, never by local edit. Because a change here can
> govern several repos, mistakes propagate — every change runs the full OpenSpec lifecycle at its
> tier, and this repo's own `pytest` suite (including the `scaffold_lint` invariant SEAL) must be
> green before commit.

Replace the `**Hard constraints:** <FILL: …>` line with this exact text (brief statement + pointer,
deliberately NOT restating the full rules that live in dedicated sections below):

> **Hard constraints:** Scaffold-managed files (see `scripts/scaffold_manifest.txt`) are edited
> only in this repo; downstream propagation (`sync_scaffold.py`) and pushes to remotes are
> **operator-gated**. The full discipline is specified under "Scaffold-managed files &
> propagation" and "Working process" below — do not weaken it.

### (b3) `openspec/config.yaml` `context:` block

Fill ONLY the first four fields (Project / Purpose / Tech stack / Testing). **Leave the `Style:`
and `Web research:` lines exactly as they are — they already carry real content; do not touch
them.** Target:

```
context: |
  Project: openspec-scaffold
  Purpose: The golden-source scaffold that defines the OpenSpec agent workflow (skills, agents, lifecycle, delegation harness, deterministic audit + scaffold-lint tooling) and propagates it to downstream project repos (extrends, psc-monitor) via scripts/sync_scaffold.py.
  Tech stack: Python 3.13 standard-library-only scripts (no third-party runtime deps); pytest for tests; markdown skills/agents loaded by both Claude Code and OpenCode.
  Testing: pytest (invoke as `pytest -q`; scripts/test-cmd encodes it); prefer property/invariant tests over output-pinning; 'tests pass' + 'the system ran clean' are the only live-status signals — never record test/doc/row counts in any tracked doc, even as history; only a failing/skipped test is worth a note.
  Style: no inline comments unless the WHY is non-obvious; no docstrings unless public API.
  Web research: always use scripts/fetch_clean.py for article/doc content; WebFetch only for single-fact extraction (full convention: rules.research in this file).
```

- [x] (b) AGENTS.md title + project-context filled; config.yaml context: first four fields filled;
  Style/Web-research lines untouched.

---

## Sub-scope (c) — add `knowledge/reference/exit-codes.md`

Create the file with exactly this content (a source-verified table; the audit family is
deliberately split because `audit_scope`/`index_coverage` never emit 2):

```markdown
# Exit-code conventions — deterministic tooling

Agent-neutral reference for the scaffold's check scripts. Convention: `0` = clean/ran, a
findings/violations code, and `3` = infrastructure failure (where applicable). Verified from
source; if a script changes its codes, update this table.

| Script | Exit codes | Meaning |
|---|---|---|
| `audit_bundle.py` | 0 / 2 / 3 | clean / findings present / infra failure or abort |
| `data_lint.py` | 0 / 2 / 3 | pass (or no checks) / violating rows / infra failure |
| `audit_scope.py` | 0 / 3 | ran clean or tag created / git-or-radon failure (or tag exists). **Never 2** |
| `index_coverage.py` | 0 / 3 | ran (leads are informational, never gate) / infra failure. **Never 2** |
| `knowledge_lint.py` | 0 / 1 | no findings / drift found (1, not 2, to stay distinct from argparse's own exit 2) |
| `scaffold_lint.py` | 0 / 1 | no findings / one+ findings |
| `sync_scaffold.py --check` | 0 / 1 | converged (all identical) / drift (any differs or missing) |
| `sync_scaffold.py --check-refs` | 0 / 1 | no dangling refs / dangling refs found |
| `sync_scaffold.py` (sync mode) | 0 / 1 | synced / preflight validation failure (target missing, no .git, missing scaffold source) |
| `status_lint.py` | 0 / 2 | clean / hard violations |
| `test-gate.sh` | 0 / 2 | allow commit (tests pass, or no/empty test-cmd, or config error) / block commit (tests failed) |
| `_convergence.py` | verdict on **stdout** | prints `CONTINUE` or `STOP:<a\|b\|c>:<detail>`; `main()` always returns 0 — the exit code is NOT the signal |

Notes:
- All Python scripts use `argparse`, so an invalid CLI flag yields argparse's standard exit `2`
  regardless of the script's own convention.
- `_convergence.py`'s header docstring advertises an "exit 1 — no parseable verdict" that the code
  never returns; the unparseable case prints `STOP:c:…` and returns 0. Read the verdict from stdout.
```

- [x] (c) `knowledge/reference/exit-codes.md` created with the exact content above.

---

## Before returning

Run and report the results of BOTH:
- `python3 scripts/scaffold_lint.py` → must print `scaffold-lint: clean`.
- `pytest -q` → must be green (pre-existing skips OK).

Report what you changed per sub-scope. Do NOT commit.
