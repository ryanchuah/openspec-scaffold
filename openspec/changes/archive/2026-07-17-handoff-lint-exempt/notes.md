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

## Verify checkpoint

**1. Verdict — READY for archive.** All six acceptance criteria confirmed by live probe on the real
tree, not by fixture green alone. Orchestrator self-review found one real defect (below); it was
fixed and re-verified. The `deepseek/deepseek-v4-pro` behavioral pass returned `VERDICT: READY`,
zero defects, on the fixed tree.

**2. What was confirmed by eyeballing live output** (behavior, not counts):

- A `knowledge/HANDOFF.md` carrying all four constructs — a forward citation, an `ai-docs/`
  retired-path token, a not-yet-existing archive pointer, and a ≥8-line block quoted verbatim from
  `knowledge/README.md` — planted on the **live tree** produced zero findings, and zero collateral
  `duplicate-content-block` on the quoted README (criteria 1).
- With that same tripping handoff present, `bash scripts/check.sh` exited 0 — the handoff is
  committable, which is the whole point of the change (criterion 2).
- The **identical** constructs in a non-handoff knowledge file still flagged all four checks
  (criterion 3) — the exemption did not blind the linter generally. This is the load-bearing guard
  and was proven live, not just in fixtures.
- Orchestrator-authored boundary fixture the executor never wrote: `knowledge/_probesub/HANDOFF.md`
  — a file literally *named* `HANDOFF.md` at a non-sanctioned path — flagged all four checks **plus**
  `handoff-file`, proving the exemption keys on exact path, not filename.
- With the handoff **absent**, lint stayed clean: the citations to `knowledge/HANDOFF.md` from
  `AGENTS.md`, `knowledge/README.md`, `knowledge/decisions/INDEX.md` and others were not flagged —
  no regression to the already-shipped citation-target carve-out (criterion 4). This closes task
  6.2's literal wording ("with no handoff present"), which the executor could not run because the
  live handoff exists.
- `sync_scaffold.check_references` against a target repo whose **only** dangling ref was sourced from
  its `knowledge/HANDOFF.md` scanned zero markdown files and returned clean; adding a dangling ref in
  a non-handoff tracked doc still reported it (criterion 5).
- `openspec validate --strict` valid; `checks.py --check spec-delta-structure` clean (criterion 6).

**3. Defect found and how it was fixed** — surfaced by the **orchestrator self-review** (the pro pass
returned READY on the pre-fix tree and did *not* catch it):

> The duplicate-scan exemption was applied inside only **one** of `_duplicate_scan_files`' three
> collection paths (the `knowledge/` walk), not the top-level glob or the configured
> `duplicate_scan_dirs` walk. Reproduced: with `[knowledge_lint] duplicate_scan_dirs = ["."]` (or
> `["knowledge"]`), the handoff was re-added and `duplicate-content-block` fired on **both** the
> handoff and the file it quoted — silently re-arming the exact trap this change exists to remove.
> This is not a hypothetical config: the codebase already treats a configured scan dir as able to
> re-widen an exclusion — `openspec/specs/` is excluded in **both** loops and pinned by
> `test_duplicate_block_openspec_specs_excluded_via_configured_scan_dir`. It matters downstream
> because `checks.toml` is per-repo and **not** scaffold-managed, so `extrends` / `psc-monitor`
> could each re-open the trap independently.

Fixed by a **re-delegated fresh Sonnet `apply-executor`** (operator pre-route; no deepseek attempt,
per `notes.md` routing) with a scoped fix-spec: the exclusion moved to the single return chokepoint
in `_duplicate_scan_files`, so no collection path can re-add the handoff. Pinned by
`test_duplicate_block_handoff_exempt_via_configured_scan_dir`, whose guard half asserts non-handoff
files sharing a block are **still** flagged. Re-verified from disk by the orchestrator across four
configs. A second, minor finding (a duplicate `"knowledge/HANDOFF.md"` literal newly introduced in
`sync_scaffold.py` — the very drift hazard task 1.3 consolidated away in the sibling linter) was
folded into the same fix-spec as `_SANCTIONED_HANDOFF`.

**4. As-built delta discovered during verify:**

