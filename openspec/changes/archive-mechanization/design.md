## Context

The archive phase (and the standalone `openspec-sync-specs` skill) promote spec deltas into
canonical main specs entirely via LLM prose editing, and move the change dir via LLM-run shell.
Three of the four delta operations — **ADDED / REMOVED / RENAMED** — are whole-block transforms
keyed by requirement name: deterministic and correctness-critical. Only **MODIFIED** (partial
scenario merge into an existing requirement) is genuine judgment.

Grounding facts (verified):
- A delta-block grammar already exists in `scripts/checks.py`: `_SECTION_HEADER_RE`
  (`^## (ADDED|MODIFIED|REMOVED|RENAMED) Requirements$`), `_REQUIREMENT_HEADER_RE`
  (`^### Requirement:\s*(.*)`), `_SCENARIO_HEADER_RE` (`^#### Scenario:`). It parses
  `### Requirement:` blocks but **does not** parse the RENAMED list-item format.
- **RENAMED uses a different shape:** `- FROM: \`### Requirement: Old\`` / `- TO: \`### Requirement: New\``
  (list items, backtick-wrapped whole header lines, often with no blank line under the section header).
- Main specs start `## Purpose` then a plain `## Requirements` header; requirement blocks run to
  the next `### Requirement:`, the next `## ` header, or EOF. All 19 existing main specs share this.
- Two callers, different discovery: the **archive-executor** operates on a change dir it also moves;
  the **standalone `openspec-sync-specs`** skill discovers the change via
  `openspec status --change <name> --json` (`artifactPaths.specs.existingOutputPaths`).
- Both `archive-executor.md` bodies are byte-identical (frontmatter aside) — enforced by
  `test_executor_body_agreement.py`. Move today is plain `mv` + `mkdir -p` + a conflict guard.

## Goals / Non-Goals

**Goals:**
- Deterministic, tested promotion of **ADDED / REMOVED / RENAMED** into main specs.
- Deterministic, tested change-dir move with a conflict guard.
- **Never corrupt a canonical spec:** plan fully, write all-or-nothing, halt-and-report on any
  ambiguous/would-write-wrong operation.
- Reserve the LLM for exactly **MODIFIED merges + doc reconciliation** — emit MODIFIED as a
  machine-readable deferral, don't attempt it deterministically.
- Serve **both** callers (archive + standalone sync-specs) from one script.

**Non-Goals:**
- Automating MODIFIED merges or the doc-reconciliation narrative (stay LLM-on-pro).
- Changing the delta *format* or the `spec-delta-structure` linter.
- Downstream propagation (operator-gated, deferred).
- OW-11 residual skill de-bloat (separate concern).

## Decisions

**D1 — Two stdlib-only scripts.** `scripts/apply_delta_spec.py` (the promoter) and
`scripts/archive_move.py` (the move). No third-party deps, matching the repo's script convention
(argparse CLI, `sys.exit(main())`, tests import + call `main()` directly).

**D2 — Parser grammar: own copy + a frozen agreement test (not a shared module).**
`apply_delta_spec.py` defines its own copies of the three `### Requirement:`-grammar regexes, and
`test_apply_delta_spec.py` imports `checks` and asserts each pattern string equals its `checks.py`
counterpart. *Rationale:* extracting a shared grammar module would churn the load-bearing
`checks.py` detector (just-fixed for a real defect) for marginal gain; the byte-agreement test is
the same anti-drift idiom the repo already uses in `test_executor_body_agreement.py`. *Alternative
(shared `_spec_grammar.py`):* rejected — churn > benefit; the OW-11 follow-on already ranks such
extraction low-priority.

