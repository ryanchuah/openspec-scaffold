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
        self._write_generic_stub("bandit", "BANDIT")
        self._write_generic_stub("semgrep", "SEMGREP")
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
        os.environ["BANDIT_FIXTURE"] = json.dumps({"results": []})
        os.environ["SEMGREP_FIXTURE"] = json.dumps({"results": []})

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
            "test-quality",
            "data-scale",
            "spec-delta-structure",
            "notes-checkpoint-structure",
            "data-lint",
            "repo-lint",
            "radon",
            "jscpd",
            "vulture",
            "bandit",
            "semgrep",
            "index-coverage",
            "outstanding",
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
        self.assertEqual(lines["test-quality"], "enabled")
        self.assertEqual(lines["data-scale"], "enabled")
        self.assertEqual(lines["spec-delta-structure"], "enabled")
        self.assertEqual(lines["inventory"], "enabled")
        self.assertEqual(lines["outstanding"], "enabled")
        # repo-lint disabled without checks/*.py
        self.assertEqual(lines["repo-lint"], "disabled")
        # heavy checks + index-coverage default OFF absent config
        self.assertEqual(lines["radon"], "disabled")
        self.assertEqual(lines["jscpd"], "disabled")
        self.assertEqual(lines["vulture"], "disabled")
        self.assertEqual(lines["bandit"], "disabled")
        self.assertEqual(lines["semgrep"], "disabled")
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

    def test_custom_check_family_fact_registers_as_fact(self):
        (self.repo / "checks.toml").write_text(
            "[checks.custom.myfact]\n"
            'command = ["sh", "-c", "echo hello-fact"]\n'
            'tier = "floor"\n'
            'family = "fact"\n'
        )
        rc, out = self._capture(["--list"])
        self.assertEqual(rc, 0)
        line = next(line for line in out.splitlines() if line.split()[0] == "myfact")
        self.assertEqual(line.split()[2], "fact")

    def test_custom_check_family_fact_preflight_exempt(self):
        """A custom fact-family check with a missing command binary
        degrades gracefully in --report instead of INFRA-FAILing."""
        (self.repo / "checks.toml").write_text(
            "[checks.custom.missingfact]\n"
            'command = ["nonexistent-binary-xyz-123"]\n'
            'tier = "heavy"\n'
            'family = "fact"\n'
        )
        out_dir = self.tmpdir / "out4"
        out_buf, err_buf = io.StringIO(), io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            rc = checks.main(["--report", "--out", str(out_dir)])
        self.assertEqual(rc, 0)
        self.assertNotIn("INFRA-FAIL", err_buf.getvalue())

    def test_custom_check_invalid_family_falls_back_to_check_and_gates(self):
        """An unrecognized family value must fall back to check-family
        (gating-safe default), not silently become fact-exempt."""
        (self.repo / "checks.toml").write_text(
            "[checks.custom.badfamily]\n"
            'command = ["nonexistent-binary-xyz-123"]\n'
            'tier = "heavy"\n'
            'family = "banana"\n'
        )
        rc, out = self._capture(["--list"])
        self.assertEqual(rc, 0)
        line = next(line for line in out.splitlines() if line.split()[0] == "badfamily")
        self.assertEqual(line.split()[2], "check")

        out_dir = self.tmpdir / "out5"
        out_buf, err_buf = io.StringIO(), io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            rc = checks.main(["--report", "--out", str(out_dir)])
        self.assertEqual(rc, 3)
        self.assertIn("INFRA-FAIL", err_buf.getvalue())


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

    def test_bandit(self):
        os.environ["BANDIT_FIXTURE"] = json.dumps(
            {
                "results": [
                    {
                        "test_id": "B602",
                        "filename": "app.py",
                        "line_number": 12,
                        "issue_text": "subprocess call with shell=True",
                    }
                ]
            }
        )
        finding = self._run_single_check("bandit")
        self.assertEqual(finding["check"], "bandit")
        self.assertEqual(finding["rule"], "B602")
        self.assertEqual(finding["path"], "app.py")
        self.assertEqual(finding["line"], 12)
        self.assertEqual(finding["message"], "subprocess call with shell=True")

    def test_semgrep(self):
        os.environ["SEMGREP_FIXTURE"] = json.dumps(
            {
                "results": [
                    {
                        "check_id": "rules.sqli",
                        "path": "api.py",
                        "start": {"line": 7},
                        "extra": {"message": "SQL injection"},
                    }
                ]
            }
        )
        finding = self._run_single_check("semgrep")
        self.assertEqual(finding["check"], "semgrep")
        self.assertEqual(finding["rule"], "rules.sqli")
        self.assertEqual(finding["path"], "api.py")
        self.assertEqual(finding["line"], 7)
        self.assertEqual(finding["message"], "SQL injection")


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
                    "test-quality:",
                    "data-scale:",
                    "spec-delta-structure:",
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

    def test_bandit_version_recorded_never_gates(self):
        os.environ["BANDIT_VERSION"] = "9.9.9"
        out_dir = self.tmpdir / "out-bandit"
        rc, out = self._capture(["--check", "bandit", "--out", str(out_dir)])
        self.assertEqual(rc, 0)

    def test_semgrep_version_recorded_never_gates(self):
        os.environ["SEMGREP_VERSION"] = "9.9.9"
        out_dir = self.tmpdir / "out-semgrep"
        rc, out = self._capture(["--check", "semgrep", "--out", str(out_dir)])
        self.assertEqual(rc, 0)

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
        (self.repo / "checks.toml").write_text(
            "[checks.scope]\nenabled = false\n"
            "[checks.test-quality]\nenabled = false\n"
            "[checks.data-scale]\nenabled = false\n"
            "[checks.spec-delta-structure]\nenabled = false\n"
            "[checks.notes-checkpoint-structure]\nenabled = false\n"
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = checks.main(["--floor"])
        self.assertEqual(rc, 0)
        self.assertIn("checks: no floor checks enabled", buf.getvalue())


class OutstandingRegistryTest(AuditBundleTestBase):
    """Task 5.4: `outstanding` is registered as a delegate fact (D1) and its
    `--check outstanding` delegate arm actually runs the gather."""

    def test_outstanding_registered_as_delegate_fact(self):
        entry = next(c for c in checks._REGISTRY if c["name"] == "outstanding")
        self.assertEqual(entry["kind"], "delegate")
        self.assertEqual(entry["family"], "fact")
        self.assertEqual(entry["tier"], "snapshot")

    def test_check_outstanding_runs_gather_and_writes_artifacts(self):
        out_dir = self.tmpdir / "out-outstanding"
        rc, out = self._capture(["--check", "outstanding", "--out", str(out_dir)])
        self.assertEqual(rc, 0)
        self.assertTrue((out_dir / "outstanding.json").exists())
        self.assertTrue((out_dir / "outstanding.md").exists())
        self.assertIn("outstanding: ok", out)


class RepoLintDelegateTest(AuditBundleTestBase):
    """Repo-lint delegation tests: auto-detect, config disable, paths rules,
    delegate run surfaces findings."""

    def _write_py_check(self, filename: str, source: str) -> None:
        p = self.repo / "checks" / filename
        p.write_text(source, encoding="utf-8")
        p.chmod(0o755)

    def _write_passing_py_check(self) -> None:
        self._write_py_check(
            "001_pass.py",
            "#!/usr/bin/env python3\nimport sys, json\nprint(json.dumps([]))\nsys.exit(0)\n",
        )

    def _write_failing_py_check(self, n_findings: int = 1) -> None:
        import json as _json

        findings = _json.dumps(
            [
                {"path": "src/bad.py", "line": i * 10, "message": f"violation {i}"}
                for i in range(1, n_findings + 1)
            ]
        )
        self._write_py_check(
            "001_fail.py",
            f"#!/usr/bin/env python3\nimport sys, json\nprint({findings!r})\nsys.exit(0)\n",
        )

    def test_list_shows_repo_lint(self):
        repo_lint_names = [c for c in checks._REGISTRY if c["name"] == "repo-lint"]
        self.assertEqual(len(repo_lint_names), 1)
        entry = repo_lint_names[0]
        self.assertEqual(entry["tier"], "floor")
        self.assertEqual(entry["kind"], "delegate")
        self.assertEqual(entry["family"], "check")

    def test_auto_enabled_when_py_checks_exist(self):
        self._write_passing_py_check()
        # Re-compute auto-detect for this repo
        defaults = checks._autodetect_defaults(self.repo)
        self.assertTrue(defaults.get("repo-lint", False))

    def test_auto_disabled_when_only_sql_exist(self):
        # Base fixture already has checks/*.sql but NO checks/*.py
        defaults = checks._autodetect_defaults(self.repo)
        self.assertFalse(defaults.get("repo-lint", False))

    def test_explicit_disable_respected(self):
        self._write_passing_py_check()
        (self.repo / "checks.toml").write_text("[checks.repo-lint]\nenabled = false\n")
        rc, out = self._capture(["--list"])
        self.assertEqual(rc, 0)
        lines = {line.split()[0]: line.split()[3] for line in out.splitlines()}
        self.assertEqual(lines.get("repo-lint"), "disabled")

    def test_second_paths_entry_infra_fails(self):
        self._write_passing_py_check()
        # Make a second checks-like dir so the path makes sense.
        alt_dir = self.repo / "alt_checks"
        alt_dir.mkdir(exist_ok=True)
        (self.repo / "checks.toml").write_text(
            '[checks.repo-lint]\npaths = ["checks", "alt_checks"]\n'
        )
        out_dir = self.tmpdir / "out-rp"
        rc, out = self._capture(["--report", "--out", str(out_dir)])
        self.assertEqual(rc, 3)
        manifest = json.loads((out_dir / "run-manifest.json").read_text())
        record = next(r for r in manifest if r.get("check") == "repo-lint")
        self.assertEqual(record["status"], "INFRA-FAIL")
        self.assertIn("only a single checks directory", record["error"])

    def test_delegate_run_surfaces_findings_as_findings_status(self):
        self._write_failing_py_check(n_findings=2)
        out_dir = self.tmpdir / "out-rp2"
        rc, out = self._capture(["--report", "--out", str(out_dir)])
        self.assertEqual(rc, 2)
        manifest = json.loads((out_dir / "run-manifest.json").read_text())
        record = next(r for r in manifest if r.get("check") == "repo-lint")
        self.assertEqual(record["status"], "FINDINGS")
        self.assertEqual(record["count"], 2)
        self.assertTrue((out_dir / "repo-lint.json").exists())


# ===================================================================
# Group 3.4 — --include flag tests (AC2)
# ===================================================================


class IncludeFlagTest(AuditBundleTestBase):
    """Tests for --include flag on --report."""

    def test_include_without_report_exits_3(self):
        rc, _out = self._capture(["--list", "--include", "jscpd"])
        self.assertEqual(rc, 3)

    def test_include_unknown_name_exits_3(self):
        out_dir = self.tmpdir / "out-inc-unknown"
        rc, _out = self._capture(["--report", "--include", "nonexistent", "--out", str(out_dir)])
        self.assertEqual(rc, 3)

    def test_include_disabled_check_runs_with_report(self):
        """A disabled registered check runs when --include'd."""
        # jscpd is disabled by default (heavy tier) but the stub is installed.
        out_dir = self.tmpdir / "out-inc-jscpd"
        rc, out = self._capture(["--report", "--include", "jscpd", "--out", str(out_dir)])
        self.assertEqual(rc, 0)
        self.assertIn("jscpd: ok — 0 findings ->", out)

    def test_include_with_missing_tool_preflight_fails(self):
        """Missing included tool fails preflight with standard guidance."""
        # Remove vulture stub.
        vulture_stub = self.stub_bin / "vulture"
        if vulture_stub.exists():
            vulture_stub.unlink()
        out_dir = self.tmpdir / "out-inc-vulture"
        rc, _out = self._capture(["--report", "--include", "vulture", "--out", str(out_dir)])
        self.assertEqual(rc, 3)


# ===================================================================
# Group 3.4 — composition_anchor inventory tests (AC4)
# ===================================================================


class CompositionAnchorTest(AuditBundleTestBase):
    """Tests for the composition_anchor sibling in the inventory fact."""

    def _run_inventory(self, out_dir: Path | None = None) -> dict:
        out_dir = out_dir or self.tmpdir / "out-inv"
        rc, out = self._capture(["--check", "inventory", "--out", str(out_dir)])
        self.assertEqual(rc, 0)
        return json.loads((out_dir / "inventory.json").read_text())

    def test_no_composition_tag_yields_null_anchor(self):
        data = self._run_inventory()
        ca = data.get("composition_anchor", {})
        self.assertIsNone(ca.get("tag"))
        # commits_since is the full-history commit count when no tag.
        import subprocess

        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=str(self.repo),
            capture_output=True,
            text=True,
        )
        full_count = int(result.stdout.strip())
        self.assertIsInstance(ca.get("commits_since"), int)
        self.assertEqual(ca.get("commits_since"), full_count)

    def test_composition_anchor_present_after_composition_tag(self):
        self._git("tag", "-a", "audit/2026-07-11-composition", "-m", "anchor", "HEAD")
        data = self._run_inventory()
        ca = data.get("composition_anchor", {})
        self.assertEqual(ca.get("tag"), "audit/2026-07-11-composition")
        self.assertEqual(ca.get("commits_since"), 0)

    def test_sibling_anchors_diverge_after_plain_tag(self):
        """Plain audit tag advances audit_anchor but NOT composition_anchor."""
        self._git("tag", "-a", "audit/2026-07-11-composition", "-m", "comp", "HEAD")
        # Add a commit then a plain tag — force distinct creator date.
        import time

        (self.repo / "b.py").write_text("y = 2\n")
        self._git("add", "-A")
        self._git("commit", "-m", "second")
        time.sleep(1.1)
        self._git("tag", "-a", "audit/2026-07-12", "-m", "plain", "HEAD")

        data = self._run_inventory()
        aa = data.get("audit_anchor", {})
        ca = data.get("composition_anchor", {})

        # audit_anchor reports the latest audit/* tag (the plain one).
        self.assertEqual(aa.get("tag"), "audit/2026-07-12")
        # composition_anchor stays on the composition tag.
        self.assertEqual(ca.get("tag"), "audit/2026-07-11-composition")


