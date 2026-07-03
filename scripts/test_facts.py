#!/usr/bin/env python3
"""Tests for facts.py — stdlib unittest, no pytest.

Builds a real temporary git repo per test (setUp) and drives facts.py's
`main()` directly and checks.py's `main()` for floor-comparison tests.
Stubs are provided for built-in tools where needed; the default fixture
has all stubs present so facts run normally.
"""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import checks  # noqa: E402
import facts  # noqa: E402

_BASE_PATH = "/usr/bin:/bin"

# --- stub templates -----------------------------------------------------

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

_RADON_STUB = """\
#!/bin/sh
if [ "$1" = "--version" ] || [ "$1" = "version" ]; then
  echo "radon ${RADON_VERSION:-1.0.0}"
  exit 0
fi
echo "radon invoked: $@" >> "$STUB_INVOKE_LOG"
printf '%s' "$RADON_FIXTURE"
exit 0
"""


class FactsTestBase(unittest.TestCase):
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
        (self.repo / "a.py").write_text("def foo():\n    return 1\n")
        self._git("add", "-A")
        self._git("commit", "-m", "initial")

        self.stub_bin = self.tmpdir / "stub_bin"
        self.stub_bin.mkdir()
        self._write_generic_stub("ruff", "RUFF", "1.0.0")
        self._write_stub("gitleaks", _GITLEAKS_STUB)
        self._write_generic_stub("osv-scanner", "OSV_SCANNER", "2.4.0")
        self._write_stub("deptry", _DEPTRY_STUB)
        self._write_generic_stub("radon", "RADON", "1.0.0")
        self._write_stub("jscpd", _JSCPD_STUB)
        self._write_generic_stub("vulture", "VULTURE", "1.0.0")
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
            f"printf '%s' \"${{{env_prefix}_FIXTURE}}\"\n"
            "exit 0\n"
        )
        self._write_stub(name, body)

    def _facts_capture(self, argv: list[str]) -> tuple[int, str, str]:
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            rc = facts.main(argv)
        return rc, out_buf.getvalue(), err_buf.getvalue()

    def _checks_capture(self, argv: list[str]) -> tuple[int, str]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = checks.main(argv)
        return rc, buf.getvalue()

    def _invoke_log_lines(self) -> list[str]:
        return [line for line in self.invoke_log.read_text().splitlines() if line.strip()]


class DefaultFactsRunTest(FactsTestBase):
    """Default facts.py (no flags) runs enabled facts and exits 0."""

    def test_default_run_exits_0_and_writes_undated_output(self):
        rc, out, err = self._facts_capture([])
        self.assertEqual(rc, 0)
        # Default: scope + inventory are enabled; radon/index-coverage disabled
        facts_dir = self.repo / "output" / "facts"
        self.assertTrue(facts_dir.is_dir())
        self.assertTrue((facts_dir / "scope.json").exists())
        self.assertTrue((facts_dir / "inventory.json").exists())
        # Radon and index-coverage are disabled by default — not written
        self.assertFalse((facts_dir / "radon.json").exists())
        self.assertFalse((facts_dir / "index-coverage.json").exists())
        # Summary lines for each fact
        self.assertIn("scope:", out)
        self.assertIn("inventory:", out)
        self.assertEqual(err, "")

    def test_default_run_no_infra_fail_stderr(self):
        """Default run produces no stderr — facts don't fail on missing tools."""
        rc, out, err = self._facts_capture([])
        self.assertEqual(rc, 0)
        self.assertEqual(err, "")

    def test_list_shows_only_facts(self):
        rc, out, err = self._facts_capture(["--list"])
        self.assertEqual(rc, 0)
        lines = {line.split()[0]: line for line in out.splitlines()}
        expected_facts = {"scope", "radon", "index-coverage", "inventory"}
        self.assertEqual(set(lines), expected_facts)
        for name in expected_facts:
            self.assertIn("fact", lines[name])
        # No check-family names in the output
        self.assertNotIn("ruff", lines)
        self.assertNotIn("gitleaks", lines)
        self.assertEqual(err, "")


class CheckFamilyRejectionTest(FactsTestBase):
    """facts.py --check rejects check-family names."""

    def test_check_family_name_rejected_with_usage_error(self):
        rc, out, err = self._facts_capture(["--check", "ruff"])
        self.assertEqual(rc, 2)
        self.assertIn("ruff", err)
        self.assertIn("check-family", err)
        self.assertIn("use checks.py", err)

    def test_unknown_name_rejected(self):
        rc, out, err = self._facts_capture(["--check", "nonexistent"])
        self.assertEqual(rc, 2)
        self.assertIn("nonexistent", err)
        self.assertIn("unknown fact", err)

    def test_fact_name_accepted(self):
        rc, out, err = self._facts_capture(["--check", "inventory"])
        self.assertEqual(rc, 0)
        self.assertIn("inventory:", out)


class FloorExcludesFactsTest(FactsTestBase):
    """checks.py --floor must NOT include any fact-family entries."""

    def test_fact_names_absent_from_checks_floor(self):
        rc, out = self._checks_capture(["--floor"])
        self.assertEqual(rc, 0)
        # --floor lines are summary-line format: "name: status — n -> path"
        lines = {line.split()[0].rstrip(":"): line for line in out.splitlines()}
        # Fact-family entries must NOT appear in --floor output
        self.assertNotIn("scope", lines)
        self.assertNotIn("radon", lines)
        self.assertNotIn("index-coverage", lines)
        self.assertNotIn("inventory", lines)
        # Check-family floor entries enabled by fixture (pyproject.toml + .git)
        self.assertIn("ruff", lines)
        self.assertIn("gitleaks", lines)
        self.assertIn("deptry", lines)


