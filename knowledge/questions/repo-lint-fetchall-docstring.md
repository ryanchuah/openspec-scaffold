# repo_lint.py no_fetchall docstring example

From `openspec/changes/archive/2026-07-13-defect-prevention-detectors/notes.md` (assumption A2):

`scripts/repo_lint.py`'s example check docstring (`no_fetchall.py`) currently implies repos should implement their own `.fetchall()` detector — but the scaffold now ships a universal `data-scale` detector in `checks.py` that does this. Update the docstring so it doesn't mislead repos into re-implementing the now-universal check.

**Priority:** Low — OPTIONAL per the change plan. The example is still valid as a `repo_lint.py` illustration; the docstring wording is the only issue.

**Status:** parked — address when the `repo_lint.py` examples are next refreshed.
