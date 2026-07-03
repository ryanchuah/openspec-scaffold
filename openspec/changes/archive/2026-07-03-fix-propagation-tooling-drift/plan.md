# SMALL plan — fix-propagation-tooling-drift

Tier: **SMALL** (two narrow, well-understood fixes to authoring-side tooling; regression tests each).
Surfaced during the 2026-07-03 extrends propagation.

## Problem statement

Two authoring-side scaffold tools disagree with reality / with each other. Neither file is
manifest-listed (both are in `scaffold_lint._MANIFEST_EXCLUDE_EXACT`), so **neither fix
propagates downstream** — this is scaffold-internal hygiene only.

1. **check-refs ephemeral-allowlist drift.** `scripts/sync_scaffold.py`'s `--check-refs` uses
   `_EPHEMERAL_PATHS = ("knowledge/HANDOFF.md",)` (line ~361). `scripts/knowledge_lint.py`
   uses `EPHEMERAL_PATHS = ("knowledge/HANDOFF.md", "knowledge/audit-log.md")` (line ~120).
   Because `knowledge/audit-log.md` is legitimately ephemeral (created on first audit; cited by
   the synced `AGENTS.md` "Deterministic audit tooling" section and `knowledge/README.md`), the
   two allowlists disagree. Result: the scaffold's **own** `sync_scaffold.py --check-refs .`
   reports 2 false dangling refs, and the same 2 fire in every downstream repo after sync.

2. **scaffold_lint oneoff exclusion is `.py`-only.** `scripts/scaffold_lint.py`'s
   `_MANIFEST_EXCLUDE_GLOB = "scripts/_*_oneoff.py"` (line ~144) does not match `.sh` oneoffs.
   A `scripts/_*_oneoff.sh` (e.g. downstream `_cron_reenable_oneoff.sh`) is flagged
   "exists but not listed in manifest" by manifest-completeness. Latent scaffold bug; surfaced
   when running `scaffold_lint.py --root <downstream>`.

## Proposed approach

1. Add `"knowledge/audit-log.md"` to `sync_scaffold._EPHEMERAL_PATHS`, with a comment cross-
   referencing `knowledge_lint.EPHEMERAL_PATHS` so the two are kept in step. Regression test in
   `scripts/test_sync_scaffold.py`: a repo whose AGENTS.md cites `knowledge/audit-log.md` (file
   absent) passes `check_references` (exit 0).
2. Broaden `scaffold_lint._MANIFEST_EXCLUDE_GLOB` to match `.sh` oneoffs too — change the single
   glob to `scripts/_*_oneoff.*` (covers `.py` and `.sh`; the `_`-prefix + `_oneoff` infix keep
   it tight). Regression test in `scripts/test_scaffold_lint.py`: a `_x_oneoff.sh` present but
   unlisted produces no manifest-completeness finding.
3. Doc: clarify `knowledge/reference/resync-verification.md` step A2 — when run against a
   **downstream** repo, `scaffold_lint`'s manifest-completeness legitimately flags per-repo
   scripts; the 4 structural checks are the meaningful downstream gate. (Doc-only; done by the
   orchestrator directly.)

## Out of scope

- Creating `knowledge/audit-log.md` — it is ephemeral by design (seeded on first audit run).
- A `--downstream` mode for `scaffold_lint` that skips manifest-completeness (larger design
  question; the A2 doc clarification covers the operational need for now).
- Any change to the synced `AGENTS.md` / `knowledge/README.md` citations (they are correct;
  the tooling was wrong).
- Any downstream propagation (both edited files are authoring-side, never synced).

## Verification

- `python3 scripts/sync_scaffold.py --check-refs .` → exit 0 (was exit 1).
- `python3 scripts/scaffold_lint.py` → `scaffold-lint: clean` (unchanged; regression-guarded).
- Full `pytest` suite green (new regression tests included).
- Single `deepseek/deepseek-v4-flash` verifier pass per the SMALL bullet.
