## Purpose

Per-change verify is single-diff-scoped by design, so a subsystem accreted from many
individually-approved changes is never reviewed as a whole, and nothing else in the
scaffold names the occasion to do so. This capability closes that gap with two parts: a
deterministic, advisory, count-based composition-audit due-signal (derived from
archived-changes and commits since the last composition anchor) that surfaces staleness
without ever gating anything, and a cheap, operator-invoked `composition-audit` skill — a
one-shot heavy-detector sweep plus a bounded LLM composition pass over top-ranked
hotspots — that produces a machine-discriminable verdict and routes generalizable
findings into the finding-closure ratchet. The ceremony reuses existing scaffold
instruments (the checks report engine, `audit_scope.py`'s tag/log-line mechanics, the
pre-digest and baseline-diffing patterns) rather than inventing parallel machinery, and
concludes with an operator-gated composition-anchor tag — a discriminable variant of the
existing `audit/*` tag family — that is the sole event resetting the composition cadence
clock.

## Requirements

### Requirement: composition-cadence-trigger-semantics

The scaffold SHALL compute a deterministic, advisory composition-audit due-signal from
repo state. The composition anchor SHALL be discovered as the latest git tag matching
`audit/*-composition` (creator-date ordering). The signal SHALL be computed as:

- `archived_changes_since` = the count of distinct top-level directories under
  `openspec/changes/archive/` that contain **at least one file added** in
  `<anchor>..HEAD` (`git diff --name-only --diff-filter=A`, first path component under
  `archive/`, deduplicated); with no anchor, the count of ALL archive directories.
- `commits_since` = `git rev-list --count <anchor>..HEAD`; with no anchor, the full
  history count.
- `due` = `archived_changes_since ≥ composition_change_threshold` OR
  `commits_since ≥ composition_commit_threshold`.

Default thresholds SHALL be `composition_change_threshold = 10` and
`composition_commit_threshold = 100`, overridable per repo under `[facts.outstanding]`
in `checks.toml` (this spec is normative for the defaults). Degradation SHALL be
graceful and loud: git unavailable → `status: "no-git"` with `due: false`; an anchor
tag whose commit is unreachable → no-anchor semantics (count everything) with the
cause stated in `reason`. The signal SHALL never gate or block any commit, verify,
CI, or lifecycle step.

#### Scenario: never-audited-mature-repo-reads-due
- **WHEN** a repo has no `audit/*-composition` tag and at least
  `composition_change_threshold` archive directories exist
- **THEN** the due-signal SHALL be `due: true` with a reason naming the archive count

#### Scenario: plain-run-audit-tag-does-not-reset-the-clock
- **WHEN** a plain `audit/<date>` tag is created after the latest composition anchor
- **THEN** the composition due-signal SHALL continue counting from the composition
  anchor, unchanged by the plain tag

#### Scenario: composition-anchor-resets-the-clock
- **WHEN** an `audit/<date>-composition` tag is created at HEAD
- **THEN** a subsequent signal computation SHALL count zero archived changes and zero
  commits since the anchor

#### Scenario: sparse-archives-co-fire-on-commits
- **WHEN** fewer than `composition_change_threshold` archive directories were added
  since the anchor but at least `composition_commit_threshold` commits accumulated
- **THEN** the due-signal SHALL be `due: true` (OR co-fire)

#### Scenario: unreachable-anchor-degrades-to-no-anchor
- **WHEN** the latest composition-anchor tag points at a commit that is no longer
  reachable
- **THEN** the signal SHALL be computed with no-anchor semantics and `reason` SHALL
  name the unreachable anchor

### Requirement: composition-anchor-tag-and-log-line

`scripts/audit_scope.py` SHALL accept `--kind composition` on its `tag` and `log-line`
subcommands. `tag --kind composition --date <YYYY-MM-DD>` SHALL create the annotated
tag `audit/<date>-composition` (same operator-gated, sole-mutation contract as the
plain tag). `log-line --kind composition` SHALL print
`- **<date>** · audit/<date>-composition · <short-sha> · <essence>`. Without
`--kind composition`, both subcommands SHALL behave byte-identically to their current
behavior. A composition anchor SHALL also count as a general audit anchor (it matches
`audit/*`); the converse SHALL NOT hold.

#### Scenario: composition-tag-created
- **WHEN** the operator runs `audit_scope.py tag --kind composition --date 2026-07-11`
- **THEN** an annotated tag `audit/2026-07-11-composition` SHALL exist at HEAD

#### Scenario: plain-invocations-unchanged
- **WHEN** `tag` or `log-line` runs without `--kind composition`
- **THEN** the tag name and printed line SHALL match the pre-change formats exactly

#### Scenario: composition-anchor-counts-as-general-anchor
- **WHEN** the latest `audit/*` tag by creator date is a composition anchor
- **THEN** general audit-anchor discovery (`audit_anchor`) SHALL report that tag

### Requirement: one-shot-include-for-report-runs

`scripts/checks.py --report` SHALL accept a repeatable `--include <name>` flag that
treats the named registered-but-disabled check as enabled for that run only. An
already-enabled name SHALL be a no-op (the check runs exactly once). An unknown name
SHALL be an INFRA-FAIL (exit 3). Included checks SHALL participate in preflight
exactly like enabled checks (a missing included tool fails the run with the standard
install-or-disable guidance). `--include` SHALL be valid only with `--report` and
SHALL never persist any configuration change.

