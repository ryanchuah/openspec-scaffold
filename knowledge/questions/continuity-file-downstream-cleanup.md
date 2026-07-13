# Handoff-file lint downstream cleanup (parked, operator-gated)

**Source:** `openspec/changes/archive/2026-07-13-outstanding-and-continuity-hardening/`
(decision `handoff-file-lint-widened` in `knowledge/decisions/INDEX.md`).

**What changed:** `knowledge_lint.py`'s handoff-file check widened from a root-only,
case-sensitive `HANDOFF*`/`HANDOVER*` prefix match to a repo-wide, case-insensitive substring
match over the whole tree (respecting gitignore), with `knowledge/HANDOFF.md` as the sole
sanctioned exemption. This is a strict, non-opt-outable reservation of the token
`handoff`/`handover` in filenames — deliberate (see the archived change's notes.md
"strict-reservation trade-off").

**Why parked, not active:** the widened check is scaffold-only today. Nothing in the scaffold
repo itself is blocked. But both downstream repos carry handoff-named files in non-gitignored
paths that the OLD root-only check never saw:

- **extrends** — roughly 27 handoff-named files, mostly under `plans/*-handoff.md`.
- **psc-monitor** — some handoff-named files in non-gitignored paths (untracked root handoff
  files were already noted separately in `knowledge/STATUS.md`'s extrends follow-on list; this
  item is about the broader repo-wide sweep in each downstream repo, not just the root).

**The coupling:** propagating the widened lint (`scripts/sync_scaffold.py`) to either downstream
repo BEFORE that repo's handoff-named files are renamed/archived under the strict
single-token-reservation rule will turn that repo's live-tree pytest gate red on next commit —
the widened check will flag every one of those files. So:

1. Cleanup (rename or archive the offending files, respecting the strict reservation — no
   opt-out marker exists for a filename check) must happen first, or in the same pass as the sync.
2. The sync itself is a separate, operator-gated action (per the existing downstream-propagation
   convention recorded in `knowledge/STATUS.md`'s Immediate next action).

**Disposition:** do nothing until the operator explicitly authorizes downstream propagation of
this change. When that happens, do the per-repo cleanup and the `sync_scaffold.py` run together
(or cleanup first), not sync-then-cleanup.
