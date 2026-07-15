# Notes — knowledge-lint-gitignored-citation-exempt (SMALL)

## Operator routing
- **Apply pre-routed to Sonnet-first** (AGENTS.md "operator MAY pre-route a specific change's
  apply to Sonnet-first"): operator instruction this session was "do the urgent fix now" +
  "use haiku/sonnet subagents where possible." deepseek/opencode also crashed twice on the
  immediately prior archive run, so Sonnet-first avoids known-flaky delegation for a 2-file fix.
- **SMALL premise pass:** satisfied by orchestrator direction-review + an independent Sonnet
  behavioral/premise review pass (substituted for the deepseek-flash opencode premise call given
  the operator urgency and deepseek instability above). Premise is a trivial generalization of an
  already-shipped, already-documented exemption (`output/` → any gitignored target), so direction
  risk is minimal. Verdict recorded below after the review.

## Assumptions
- `deploy/rendered/` is gitignored in psc-monitor (confirmed by the prior agent's report: the dir
  "will vanish again on the next git clean -x"). The scaffold fix keys on git's own ignore set,
  so no assumption about the specific path is baked into scaffold code.

## Verdicts
- Independent Sonnet review (read-only, separate context): **PREMISE: AGREE** (narrow, correct
  generalization; tracked-path drift still flags) + **BEHAVIORAL: CONFIRMED** (guard order/target
  correct, threading correct, git-unavailable `output/` fallback intact, new test git-inits so it
  genuinely exercises the guard, no suppression path for tracked missing files). No defects.
- Orchestrator verify: `scripts/check.sh` green (ruff check + format clean; full pytest suite green,
  including `scaffold_lint` and the live-tree `test_doc_lint_gate`). New test genuinely fails without
  the guard (deploy/ is a real top-level dir → citation would resolve-check → flag). Done.
