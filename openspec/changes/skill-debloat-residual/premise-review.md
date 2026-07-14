# Premise review — skill-debloat-residual (direction gate)

Reviewer: `openspec-reviewer` (deepseek/deepseek-v4-pro), 2026-07-14. Full text: `premise-review-full.md`.

### Premise Verdict

PREMISE: AGREE
- None — the four problems are correctly identified as instances of a single root cause
  (prose-as-enforcement is unreliable); the proposed solutions replace fuzzy prose with
  deterministic mechanisms; scope is well-framed with explicit out-of-scope items.

Severity verdict: **PASS**, zero 🔴.

### Design-time guidance carried into design.md (from the reviewer's 🟡/💡)

- **🟡-1 (fold): verify de-bloat needs NO spec delta.** `verify-multimodel-gate` governs the
  multi-model passes, NOT the artifact/spec-mapping checklist (verify steps 12–16), which lives in
  skill prose and was never spec-gated. The de-bloat is a skill-prose change. Net spec deltas for
  this change: ADDED notes-checkpoint detector in `defect-prevention-detectors`; MODIFIED freeze
  requirement in `premise-review-gate`. (Confirm at design whether the notes-checkpoint verify-time
  enforcement wording touches `verify-multimodel-gate` — expected: no.)
- **🟡-2 (fold, highest-risk): don't reintroduce fragile requirement↔task keyword-matching.** There
  is no reliable mechanical key between a delta `### Requirement:` and a free-text `tasks.md`
  checkbox. Design the coverage step as: DETERMINISTIC = enumerate requirements/scenarios from the
  delta (grep) + confirm all task checkboxes `[x]` + run `spec-delta-structure`; JUDGMENT = a short
  **coherence note** where the orchestrator maps each enumerated requirement to the behavioral
  evidence gathered in steps 4–8 and flags any unexercised requirement as a gap. The CRITICAL trigger
  is a requirement left unaddressed by the coherence note, NOT "keyword not found."
- **💡-1 (fold): name the reviewer agent file.** Item 3's FREEZE-token contract edits
  `.opencode/agents/openspec-reviewer.md` (reviewer output contract) + the propose skill's
  reviewer-invocation prompt. Add to scope explicitly.
- **💡-2 (fold): commit L5 (checks.py cwd litter) at proposal time**, not design-gated — but confirm
  in design that no caller reads `./<name>.json` from cwd before changing the `--check` output dir.

Direction settled. Advancing to propose.
