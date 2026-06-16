<!-- This delta augments the `apply-convergence-guard` capability defined in openspec/specs/apply-convergence-guard/spec.md. -->

## ADDED Requirements

### Requirement: The convergence guard ships with a hardened, instruction-gated canary
The repository SHALL carry an end-to-end canary fixture that an honest apply-executor cannot satisfy by editing the file it is instructed to edit. The impossibility SHALL live in an implementation module that a frozen test imports — NOT in an assertion inside the file the executor is told to edit. The canary's `tasks.md` SHALL list only the implementation module as editable and SHALL mark the test file do-not-edit. Running the apply-executor against the canary SHALL produce a declared `### NON-CONVERGENCE BLOCKER` (trigger a, b, or c — whichever the guard reaches first), not a green result and not a wall-clock timeout. The freeze is instruction-gated (it hardens against the honest edit-the-assertion shortcut, not a malicious rewrite), which is sufficient for the canary's purpose.

#### Scenario: The canary cannot be made green by editing the impl
- **WHEN** an honest apply-executor runs the canary, editing only the implementation module it is told to edit
- **THEN** no implementation of that module can satisfy the frozen test
- **AND** the executor never reaches a green result

#### Scenario: The canary forces a declared non-convergence blocker
- **WHEN** the apply-executor exhausts its convergence budget against the canary
- **THEN** it emits a `### NON-CONVERGENCE BLOCKER` whose trigger is a, b, or c — whichever the guard reaches first — rather than a green result or a wall-clock timeout

#### Scenario: The impossibility is not in the editable surface
- **WHEN** the canary fixture is inspected
- **THEN** the contradiction lives in a frozen test that imports an implementation module
- **AND** it is NOT an assertion inside a file the canary's `tasks.md` lists as editable
