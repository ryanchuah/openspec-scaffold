## Purpose

Give discovered defect classes a closure contract: a generalizable finding is closed only
by a recorded, machine-verifiable disposition (enforcing check, frozen-test linkage, or
explicit waiver) in a lint-enforced ledger, with routing steps at the existing archive and
audit close-out gates — so found bug classes cannot silently recur the way prose-only
lessons allow.

## Requirements

### Requirement: generalizable-findings-close-only-with-a-recorded-disposition

A generalizable finding SHALL NOT be treated as closed until `knowledge/ratchet-log.md`
records exactly one disposition for its class: an enforcing deterministic check
(`check:`), a frozen regression-test linkage (`test:`), an explicit waiver
(`waiver:review-by YYYY-MM-DD` with a reason), a temporary `open:since YYYY-MM-DD` state,
or `grandfathered` (legal only for pre-ratchet legacy lessons). A generalizable finding is
a defect class that could recur in sibling code, not a one-off instance; the normative
preference ordering is check > frozen test > waiver.

#### Scenario: class closed by an enforcing check

- **WHEN** a bug class is fixed and a detector for the class lands (a `checks/*.py`
  invariant, a `checks/*.sql` invariant per the existing `data_lint.py` flat-dir
  convention, or a named check in a scaffold lint script)
- **THEN** the ledger gains one registry line with a `check:` pointer to that artifact,
  and the class is closed

#### Scenario: domain-judgment-only class is waived, not silently dropped

- **WHEN** a real, generalizable class is judged not mechanically detectable and not
  test-freezable
- **THEN** the ledger records `waiver:review-by <date> — <reason>` rather than nothing,
  so the open decision is visible and re-reviewable instead of becoming prose-only memory

#### Scenario: enforcement deferred without blocking the change

- **WHEN** a fix ships but its enforcing artifact is deferred
- **THEN** the ledger records `open:since <date>` and archive proceeds; the entry is
  age-flagged by lint once it exceeds the configured threshold

### Requirement: ratchet-ledger-has-a-lintable-registry-format

`knowledge/ratchet-log.md` SHALL hold one line per finding-class in the registry-line
format `- **YYYY-MM-DD** · <kebab-class-slug> · <disposition> — <essence>`, where
`<disposition>` is one of `check:<pointer>`, `test:<path>[::<name>]`,
`waiver:review-by YYYY-MM-DD`, `open:since YYYY-MM-DD`, `grandfathered`. Dates MUST be
valid ISO 8601 calendar dates. Ledger format is scaffold-defined; ledger content is
per-repo and never manifest-synced.

#### Scenario: malformed entry is flagged

- **WHEN** a ledger line has an unknown disposition keyword, a non-kebab slug, or an
  invalid calendar date (e.g. `2026-13-01`)
- **THEN** the deterministic knowledge linter reports a finding naming the line

#### Scenario: format check is guarded on adoption

- **WHEN** a repo has no `knowledge/ratchet-log.md`
- **THEN** the linter reports nothing for the ratchet (absent file = clean; un-adopted
  repos are unaffected)

### Requirement: enforcement-pointers-are-verified-live-not-declarative

The deterministic knowledge linter SHALL verify that every `check:` and `test:`
disposition points at an artifact that exists: the pointed-at file path must exist, and
**when a `::<name>` suffix is present** it must appear textually in the pointed-at file
(a bare file path is legal and verifies file existence only). Waivers past their
`review-by` date and `open` entries older than the configured age threshold (default 30
days, configurable as `ratchet_open_max_age_days` under the `[knowledge_lint]` table of
`checks.toml`) SHALL be flagged. `grandfathered` entries receive format validation only —
no liveness checks.

#### Scenario: dangling pointer is flagged

- **WHEN** a ledger entry cites `check:checks/no_such_file.py` or
  `test:scripts/test_x.py::test_gone` where the file is missing or the name does not
  appear in the file
- **THEN** the linter reports a dangling-enforcement finding for that entry

#### Scenario: valid entry passes without findings

- **WHEN** a ledger entry cites `check:scripts/knowledge_lint.py::_check_ratchet_log` and
  the file exists with the named symbol textually present
- **THEN** the linter reports no finding for that line

#### Scenario: grandfathered entry not checked for liveness

- **WHEN** a ledger entry has disposition `grandfathered` and its essence text mentions a
  path that does not exist
- **THEN** the linter does not report a dangling-pointer finding for it (format only)

#### Scenario: stale waiver is flagged

- **WHEN** a `waiver:review-by` date is in the past
- **THEN** the linter reports a stale-waiver finding, forcing a re-review or a renewed
  date

#### Scenario: aged open entry is flagged

- **WHEN** an `open:since` entry is older than the configured threshold
- **THEN** the linter reports an aged-open finding

### Requirement: close-out-gates-route-findings-into-the-ledger

The archive skill (primary's review step) and the run-audit skill (triage step) SHALL
each include a bounded triage step of at most three questions — real defect? →
generalizable class? → mechanically detectable or test-freezable? — whose output for a
qualifying finding is one ledger line plus its enforcing artifact or waiver. Findings
judged not-real (Q1 = no) or not-generalizable (Q2 = no) SHALL produce no ledger entry —
the ledger holds classes, not noise or one-offs. The triage is performed by the
orchestrating agent (judgment work), never delegated to the mechanical archive-executor,
and never blocks on building a detector (the `open` disposition exists for deferral).

#### Scenario: bug found and fixed during a change reaches the ledger at archive

- **WHEN** a change's notes/review log record a defect found and fixed during
  apply/verify, and the primary judges the class generalizable
- **THEN** the archive commit includes a ledger line for the class (check/test if the
  enforcing artifact shipped with the fix, otherwise open or waiver)

#### Scenario: audit finding judged real reaches the ledger at triage

- **WHEN** a run-audit cycle's triage judges a finding a real, generalizable defect class
- **THEN** the triage output includes a ledger line alongside the existing audit-log
  ceremony
