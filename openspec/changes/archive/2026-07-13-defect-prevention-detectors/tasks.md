# tasks — defect-prevention-detectors (OW-1 + OW-4)

Apply-phase edits only. Acceptance criteria + architecture: `notes.md`; deciding facts +
checks.py anchors: `recon-digest.md`. Spec deltas are already authored under `specs/` — do NOT
re-author them; implement code to match them. The **tests pin exact behavior** — where a rule is
ambiguous, make the positive fixture flag and the negative fixture not-flag.

## Group 1 — checks.py: the two detectors (in-process AST builtins)

- [x] **T1 — Registry entries.** In `scripts/checks.py` `_REGISTRY` (~L198-254) add two entries:
  `{"name":"test-quality","tier":"floor","kind":"builtin","family":"check", "trigger":"python test files present", "coverage_note":"disabling drops test-quality detection"}`
  and `{"name":"data-scale","tier":"floor","kind":"builtin","family":"check", "trigger":"python source present","coverage_note":"disabling drops unbounded-query detection"}`.
  Place them near the other floor check-family builtins (after `ruff`/before `inventory` is fine);
  registry order is load-bearing for `--list`, so mirror it in the tests (T8).

- [x] **T2 — Availability special-case.** In `_availability_for_check` (~L417-429) special-case both
  new names to return `available` unconditionally (same as `inventory` at L426-427) — they run
  in-process AST, no external binary, so they must NOT hit `_BUILTIN_TOOL_BIN[name]` (KeyError).

- [x] **T3 — Autodetect defaults (enabled).** In `_autodetect_defaults` (~L301-323) add
  `test-quality: True` and `data-scale: True` (enabled by default; they are pure-AST, near-zero-FP,
  advisory). Trigger presence is Python files existing (both scan `.py`); keep it simple — default
  enabled, `[checks.<name>].enabled=false` overrides via `_is_enabled`.

- [x] **T4 — In-process execution dispatch (REVISED per review R1 🔴1+🔴2).** Do NOT mirror the
  `inventory` special-case in `_execute_check` (inventory has zero findings and skips path
  normalization). Instead register the two detectors in **`_BUILTIN_RUNNERS`** (~L920-928) so the
  normal builtin `else` branch (~L1138-1147) handles them uniformly — that branch already calls
  `_normalize_finding_paths` (repo-relative rewrite, REQUIRED — the `_fingerprint` at ~L1185-1193
  keys on repo-relative `path`) and builds the record from the runner's outcome. Register
  `test-quality→_run_test_quality`, `data-scale→_run_data_scale`, matching the existing
  `_BUILTIN_RUNNERS[name](check, config, out_path)` signature.
  **The runner MUST return the OUTCOME dict shape the record-builder expects** (same as other
  `_BUILTIN_RUNNERS` entries), which INCLUDES a `"findings"` key (the list of
  `{check,rule,path,line,message}` dicts) — NOT the `{check,status,count,artifact}` record shape.
  (The else-branch OVERRIDES `count` from the findings length and IGNORES `artifact` — using
  `str(out_path)` — so `findings` is the only load-bearing key; `status` should still be set.)
  `_execute_check` extracts `outcome["findings"]` into the record's `_findings` for the aggregate
  `findings.json`; omitting `findings` makes the detector's findings silently vanish from the
  aggregate + baseline diff. Each runner writes its own findings JSON artifact to `out_path` AND
  returns `{status, count, findings, artifact}`. Because these are in-process (no external binary),
  their `_run_*` functions do their AST work directly and do NOT call `_run_builtin_tool_json` /
  `_BUILTIN_TOOL_BIN` (which T2's availability special-case also avoids).
  **Resume (R1 🟡3):** the `--resume` recovery guard (~L1379) gates finding-recovery on
  `_PARSERS` membership. These detectors write recoverable artifacts, so register them so resume
  recovers their findings — add `"test-quality"` and `"data-scale"` to `_PARSERS`. **The value MUST
  be CALLABLE** (R2 🟡1): `_PARSERS[name]` is invoked as `_PARSERS[name](result.stdout)` at ~L791 in
  `_run_builtin_tool_json`, so `None` would crash if ever routed there — use a safe callable no-op
  (e.g. `lambda _stdout: []`). The detectors don't go through `_run_builtin_tool_json` (they run AST
  directly), so the value is exercised only by the resume-membership path in practice, but keep it
  callable to be refactor-safe.

