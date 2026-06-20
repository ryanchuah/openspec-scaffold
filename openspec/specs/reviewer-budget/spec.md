## Purpose

Protect the separate-model reviewer's thoroughness from timeout starvation — adequate budget, incremental output that survives a cutoff, and partial salvage — without weakening its read-only guarantee.

## Requirements

### Requirement: The reviewer is budgeted for thoroughness, never rushed
The reviewer invocation SHALL allow at least 780 seconds of wall-clock budget. There are three workflows
that invoke the `openspec-reviewer`, all defined by the `premise-review-gate` capability except the first:
the `openspec-propose` `proposal.md` review (`deepseek-v4-pro`), the **explore direction gate**
(`deepseek-v4-pro`, reviewing an `explore-brief.md`), and the **SMALL pre-apply premise pass**
(`deepseek-v4-flash`, reviewing a plan). (`openspec-verify-change`'s behavioral review is the
orchestrator's own, not a wrapped reviewer call.) All invocations run under the same envelope: the reviewer
SHALL NOT be instructed to read fewer files, avoid re-examination, or otherwise hurry; the cap is a runaway
backstop, not a target; and the invocation SHALL retain a soft-kill grace (`-k 15`) so the process can
flush its last findings before SIGKILL (load-bearing for partial salvage). The explore and SMALL passes
reuse this same 780s / `-k 15` envelope — a review of a short brief or plan finishes well inside it.

#### Scenario: Reviewer budget — propose review
- **WHEN** the reviewer is invoked from the propose workflow to review `proposal.md`
- **THEN** the call is wrapped to allow at least 780s before it is killed

#### Scenario: Reviewer budget — explore direction gate
- **WHEN** the reviewer is invoked for the explore direction gate to review an `explore-brief.md`
- **THEN** the call is wrapped with the same 780s budget and `-k 15` soft-kill grace as the propose review

#### Scenario: Reviewer budget — SMALL premise pass
- **WHEN** the reviewer is invoked for the SMALL pre-apply premise pass
- **THEN** the call is wrapped with the same 780s budget and `-k 15` soft-kill grace as the propose review

#### Scenario: Re-examination is permitted
- **WHEN** the reviewer re-reads a file or re-searches a symbol after learning new information
- **THEN** this is treated as legitimate thorough review, not a fault to be throttled

### Requirement: Review output survives a cutoff
The reviewer SHALL emit its `## Review Round` header first and then each finding as it is
determined, with the verdict last, so that partial output is already usable. On a reviewer timeout
the primary SHALL salvage whatever review text was emitted, record it marked `PARTIAL`, and then
decide: re-run once at full budget if the partial carries at least one finding or was killed more
than 120s into the run; otherwise escalate.

#### Scenario: Incremental emission
- **WHEN** the reviewer produces a review
- **THEN** the round header and findings are emitted progressively, not only in a final block

#### Scenario: Timeout with salvageable findings
- **WHEN** the reviewer is killed by the timeout but had emitted at least one finding (or ran >120s)
- **THEN** the primary records the partial review marked `PARTIAL` and re-runs once at full budget

#### Scenario: Timeout with nothing useful
- **WHEN** the reviewer is killed in under 120s having emitted no findings
- **THEN** the primary records the empty partial and escalates to the user

### Requirement: The reviewer remains read-only
Incremental output SHALL NOT require granting the reviewer write access. The reviewer SHALL retain
its read-only permissions (`edit: deny`, `bash: deny`); findings reach disk via the reviewer's
stdout, which the primary appends to `review-log.md`.

#### Scenario: Reviewer does not write files
- **WHEN** the reviewer runs
- **THEN** it does not modify any file; the primary owns the append to `review-log.md`
