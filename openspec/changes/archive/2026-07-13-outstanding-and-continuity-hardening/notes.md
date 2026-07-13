# Notes — outstanding-and-continuity-hardening

**Tier: MEDIUM.** Per the AGENTS.md MEDIUM override, propose emits `tasks.md` (+ this notes.md
for acceptance criteria) + the spec delta; no proposal.md/design.md. The seed plan (problem,
approach, out-of-scope, strict-reservation trade-off) is `plans/outstanding-and-continuity-hardening.md`.

**Premise:** already settled AGREE by a flash `openspec-reviewer` pass on the seed plan
(2026-07-13), before the change dir existed — the direction gate is satisfied; the pro review
below covers the artifacts (tasks + delta), not the premise.

**Why MEDIUM, not SMALL:** the change modifies a governed capability spec — the `knowledge-lint`
requirement that pins the handoff-file check to root-only scope + `HANDOFF*` prefix. A behavior
change to a promoted spec belongs on the delta-and-promote path (spec delta reviewed before
freeze), not a direct SMALL edit. The code footprint is small but the enforced gate propagates
to both downstream repos. Precedent: archived MEDIUM changes shipped `specs/` + `tasks.md`
without proposal/design.

**Disclosed direct-edit exception (task 1.5):** the seed plan said the spec change "rides a
change-dir delta … not a direct edit to the promoted spec." That holds for the *requirement*
(handled by the RENAMED+MODIFIED delta, promoted at archive). It does NOT cover two stale
"root-handoff-file check" cross-references in the spec's **overview prose** (the top paragraph
and the overview requirement's check list) — deltas carry only requirement-level changes, so
delta-sync will never touch overview text. Task 1.5 fixes those two phrases by a direct edit,
which touches no requirement and so cannot conflict with archive delta-sync. This is a scoped,
acknowledged exception to the plan's bright line, not a drift from it.

**Bundling:** this is one coherent pass over two shipped mechanisms — (Q1) the canonical
handoff/continuity file, now strictly enforced repo-wide; (Q2) outstanding-work discovery +
the residual LLM sweep. They share the same "make an existing mechanism actually reachable /
enforced" shape, so they ship together.

**Strict-reservation trade-off (operator chose STRICT, 2026-07-13):** a case-insensitive
substring rule also flags legitimate content-word filenames (`handoff-protocol.md`,
`incident-handover-checklist.md`). Under strict reservation those must be renamed. No opt-out
marker is added (a filename check cannot read an in-file `<!-- lint:... -->` marker); if a real
downstream collision appears, park a path-allowlist follow-on rather than weakening the rule.

## Out of scope (explicit)
- **Downstream cleanup + propagation.** Renaming/archiving extrends' ~27 and psc-monitor's
  handoff-named files, and running `sync_scaffold.py` to push the widened lint, are a **separate
  operator-gated** follow-on. They are coupled: syncing the widened lint before the downstream
  files are cleaned turns those repos' pytest gates red. This change ships the mechanism in the
  scaffold only.
- The frozen OW-2→3→5→6 apply batch — untouched; `knowledge/HANDOFF.md` stays exactly as is.
- `outstanding.py` gather-scope changes (e.g. the parked `plans-scope-alignment` SMALL).

## Acceptance criteria (verified behaviorally at verify)

1. **Repo-wide enforcement:** `knowledge_lint.py` flags a handoff/handover-named file at ANY
   non-gitignored path (nested `plans/…-handoff.md`, `docs/HANDOVER.md`), case-insensitively,
   with the sole exemption `knowledge/HANDOFF.md`; gitignored handoff-named files are not
   flagged. The finding slug is `handoff-file`.
2. **Scaffold tree stays green:** the doc-lint live-tree gate (`test_doc_lint_gate.py`) passes
   unchanged — the scaffold has only `knowledge/HANDOFF.md`. `bash scripts/check.sh` is green
   (ruff + format + full suite + scaffold SEAL).
3. **Spec matches code:** the `knowledge-lint` delta (RENAMED + MODIFIED) describes exactly the
   widened behavior; `openspec validate outstanding-and-continuity-hardening --strict` is clean;
   the delta promotes at archive with no residual "root-only" / "`HANDOFF*` prefix" wording in
   the promoted spec (incl. the two summary lines that describe the check).
4. **Discovery signposted:** AGENTS.md's Working process names the `outstanding-work-review`
   skill as the canonical outstanding-work entry point, in one bullet, without boot-wiring it.
5. **Residual sweep named:** the `outstanding-work-review` skill's Judge step contains a named
   "Residual sweep" sub-step enumerating the deterministic gather's non-coverage (prose bodies,
   in-code TODO, orphaned research docs); the deterministic collector's enumeration is unchanged.