- [x] **T5 — Scoping helpers.** Add two small helpers (R2 💡2: keyword-only bool params
  `tests_only`/`source_only`, exactly one True per call):
  `_iter_py_files(paths, *, tests_only=False, source_only=False)` walking each configured path's `.py` files,
  where a **test file** = basename matches `test_*.py` OR `*_test.py` (pytest discovery). Exclude
  common non-source dirs already excluded elsewhere if any (`.venv`, `.git`, `__pycache__`).
  `test-quality` iterates tests_only; `data-scale` iterates source_only (NOT test files).

- [x] **T6 — `_run_test_quality` (AST).** For each test file, parse with `ast` and emit a finding per
  match. Rules (stable `rule` slugs), each with the message noted:
  - `assert-true` — `ast.Assert` whose `test` is `ast.Constant(value=True)`. msg: "tautological `assert True`".
  - `assert-or-true` — `ast.Assert` whose `test` is `ast.BoolOp(ast.Or)` with any operand
    `ast.Constant(value=True)`. msg: "forced-green `assert ... or True`".
  - `empty-test` — `ast.FunctionDef` whose name startswith `test` and whose body, after dropping a
    leading docstring `Expr(Constant str)`, is empty or only `ast.Pass`. msg: "empty test body (no assertions)".
  - `unfrozen-clock` — inside a `test_*` function, a `Call` to attr `now`/`utcnow` (on a `datetime`
    name/attr) or `time.time`/`time.monotonic`. msg: "unfrozen clock in test — freeze it for determinism".
  - `self-mock` — a `Call` to `patch`/`patch.object`/`mock.patch` whose FIRST **string-literal** arg's
    root dotted component equals the module-under-test derived from the filename
    (`test_<m>.py`→`<m>`, `<m>_test.py`→`<m>`); skip if the target is not a string literal or no
    module-under-test is derivable. msg: "test mocks the module under test (self-mock)".
    **Note (R1 🟡4):** this catches only the string-literal target form; the common
    `patch.object(<ModuleObj>, "attr")` form takes an `ast.Name`/`ast.Attribute` first arg and is
    deliberately NOT detected (would require import resolution → FP risk). Low recall, near-zero FP —
    do not spend effort detecting `ast.Name` targets.
  - `unfrozen-clock` and `discarded-return-flag` are **ADVISORY** (higher FP than the others — see
    below); prefix their messages with `advisory: `.
  - `discarded-return-flag` (ADVISORY, documented FP) — an `ast.Assign` inside a `test_*` function
    whose target is an `ast.Tuple` containing an `ast.Name(id="_")` and whose value is an `ast.Call`.
    msg: "advisory: discarded return value (`, _ =`) — a returned status may be dropped (many uses are legitimate, e.g. `x, _ = divmod(...)`)".
  Line = the node's `lineno`. One finding per site. **Noise note (R1 🟡6):** `unfrozen-clock` and
  `discarded-return-flag` will be the noisiest rules; a per-rule enable/disable toggle is a v2
  follow-on (see notes.md A3) — v1 ships them advisory-labeled and enabled, and a repo drowning in
  them can disable the whole detector via `[checks.test-quality] enabled = false`.

- [x] **T7 — `_run_data_scale` (AST).** For each non-test source file, parse with `ast`; emit
  `unbounded-fetchall` for each `Call` whose `func` is `ast.Attribute(attr="fetchall")`. msg:
  "unbounded `.fetchall()` — record an at-scale run or a bounded-domain argument in notes.md, or add a LIMIT/pagination". Line = call `lineno`.

