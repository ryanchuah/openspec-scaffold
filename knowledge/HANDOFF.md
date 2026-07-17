# HANDOFF — handoff-lint-exempt (resume at apply)

**Written:** 2026-07-17 · **Phase reached:** propose COMPLETE, artifacts frozen · **Resume at:** apply
**Change dir:** `openspec/changes/handoff-lint-exempt/` · **Tier:** MEDIUM

Operator instruction: the proposing session halts here; a fresh session carries out **apply →
verify → archive**. Autonomy through archive was granted. Read this file, then the change dir, then
proceed.

---

## 1. Read these first, in this order

1. `openspec/changes/handoff-lint-exempt/notes.md` — problem statement, reproduced evidence,
   rejected alternatives, operator pre-routing, assumptions, and the **acceptance criteria**.
   This is the densest artifact; it carries the reasoning this file only summarises.
2. `openspec/changes/handoff-lint-exempt/tasks.md` — the frozen, reviewed implementation plan.
3. `openspec/changes/handoff-lint-exempt/review-log.md` — the pro review and how each finding was
   dispositioned.
4. The two frozen delta specs under `openspec/changes/handoff-lint-exempt/specs/`.

You do **not** need to re-derive the analysis. It is frozen and reviewed. Start at task 1.1.

## 2. What this change fixes (the one-paragraph version)

`knowledge/HANDOFF.md` — this very file — is the scaffold's sanctioned mid-session handoff. Its
purpose is to tell the *next* session what to build, so it forward-references files that do not
exist yet and carries quoted context forward. But `scripts/knowledge_lint.py` scans it as ordinary
steady-state knowledge prose and flags all of that as drift. The live-tree gate in
`scripts/test_doc_lint_gate.py` then turns `scripts/check.sh` red, and the shipped `PreToolUse`
commit-test-gate hook blocks the commit. **So the scaffold mandates a handoff mechanism and
simultaneously makes it un-committable** — the only route to green is to delete the handoff. Every
agent that has hit this correctly diagnosed a red suite and reached the one available remedy:
destroying the handoff. That is the bug. It has been silently eating handoffs.

The fix extends an exclusion precedent that already exists in the same file: `knowledge/research/`
is exempt from content checks because period-correct historical prose legitimately cites paths that
no longer exist. A handoff is the mirror image — forward-looking prose that legitimately cites paths
that do not exist *yet*. Neither is steady-state knowledge.

## 3. Status: what is done, what is left

**Done (do not redo):**
- Root cause reproduced deterministically on the live tree, not inferred.
- Scope established empirically: **four** check families trip on a realistic handoff, not the one
  that was reported (see §4).
- MEDIUM tier self-classified; artifacts written and frozen: `tasks.md` + two delta specs +
  `notes.md`.
- Pro review (deepseek-v4-pro, `openspec-reviewer`) round 1: `VERDICT: PASS`, `PREMISE: AGREE`,
  zero 🔴. `scripts/freeze_check.py` → `FREEZE: READY`. Delegation verified real: `status=ok
  fallback=no marker_ok=yes`.
- All non-blocking reviewer findings folded into `tasks.md` / `notes.md` (see `review-log.md`).
- `openspec validate handoff-lint-exempt --type change --strict` → valid.
- Baseline `bash scripts/check.sh` → green.

**Left:** apply → verify → archive. Nothing else.

**Not yet committed.** The change dir and this handoff are uncommitted working-tree files. Commit
them as your first checkpoint if you like, or fold them into the apply commit.

## 4. The single most important piece of context

The reported symptom was **one** check (`broken-prose-path-citation`). The real scope is **four**.
This was established by writing a realistic handoff fixture to the live tree and running the linter
— evidence, not speculation. All four fire:

| Check | Why a handoff inherently trips it |
|---|---|
| `broken-prose-path-citation` | forward-references not-yet-created files — the file's whole purpose |
| `retired-path-token` | fires even on prose *warning against* a retired path |
| `dangling-archive-pointer` | names the archive dir the in-flight change will land in |
| `duplicate-content-block` | carries quoted context forward — **and pins a collateral finding on the innocent quoted file** |

**Fixing only the reported symptom leaves three triggers armed**, and the next context-exhausted
session deletes the next handoff. The frozen plan closes all four. Do not narrow it.

There is also an existing `<!-- lint:planned -->` marker mechanism. It is **not** the answer, and
`notes.md` explains why at length: it suppresses only 1 of the 4 checks, it is line-scoped and
manual (demanding per-citation ceremony from a session that is by definition out of context), and
it cannot reach the collateral duplicate finding on the quoted file at all. Do not let a reviewer
or your own instinct re-litigate this — it was assessed and the pro reviewer agreed.

