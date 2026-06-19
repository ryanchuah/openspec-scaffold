# fix-sync-mechanism follow-ons

Shipped 2026-06-17. Rationale in decisions registry; archive: `openspec/changes/archive/2026-06-17-fix-sync-mechanism/`.

- **Guard coverage limit (M1) — carried, not closed.** `scaffold_check.py` only intercepts Claude Bash-tool commits; operator-terminal and opencode/deepseek executor commits bypass it; `--no-verify` is the sanctioned escape.
- **`--check` AGENTS.md first-run cosmetic DIFFERS (D6 caveat)** — one-time formatting mismatch; running sync once normalizes it.
- **Manifest staleness (R3)** — self-managed manifest; newly-added shared file not listed is invisible to sync until updated.
- **R1 line-anchored span risk (accepted)** — downstream `## Project context` containing literal `## Roles` would mis-slice; low-risk.
- **Live guard hook smoke is W6** — DONE (W6 2026-06-17).
