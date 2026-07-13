# notes — lifecycle-skill-hardening (SMALL)

## 2026-07-13 — Opus orchestrating; deepseek-flash apply

**Origin:** three defects observed during the OW-2 (`lesson-check-ratchet`) session; operator chose
"harden scaffold now" (a SMALL change) before resuming the frozen OW-3→5→6 batch.

**Premise pass:** flash reviewer, `PREMISE: AGREE`, PASS, zero 🔴 (all three defects independently
confirmed against the skill files). Verdict in `premise-review.md`. Two non-blocking notes folded
into the apply brief.

**Apply:** deepseek-v4-flash, one clean pass, no fallback. Edited ONLY the three lifecycle
`SKILL.md` files (propose/apply/archive). No code, no spec deltas.

**Verify (SMALL: own review + single flash verifier pass — NOT the verify skill):**
- Own review: all three edits correct and well-placed. Fix #1 (`openspec validate --strict` gate) is
  step `f`, after the loop-termination step `d`, so it runs once after all artifacts freeze.
- **Real-output proof of fix #2:** ran both the old and new detection logic against OW-2's actual
  apply jsonl (`/tmp/apply-out.jsonl`, which had false-positived): OLD raw-jsonl grep → MATCH
  (reproduces the bug); NEW extracted-report grep → no match (correct). The fix eliminates the
  false-positive on the exact input that triggered it.
- Green gate (`scripts/check.sh`) green. Single flash verifier pass: `VERDICT: READY`, no defects.
- No defects found; no re-delegation; no Sonnet.

**As-built:** matches the plan. Minor cosmetic: step `f`'s content indent (7 spaces) matches step
`d`; step `e` uses 6 — a pre-existing inconsistency in the file, not introduced here, left as-is.

**Decision essence (for decisions/INDEX.md):** wire the existing `openspec validate --strict` into
the propose freeze gate (mechanism over a bespoke check, since validate already detects the
first-line-parse class); retarget the apply non-convergence grep to the extracted completion report
(the raw jsonl carries the executor's tool-reads of the skill heading → false-positive); add
`knowledge_lint` + moved-dir citation repointing to the archive pre-commit lint (its broken-citation
check runs in the live-tree gate and would block the archive commit).

**STATUS reconciliation note:** this is a scaffold-process hardening (SMALL) — record it as a
"SHIPPED" sub-note under `## Immediate next action` (like the fix-propagation-tooling-drift
precedent), NOT a new `## Latest change` section, to preserve the ≤3-cap for feature changes. Do
NOT touch `knowledge/HANDOFF.md` (the primary owns it — it will update the now-shipped lessons).
Next work is unchanged: OW-3 → OW-5 → OW-6.
