#!/usr/bin/env python3
"""Tests for checks.py — stdlib unittest, no pytest.

Every external binary (ruff, gitleaks, osv-scanner, deptry, radon, jscpd,
vulture, psql) is faked with a small stub shell script prepended to PATH.
Stub content/version is driven by env vars so each test can inject a
specific scenario (clean, findings, wrong version, missing) without
touching the stub scripts themselves. Stubs append an invocation line to
`$STUB_INVOKE_LOG` (skipped for `--version`/`version` probes) so tests can
prove call order / that a check was or wasn't actually run.
"""

from __future__ import annotations

import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import checks  # noqa: E402

_BASE_PATH = "/usr/bin:/bin"

# --- stub templates -----------------------------------------------------
# Each stub: `<tool> --version` / `<tool> version` -> prints a version
# string (env-var overridable). Any other invocation is the "real" run;
# each writes/prints its canned fixture (env-var content) to wherever the
# real tool would put it, and logs its invocation for order-proofing.

_GITLEAKS_STUB = """\
#!/bin/sh
if [ "$1" = "--version" ] || [ "$1" = "version" ]; then
  echo "gitleaks ${GITLEAKS_VERSION:-8.30.1}"
  exit 0
fi
echo "gitleaks invoked: $@" >> "$STUB_INVOKE_LOG"
prev=""
OUT=""
for arg in "$@"; do
  if [ "$prev" = "--report-path" ]; then
    OUT="$arg"
  fi
  prev="$arg"
done
printf '%s' "$GITLEAKS_FIXTURE" > "$OUT"
exit 0
"""

_DEPTRY_STUB = """\
#!/bin/sh
if [ "$1" = "--version" ] || [ "$1" = "version" ]; then
  echo "deptry ${DEPTRY_VERSION:-1.0.0}"
  exit 0
fi
echo "deptry invoked: $@" >> "$STUB_INVOKE_LOG"
prev=""
OUT=""
for arg in "$@"; do
  if [ "$prev" = "-o" ]; then
    OUT="$arg"
  fi
  prev="$arg"
done
printf '%s' "$DEPTRY_FIXTURE" > "$OUT"
exit 0
"""

_JSCPD_STUB = """\
#!/bin/sh
if [ "$1" = "--version" ] || [ "$1" = "version" ]; then
  echo "jscpd ${JSCPD_VERSION:-5.0.11}"
  exit 0
fi
echo "jscpd invoked: $@" >> "$STUB_INVOKE_LOG"
prev=""
OUT=""
for arg in "$@"; do
  if [ "$prev" = "--output" ]; then
    OUT="$arg"
  fi
  prev="$arg"
done
mkdir -p "$OUT"
printf '%s' "$JSCPD_FIXTURE" > "$OUT/jscpd-report.json"
exit 0
"""

_PSQL_STUB = """\
#!/bin/sh
echo "psql invoked: $@" >> "$STUB_INVOKE_LOG"
printf 'col1\\n'
exit 0
"""


