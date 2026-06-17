# verify-multimodel-gate Specification — delta (lifecycle-gates)

Delta against `openspec/specs/verify-multimodel-gate/spec.md`. The multi-model passes, the
simplicity/quality gate, and the security review are tier-conditioned per the tiers in `AGENTS.md`.

## MODIFIED Requirements

### Requirement: Verify runs independent multi-model passes after the self-review
The verify step SHALL run independent verification passes by additional models, layered immediately after the orchestrator's MANDATORY behavioral review (the self-review, "pass 1") and before the artifact/spec mapping checklist and the report/`notes.md` steps. The self-review remains the orchestrator's own non-delegated review; the additional passes SHALL NOT replace it. These passes apply to **MEDIUM and COMPLEX** changes ONLY: a SMALL change does its own verification per `AGENTS.md` (optionally one `deepseek/deepseek-v4-flash` pass if the orchestrator judges it risky) and SHALL NOT run these passes or invoke the verify skill. For a MEDIUM or COMPLEX change the pass sequence SHALL depend on the orchestrator's platform: a Claude Code orchestrator SHALL run self-review → a `deepseek/deepseek-v4-pro` verifier pass → a `deepseek/deepseek-v4-flash` verifier pass; an OpenCode orchestrator SHALL run self-review → a `deepseek/deepseek-v4-flash` verifier pass only.

#### Scenario: A MEDIUM/COMPLEX Claude Code change runs three passes

- **WHEN** the orchestrator is Claude Code, the change is MEDIUM or COMPLEX, and the self-review completes
- **THEN** a `deepseek/deepseek-v4-pro` verifier pass runs, then a `deepseek/deepseek-v4-flash` verifier pass runs, before any report or `notes.md` is written

#### Scenario: A MEDIUM/COMPLEX OpenCode change runs the flash pass only

- **WHEN** the orchestrator is OpenCode, the change is MEDIUM or COMPLEX, and the self-review completes
- **THEN** a single `deepseek/deepseek-v4-flash` verifier pass runs, and no pro pass runs

#### Scenario: A SMALL change runs self-review only (with an optional flash pass)

- **WHEN** the change is SMALL
- **THEN** it does NOT invoke the verify skill, its multi-model passes, or the verify phase-gate STOP
- **AND** the orchestrator may optionally run a single `deepseek/deepseek-v4-flash` verifier pass if the orchestrator judges the change risky

#### Scenario: The self-review is preserved

- **WHEN** the multi-model passes run (for MEDIUM/COMPLEX)
- **THEN** the orchestrator has already performed its own non-delegated behavioral review, and the delegated passes are additional confirmations rather than a substitute for it

## ADDED Requirements

### Requirement: Verify runs a simplicity/quality gate (MEDIUM/COMPLEX)
For MEDIUM and COMPLEX changes, the verify step SHALL run a harness-neutral simplicity/duplication/dead-code review of the change's `git diff`, positioned after the verifier passes return READY and before the artifact/spec mapping checklist. The gate does NOT block on pure style nits — it targets over-engineering, duplication, and dead code.

SMALL changes are exempt from this gate.

#### Scenario: Claude Code uses the simplify/code-review skill

- **WHEN** the orchestrator is Claude Code and the verifier passes have returned READY for a MEDIUM/COMPLEX change
- **THEN** the orchestrator invokes the `simplify` (or `/code-review`) skill on the change's `git diff` and folds confirmed findings into the defect path

#### Scenario: OpenCode uses a concrete checklist

- **WHEN** the orchestrator is OpenCode and the verifier passes have returned READY for a MEDIUM/COMPLEX change
- **THEN** the orchestrator itself reviews the `git diff` against this concrete checklist — (a) code duplicating functionality that already exists elsewhere in the repo; (b) abstractions introduced but used only once; (c) dead or unreachable code paths; (d) over-parameterization/config beyond the change's actual scope

#### Scenario: A confirmed simplification defect uses the re-delegation path

- **WHEN** a simplicity/quality finding is confirmed from disk
- **THEN** the orchestrator routes it through the existing defect re-delegation path (same as verifier findings)

### Requirement: Verify runs a security review for sensitive-surface changes
When a change touches auth, credentials/secrets, persisted data, or an external API/network surface, the verify step SHALL run a harness-neutral security review before declaring READY. This is a **hard gate for COMPLEX** changes on those surfaces and a **recommended** pass for MEDIUM changes on those surfaces. Changes touching none of those surfaces do not trigger it.

#### Scenario: Claude Code uses the security-review skill

- **WHEN** the change (MEDIUM or COMPLEX) touches auth, credentials/secrets, persisted data, or an external API/network surface
- **AND** the orchestrator is Claude Code
- **THEN** the orchestrator invokes the `security-review` skill on the diff

#### Scenario: OpenCode uses a concrete security checklist

- **WHEN** the change (MEDIUM or COMPLEX) touches auth, credentials/secrets, persisted data, or an external API/network surface
- **AND** the orchestrator is OpenCode
- **THEN** the orchestrator itself reviews the diff against this concrete checklist — (a) authn/authz bypass or missing authorization on new endpoints/queries; (b) credential/secret leakage (logged, returned in a response, or committed); (c) unsanitized external/user input reaching SQL, shell, or file paths (injection); (d) unsafe deserialization; (e) missing input-confirmation guard on a destructive operation

#### Scenario: A confirmed security defect uses the re-delegation path

- **WHEN** a security finding is confirmed from disk
- **THEN** the orchestrator routes it through the existing defect re-delegation path (same as verifier findings)

#### Scenario: Changes without sensitive surfaces skip the security gate

- **WHEN** the change touches none of auth, credentials/secrets, persisted data, or an external API/network surface
- **THEN** the security review is not triggered
