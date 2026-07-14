# product-audit-skill follow-ons (OW-16, shipped 2026-07-14)

Decision record: `knowledge/decisions/INDEX.md` (`product-audit-skill`). Archive:
`openspec/changes/archive/2026-07-14-product-audit-skill/`.

Non-blocking items surfaced during verify (notes.md field 5), none gating other work:

- **Optional sha256-recompute helper.** A small script to reduce claims-ledger maintenance friction
  (recompute-and-rewrite the manifest's hash rows) is not built; the skill inlines the raw `sha256sum
  <path>` command instead. Candidate future extension, non-blocking (design.md Open Questions).
- **Claims-ledger location is fixed.** The staleness detector globs `knowledge/reference/*.md`; a repo
  needing an alternate home for the ledger is a future extension, not supported today (notes.md
  assumption A1).
- **Staleness fires on any content change, by design.** The lint flags a covered file whose content
  drifted at all, including trivial/cosmetic edits — a conservative false-positive bias accepted
  deliberately (design.md Risks). Monitored; revisit only if the noise is observed to be a problem in
  practice.
- **Manifest completeness is deliberately un-linted.** A promise-surface file that exists on disk but is
  absent from the ledger's manifest is not flagged — coverage is left to operator judgment, not
  mechanized (design.md Decision 2). Revisit only if downstream drift is observed.

Infra/process note (not a product item): the `deepseek/deepseek-v4-pro` behavioral verifier emitted tool
calls but zero text/verdict in both attempts this session (original + focused re-run); the behavioral
verify pass was completed by a Sonnet subagent fallback per the verify ladder, which returned a clean
independent READY. If the pro-tier verifier keeps failing to emit verdicts across future sessions, the
verify multi-model chain needs investigation (the pro-tier premise/proposal reviews worked fine this
session — only the behavioral pass failed to emit text).