class TestQualityDetectorTest(AuditBundleTestBase):
    """Tests for the test-quality in-process AST detector."""

    def _write_source(self, filename: str, source: str) -> Path:
        p = self.repo / filename
        p.write_text(source, encoding="utf-8")
        self._git("add", str(p.name))
        return p

    def test_all_rules_flagged_in_test_file(self):
        """test-quality flags all six rules in a single test file."""
        source = """\
import time
from datetime import datetime, timezone
from unittest.mock import patch


def test_trivial():
    assert True


def test_forced_green():
    x = compute()
    assert x or True


def test_empty():
    pass


def test_clock():
    now = datetime.now()
    utc = datetime.utcnow()
    t = time.time()


def test_discard():
    result, _ = some_call()


def test_self_mock():
    patch("sample.do_stuff")
    patch.object(widget, "do_stuff")
"""
        self._write_source("test_sample.py", source)

        out_dir = self.tmpdir / "out-tq"
        rc, out = self._capture(["--check", "test-quality", "--out", str(out_dir)])
        self.assertEqual(rc, 2, f"expected FINDINGS, got rc={rc}, out={out!r}")
        data = json.loads((out_dir / "test-quality.json").read_text())

        # Build a map of rule -> finding for assertion
        findings_by_rule = {}
        for f in data:
            self.assertEqual(f["check"], "test-quality")
            self.assertEqual(f["path"], "test_sample.py")
            findings_by_rule[f["rule"]] = f

        self.assertIn("assert-true", findings_by_rule)
        self.assertEqual(findings_by_rule["assert-true"]["line"], 7)

        self.assertIn("assert-or-true", findings_by_rule)
        self.assertEqual(findings_by_rule["assert-or-true"]["line"], 12)

        self.assertIn("empty-test", findings_by_rule)
        self.assertEqual(findings_by_rule["empty-test"]["line"], 15)

        self.assertIn("unfrozen-clock", findings_by_rule)
        self.assertIn("advisory:", findings_by_rule["unfrozen-clock"]["message"])
        # unfrozen-clock fires on every wall-clock call in the fixture; assert membership
        # (order-independent) rather than the last-walked instance.
        unfrozen_lines = {f["line"] for f in data if f["rule"] == "unfrozen-clock"}
        self.assertIn(22, unfrozen_lines)

        self.assertIn("discarded-return-flag", findings_by_rule)
        self.assertIn("advisory:", findings_by_rule["discarded-return-flag"]["message"])
        self.assertEqual(findings_by_rule["discarded-return-flag"]["line"], 26)

        self.assertIn("self-mock", findings_by_rule)
        self.assertEqual(findings_by_rule["self-mock"]["line"], 30)

    def test_non_test_file_not_scanned(self):
        """test-quality produces zero findings on non-test files."""
        self._write_source(
            "sample.py",
            "assert True\nassert x or True\nfrom datetime import datetime\nnow = datetime.now()\n",
        )
        out_dir = self.tmpdir / "out-tq-neg"
        rc, out = self._capture(["--check", "test-quality", "--out", str(out_dir)])
        self.assertEqual(rc, 0)
        data = json.loads((out_dir / "test-quality.json").read_text())
        self.assertEqual(data, [])

    def test_empty_test_with_only_docstring(self):
        """An empty test body with only a docstring is flagged."""
        self._write_source(
            "test_doc.py",
            'def test_do_nothing():\n    """This test does nothing."""\n    pass\n',
        )
        out_dir = self.tmpdir / "out-tq-empty"
        rc, out = self._capture(["--check", "test-quality", "--out", str(out_dir)])
        self.assertEqual(rc, 2)
        data = json.loads((out_dir / "test-quality.json").read_text())
        rules = {f["rule"] for f in data}
        self.assertIn("empty-test", rules)

    def test_self_mock_with_mock_patch(self):
        """self-mock via mock.patch is detected."""
        self._write_source(
            "test_widget.py",
            'from unittest import mock\nmock.patch("widget.do_stuff")\n',
        )
        out_dir = self.tmpdir / "out-tq-sm"
        rc, out = self._capture(["--check", "test-quality", "--out", str(out_dir)])
        self.assertEqual(rc, 2)
        data = json.loads((out_dir / "test-quality.json").read_text())
        rules = {f["rule"] for f in data}
        self.assertIn("self-mock", rules)

    def test_hidden_dir_skipped(self):
        """test-quality skips files inside hidden directories."""
        hidden_dir = self.repo / ".hidden"
        hidden_dir.mkdir()
        (hidden_dir / "test_skipme.py").write_text("def test_x():\n    assert True\n")
        out_dir = self.tmpdir / "out-tq-hidden"
        rc, out = self._capture(["--check", "test-quality", "--out", str(out_dir)])
        self.assertEqual(rc, 0)
        data = json.loads((out_dir / "test-quality.json").read_text())
        self.assertEqual(data, [])


