# SMALL plan — exempt gitignored citation targets from knowledge_lint broken-citation check

**Tier:** SMALL. Scaffold-managed linter (`scripts/knowledge_lint.py`) + its unit test.

## Problem statement

`knowledge_lint.py` check 3 (broken prose path citation) flags a backtick citation whose
target does not exist under the repo root. It already exempts one prefix — `output/` — with
the rationale *"ephemeral (generated/gitignored)"* (see `knowledge_lint.py:459-462`). But the
exemption is a single hardcoded literal, so any **other** generated/gitignored path a doc
legitimately cites is flagged the moment the artifact is absent on a clean tree.

This bit psc-monitor: its operator-install docs cite `deploy/rendered/crontab.txt` — a
deploy-time-rendered, **gitignored** file (you install the rendered artifact, not the
template). `deploy/` is a real tracked top-level dir, so the citation clears the first-segment
gate; `rendered/` is gitignored, so after `git clean -x` the file is absent and the live-tree
lint gate (`test_doc_lint_gate::test_knowledge_lint_live_tree_clean`) goes red on a clean
checkout. The citations are correct — the linter's model of "broken" is wrong for
generated artifacts.

## Proposed approach

Generalize the existing `output/` special-case to **any gitignored citation target**. The
`is_ignored` git-check-ignore callable is already built in `collect_findings`
(`make_git_ignore_checker`); thread it into `_check_broken_citations` and, right before the
existence check on `check_token`, skip when `is_ignored(check_token)` is true. A citation to a
generated/gitignored path is not drift — its steady-state absence is expected, exactly the
rationale the `output/` hardcode already encodes.

Keep the literal `first_segment == "output"` guard in place as the **git-unavailable
fallback** (the linter is git-optional by design D2: when `root` is not a git repo,
`is_ignored` always returns `False`). When git is available the general guard subsumes it;
when git is absent the literal keeps `output/` behavior unchanged. Net behavior change: no
regression to any existing case; the newly-exempt set is exactly "targets git actually
ignores."

This is a scaffold-general fix — it introduces **no** psc-monitor-specific path into
scaffold-managed code; `deploy/rendered/` is covered only because git ignores it in that repo.

**Test:** add one unit test to `test_knowledge_lint.py` that `git init`s a `tmp_path`, writes a
`.gitignore` containing `deploy/rendered/`, creates a tracked `deploy/` top-level dir, and a
knowledge doc citing both `deploy/rendered/crontab.txt` (gitignored, absent) and a genuinely
missing non-ignored path. Assert the gitignored citation is NOT flagged and the missing
non-ignored path IS flagged (guards against over-broad suppression). This reproduces the
psc-monitor scenario end-to-end.

## Out of scope

- Any change to psc-monitor's own docs or tree — the fix is in the scaffold linter; psc-monitor
  receives it by the normal operator-gated scaffold sync (see `pending-downstream-propagation.md`).
- Broadening the exemption beyond gitignored targets (e.g. blanket-exempting missing files) —
  drift on tracked paths must still flag.
- Issue 1 (outstanding-work-review residual-sweep skill split) — split into a separate change,
  specified in `knowledge/HANDOFF.md` per operator instruction.
