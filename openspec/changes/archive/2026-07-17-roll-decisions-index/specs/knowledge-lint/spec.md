## ADDED Requirements

### Requirement: The decisions index has an enforced byte budget with a named remedy
`knowledge_lint.py` SHALL report a `decisions-index-budget` finding when `knowledge/decisions/INDEX.md` exceeds its configured byte budget — default 16,000 bytes, per-repo overridable via a `decisions_index_max_bytes` key in the `checks.toml` `[knowledge_lint]` table, with invalid values (non-integer or negative) falling back to the default with a stderr note. The finding message SHALL state the actual size and the budget, name the exact remedy command (`python3 scripts/roll_decisions.py`, rolling oldest entries to `knowledge/decisions/HISTORY.md` per `knowledge/README.md`), and state that raising the budget is an operator decision recorded in the decisions registry. The check SHALL ignore `knowledge/decisions/HISTORY.md`'s size entirely, and a missing INDEX.md SHALL produce no finding.

#### Scenario: over-budget index flags with the remedy named
- **WHEN** `knowledge/decisions/INDEX.md` is larger than the configured byte budget
- **THEN** `knowledge_lint.py` reports exactly one `decisions-index-budget` finding whose message names `roll_decisions.py` as the remedy and marks a budget raise as an operator decision

#### Scenario: under-budget index and unbounded history stay silent
- **WHEN** `knowledge/decisions/INDEX.md` is at or under the budget, regardless of how large `knowledge/decisions/HISTORY.md` has grown
- **THEN** no `decisions-index-budget` finding is reported

#### Scenario: per-repo override honored, invalid override safe
- **WHEN** `checks.toml` sets `[knowledge_lint] decisions_index_max_bytes` to a valid integer, or to an invalid value (string, negative, boolean)
- **THEN** a valid override replaces the default budget for the check, and an invalid one falls back to the 16,000-byte default with a one-line stderr note
