# notes — handoff-lint-exempt

**Tier:** MEDIUM. Scaffold-managed linter (`scripts/knowledge_lint.py`) + the ref-checker
(`scripts/sync_scaffold.py`) + their tests + two spec deltas. Golden source → propagates to
`extrends` and `psc-monitor`.

## Problem (root cause, reproduced — not inferred)

`knowledge/HANDOFF.md` is the scaffold's sanctioned mid-session handoff: a session that runs out
of context writes it, the next session absorbs and deletes it (`knowledge-organization` spec,
"each-knowledge-type-has-one-home"). Its entire purpose is to tell the **next** session what to
build — so it forward-references files that **do not exist yet**, and carries quoted context
forward so the next session need not re-read the source.

`knowledge_lint.py` scans it as ordinary steady-state knowledge prose. Those forward references and
quoted blocks are flagged as drift. The live-tree gate
(`scripts/test_doc_lint_gate.py::test_knowledge_lint_live_tree_clean`) turns the canonical green
gate (`scripts/check.sh`) red, and the shipped `PreToolUse` commit-test-gate hook then blocks the
commit.

**The scaffold therefore mandates a handoff mechanism and simultaneously makes it un-committable.**
The only way to reach green is to delete the handoff. Every agent hitting this has correctly
diagnosed a red suite and reached the one available remedy — destroying the handoff. This is not
lint noise; it is a self-defeating loop that has been silently eating handoffs.

## Evidence — four check families trip, empirically enumerated

Written to a realistic handoff fixture on the live tree and run (fixture removed afterwards; the
baseline tree is green):

| Check | Trips? | Why it is inherent to a handoff |
|---|---|---|
| `broken-prose-path-citation` | yes (×3) | forward-references not-yet-created files — the file's purpose |
| `retired-path-token` | yes | fired even on prose saying *"the old `ai-docs/` layout is gone; do not resurrect it"* |
| `dangling-archive-pointer` | yes | names the archive dir the in-flight change will land in |
| `duplicate-content-block` | yes | carries quoted context forward; **also pins a collateral finding on the innocent quoted file** (`knowledge/README.md`) |

The reported symptom was only the first row. Fixing only that leaves three triggers armed, and the
next context-exhausted session deletes the next handoff.

## Why not the existing `lint:planned` marker

