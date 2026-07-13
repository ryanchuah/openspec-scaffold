# composition-audit-cadence (OW-6) follow-ons

**Source:** `openspec/changes/archive/2026-07-13-composition-audit-cadence/notes.md` (verify
checkpoint, field 5) — monitored/deferred items surfaced during verify, none blocking.

1. **Advisory-signal edge — pre-anchor dir counted on a post-anchor add.**
   `archived_changes_since` counts a pre-anchor archive directory if a NEW file is added to it
   after the anchor (the implementation matches the spec's literal "dir with ≥1 file added in
   range" rule). Benign on an advisory, never-gating signal, but the trigger technically violates
   the immutable-archive-dir policy. If real repos hit it, tighten the spec rule/impl. Also fix
   `design.md`'s counting note, which conflates "edit" and "add" (a post-archive edit to an
   existing dir never inflates the count, but a post-archive add does).

2. **Advisory-signal edge — inconsistent no-anchor counting basis.** The no-anchor branch counts
   on-disk archive directories via `iterdir()` (including untracked dirs), while the anchored
   branch counts via git diff — an inconsistent basis on untracked WIP dirs. Benign and transient;
   consider a git-based no-anchor count for consistency.

3. **Behavior-preserving cleanups parked to `ratchet-lint-cleanup.md`** (appended there, not
   repeated here in full): `outstanding.py`'s duplicate `rev-list` blocks and duplicate no-git
   degraded-dict; a `checks.py` `composition_anchor`↔`audit_anchor` shared-helper extraction; the
   `audit/<date>-composition` literal, hardcoded across 4 modules, centralized into one constant;
   and `audit_scope.py`'s defensive `getattr(args, "kind")` fallback.

4. **`audit_anchor` null-parity asymmetry.** `composition_anchor` returns the full-history commit
   count when no composition tag exists (per its spec); `audit_anchor` keeps its pre-existing
   `null`-when-no-tag behavior. Align in a separate change if the operator wants parity — out of
   OW-6 scope.

5. **Threshold recalibration.** `composition_change_threshold = 10` /
   `composition_commit_threshold = 100` are evidence-anchored judgment, not derivation. The first
   two downstream ceremony cycles should revisit them via the per-repo `[facts.outstanding]` keys.

6. **D8 30-day revisit trigger.** Signal visibility is pull-only for v1 (the recurring-surface
   notice was declined). If a downstream repo is observed sitting `due` unseen for more than 30
   days, add the recurring-surface notice then, as its own SMALL change.

7. **`run-audit-untested` partial-closure evidence.** The first downstream composition ceremony
   exercises the shared tag/log-line/wiring-detection surfaces end-to-end, providing partial
   closure evidence for `knowledge/questions/run-audit-untested.md` — feed findings back there
   when it happens.
