# notes — lifecycle-gates (W4)

**Tier:** MEDIUM (propose emits `tasks.md` only; acceptance criteria here; one deepseek-v4-pro review
before freeze). **Position:** after W0/W1/W2 (shipped) and concurrent with W3 `fix-convergence-guard`
(disjoint files); before W6 propagation. **Source of record:** `ai-docs/consolidation-plan-2026-06-16.md`
(W4 row) + `ai-docs/workflow-audit-2026-06-16.md` §§E1, B2, D-i, D-ii, E3, C4.

## Scope (folds 6 findings; C4 included per operator)
| Finding | Sev | What | Files |
|---|---|---|---|
| E1 | 🟠 | add tier-scaled simplicity/quality gate to verify | verify SKILL.md, AGENTS.md, spec delta |
| B2 | 🟡 | tier-scale the multi-model verify chain (SMALL reduced) | verify SKILL.md, AGENTS.md, spec delta |
| D-ii | 🟡 | resolve whether SMALL invokes verify skill / phase gate | AGENTS.md Change tiers + Roles |
| E3 | 🟠 | security review for auth/data/external-surface changes | verify SKILL.md, AGENTS.md, spec delta |
| D-i | 🟡 | add RENAMED to both archive-executor bodies | 2 agent files |
| C4 | 🟡 | executor `.claude`/`.opencode` body-agreement guard | new test + manifest (**cuttable §5**) |

## Acceptance criteria (verify behaviorally against these)
1. **Tier-scaled verify (B2/D-ii):** a SMALL change does **not invoke the verify skill at all** (no
   multi-model passes, no verify phase-gate STOP) — it does its own verification per AGENTS.md (optionally
   one flash pass if risky), and AGENTS.md is the single home for that behavior. A MEDIUM/COMPLEX change
   runs the verify skill with the full platform chain (Claude: self→pro→flash; OpenCode: self→flash). The
   verify skill self-documents its MEDIUM/COMPLEX-only applicability and carries **no** SMALL-branch logic
   (avoids the dead-code contradiction). No existing gate/rerun/loop-bound semantics changed.
2. **Simplicity gate (E1):** for MEDIUM/COMPLEX, verify runs a harness-neutral simplicity/duplication/
   dead-code pass on the diff after the verifier passes and before READY; under Claude it invokes
   `simplify`/`/code-review`, under OpenCode a concrete checklist review (see tasks §2.1); it does not block on pure style nits;
   confirmed findings route through the existing defect re-delegation path. SMALL is exempt.
3. **Security gate (E3):** a change touching auth/credentials/persisted-data/external-API surfaces runs a
   harness-neutral security review before READY — hard gate at COMPLEX, recommended at MEDIUM. A change
   touching none of those surfaces does not trigger it.
4. **RENAMED (D-i):** both archive-executor bodies (`.claude` + `.opencode`) instruct the executor to apply
   additions, modifications, removals **and renames** (RENAMED FROM:/TO:), matching the archive skill
   (`:81`) and `openspec-sync-specs`. The two edited lines are byte-identical across the pair.
5. **Body-agreement guard (C4, if kept):** `python3 scripts/test_executor_body_agreement.py` is green and
   FAILS if either executor pair's bodies drift on any non-intro line; the test is listed in
   `scripts/scaffold_manifest.txt`.
6. **Spec delta:** `specs/verify-multimodel-gate/spec.md` carries the MODIFIED pass-chain requirement +
   the two ADDED requirements (simplicity, security), passes the manual validation checklist in tasks §6.1
   (the `openspec validate` CLI does not recognize a proposal-less MEDIUM change), and is the version
   promoted at archive.

## Harness-neutrality note (golden-source rule)
E1/E3 reference Claude-only built-in skills (`simplify`, `code-review`, `security-review`). Every
instruction added MUST be written harness-neutral — name the Claude skill as the Claude path and require an
*equivalent* review under OpenCode — never assume the skill exists for the deepseek/OpenCode side. Source
for these gates is the in-repo audit (`workflow-audit-2026-06-16.md` E1/E3), satisfying
"established rules only" (`golden-source-edit-rules`).

## Operator decisions (resolved 2026-06-17, pre-freeze)
- **Scope:** **C4 INCLUDED** (§5 body-agreement guard stays). W4 covers all 6 findings.
- **Tier:** MEDIUM (propose = tasks.md + notes.md; one pro review). With C4 it is a heavier MEDIUM but
  stays MEDIUM per operator.
