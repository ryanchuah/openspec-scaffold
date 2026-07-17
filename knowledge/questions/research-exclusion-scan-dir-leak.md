# research-exclusion configured-scan-dir leak

Parked from `openspec/changes/archive/2026-07-17-handoff-lint-exempt/notes.md` (field-5
"Forward-looking items"). Non-blocking, deferred — pre-existing and explicitly out of scope for that
change.

## The finding

The same class of leak fixed for `knowledge/HANDOFF.md` in `handoff-lint-exempt` also affects the
pre-existing `knowledge/research/` duplicate-block exclusion in `scripts/knowledge_lint.py`.
Reproduced during that change's verify: with `[knowledge_lint] duplicate_scan_dirs = ["."]` (or
similarly configured), a `knowledge/research/` file **is** flagged for `duplicate-content-block`,
even though the normal `knowledge/` walk prunes research files from that check. The extra
`duplicate_scan_dirs` loop re-adds the file, re-arming the same trap the handoff fix closed via a
single chokepoint exclusion in `_duplicate_scan_files`.

## Why it was not fixed there

`handoff-lint-exempt`'s `notes.md` explicitly scoped out changing the `knowledge/research/`
exclusion ("Out of scope: ... Changing ... the `knowledge/research/` exclusion"). The chokepoint
fix that change applied for the handoff (moving the exclusion to the single return point in
`_duplicate_scan_files`) is architecturally the same shape of fix `_is_research` would need, but it
was not applied there.

## Candidate fix

Apply the same chokepoint discipline to `_is_research` (or fold both exclusions into one
chokepoint-level allowlist check in `_duplicate_scan_files`) so no collection path — the normal
`knowledge/` walk, the top-level glob, or a configured `duplicate_scan_dirs` entry — can re-add a
research file. Candidate for the finding-closure ratchet, since the general shape is "an exclusion
applied per-loop rather than at the collection chokepoint" — the same shape already fixed once for
the handoff.

## Priority

Low/monitored. Only trips when a repo's `checks.toml` configures `duplicate_scan_dirs` to include
`.` or `knowledge` explicitly (not the default). Revisit if a downstream repo's config triggers it,
or when `_duplicate_scan_files` is next touched.
