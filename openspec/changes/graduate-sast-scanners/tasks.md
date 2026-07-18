# Tasks — graduate-sast-scanners

Apply-phase implementation only. Implement top-to-bottom, checking off each task. Every runner
argv and parser key-path is pinned below (resolving the direction-gate 🟡 questions) — do not
improvise them. After each touched file, run `ruff check --fix` + `ruff format` on it.

## 1. `scripts/checks.py` — register `bandit` + `semgrep` as built-in parsed checks

- [x] 1.1 Add two `_REGISTRY` entries in the **heavy-tier block, immediately after the `vulture`
  entry and before `index-coverage`** (registry order is load-bearing for `--report` execution
  order):
  ```python
  {
      "name": "bandit",
      "tier": "heavy",
      "kind": "builtin",
      "family": "check",
      "trigger": "always (enabled explicitly)",
      "coverage_note": "disabling drops Python security (SAST) scanning",
  },
  {
      "name": "semgrep",
      "tier": "heavy",
      "kind": "builtin",
      "family": "check",
      "trigger": "always (enabled explicitly)",
      "coverage_note": "disabling drops SAST pattern scanning",
  },
  ```
- [x] 1.2 In `_autodetect_defaults`, add to the returned dict (default-disabled — the
  jscpd/vulture opt-in pattern): `"bandit": False,` and `"semgrep": False,`.
- [x] 1.3 In `_BUILTIN_TOOL_BIN`, add: `"bandit": "bandit",` and `"semgrep": "semgrep",`.
- [x] 1.4 Add parser `_parse_bandit` (Bandit `-f json` nests findings under `results[]`):
  ```python
  def _parse_bandit(raw: str) -> list[dict]:
      data = json.loads(raw) if raw.strip() else {}
      findings = []
      for item in data.get("results", []) or []:
          findings.append(
              {
                  "check": "bandit",
                  "rule": item.get("test_id") or "",
                  "path": item.get("filename") or "",
                  "line": item.get("line_number"),
                  "message": item.get("issue_text") or "",
              }
          )
      return findings
  ```
- [x] 1.5 Add parser `_parse_semgrep` (Semgrep `--json` nests findings under `results[]`, with
  `start.line` and `extra.message`):
  ```python
  def _parse_semgrep(raw: str) -> list[dict]:
      data = json.loads(raw) if raw.strip() else {}
      findings = []
      for item in data.get("results", []) or []:
          start = item.get("start") or {}
          extra = item.get("extra") or {}
          findings.append(
              {
                  "check": "semgrep",
                  "rule": item.get("check_id") or "",
                  "path": item.get("path") or "",
                  "line": start.get("line"),
                  "message": extra.get("message") or "",
              }
          )
      return findings
  ```
- [x] 1.6 Register both in `_PARSERS`: `"bandit": _parse_bandit,` and `"semgrep": _parse_semgrep,`.
- [x] 1.7 Add runner `_run_bandit` (Bandit writes JSON to **stdout** with `-f json`; it exits 1
  when it finds issues, but `_run_builtin_tool_json` parses stdout regardless of exit code, so no
  special exit-code handling is needed):
  ```python
  def _run_bandit(check: dict, config: dict, out_path: Path) -> dict:
      cmd = [
          "bandit",
          "-f",
          "json",
          "-q",
          *_check_args("bandit", config),
          "-r",
          *_check_paths("bandit", config),
      ]
      return _run_builtin_tool_json("bandit", cmd, out_path)
  ```
- [x] 1.8 Add runner `_run_semgrep` (Semgrep writes JSON to **stdout** with `--json`; the repo
  supplies its ruleset via `[checks.semgrep].args`, e.g. `args = ["--config", "<ruleset>"]`; a
  deprecation notice, if any, goes to stderr and does not pollute the parsed stdout):
  ```python
  def _run_semgrep(check: dict, config: dict, out_path: Path) -> dict:
      cmd = [
          "semgrep",
          "--json",
          "--quiet",
          *_check_args("semgrep", config),
          *_check_paths("semgrep", config),
      ]
      return _run_builtin_tool_json("semgrep", cmd, out_path)
  ```
- [x] 1.9 Register both in `_BUILTIN_RUNNERS`: `"bandit": _run_bandit,` and
  `"semgrep": _run_semgrep,`.
- [x] 1.10 Do **NOT** add `bandit`/`semgrep` to `EXPECTED_TOOL_VERSIONS` — leaving them out is
  what keeps their version recorded-not-gated (the ruff/deptry/radon/vulture Python-ecosystem
  posture).
- [x] 1.11 Update the module docstring:
  - Add `bandit` and `semgrep` to the built-in PARSED-checks enumeration (the paragraph beginning
    "Built-in PARSED checks (native output -> normalized finding …)").
  - In the Python-ecosystem-tools sentence, change "(ruff, deptry, radon,\nvulture)" to
    "(ruff, deptry, radon, vulture, bandit, semgrep)".
  - Add one sentence: `bandit` and `semgrep` are default-disabled opt-in SAST security checks
    (enable per repo via `[checks.<name>] enabled = true`); `semgrep` additionally requires a
    ruleset supplied via `[checks.semgrep] args = ["--config", "<ruleset>"]`.