- **B2 MEDIUM behavior:** **keep the FULL chain for MEDIUM** (only SMALL is exempted), faithful to the
  audit's "reserve the full chain for MEDIUM/COMPLEX."
- **Autonomy:** operator granted fast-track for this session — proceed propose→apply→verify→archive
  without phase-gate prompts; opencode timeouts raised to 900s.

## Verify outcome (2026-06-17)
1. **Verdict:** READY for archive. Self-review (orchestrator, from disk) + one independent
   `deepseek/deepseek-v4-flash` verifier pass → VERDICT READY, 0 defects. The pro verifier pass was
   skipped per the operator's established W1/W2 lighter pattern for low-risk scaffold instruction changes.
2. **Confirmed by eyeballing real output (behavior, not counts):** both stdlib test suites run green —
   `test_executor_body_agreement.py` (the new C4 guard; its logic strips frontmatter, normalizes the one
   sanctioned intro-clause divergence, and byte-compares each `.claude`/`.opencode` body, so a green run
   means both executor pairs genuinely agree) and `test_sync_scaffold.py` (manifest/byte-sync, reports
   IDENTICAL). Read the edited `SKILL.md`/`AGENTS.md`/delta-spec end to end: the tier guard, simplicity
   gate, and security gate read coherently and harness-neutrally (Claude-skill path + concrete OpenCode
   checklist, never "perform the equivalent review"); the RENAMED clause is byte-identical across the
   archive-executor pair; the delta spec is in canonical `## MODIFIED`/`## ADDED Requirements` form and is
   promotable by the archive-executor.
3. **Defect found and how fixed (who):** surfaced by **self-review** — the delta spec was first authored in
   a NON-canonical format (inline `— MODIFIED`/`— ADDED` suffixes, a `**Change:**` prose note instead of
   full requirement text, and 5 noise `— UNCHANGED` requirements). Left as-is it would risk mis-promotion
   at archive. Diagnosed + scoped, then **re-delegated a format-rewrite to a fresh deepseek-v4-flash
   apply-executor** (not Sonnet); the rewrite is now canonical (2 section headers, 3 requirements full-text,
   0 UNCHANGED, 11 WHEN/THEN scenarios). Re-verified from disk.
4. **As-built delta discovered during verify:** the apply-executor found and fixed **pre-existing drift in
   BOTH `.claude`/`.opencode` executor pairs** to make the new C4 guard pass — apply-executor: bullet
   ordering ("Do not commit" moved up); archive-executor: `**completion report**` bold added to `.claude`
   to match `.opencode`. Pure normalization, no semantic change; this is the first thing the C4 guard caught.
5. **Forward-looking items (for open-questions.md at archive):**
   - **C4 guard coverage is partial.** It checks only the apply-executor + archive-executor pairs.
     `openspec-reviewer` and `openspec-verifier` exist as `.opencode`-only agents (no `.claude` twin), so
     they're out of scope today — if a `.claude` counterpart is ever added, extend the guard to that pair.
   - **The gates reference Claude-only harness skills** (`simplify`/`code-review`/`security-review`) that
     do not live in the scaffold tree; the OpenCode path is the concrete checklist. If those skills are
     renamed/removed harness-side, the Claude path silently degrades — the checklist is the durable floor.
   - **Tier-conditioning now formally exempts SMALL from the verify gate** (optional flash pass only, at
     orchestrator discretion). Monitor that risky SMALL changes aren't under-verified in practice.
   - **Scaffold-only; propagation is W6.** The new `scripts/test_executor_body_agreement.py` + its manifest
     entry join the W6 snapshot to extrends/psc-monitor.

## Still owned by archive
`STATUS.md`, `ai-docs/decisions.md` (record the tier-scaling, the simplicity + security gates, the RENAMED
fix, the C4 body-agreement guard, and the executor-pair drift normalization), `ai-docs/open-questions.md`
(the four forward-looking items above), **spec promotion** of the `verify-multimodel-gate` delta into
`openspec/specs/verify-multimodel-gate/spec.md` (a MODIFIED + 2 ADDED requirements — exercises the very
RENAMED/MODIFIED path this change hardened), and deletion of this change dir into the dated archive.
**⚠️ Commit hygiene:** `ai-docs/open-questions.md` currently carries an UNCOMMITTED foreign edit from the
concurrent **W5** (`cleanup-workflow-ergonomics`) work — it is NOT part of W4 and must be EXCLUDED from the
W4 commit (commit W4 files explicitly, never `git add -A`).
