# tasks — lifecycle-gates (W4)

MEDIUM tier. Apply-phase implementation work only (no verify/archive checkboxes). Acceptance
criteria live in `notes.md`. Folds audit findings **E1** (simplicity/quality gate), **B2 + D-ii**
(tier-scale verify; resolve verify-vs-SMALL), **E3** (security gate), **D-i** (RENAMED in
archive-executor bodies), and **C4** (executor body-agreement guard — *scope-cut candidate*, §5).

Behavior change is intentional and confined to the verify gate + Change-tiers prose + two agent
bodies + one new guard test. No `_convergence.py` / `test-gate.sh` edits (that is W3
`fix-convergence-guard` — disjoint).

---

## 1. Tier-scale the verify gate (B2) + resolve verify-vs-SMALL (D-ii)

Source: audit §B2 (`workflow-audit-2026-06-16.md`), §D-ii. The verify multi-model passes branch
**only on platform** (`openspec-verify-change/SKILL.md:40-43`; `AGENTS.md:89-101`), never on tier, so
the full self→pro→flash chain (two 780s `opencode run` invocations) fires even for a one-line change.
Minimal, faithful fix: **SMALL is exempted/reduced; MEDIUM and COMPLEX keep the full platform chain.**

- [x] **1.1** In `.claude/skills/openspec-verify-change/SKILL.md`, add a **tier-applicability guard** at
      the top of the `### Multi-model passes (independent verification gates)` section (exact heading,
      currently at line ~36): state that **this skill and its multi-model passes apply to MEDIUM and
      COMPLEX changes only.** A SMALL change does its own verification per `AGENTS.md` and does **not**
      invoke this skill, its multi-model passes, or the verify phase-gate. Do **NOT** add any SMALL-branch
      pass logic inside the skill — SMALL never reaches this file, so a SMALL branch here would be dead
      code (the contradiction the reviewer flagged). The existing platform pass chain (Claude: self → pro →
      flash; OpenCode: self → flash) stays exactly as-is for MEDIUM/COMPLEX; only the new
      tier-applicability sentence is added, and all gate/rerun/loop-bound semantics stay verbatim.
- [x] **1.2** In `AGENTS.md` **"Change tiers"** (lines ~129-147) and the verifier **"Roles"** bullet
      (lines ~89-101), state explicitly which tiers invoke the verify skill and its gate. **AGENTS.md is
      the single home for SMALL verify behavior** (per 1.1 the skill carries none):
      - SMALL **does not invoke the verify skill**; it does its own verification per the SMALL bullet, is
        **not** subject to the multi-model passes or the verify phase-gate STOP, and MAY run a single
        `deepseek/deepseek-v4-flash` verifier pass if the orchestrator judges the change risky.
      - MEDIUM and COMPLEX **run the verify skill**, including its full multi-model passes and the
        phase-gate STOP-after-verify.
      This is the D-ii resolution. Reword the verifier Roles bullet so the "self → pro → flash" chain is
      described as the **MEDIUM/COMPLEX** chain, not unconditional.

## 2. Add the simplicity / quality gate to verify (E1)

Source: audit §E1 (🟠). There is **no** simplicity/quality gate anywhere — `simplify` / `code-review`
are referenced nowhere in the workflow (grep-confirmed: only the audit docs mention them). The implementer
is deepseek-flash (most prone to over-built output), and verify's Coherence dimension explicitly says
"don't nitpick style" (`SKILL.md:323`), so over-engineering/duplication/dead-code flows through ungated.

- [x] **2.1** In `.claude/skills/openspec-verify-change/SKILL.md`, add a **simplicity/quality pass** step
      in the `### Multi-model passes (independent verification gates)` section (exact heading), positioned
      **after** the verifier passes return READY and **before** the artifact/spec mapping checklist + final
      READY verdict. Runs for MEDIUM/COMPLEX (the skill is MEDIUM/COMPLEX-only per §1). Make it
      **harness-neutral**:
      - **Under Claude Code:** the orchestrator runs the `simplify` (or `/code-review`) skill on the change's
        `git diff` and folds confirmed findings into the defect path.
      - **Under OpenCode (no such skill exists):** the orchestrator itself reviews the `git diff` against
        this concrete checklist — (a) code duplicating functionality that already exists elsewhere in the
        repo; (b) abstractions introduced but used only once; (c) dead or unreachable code paths;
        (d) over-parameterization/config beyond the change's actual scope. **This checklist IS the OpenCode
        instruction — do NOT write "perform the equivalent review" as the prose** (that gives the executor
        nothing concrete to transcribe).
      Findings are leads to confirm from disk (same discipline as verifier findings); a confirmed
      simplification defect uses the existing defect re-delegation path. The gate does **not** block on pure
      style nits — it targets over-engineering, duplication, and dead code.
