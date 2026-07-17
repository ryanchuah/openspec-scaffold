# correctness-audit-skill follow-ons

Parked forward-looking items surfaced during the OW-5 verify pass (2026-07-13). None of
these are blockers — see `knowledge/decisions/INDEX.md` (`correctness-audit-skill`,
`audit-dossier-lint-marker-gated`) for the shipped decision rationale.

1. **Dossier-lint format-robustness limits (v1, by design).** `_check_audit_dossier`'s
   census check parses ONLY pipe-separated rows with no leading pipe. Tab-separated
   rows are silently skipped; a markdown-table census (leading `|` + a `---` separator
   row) would mis-column the disposition / false-positive on the separator row. The
   documented format is pipe-no-leading-pipe. Candidate future hardening if a
   downstream repo authors a census as a markdown table.

2. **Template↔parser round-trip not test-enforced — the one generalizable class.** No
   test extracts the SKILL's fenced CENSUS/FINDINGS template block and runs it through
   the lint, so a future SKILL-template edit that drifts from the parser has no
   deterministic catch (same class as "graduation log not lint-enforced" below).
   Concrete fix available: a test that extracts the fenced template and asserts it
   lints clean. Candidate `test:` follow-on for the finding-closure ratchet — decide
   disposition (check/test/waiver/open) when this is next picked up.

3. **`(c)` parser fragility.** A stray `### ` subheading inside a finding body
   truncates entry-collection and could skip the Prior/Class check (false negative);
   "graduated" is keyed off the FINDINGS evidence label, not the census disposition (a
   census `AUDITED-finding` left `LEAD` in FINDINGS escapes the check). Both require
   non-template input; low priority.

4. **Merge the two `FINDINGS*.md` read loops in `_check_audit_dossier`** into a single
   pass — behavior-preserving, low value on tiny files. Routed to the existing
   `ratchet-lint-cleanup` parked follow-on (`knowledge/questions/ratchet-lint-cleanup.md`)
   rather than tracked separately here.

5. **Carried from freeze (reconfirmed at verify).**
   - Graduation log is not lint-enforced (D8 scopes to core format checks, by design);
     a future audit shipping without one is a drift signal for
     `knowledge-drift-review`, not `knowledge_lint`.
   - First-real-audit manual check (not unit-testable): confirm wave-gate triage-file
     appends keep graduated findings out of the `untriaged-finding-stale` bucket
     during a live audit.
