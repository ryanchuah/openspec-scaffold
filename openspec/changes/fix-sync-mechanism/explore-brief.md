# Explore brief — fix-sync-mechanism (W1)

This change is **W1** in the consolidation family that supersedes `scaffold-sync`. It builds the
scaffold→downstream sync mechanism correctly and minimally. Reviewers: read these sources for context.

## What W1 is (and is not)
- **Is:** build `sync_scaffold.py` + `scaffold_manifest.txt` + `scaffold_check.py` + `test_sync_scaffold.py`
  in the **scaffold repo only**, folding the principal-review fixes in from the start.
- **Is not:** propagation. Wiring the guard into downstream `.claude/settings.json` and running the sync
  against extrends/psc-monitor is **W6** (one-time snapshot), out of scope here.

## Source material (authoritative — re-confirm claims against these)
- `ai-docs/consolidation-plan-2026-06-16.md` — THE MAP. §3 (supersession table: what the audit overrides
  vs. what survives) and the spec-impact list are the contract for W1's spec rewrite.
- `openspec/changes/scaffold-sync/principal-review.md` — the review W1 implements: B1 (guard exit 2),
  B2 (AGENTS.md header non-idempotency), M-1 (cut the header subsystem), M-2 (add unit tests), M1/M2 minors.
- `openspec/changes/scaffold-sync/design.md` (D1–D10) and `specs/scaffold-sync-mechanism/spec.md` — the
  FROZEN prior design W1 inherits-and-corrects. The span-replace algorithm (D3), self-managed manifest,
  D10 drift-check, D7 settings.json shape, D8 test-cmd all survive; the D4 header subsystem is CUT.

## Decisions already made (do not re-litigate)
- **Cut the "DO NOT EDIT" header subsystem entirely** (M-1) — no header injected; `--check` is byte-compare
  for regular files, span-reconstruction compare for AGENTS.md. This kills B2.
- **Guard helper `scaffold_check.py` exits `2`** (B1) — the only file whose exit code changes. The `--check`
  CLI stays exit `1` on drift (diagnostic, not a blocking hook).
- **M1 minor:** document the guard's PreToolUse-only coverage limit; do NOT install a real `.git/hooks/pre-commit`.
- Capability `scaffold-sync-mechanism` was never archived → W1's spec is **ADDED Requirements** (fresh), de-headered.
