#!/usr/bin/env python3
"""Tests for repo_lint.py — stdlib unittest, no pytest (matching test_data_lint.py style).

Check files are small Python scripts that exercise the subprocess path.
"""

from __future__ import annotations

import io
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import repo_lint  # noqa: E402


class RepoLintTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.checks_dir = self.tmpdir / "checks"
        self.checks_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_check(self, filename: str, source: str) -> Path:
        p = self.checks_dir / filename
        p.write_text(source, encoding="utf-8")
        p.chmod(0o755)
        return p

    def _write_passing_check(self, filename: str) -> Path:
        return self._write_check(
            filename,
            "#!/usr/bin/env python3\nimport sys, json\nprint(json.dumps([]))\nsys.exit(0)\n",
        )

    def _write_finding_check(self, filename: str, n_findings: int = 1) -> Path:
        findings = json.dumps(
            [
                {"path": "src/bad.py", "line": i * 10, "message": f"violation {i}"}
                for i in range(1, n_findings + 1)
            ]
        )
        return self._write_check(
            filename,
            f"#!/usr/bin/env python3\nimport sys, json\nprint({findings!r})\nsys.exit(0)\n",
        )

    def _write_non_json_check(self, filename: str) -> Path:
        return self._write_check(
            filename,
            "#!/usr/bin/env python3\nimport sys\nprint('this is not json')\nsys.exit(0)\n",
        )

    def _write_nonzero_exit_check(self, filename: str) -> Path:
        return self._write_check(
            filename,
            "#!/usr/bin/env python3\n"
            "import sys\n"
            "print('crash message', file=sys.stderr)\n"
            "sys.exit(1)\n",
        )

    def _write_hanging_check(self, filename: str) -> Path:
        return self._write_check(
            filename,
            "#!/usr/bin/env python3\nimport sys, time\ntime.sleep(999)\nprint('[]')\nsys.exit(0)\n",
        )

    def _write_sentinel_check(self, filename: str, sentinel_path: Path) -> Path:
        """A check that writes a sentinel file when executed (used to prove
        a later check was NOT run after an infra failure)."""
        return self._write_check(
            filename,
            "#!/usr/bin/env python3\n"
            f"import sys\n"
            f"open({str(sentinel_path)!r}, 'w').write('ran')\n"
            "import json\n"
            "print(json.dumps([]))\n"
            "sys.exit(0)\n",
        )

    def _capture(self, argv: list[str]) -> tuple[int, str, str]:
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            rc = repo_lint.main(argv)
        return rc, out_buf.getvalue(), err_buf.getvalue()

    # ------------------------------------------------------------------

    def test_clean_check_exit_0(self):
        self._write_passing_check("001_pass.py")
        json_path = self.tmpdir / "out.json"
        rc, out, err = self._capture(
            [
                "--checks-dir",
                str(self.checks_dir),
                "--json",
                str(json_path),
            ]
        )
        self.assertEqual(rc, 0)
        data = json.loads(json_path.read_text())
        self.assertEqual(data["generated_by"], "repo_lint.py")
        self.assertEqual(len(data["checks"]), 1)
        self.assertEqual(data["checks"][0]["status"], "pass")
        self.assertEqual(data["checks"][0]["findings"], 0)
        self.assertEqual(data["checks"][0]["sample"], [])
        self.assertIn("repo_lint/001_pass: pass — 0 findings", out)
        self.assertIn("repo_lint: clean ->", out)
        self.assertEqual(err, "")

    def test_finding_check_exit_2_with_count_and_capped_sample(self):
        self._write_finding_check("001_fail.py", n_findings=3)
        json_path = self.tmpdir / "out.json"
        rc, out, err = self._capture(
            [
                "--checks-dir",
                str(self.checks_dir),
                "--json",
                str(json_path),
            ]
        )
        self.assertEqual(rc, 2)
        data = json.loads(json_path.read_text())
        entry = data["checks"][0]
        self.assertEqual(entry["status"], "fail")
        self.assertEqual(entry["findings"], 3)
        self.assertEqual(len(entry["sample"]), 3)
        self.assertEqual(
            entry["sample"][0], {"path": "src/bad.py", "line": 10, "message": "violation 1"}
        )
        self.assertIn("repo_lint/001_fail: FAIL — 3 findings", out)
        self.assertIn("repo_lint: 1 check(s) failing ->", out)

    def test_sample_capped_at_max_sample(self):
        self._write_finding_check("001_fail.py", n_findings=10)
        json_path = self.tmpdir / "out.json"
        rc, out, err = self._capture(
            [
                "--checks-dir",
                str(self.checks_dir),
                "--json",
                str(json_path),
                "--max-sample",
                "2",
            ]
        )
        self.assertEqual(rc, 2)
        data = json.loads(json_path.read_text())
        entry = data["checks"][0]
        self.assertEqual(entry["findings"], 10)
        self.assertEqual(len(entry["sample"]), 2)

    def test_non_json_stdout_exit_3(self):
        self._write_non_json_check("001_bad.py")
        json_path = self.tmpdir / "out.json"
        rc, out, err = self._capture(
            [
                "--checks-dir",
                str(self.checks_dir),
                "--json",
                str(json_path),
            ]
        )
        self.assertEqual(rc, 3)
        self.assertIn("INFRA-FAIL", err)
        self.assertIn("001_bad", err)
        self.assertIn("unparseable stdout", err)

    def test_nonzero_exit_check_exit_3(self):
        self._write_nonzero_exit_check("001_crash.py")
        json_path = self.tmpdir / "out.json"
        rc, out, err = self._capture(
            [
                "--checks-dir",
                str(self.checks_dir),
                "--json",
                str(json_path),
            ]
        )
        self.assertEqual(rc, 3)
        self.assertIn("INFRA-FAIL", err)
        self.assertIn("001_crash", err)
        self.assertIn("crash message", err)

    def test_stops_on_first_infra_failure(self):
        """A later sorted check file is NOT executed after an early infra fail."""
        sentinel = self.tmpdir / "sentinel.txt"
        # 001 runs first and fails (non-JSON)
        self._write_non_json_check("001_bad.py")
        # 002 should NOT run
        self._write_sentinel_check("002_should_not_run.py", sentinel)
        json_path = self.tmpdir / "out.json"
        rc, out, err = self._capture(
            [
                "--checks-dir",
                str(self.checks_dir),
                "--json",
                str(json_path),
            ]
        )
        self.assertEqual(rc, 3)
        # The sentinel file should NOT exist — 002 never ran.
        self.assertFalse(sentinel.exists())

    def test_hung_check_killed_at_timeout_exit_3(self):
        self._write_hanging_check("001_hang.py")
        json_path = self.tmpdir / "out.json"
        t0 = time.monotonic()
        rc, out, err = self._capture(
            [
                "--checks-dir",
                str(self.checks_dir),
                "--json",
                str(json_path),
                "--timeout",
                "1",
            ]
        )
        elapsed = time.monotonic() - t0
        self.assertEqual(rc, 3)
        self.assertLess(elapsed, 15.0)  # well under 999s sleep
        self.assertIn("INFRA-FAIL", err)
        self.assertIn("001_hang", err)
        self.assertIn("timed out", err)

    def test_absent_checks_dir_exit_0_no_checks_configured(self):
        json_path = self.tmpdir / "out.json"
        rc, out, err = self._capture(
            [
                "--checks-dir",
                str(self.tmpdir / "does-not-exist"),
                "--json",
                str(json_path),
            ]
        )
        self.assertEqual(rc, 0)
        self.assertIn("repo_lint: no checks configured", out)

    def test_empty_checks_dir_exit_0_no_checks_configured(self):
        json_path = self.tmpdir / "out.json"
        rc, out, err = self._capture(
            [
                "--checks-dir",
                str(self.checks_dir),
                "--json",
                str(json_path),
            ]
        )
        self.assertEqual(rc, 0)
        self.assertIn("repo_lint: no checks configured", out)
        data = json.loads(json_path.read_text())
        self.assertEqual(data, {"generated_by": "repo_lint.py", "checks": []})

    def test_sorted_execution_order(self):
        """Checks execute in sorted filename order."""
        # Create out of alphabetical order.
        self._write_passing_check("002_b.py")
        self._write_passing_check("001_a.py")
        self._write_passing_check("003_c.py")
        json_path = self.tmpdir / "out.json"
        rc, out, err = self._capture(
            [
                "--checks-dir",
                str(self.checks_dir),
                "--json",
                str(json_path),
            ]
        )
        self.assertEqual(rc, 0)
        data = json.loads(json_path.read_text())
        self.assertEqual(
            [c["name"] for c in data["checks"]],
            ["001_a", "002_b", "003_c"],
        )

    def test_json_artifact_schema_fields_present(self):
        """JSON artifact has the expected schema fields."""
        self._write_finding_check("001_test.py", n_findings=1)
        json_path = self.tmpdir / "out.json"
        rc, out, err = self._capture(
            [
                "--checks-dir",
                str(self.checks_dir),
                "--json",
                str(json_path),
            ]
        )
        self.assertEqual(rc, 2)
        data = json.loads(json_path.read_text())
        self.assertIn("generated_by", data)
        self.assertEqual(data["generated_by"], "repo_lint.py")
        self.assertIn("checks", data)
        self.assertEqual(len(data["checks"]), 1)
        entry = data["checks"][0]
        self.assertIn("name", entry)
        self.assertIn("status", entry)
        self.assertIn("findings", entry)
        self.assertIn("sample", entry)
        self.assertIsInstance(entry["sample"], list)


if __name__ == "__main__":
    unittest.main()
