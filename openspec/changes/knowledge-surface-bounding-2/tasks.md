# tasks — knowledge-surface-bounding-2

> Read `notes.md` first (acceptance criteria, budgets, thresholds, design decisions D1–D4).
> **Precondition (orchestrator-performed BEFORE apply, NOT an executor task):** `knowledge/STATUS.md`
> `## Immediate next action` has been pruned to ≤550 words and `knowledge/reference/pending-downstream-propagation.md`
> created, so the new status_lint C3 gate is already green on the live tree. Do NOT edit `knowledge/STATUS.md`
> or create that reference doc — they are already done. Your job is the code/tests/scripts below.
> All `scripts/*.py` are invoked as `/usr/bin/python3 scripts/<name>.py` (no execute bit; bare path → exit 126).

## 1. status_lint per-section word budgets (C3)

- [x] 1.1 In `scripts/status_lint.py`, replace the `EXEMPT_HEADINGS` frozenset (currently lines
  ~38-45) with a dict mapping each normalized cap-exempt heading to a max-word budget. Name it
  `EXEMPT_HEADING_BUDGETS`. Exact contents:
  ```python
  EXEMPT_HEADING_BUDGETS: dict[str, int] = {
      "current state": 500,
      "immediate next action": 550,
      "done": 300,
      "pointers": 200,
  }
  ```
- [x] 1.2 In `_check_status_md` (currently ~line 127), keep the C1/C2 partition byte-for-byte
  equivalent by changing only the membership test: the exempt check becomes
  `if norm in EXEMPT_HEADING_BUDGETS:` (dict-key membership == old frozenset membership). C1 (`> 3`
  cap) and C2 (`> 150` change-entry word budget) logic and thresholds are UNCHANGED.
- [x] 1.3 In `_check_status_md`, add the **C3** check: iterate the split `sections` again for exempt
  sections. In the loop body, first bind `norm = _normalize_heading(heading)`; skip the section
  unless `norm in EXEMPT_HEADING_BUDGETS`; then for each PRESENT budgeted section compute
  `wc = _word_count(_remove_fenced_code_blocks(body))` and, if `wc > EXEMPT_HEADING_BUDGETS[norm]`,
  append a violation string in the same shape as C2, e.g.
  `f"  knowledge/STATUS.md: {heading} body has {wc} words (max {EXEMPT_HEADING_BUDGETS[norm]})"`.
  Reuse the existing helpers — do NOT add new word-count/fence-strip logic. A budgeted heading that
  is ABSENT from STATUS.md contributes no violation (only present sections are checked). A separate
  C3 pass over `sections` is fine at this scale (≤4 exempt sections); no need to fold it into the
  C1/C2 partition loop.
- [x] 1.4 Update the `scripts/status_lint.py` module docstring (lines ~1-25) to describe C3 and the
  per-section budget map alongside the existing C1/C2 description. Keep the "Exit codes 0 / 2"
  section accurate (C3 is a hard violation → exit 2, same as C1/C2).
- [x] 1.5 In `scripts/test_status_lint.py` (stdlib `unittest`; helpers `_make_repo`, `_n_words`,
  `_make_archive_dir`): add C3 tests mirroring the existing C2 over/under/exact-boundary +
  fence-excluded shape. **Cover all four exempt headings** (the superseded
  `test_exempt_sections_skip_c2` covered all four): for EACH of `current state` (500),
  `immediate next action` (550), `done` (300), `pointers` (200), assert a body of `_n_words(budget+1)`
  → exit 2 and `_n_words(budget)` → exit 0 (at budget passes). Additionally, for at least one heading,
  assert `_n_words(budget-1)` → exit 0 and that a fenced code block padding the body is excluded from
  the count. Replace the now-superseded `test_exempt_sections_skip_c2` (currently ~line 191) with
  these per-section budget tests (an exempt section OVER its budget must now FAIL, inverting that old
  assertion). Keep all C1/C2 and `HelperTest` cases and their asserted outcomes unchanged. Add one
  test that a section whose heading is NOT a recognized exempt heading is still treated as a
  change-entry (C1/C2), not budget-exempt.

## 2. boot_surface_lint.py + tests

