# delegated-agent-safety follow-ons

Decision record: `knowledge/decisions/INDEX.md` (2026-07-03 entries `verifier-bash-denylist-speedbump`,
`knowledge-handoff-file`, `sync-drift-beacon`). Full narrative in
`openspec/changes/archive/2026-07-03-delegated-agent-safety/notes.md`.

## Literal-spelling bypass is fundamentally incomplete (accepted residual, not fixed)

The verify verifier's `bash:` denylist matches literal command spelling, not command identity. A
path-prefixed binary (`/usr/bin/rm`), a version-suffixed interpreter (`python3.11 -c` on another
host), a multiplexer/unenumerated wrapper (`busybox rm`, `nohup rm`, `timeout 5 rm`), or an unlisted
file-writing tool (`rsync`, `patch`, `ex`) all run under the catch-all `"*": allow`. This is not
closable by enumeration. The real backstop is repo-level data isolation (test-DB fixtures, blanked
live credentials, a backup of any irreplaceable store) — a downstream-repo concern, not expressible
in the scaffold verifier's permission configuration. Revisit only if a real incident recurs through
one of these vectors.

## `knowledge/HANDOFF.md` shares STATUS.md's trust model re: prompt injection

`knowledge/HANDOFF.md` is a boot-read file, same as `knowledge/STATUS.md` — it is git-tracked and
reviewable, so it is not a *new* injection surface beyond the existing boot files. Noted for
completeness, not a new mitigation requirement.