- [x] **2.2** Update the `AGENTS.md` "After reading this file" acknowledgement (item 2, lines ~244-246) and
      the workflow step 4 (line ~111) so "verify" names the simplicity/quality pass alongside the multi-model
      passes. Keep it one clause — do not bloat the section.

## 3. Security-review gate for sensitive-surface changes (E3)

Source: audit §E3 (🟠). No lifecycle step considers security; `security-review` is referenced nowhere.
Downstream repos (extrends/psc-monitor) handle real data, Postgres, external APIs, credentials.

- [x] **3.1** In `.claude/skills/openspec-verify-change/SKILL.md`, add a **conditional security pass**: when
      the change touches **auth, credentials/secrets, persisted data, or an external API/network surface**,
      the orchestrator runs a security review before declaring READY. Harness-neutral:
      - **Under Claude Code:** invoke the `security-review` skill on the diff.
      - **Under OpenCode (no such skill exists):** the orchestrator itself reviews the diff against this
        concrete checklist — authn/authz bypass or missing authorization on new endpoints/queries;
        credential/secret leakage (logged, returned in a response, or committed); unsanitized external/user
        input reaching SQL, shell, or file paths (injection); unsafe deserialization; missing
        input-confirmation guard on a destructive operation. **This checklist IS the OpenCode instruction —
        not "perform an equivalent review".**
      It is a **hard gate for COMPLEX** changes on those surfaces and a **recommended** pass for
      MEDIUM changes on those surfaces. Confirmed findings use the existing defect re-delegation path.
- [x] **3.2** In `AGENTS.md` "Change tiers", add one line: a COMPLEX change touching auth/data/external
      surfaces SHALL run the security pass at verify (see the verify skill). Keep it to a single sentence.

## 4. Add RENAMED to the archive-executor bodies (D-i)

Source: audit §D-i (🟡). The archive **skill** assesses renames
(`openspec-archive-change/SKILL.md:81`) and `openspec-sync-specs` handles RENAMED (`:45,74,111`,
FROM:/TO: format), but **both archive-executor agent bodies** that perform the delegated sync say only
"Apply additions, modifications, and **removals**" (`.opencode/agents/archive-executor.md:48`,
`.claude/agents/archive-executor.md:35`) — a RENAMEd requirement synced via archive can be silently dropped.

- [x] **4.1** In **both** `.opencode/agents/archive-executor.md` and `.claude/agents/archive-executor.md`,
      step 2 ("Sync delta specs"), change "Apply additions, modifications, and removals to the main spec"
      to include **renames** (e.g. "additions, modifications, removals, **and renames** (RENAMED, FROM:/TO:
      format — see `openspec-sync-specs`)"). Keep the two bodies' wording identical for this line so §5's
      guard (if kept) stays green. Make the **same** edit to both files.

## 5. Executor body-agreement guard (C4) — SCOPE-CUT CANDIDATE

