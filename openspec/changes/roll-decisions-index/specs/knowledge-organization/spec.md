## ADDED Requirements

### Requirement: The decisions registry is a rolling window with on-demand history
`knowledge/decisions/INDEX.md` SHALL hold only the newest tail of the decisions registry, bounded by the `decisions-index-budget` byte budget (default 16,000 bytes; per-repo overridable), with all older entries relocated verbatim — same one-line registry format, same chronological order — into `knowledge/decisions/HISTORY.md`, which is not part of the mandatory boot-read set and is loaded on demand only (grep `knowledge/decisions/` when history matters). When HISTORY.md exists, INDEX.md SHALL carry a standing pointer line to it. The roll SHALL move oldest entries first, be performed by the deterministic `scripts/roll_decisions.py` (verbatim moves, byte-conservation guard, `--dry-run` supported, never empties INDEX), and reduce INDEX to the script's hysteresis target (default 12,000 bytes) so routine archive appends do not immediately re-trip the budget. Raising a decisions-index or boot-surface byte budget SHALL be an explicit operator decision recorded in the decisions registry — never an agent's silent remedy for budget pressure.

#### Scenario: pressure triggers a roll, not a raise
- **WHEN** `knowledge/decisions/INDEX.md` exceeds its byte budget and `scripts/roll_decisions.py` runs
- **THEN** the oldest entry blocks move verbatim to the end of `knowledge/decisions/HISTORY.md`, INDEX.md ends at or under the hysteresis target with its header and newest entries intact plus the HISTORY pointer line, and no byte of any entry is rewritten

#### Scenario: history remains reachable without boot cost
- **WHEN** an agent needs a decision older than INDEX.md's retained tail
- **THEN** the INDEX.md pointer line directs it to `knowledge/decisions/HISTORY.md`, whose entries are in the same registry format and chronological order, and which no mandatory boot read ever loads

#### Scenario: budget raises are operator decisions
- **WHEN** budget pressure fires (a `decisions-index-budget` finding or a boot-surface WARN/FAIL) and no operator decision authorizes a raise
- **THEN** the remedy applied is the roll (or other condensation), and any threshold/budget raise happens only as an operator decision recorded in the decisions registry
