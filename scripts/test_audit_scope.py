#!/usr/bin/env python3
"""Tests for audit_scope.py — stdlib unittest, no pytest.

Builds a real temporary git repo per test (setUp) and drives audit_scope's
`main()` directly. `radon` is faked with a stub executable prepended to
PATH (real `radon` is not installed on the test machine anyway); `git` is
always resolved from the restricted-but-real system PATH.
"""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import audit_scope  # noqa: E402

# A restricted-but-real PATH: enough to find git, guaranteed to lack radon
# (radon is not installed on this machine at all, but restricting to the
# system dirs keeps the test deterministic regardless of the host).
_BASE_PATH = "/usr/bin:/bin"

_RADON_STUB = """\
#!/bin/sh
# args: cc -j <path1> <path2> ... — one invocation covers MULTIPLE paths
# (Fix 2: batched radon invocations). Emits one combined JSON object keyed
# by every path given, mirroring radon's real per-invocation output shape.
shift 2  # drop "cc" "-j"
if [ -n "$RADON_INVOKE_LOG" ]; then
  echo "invoked with $# path(s)" >> "$RADON_INVOKE_LOG"
fi
printf '{'
first=1
for path in "$@"; do
  case "$path" in
    *hot*) complexity=9 ;;
    *) complexity=2 ;;
  esac
  if [ "$first" -eq 1 ]; then
    first=0
  else
    printf ','
  fi
  printf '"%s": [{"type": "function", "name": "f", "complexity": %s, "lineno": 1}]' "$path" "$complexity"
done
printf '}\\n'
"""


def _run(cmd: list[str], cwd: Path) -> str:
    result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{cmd} failed: {result.stderr}")
    return result.stdout


class AuditScopeTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.repo = self.tmpdir / "repo"
        self.repo.mkdir()

        _run(["git", "init", "-b", "main"], self.repo)
        _run(["git", "config", "user.email", "test@example.com"], self.repo)
        _run(["git", "config", "user.name", "Test User"], self.repo)

        (self.repo / "a.py").write_text("def foo():\n    return 1\n")
        _run(["git", "add", "a.py"], self.repo)
        _run(["git", "commit", "-m", "initial"], self.repo)

        self._orig_cwd = os.getcwd()
        os.chdir(self.repo)
        self._orig_path = os.environ.get("PATH", "")
        os.environ["PATH"] = _BASE_PATH

    def tearDown(self):
        os.chdir(self._orig_cwd)
        os.environ["PATH"] = self._orig_path
        os.environ.pop("RADON_INVOKE_LOG", None)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _stub_radon(self) -> Path:
        stub_bin = self.tmpdir / "stub_bin"
        stub_bin.mkdir(exist_ok=True)
        radon = stub_bin / "radon"
        radon.write_text(_RADON_STUB)
        radon.chmod(0o755)
        return stub_bin

    def _capture(self, argv: list[str]) -> tuple[int, str]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = audit_scope.main(argv)
        return rc, buf.getvalue()

    # ------------------------------------------------------------------
    # scan — no tag => full scope
    # ------------------------------------------------------------------

    def test_scan_no_tag_scope_full(self):
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(["scan", "--json", str(json_path)])
        self.assertEqual(rc, 0)
        data = json.loads(json_path.read_text())
        self.assertEqual(data["scope"], "full")
        self.assertIsNone(data["tag"])
        self.assertIsNone(data["anchor_commit"])
        self.assertIsNone(data["commits_since"])
        self.assertFalse(data["complexity_available"])
        paths = {f["path"] for f in data["files"]}
        self.assertIn("a.py", paths)
        for f in data["files"]:
            self.assertIsNone(f["complexity"])
            self.assertEqual(f["hotspot_score"], f["churn"])

    # ------------------------------------------------------------------
    # scan — after tag + further commits => delta scope, correct ordering
    # ------------------------------------------------------------------

    def test_scan_after_tag_delta_scope_and_churn_ordering(self):
        rc = audit_scope.main(["tag", "--date", "2026-06-01"])
        self.assertEqual(rc, 0)

        # Small edit to a.py (low churn).
        (self.repo / "a.py").write_text("def foo():\n    return 2\n")
        _run(["git", "add", "a.py"], self.repo)
        _run(["git", "commit", "-m", "edit a"], self.repo)

        # New file with much larger churn.
        big_content = "\n".join(f"line {i}" for i in range(50)) + "\n"
        (self.repo / "b.py").write_text(big_content)
        _run(["git", "add", "b.py"], self.repo)
        _run(["git", "commit", "-m", "add b"], self.repo)

        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(["scan", "--json", str(json_path)])
        self.assertEqual(rc, 0)
        data = json.loads(json_path.read_text())

        self.assertEqual(data["scope"], "delta")
        self.assertEqual(data["tag"], "audit/2026-06-01")
        self.assertEqual(data["commits_since"], 2)
        self.assertIsNotNone(data["anchor_commit"])

        paths = [f["path"] for f in data["files"]]
        self.assertIn("a.py", paths)
        self.assertIn("b.py", paths)

        # b.py churned far more than a.py => ranked first (descending).
        self.assertEqual(paths[0], "b.py")
        by_path = {f["path"]: f for f in data["files"]}
        self.assertGreater(by_path["b.py"]["churn"], by_path["a.py"]["churn"])
        self.assertGreater(
            by_path["b.py"]["hotspot_score"], by_path["a.py"]["hotspot_score"]
        )

    # ------------------------------------------------------------------
    # radon absent => complexity_available false, hotspot ranking produced
    # ------------------------------------------------------------------

    def test_radon_absent_hotspot_ranking_still_produced(self):
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(["scan", "--json", str(json_path)])
        self.assertEqual(rc, 0)
        data = json.loads(json_path.read_text())
        self.assertFalse(data["complexity_available"])
        self.assertTrue(len(data["files"]) >= 1)
        for f in data["files"]:
            self.assertIsNone(f["complexity"])

    # ------------------------------------------------------------------
    # radon present => complexity merged into hotspot score
    # ------------------------------------------------------------------

    def test_radon_present_complexity_merged_into_hotspot(self):
        stub_bin = self._stub_radon()
        os.environ["PATH"] = f"{stub_bin}{os.pathsep}{_BASE_PATH}"

        # Rename so the stub's *hot* branch fires for this file.
        (self.repo / "a.py").rename(self.repo / "hot_module.py")
        _run(["git", "add", "-A"], self.repo)
        _run(["git", "commit", "-m", "rename to hot"], self.repo)

        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(["scan", "--json", str(json_path)])
        self.assertEqual(rc, 0)
        data = json.loads(json_path.read_text())
        self.assertTrue(data["complexity_available"])
        by_path = {f["path"]: f for f in data["files"]}
        self.assertIn("hot_module.py", by_path)
        entry = by_path["hot_module.py"]
        self.assertEqual(entry["complexity"], 9)
        self.assertEqual(entry["hotspot_score"], entry["churn"] * (1 + 9))

    # ------------------------------------------------------------------
    # git rename syntax — churn/complexity attributed to the NEW path,
    # never the stale "old => new" arrow string (Fix 1 / Defect probe).
    # ------------------------------------------------------------------

    def test_scan_pure_rename_no_edit_attributes_to_new_path(self):
        rc = audit_scope.main(["tag", "--date", "2026-06-10"])
        self.assertEqual(rc, 0)

        # Identical content, no edit — git detects this as an exact rename
        # (numstat emits the "old => new" arrow form for the whole path
        # since the names share no meaningful prefix/suffix).
        (self.repo / "a.py").rename(self.repo / "renamed.py")
        _run(["git", "add", "-A"], self.repo)
        _run(["git", "commit", "-m", "pure rename"], self.repo)

        stub_bin = self._stub_radon()
        os.environ["PATH"] = f"{stub_bin}{os.pathsep}{_BASE_PATH}"

        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(["scan", "--json", str(json_path)])
        self.assertEqual(rc, 0)
        data = json.loads(json_path.read_text())
        by_path = {f["path"]: f for f in data["files"]}
        # The stale arrow string never appears as a path.
        self.assertFalse(any("=>" in p for p in by_path))
        self.assertIn("renamed.py", by_path)
        # radon found "renamed.py" ON DISK (stub's non-hot branch => 2), not
        # 0 — proving the old bug (looking up the literal arrow string,
        # which never exists on disk) is fixed.
        self.assertEqual(by_path["renamed.py"]["complexity"], 2)

    def test_scan_rename_plus_edit_attributes_churn_and_complexity_to_new_path(self):
        # Enough shared content that git's default similarity threshold
        # still detects the rename after a small edit (verified: a 4-line
        # file with only the last line changed = 75% line-identical).
        (self.repo / "multi.py").write_text(
            "def foo():\n    return 1\n    return 1\n    return 1\n"
        )
        _run(["git", "add", "-A"], self.repo)
        _run(["git", "commit", "-m", "add multi.py"], self.repo)

        rc = audit_scope.main(["tag", "--date", "2026-06-11"])
        self.assertEqual(rc, 0)

        (self.repo / "multi.py").rename(self.repo / "hot_multi.py")
        _run(["git", "add", "-A"], self.repo)
        _run(["git", "commit", "-m", "rename multi.py"], self.repo)

        (self.repo / "hot_multi.py").write_text(
            "def foo():\n    return 1\n    return 1\n    return 42\n"
        )
        _run(["git", "add", "-A"], self.repo)
        _run(["git", "commit", "-m", "edit after rename"], self.repo)

        # Sanity: confirm git itself still reports this as a rename (arrow
        # form), not a straight delete+add — otherwise this fixture would
        # not actually be exercising the rename-parsing code path.
        raw_numstat = _run(
            ["git", "diff", "--numstat", "audit/2026-06-11..HEAD"], self.repo
        )
        self.assertIn("=>", raw_numstat)

        stub_bin = self._stub_radon()
        os.environ["PATH"] = f"{stub_bin}{os.pathsep}{_BASE_PATH}"

        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(["scan", "--json", str(json_path)])
        self.assertEqual(rc, 0)
        data = json.loads(json_path.read_text())
        by_path = {f["path"]: f for f in data["files"]}
        self.assertFalse(any("=>" in p for p in by_path))
        self.assertIn("hot_multi.py", by_path)
        entry = by_path["hot_multi.py"]
        # The edit's churn is attributed to the new path, not stranded.
        self.assertGreater(entry["churn"], 0)
        # radon found "hot_multi.py" on disk => stub's *hot* branch (9), not 0.
        self.assertEqual(entry["complexity"], 9)

    # ------------------------------------------------------------------
    # radon batching (Fix 2) — one invocation covers several files.
    # ------------------------------------------------------------------

    def test_radon_batched_one_invocation_covers_multiple_files(self):
        for name in ("b.py", "c.py", "d.py"):
            (self.repo / name).write_text(f"def {name[0]}():\n    return 1\n")
        _run(["git", "add", "-A"], self.repo)
        _run(["git", "commit", "-m", "add three more files"], self.repo)

        stub_bin = self._stub_radon()
        os.environ["PATH"] = f"{stub_bin}{os.pathsep}{_BASE_PATH}"
        invoke_log = self.tmpdir / "radon_invoke.log"
        invoke_log.write_text("")
        os.environ["RADON_INVOKE_LOG"] = str(invoke_log)

        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(["scan", "--json", str(json_path)])
        self.assertEqual(rc, 0)
        data = json.loads(json_path.read_text())
        self.assertGreaterEqual(len(data["files"]), 4)  # a.py, b.py, c.py, d.py

        invoke_lines = [ln for ln in invoke_log.read_text().splitlines() if ln.strip()]
        # Fewer radon invocations than files — proof of batching (one
        # invocation, covering all >=4 files, rather than one per file).
        self.assertLess(len(invoke_lines), len(data["files"]))
        self.assertEqual(len(invoke_lines), 1)

    # ------------------------------------------------------------------
    # tag — annotated + duplicate refusal
    # ------------------------------------------------------------------

    def test_tag_creates_annotated_tag_and_duplicate_exits_3(self):
        rc = audit_scope.main(["tag", "--date", "2026-06-02"])
        self.assertEqual(rc, 0)

        tag_type = _run(
            ["git", "cat-file", "-t", "audit/2026-06-02"], self.repo
        ).strip()
        self.assertEqual(tag_type, "tag")

        rc2 = audit_scope.main(["tag", "--date", "2026-06-02"])
        self.assertEqual(rc2, 3)

    # ------------------------------------------------------------------
    # log-line — exact registry format
    # ------------------------------------------------------------------

    def test_log_line_exact_format(self):
        short_sha = _run(["git", "rev-parse", "--short", "HEAD"], self.repo).strip()
        rc, out = self._capture(
            ["log-line", "--date", "2026-06-03", "--essence", "found 3 bugs"]
        )
        self.assertEqual(rc, 0)
        expected = f"- **2026-06-03** · audit/2026-06-03 · {short_sha} · found 3 bugs\n"
        self.assertEqual(out, expected)

    # ------------------------------------------------------------------
    # summary line — single line, contains the JSON path
    # ------------------------------------------------------------------

    def test_summary_line_single_line_contains_json_path(self):
        json_path = self.tmpdir / "out.json"
        rc, out = self._capture(["scan", "--json", str(json_path)])
        self.assertEqual(rc, 0)
        lines = out.splitlines()
        self.assertEqual(len(lines), 1)
        self.assertIn(str(json_path), lines[0])
        self.assertTrue(lines[0].startswith("audit_scope: "))


class NumstatRenamePathParsingTest(unittest.TestCase):
    """Unit-level checks of the git-numstat rename-arrow parsing (Fix 1) —
    no git repo needed, just the pure path-resolution helper."""

    def test_whole_path_arrow_form_resolves_to_new_path(self):
        self.assertEqual(
            audit_scope._resolve_renamed_path("dir1/old.py => dir2/new.py"),
            "dir2/new.py",
        )

    def test_braced_form_resolves_to_new_path(self):
        self.assertEqual(
            audit_scope._resolve_renamed_path("dir/{old => new}/file.py"),
            "dir/new/file.py",
        )

    def test_braced_form_with_no_prefix_or_suffix(self):
        self.assertEqual(
            audit_scope._resolve_renamed_path("{old => new}"), "new"
        )

    def test_non_rename_path_passes_through_unchanged(self):
        self.assertEqual(audit_scope._resolve_renamed_path("a.py"), "a.py")


if __name__ == "__main__":
    unittest.main()