class DataScaleDetectorTest(AuditBundleTestBase):
    """Tests for the data-scale in-process AST detector."""

    def _write_source(self, filename: str, source: str) -> Path:
        p = self.repo / filename
        p.write_text(source, encoding="utf-8")
        self._git("add", str(p.name))
        return p

    def test_fetchall_flagged_in_source(self):
        """data-scale flags .fetchall() in non-test source."""
        self._write_source(
            "db.py",
            "def get_all():\n    cur = conn.cursor()\n    rows = cur.fetchall()\n    return rows\n",
        )
        out_dir = self.tmpdir / "out-ds"
        rc, out = self._capture(["--check", "data-scale", "--out", str(out_dir)])
        self.assertEqual(rc, 2, f"expected FINDINGS, got rc={rc}, out={out!r}")
        data = json.loads((out_dir / "data-scale.json").read_text())
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["check"], "data-scale")
        self.assertEqual(data[0]["rule"], "unbounded-fetchall")
        self.assertEqual(data[0]["path"], "db.py")
        self.assertEqual(data[0]["line"], 3)
        self.assertIn("fetchall", data[0]["message"])

    def test_fetchall_in_test_file_not_flagged(self):
        """data-scale does not flag .fetchall() in test files."""
        self._write_source(
            "test_db.py",
            "def test_fetch():\n    rows = cur.fetchall()\n    assert len(rows) > 0\n",
        )
        out_dir = self.tmpdir / "out-ds-neg"
        rc, out = self._capture(["--check", "data-scale", "--out", str(out_dir)])
        self.assertEqual(rc, 0)
        data = json.loads((out_dir / "data-scale.json").read_text())
        self.assertEqual(data, [])