`knowledge_lint.py` already has `<!-- lint:planned -->` (knowledge-lint spec, "An inline lint:planned
marker suppresses forward-reference citations"). It is **not** the answer here:

- It suppresses **only** `broken-prose-path-citation` — 1 of the 4 trips. A diligent handoff author
  annotating every line still goes red on the other three.
- It is **line-scoped and manual**, demanding per-citation ceremony from a session that is by
  definition out of context. That is the worst possible moment to require annotation discipline.
- `duplicate-content-block` is **block**-scoped and fires collaterally on the *quoted* file, which no
  marker on the handoff can reach.

`lint:planned` is correctly designed for a **steady-state** knowledge doc making an *occasional,
exceptional* forward reference. In a handoff, forward references are the **rule**. The mismatch is
categorical, which is why the fix belongs at file-category level, not line level.

## Approach — extend the existing exclusion precedent

`knowledge_lint.py` already excludes `knowledge/research/` from content checks
(`_RESEARCH_EXCLUDE`, mirrored by `sync_scaffold.py`'s `_REF_SCAN_EXCLUDE`), because
*"period-correct historical analyses legitimately cite pre-restructure paths."*

`knowledge/HANDOFF.md` is the **exact mirror image**: a forward-looking file that legitimately cites
not-yet-created paths. Research prose resolves against a past that is gone; handoff prose resolves
against a future that has not arrived. Neither is steady-state knowledge, and the linter's model of
"broken" is wrong for both.

So: exempt `knowledge/HANDOFF.md` from the same prose-hygiene scan sets, extended to cover the two
additional sets the evidence proves it trips (archive-pointer, duplicate-block). This is an
**extension of an established precedent, not a new mechanism** — and it completes a set of
carve-outs that already exists for this exact file:

1. exempt as a **citation target** (`EPHEMERAL_PATHS`) — already shipped
2. exempt from the **handoff-named-file** check (sole sanctioned handoff) — already shipped
3. exempt as a **scanned source** — **this change** (the missing leg)

## Operator pre-routing (recorded per AGENTS.md Roles)

The operator explicitly pre-routed this change's **apply** and **archive** executors to a **Sonnet
subagent**, in place of the default deepseek-driven `opencode run` executors:

> "For apply-executor and archive, use sonnet subagent instead of deepseek"

AGENTS.md sanctions exactly this ("The operator MAY pre-route a specific change's apply to
Sonnet-first, recorded in that change's `notes.md`"), and the `.claude/agents/apply-executor` and
`.claude/agents/archive-executor` subagents are the designated Sonnet fallbacks. Use them **first**
here — this is a pre-route, not a fallback after a crash, so no deepseek attempt is needed. The
routing does not change the tier, the gates, or the verify chain.

**Verify is NOT pre-routed.** The operator's instruction named apply and archive only. Verify's
independent multi-model passes (MEDIUM → orchestrator self-review, then a
`deepseek/deepseek-v4-pro` behavioral pass via the verify skill) run as normal — routing verify to
Sonnet too would collapse the multi-model independence the gate exists to provide.

## Assumptions (recorded defaults — non-blocking; operator away)

- **A1 — Whole-file, not per-line.** Exempting the whole file (vs. extending `lint:planned` to the
  other checks) is chosen because the file's *category* differs; see above. Reversible.
- **A2 — Structural/tree-shape checks still apply.** `orphan-duplicate` and the named-file checks
  (audit-log, ratchet-log, ledgers) still run over `HANDOFF.md`. It is cited by `knowledge/README.md`
  and `AGENTS.md`, so it is not an orphan; the named-file checks do not target it. Only the four
  **prose-hygiene** checks are exempted — the narrowest cut that closes every proven trigger.
- **A3 — HANDOFF stays tracked, not gitignored.** Gitignoring it would also silence the linter, but
  would violate the cross-agent rule (AGENTS.md: all project state lives in **tracked**,
  agent-neutral files) and would keep the handoff from reaching a different agent/machine. Rejected.
- **A4 — `sync_scaffold.py` is fixed too** though it is not in `scaffold_manifest.txt`: its
  `--check-refs` scans a **target** repo's tracked markdown, so a downstream `knowledge/HANDOFF.md`
  hits the same source-scan blind spot. Fixing one tool and not its mirror would re-open the trap
  downstream.

## Acceptance criteria (change-specific; MEDIUM → criteria live here, not in tasks.md)

1. A `knowledge/HANDOFF.md` containing forward references, a retired-path token, a planned archive
   pointer, and a quoted ≥8-line block from another knowledge file produces **zero**
   `knowledge_lint.py` findings — including zero **collateral** findings on the quoted file.
2. With that handoff present, `bash scripts/check.sh` is **green** — i.e. a handoff is committable,
   which is the whole point of the change.
3. **Over-broad-suppression guard (load-bearing):** the identical broken citation, retired-path
   token, planned archive pointer, and duplicated block in a **non-handoff** knowledge file are
   **still flagged**. The exemption must be keyed to `knowledge/HANDOFF.md` exactly — not to a
   substring, not to any handoff-named file, not to `knowledge/*`.
4. `knowledge/HANDOFF.md` remains exempt from the handoff-named-file check (no regression to the
   sole-sanctioned-handoff behavior).
5. `sync_scaffold.py --check-refs` does not report dangling refs sourced **from** a target repo's
   `knowledge/HANDOFF.md`, while still reporting dangling refs from every other tracked doc.
6. `bash scripts/check.sh` and `openspec validate --strict` clean on the baseline tree.

## Out of scope

- Broadening any exemption beyond `knowledge/HANDOFF.md` (e.g. all handoff-named files, or
  blanket-exempting missing citations) — drift on tracked steady-state prose must still flag.
- Changing `lint:planned` semantics, or the `knowledge/research/` exclusion.
- Downstream propagation to `extrends` / `psc-monitor` — operator-gated
  (`knowledge/reference/pending-downstream-propagation.md`).
- The `knowledge-drift-review` skill's LLM semantic pass (raised by the round-1 reviewer). It runs
  `knowledge_lint.py` first and then sweeps for stale claims, so it could still surface a handoff's
  forward-referencing prose as a "not yet built" contradiction. Deliberately left alone: that skill is
  **operator-invoked and never a commit gate**, so it cannot re-create the self-defeating
  write→red→delete loop this change fixes. Recorded as a boundary, not a defect.
- Archiving the already-verified `openspec/changes/knowledge-lint-gitignored-citation-exempt/`
  (a pre-existing, unrelated ready-to-archive item flagged in `knowledge/STATUS.md`).