- [x] 2.1 Create `scripts/boot_surface_lint.py`, stdlib-only (`argparse`, `sys`, `pathlib`), mirroring
  `status_lint.py`'s shape (module docstring with an "Exit codes" section; `main(argv: list[str] |
  None = None) -> int`; `repo_root` optional positional defaulting to
  `Path(__file__).resolve().parent.parent`; `if __name__ == "__main__": sys.exit(main())`). Behavior:
  - Module constants:
    ```python
    BOOT_FILES = (
        "AGENTS.md",
        "knowledge/STATUS.md",
        "knowledge/questions/INDEX.md",
        "knowledge/decisions/INDEX.md",
    )
    WARN_BYTES = 80_000
    FAIL_BYTES = 100_000
    ```
  - Sum `(.stat().st_size)` for each `BOOT_FILES` path that exists under `repo_root`; a missing file
    is skipped (contributes 0, NOT an error).
  - Verdict + exit code: `total < WARN_BYTES` → print clean, return `0`; `WARN_BYTES <= total <
    FAIL_BYTES` → print a WARN line, return `1`; `total >= FAIL_BYTES` → print a FAIL line, return `2`.
  - Console output: one line per present file (`  <path>: <bytes>`), a `total: <bytes>` line, and a
    final verdict line naming the crossed threshold. Keep output shape consistent with `status_lint`'s
    `boot_surface_lint: OK|WARN|FAIL` style.
- [x] 2.2 Create `scripts/test_boot_surface_lint.py` (stdlib `unittest`, mirroring
  `test_status_lint.py`'s tempfile pattern; `sys.path.insert` + `import boot_surface_lint`):
  - Add a small helper for constructing a temp repo whose `BOOT_FILES` have exact byte sizes — e.g.
    `def _make_boot_repo(tmpdir: Path, sizes: dict[str, int]) -> Path:` that, for each
    `BOOT_FILES`-relative path in `sizes`, creates parent dirs and writes `"x" * n` bytes (ASCII, so
    bytes == chars); a path omitted from `sizes` is left absent (to exercise the missing-file branch).
  - Fixture unit tests using that helper with controlled sizes: total under 80,000 → `main`
    returns 0; total in `[80_000, 100_000)` → returns 1; total ≥ 100,000 → returns 2; **boundary**
    exactly 80,000 → 1 (WARN side) and exactly 100,000 → 2 (FAIL side); a missing boot file (e.g. no
    `knowledge/decisions/INDEX.md`) is skipped without error and still returns a verdict.
  - A **live-tree gate** `test_boot_surface_live_tree_not_fail` asserting
    `boot_surface_lint.main([str(REPO_ROOT)]) != 2` where `REPO_ROOT =
    Path(__file__).resolve().parent.parent` — assert only that the FAIL threshold is NOT crossed (a
    non-blocking WARN must not redden the suite). Do NOT assert `== 0`.

## 3. Manifest + exit-codes doc

- [x] 3.1 Add two lines to `scripts/scaffold_manifest.txt` under the `# Scripts` banner (plain
  repo-relative path, no trailing comment): `scripts/boot_surface_lint.py` on the line **after** the
  existing `scripts/status_lint.py` line, and `scripts/test_boot_surface_lint.py` on the line
  **after** the existing `scripts/test_status_lint.py` line.
- [x] 3.2 Add `scripts/boot_surface_lint.py`'s exit-code convention (`0` clean / `1` WARN, advisory /
  `2` FAIL, blocking) to `knowledge/reference/exit-codes.md`, matching that file's existing per-tool
  entry format. (If the file has no per-script section yet, add a short one consistent with how
  `status_lint`/`check.sh` are documented there.)

## 4. Green gate

- [x] 4.1 Run `ruff check --fix` and `ruff format` on every file you touched, then run
  `bash scripts/check.sh` and confirm it exits 0 (ruff + format + full `pytest -q`, including the two
  new live-tree gates: `status_lint` C3 clean on the pre-pruned STATUS.md, and `boot_surface_lint`
  not-FAIL on the live tree). If any stage is non-green, STOP and report the failing stage name and
  its output back to the orchestrator — do NOT edit `knowledge/STATUS.md` to force it green (the
  prune is already done by the orchestrator).
