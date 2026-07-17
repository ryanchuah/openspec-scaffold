# Un-backticked path references dangle invisibly

**Status:** monitored, low priority. Surfaced 2026-07-16 during `reconcile-parked-backlog`.

## The problem

`scripts/knowledge_lint.py`'s broken-prose-path-citation check only inspects **backtick-wrapped**
path-like tokens (a deliberate false-positive guard — see the `knowledge-lint` spec's
`broken-prose-path-citation-flagged` scenario). A bare-prose filename reference — one that never
gets backticks — is invisible to the check and can dangle indefinitely.

## Concrete evidence

`knowledge/questions/lean-boot-context-follow-ons.md:5` cited `parked-follow-ons.md` in bare prose
(no backticks). That file was renamed away during the pre-restructure project-knowledge migration
(the tracked-folder rename to today's `knowledge/` tree) and has not existed since. The bare citation
survived the entire restructure undetected — `knowledge_lint` never flagged it because it only scans
backtick-wrapped tokens — and was found only by hand during `reconcile-parked-backlog`'s apply pass,
which repointed it to `knowledge/questions/parked-psc-monitor.md`.

## Why this isn't fixed here

Widening the check to bare tokens would be noisy: the backtick-only scope is a deliberate
false-positive guard (see the many legitimate non-path backtick tokens the check already has to
skip — `WHEN/THEN/AND`, cross-repo names, GitHub shorthand, etc. — the bare-prose surface is far
wider and noisier still). The realistic mitigation is authoring discipline: always backtick a path
citation. No new mechanism is warranted at this time.

## Disposition

Parked. Revisit if another bare-prose dangling citation is found by hand (a second occurrence would
argue the discipline-only mitigation isn't holding), or if a low-noise way to widen the check is
identified.
