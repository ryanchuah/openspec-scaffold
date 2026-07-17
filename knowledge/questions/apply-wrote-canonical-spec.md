# An apply-executor wrote directly to `openspec/specs/`, bypassing archive promotion

**Status:** monitored, low priority. Surfaced 2026-07-17 during `reconcile-parked-backlog`, found by
the archive-executor (not by any check).

## What happened

`reconcile-parked-backlog`'s task 3.2 instructed the apply-executor to *"update the
`outstanding-work-view` spec (~lines 88-91)"* — i.e. to edit the **canonical**
`openspec/specs/outstanding-work-view/spec.md` during **apply**. The same change also carried a
proper MODIFIED delta for that requirement, to be promoted at archive.

So the same requirement was rewritten twice by two different paths: once directly at apply (commit
`aba963f`), once by the archive-time merge. At archive the executor found the canonical spec already
carried the change and flagged it.

**No harm this time:** the two versions were diffed and are word-identical — only line-wrapping and a
trailing blank line differed. The delta and the canonical spec agree.

## Why it matters anyway

The convention is that `openspec/specs/` is written **only at archive**, by promoting the change's
delta specs. Editing it during apply breaks that in two ways:

1. **Divergence risk.** Had the direct edit and the delta drifted, the canonical spec would silently
   hold something the frozen, reviewed delta never said — and the archive-time merge would have had
   to reconcile two competing sources with no obvious winner. That the two matched here was luck
   (both were written from the same intent in the same session), not a guarantee.
2. **It voids the delta's purpose.** The delta is the reviewed contract; promotion is the controlled
   application of it. A direct edit applies an unreviewed version of the same change ahead of the gate.

## Root cause

Task-authoring, not executor error — the executor did exactly what task 3.2 said. The task was
written before the change's delta specs existed (the deltas were added later, when `openspec validate`
demanded ≥1 delta), and the redundancy was never noticed.

**The authoring rule:** when a change alters spec'd behavior, write the **delta spec** and let archive
promote it. Do not also instruct apply to edit `openspec/specs/` — the only apply-phase spec write is
the delta under the change dir.

## Disposition

Open, low priority — one observed instance, no damage. Worth considering if it recurs:

- A deterministic check could plausibly flag a non-archive commit whose diff touches
  `openspec/specs/`, but keying "is this an archive commit" reliably is the hard part, and a
  false-positive here would block legitimate archive promotion. Not obviously worth building for a
  single instance.
- Cheaper mitigation: the propose-time reviewer already reads `tasks.md` — a task instructing a write
  to `openspec/specs/` is a reviewable smell. It was simply not looked for.