## Group 2 — Tests (the behavioral contract)

- [x] **T8 — Registry/list/autodetect tests.** In `scripts/test_checks.py`: update
  `ListModeTest.expected_names` (~L198-224) to include `test-quality` and `data-scale`; update
  `AutodetectTest` (~L241-261) to assert both are enabled by default. **Also (R1 🟡5):** add
  `"test-quality:"` and `"data-scale:"` to the `SummaryLineFormatTest` startswith filter tuple
  (~L863-872) so their summary-line format is covered.

- [x] **T9 — test-quality finding + scoping tests.** Add tests that write a real `test_sample.py`
  into the temp repo (`self.repo`) containing one positive case per rule, run `--check test-quality`,
  and assert `rc==2` + a finding with the expected `rule`/`line` for each (use the
  `NormalizedFindingsTest._run_single_check` pattern, generalized to multiple findings). Add a
  NEGATIVE test: a non-test file (`sample.py`) with `assert x or True` and `datetime.now()` produces
  ZERO test-quality findings (scoping). Include an `empty-test` and `self-mock` (write
  `test_widget.py` that patches `widget.foo`) positive case.

- [x] **T10 — data-scale finding + scoping tests.** Write a non-test `db.py` with
  `rows = cur.fetchall()` → assert `--check data-scale` yields `rc==2` + `unbounded-fetchall` at the
  right line. NEGATIVE: a `test_db.py` with `.fetchall()` yields ZERO data-scale findings.

## Group 3 — Verify-skill wiring (match the spec deltas)

- [x] **T11 — Concrete detector wiring in the lens prompts.** In
  `.claude/skills/openspec-verify-change/SKILL.md`, update the test-quality lens (~L97-110) and
  data-scale lens (~L112-121) prompts so each first instructs the verifier to run
  `checks.py --check test-quality` (resp. `--check data-scale`) and confirm its findings from disk,
  THEN apply the residual lens judgment. Update the "Forward-compatibility" line (~L125) to state the
  detectors now exist (no longer "when it ships"). Match the MODIFIED `verify-multimodel-gate` delta.

- [x] **T12 — Data-path verify RULE.** In the same skill, add a conditional gate block modeled on the
  security-review gate (~L157-164): "When a change modifies a data path … verify SHALL require
  `notes.md` to record either an at-scale run or a bounded-domain argument." Cite the canonical
  `AGENTS.md` "Mind data scale" span + `openspec/config.yaml rules.verify` — do NOT restate them.
  Match the ADDED `verify-multimodel-gate` delta requirement.

## Group 4 — Optional + gate

- [x] **T13 (OPTIONAL, park if not cheap) — repo_lint.py example.** Consider updating
  `scripts/repo_lint.py`'s `no_fetchall.py` docstring example to note that data-scale is now a
  universal checks.py detector (so repos don't re-implement it). Skip if it risks the repo_lint
  tests; not load-bearing.

- [x] **T14 — Green gate.** Run `bash scripts/check.sh` → exit 0 (ruff + format + pytest). Run
  `ruff check --fix` + `ruff format` on every edited `.py`. **Self-findings check:** run
  `python -m pytest -q -k checks` and also invoke `checks.py --check test-quality` and
  `--check data-scale` on THIS repo; if the scaffold's own test files trip a rule, confirm NO
  existing test asserts a global "zero findings" that would now break, and note any real self-finding
  in the completion report for triage (advisory, must not red the suite). Do NOT commit.
  **(R1 💡9)** EXPECT `scripts/test_checks.py` to produce self-findings (especially `self-mock` /
  `discarded-return-flag` / `unfrozen-clock`) — that is fine and advisory; the check is only that no
  EXISTING test asserts global zero-findings on the scaffold.
