# notes — verify-adversarial-fixtures (MEDIUM)

## Problem
The verify step's self-review (verify skill Steps 4–8; canonical rule `openspec/config.yaml`
`rules.verify`) re-runs the **apply-executor's** test suite and already states "green is necessary
but NOT sufficient" — but gives no actionable teeth for the failure class that a green suite hides.
A real defect has already survived exactly this: the `spec-delta-structure` detector (OW-11) shipped
with a false-negative on multi-section (ADDED+MODIFIED) deltas while its executor-written tests
(single-section only) all passed green; only orchestrator-authored multi-section fixtures caught it.
That instance is closed by ratchet `detector-statemachine-boundary-flush` (a single pinned regression
test), but the **general** lesson — *at verify, the orchestrator authors its own adversarial/boundary
fixtures rather than trusting the executor's green suite* — is recorded nowhere durable: only in the
ephemeral `knowledge/HANDOFF.md` (deleted once wave-2 ships) and that one instance-scoped ratchet
entry. This change promotes the general rule into the scaffold's verify surface.

## Source-traceability (lessons.md §2.1 — "established rules only")
The rule is NOT invented: it is the actionable extension of `config.yaml rules.verify` step (2)'s
existing "green is necessary but NOT sufficient" clause, sourced from the validated real-world lesson
`detector-statemachine-boundary-flush` (`knowledge/ratchet-log.md`) and its carried-forward statement
in `knowledge/HANDOFF.md`.

## Design decision — placement (canonical home + operational cite, NO spec delta)
Per the lessons.md §2 single-source registry, a workflow rule gets ONE canonical home; every other
site keeps per-context specifics + a citation and never re-expands the rule text.
- **Canonical home:** `openspec/config.yaml` `rules.verify` step (2). It already owns the self-review
  methodology and the "green not sufficient" clause; it is prompt-injected and propagated downstream
  (the `rules:` block auto-syncs). The one-clause extension lands here.
- **Operational site:** `.claude/skills/openspec-verify-change/SKILL.md` — a new subsection carrying
  the concrete fixture-construction heuristics + the war-story + the distinction from the test-quality
  lens, plus a Step 5 pointer. It **cites** the canonical rule; it does not restate it.
- **No spec delta.** The self-review's *content* is governed by `config.yaml rules.verify` + the skill,
  NOT by the `verify-multimodel-gate` capability (which scopes itself to the *multi-model passes* and
  only *references* the self-review as "pass 1"). Adding a self-review requirement to that spec would
  mismatch its stated Purpose and duplicate the canonical rule — a single-source violation. This is
  the principled divergence from skill-debloat-gates' precedent (that change touched the spec's *own*
  domain — pass concurrency; this one touches the self-review, a different domain).

## Scope
IN: (1) one clause appended to `config.yaml rules.verify` step (2); (2) one new subsection +
one Step 5 pointer in the verify skill.
OUT (explicit):
- No `verify-multimodel-gate` (or any) spec delta — see placement rationale.
- No deterministic check/detector — the ratchet entry already established this is semantic
  ("can't statically prove every boundary flushes"); it is inherently a methodology rule.
- No new tests — no code changes; the specific-instance regression test already exists
  (`test_checks.py::test_multisection_added_requirement_no_scenario_flagged`).
- No edit to `AGENTS.md` (it references the behavioral review generically; it is "stable") or to
  `knowledge/lessons.md` §2 registry (archive-time reconciliation may add a `rules.verify` row — see
  forward-looking below; not apply-phase work).
- No downstream propagation (operator-gated + deferred, like all recent scaffold changes).

## Acceptance criteria (verified behaviorally at verify)
1. `config.yaml rules.verify` step (2) carries the adversarial/boundary-fixture obligation, scoped to
   logic-bearing diffs (parser / state machine / detector / validator / branch-taking transform), with
   the concrete boundary + should/should-not-trip heuristic, source-traceable to the "green not
   sufficient" clause.
2. The verify skill has a new subsection "Adversarial / boundary fixtures (self-review core)" with:
   the single-source **cite** to `config.yaml rules.verify` (NOT a re-expansion), the
   `detector-statemachine-boundary-flush` war-story, the per-code-type heuristics, the explicit
   distinction from the test-quality lens, and the pure-prose exemption.
3. The verify skill Step 5 points to that subsection (short directive, not a duplicate of it).
4. Single-source discipline holds: the rule statement is not re-expanded at two sites; the skill cites.
5. `bash scripts/check.sh` exits 0 (ruff + format + pytest) and `scaffold_lint` is clean (no new
   citation / model-id / budget findings from the edits).
6. The obligation correctly EXEMPTS pure-prose/config changes — including this very change, whose own
   diff carries no decision logic (nice dogfood: at verify, record "no decision logic → obligation N/A").