Source: audit §C4 (🟡), batched here from W2. `apply-executor` and `archive-executor` each exist as a
`.claude/` + `.opencode/` pair whose **bodies** are near-identical and hand-synced (lengths:
apply 83/93, archive 77/88 lines; only the intro line legitimately differs — ".../the Claude Code
counterpart of the OpenCode `@<agent>`"). Nothing checks the prose halves agree. The
verify-multimodel-gate decision (D3, `ai-docs/decisions.md:134`) explicitly rejected a second file
*because* of "duplicated body prompt that must be kept in sync" — yet apply/archive carry exactly that.

> **Cut this section if the operator scopes W4 to the gates only.** It is the most mechanism-heavy item
> and the least thematically "lifecycle-gate"; deferring it to W5/standalone is clean (delete §5 + its
> notes.md acceptance row; nothing else depends on it).

- [x] **5.1** Add `scripts/test_executor_body_agreement.py` (stdlib `unittest`, run with `python3` — the
      scaffold has no `.venv`; match `scripts/test_sync_scaffold.py`). For each executor pair
      (`apply-executor`, `archive-executor`): strip YAML frontmatter, then assert the post-frontmatter
      bodies agree on their shared content — normalize away the one sanctioned divergence (the intro
      sentence's "(the Claude Code counterpart of the OpenCode `@…`)" clause) and assert the remainder is
      byte-identical. The test FAILS when the two bodies drift on any non-intro line. **Remediation if a
      pair fails:** the apply-executor pair should already agree today, but if either pair (apply or
      archive) fails, diagnose and fix the drift so both bodies agree beyond the sanctioned intro sentence,
      applying the same minimal-edit discipline as §4.1 — do not weaken the test to pass.
- [x] **5.2** Add `scripts/test_executor_body_agreement.py` to `scripts/scaffold_manifest.txt` so it
      propagates at W6 and is itself sync-managed. (Manifest-changing → must land before W6; W4 is before W6.)
- [x] **5.3** Run `python3 scripts/test_executor_body_agreement.py` **after §4.1's edits are complete** and
      confirm green.

## 6. Author the delta spec for verify-multimodel-gate

The change modifies the verify gate's contract, so it carries a delta spec (promoted at archive).

- [x] **6.1** Author `openspec/changes/lifecycle-gates/specs/verify-multimodel-gate/spec.md` as an OpenSpec
      delta:
      - **MODIFIED** the "Verify runs independent multi-model passes after the self-review" requirement so the
        passes are **tier-conditioned**: they apply to **MEDIUM/COMPLEX** only; a SMALL change does its own
        verification (per AGENTS.md, optionally one flash pass) and does not run them. **Update the existing
        platform scenarios** (`Claude Code orchestrator runs three passes`, `OpenCode orchestrator runs the
        flash pass only`) to add the MEDIUM/COMPLEX qualifier — e.g. rename the first to "A MEDIUM/COMPLEX
        Claude Code change runs three passes" — and **add** `#### Scenario: A SMALL change runs self-review
        only (with an optional flash pass)` whose body notes the optional single flash pass for risky
        changes. (Leaving the platform scenarios unconditional would contradict the tier-conditioned requirement.)
      - **ADDED** a requirement "Verify runs a simplicity/quality gate (MEDIUM/COMPLEX)" (E1): a
        harness-neutral simplicity/duplication/dead-code review of the diff after the verifier passes and
        before READY; SMALL exempt. One scenario for the Claude path (invokes `simplify`/`code-review`) and
        one for the OpenCode path (the concrete (a)-(d) checklist from §2.1).
      - **ADDED** a requirement "Verify runs a security review for sensitive-surface changes" (E3): a change
        touching auth/credentials/data/external surfaces runs a harness-neutral security review before READY
        (hard gate at COMPLEX, recommended at MEDIUM). Two scenarios (Claude path invokes `security-review`;
        OpenCode path uses the §3.1 checklist), or one scenario whose body explicitly covers both platform branches.
      - **Validate the delta manually** — `openspec validate <change>` does NOT recognize a proposal-less
        MEDIUM change (confirmed: it returns "Unknown item 'lifecycle-gates'"), so do not rely on the CLI.
        Checklist: every requirement carries an ADDED/MODIFIED marker; the MODIFIED requirement's scenarios
        all gained tier qualifiers and the new SMALL scenario is present; each ADDED requirement has ≥1
        `#### Scenario:`; every scenario has WHEN/THEN (AND optional) structure.

---

### Out of scope (do NOT touch — belongs to other W's)
- `scripts/_convergence.py`, `scripts/test-gate.sh` — W3 `fix-convergence-guard` (concurrent).
- apply/verify **happy-path-first** restructure (B1), spec-header normalize (D-iii), rollback branch (E4),
  version-pin smoke (E5) — W5 cleanup.
- Cross-repo propagation to extrends/psc-monitor — W6 snapshot.
