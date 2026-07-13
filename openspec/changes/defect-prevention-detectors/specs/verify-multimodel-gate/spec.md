# Delta — verify-multimodel-gate (defect-prevention-detectors)

The lens requirement's forward-compat clause said "when a corresponding detector ships … the lens
prompt SHALL direct the verifier to run and confirm the detector's findings." Those detectors now
ship (the `defect-prevention-detectors` capability), so this delta makes the clause concrete (name
the `checks.py --check` invocations) and adds the OW-4 data-path recording rule as a verify gate.

## MODIFIED Requirements

### Requirement: The COMPLEX third pass runs a lens the behavioral stack lacks
For a COMPLEX change, the third delegated pass SHALL be a **lens pass**: a fixed prompt asking questions the behavioral checklist does not ask, rather than a third run of the same behavioral checklist. The verify skill SHALL carry the canonical lens prompts inline (not by pointer into an archived change). The v1 lens menu is:
- **Test-quality / adversarial-oracle lens (default):** for each test the change adds or modifies, would the test fail if the behavior it claims to cover broke — name the assertion that would trip; flag tautological or forced-green assertions, empty test bodies, mocks that replace the module under test, discarded return values/flags, and unfrozen clocks in tests.
- **Data-scale lens (for data-path-dominant changes):** which input domains are unbounded in production; whether the change fully materializes an unbounded query result (e.g. `fetchall()` on an unbounded query); whether the change needs an at-scale run or a recorded bounded-domain argument.

The orchestrator SHALL select the lens per change and record the selection with a one-line rationale in `review-log.md`. The lens pass is **diff-scoped**: it SHALL NOT be required to re-run the full test suite (the pro behavioral pass has already done so) and MAY run targeted commands/probes instead. Its findings are leads the orchestrator confirms from disk, and it retains the hard-gate and recovery semantics of the pass-sequence requirements. The orchestrator MAY additionally run a lens pass on a MEDIUM change when the change's risk profile warrants it, under the same contract and recording rules. The scaffold now ships the corresponding deterministic detectors (the `defect-prevention-detectors` capability: `checks.py --check test-quality` and `checks.py --check data-scale`); each lens prompt SHALL direct the verifier to FIRST run the matching detector and confirm its findings from disk, THEN apply the lens judgment the detector cannot make mechanically (e.g. "would this test fail if the behavior broke?", or "is this unbounded domain actually bounded in production?") — rather than rediscover the mechanical findings by hand.

#### Scenario: Default lens selection
- **WHEN** a COMPLEX change has no dominant data-path risk
- **THEN** the orchestrator selects the test-quality/adversarial-oracle lens and records the selection with a one-line rationale in `review-log.md`

#### Scenario: Data-scale lens for a data-path change
- **WHEN** a COMPLEX change's dominant risk is data-path behavior (unbounded inputs, query volume, large-scale processing)
- **THEN** the orchestrator selects the data-scale lens and records the selection with a one-line rationale in `review-log.md`

#### Scenario: The lens runs the shipped detector before judging
- **WHEN** the test-quality or data-scale lens pass runs and the matching `checks.py` detector exists
- **THEN** the lens prompt directs the verifier to run `checks.py --check <test-quality|data-scale>` and confirm its findings from disk before applying the residual lens judgment

#### Scenario: The lens pass does not re-run the full suite
- **WHEN** the lens pass runs
- **THEN** it is not required to re-run the full test suite and may run targeted probes scoped to its lens questions

#### Scenario: The lens pass is a hard gate
- **WHEN** the lens pass returns NEEDS REVISION and the orchestrator confirms the defect from disk
- **THEN** the existing fix → re-run-failed-pass recovery path applies, including the three-cycle escalation bound

#### Scenario: A MEDIUM change opts into a lens pass
- **WHEN** the orchestrator judges a MEDIUM change's risk profile to warrant a lens pass
- **THEN** it MAY run one flash lens pass after the pro pass, with the same selection recording, gate semantics, and verdict contract

## ADDED Requirements

### Requirement: A data-path change records an at-scale run or a bounded-domain argument
When a change modifies a data path (a query, bulk transform, or any code whose input volume can grow with data or history), verify SHALL require the change's `notes.md` to record EITHER evidence of an at-scale run OR an explicit bounded-domain argument (why the input is bounded in production). This is the standing enforcement of the canonical "Mind data scale" rule (`AGENTS.md`, `openspec/config.yaml` `rules.verify`) — cited, not restated. Absence of both, on a data-path change, is a verify defect the orchestrator resolves before archive. Changes touching no data path do not trigger it.

#### Scenario: Data-path change with neither record is a defect
- **WHEN** a change adds an unbounded query or bulk-materialization path and its `notes.md` records neither an at-scale run nor a bounded-domain argument
- **THEN** verify flags it as a defect to resolve before archive

#### Scenario: A bounded-domain argument satisfies the rule
- **WHEN** a data-path change's `notes.md` records why the input domain is bounded in production (e.g. "keyed by one run's rows, not all history")
- **THEN** the rule is satisfied without requiring an at-scale run
