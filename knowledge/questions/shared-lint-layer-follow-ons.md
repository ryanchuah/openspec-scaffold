# shared-lint-layer follow-ons

Parked from `openspec/changes/archive/2026-07-03-shared-lint-layer/notes.md` (verify-outcome
field 5). None are active blockers — all are deferred, monitored, or gated behind a later operator
action.

## `<!-- lint:planned -->` marker — SHIPPED; extrends D1 follow-on owed

The `<!-- lint:planned -->` inline suppression marker was added to scaffold `knowledge_lint` by C
(committed `ddbeb65`). It lets a doc deliberately forward-reference a not-yet-created file without
tripping the commit gate. D1 specifically owes: apply the marker (or reword) to extrends' 2
forward-references (`scripts/_autolabel_v2_oneoff.py`, `config/subreddits_general.yaml`) once C  <!-- lint:planned -->
syncs, so extrends' `knowledge_lint` reaches zero and its live-tree gate can go green. Also: document
the marker convention for authors.

## `output/` ephemeral skip — consider `.gitignore`-aware general form

The current `output/` skip is a hardcoded first-segment prefix — it catches `output/digest-2026-W25.md`
but not an `output/` path nested deeper. A `.gitignore`-aware general form (checking whether the
resolved path is `git check-ignore`-d, or matching `.gitignore` patterns directly) would be more
robust. Deferred; the hardcoded prefix covers the common case.

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

## Commit-test-gate wiring-smoke doc — note stdin command-detection

The hook now has a stdin command-detection layer (reads PreToolUse JSON, classifies tokens, gate fires
only on real `git commit`). The gated-session smoke procedure in `tests/commit-gate-smoke/README.md`
could note verifying this new layer, adding a step to confirm that complex non-commit Bash carrying
`git commit` as a substring no longer trips the gate.
