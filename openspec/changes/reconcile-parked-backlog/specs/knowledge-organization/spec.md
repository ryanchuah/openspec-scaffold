## MODIFIED Requirements

### Requirement: archive-step-reconciles-into-new-structure

The archive step SHALL reconcile current project state into the new structure — `knowledge/STATUS.md`, `knowledge/decisions/INDEX.md`, and `knowledge/questions/` — and SHALL NOT write to the legacy `STATUS.md` (root) or `ai-docs/` paths. Before filing a follow-on item into `knowledge/questions/`, the archive step SHALL verify the item was not already resolved by the very change being archived — checking the change's own diff and commits — and SHALL file the item only if it is still open.

#### Scenario: archive-updates-memory-state
- **WHEN** a change is archived
- **THEN** the archive step SHALL update `knowledge/STATUS.md`, append the decision to `knowledge/decisions/INDEX.md`, and reconcile `knowledge/questions/` (Active/Parked)

#### Scenario: decisions-index-entry-points-to-archive
- **WHEN** a decision is appended to `knowledge/decisions/INDEX.md` during archiving
- **THEN** the entry SHALL be a one-line registry entry that points to the change archive holding the full rationale (or carries the rationale inline when no archive exists)

#### Scenario: questions-horizon-split-on-archive
- **WHEN** a change is archived and leaves follow-on items
- **THEN** blocking items SHALL remain in `knowledge/questions/INDEX.md` (Active) and non-blocking items SHALL be moved to Parked, so the boot-read Active section holds only current blockers

#### Scenario: archive-checks-follow-on-not-already-resolved-by-this-change
- **WHEN** the archive step is about to file a follow-on item into `knowledge/questions/`
- **THEN** it SHALL first check the change's own diff/commits to confirm the item was not already resolved by this change, and SHALL file the item only if it is still open
