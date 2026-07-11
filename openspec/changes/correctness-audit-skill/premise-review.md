## Review Round 1 — explore-brief.md (premise review)

### Summary

The brief correctly identifies a real scaffold gap — two downstream repos independently built the same multi-wave LLM correctness-audit protocol with no scaffold ownership. All six named failure modes are well-evidenced by the research dossiers. The root cause (protocol has no scaffold home) is accurate, and the solution direction (scaffold-managed skill standardizing the protocol while leaving product judgment per-repo) directly addresses the root. The dependency on OW-2 is correctly identified as an apply-order constraint, not a propose blocker. The scope boundaries are explicit and reasonable. I find no 🔴 blocking issues — the direction is sound.

Three 🟡 implementation-preparation notes (none are direction faults) and two 💡 suggestions follow.

### 🔴 Blocking Issues

None.

### 🟡 Should Fix

1. **Delegation-harness obligations not acknowledged.** The brief says the skill will "fan out" audit waves, implying `opencode run` delegation, but doesn't acknowledge that `.claude/skills/_shared/delegation-harness.md` governs every such invocation: hardened shape (`< /dev/null`, `--dir`), assert-real-agent-ran, timeout budgets from the sanctioned table (only `-k 30 600` and `-k 15 780` pass `budget-agreement` lint), and EXIT-sentinel completion detection for background launches. If the skill uses a novel timeout pair, it will fail the SEAL. The design will need to resolve this — flagging it now prevents a surprise at `design.md` time. (scaffold-conventions.md §4 documents the full constraints.)

2. **Audit-instrument verification (Wave 0) not addressed.** Both downstream repos had a precursor phase that hardened the audit's own instruments before any finding work (scratch-DB tooling, deterministic baseline, invariant "ruler" verification). The brief's ground rules mention "narrow fix-now for audit instruments" in passing but the solution direction doesn't specify whether the skill itself has a self-verification step. The census/dossier lint covers deterministic output checks, but an LLM-driven audit has a trustworthiness problem the refuter-overrule rule only partially addresses — what checks that the probes are probing the right things? This is implementation detail for `design.md`, not a direction fault, but leaving it unmentioned risks a gap in the design.

3. **Per-repo wiring discovery not covered.** The `run-audit` skill has a "wiring-detection branch" that checks whether per-repo config exists and gives inline guidance rather than auto-provisioning (scaffold-conventions.md §7). The brief says the census is "skeleton seedable from the existing `facts.py` inventory fact" and mentions "detect-and-explain, per run-audit precedent" in the Out of Scope section, but the "per-repo (deliberately not standardized)" items — severity taxonomy, wave decomposition, verification-method map, census content — all need to *exist* before a wave can run. How the skill discovers or guides the operator to create them is an open design question the brief doesn't flag. Again, a `design.md` concern, not a direction fault.

### 💡 Suggestions

1. **Model routing policy could be more explicit.** The brief's ground rules bullet says "model routing (judgment → pro-tier, mechanical → flash)" but the solution direction section doesn't say whether the skill *enforces* this routing or leaves it as guidance. Both downstream repos converged on the same routing rule independently (psc-audit-method.md §2, extrends-audit-method.md §2), so standardizing it in the scaffold-owned protocol would be consistent with the brief's own premise. Consider stating it explicitly in the scaffold-owned section.

2. **Consider noting the `_NON_OPENSPEC_SKILL_TOKENS` scaffold_lint edit.** Per scaffold-conventions.md §2, a new non-`openspec-`-prefixed skill that gets cross-referenced in scaffold-managed docs may need a `scripts/scaffold_lint.py` edit to add `correctness-audit` to `_NON_OPENSPEC_SKILL_TOKENS`. The brief doesn't mention this — the dir-name fallback likely makes it non-essential, but noting it in the design would save a round-trip.

### Premise Verdict

**PREMISE: AGREE**

The problem is real and well-evidenced. The root cause (protocol with no scaffold home) genuinely explains why both repos hand-rolled the same pattern. The solution direction (scaffold-managed skill + templates + lint, per-repo product judgment) targets the root, not a symptom. Scope is appropriately bounded with explicit out-of-scope items. The six named failure modes each map to a named mechanism in the proposed skill (Prior: field → dedup, Class: slug → defect-class naming, refuter-overrule → unreliable refuters, census → stopping rule, ratchet routing → closure enforcement and output visibility). Dependencies are correctly sequenced (OW-2 apply-order, no OW-3 dependency). The brief is well-calibrated for explore altitude — it captures enough direction to proceed to design without over-specifying implementation.

- D11 (explore-altitude): under-specification is expected — the three 🟡 items above are implementation gaps to resolve at `design.md`, not direction defects.
- D10 (drift): not applicable — this is the first artifact; the brief correctly derives from the scaffold gap analysis's `OUTSTANDING-WORK.md` OW-5 entry without reframing the problem, switching to a ruled-out approach, or expanding scope beyond what was vetted.

### Verdict

**PASS** — ready to freeze and move to `design.md`. No 🔴 blocking issues.
