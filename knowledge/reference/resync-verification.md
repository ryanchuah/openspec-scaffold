# Re-sync verification checklist

Scaffold-local, on-demand reference — NOT manifest-listed, so it never syncs downstream (same class as
`knowledge/reference/new-repo-bootstrap.md`). Consult it *here* (in the scaffold) when propagating a
scaffold change into an **already-bootstrapped** downstream repo (`extrends`, `psc-monitor`, …) by
re-running `scripts/sync_scaffold.py`.

Distinct from `new-repo-bootstrap.md`: that is a one-time standup checklist for a *fresh* repo (wire
hooks, seed identity, arm the gate). This is the *per-propagation* verification for a repo that already
exists — what to check every time you re-sync, so a change lands cleanly and nothing silently drifts.

**Why two halves.** `sync_scaffold.py --check` iterates only the manifest
(`scripts/scaffold_manifest.txt`), so it verifies the *auto-propagated* layer deterministically — but it
is structurally blind to everything the manifest does not list: per-repo `knowledge/`, `openspec/specs/`,
and any file *deletion* (the manifest has no delete verb). The deterministic checks catch mechanical
drift; the judgment sweep catches what the manifest cannot see. You need both.

## Order of operations

1. `scripts/sync_scaffold.py <target>` — the full sync: copies manifest files byte-identical,
   span-replaces the shared `AGENTS.md` sections, rules-block-replaces `openspec/config.yaml`, and stamps
   the `.scaffold-version` provenance beacon at the target root.
2. Run the deterministic checks (A) — all must be green.
3. Do the judgment sweep (B) — the part only a human/agent, not `--check`, can do.
4. Operator reviews the downstream diff and commits **in the downstream repo** (the downstream
   commit-test gate re-runs its suite).
5. Push **only** with explicit operator authorization — never by default.

## A. Deterministic checks (all must pass)

1. **Convergence.** `scripts/sync_scaffold.py --check <target>` → exit `0`; every manifest file reports
   IDENTICAL. A per-repo `## Project context` / `context:` block is correctly ignored; a DIFFERS or
   MISSING means the sync did not fully land — re-run the full sync and investigate.
2. **Scaffold lint (structural checks).** `scaffold_lint.py` is authoring-side and never syncs, so run
   it FROM the scaffold against the target: `python3 scripts/scaffold_lint.py --root <target>`. The four
   *structural* checks — AGENTS.md anchors, dangling skill refs, config-rules-last, budget agreement —
   are the meaningful downstream gate and must be clean. Its fifth check, *manifest-completeness*, is a
   scaffold-authoring invariant: run against a downstream repo it will legitimately flag that repo's own
   per-repo scripts (e.g. `run_trendscope.sh`, `_*_oneoff.sh`) that are not in the shared manifest —
   those findings are expected downstream, not drift.
3. **Knowledge lint.** In the target: `python3 scripts/knowledge_lint.py` → exit `0` (orphan/duplicate
   canonical files, retired-path tokens, broken prose citations, dangling archive pointers).
4. **Suite green.** The target's own test suite passes (its `scaffold_lint` invariant SEAL plus all
   tests), enforced by the target's commit-test gate at commit time.
5. **Provenance beacon.** `.scaffold-version` at the target root names the scaffold HEAD you synced from
   (short SHA + committer date + subject). Confirm it advanced to the commit you intended to propagate.

## B. Judgment sweep (`--check` is blind to all of this)

6. **Non-auto-propagated layer.** The sync does NOT touch per-repo knowledge (`knowledge/STATUS.md`,
   `knowledge/decisions/`, `knowledge/questions/`, `knowledge/lessons.md`, `knowledge/roadmap.md`,
   `knowledge/reference/`, `knowledge/research/`) or `openspec/specs/`. If the scaffold change introduced
   or renamed any *terminology, rule, or process concept*, re-apply that change **by hand** in each
   downstream repo's knowledge and specs, then re-read for contradictions. The `lint-knowledge` skill is
   the semantic-drift pass for this; `knowledge_lint` only catches *structural* drift, not stale meaning.
7. **Deletions / tombstones.** The manifest has no delete mechanism, so a file the scaffold *removed*
   still lives downstream until deleted by hand. Currently owed: delete the `openspec-onboard` skill in
   each downstream repo (the onboard tombstone) and confirm it is gone. Whenever a propagation batch
   includes a scaffold-side deletion, record it as an explicit per-repo manual step before syncing.
8. **Per-repo wiring follow-ons.** Anything downstream the scaffold cannot carry: `audit.toml`,
   `checks/*.sql`, task-runner (`just`) targets, dev-extras pins for the audit layer, and a first
   `lint-knowledge` pass. These are per-repo build-out tracked as parked follow-ons in
   `knowledge/questions/INDEX.md` — verify they exist / are updated; do not assume the sync created them.

## Deeper reference

- Mechanism and exact contracts: the `scaffold-sync-mechanism` capability spec
  (`openspec/specs/scaffold-sync-mechanism/spec.md`) — see `check-mode-reports-drift`,
  `sync-stamps-scaffold-provenance`, and the `AGENTS.md` span-replace / `openspec/config.yaml`
  rules-block requirements.
- Fresh-repo standup (not re-sync): `knowledge/reference/new-repo-bootstrap.md`.
- The auto-vs-manual propagation split in prose: the "Scaffold-managed files & propagation" section of
  `AGENTS.md`.
- Which changes are currently queued for propagation: `knowledge/STATUS.md` (`## Immediate next action`)
  — deliberately kept there, not duplicated here, so this checklist stays durable across propagations.
