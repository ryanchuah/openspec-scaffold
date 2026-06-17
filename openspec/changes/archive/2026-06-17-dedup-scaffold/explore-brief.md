# Explore brief — dedup-scaffold (W2: C1 + B3)

**Source:** `ai-docs/consolidation-plan-2026-06-16.md` (W2) + `ai-docs/workflow-audit-2026-06-16.md`
(§C1, §B3). Scope confirmed by operator 2026-06-17: **C1 + B3 only** (C2 rule-restatements and
C4 executor-body guard deferred).

## The problem (verified against disk 2026-06-17, current line numbers)

The `opencode run` delegation harness is copy-pasted across all four delegating skills and is
**already drifting**. Confirmed anchors:

| Element | apply | verify | propose | archive |
|---|---|---|---|---|
| hardened invocation (`< /dev/null` + `--dir <repoRoot>`) | `:92,:97,:108` | `:27,:60,:67,:72` | `:109,:113,:121` | `:132,:137,:151` |
| "assert real agent ran" (grep `Falling back to default agent`, extract `part.text`) | `:153,:158` (full) | `:88` (abbreviated) | `:143,:148` (full) | `:167,:171` (full) |
| bounded wait + surgical kill / never `pkill opencode` | `:120,:124` | `:27` (inline) | `:127,:135` | `:156,:160` |
| EXIT-sentinel completion detection | present | `:62,:69` (`echo "EXIT=$?"`) | — | — |
| timeout budget (B3) | `-k 30 600` | `-k 15 300` (fix) / `-k 15 780` (verifier) | `-k 15 780` | `-k 30 600` |

**Observed drift (the liability):** kill-grace differs (`-k 30` vs `-k 15`); the assert-ran block is
spelled in full in three skills but abbreviated in verify; the EXIT-file sentinel pattern is only in
apply + verify. A hardening fix to this safety-critical machinery must today be made in four places by
hand with nothing checking they agree.

## The fix pattern (already used in this repo)

`noninteractive-delegation-safety` is an OpenSpec **capability spec** (`openspec/specs/`) that all four
skills already *cite* ("see the `noninteractive-delegation-safety` capability spec for the full
rationale") instead of inlining its rationale. C1 gives the *operational* harness the same treatment:
one referenced doc, each skill cites it + keeps only its per-phase specifics.

## Scope boundaries

- **This is extraction, not redesign.** Behavior must be byte-for-byte preserved; assemble the canonical
  doc from the EXACT existing skill text ([[golden-source-edit-rules]]: established rules only).
- **No spec delta.** The harness extracts to an `ai-docs` doc; the timeout table only cross-references
  the existing `reviewer-budget` spec (reviewer 780s) — no capability spec is modified. → MEDIUM,
  tasks.md only.
- **Genuinely per-phase logic stays inline:** apply's convergence-blocker triage ladder, verify's
  escalate-to-Sonnet path, archive's reconciliation recovery, and each skill's agent/model/budget/prompt.
- **verify's in-process self-review pass** (`:82`) is a Task-tool spawn, NOT `opencode run`, and is
  explicitly NOT subject to the `< /dev/null`/`--dir` hardening — the doc must preserve that carve-out.
- The four `.claude/skills/openspec-{apply,verify,propose,archive}-change/SKILL.md` are scaffold-managed
  (in `scripts/scaffold_manifest.txt`); the new doc joins them so W6 propagates it.