#### Scenario: disabled-check-runs-under-include
- **WHEN** `--report --include jscpd` runs in a repo whose config leaves `jscpd`
  disabled and the tool is installed
- **THEN** the jscpd check SHALL execute and its findings SHALL appear in the run's
  `findings.json`

#### Scenario: include-subjects-run-to-preflight
- **WHEN** `--report --include vulture` runs and the vulture tool is not installed
- **THEN** preflight SHALL fail the run (exit 3) with the standard guidance line

#### Scenario: no-include-no-change
- **WHEN** `--report` runs without `--include`
- **THEN** behavior SHALL be identical to the pre-change engine

#### Scenario: already-enabled-include-is-a-no-op
- **WHEN** `--report --include ruff` runs in a repo whose config already enables `ruff`
- **THEN** the ruff check SHALL run exactly once and the run SHALL otherwise be
  identical to `--report` without the flag

### Requirement: composition-ceremony-contract

The scaffold SHALL ship an operator-invoked `composition-audit` skill implementing
this ceremony (this spec is the single normative home for the sequence; the skill
cites it):

1. Wiring detection (missing audit layer → guide build-out, stop).
2. Signal read via the `outstanding` fact (a not-yet-due run SHALL be allowed and
   also resets the clock at close-out).
3. Deterministic sweep: `checks.py --report --include jscpd --include vulture
   --include radon`, plus `--baseline output/checks/composition-baseline.json` when
   that file exists, plus `audit_scope.py scan` for hotspot ranking; an INFRA-FAIL
   SHALL stop the ceremony with the preflight guidance surfaced verbatim.
4. Pre-digest of the detector wall by a delegated cheap-model pass (cluster/dedupe
   into a shortlist, checkpointed to the report dir).
5. A bounded orchestrator judgment pass over the top-K ranked hotspots (default
   K=5 — this spec is normative for the default; the skill cites it), assigning
   `Class:` slugs to findings.
6. A machine-discriminable verdict written to the report dir: exactly one of
   `COMPOSITION: CLEAN`, `COMPOSITION: FINDINGS-ROUTED`, `COMPOSITION: ESCALATE`;
   ESCALATE SHALL be a recommendation to charter a correctness audit and SHALL NOT
   itself charter one.
7. Close-out: for each generalizable finding, the finding-closure-ratchet triage
   (performed by the orchestrating agent, never a delegated executor) and a
   ratchet-ledger line in the frozen format; one audit-log line
   (`--kind composition` variant); the operator-gated composition-anchor tag; and a
   copy of the run's `findings.json` to `output/checks/composition-baseline.json`.

The ceremony SHALL never run autonomously and SHALL never gate any other process.
With no baseline present, the sweep SHALL state that the delta degrades to
"everything new" rather than reporting silently.

#### Scenario: verdict-is-machine-discriminable
- **WHEN** a ceremony completes
- **THEN** the report dir SHALL contain exactly one `COMPOSITION:` verdict line with
  one of the three values

#### Scenario: escalate-recommends-never-charters
- **WHEN** the judgment pass meets an ESCALATE indicator (≥2 distinct cross-module
  classes, any correctness-suspect finding, or a baseline delta that grew after the
  previous FINDINGS-ROUTED close-out)
- **THEN** the verdict SHALL be `COMPOSITION: ESCALATE` recommending a chartered
  correctness audit, and the ceremony SHALL take no chartering action itself

#### Scenario: close-out-routes-into-the-ratchet
- **WHEN** a ceremony ends `FINDINGS-ROUTED` with at least one generalizable finding
- **THEN** the close-out SHALL append conforming ratchet-ledger line(s), one
  composition audit-log line, and lay the composition anchor (operator-gated), and
  copy the run's findings to the standing baseline pointer

#### Scenario: missing-wiring-guides-instead-of-failing
- **WHEN** the ceremony is invoked in a repo with no wired audit layer (no
  `checks.toml`)
- **THEN** the skill SHALL guide the build-out and stop, taking no other action

### Requirement: composition-signal-is-surfaced-in-inventory

The `inventory` fact SHALL expose a `composition_anchor` block as a **sibling** of the
existing `audit_anchor` block, carrying at minimum the fields `tag` (the latest
`audit/*-composition` tag, or `null` when none exists) and `commits_since` (commits
since that tag; full-history count when `tag` is `null`) — the same field shape
`audit_anchor` carries today. The two fields SHALL be allowed to diverge (a plain
run-audit tag advances `audit_anchor` but never `composition_anchor`).

#### Scenario: sibling-anchors-diverge-after-plain-tag
- **WHEN** a plain `audit/<date>` tag is laid after a composition anchor
- **THEN** `inventory.audit_anchor` SHALL report the plain tag while
  `inventory.composition_anchor` SHALL keep reporting the composition anchor

#### Scenario: no-composition-anchor-yields-null-tag
- **WHEN** no `audit/*-composition` tag exists in the repo
- **THEN** `inventory.composition_anchor` SHALL report `tag: null` with
  `commits_since` counting the full history