class SpecDeltaStructureDetectorTest(AuditBundleTestBase):
    """Tests for the spec-delta-structure in-process delta validator."""

    def _write_spec_delta(self, rel_path: str, content: str) -> Path:
        p = self.repo / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        self._git("add", str(p))
        self._git("commit", "-m", f"add {rel_path}")
        return p

    def test_missing_delta_header_flagged(self):
        """A delta with ### Requirement: but no ## ... Requirements header."""
        self._write_spec_delta(
            "openspec/changes/mychange/specs/cap/spec.md",
            "# Delta — mychange\n\n"
            "### Requirement: Something\n"
            "SHALL do something.\n\n"
            "#### Scenario: Happy\n"
            "- **WHEN** x\n"
            "- **THEN** y\n",
        )
        out_dir = self.tmpdir / "out-sds-missing"
        rc, out = self._capture(["--check", "spec-delta-structure", "--out", str(out_dir)])
        self.assertEqual(rc, 2)
        data = json.loads((out_dir / "spec-delta-structure.json").read_text())
        rules = {f["rule"] for f in data}
        self.assertIn("missing-delta-header", rules)
        for f in data:
            self.assertEqual(f["check"], "spec-delta-structure")

    def test_shall_not_first_line_flagged(self):
        """An ADDED requirement whose SHALL is not on the first body line."""
        self._write_spec_delta(
            "openspec/changes/mychange/specs/cap/spec.md",
            "# Delta — mychange\n\n"
            "## ADDED Requirements\n\n"
            "### Requirement: Late shall\n"
            "Some prose introduction.\n"
            "SHALL do this thing.\n\n"
            "#### Scenario: Test\n"
            "- **WHEN** x\n"
            "- **THEN** y\n",
        )
        out_dir = self.tmpdir / "out-sds-shall"
        rc, out = self._capture(["--check", "spec-delta-structure", "--out", str(out_dir)])
        self.assertEqual(rc, 2)
        data = json.loads((out_dir / "spec-delta-structure.json").read_text())
        rules = {f["rule"] for f in data}
        self.assertIn("shall-not-first-line", rules)
        # The finding should point to the requirement header line
        shall_findings = [f for f in data if f["rule"] == "shall-not-first-line"]
        self.assertEqual(len(shall_findings), 1)
        self.assertIn("Late shall", shall_findings[0]["message"])

    def test_requirement_no_scenario_flagged(self):
        """An ADDED requirement with no #### Scenario: block."""
        self._write_spec_delta(
            "openspec/changes/mychange/specs/cap/spec.md",
            "# Delta — mychange\n\n"
            "## ADDED Requirements\n\n"
            "### Requirement: No scenario\n"
            "SHALL do something.\n",
        )
        out_dir = self.tmpdir / "out-sds-noscen"
        rc, out = self._capture(["--check", "spec-delta-structure", "--out", str(out_dir)])
        self.assertEqual(rc, 2)
        data = json.loads((out_dir / "spec-delta-structure.json").read_text())
        rules = {f["rule"] for f in data}
        self.assertIn("requirement-no-scenario", rules)
        no_scen_findings = [f for f in data if f["rule"] == "requirement-no-scenario"]
        self.assertEqual(len(no_scen_findings), 1)
        self.assertIn("No scenario", no_scen_findings[0]["message"])

    def test_multisection_added_requirement_no_scenario_flagged(self):
        """An ADDED requirement with no scenarios followed by a MODIFIED section
        IS flagged — the section-header boundary must not swallow the finding."""
        self._write_spec_delta(
            "openspec/changes/mychange/specs/cap/spec.md",
            "# Delta — mychange\n\n"
            "## ADDED Requirements\n\n"
            "### Requirement: Foo\n"
            "Foo SHALL do X.\n\n"
            "## MODIFIED Requirements\n\n"
            "### Requirement: Bar\n"
            "Bar SHALL do Y.\n\n"
            "#### Scenario: s\n"
            "- **WHEN** a\n"
            "- **THEN** b\n",
        )
        out_dir = self.tmpdir / "out-sds-multisection"
        rc, out = self._capture(["--check", "spec-delta-structure", "--out", str(out_dir)])
        self.assertEqual(rc, 2)
        data = json.loads((out_dir / "spec-delta-structure.json").read_text())
        no_scen_findings = [f for f in data if f["rule"] == "requirement-no-scenario"]
        self.assertEqual(len(no_scen_findings), 1)
        self.assertIn("Foo", no_scen_findings[0]["message"])
        # Bar has a scenario and must NOT be flagged.
        bar_findings = [f for f in no_scen_findings if "Bar" in f["message"]]
        self.assertEqual(len(bar_findings), 0)

    def test_well_formed_delta_zero_findings(self):
        """A well-formed delta with MODIFIED requirement SHALL on line 2."""
        self._write_spec_delta(
            "openspec/changes/mychange/specs/cap/spec.md",
            "# Delta — mychange\n\n"
            "## MODIFIED Requirements\n\n"
            "### Requirement: Clean requirement\n"
            "SHALL do this.\n\n"
            "#### Scenario: Test\n"
            "- **WHEN** x\n"
            "- **THEN** y\n",
        )
        out_dir = self.tmpdir / "out-sds-clean"
        rc, out = self._capture(["--check", "spec-delta-structure", "--out", str(out_dir)])
        self.assertEqual(rc, 0)
        data = json.loads((out_dir / "spec-delta-structure.json").read_text())
        self.assertEqual(data, [])

    def test_archive_dir_not_scanned(self):
        """Deltas under openspec/changes/archive/ are not scanned."""
        self._write_spec_delta(
            "openspec/changes/archive/oldchange/specs/cap/spec.md",
            "# Delta — old\n\n### Requirement: Something\nSHALL do something.\n",
        )
        # Also put a clean change that would normally flag if scanned
        self._write_spec_delta(
            "openspec/changes/active/specs/cap/spec.md",
            "# Delta — active\n\n"
            "## ADDED Requirements\n\n"
            "### Requirement: Good\n"
            "SHALL work.\n\n"
            "#### Scenario: Test\n"
            "- **WHEN** x\n"
            "- **THEN** y\n",
        )
        out_dir = self.tmpdir / "out-sds-archive"
        rc, out = self._capture(["--check", "spec-delta-structure", "--out", str(out_dir)])
        self.assertEqual(rc, 0)
        data = json.loads((out_dir / "spec-delta-structure.json").read_text())
        self.assertEqual(data, [])

    def test_hidden_change_dir_not_scanned(self):
        """A .-prefixed change directory is not scanned."""
        self._write_spec_delta(
            "openspec/changes/.hidden/specs/cap/spec.md",
            "# Delta — hidden\n\n### Requirement: Hidden\nSHALL do something.\n",
        )
        out_dir = self.tmpdir / "out-sds-hidden"
        rc, out = self._capture(["--check", "spec-delta-structure", "--out", str(out_dir)])
        self.assertEqual(rc, 0)
        data = json.loads((out_dir / "spec-delta-structure.json").read_text())
        self.assertEqual(data, [])

    def test_shall_on_first_line_clean(self):
        """MODIFIED requirement whose SHALL is on the first body line -> clean."""
        self._write_spec_delta(
            "openspec/changes/mychange/specs/cap/spec.md",
            "# Delta — mychange\n\n"
            "## MODIFIED Requirements\n\n"
            "### Requirement: Good shall\n"
            "SHALL do this thing correctly.\n"
            "Some additional context.\n\n"
            "#### Scenario: Test\n"
            "- **WHEN** x\n"
            "- **THEN** y\n",
        )
        out_dir = self.tmpdir / "out-sds-shall-ok"
        rc, out = self._capture(["--check", "spec-delta-structure", "--out", str(out_dir)])
        self.assertEqual(rc, 0)
        data = json.loads((out_dir / "spec-delta-structure.json").read_text())
        self.assertEqual(data, [])


