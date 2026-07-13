# Plan — lifecycle-skill-hardening (SMALL)

## Problem statement

Three defects in the scaffold-managed OpenSpec lifecycle skills surfaced during the OW-2
(`lesson-check-ratchet`) apply→verify→archive session. All three live in skills that propagate to
every downstream repo, so a fix in this golden source benefits every repo on the next sync. Each is
a confirmed, currently-present defect, not a hypothetical:

1. **Propose skill never runs `openspec validate --strict`.** Freeze is gated on zero 🔴 +
   `PREMISE: AGREE` only; no structural validation runs. openspec parses a requirement's `text` as
   its **first physical line only**, so a requirement whose normative `SHALL`/`MUST` is wrapped onto
   line 2 fails `openspec validate --strict` — yet can be frozen and reach apply. OW-2 hit exactly
   this (the frozen `finding-closure-ratchet` delta failed validate; caught only at pre-apply).

2. **Apply skill's non-convergence detection greps the RAW jsonl.** In
   `.claude/skills/openspec-apply-change/SKILL.md` (~lines 172–173) the failure-triage greps
   `/tmp/apply-out.jsonl` (and `/tmp/apply-err.log`) for the literal heading
   `### NON-CONVERGENCE BLOCKER`. The raw jsonl stream includes the executor's own tool-reads of
   `SKILL.md`, which *contains that heading in its documentation* — so a clean run false-positives as
   a "declared blocker" and mis-routes the failure ladder. OW-2 hit this (benign only because tasks
   were verifiably complete).

3. **Archive skill doesn't guard the post-`git mv` broken-citation blocker.** Step 6's "Lint before
   committing" names only `status_lint`. After the change dir is `git mv`'d to `archive/`, any prose
   citation to the old change-dir path breaks `knowledge_lint`'s broken-prose-path-citation check
   (exit 1), which runs in the live-tree pytest gate — so the commit-test-gate **blocks the archive
   commit**. OW-2 hit this (`knowledge/HANDOFF.md` cited the moved dir).

## Proposed approach / fix

Edit only the three lifecycle `SKILL.md` files (no code, no spec deltas — SMALL). Byte-scoped,
additive text changes:

1. **`.claude/skills/openspec-propose/SKILL.md`** — add a structural-validation gate at propose
   completion (the PHASE GATE region, ~line 21, after the last artifact freezes): before declaring
   the change ready for apply, run `openspec validate <name> --strict`; it MUST exit 0. On failure,
   fix the structural error and re-validate before handing off. Include a one-line note naming the
   most common failure: *a requirement whose normative `SHALL`/`MUST` is not on the requirement's
   first physical line — openspec parses requirement text as the first line only.* Do not weaken the
   existing zero-🔴 / `PREMISE: AGREE` freeze conditions; this is an added final gate.

2. **`.claude/skills/openspec-apply-change/SKILL.md`** — fix the non-convergence detection so it
   inspects the executor's **extracted completion report** (`grep '"type":"text"'
   /tmp/apply-out.jsonl | tail -1 | jq -r '.part.text'`, already produced at ~line 155), NOT the raw
   `/tmp/apply-out.jsonl`. Update the `if grep -q "### NON-CONVERGENCE BLOCKER" …` block (~lines
   172–173) to grep the extracted text (keep the `/tmp/apply-err.log` grep as-is — stderr does not
   carry the skill docs). Add a one-line caveat: *grep the extracted completion report, never the raw
   jsonl — the raw stream contains the executor's tool-reads of this SKILL.md, which include the
   `### NON-CONVERGENCE BLOCKER` heading and would false-positive.* Keep the other prose references to
   the heading (they describe the report's content, which is correct).

3. **`.claude/skills/openspec-archive-change/SKILL.md`** — extend Step 6's "Lint before committing"
   bullet: after `status_lint`, also run `scripts/knowledge_lint.py` and, before committing, repoint
   any prose citation to the just-moved change dir to its new `archive/<date>-<name>/` path (the most
   common culprit is `knowledge/HANDOFF.md`, plus any STATUS/decisions/questions line citing the old
   dir). State the why: `knowledge_lint`'s broken-citation check runs in the live-tree pytest gate, so
   an unrepointed citation makes the commit-test-gate block the archive commit.

## Out of scope

- The other four OW-2 lessons — delegation-invocation confirmation and ratchet self-application are
  already in the scaffold; the apply-executor markdown-indent habit and the simplicity-gate
  frozen-code discipline are low-value guidance not worth a change now.
- The frozen OW-3/5/6 batch and every file it touches (`openspec-verify-change/SKILL.md`, `AGENTS.md`
  roles, `_shared/delegation-harness.md`, `scripts/knowledge_lint.py`) — this change edits ONLY the
  propose/apply/archive `SKILL.md` files, so it does not collide with the batch.
- Building a bespoke deterministic check for the first-line gotcha — `openspec validate --strict`
  already detects it; fix #1 only wires the existing validator into the freeze gate.
- Downstream propagation to extrends/psc-monitor — operator-gated, arrives on the next authorized
  `sync_scaffold.py` run (these skills propagate via the normal mechanism).