**D3 — RENAMED gets a separate parser path.** Under `## RENAMED Requirements`, parse `- FROM:` /
`- TO:` list items; extract the text between the backticks (the full `### Requirement: <name>`
header line). This is a distinct code path from the `### Requirement:`-block parser — the existing
grammar never handled it. (Direction-gate 🟡 #1.)

**D4 — The operation truth table.** One principle governs every case:
**already-achieved end-state → reported *skip* (no-op); would-write-wrong or ambiguous → *anomaly*
(halt, write nothing); clean forward op → *apply*.**

| Operation | Main-spec state | Action |
|---|---|---|
| **ADDED** `X` | `X` absent | **apply** — append block under `## Requirements` |
| **ADDED** `X` | `X` present, body norm-equal | **skip** (already added) |
| **ADDED** `X` | `X` present, body differs | **ANOMALY** (would overwrite different content) |
| **REMOVED** `X` | `X` present | **apply** — delete the block |
| **REMOVED** `X` | `X` absent | **skip** (already removed / nothing to do) |
| **RENAMED** `X→Y` | `X` present, `Y` absent | **apply** — rewrite header line `X`→`Y` |
| **RENAMED** `X→Y` | `X` absent, `Y` present | **skip** (already renamed) |
| **RENAMED** `X→Y` | `X` absent, `Y` absent | **ANOMALY** (rename target does not exist) |
| **RENAMED** `X→Y` | `X` present, `Y` present | **ANOMALY** (ambiguous — would duplicate `Y`) |
| **MODIFIED** `X` | (any) | **defer** — emit in report for the LLM; never applied |

*Body normalization for the ADDED-present comparison:* compare the requirement block with
per-line trailing whitespace stripped and leading/trailing blank lines trimmed, so blank-line
drift never manufactures a false anomaly while real content differences still halt. *REMOVED-absent
= skip (not anomaly):* the end-state REMOVED wants (requirement absent from main) is already true,
it corrupts nothing, and it keeps re-runs safe. Recorded as a *monitored* choice — flip to anomaly
if a silent-skip typo ever bites. *Detection surface for a typo'd REMOVED name:* the `skipped` list
carries `reason: "target-absent"`, and the archive skill's Step 6 review surfaces the skipped list
to the operator — the applier is not a name-existence gate (neither is `_validate_delta`), so a
mistyped REMOVED name shows up as a visible skip, not a silent loss. *Alternative (REMOVED-absent →
anomaly):* rejected — breaks idempotency and halts the whole promotion for a benign no-op.

*The same rules apply to self-collisions **within** one delta.* Two `### Requirement: X` blocks under
`## ADDED Requirements` with differing bodies → the planner applies the first in memory, then sees
`X` present-with-different-body → **anomaly**; two identical blocks → the second is a **skip**. No
special-casing — the in-memory plan is built incrementally, so intra-delta collisions fall out of
the same table.

**D5 — ADDED behavior change is intentional and BREAKING.** The current sync skill (Step 4c) treats
ADDED-name-collision as implicit-MODIFIED and silently overwrites. D4 replaces that: byte-normal
collision → skip, differing collision → anomaly. **Never a silent overwrite.** This is the change's
one deliberate contract break — a strict safety improvement. (Direction-gate 🟡 #2.)

**D6 — Atomicity: plan-all-in-memory, write-all-or-nothing across the change's specs.** The applier
parses every `specs/<cap>/spec.md` delta, computes the full post-promotion content of every touched
main spec in memory, and classifies each op. If **any** op across **any** spec is an ANOMALY: write
nothing, print the full report (all applies/skips/defers/anomalies), exit nonzero. Only a fully clean
plan (zero anomalies) writes — then it writes every touched main spec. *Rationale:* a change's spec
deltas are one logical unit; a half-promoted spec set is worse than none. MODIFIED-deferred and
skips do **not** block the write (they are expected/benign). *Per-file write is atomic* (temp file
in the same dir + `os.replace`), so no single main spec is ever left half-written. *Limit — not
multi-file transactional:* a process crash / disk-full / permission error between writing spec A and
spec B can leave A promoted and B not; the applier has no in-script rollback for that. The archive
skill's recovery block (`git reset --hard HEAD` + scoped `git clean`; D7 guarantees the change dir
has not moved yet) is the sole mitigation and restores the Step-5.0 checkpoint cleanly.

**D7 — Ordering: promote-then-move.** The archive-executor runs the applier against the **active**
change dir first, then moves. *Rationale:* spec promotion is the risky operation; if it anomaly-halts,
nothing has moved, main specs are untouched, and recovery is trivial. The applier takes an explicit
`--change-dir`, so it is order-agnostic; the skill/executor orchestrates the order. Executor step
order becomes: (1) `apply_delta_spec.py` (ADD/REM/REN, from active change dir) → (2) LLM MODIFIED
merges (from the applier's deferred list) → (3) `archive_move.py` → (4) reconcile docs (from the
moved archive dir). *Alternative (move-then-promote, today's order):* rejected — an anomaly after
the move leaves an archived-but-unpromoted state. The existing recovery block
(`git reset --hard HEAD` + scoped `git clean`) still rolls back cleanly under the new order.
(Proposal 🟡 #3.)

**D8 — MODIFIED-deferral ordering is naturally correct.** Because the deterministic applier runs
*before* the LLM MODIFIED pass, a delta that RENAMEs `X→Y` and also MODIFIEs `Y` (a real pattern —
`2026-07-13-outstanding-and-continuity-hardening`) works: the applier renames first, the LLM then
merges scenarios into the already-renamed `Y`.

**D9 — New-main-spec creation.** An ADDED requirement whose capability has no
`openspec/specs/<cap>/spec.md` → create it with a `## Purpose` (one TBD line) + `## Requirements`
skeleton, then append the ADDED blocks. A REMOVED/RENAMED targeting a nonexistent main spec →
ANOMALY (nothing to modify). (Direction-gate 💡 #3.) *A main spec with a `## Purpose` but no
`## Requirements` header* is parsed as having zero requirements (REMOVED-absent → skip,
RENAMED-absent → anomaly per D4); when ADDED must append to it, the applier inserts a
`## Requirements` header before the block. The parser never crashes on a missing `## Requirements`.

**D10 — Dual-invocation via one script + a preserved discovery flow.** `apply_delta_spec.py` accepts
`--change-dir <dir>` (which contains `specs/<cap>/spec.md`) and `--specs-root <dir>` (default
`openspec/specs`). The **standalone `openspec-sync-specs`** skill keeps its `openspec` CLI discovery
(Steps 1–3) and calls the applier as a subprocess for ADD/REM/REN, then does MODIFIED merges by hand;
the **archive-executor** calls it on the active change dir per D7. (Direction-gate 🟡 #3, 💡 #2.)
The archive skill's **Step 4** (the pre-prompt sync assessment) is rewired to run
`apply_delta_spec.py --dry-run --json`, parse the report, and surface applied + skipped + deferred
+ anomalies in the operator prompt in place of today's hand-eyeballed delta-vs-main comparison. If
the dry-run reports any anomaly, the prompt advises the operator to resolve it before archiving
(the executor's real run would halt on it anyway); the sync/no-sync decision maps to whether the
report shows any pending applies/defers.

**D11 — Report + CLI contracts.**
- `apply_delta_spec.py --change-dir <dir> [--specs-root openspec/specs] [--dry-run] [--json]`
  emits a JSON report (with `--json`) and a human summary otherwise. `--dry-run` plans + reports
  but writes nothing (used by the archive skill's Step-4 pre-prompt sync assessment). Report shape:
  ```json
  {"status": "ok|anomaly",
   "specs": [{"capability": "...", "main_spec": "...", "created": false,
              "applied": {"added": ["..."], "removed": ["..."], "renamed": [["Old","New"]]},
              "skipped": [{"op":"REMOVED","name":"...","reason":"target-absent"},
                          {"op":"ADDED","name":"...","reason":"body-equal"},
                          {"op":"RENAMED","name":"X->Y","reason":"already-renamed"}],
              "deferred_modified": ["..."],
              "anomalies": [{"op":"ADDED","name":"...","reason":"present with different body"}]}]}
  ```
  Exit **0** = clean plan applied (writes done; MODIFIED may remain, skips may exist);
  exit **2** = ≥1 anomaly (nothing written). `--dry-run` uses the same exit codes without writing.
  The **human summary** (no `--json`) lists anomalies **first** and prominently, then applies /
  skips / deferred — so a halting archive is not buried in a wall of text. The script's `--help`
  summarizes the D4 operation semantics (what applies / skips / anomalies / defers) so it is
  self-documenting for an operator debugging a halted archive.
- `archive_move.py --change-root <dir> --archive-path <dir>`: assert source exists, assert dest does
  **not** (conflict → exit 2, nothing moved), `mkdir -p` the dest parent, move (plain `shutil.move`
  — git stays out of the script; the primary stages at commit). Exit **0** on success.

**D12 — Manifest + guards.** All four new files go in `scripts/scaffold_manifest.txt`
(scaffold-managed). The rewritten executor bodies stay byte-identical
(`test_executor_body_agreement.py`); skill edits introduce no dangling refs, no new hardcoded model
IDs or delegation budgets (the archive invocation budget is unchanged).

## Risks / Trade-offs

- **Parser-grammar drift** between the applier and `checks.py` → *Mitigation:* D2 agreement test.
- **Requirement-block boundary edge cases** (trailing blank lines, EOF, blocks with no scenarios,
  H1/intro/`## Purpose` preamble before the first section) → *Mitigation:* orchestrator-authored
  adversarial fixtures at verify; block boundary = next `### Requirement:` / next `## ` / EOF.
- **RENAMED debut** (never exercised repo-wide) → *Mitigation:* tested contract + fixtures for all
  four RENAMED rows of D4.
- **All-or-nothing blocks the whole change on one anomaly** → *Accepted:* safety over partial
  progress; the report names the offending op and the primary/LLM resolves it, then re-runs.
- **REMOVED-absent silent-skip could mask a typo** → *Accepted + monitored* (D4); low-severity,
  visible in the `skipped` report, and caught upstream by delta review.

## Migration Plan

No data migration; backward-compatible. Existing archived changes are untouched. The scripts are
additive; the skill/executor prose is rewired to call them. Rollback = revert the change (the
scripts are unused once the prose no longer references them). The first real archive that carries a
RENAMED delta exercises that path for the first time — now under a tested contract.

## Open Questions

None blocking. The two prior open questions (REMOVED-absent, ordering) are resolved in D4/D7. The
REMOVED-absent skip-vs-anomaly choice is recorded as monitored (revisit only if a silent-skip typo
is observed).

## Verification (change-specific acceptance criteria)

- **`apply_delta_spec.py` — every D4 row:** ADDED apply/skip/anomaly (absent / present-normequal /
  present-differ); REMOVED apply/skip (present / absent); RENAMED apply/skip/anomaly×2 (FROM-present,
  already-renamed, neither, both); MODIFIED deferred-not-applied; new-main-spec creation; REMOVED/
  RENAMED-on-missing-spec anomaly.
- **Intra-delta self-collision:** two ADDED blocks for the same name, differing bodies → anomaly;
  identical → skip.
- **RENAMED+MODIFIED combo (D8):** a single delta with RENAMED `X→Y` **and** MODIFIED `Y` applies the
  rename and reports `Y` in `deferred_modified` (the applier does not attempt the merge), confirming
  rename-before-merge ordering.
- **Empty / degenerate deltas:** a `## ADDED Requirements` section with no requirement block is a
  clean no-op (no crash); a delta with no section headers at all is a clean no-op.
- **Only-`## Purpose` main spec:** REMOVED-absent → skip, RENAMED-absent → anomaly, ADDED inserts a
  `## Requirements` header — no crash on the missing header.
- **Atomicity:** a delta set mixing a clean ADDED with one anomaly writes **nothing** and exits 2;
  a written main spec is never left half-written (per-file `os.replace`).
- **`--dry-run`:** writes nothing, reports the same plan/exit code.
- **Report shape:** `--json` emits the D11 schema; `status` and exit code agree.
- **D2 agreement test:** applier's three shared regex patterns equal `checks.py`'s.
- **`archive_move.py`:** moves a dir; dest-exists → exit 2, nothing moved; creates the archive parent.
- **Integration/guards:** `scripts/check.sh` green; `scaffold_lint` clean (4 new files in manifest);
  `test_executor_body_agreement.py` passes (both bodies identical post-rewrite); no dangling skill refs.
- **Prose rewiring (human-verified at verify):** archive SKILL Step 5 + both executor bodies invoke
  the two scripts in the D7 order; sync-specs calls the applier for ADD/REM/REN and reserves the LLM
  for MODIFIED; the ADDED-collision BREAKING note (D5) replaces the old Step-4c overwrite prose.
