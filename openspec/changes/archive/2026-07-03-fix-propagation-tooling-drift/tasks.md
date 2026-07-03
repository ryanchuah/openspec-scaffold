# tasks — fix-propagation-tooling-drift (SMALL)

Implement top-to-bottom. Do NOT commit (the orchestrator reviews and commits).

- [x] 1. `scripts/sync_scaffold.py`: extend `_EPHEMERAL_PATHS` (currently
      `("knowledge/HANDOFF.md",)`, ~line 361) to `("knowledge/HANDOFF.md", "knowledge/audit-log.md")`.
      Update the adjacent comment to note this set must stay in step with
      `knowledge_lint.EPHEMERAL_PATHS` (single source of truth for "legitimately ephemeral" paths).
- [x] 2. `scripts/test_sync_scaffold.py`: add a regression test — a target repo whose `AGENTS.md`
      (and/or a synced `knowledge/*.md`) cites `knowledge/audit-log.md` while that file is ABSENT
      must pass `check_references` (return 0 / no DANGLING line for audit-log.md). Mirror the style
      of the existing check-refs tests in that file.
- [x] 3. `scripts/scaffold_lint.py`: change `_MANIFEST_EXCLUDE_GLOB` (~line 144) from
      `"scripts/_*_oneoff.py"` to `"scripts/_*_oneoff.*"` so `.sh` (and any other) oneoffs are
      excluded from manifest-completeness. Update the docstring's exclusion-list mention
      (the `scripts/_*_oneoff.py` glob reference in the module docstring, ~line 49) to match.
- [x] 4. `scripts/test_scaffold_lint.py`: add a regression test — a `scripts/_x_oneoff.sh` present
      but NOT in the manifest produces NO `manifest-completeness` finding. Mirror the existing
      manifest-completeness tests.
- [x] 5. Verify (do not commit): full `pytest` suite green; `python3 scripts/sync_scaffold.py
      --check-refs .` → exit 0; `python3 scripts/scaffold_lint.py` → `scaffold-lint: clean`.
      (Orchestrator + flash verifier both green — VERDICT: READY. See `review-log.md`.)