- [x] 1.12 Update the two stale "seven parsers" code comments (bandit + semgrep now funnel through
  `_normalize_finding_paths` too, making it nine): in `_normalize_finding_paths` (the comment
  "means all seven parsers (ruff, gitleaks, osv-scanner, deptry, radon, jscpd, vulture) are
  covered") and in `_execute_check` (the comment "all seven builtin parsers funnel through this one
  point"). Change "seven" → "nine" and add `bandit, semgrep` to the parenthesized list.

## 2. `scripts/install-tools.sh` — add a pip provisioning path for the two Python scanners

- [x] 2.1 Restructure the Go-toolchain guard so its **absence no longer short-circuits the whole
  script**: replace the `if ! command -v go …; then <warn>; exit 0; fi` early-return + the
  unconditional `go install` lines with an `if command -v go >/dev/null 2>&1; then <go install
  gitleaks + osv-scanner>; else <the existing warning lines, but NO exit>; fi` block. Execution
  MUST continue past this block whether or not Go is present. Keep `set -euo pipefail`.
- [x] 2.2 After the Go block, add a pip-provisioning block for the two Python security scanners:
  ```bash
  if python3 -m pip --version >/dev/null 2>&1; then
      echo "${INSTALL_NAME}: installing semgrep + bandit via pip..."
      python3 -m pip install --upgrade semgrep bandit
  else
      echo "${INSTALL_NAME}: WARNING — python3 pip not found; skipping semgrep/bandit installation" >&2
      echo "${INSTALL_NAME}: See knowledge/reference/security-scanners.md for details." >&2
  fi
  ```
  (Guard on pip **presence** only — degrade-don't-block, mirroring the Go guard. A pip *install*
  failure is allowed to fail the script, same as a failing `go install`.)
- [x] 2.3 Update the header comment block and final success message: the script now provisions
  **both** the Go security scanners (gitleaks, osv-scanner via `go install`) **and** the Python
  SAST security scanners (semgrep, bandit via pip). Note in the comment that semgrep/bandit are
  installed unpinned (latest) and are version-recorded-not-gated by `checks.py`; a repo needing
  version-exactness pins them in its own dev extras. Point to
  `knowledge/reference/security-scanners.md`.

## 3. `knowledge/reference/security-scanners.md` — document the two Python SAST scanners

- [x] 3.1 Add `semgrep` and `bandit` to the doc (extend the tool table or add a "Python SAST
  scanners" subsection): what each detects (semgrep = SAST pattern findings against a
  repo-supplied ruleset; bandit = Python security linting); that they are pip tools provisioned by
  the `install-tools.sh` pip block (degrade-don't-block when pip absent); that they are
  version-recorded-not-gated by `checks.py`; and that they are **default-disabled** in `checks.py`
  (opt-in via `[checks.<name>] enabled = true`, and semgrep needs `--config <ruleset>` via
  `[checks.semgrep] args`). Keep the existing Go-scanner content intact.

## 4. `scripts/test_checks.py` — mirror the existing built-in-check tests

- [x] 4.1 In `setUp`, register stub binaries next to the existing ones:
  `self._write_generic_stub("bandit", "BANDIT")` and
  `self._write_generic_stub("semgrep", "SEMGREP")`; and set clean-default fixtures alongside the
  other `*_FIXTURE` defaults: `os.environ["BANDIT_FIXTURE"] = json.dumps({"results": []})` and
  `os.environ["SEMGREP_FIXTURE"] = json.dumps({"results": []})`.
- [x] 4.2 In `test_list_includes_every_check_with_tier_and_availability`, add `"bandit"` and
  `"semgrep"` to the `expected_names` set (this test is a set-equality assertion — it fails until
  the two names are added). **Depends on 1.1** — once 1.1 lands, `--list` emits the two new names,
  so this set MUST be updated in the same pass or the test transiently reds.
- [x] 4.3 In `test_autodetect_enables_exactly_triggered_checks`, assert both are default-disabled:
  `self.assertEqual(lines["bandit"], "disabled")` and
  `self.assertEqual(lines["semgrep"], "disabled")`.
- [x] 4.4 Add `test_bandit` to `NormalizedFindingsTest`, mirroring `test_osv_scanner`: set
  `BANDIT_FIXTURE` to `json.dumps({"results": [{"test_id": "B602", "filename": "app.py",
  "line_number": 12, "issue_text": "subprocess call with shell=True"}]})`, run
  `["--check", "bandit", "--out", <dir>]`, expect rc `2`, read `bandit.json`, and assert the single
  normalized finding equals
  `{"check": "bandit", "rule": "B602", "path": "app.py", "line": 12, "message": "subprocess call with shell=True"}`.
- [x] 4.5 Add `test_semgrep` to `NormalizedFindingsTest`: set `SEMGREP_FIXTURE` to
  `json.dumps({"results": [{"check_id": "rules.sqli", "path": "api.py", "start": {"line": 7},
  "extra": {"message": "SQL injection"}}]})`, run `["--check", "semgrep", "--out", <dir>]`, expect
  rc `2`, and assert the finding equals
  `{"check": "semgrep", "rule": "rules.sqli", "path": "api.py", "line": 7, "message": "SQL injection"}`.
- [x] 4.6 Extend `PythonToolVersionRecordedTest.test_python_tool_version_recorded_never_gates` (or
  add a sibling test) to include `bandit` and `semgrep`. Concretely: set `BANDIT_VERSION` /
  `SEMGREP_VERSION` to an arbitrary value (e.g. `"9.9.9"`), run `["--check", "bandit"]` /
  `["--check", "semgrep"]`, and assert the return code is `0` (ok — clean `{"results": []}`
  fixture) and that the run does NOT emit a version-mismatch INFRA-FAIL (they are absent from
  `EXPECTED_TOOL_VERSIONS`, so the probed version is recorded, never gated). Mirror the existing
  ruff/deptry/radon/vulture assertions in that test.

## 5. Green gate

- [x] 5.1 Run `bash scripts/check.sh` (ruff check + ruff format --check + `pytest -q`) and confirm
  it exits 0. Fix any lint/format/test failure introduced by the tasks above before reporting done.
