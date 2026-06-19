# fix-convergence-guard (W3) follow-ons

Shipped 2026-06-17. Rationale in decisions registry; archive: `openspec/changes/archive/2026-06-17-fix-convergence-guard/`.

- **Minor cleanup — redundant `_FINGERPRINTS_KEY` re-assignment on CONTINUE path (LOW).** `scripts/_convergence.py` re-assigns the fingerprints dict on the CONTINUE path even though it was already assigned earlier. Harmless; readability cleanup candidate.
- **`openspec validate <change-id>` does not recognize MEDIUM tasks-only changes (LOW).** W3 is MEDIUM with `tasks.md` only (no `proposal.md`); `openspec validate fix-convergence-guard` would fail. Validation via `openspec validate --all` (passed 8/8). Consider teaching `openspec validate` about MEDIUM tasks-only changes.