class NotesCheckpointStructureDetectorTest(AuditBundleTestBase):
    """Tests for the notes-checkpoint-structure in-process detector."""

    def _write_all_x_tasks(self, change_name: str = "active") -> Path:
        """Create a change dir with all-[x] tasks.md (verify-due)."""
        change_dir = self.repo / "openspec" / "changes" / change_name
        change_dir.mkdir(parents=True, exist_ok=True)
        tasks = change_dir / "tasks.md"
        tasks.write_text(
            "- [x] T1: First task done\n- [x] T2: Second task done\n",
            encoding="utf-8",
        )
        self._git("add", str(tasks))
        self._git("commit", "-m", f"add all-x tasks.md for {change_name}")
        return change_dir

    def _write_wip_tasks(self, change_name: str = "wip") -> Path:
        """Create a change dir with a mix of [x] and [ ] tasks (WIP)."""
        change_dir = self.repo / "openspec" / "changes" / change_name
        change_dir.mkdir(parents=True, exist_ok=True)
        tasks = change_dir / "tasks.md"
        tasks.write_text(
            "- [x] T1: Done\n- [ ] T2: Still working\n",
            encoding="utf-8",
        )
        self._git("add", str(tasks))
        self._git("commit", "-m", f"add wip tasks.md for {change_name}")
        return change_dir

    def _write_no_checkbox_tasks(self, change_name: str = "no-checkbox") -> Path:
        """Create a change dir with tasks.md but no checkbox lines."""
        change_dir = self.repo / "openspec" / "changes" / change_name
        change_dir.mkdir(parents=True, exist_ok=True)
        tasks = change_dir / "tasks.md"
        tasks.write_text("# Just a list\n- A bullet\n- Another bullet\n", encoding="utf-8")
        self._git("add", str(tasks))
        self._git("commit", "-m", f"add no-checkbox tasks.md for {change_name}")
        return change_dir

    def _write_checkpoint_notes(
        self, change_dir: Path, *, missing_fields: list[str] | None = None, no_heading: bool = False
    ) -> None:
        """Write notes.md with a verify-checkpoint section.
        If *missing_fields* is given, those field keywords are omitted from the checkpoint.
        If *no_heading* is True, the heading is omitted entirely.
        """
        lines = []
        lines.append("# Change Notes\n\n")
        if not no_heading:
            lines.append("## Verify Checkpoint\n\n")
            lines.append("**Verdict:** ready for archive\n\n")
            lines.append("**Live output:** ran the suite, all passed\n\n")
            lines.append("**Defect:** none found\n\n")
            lines.append("**As-built delta:** no drift from design\n\n")
            lines.append("**Forward-looking items:** confirm in next session\n\n")

        if missing_fields:
            # Remove sections whose keyword matches
            field_keywords = {
                1: "verdict",
                2: "live output",
                3: "defect",
                4: "as-built",
                5: "forward-looking",
            }
            filtered = []
            skip_keywords = set()
            for fid in missing_fields:
                skip_keywords.add(field_keywords[fid].lower())
            for line in lines:
                should_skip = False
                for kw in skip_keywords:
                    if kw in line.lower():
                        should_skip = True
                        break
                if not should_skip:
                    filtered.append(line)
            lines = filtered

        notes = change_dir / "notes.md"
        notes.write_text("".join(lines), encoding="utf-8")
        self._git("add", str(notes))
        self._git("commit", "-m", "add notes.md")

    def test_registry_entries(self):
        """notes-checkpoint-structure is registered, floor, check, builtin."""
        entry = next(c for c in checks._REGISTRY if c["name"] == "notes-checkpoint-structure")
        self.assertEqual(entry["tier"], "floor")
        self.assertEqual(entry["family"], "check")
        self.assertEqual(entry["kind"], "builtin")

    def test_list_shows_enabled(self):
        """--list shows notes-checkpoint-structure as enabled."""
        rc, out = self._capture(["--list"])
        self.assertEqual(rc, 0)
        lines = {line.split()[0]: line.split()[3] for line in out.splitlines()}
        self.assertEqual(lines.get("notes-checkpoint-structure"), "enabled")

    def test_autodetect_enables(self):
        """notes-checkpoint-structure is enabled by default (autodetect)."""
        defaults = checks._autodetect_defaults(self.repo)
        self.assertTrue(defaults.get("notes-checkpoint-structure", False))

    def test_always_available(self):
        """notes-checkpoint-structure reports available without probing a binary."""
        entry = next(c for c in checks._REGISTRY if c["name"] == "notes-checkpoint-structure")
        avail = checks._availability_for_check(entry, {})
        self.assertEqual(avail["status"], "available")

    def test_checkpoint_missing_flagged(self):
        """All-[x] tasks + notes.md without checkpoint heading => checkpoint-missing."""
        change_dir = self._write_all_x_tasks("checkpoint-missing")
        self._write_checkpoint_notes(change_dir, no_heading=True)

        out_dir = self.tmpdir / "out-ncs-cpm"
        rc, out = self._capture(["--check", "notes-checkpoint-structure", "--out", str(out_dir)])
        self.assertEqual(rc, 2)
        data = json.loads((out_dir / "notes-checkpoint-structure.json").read_text())
        rules = {f["rule"] for f in data}
        self.assertIn("checkpoint-missing", rules)
        for f in data:
            self.assertEqual(f["check"], "notes-checkpoint-structure")

    def test_notes_missing_flagged(self):
        """All-[x] tasks + no notes.md => notes-missing."""
        self._write_all_x_tasks("notes-missing")
        out_dir = self.tmpdir / "out-ncs-nm"
        rc, out = self._capture(["--check", "notes-checkpoint-structure", "--out", str(out_dir)])
        self.assertEqual(rc, 2)
        data = json.loads((out_dir / "notes-checkpoint-structure.json").read_text())
        rules = {f["rule"] for f in data}
        self.assertIn("notes-missing", rules)

    def test_checkpoint_field_missing_flagged(self):
        """Checkpoint present but one field missing => checkpoint-field-missing."""
        change_dir = self._write_all_x_tasks("field-missing")
        self._write_checkpoint_notes(change_dir, missing_fields=[3])  # omit "defect"

        out_dir = self.tmpdir / "out-ncs-cfm"
        rc, out = self._capture(["--check", "notes-checkpoint-structure", "--out", str(out_dir)])
        self.assertEqual(rc, 2)
        data = json.loads((out_dir / "notes-checkpoint-structure.json").read_text())
        field_findings = [f for f in data if f["rule"] == "checkpoint-field-missing"]
        self.assertGreaterEqual(len(field_findings), 1)
        # The missing field message should mention "defect"
        self.assertTrue(
            any("defect" in f["message"].lower() for f in field_findings),
            msg=f"No finding mentions defect among {field_findings}",
        )

    def test_clean_checkpoint_zero_findings(self):
        """Well-formed all-[x] tasks + fully populated checkpoint => no findings."""
        change_dir = self._write_all_x_tasks("clean-chk")
        self._write_checkpoint_notes(change_dir)

        out_dir = self.tmpdir / "out-ncs-clean"
        rc, out = self._capture(["--check", "notes-checkpoint-structure", "--out", str(out_dir)])
        self.assertEqual(rc, 0)
        data = json.loads((out_dir / "notes-checkpoint-structure.json").read_text())
        self.assertEqual(data, [])

    def test_wip_tasks_skipped(self):
        """A change with any unchecked [ ] produces no findings (WIP skip)."""
        self._write_wip_tasks("wip-change")

        out_dir = self.tmpdir / "out-ncs-wip"
        rc, out = self._capture(["--check", "notes-checkpoint-structure", "--out", str(out_dir)])
        self.assertEqual(rc, 0)
        data = json.loads((out_dir / "notes-checkpoint-structure.json").read_text())
        self.assertEqual(data, [])

    def test_no_checkbox_tasks_skipped(self):
        """tasks.md with zero checkbox lines => skip (no findings)."""
        self._write_no_checkbox_tasks("no-checkbox")

        out_dir = self.tmpdir / "out-ncs-nocb"
        rc, out = self._capture(["--check", "notes-checkpoint-structure", "--out", str(out_dir)])
        self.assertEqual(rc, 0)
        data = json.loads((out_dir / "notes-checkpoint-structure.json").read_text())
        self.assertEqual(data, [])

    def test_absent_tasks_skipped(self):
        """No tasks.md file => skip (no findings)."""
        change_dir = self.repo / "openspec" / "changes" / "no-tasks"
        change_dir.mkdir(parents=True, exist_ok=True)
        notes = change_dir / "notes.md"
        notes.write_text("## Verify Checkpoint\n\n**Verdict:** pass\n", encoding="utf-8")
        self._git("add", str(notes))
        self._git("commit", "-m", "add notes without tasks.md")

        out_dir = self.tmpdir / "out-ncs-notasks"
        rc, out = self._capture(["--check", "notes-checkpoint-structure", "--out", str(out_dir)])
        self.assertEqual(rc, 0)
        data = json.loads((out_dir / "notes-checkpoint-structure.json").read_text())
        self.assertEqual(data, [])

    def test_archive_dir_not_scanned(self):
        """Changes under openspec/changes/archive/ are not scanned."""
        archive_dir = self.repo / "openspec" / "changes" / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        archived = archive_dir / "old"
        archived.mkdir()
        tasks = archived / "tasks.md"
        tasks.write_text("- [x] T1: Done\n", encoding="utf-8")
        self._git("add", str(tasks))
        self._git("commit", "-m", "add archived change")

        out_dir = self.tmpdir / "out-ncs-archive"
        rc, out = self._capture(["--check", "notes-checkpoint-structure", "--out", str(out_dir)])
        self.assertEqual(rc, 0)
        data = json.loads((out_dir / "notes-checkpoint-structure.json").read_text())
        self.assertEqual(data, [])


class CheckOutputDirDefaultTest(AuditBundleTestBase):
    """Tests for the --check output dir default change (D6 / L5)."""

    def test_check_default_writes_to_output_checks(self):
        """--check <name> without --out writes output/checks/<name>.json."""
        rc, out = self._capture(["--check", "inventory"])
        self.assertEqual(rc, 0)
        expected = self.repo / "output" / "checks" / "inventory.json"
        self.assertTrue(
            expected.exists(),
            msg=f"expected output/checks/inventory.json, cwd files: {list(self.repo.iterdir())}",
        )
        # CWD should remain clean — no inventory.json at repo root
        cwd_json = self.repo / "inventory.json"
        self.assertFalse(cwd_json.exists(), msg="inventory.json should NOT be at repo root")


if __name__ == "__main__":
    unittest.main()