class AuditBundleTestBase(unittest.TestCase):
    """Common fixture: a temp git repo + stub PATH."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.repo = self.tmpdir / "repo"
        self.repo.mkdir()
        self._git("init", "-b", "main")
        self._git("config", "user.email", "test@example.com")
        self._git("config", "user.name", "Test User")

        (self.repo / "pyproject.toml").write_text(
            '[project]\nname = "fixture"\nversion = "0.1.0"\n'
        )
        (self.repo / "requirements.txt").write_text("flask==1.0\n")
        checks_dir = self.repo / "checks"
        checks_dir.mkdir()
        (checks_dir / "001_a.sql").write_text("-- STUB: zero\nSELECT 1;\n")
        (self.repo / "a.py").write_text("def foo():\n    return 1\n")
        self._git("add", "-A")
        self._git("commit", "-m", "initial")

        self.stub_bin = self.tmpdir / "stub_bin"
        self.stub_bin.mkdir()
        self._write_generic_stub("ruff", "RUFF")
        self._write_generic_stub("osv-scanner", "OSV_SCANNER", default_version="2.4.0")
        self._write_generic_stub("radon", "RADON")
        self._write_generic_stub("vulture", "VULTURE")
        self._write_stub("gitleaks", _GITLEAKS_STUB)
        self._write_stub("deptry", _DEPTRY_STUB)
        self._write_stub("jscpd", _JSCPD_STUB)
        self._write_stub("psql", _PSQL_STUB)

        self.invoke_log = self.tmpdir / "invoke.log"
        self.invoke_log.write_text("")

        self._orig_cwd = os.getcwd()
        os.chdir(self.repo)
        self._orig_env = dict(os.environ)
        os.environ["PATH"] = f"{self.stub_bin}{os.pathsep}{_BASE_PATH}"
        os.environ["STUB_INVOKE_LOG"] = str(self.invoke_log)
        os.environ["AUDIT_DB_URL"] = "postgres://fake/db"
        os.environ["RUFF_FIXTURE"] = "[]"
        os.environ["GITLEAKS_FIXTURE"] = "[]"
        os.environ["OSV_SCANNER_FIXTURE"] = '{"results": []}'
        os.environ["DEPTRY_FIXTURE"] = "[]"
        os.environ["RADON_FIXTURE"] = "{}"
        os.environ["JSCPD_FIXTURE"] = '{"duplicates": []}'
        os.environ["VULTURE_FIXTURE"] = ""

    def tearDown(self):
        os.chdir(self._orig_cwd)
        os.environ.clear()
        os.environ.update(self._orig_env)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _git(self, *args):
        import subprocess

        result = subprocess.run(["git", *args], cwd=str(self.repo), capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"git {args} failed: {result.stderr}")

    def _write_stub(self, name: str, body: str) -> None:
        p = self.stub_bin / name
        p.write_text(body)
        p.chmod(0o755)

    def _write_generic_stub(
        self, name: str, env_prefix: str, default_version: str = "1.0.0"
    ) -> None:
        body = (
            "#!/bin/sh\n"
            'if [ "$1" = "--version" ] || [ "$1" = "version" ]; then\n'
            f'  echo "{name} ${{{env_prefix}_VERSION:-{default_version}}}"\n'
            "  exit 0\n"
            "fi\n"
            f'echo "{name} invoked: $@" >> "$STUB_INVOKE_LOG"\n'
            f"printf '%s' \"${env_prefix}_FIXTURE\"\n"
            "exit 0\n"
        )
        self._write_stub(name, body)

    def _capture(self, argv: list[str]) -> tuple[int, str]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = checks.main(argv)
        return rc, buf.getvalue()

    def _invoke_log_lines(self) -> list[str]:
        return [line for line in self.invoke_log.read_text().splitlines() if line.strip()]


class ListModeTest(AuditBundleTestBase):
    def test_list_includes_every_check_with_tier_and_availability(self):
        rc, out = self._capture(["--list"])
        self.assertEqual(rc, 0)
        lines = {line.split()[0]: line for line in out.splitlines()}
        expected_names = {
            "scope",
            "ruff",
            "gitleaks",
            "osv-scanner",
            "deptry",
            "data-lint",
            "radon",
            "jscpd",
            "vulture",
            "index-coverage",
            "inventory",
        }
        self.assertEqual(set(lines), expected_names)
        # correct tiers
        self.assertIn("floor", lines["ruff"])
        self.assertIn("heavy", lines["radon"])
        self.assertIn("snapshot", lines["inventory"])
        # all stubbed tools report available
        self.assertIn("available", lines["ruff"])
        self.assertIn("available", lines["gitleaks"])

    def test_version_mismatch_reported_in_list(self):
        os.environ["GITLEAKS_VERSION"] = "1.2.3"  # pinned expects 8.30.1
        rc, out = self._capture(["--list"])
        self.assertEqual(rc, 0)  # --list always exits 0
        lines = {line.split()[0]: line for line in out.splitlines()}
        self.assertIn("version-mismatch", lines["gitleaks"])

    def test_missing_binary_reported_unavailable_in_list(self):
        os.remove(self.stub_bin / "deptry")
        rc, out = self._capture(["--list"])
        self.assertEqual(rc, 0)
        lines = {line.split()[0]: line for line in out.splitlines()}
        self.assertIn("unavailable", lines["deptry"])


class AutodetectTest(AuditBundleTestBase):
    def test_autodetect_enables_exactly_triggered_checks(self):
        rc, out = self._capture(["--list"])
        self.assertEqual(rc, 0)
        lines = {line.split()[0]: line.split()[3] for line in out.splitlines()}
        # triggers present in fixture: pyproject.toml, .git/, requirements.txt, checks/*.sql
        self.assertEqual(lines["scope"], "enabled")
        self.assertEqual(lines["ruff"], "enabled")
        self.assertEqual(lines["gitleaks"], "enabled")
        self.assertEqual(lines["osv-scanner"], "enabled")
        self.assertEqual(lines["deptry"], "enabled")
        self.assertEqual(lines["data-lint"], "enabled")
        self.assertEqual(lines["inventory"], "enabled")
        # heavy checks + index-coverage default OFF absent config
        self.assertEqual(lines["radon"], "disabled")
        self.assertEqual(lines["jscpd"], "disabled")
        self.assertEqual(lines["vulture"], "disabled")
        self.assertEqual(lines["index-coverage"], "disabled")


class CustomCheckTest(AuditBundleTestBase):
    def test_custom_check_command_captured_to_txt(self):
        (self.repo / "checks.toml").write_text(
            "[checks.custom.mycheck]\n"
            'command = ["sh", "-c", "echo hello-custom"]\n'
            'tier = "floor"\n'
            "gate = true\n"
        )
        out_dir = self.tmpdir / "out1"
        rc, out = self._capture(["--check", "mycheck", "--out", str(out_dir)])
        self.assertEqual(rc, 0)
        artifact = out_dir / "mycheck.txt"
        self.assertTrue(artifact.exists())
        self.assertIn("hello-custom", artifact.read_text())
        self.assertIn("mycheck: ok — ? findings ->", out)

    def test_custom_check_gate_false_never_findings(self):
        (self.repo / "checks.toml").write_text(
            "[checks.custom.failer]\n"
            'command = ["sh", "-c", "exit 1"]\n'
            'tier = "heavy"\n'
            "gate = false\n"
        )
        out_dir = self.tmpdir / "out2"
        rc, out = self._capture(["--check", "failer", "--out", str(out_dir)])
        self.assertEqual(rc, 0)  # gate=false -> report-only, never FINDINGS

    def test_custom_check_gate_true_nonzero_is_findings(self):
        (self.repo / "checks.toml").write_text(
            "[checks.custom.failer]\n"
            'command = ["sh", "-c", "exit 1"]\n'
            'tier = "heavy"\n'
            "gate = true\n"
        )
        out_dir = self.tmpdir / "out3"
        rc, out = self._capture(["--check", "failer", "--out", str(out_dir)])
        self.assertEqual(rc, 2)


class ConfigCoercionTest(AuditBundleTestBase):
    """Fix 6: scalar-string TOML values are coerced to the equivalent
    single-element list rather than silently footgunning (string indexing /
    per-character iteration); a genuinely-wrong config shape is an explicit
    INFRA-FAIL, not a silent no-op."""

    def _write_alt_checks_dir(self) -> None:
        alt_checks = self.repo / "alt_checks"
        alt_checks.mkdir()
        (alt_checks / "001_a.sql").write_text("-- STUB: zero\nSELECT 1;\n")

    def test_data_lint_paths_scalar_string_same_as_list_form(self):
        self._write_alt_checks_dir()

        (self.repo / "checks.toml").write_text('[checks.data-lint]\npaths = "alt_checks"\n')
        out_dir_scalar = self.tmpdir / "out-scalar"
        rc_scalar, _ = self._capture(["--check", "data-lint", "--out", str(out_dir_scalar)])

        (self.repo / "checks.toml").write_text('[checks.data-lint]\npaths = ["alt_checks"]\n')
        out_dir_list = self.tmpdir / "out-list"
        rc_list, _ = self._capture(["--check", "data-lint", "--out", str(out_dir_list)])

        self.assertEqual(rc_scalar, rc_list)
        self.assertEqual(rc_scalar, 0)
        data_scalar = json.loads((out_dir_scalar / "data-lint.json").read_text())
        data_list = json.loads((out_dir_list / "data-lint.json").read_text())
        self.assertEqual(data_scalar, data_list)
        self.assertEqual(data_scalar["checks"][0]["name"], "001_a")

    def test_index_coverage_schema_scalar_string_same_as_list_form(self):
        schema_file = self.repo / "schema.sql"
        schema_file.write_text(
            "CREATE TABLE users (\n    id SERIAL PRIMARY KEY,\n    email TEXT\n);\n"
        )
        queries_dir = self.repo / "queries"
        queries_dir.mkdir()
        (queries_dir / "q.sql").write_text("SELECT * FROM users WHERE email = 'x';\n")

        (self.repo / "checks.toml").write_text(
            '[checks.index-coverage]\nschema = "schema.sql"\nqueries = ["queries/*.sql"]\n'
        )
        out_dir_scalar = self.tmpdir / "out-scalar"
        rc_scalar, _ = self._capture(["--check", "index-coverage", "--out", str(out_dir_scalar)])

        (self.repo / "checks.toml").write_text(
            '[checks.index-coverage]\nschema = ["schema.sql"]\nqueries = ["queries/*.sql"]\n'
        )
        out_dir_list = self.tmpdir / "out-list"
        rc_list, _ = self._capture(["--check", "index-coverage", "--out", str(out_dir_list)])

        self.assertEqual(rc_scalar, rc_list)
        self.assertEqual(rc_scalar, 0)
        data_scalar = json.loads((out_dir_scalar / "index-coverage.json").read_text())
        data_list = json.loads((out_dir_list / "index-coverage.json").read_text())
        self.assertEqual(data_scalar, data_list)
        self.assertGreater(len(data_scalar["leads"]), 0)

    def test_index_coverage_queries_scalar_string_same_as_list_form(self):
        schema_file = self.repo / "schema.sql"
        schema_file.write_text(
            "CREATE TABLE users (\n    id SERIAL PRIMARY KEY,\n    email TEXT\n);\n"
        )
        queries_dir = self.repo / "queries"
        queries_dir.mkdir()
        (queries_dir / "q.sql").write_text("SELECT * FROM users WHERE email = 'x';\n")

        (self.repo / "checks.toml").write_text(
            '[checks.index-coverage]\nschema = "schema.sql"\nqueries = "queries/*.sql"\n'
        )
        out_dir_scalar = self.tmpdir / "out-scalar"
        rc_scalar, _ = self._capture(["--check", "index-coverage", "--out", str(out_dir_scalar)])

        (self.repo / "checks.toml").write_text(
            '[checks.index-coverage]\nschema = "schema.sql"\nqueries = ["queries/*.sql"]\n'
        )
        out_dir_list = self.tmpdir / "out-list"
        rc_list, _ = self._capture(["--check", "index-coverage", "--out", str(out_dir_list)])

        self.assertEqual(rc_scalar, rc_list)
        self.assertEqual(rc_scalar, 0)
        data_scalar = json.loads((out_dir_scalar / "index-coverage.json").read_text())
        data_list = json.loads((out_dir_list / "index-coverage.json").read_text())
        self.assertEqual(data_scalar, data_list)
        self.assertGreater(len(data_scalar["leads"]), 0)

    def test_data_lint_paths_two_entries_infra_fail_with_config_error(self):
        self._write_alt_checks_dir()
        (self.repo / "checks.toml").write_text(
            '[checks.data-lint]\npaths = ["checks", "alt_checks"]\n'
        )
        out_dir = self.tmpdir / "out"
        rc, out = self._capture(["--report", "--out", str(out_dir)])
        self.assertEqual(rc, 3)
        manifest = json.loads((out_dir / "run-manifest.json").read_text())
        record = next(r for r in manifest if r.get("check") == "data-lint")
        self.assertEqual(record["status"], "INFRA-FAIL")
        self.assertIn("only a single checks directory is supported", record["error"])

    def test_data_lint_paths_wrong_type_infra_fail_with_config_error(self):
        (self.repo / "checks.toml").write_text("[checks.data-lint]\npaths = 5\n")
        out_dir = self.tmpdir / "out"
        rc, out = self._capture(["--report", "--out", str(out_dir)])
        self.assertEqual(rc, 3)
        manifest = json.loads((out_dir / "run-manifest.json").read_text())
        record = next(r for r in manifest if r.get("check") == "data-lint")
        self.assertEqual(record["status"], "INFRA-FAIL")
        self.assertIn("expected a string or list of strings", record["error"])


class DelegateErrorCapturedTest(AuditBundleTestBase):
    """Fix 7: a delegate check's INFRA-FAIL record captures the delegate's
    stderr reason, not just a bare status with no explanation."""

    def test_data_lint_missing_db_url_error_captured_in_manifest(self):
        os.environ.pop("AUDIT_DB_URL", None)
        out_dir = self.tmpdir / "out"
        rc, out = self._capture(["--report", "--out", str(out_dir)])
        self.assertEqual(rc, 3)
        manifest = json.loads((out_dir / "run-manifest.json").read_text())
        record = next(r for r in manifest if r.get("check") == "data-lint")
        self.assertEqual(record["status"], "INFRA-FAIL")
        self.assertIn("error", record)
        self.assertIn("AUDIT_DB_URL", record["error"])


class RepoRootSubdirectoryTest(AuditBundleTestBase):
    """Fix 8: repo_root is resolved via git toplevel, not bare CWD, so
    invoking from a repo subdirectory still yields root-relative paths."""

    def test_inventory_tree_is_root_relative_when_invoked_from_subdirectory(self):
        subdir = self.repo / "pkg"
        subdir.mkdir()
        (subdir / "mod.py").write_text("x = 1\n")
        self._git("add", "-A")
        self._git("commit", "-m", "add pkg/mod.py")

        os.chdir(subdir)
        out_dir = self.tmpdir / "out"
        rc, out = self._capture(["--check", "inventory", "--out", str(out_dir)])
        self.assertEqual(rc, 0)
        data = json.loads((out_dir / "inventory.json").read_text())
        self.assertIn("pkg/mod.py", data["tree"])
        self.assertIn("pyproject.toml", data["tree"])
        # Never a subdir-relative (bare "mod.py") or absolute path.
        self.assertNotIn("mod.py", data["tree"])
        for p in data["tree"]:
            self.assertFalse(Path(p).is_absolute())


class NormalizedFindingsTest(AuditBundleTestBase):
    """Each built-in parser fixture -> correct normalized-findings shape."""

    def _run_single_check(self, name: str) -> dict:
        out_dir = self.tmpdir / f"out-{name}"
        rc, out = self._capture(["--check", name, "--out", str(out_dir)])
        self.assertEqual(rc, 2, f"{name}: expected FINDINGS, got rc={rc}, out={out!r}")
        data = json.loads((out_dir / f"{name}.json").read_text())
        self.assertEqual(len(data), 1)
        return data[0]

    def test_ruff(self):
        os.environ["RUFF_FIXTURE"] = json.dumps(
            [
                {
                    "cell": None,
                    "code": "F401",
                    "name": "unused-import",
                    "severity": "error",
                    "end_location": {"column": 10, "row": 3},
                    "filename": "pkg/mod.py",
                    "fix": None,
                    "location": {"column": 1, "row": 3},
                    "message": "`os` imported but unused",
                    "noqa_row": None,
                    "url": "https://docs.astral.sh/ruff/rules/unused-import",
                }
            ]
        )
        finding = self._run_single_check("ruff")
        self.assertEqual(finding["check"], "ruff")
        self.assertEqual(finding["rule"], "F401")
        self.assertEqual(finding["path"], "pkg/mod.py")
        self.assertEqual(finding["line"], 3)
        self.assertEqual(finding["message"], "`os` imported but unused")

    def test_gitleaks(self):
        os.environ["GITLEAKS_FIXTURE"] = json.dumps(
            [
                {
                    "RuleID": "generic-api-key",
                    "Description": "Generic API Key",
                    "StartLine": 5,
                    "EndLine": 5,
                    "StartColumn": 1,
                    "EndColumn": 20,
                    "Match": "abc",
                    "Secret": "abc",
                    "File": "config.py",
                    "SymlinkFile": "",
                    "Commit": "",
                    "Entropy": 3.5,
                    "Author": "",
                    "Email": "",
                    "Date": "",
                    "Message": "",
                    "Tags": [],
                    "Fingerprint": "config.py:generic-api-key:1",
                }
            ]
        )
        finding = self._run_single_check("gitleaks")
        self.assertEqual(finding["check"], "gitleaks")
        self.assertEqual(finding["rule"], "generic-api-key")
        self.assertEqual(finding["path"], "config.py")
        self.assertEqual(finding["line"], 5)
        self.assertEqual(finding["message"], "Generic API Key")

    def test_osv_scanner(self):
        os.environ["OSV_SCANNER_FIXTURE"] = json.dumps(
            {
                "results": [
                    {
                        "source": {"path": "requirements.txt", "type": "lockfile"},
                        "packages": [
                            {
                                "package": {"name": "flask", "version": "1.0", "ecosystem": "PyPI"},
                                "vulnerabilities": [
                                    {
                                        "id": "GHSA-xxxx-yyyy-zzzz",
                                        "summary": "Flask vulnerable to XSS",
                                        "details": "...",
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }
        )
        finding = self._run_single_check("osv-scanner")
        self.assertEqual(finding["check"], "osv-scanner")
        self.assertEqual(finding["rule"], "GHSA-xxxx-yyyy-zzzz")
        self.assertEqual(finding["path"], "requirements.txt")
        self.assertIsNone(finding["line"])
        self.assertEqual(finding["message"], "Flask vulnerable to XSS")

    def test_deptry(self):
        os.environ["DEPTRY_FIXTURE"] = json.dumps(
            [
                {
                    "error": {
                        "code": "DEP002",
                        "message": "'requests' defined as a dependency but not used",
                    },
                    "module": "requests",
                    "location": {"file": "pkg/mod.py", "line": 1, "column": 1},
                }
            ]
        )
        finding = self._run_single_check("deptry")
        self.assertEqual(finding["check"], "deptry")
        self.assertEqual(finding["rule"], "DEP002")
        self.assertEqual(finding["path"], "pkg/mod.py")
        self.assertEqual(finding["line"], 1)
        self.assertEqual(finding["message"], "'requests' defined as a dependency but not used")

    def test_radon(self):
        os.environ["RADON_FIXTURE"] = json.dumps(
            {
                "pkg/mod.py": [
                    {
                        "type": "function",
                        "name": "complex_fn",
                        "complexity": 25,
                        "rank": "D",
                        "lineno": 10,
                    }
                ]
            }
        )
        finding = self._run_single_check("radon")
        self.assertEqual(finding["check"], "radon")
        self.assertEqual(finding["rule"], "complexity-D")
        self.assertEqual(finding["path"], "pkg/mod.py")
        self.assertEqual(finding["line"], 10)
        self.assertIn("complex_fn", finding["message"])
        self.assertIn("25", finding["message"])

    def test_jscpd(self):
        os.environ["JSCPD_FIXTURE"] = json.dumps(
            {
                "duplicates": [
                    {
                        "format": "python",
                        "lines": 8,
                        "tokens": 40,
                        "fragment": "...",
                        "firstFile": {"name": "pkg/a.py", "start": 5, "end": 12},
                        "secondFile": {"name": "pkg/b.py", "start": 20, "end": 27},
                    }
                ]
            }
        )
        finding = self._run_single_check("jscpd")
        self.assertEqual(finding["check"], "jscpd")
        self.assertEqual(finding["path"], "pkg/a.py")
        self.assertEqual(finding["line"], 5)
        self.assertIn("pkg/b.py", finding["message"])
        self.assertIn("20", finding["message"])
        self.assertIn("8", finding["message"])

    def test_vulture(self):
        os.environ["VULTURE_FIXTURE"] = "pkg/mod.py:12: unused variable 'x' (60% confidence)\n"
        finding = self._run_single_check("vulture")
        self.assertEqual(finding["check"], "vulture")
        self.assertEqual(finding["path"], "pkg/mod.py")
        self.assertEqual(finding["line"], 12)
        self.assertEqual(finding["message"], "unused variable 'x'")


class PathNormalizationTest(AuditBundleTestBase):
    """Findings whose path is absolute under the repo root are normalized to
    repo-relative before hitting the per-check artifact JSON or
    findings.json (Defect 1 fix); absolute paths outside the repo root are
    left unchanged."""

    def test_absolute_path_under_repo_root_normalized_in_per_check_artifact(self):
        abs_path = str(self.repo / "pkg" / "mod.py")
        os.environ["RUFF_FIXTURE"] = json.dumps(
            [
                {
                    "code": "F401",
                    "filename": abs_path,
                    "location": {"row": 3, "column": 1},
                    "message": "unused import",
                }
            ]
        )
        out_dir = self.tmpdir / "out-abs-in-repo"
        rc, out = self._capture(["--check", "ruff", "--out", str(out_dir)])
        self.assertEqual(rc, 2)
        data = json.loads((out_dir / "ruff.json").read_text())
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["path"], "pkg/mod.py")

    def test_absolute_path_outside_repo_root_left_unchanged(self):
        outside_path = str(self.tmpdir / "outside" / "mod.py")  # sibling of repo, not under it
        os.environ["RUFF_FIXTURE"] = json.dumps(
            [
                {
                    "code": "F401",
                    "filename": outside_path,
                    "location": {"row": 3, "column": 1},
                    "message": "unused import",
                }
            ]
        )
        out_dir = self.tmpdir / "out-abs-outside"
        rc, out = self._capture(["--check", "ruff", "--out", str(out_dir)])
        self.assertEqual(rc, 2)
        data = json.loads((out_dir / "ruff.json").read_text())
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["path"], outside_path)

    def test_findings_json_also_gets_repo_relative_path(self):
        abs_path = str(self.repo / "pkg" / "mod.py")
        os.environ["RUFF_FIXTURE"] = json.dumps(
            [
                {
                    "code": "F401",
                    "filename": abs_path,
                    "location": {"row": 3, "column": 1},
                    "message": "unused import",
                }
            ]
        )
        out_dir = self.tmpdir / "out-report"
        rc, out = self._capture(["--report", "--out", str(out_dir)])
        self.assertEqual(rc, 2)
        findings = json.loads((out_dir / "findings.json").read_text())
        ruff_findings = [f for f in findings if f["check"] == "ruff"]
        self.assertEqual(len(ruff_findings), 1)
        self.assertEqual(ruff_findings[0]["path"], "pkg/mod.py")


class VersionMismatchReportTest(AuditBundleTestBase):
    def test_version_mismatch_exits_3_in_report_with_expected_found_message(self):
        os.environ["GITLEAKS_VERSION"] = "1.2.3"
        out_dir = self.tmpdir / "out"
        out_buf, err_buf = io.StringIO(), io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            rc = checks.main(["--report", "--out", str(out_dir)])
        self.assertEqual(rc, 3)
        self.assertIn("1.2.3", err_buf.getvalue())
        self.assertIn("8.30.1", err_buf.getvalue())


class PreflightTest(AuditBundleTestBase):
    """Preflight semantics (task 2.2): missing check-family tools are all
    reported in one pass before any check executes; mid-run failures still
    stop on first failure."""

    def test_preflight_reports_all_missing_and_runs_nothing(self):
        """(a) Two missing check-family tools both reported; none executed."""
        os.remove(self.stub_bin / "deptry")
        os.remove(self.stub_bin / "gitleaks")

        out_dir = self.tmpdir / "out"
        out_buf, err_buf = io.StringIO(), io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            rc = checks.main(["--report", "--out", str(out_dir)])
        self.assertEqual(rc, 3)
        stderr = err_buf.getvalue()

        # Both missing tools reported in stderr with INFRA-FAIL
        self.assertIn("deptry", stderr)
        self.assertIn("gitleaks", stderr)
        self.assertIn("INFRA-FAIL", stderr)
        # Each carries install-or-disable guidance
        self.assertIn("Install deptry", stderr)
        self.assertIn("Install gitleaks", stderr)

        # No check was actually executed
        self.assertEqual(self._invoke_log_lines(), [])

        # Manifest has both INFRA-FAIL records
        manifest = json.loads((out_dir / "run-manifest.json").read_text())
        records = {r["check"]: r for r in manifest if not r.get("meta")}
        self.assertIn("deptry", records)
        self.assertEqual(records["deptry"]["status"], "INFRA-FAIL")
        self.assertIn("gitleaks", records)
        self.assertEqual(records["gitleaks"]["status"], "INFRA-FAIL")

    def test_mid_run_infra_fail_stops_after_failing_check(self):
        """(b) Mid-run INFRA-FAIL (binary passes preflight but crashes at
        runtime) records the aborting check and stops."""
        # osv-scanner stub exists with correct version (passes preflight),
        # but its output is unparseable — triggers INFRA-FAIL at run time.
        os.environ["OSV_SCANNER_FIXTURE"] = "not valid json"

        out_dir = self.tmpdir / "out"
        out_buf, err_buf = io.StringIO(), io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            rc = checks.main(["--report", "--out", str(out_dir)])
        self.assertEqual(rc, 3)

        manifest = json.loads((out_dir / "run-manifest.json").read_text())
        records = [r for r in manifest if not r.get("meta")]
        checks_run = [r["check"] for r in records]

        # Checks before osv-scanner in registry order completed
        self.assertIn("ruff", checks_run)
        self.assertIn("gitleaks", checks_run)
        # osv-scanner itself is INFRA-FAIL
        osv_record = next(r for r in records if r["check"] == "osv-scanner")
        self.assertEqual(osv_record["status"], "INFRA-FAIL")
        # Checks after osv-scanner did NOT run
        self.assertNotIn("deptry", checks_run)
        self.assertNotIn("data-lint", checks_run)
        self.assertNotIn("inventory", checks_run)


class ResumeOrderProofTest(AuditBundleTestBase):
    def test_resume_skips_completed_checks_and_retries_infra_fails(self):
        """--resume skips completed (ok/FINDINGS) checks; retries INFRA-FAIL."""
        # Mid-run failure via osv-scanner unparseable output
        os.environ["OSV_SCANNER_FIXTURE"] = "not valid json"
        out_dir = self.tmpdir / "out"

        out_buf, err_buf = io.StringIO(), io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            rc1 = checks.main(["--report", "--out", str(out_dir)])
        self.assertEqual(rc1, 3)
        first_log = list(self._invoke_log_lines())
        self.assertTrue(any("ruff invoked" in line for line in first_log))
        self.assertTrue(any("gitleaks invoked" in line for line in first_log))

        # "Fix" osv-scanner: restore valid fixture.
        os.environ["OSV_SCANNER_FIXTURE"] = '{"results": []}'

        rc2, out2 = self._capture(["--report", "--out", str(out_dir), "--resume"])
        self.assertEqual(rc2, 0)

        second_log = self._invoke_log_lines()
        ruff_calls = [line for line in second_log if line.startswith("ruff invoked")]
        gitleaks_calls = [line for line in second_log if line.startswith("gitleaks invoked")]
        # Only ONE invocation each across both runs — resume did not re-run them.
        self.assertEqual(len(ruff_calls), 1)
        self.assertEqual(len(gitleaks_calls), 1)
        # osv-scanner was retried (INFRA-FAIL is not a completion).
        osv_calls = [line for line in second_log if line.startswith("osv-scanner invoked")]
        self.assertEqual(len(osv_calls), 2)

        manifest = json.loads((out_dir / "run-manifest.json").read_text())
        completed = {
            r["check"] for r in manifest if not r.get("meta") and r["status"] != "INFRA-FAIL"
        }
        self.assertIn("deptry", completed)
        self.assertIn("data-lint", completed)
        self.assertIn("inventory", completed)


class PreflightMessageShapeTest(AuditBundleTestBase):
    """Task 6.2: preflight-message shape — trigger, install-or-disable,
    coverage note; fact-family missing does NOT trigger preflight; --list
    summary line appears when a check-family entry is unavailable."""

    def test_infra_fail_line_contains_trigger_and_coverage_note(self):
        """Each INFRA-FAIL line carries trigger, install-or-disable, and
        coverage note."""
        os.remove(self.stub_bin / "deptry")

        out_dir = self.tmpdir / "out"
        out_buf, err_buf = io.StringIO(), io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            rc = checks.main(["--report", "--out", str(out_dir)])
        self.assertEqual(rc, 3)
        stderr = err_buf.getvalue()

        # Trigger: deptry has trigger "pyproject.toml present"
        self.assertIn("pyproject.toml present", stderr)
        # Install-or-disable guidance
        self.assertIn("Install deptry", stderr)
        self.assertIn("disable in checks.toml", stderr)
        self.assertIn("[checks.deptry]", stderr)
        # Coverage note
        self.assertIn("drops dependency-hygiene checking", stderr)

    def test_fact_family_missing_does_not_trigger_preflight(self):
        """A missing fact-family tool (radon) does NOT trigger preflight
        failure in --report — it degrades gracefully."""
        os.remove(self.stub_bin / "radon")
        # Enable radon in config so it's selected (heavy, default disabled).
        (self.repo / "checks.toml").write_text("[checks.radon]\nenabled = true\n")

        out_dir = self.tmpdir / "out"
        out_buf, err_buf = io.StringIO(), io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            rc = checks.main(["--report", "--out", str(out_dir)])
        # --report should still succeed; radon degrades gracefully,
        # producing "ok — 0 findings" with a null version.
        self.assertEqual(rc, 0)
        # Preflight failure NOT triggered for radon
        self.assertNotIn("INFRA-FAIL", err_buf.getvalue())

    def test_list_summary_line_when_check_family_unavailable(self):
        """--list prints the summary line when an enabled check-family
        entry is unavailable."""
        os.remove(self.stub_bin / "deptry")

        rc, out = self._capture(["--list"])
        self.assertEqual(rc, 0)
        lines = out.splitlines()
        # The last line should be the summary
        last_line = lines[-1]
        self.assertIn("enabled check(s) unavailable", last_line)
        self.assertIn("--floor/--report will fail preflight", last_line)


class SummaryLineFormatTest(AuditBundleTestBase):
    def test_summary_and_final_line_formats(self):
        out_dir = self.tmpdir / "out"
        rc, out = self._capture(["--report", "--out", str(out_dir)])
        self.assertEqual(rc, 0)
        lines = out.splitlines()
        per_check_lines = [
            line
            for line in lines
            if line.startswith(
                (
                    "scope:",
                    "ruff:",
                    "gitleaks:",
                    "osv-scanner:",
                    "deptry:",
                    "data-lint:",
                    "inventory:",
                )
            )
        ]
        self.assertTrue(len(per_check_lines) >= 7)
        for line in per_check_lines:
            self.assertRegex(
                line, r"^\S+: (ok|FINDINGS|INFRA-FAIL|skipped) — (\d+|\?) findings -> .+$"
            )
        final_lines = [line for line in lines if line.startswith("checks: ")]
        self.assertEqual(len(final_lines), 1)
        self.assertRegex(final_lines[0], r"^checks: \d+ findings across \d+ checks -> .+$")


class BaselineDiffTest(AuditBundleTestBase):
    def test_baseline_diff_new_resolved_unchanged_line_insensitive(self):
        os.environ["RUFF_FIXTURE"] = json.dumps(
            [
                {
                    "code": "E501",
                    "filename": "a.py",
                    "location": {"row": 10, "column": 1},
                    "message": "line too long",
                },
                {
                    "code": "F401",
                    "filename": "b.py",
                    "location": {"row": 5, "column": 1},
                    "message": "unused import",
                },
            ]
        )
        baseline_path = self.tmpdir / "baseline.json"
        baseline_path.write_text(
            json.dumps(
                [
                    {
                        "check": "ruff",
                        "rule": "E501",
                        "path": "a.py",
                        "line": 99,
                        "message": "line too long",
                    },
                    {
                        "check": "ruff",
                        "rule": "W605",
                        "path": "c.py",
                        "line": 3,
                        "message": "old finding",
                    },
                ]
            )
        )

        out_dir = self.tmpdir / "out"
        rc, out = self._capture(
            ["--report", "--out", str(out_dir), "--baseline", str(baseline_path)]
        )
        self.assertEqual(rc, 2)  # new findings present

        delta = json.loads((out_dir / "delta.json").read_text())
        self.assertEqual(delta["unchanged_count"], 1)
        self.assertEqual(len(delta["new"]), 1)
        self.assertEqual(delta["new"][0]["path"], "b.py")
        self.assertEqual(len(delta["resolved"]), 1)
        self.assertEqual(delta["resolved"][0]["path"], "c.py")
        self.assertIn("delta: 1 new, 1 resolved vs", out)

    def test_baseline_only_valid_with_report(self):
        baseline_path = self.tmpdir / "baseline.json"
        baseline_path.write_text("[]")
        rc, out = self._capture(["--floor", "--baseline", str(baseline_path)])
        self.assertEqual(rc, 3)


class PythonToolVersionRecordedTest(AuditBundleTestBase):
    """Python-ecosystem tools (ruff etc.) never gate on version — only recorded (4.3)."""

    def test_python_tool_version_recorded_never_gates(self):
        os.environ["RUFF_VERSION"] = "999.0.0"  # arbitrary — ruff has no pin to mismatch against
        out_dir = self.tmpdir / "out"
        rc, out = self._capture(["--check", "ruff", "--out", str(out_dir)])
        self.assertEqual(rc, 0)  # clean RUFF_FIXTURE ("[]") -> ok, never fails on version

    def test_run_manifest_records_builtin_tool_version(self):
        out_dir = self.tmpdir / "out"
        rc, out = self._capture(["--report", "--out", str(out_dir)])
        self.assertEqual(rc, 0)
        manifest = json.loads((out_dir / "run-manifest.json").read_text())
        ruff_record = next(r for r in manifest if r.get("check") == "ruff")
        self.assertIn("version", ruff_record)
        self.assertIsNotNone(ruff_record["version"])
        gitleaks_record = next(r for r in manifest if r.get("check") == "gitleaks")
        self.assertEqual(gitleaks_record["version"], "8.30.1")


class ReportDateTest(AuditBundleTestBase):
    def test_report_without_date_uses_today_dir_name(self):
        rc, out = self._capture(["--report"])
        self.assertEqual(rc, 0)
        expected_dir = self.repo / "output" / "checks" / date.today().isoformat()
        self.assertTrue(expected_dir.is_dir())

    def test_report_with_date_pins_dir_name(self):
        rc, out = self._capture(["--report", "--date", "2026-01-15"])
        self.assertEqual(rc, 0)
        expected_dir = self.repo / "output" / "checks" / "2026-01-15"
        self.assertTrue(expected_dir.is_dir())


class FloorNoChecksEnabledTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.repo = self.tmpdir / "repo"
        self.repo.mkdir()
        self._orig_cwd = os.getcwd()
        os.chdir(self.repo)
        self._orig_path = os.environ.get("PATH", "")
        os.environ["PATH"] = _BASE_PATH

    def tearDown(self):
        os.chdir(self._orig_cwd)
        os.environ["PATH"] = self._orig_path
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_floor_no_checks_enabled_exits_0(self):
        (self.repo / "checks.toml").write_text("[checks.scope]\nenabled = false\n")
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = checks.main(["--floor"])
        self.assertEqual(rc, 0)
        self.assertIn("checks: no floor checks enabled", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