## 5. Dogfood note — read before you touch this file

This handoff was hand-threaded around the very trap the change removes: paths verified to resolve
one by one, no retired-path token written, no archive dir named, no long verbatim quote. That
ceremony is exactly what the fix eliminates, and doing it manually is the firsthand evidence that
the burden is real.

**Consequence for you:** until task 2.x lands, editing this file can turn `scripts/check.sh` red and
the commit hook will block you. If that happens, **do not delete this file** — that is the exact
failure being fixed. Either run `python3 scripts/knowledge_lint.py`, read the finding, and adjust
the prose; or land the fix first and then write freely. After the fix lands, this file is exempt and
you can edit it without care.

## 6. Operator routing — pre-routed to Sonnet

The operator explicitly pre-routed **apply** and **archive** to **Sonnet subagents** instead of the
default deepseek `opencode run` executors:

> "For apply-executor and archive, use sonnet subagent instead of deepseek"

AGENTS.md sanctions this (recorded in `notes.md` per the Roles section). Use the `apply-executor`
and `archive-executor` subagents (`.claude/agents/apply-executor.md`,
`.claude/agents/archive-executor.md`) **directly and first** — this is a pre-route, not a
post-crash fallback, so do not attempt deepseek first and do not walk the failure ladder in
`.claude/skills/_shared/delegation-harness.md`.

**Verify is deliberately NOT pre-routed.** The operator named apply and archive only. MEDIUM's
verify chain (orchestrator self-review → `deepseek/deepseek-v4-pro` behavioral pass via the verify
skill) runs as normal. Routing verify to Sonnet as well would collapse the multi-model independence
that the gate exists to provide — the whole point is that the final quality call is not made by one
model's blind spots.

## 7. Phase-by-phase

**Apply** — invoke the `openspec-apply-change` skill; delegate to the Sonnet `apply-executor`
subagent with the change dir. Tasks are sequential, top to bottom; the executor checks each off. It
does **not** commit — you review and commit in small checkpoints. Do not fan out: the tasks are
dependency-laden and concurrent writers corrupt each other.

**Verify** — invoke `openspec-verify-change`. MEDIUM ⇒ self-review, then the pro behavioral pass,
then the simplicity/quality gate, before the artifact/spec mapping checks. The acceptance criteria
are in `notes.md` (**not** `design.md` — MEDIUM emits no design.md; the config rule text assumes a
design.md that this tier does not produce). Criterion 3 (the over-broad-suppression guard) is the
load-bearing one: **prove the exemption did not blind the linter generally.** The cheapest honest
proof is to plant the four constructs in a non-handoff knowledge file and watch them still flag.
Eyeball a live probe rather than trusting the suite — a green suite at fixture scale is not
evidence the live tree behaves.

**Archive** — invoke `openspec-archive-change`; delegate to the Sonnet `archive-executor`. It moves
the change dir, syncs the two delta specs into `openspec/specs/`, and reconciles `knowledge/STATUS.md`
+ `knowledge/decisions/INDEX.md` + `knowledge/questions/INDEX.md`. Respect the STATUS cap rule (≤3
change sections). **Delete this handoff file as part of archive** — its normal state is absent, and by
then its content lives in the archived change dir.

## 8. Gates and boundaries — do not cross without the operator

- **Downstream propagation is operator-gated.** This change touches scaffold-managed files that
  propagate to `extrends` and `psc-monitor`. Do **not** run the sync. Record the change as pending in
  `knowledge/reference/pending-downstream-propagation.md` — that ledger is the handoff to the
  operator, and the last few changes are already queued there.
- **Push to remote is operator-gated.** Commit to `main` freely in small tested checkpoints; do not
  push.
- **`scripts/sync_scaffold.py` is not in the manifest** but is still in scope (task 3.x): its
  `--check-refs` scans a *target* repo's tracked markdown, so a downstream handoff hits the same
  source-scan blind spot. Fixing one tool and not its mirror re-opens the trap downstream.

## 9. Loose ends you will trip over (both pre-existing, both out of scope)

- `openspec/changes/knowledge-lint-gitignored-citation-exempt/` is verified, landed, and needs only
  an archive-move. It is **unrelated** to this change despite the similar name — it generalises the
  `output/` citation exemption to any gitignored target. It is flagged in `knowledge/STATUS.md`.
  Leave it alone unless the operator asks; do not let the archive step sweep it up.
- The composition-audit ceremony is **DUE** per `knowledge/STATUS.md`. Operator ceremony, not a
  scaffold change. Not yours.
