# shared-lint-layer follow-ons

Parked from `openspec/changes/archive/2026-07-03-shared-lint-layer/notes.md` (verify-outcome
field 5). None are active blockers — all are deferred, monitored, or gated behind a later operator
action.

## `data_lint` strict row-validation deferred

Whether `zip(strict=True)` (fail-loud on ragged CSV) is actually wanted was deferred during C's apply.
The change kept behavior-preserving `strict=False`. A deliberate operator call: fail-loud is safer for
some datasets but would break any pipeline producing uneven-width rows. Revisit when `data_lint`'s CSV
validation gets its first downstream exercise.

## E501 ratchet-back on long-line reflow

`ruff.toml` selects E,F,I,B but `ignore = ["E501"]`, since `ruff format` is authoritative for width and
does not reflow long comments/strings/docstrings. This is marginally narrower than "all of E." Ratchet
E501 back on if a manual long-line reflow pass across the scaffold's prose-heavy `scripts/` is ever done.

## Pinned scanner versions — no CVE-drift auto-bump

Pinned `gitleaks` and `osv-scanner` versions (in `knowledge/reference/security-scanners.md` and
`scripts/install-tools.sh`) have no automated CVE-drift refresh. Dependabot/renovate is a parked operator
decision; until then, bump both `security-scanners.md` and `scripts/install-tools.sh` together by hand.
