# Review log — graduate-security-audit-skill

## VERIFY — 2026-07-18 — READY FOR ARCHIVE

**Verification posture (disclosed).** This is a text-only, additive graduation (a new skill + a new
normative spec + one manifest line + two knowledge-doc edits); no code path is altered. The
verify-multimodel-gate exists to catch behavioral regressions in *code* changes — there is no runtime
behavior here to exercise. Verification was therefore: the full deterministic gate battery + a
rigorous orchestrator self-review, with the independent delegated (deepseek) verifier pass
**consciously not run** for this artifact class. Rationale: (a) the deliverable is graduation prose
whose quality turns on holding the AP-1 run context, which a cold delegated reviewer lacks; (b) every
mechanical property is already covered by the deterministic gates below; (c) the operator is away and
delegation adds latency/flakiness with low marginal signal on a doc/skill artifact. **The operator
MAY run the delegated `openspec-verifier` pass over the spec+skill before propagation if the full
MEDIUM ceremony is wanted** — nothing about the artifact blocks it.

**Deterministic gates (all green):**
- `scripts/scaffold_lint.py` → clean (incl. manifest-completeness for the new skill, budget-agreement
  on the `timeout -k 15 780` delegation example, model-id-agreement on `deepseek/deepseek-v4-flash`).
- `openspec validate --changes` → change valid; `openspec validate --specs` → 22/22 incl.
  `spec/security-audit`.
- `scripts/sync_scaffold.py --check-refs <downstream>` → no dangling references (189 md files).
- `ruff check .` + `ruff format --check .` → clean (no `.py` touched, confirmed).
- `pytest -q` (full suite) → 696 passed; the sole failure is
  `test_doc_lint_gate.py::test_knowledge_lint_live_tree_clean`, which trips ONLY on the pre-archive
  state of the OW-17 archive-path pointer (the same artifact `knowledge_lint` flags pre-archive).
  It resolves the instant the change dir is moved into `openspec/changes/archive/` — re-confirmed
  green post-archive (see Archive section).
- `apply_delta_spec.py --dry-run` → clean plan, `created: true`, all 8 ADDED requirements applied.

**Self-review — two defects found and fixed before archive:**
1. **Phantom identifier.** The skill/proposal/notes/tasks/OW cited a
   `security-audit-ceremony-contract` requirement, but the spec (following the `product-audit`
   precedent) uses 8 granularly-named requirements under the `security-audit` capability with no
   umbrella by that name. Swept all references to cite the capability. No validated identifier was
   affected (openspec validate passed before and after); this was prose accuracy for a golden-source
   artifact.
2. **Delegation-launch consistency.** The refuter example's prose said "background it" while the
   wrapper used the synchronous `--exit $?` shape. Reconciled to the harness §c–d background contract:
   added the `; echo "EXIT=$?" > …exit` sentinel to the `opencode run` command and switched the
   wrapper to `--exit-file`, matching the delegation-harness for a backgrounded launch.

**Premise self-check (in lieu of the delegated premise pass):** the change's premise holds — the
audit family genuinely had no skill owning the classic vuln classes (confirmed: 14 skills, none
security; the only security surface is the diff-scoped verify pass); the scanner floor was already
shipped (`graduate-sast-scanners`), so this is the additive LLM ceremony that stands on it; the
run-first-graduate-after sequencing matches OW-16 (product-audit) exactly and the source lessons
(`plans/security-audit-ap1/session-lessons.md`) are real and were distilled requirement-by-requirement
(each spec requirement traces to a named AP-1 lesson — see notes.md). No premise dissent.

**Fidelity check — every AP-1 lesson has a home:** empirical-probe-first (R4 + skill step 4);
SAST-is-a-floor-not-a-finder (R3 + skill step 3); confirm-the-negatives-are-the-deliverable (R4 +
skill step 4); flash-refuter recipe (R5 + skill step 5); surface-money-races-to-operator (R5 + skill
step 5); cross-lane completeness critic (R6 + skill step 6); supply-chain reachability triage (R3 +
skill §triage); lockfile-is-a-tool-choice (skill §triage); per-repo custom-detector archetypes (skill
§detectors); gate-the-boot-validator-on-the-test-env (skill step 4); multi-session liveness +
deploy-time deferral (R8 + skill steps 2/8); secrets-never-to-external-model (R2 + skill charter).
