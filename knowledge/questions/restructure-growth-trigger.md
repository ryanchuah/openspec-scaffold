# Growth-trigger (forward-looking, not built)

From `openspec/changes/archive/2026-06-19-restructure-project-knowledge/design.md` Open Questions:

The `knowledge-organization` spec's `growth-trigger-splits-file` requirement is a standing rule
for the future; this change did NOT build an auto-splitter. The only enforcement shipped is the
existing `status_lint.py` bounds (≤3 STATUS sections, ≤150 words). A splitting mechanism is not
built until a file actually exceeds its budget in practice.

**Status:** parked — not blocking, revisit when a `knowledge/` file hits its bound.
