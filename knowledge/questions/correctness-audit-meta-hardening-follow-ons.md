# correctness-audit-meta-hardening follow-ons (OW-15, shipped 2026-07-14)

Full decision → `knowledge/decisions/INDEX.md` (`correctness-audit-meta-hardening`). Full evidence →
the archived change's `notes.md`
(`openspec/changes/archive/2026-07-14-correctness-audit-meta-hardening/notes.md`).

## (a) Liveness substring-match false-negative (monitored, low priority)

`_check_audit_liveness` uses substring membership: a dossier `correctness-audit-2026-07` is
considered "referenced" if the Active section contains any longer token embedding it (e.g.
`correctness-audit-2026-07-appendix`, or a reference to that audit's own `-triage.md`). Benign
under the unique `YYYY-MM` naming and because a same-audit triage reference legitimately surfaces
the audit. A word-boundary match is the follow-on if this ever bites in practice.

## (b) Delta-4 ledger lint is well-formedness-only (deferred scope)

The `post-close-ledger-format` check validates line format when a `POST-CLOSE-LEDGER.md` is
present; it does NOT enforce "a ledger must exist after close-out" — that needs a git-diff-since-
close analysis, out of scope for a deterministic `knowledge_lint` check. The should-exist
obligation rests on the coverage-gap review + operator (a protocol SHALL, not a lint). Candidate
follow-on if the "audit closed but no ledger seeded" gap is ever observed downstream.

## (c) Ledger "at least five" vs "exactly five" cell tolerance (monitored)

Chose the false-positive-safe "at least five, each non-empty" posture (rationale pinned in the
archived change's `tasks.md` §2.1 + `review-log.md`). Monitored; revisit only if a concrete
trade-off surfaces (e.g. a malformed line with exactly the right cell count still passing).
