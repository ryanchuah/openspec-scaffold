## Purpose

Define the protocol contract for the deep residual-sweep of outstanding work: an operator-invoked,
pull-only skill that layers on top of the deterministic `outstanding-work-scan` gather and fans out
the five residual-source categories the point-only/heading-only collector structurally cannot read
from prose bodies — in-code markers, questions/decisions/lessons bodies, plans bodies,
reference/compliance/roadmap bodies, and change-dir prose/specs plus untriaged-bucket dedup — as
parallel subagents, then triages surfaced items into the trackers. It mirrors the guardrail shape of
`correctness-audit`/`composition-audit`/`product-audit`: never wired into boot, `AGENTS.md`, or any
auto-run path.

## Requirements

### Requirement: pull-only-operator-invoked-deep-sweep

The `outstanding-work-deep-sweep` capability SHALL be a scaffold-managed skill under
`.claude/skills/` (auto-discovered by both Claude and OpenCode) that is **operator-invoked and
pull-only**: it SHALL NOT be wired into session boot, `AGENTS.md`, any mandatory-read set, or any
auto-run hook, and SHALL be read-only with respect to repo state until its triage step writes triage
outcomes into the trackers. It carries zero boot-context cost, matching the guardrail shape of
`correctness-audit` and `composition-audit`.

#### Scenario: skill exists and is pull-only
- **WHEN** an operator wants the deep residual sweep of outstanding work
- **THEN** the `outstanding-work-deep-sweep` skill SHALL exist under `.claude/skills/` and be invocable on demand

#### Scenario: no boot-path or auto-run wiring
- **WHEN** the scaffold's boot set (`AGENTS.md`, `knowledge/STATUS.md`, `knowledge/questions/INDEX.md` Active) and any auto-run hooks are inspected
- **THEN** none SHALL embed or trigger the deep sweep as a standing or automatic instruction (at most a one-line pointer to the skill)

### Requirement: layers-on-the-deterministic-scan

The deep sweep SHALL run the deterministic `outstanding-work-scan` skill first and build on its
snapshot, rather than replacing or duplicating the deterministic gather. It SHALL NOT modify
`scripts/outstanding.py`, `scripts/checks.py`, `scripts/facts.py`, or the `knowledge_lint` drift
checks — its purpose is the human/LLM judgment step the deterministic collector structurally cannot
perform, not automating that collector.

#### Scenario: scan runs before the sweep
- **WHEN** the deep-sweep skill is invoked
- **THEN** its first step SHALL run `outstanding-work-scan` (the deterministic gather + untriaged dedup) before any residual-prose sweep begins

#### Scenario: collector is not modified
- **WHEN** the deep sweep executes
- **THEN** it SHALL NOT edit `scripts/outstanding.py` or the deterministic detector/fact/lint scripts

### Requirement: five-category-residual-sweep-as-parallel-subagents

The deep sweep SHALL cover the five residual-source categories the point-only/heading-only collector
cannot read from prose bodies — (1) in-code markers, (2) questions/decisions/lessons body sweep,
(3) plans body sweep, (4) reference/compliance/roadmap-body sweep, (5) change-dir prose + specs +
untriaged-dedup — and SHALL run them as parallel subagents that each checkpoint findings to disk so
the work survives interruption.

#### Scenario: all five categories covered
- **WHEN** the deep sweep runs
- **THEN** each of the five residual-source categories SHALL be swept, and each category's subagent SHALL checkpoint its findings to disk

#### Scenario: cross-referenced against existing trackers
- **WHEN** a category subagent reports a candidate item
- **THEN** it SHALL be cross-referenced against `knowledge/questions/INDEX.md` and `knowledge/roadmap.md` so already-tracked work is not re-reported

### Requirement: untriaged-nested-citation-discipline

For the untriaged-findings bucket, the skill SHALL, before promoting a finding ID, check whether
that ID is a child evidence-citation nested inside an already-dispositioned parent finding rather
than a free-standing finding — and SHALL check the **parent-ID disposition** before promoting the
child. This discipline exists because nested child citations and incidental hash-shaped tokens
false-positive identically under a permissive `finding_id_pattern`.

#### Scenario: child citation under a dispositioned parent is not promoted
- **WHEN** an untriaged ID is a child evidence-citation whose parent finding is already scheduled, refuted, or closed elsewhere in the trackers
- **THEN** the skill SHALL NOT promote the child ID as new work, recording the parent disposition instead

### Requirement: triage-into-trackers

After sweeping, the skill SHALL triage surfaced items into `knowledge/questions/INDEX.md` (or
per-item question files) and `knowledge/roadmap.md` — promoting real uncaptured work and recording
why dismissed items were dismissed. This is the full body-triage the deep sweep exists to perform,
which the renamed `outstanding-work-scan` skill deliberately no longer does (its step 3 is narrowed
to the untriaged-bucket dedup only). Durable structural reconciliation of the trackers still normally
happens at archive; this triage is the content pass (what to track, at what priority), not the
structural reconciliation.

#### Scenario: uncaptured work is promoted
- **WHEN** the sweep surfaces a genuinely uncaptured item not reflected in any tracker
- **THEN** the skill SHALL promote it into `knowledge/questions/INDEX.md` (or a per-item file) or `knowledge/roadmap.md`

#### Scenario: dismissed items are recorded with a reason
- **WHEN** a surfaced candidate is judged not to be real trackable work
- **THEN** the skill SHALL record why it was dismissed (refuted, duplicate, already-tracked, not actionable) rather than silently dropping it