## Assumptions (non-blocking; recorded per AGENTS.md batch-ambiguity rule)
- A1: Appending the obligation to step (2) (rather than inserting a renumbered new point) is preferred
  — it keeps the rule attached to the "green not sufficient" clause it extends and avoids renumbering
  config's (1)-(4) points. Default chosen; low-risk.
- A2: The skill subsection is placed immediately before "### Multi-model passes" (self-review guidance
  precedes delegated-pass guidance). Default chosen; cosmetic.

## Forward-looking (for archive reconciliation — notes.md field 5 seed)
- Consider adding a `rules.verify` row to the `knowledge/lessons.md` §2 single-source registry (its
  canonical home is now load-bearing for two rules — the self-review steps and this obligation). Archive
  judgment call; low priority.
- The general lesson is now durable in `config.yaml`/skill; the narrow ratchet entry
  `detector-statemachine-boundary-flush` remains valid as the specific-instance disposition.
- Downstream propagation of the `rules:` block + verify skill is operator-gated and deferred.

---

## Verify checkpoint (2026-07-14)

1. **Verdict:** READY FOR ARCHIVE. Self-review PASS → pro behavioral verifier pass (deepseek-v4-pro)
   VERDICT: READY, zero defects. `bash scripts/check.sh` green (my own re-run). Simplicity gate:
   assessed clean (no code; the only mappable concern — rule duplication across sites — was designed
   against and the pro pass confirmed the skill "does not restate" the config rule). Security/data-path
   gates: N/A (no auth/creds/persisted-data/external-API/data-path surface).

2. **Eyeballed live output (behavior, not counts):** YAML-parsed `openspec/config.yaml` and rendered
   `rules.verify[0]` — the `>-` folded scalar's continuation lines fold to clean spaces with NO broken
   or concatenated words at any fold point ("single blind source", "OWN adversarial/boundary fixtures",
   "the executor's", "a real defect", "boundary fixtures"), and step (2) flows correctly into
   "(3) eyeball the real output…". In the verify skill, the new `### Adversarial / boundary fixtures
   (self-review core)` subsection renders coherently and Step 5's pointer resolves to that exact heading
   (no dead cross-reference). The pro verifier independently traced every fold point to the same result.

3. **Defect found and how fixed:** NONE (no code defect from any pass). One process hiccup: the pro
   verifier's FIRST pass did the real review but emitted a terse prose summary instead of the required
   `## Verify Pass / VERDICT:` block; the wrapper's marker assertion caught it (marker-missing), and a
   single re-run with a strict output-contract prompt returned the proper `VERDICT: READY` block. No
   Sonnet fallback used anywhere this change.

4. **As-built delta discovered during verify:** NONE — the three edits match `tasks.md`/`notes.md`
   exactly (config clause authored multi-line-folded per review 🟡#1; skill subsection + Step 5 pointer
   verbatim). No spec delta exists or was promoted.

5. **Forward-looking (fold into project docs at archive):**
   - **Dogfood confirmation (nice-to-record):** this change's own diff carries NO decision logic, so its
     new adversarial-fixture obligation was correctly assessed N/A — the pure-prose exemption path works
     as designed on its very first application.
   - Consider adding a `rules.verify` row to the `knowledge/lessons.md` §2 single-source registry — its
     canonical home now governs two rules (the self-review steps + this obligation). Archive judgment
     call; low priority (park under questions/INDEX.md if not done inline).
   - The general lesson (a generalization of ratchet `detector-statemachine-boundary-flush`) is now
     durable in `config.yaml rules.verify` + the verify skill; the narrow ratchet entry remains valid as
     the specific-instance disposition (no ratchet edit needed — this is a proactive hardening, not a new
     finding to close).
   - **Monitored follow-on (non-blocking):** the openspec-verifier occasionally emits a terse summary
     instead of the mandated verdict block (observed this session; the wrapper's marker assertion is the
     working backstop, one re-run cleared it). Candidate for a verifier-prompt hardening if it recurs.
   - **Downstream propagation is operator-gated + DEFERRED** (like all recent scaffold changes): the
     `rules:` block of `openspec/config.yaml` and the verify skill are scaffold-managed and propagated;
     NOT synced to extrends/psc-monitor without fresh operator authorization.

   **Still owned by archive (reconcile from this change dir):** `knowledge/STATUS.md` (new Latest-change
   section, respect the ≤3-section cap — drop the oldest), `knowledge/decisions/INDEX.md` (one registry
   line for this change), `knowledge/questions/INDEX.md` (Parked pointer for the two follow-ons above),
   NO spec promotion (no delta), no other cleanup. Then commit the archive.