class InventoryAuditAnchorTest(FactsTestBase):
    """Inventory's audit_anchor field reflects the latest audit/* tag."""

    def test_no_tag_returns_null_anchor(self):
        rc, out, err = self._facts_capture(["--check", "inventory"])
        self.assertEqual(rc, 0)
        facts_dir = self.repo / "output" / "facts"
        data = json.loads((facts_dir / "inventory.json").read_text())
        anchor = data["audit_anchor"]
        self.assertIsNone(anchor["tag"])
        self.assertIsNone(anchor["commits_since"])
        self.assertEqual(err, "")

    def test_audit_tag_returns_tag_and_commits_since(self):
        # Create an audit tag at the current commit
        self._git("tag", "-a", "audit/2026-01-01", "-m", "audit anchor 2026-01-01")
        # Add more commits after the tag
        (self.repo / "b.py").write_text("y = 2\n")
        self._git("add", "-A")
        self._git("commit", "-m", "second commit")

        rc, out, err = self._facts_capture(["--check", "inventory"])
        self.assertEqual(rc, 0)
        facts_dir = self.repo / "output" / "facts"
        data = json.loads((facts_dir / "inventory.json").read_text())
        anchor = data["audit_anchor"]
        self.assertEqual(anchor["tag"], "audit/2026-01-01")
        self.assertEqual(anchor["commits_since"], 1)  # 1 commit after tag
        self.assertEqual(err, "")

    def test_non_audit_tag_not_picked_up(self):
        # Create a non-audit/* tag — must NOT be picked up
        self._git("tag", "-a", "v1.0", "-m", "release 1.0")
        # Also create a tag with 'audit' in the name but wrong prefix
        self._git("tag", "-a", "pre-audit/test", "-m", "some other tag")

        rc, out, err = self._facts_capture(["--check", "inventory"])
        self.assertEqual(rc, 0)
        facts_dir = self.repo / "output" / "facts"
        data = json.loads((facts_dir / "inventory.json").read_text())
        anchor = data["audit_anchor"]
        # Neither tag matches "audit/*" glob
        self.assertIsNone(anchor["tag"])
        self.assertIsNone(anchor["commits_since"])
        self.assertEqual(err, "")

    def test_audit_tag_with_two_commits_after(self):
        self._git("tag", "-a", "audit/2026-06-01", "-m", "audit anchor")
        (self.repo / "c.py").write_text("z = 3\n")
        self._git("add", "-A")
        self._git("commit", "-m", "commit 1")
        (self.repo / "d.py").write_text("w = 4\n")
        self._git("add", "-A")
        self._git("commit", "-m", "commit 2")

        rc, out, err = self._facts_capture(["--check", "inventory"])
        self.assertEqual(rc, 0)
        facts_dir = self.repo / "output" / "facts"
        data = json.loads((facts_dir / "inventory.json").read_text())
        anchor = data["audit_anchor"]
        self.assertEqual(anchor["tag"], "audit/2026-06-01")
        self.assertEqual(anchor["commits_since"], 2)
        self.assertEqual(err, "")

    def test_multiple_audit_tags_picks_latest(self):
        self._git("tag", "-a", "audit/2025-01-01", "-m", "old anchor")
        time.sleep(1.1)  # ensure distinct creatordate for sort determinism
        self._git("tag", "-a", "audit/2026-01-01", "-m", "newer anchor")
        # commit after newer tag
        (self.repo / "e.py").write_text("v = 5\n")
        self._git("add", "-A")
        self._git("commit", "-m", "after newer")

        rc, out, err = self._facts_capture(["--check", "inventory"])
        self.assertEqual(rc, 0)
        facts_dir = self.repo / "output" / "facts"
        data = json.loads((facts_dir / "inventory.json").read_text())
        anchor = data["audit_anchor"]
        self.assertEqual(anchor["tag"], "audit/2026-01-01")
        self.assertEqual(anchor["commits_since"], 1)


class RadonAbsentDegradationTest(FactsTestBase):
    """Radon absent does NOT fail a facts run — graceful degradation."""

    def test_radon_absent_with_config_enabled_still_exits_0(self):
        # Enable radon, then remove its stub
        (self.repo / "checks.toml").write_text("[checks.radon]\nenabled = true\n")
        os.remove(self.stub_bin / "radon")

        rc, out, err = self._facts_capture([])
        self.assertEqual(rc, 0)
        # Radon appears in output (may show INFRA-FAIL since the binary is
        # absent, but the overall process exits 0 — graceful degradation).
        self.assertIn("radon:", out)
        # Other facts still ran
        self.assertIn("scope:", out)
        self.assertIn("inventory:", out)


class FactsListSummaryTest(FactsTestBase):
    """facts.py --list has no summary line for unavailable check-family entries."""

    def test_list_no_unavailable_summary(self):
        """facts.py --list never prints the 'N check(s) unavailable' line
        since it only lists fact-family entries."""
        rc, out, err = self._facts_capture(["--list"])
        self.assertEqual(rc, 0)
        # The checks.py summary line refers to "check(s) unavailable"
        self.assertNotIn("check(s) unavailable", out)
        self.assertEqual(err, "")


if __name__ == "__main__":
    unittest.main()