- **Task 4.4's illustrative path was unsatisfiable, and so was the matching spec scenario.**
  `broken-prose-path-citation` only ever scans `knowledge/**/*.md` (it is only called with
  `content_check_md`, built from `_knowledge_markdown`). So at `plans/session-handoff.md` only
  `handoff-file` fires — the broken citation is never checked there, and a test at that path would
  pass **vacuously**. The apply-executor caught this and used `knowledge/session-handoff.md`
  instead; verified empirically at both paths. The `knowledge-lint` delta spec's scenario
  "a handoff-named file elsewhere is exempt from neither check family" asserted both flags for the
  `plans/` example, which is **false** — it was corrected at verify to use a `knowledge/` example and
  to state the `knowledge/**` scan-domain boundary explicitly, so the promoted spec does not ship a
  claim that isn't true.
- **The pro pass's `marker-missing` was a wrapper artifact, overruled with rationale.** The re-run
  pass's wrapper reported `status=marker-missing`, which the verify skill's ladder would escalate as
  an operational crash. Judged from disk instead: the `## Verify Pass` / `VERDICT: READY` block *was*
  emitted, as the model's own `type:"text"` part (not a tool-read of the skill template — the raw
  jsonl was deliberately not grepped, per the skill's own false-positive warning). See field 5.

**5. Forward-looking items for the project docs** (surfaced here, recorded nowhere else — these must
reach `knowledge/questions/INDEX.md` at archive or they die at the session boundary):

- **The same configured-scan-dir leak affects the pre-existing `knowledge/research/` exclusion.**
  Reproduced during verify: with `duplicate_scan_dirs = ["."]`, a `knowledge/research/` file **is**
  flagged for `duplicate-content-block`, even though the `knowledge/` walk prunes research — the
  extra-dirs loop re-adds it, exactly as it did for the handoff. This is **pre-existing** and
  explicitly out of scope here (`notes.md` excludes the research exclusion), so it was deliberately
  not fixed. The chokepoint discipline this change adopted for the handoff arguably belongs to
  `_is_research` too. Candidate for the finding-closure ratchet, since the general shape is
  "an exclusion applied per-loop rather than at the collection chokepoint".
- **`scripts/opencode_delegate.py`'s `extract_text` returns only the LAST `type:"text"` part.** A
  delegate that emits its verdict block and then a trailing summary line yields a false
  `marker-missing` — and the verify skill's ladder treats marker-missing as an operational crash and
  escalates to Sonnet. This fired live in this session: the re-run pro pass emitted a full
  `VERDICT: READY` block, then appended a one-line summary, and the wrapper reported
  `marker-missing`. The first pro pass extracted fine because its verdict block *happened* to be
  last — so the failure is **intermittent and model-behavior-dependent**, which makes it worse: it
  spuriously escalates good passes. Candidate fix: scan all text parts (or the concatenation) for
  required markers rather than only the last. Generalizable harness defect, out of scope here.
- **Downstream propagation is pending and operator-gated** — this change edits scaffold-managed
  files that govern `extrends` and `psc-monitor`. Recorded in
  `knowledge/reference/pending-downstream-propagation.md`. The `duplicate_scan_dirs` finding above
  makes propagation more valuable than usual: each downstream repo's `checks.toml` is per-repo and
  could otherwise re-open the trap.
- **Data-path bounded-domain argument (recorded per the data-path verify rule):** `knowledge_lint.py`
  and `sync_scaffold.py --check-refs` read a repo's tracked markdown into memory. The input domain is
  bounded by a single repo's tracked `.md` files — it does not grow with data or history — so no
  at-scale run is required. The change only *removes* one file from that list; it does not widen the
  domain.

**Still owned by archive:** move the change dir to the dated archive location; promote **both** delta
specs (`knowledge-lint` ADDED, `knowledge-organization` MODIFIED) into `openspec/specs/`; reconcile
`knowledge/STATUS.md` (respect the ≤3-change-section cap), `knowledge/decisions/INDEX.md` (registry
line), and `knowledge/questions/INDEX.md` (fold in the field-5 items above); **delete
`knowledge/HANDOFF.md`** — its normal state is absent and its content now lives in the archived
change dir. Do **not** run the downstream sync (operator-gated) and do **not** push (operator-gated).
Leave `openspec/changes/knowledge-lint-gitignored-citation-exempt/` alone — it is an unrelated
pre-existing ready-to-archive item.
