#!/usr/bin/env python3
"""checks.py — checks-and-facts engine (D1, D2, D3, D6, D8).

The checks/facts/audit trichotomy:
  **checks** = findings-capable detectors (gate/record semantics, dated
  output). ``ruff``, ``gitleaks``, ``osv-scanner``, ``deptry``,
  ``data-lint``, ``repo-lint``, ``jscpd``, ``vulture``.
  **facts**  = can't-fail repo snapshots (cache semantics, undated output,
  regenerate-on-use). ``scope``, ``radon``, ``index-coverage``,
  ``inventory``.
  **audit**  = the operator ceremony: ``audit_scope.py`` tag/log + the
  ``run-audit`` skill + ``knowledge/audit-log.md``.

Entry points: ``checks.py`` (checks + inventory fact; all modes) and
``facts.py`` (thin facts-only CLI, imports engine from here).

`repo_root` is resolved via `git rev-parse --show-toplevel` (falling back to
`Path.cwd()` if that fails, e.g. no git binary or not a repo) — NOT bare
`Path.cwd()` — so path normalization and the inventory tree stay consistent
with `audit_scope`'s git-root-relative paths even when invoked from a repo
subdirectory.

Config schema (``checks.toml``, repo root, stdlib ``tomllib``;
self-documenting — this docstring + ``--help`` are the ONLY documentation,
per D1/knowledge-recoverability: no standing doc file for a code-derivable
schema)
--------------------------------------------------------------------------
Absent config → built-in defaults with trigger-based auto-detection (only
for floor-tier checks with an external-tool dependency; checks with no
external dependency — ``scope``, ``inventory`` — are unconditionally
enabled; heavy-tier checks — ``radon``, ``jscpd``, ``vulture``,
``index-coverage`` — default DISABLED absent explicit config, since they are
on-demand/audit-time per the brief's D8e, and ``index-coverage``
additionally has no sane default ``--schema`` path to auto-detect):

    pyproject.toml                                        -> ruff, deptry
    .git/                                                  -> gitleaks, scope
    requirements*.txt | poetry.lock | uv.lock | package-lock.json
                                                             -> osv-scanner
    checks/ (any *.sql)                                    -> data-lint
    checks/ (any *.py)                                     -> repo-lint
    (always)                                               -> inventory

``[tools]`` — version-pin overrides for `EXPECTED_TOOL_VERSIONS` (binary
tools only: gitleaks/osv-scanner/jscpd by default). Table of
``tool = "x.y.z"`` (bare, no leading ``v``).

``[checks.<name>]`` — per built-in/delegating check: ``enabled`` (bool,
overrides auto-detection), ``args`` (list[str], extra CLI flags), ``paths``
(list[str], scan targets for ruff/radon/vulture/jscpd; default ``["."]``).
For ``data-lint`` specifically, ``paths`` means the checks DIRECTORY (the
FIRST entry is used as ``--checks-dir``; a SECOND or later entry is an
explicit INFRA-FAIL config error, never silently dropped). A scalar string
is accepted anywhere a ``list[str]`` is documented (``paths``,
``[checks.index-coverage].schema``, ``.queries``) — coerced to a
single-element list — since a bare TOML string value indexed/iterated as a
list is a classic silent no-op footgun; any other scalar type (int, bool,
...) is an explicit INFRA-FAIL config-type error.

``[checks.custom.<name>]`` — generic non-parsed check: ``command``
(list[str], the argv to run), ``tier`` (``floor|heavy|snapshot``, default
``heavy`` if omitted), ``gate`` (bool, default ``true``: nonzero exit =
findings/exit-2 class; ``gate = false`` = report-only — output is still
captured and the run continues regardless of exit code). Output is always
captured verbatim to ``<check>.txt`` with a null findings-count (`?` in the
stdout summary) — there is no parser for custom commands.

**D3 caveat (custom checks):** the engine cannot prevent a custom
``command`` from writing to the repo — keeping a custom check check-only is
the CONFIGURING repo's responsibility, not something this orchestrator can
enforce for arbitrary argv.

``[facts.outstanding]`` — config for the ``outstanding`` fact (``outstanding.py``,
consumed by ``facts.py --check outstanding`` and ``knowledge_lint.py``'s
``_check_untriaged_age``). All keys optional with documented defaults:
``findings_globs`` (list[str], default ``["knowledge/research/**/FINDINGS*.md"]``,
from ``outstanding.py:29``),
``finding_id_pattern`` (str, default ``\\b[A-Z]{2,}(?:-[A-Z0-9]+)?-\\d+\\b``,
from ``outstanding.py:32``),
``composition_change_threshold`` (int, default ``10``, from the composition-audit
spec — the count of archived-change directories since the last composition anchor
that triggers ``due``),
``composition_commit_threshold`` (int, default ``100``, from the composition-audit
spec — the commit count since the last composition anchor that triggers ``due``).
The composition-audit spec is normative for the threshold defaults; per-repo
overrides go here.

Check registry
--------------
Built-in PARSED checks (native output -> normalized finding
``{check, rule, path, line, message}`` — ``path`` is normalized to
repo-relative whenever the tool emitted an absolute path under the repo
root, e.g. ruff; an absolute path OUTSIDE the repo root is left unchanged;
this keeps baseline fingerprints (4.6) portable across checkouts/machines):
``ruff``, ``gitleaks``,
``osv-scanner``, ``deptry``, ``radon`` (findings = blocks ranked D/E/F on
radon's A-F cyclomatic-complexity scale), ``jscpd``, ``vulture`` (its
line-text output, e.g. ``path.py:12: unused variable 'x' (60% confidence)``,
parsed by regex). Delegating checks (own JSON shape, NOT merged into the
aggregate `findings.json`): ``scope`` (`audit_scope.py scan`, floor, never
gates — informational hotspot ranking), ``data-lint`` (`data_lint.py`,
floor, gates on violating rows), ``repo-lint`` (`repo_lint.py`, floor,
gates on check findings), ``index-coverage`` (`index_coverage.py`,
heavy, NEVER gates — leads are for LLM triage only). Built-in snapshot
``inventory`` (zero-findings semantics — always "ok"): tracked source-file
tree, detected entrypoints (pyproject `[project.scripts]`, `justfile`/
`Makefile` target names, `package.json` "scripts"), and env-var names
referenced in source via ``os.environ``/``os.getenv(...)``/``process.env``
(anchored forms only — a `my_getenv_wrapper` identifier does not match).

Everything else named in the brief (eslint, tsc, sqlfluff, alembic-check,
pyan3, paracelsus, pg_dump, openapi fetch, schemathesis, testmon) is
deliberately NOT parsed here — downstream repos wire them as
``[checks.custom.*]``.

Availability + version pinning
-------------------------------
Binary tools in ``EXPECTED_TOOL_VERSIONS`` are probed before running: try
``<tool> --version``, then ``<tool> version`` on nonzero exit; both
nonzero (or the binary absent) = ``unavailable``. From the successful
probe's combined stdout+stderr, the FIRST ``\\d+\\.\\d+(\\.\\d+)?`` substring
is compared EXACT-STRING to the pin; a mismatch or unparseable version is
``version-mismatch`` — an infra failure whenever the check actually runs
(``--check``/``--floor``/``--report``), though `--list` only reports the
status without failing. Python-ecosystem tools (ruff, deptry, radon,
vulture) are probed the same way but NEVER fail on a version mismatch —
pinned in each repo's dev extras, not here; their probed version is only
*recorded*, and an unprobeable one is ``null``. A tool missing from PATH is
an infra failure in `--report`/`--floor` (stop-on-first-failure for
check-family; fact-family entries degrade gracefully) but merely
``unavailable``/``skipped`` (no failure) in `--list`/single `--check`.

Modes
-----
``--list``                one line per registered check, always exit 0.
``--check <name>``        run exactly one check (query shape).
``--floor``                all enabled floor-tier check-family entries.
``--report [--out DIR] [--date YYYY-MM-DD] [--resume] [--baseline PATH] [--include NAME ...]``
                            floor + heavy + snapshot checks, in registry
                            order, checkpointed incrementally. ``--include``
                            force-enables a registered-but-disabled check for
                            this run only (repeatable; composition-audit uses
                            it for jscpd/vulture/radon).

Output contract (D8b)
----------------------
Per check: ``<out>/<check>.json`` (built-in parsed + delegating + snapshot)
or ``<out>/<check>.txt`` (custom), plus one stdout summary line:
``<check>: <ok|FINDINGS|INFRA-FAIL|skipped> — <n or ?> findings ->
<artifact-path>``. After a full/floor run: aggregate ``<out>/findings.json``
(all normalized findings from built-in PARSED checks only) and a final
line ``checks: <n> findings across <m> checks -> <out>``.

Exit codes
----------
0 — ran clean / no findings. 2 — findings present. 3 — infra failure or
abort (preflight failure or stop-on-first-failure; findings never abort).
"""

from __future__ import annotations

import argparse
import ast
import glob as glob_module
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from io import StringIO
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import audit_scope  # noqa: E402
import data_lint  # noqa: E402
import index_coverage  # noqa: E402
import outstanding  # noqa: E402
import repo_lint  # noqa: E402

GENERATED_BY = "checks.py"

# Live-verified 2026-07-02 (GitHub Releases API): gitleaks v8.30.1,
# osv-scanner v2.4.0, jscpd v5.0.11. Overridable via `[tools]`.
EXPECTED_TOOL_VERSIONS: dict[str, str] = {
    "gitleaks": "8.30.1",
    "osv-scanner": "2.4.0",
    "jscpd": "5.0.11",
}

# Registry order is load-bearing: --list, --report, and run-manifest
# ordering all follow this sequence.
_REGISTRY: list[dict] = [
    {"name": "scope", "tier": "floor", "kind": "delegate", "family": "fact"},
    {
        "name": "ruff",
        "tier": "floor",
        "kind": "builtin",
        "family": "check",
        "trigger": "pyproject.toml present",
        "coverage_note": "disabling drops lint checking",
    },
    {
        "name": "gitleaks",
        "tier": "floor",
        "kind": "builtin",
        "family": "check",
        "trigger": ".git present",
        "coverage_note": "disabling drops secret scanning",
    },
    {
        "name": "osv-scanner",
        "tier": "floor",
        "kind": "builtin",
        "family": "check",
        "trigger": "lockfile present",
        "coverage_note": "drops known-vulnerability scanning",
    },
    {
        "name": "deptry",
        "tier": "floor",
        "kind": "builtin",
        "family": "check",
        "trigger": "pyproject.toml present",
        "coverage_note": "drops dependency-hygiene checking",
    },
    {
        "name": "test-quality",
        "tier": "floor",
        "kind": "builtin",
        "family": "check",
        "trigger": "python test files present",
        "coverage_note": "disabling drops test-quality detection",
    },
    {
        "name": "data-scale",
        "tier": "floor",
        "kind": "builtin",
        "family": "check",
        "trigger": "python source present",
        "coverage_note": "disabling drops unbounded-query detection",
    },
    {"name": "data-lint", "tier": "floor", "kind": "delegate", "family": "check"},
    {"name": "repo-lint", "tier": "floor", "kind": "delegate", "family": "check"},
    {"name": "radon", "tier": "heavy", "kind": "builtin", "family": "fact"},
    {
        "name": "jscpd",
        "tier": "heavy",
        "kind": "builtin",
        "family": "check",
        "trigger": "always (enabled explicitly)",
        "coverage_note": "disabling drops duplication detection",
    },
    {
        "name": "vulture",
        "tier": "heavy",
        "kind": "builtin",
        "family": "check",
        "trigger": "always (enabled explicitly)",
        "coverage_note": "disabling drops dead-code detection",
    },
    {"name": "index-coverage", "tier": "heavy", "kind": "delegate", "family": "fact"},
    {"name": "outstanding", "tier": "snapshot", "kind": "delegate", "family": "fact"},
    {"name": "inventory", "tier": "snapshot", "kind": "builtin", "family": "fact"},
]

_LOCKFILE_PATTERNS = (
    "requirements*.txt",
    "poetry.lock",
    "uv.lock",
    "package-lock.json",
)


# ---------------------------------------------------------------------------
# Repo root resolution (Fix 8)
# ---------------------------------------------------------------------------


def _resolve_repo_root() -> Path:
    """Resolve the repo root as ``git rev-parse --show-toplevel`` (run from
    CWD) when it succeeds, else fall back to ``Path.cwd()``. Bare
    ``Path.cwd()`` diverges from ``audit_scope``'s git-toplevel-relative
    paths whenever the bundle is invoked from a repo subdirectory — this
    keeps the inventory tree and finding-path normalization consistent with
    ``scope.json`` in the same run's output."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True
        )
    except OSError:
        return Path.cwd()
    if result.returncode != 0:
        return Path.cwd()
    return Path(result.stdout.strip())


# ---------------------------------------------------------------------------
# Config loading (4.1)
# ---------------------------------------------------------------------------


def _load_config(repo_root: Path) -> tuple[dict, str]:
    """Return (config_dict, source) — source is "checks.toml" or "defaults"."""
    config_path = repo_root / "checks.toml"
    if not config_path.is_file():
        return {}, "defaults"
    with open(config_path, "rb") as f:
        return tomllib.load(f), "checks.toml"


def _autodetect_defaults(repo_root: Path) -> dict[str, bool]:
    has_pyproject = (repo_root / "pyproject.toml").is_file()
    has_git = (repo_root / ".git").exists()
    has_lockfile = any(glob_module.glob(str(repo_root / pattern)) for pattern in _LOCKFILE_PATTERNS)
    checks_dir = repo_root / "checks"
    has_sql_checks = checks_dir.is_dir() and any(checks_dir.glob("*.sql"))
    has_py_checks = checks_dir.is_dir() and any(checks_dir.glob("*.py"))

    return {
        "scope": has_git,
        "ruff": has_pyproject,
        "gitleaks": has_git,
        "osv-scanner": has_lockfile,
        "deptry": has_pyproject,
        "data-lint": has_sql_checks,
        "repo-lint": has_py_checks,
        "test-quality": True,
        "data-scale": True,
        "radon": False,
        "jscpd": False,
        "vulture": False,
        "index-coverage": False,
        "outstanding": True,
        "inventory": True,
    }


def _custom_checks(config: dict) -> list[dict]:
    custom_cfg = config.get("checks", {}).get("custom", {})
    result = []
    for name, spec in custom_cfg.items():
        result.append(
            {
                "name": name,
                "tier": spec.get("tier", "heavy"),
                "kind": "custom",
                "family": "check",
                "command": spec.get("command", []),
                "gate": spec.get("gate", True),
            }
        )
    return result


def _is_enabled(check_name: str, config: dict, defaults: dict[str, bool]) -> bool:
    check_cfg = config.get("checks", {}).get(check_name, {})
    if isinstance(check_cfg, dict) and "enabled" in check_cfg:
        return bool(check_cfg["enabled"])
    return defaults.get(check_name, False)


def _check_paths(check_name: str, config: dict) -> list[str]:
    check_cfg = config.get("checks", {}).get(check_name, {})
    if isinstance(check_cfg, dict) and check_cfg.get("paths"):
        return list(check_cfg["paths"])
    return ["."]


def _check_args(check_name: str, config: dict) -> list[str]:
    check_cfg = config.get("checks", {}).get(check_name, {})
    if isinstance(check_cfg, dict) and check_cfg.get("args"):
        return list(check_cfg["args"])
    return []


# ---------------------------------------------------------------------------
# Availability + version probing (4.3)
# ---------------------------------------------------------------------------

_VERSION_RE = re.compile(r"\d+\.\d+(?:\.\d+)?")


def _probe_raw_version(tool: str) -> str | None:
    """Two-step probe protocol. Returns the first extracted version
    substring, or None if the tool is unavailable (both subcommands failed
    or the binary is absent)."""
    for probe_args in (["--version"], ["version"]):
        try:
            result = subprocess.run([tool, *probe_args], capture_output=True, text=True, timeout=15)
        except (OSError, subprocess.TimeoutExpired):
            continue
        if result.returncode == 0:
            combined = (result.stdout or "") + (result.stderr or "")
            m = _VERSION_RE.search(combined)
            return m.group(0) if m else ""
    return None


def _tool_status(tool: str, pins: dict[str, str]) -> dict:
    """Returns {"status": ..., "version": str|None, "expected": str|None}."""
    version = _probe_raw_version(tool)
    if version is None:
        return {"status": "unavailable", "version": None, "expected": pins.get(tool)}
    pin = pins.get(tool)
    if pin is not None and version != pin:
        return {"status": "version-mismatch", "version": version, "expected": pin}
    return {"status": "available", "version": version, "expected": pin}


def _custom_availability(command: list[str]) -> dict:
    if not command:
        return {"status": "unavailable", "version": None, "expected": None}
    if shutil.which(command[0]) is None:
        return {"status": "unavailable", "version": None, "expected": None}
    return {"status": "available", "version": None, "expected": None}


_BUILTIN_TOOL_BIN = {
    "ruff": "ruff",
    "gitleaks": "gitleaks",
    "osv-scanner": "osv-scanner",
    "deptry": "deptry",
    "radon": "radon",
    "jscpd": "jscpd",
    "vulture": "vulture",
}


def _availability_for_check(check: dict, pins: dict[str, str]) -> dict:
    kind = check["kind"]
    if kind == "delegate":
        # Delegating scripts are always-present scaffold siblings; their own
        # internal tool dependencies (psql, radon) report as infra failures
        # from inside that script, not at this orchestration layer.
        return {"status": "available", "version": None, "expected": None}
    if kind == "custom":
        return _custom_availability(check.get("command", []))
    if check["name"] in ("inventory", "test-quality", "data-scale"):
        return {"status": "available", "version": None, "expected": None}
    tool_bin = _BUILTIN_TOOL_BIN[check["name"]]
    return _tool_status(tool_bin, pins)


# ---------------------------------------------------------------------------
# Built-in parsers — native tool JSON/text -> normalized findings
# ---------------------------------------------------------------------------


def _parse_ruff(raw: str) -> list[dict]:
    data = json.loads(raw) if raw.strip() else []
    findings = []
    for item in data:
        location = item.get("location") or {}
        findings.append(
            {
                "check": "ruff",
                "rule": item.get("code") or "",
                "path": item.get("filename") or "",
                "line": location.get("row"),
                "message": item.get("message") or "",
            }
        )
    return findings


def _parse_gitleaks(raw: str) -> list[dict]:
    data = json.loads(raw) if raw.strip() else []
    if data is None:
        data = []
    findings = []
    for item in data:
        findings.append(
            {
                "check": "gitleaks",
                "rule": item.get("RuleID") or "",
                "path": item.get("File") or "",
                "line": item.get("StartLine"),
                "message": item.get("Description") or item.get("Match") or "",
            }
        )
    return findings


def _parse_osv_scanner(raw: str) -> list[dict]:
    data = json.loads(raw) if raw.strip() else {}
    findings = []
    for result in data.get("results", []) or []:
        path = (result.get("source") or {}).get("path", "")
        for pkg in result.get("packages", []) or []:
            for vuln in pkg.get("vulnerabilities", []) or []:
                findings.append(
                    {
                        "check": "osv-scanner",
                        "rule": vuln.get("id") or "",
                        "path": path,
                        "line": None,
                        "message": vuln.get("summary") or vuln.get("details") or "",
                    }
                )
    return findings


def _parse_deptry(raw: str) -> list[dict]:
    data = json.loads(raw) if raw.strip() else []
    findings = []
    for item in data:
        error = item.get("error") or {}
        location = item.get("location") or {}
        findings.append(
            {
                "check": "deptry",
                "rule": error.get("code") or "",
                "path": location.get("file") or "",
                "line": location.get("line"),
                "message": error.get("message") or "",
            }
        )
    return findings


# radon's A-F cyclomatic-complexity rank scale; D and worse are flagged as
# findings (a design choice — the tasks left the exact threshold to the
# executor's discretion).
_RADON_FINDING_RANKS = {"D", "E", "F"}


def _parse_radon(raw: str) -> list[dict]:
    data = json.loads(raw) if raw.strip() else {}
    findings = []
    for path, blocks in data.items():
        if isinstance(blocks, dict):
            continue  # a per-file {"error": ...} entry, not a block list
        for block in blocks:
            rank = block.get("rank")
            if rank in _RADON_FINDING_RANKS:
                findings.append(
                    {
                        "check": "radon",
                        "rule": f"complexity-{rank}",
                        "path": path,
                        "line": block.get("lineno"),
                        "message": (
                            f"{block.get('type')} '{block.get('name')}' has "
                            f"cyclomatic complexity {block.get('complexity')} (rank {rank})"
                        ),
                    }
                )
    return findings


def _parse_jscpd(raw: str) -> list[dict]:
    data = json.loads(raw) if raw.strip() else {}
    findings = []
    for dup in data.get("duplicates", []) or []:
        first = dup.get("firstFile", {}) or {}
        second = dup.get("secondFile", {}) or {}
        findings.append(
            {
                "check": "jscpd",
                "rule": "",
                "path": first.get("name") or "",
                "line": first.get("start"),
                "message": (
                    f"duplicate of {second.get('name')}:{second.get('start')} "
                    f"({dup.get('lines')} lines)"
                ),
            }
        )
    return findings


_VULTURE_LINE_RE = re.compile(
    r"^(?P<path>.+):(?P<line>\d+):\s*(?P<message>.+?)\s*"
    r"\((?P<confidence>\d+)% confidence(?:, \d+ lines?)?\)\s*$"
)


def _parse_vulture(raw: str) -> list[dict]:
    findings = []
    for line in raw.splitlines():
        m = _VULTURE_LINE_RE.match(line.strip())
        if not m:
            continue
        findings.append(
            {
                "check": "vulture",
                "rule": "",
                "path": m.group("path"),
                "line": int(m.group("line")),
                "message": m.group("message"),
            }
        )
    return findings


_PARSERS = {
    "ruff": _parse_ruff,
    "gitleaks": _parse_gitleaks,
    "osv-scanner": _parse_osv_scanner,
    "deptry": _parse_deptry,
    "radon": _parse_radon,
    "jscpd": _parse_jscpd,
    "vulture": _parse_vulture,
    "test-quality": lambda _stdout: [],
    "data-scale": lambda _stdout: [],
}


# ---------------------------------------------------------------------------
# Inventory (built-in snapshot, zero-findings)
# ---------------------------------------------------------------------------

_ENV_GETENV_RE = re.compile(r"\bos\.getenv\(\s*[\"']([A-Za-z_][A-Za-z0-9_]*)[\"']")
_ENV_ENVIRON_RE = re.compile(
    r"\bos\.environ(?:\.get)?\s*[\[\(]\s*[\"']([A-Za-z_][A-Za-z0-9_]*)[\"']"
)
_ENV_PROCESS_ATTR_RE = re.compile(r"\bprocess\.env\.([A-Za-z_][A-Za-z0-9_]*)")
_ENV_PROCESS_BRACKET_RE = re.compile(r"\bprocess\.env\[\s*[\"']([A-Za-z_][A-Za-z0-9_]*)[\"']")


def _detect_env_vars(repo_root: Path, tracked: list[str]) -> set[str]:
    names: set[str] = set()
    for rel in tracked:
        if not rel.endswith((".py", ".js", ".ts", ".jsx", ".tsx")):
            continue
        path = repo_root / rel
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for rx in (_ENV_GETENV_RE, _ENV_ENVIRON_RE, _ENV_PROCESS_ATTR_RE, _ENV_PROCESS_BRACKET_RE):
            for m in rx.finditer(text):
                names.add(m.group(1))
    return names


def _detect_entrypoints(repo_root: Path) -> list[str]:
    entrypoints: list[str] = []

    pyproject = repo_root / "pyproject.toml"
    if pyproject.is_file():
        try:
            with open(pyproject, "rb") as f:
                data = tomllib.load(f)
            scripts = (data.get("project") or {}).get("scripts") or {}
            entrypoints.extend(sorted(scripts))
        except (tomllib.TOMLDecodeError, OSError):
            pass

    for makefile_name in ("Makefile", "makefile"):
        makefile = repo_root / makefile_name
        if makefile.is_file():
            text = makefile.read_text(encoding="utf-8", errors="ignore")
            for m in re.finditer(r"^([A-Za-z0-9_.-]+):(?!=)", text, re.MULTILINE):
                if not m.group(1).startswith("."):
                    entrypoints.append(m.group(1))
            break

    justfile = repo_root / "justfile"
    if justfile.is_file():
        text = justfile.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"^([A-Za-z0-9_-]+)\s*:", text, re.MULTILINE):
            entrypoints.append(m.group(1))

    package_json = repo_root / "package.json"
    if package_json.is_file():
        try:
            data = json.loads(package_json.read_text(encoding="utf-8"))
            entrypoints.extend(sorted((data.get("scripts") or {}).keys()))
        except (json.JSONDecodeError, OSError):
            pass

    return entrypoints


def _run_inventory(repo_root: Path) -> dict:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files"], capture_output=True, text=True
    )
    tracked = (
        sorted(line for line in result.stdout.splitlines() if line.strip())
        if result.returncode == 0
        else []
    )
    # Compute audit_anchor from the latest audit/* tag.
    tag = None
    commits_since = None
    try:
        tag_result = subprocess.run(
            ["git", "-C", str(repo_root), "tag", "--list", "audit/*", "--sort=-creatordate"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        lines = [ln for ln in tag_result.stdout.splitlines() if ln.strip()]
        if lines:
            tag = lines[0]
            count_result = subprocess.run(
                ["git", "-C", str(repo_root), "rev-list", "--count", f"{tag}..HEAD"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if count_result.returncode == 0:
                commits_since = int(count_result.stdout.strip())
    except (OSError, subprocess.TimeoutExpired, ValueError):
        pass

    # Compute composition_anchor from the latest audit/*-composition tag (sibling).
    comp_tag = None
    comp_commits_since = None
    try:
        comp_tag_result = subprocess.run(
            [
                "git",
                "-C",
                str(repo_root),
                "tag",
                "--list",
                "audit/*-composition",
                "--sort=-creatordate",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        comp_lines = [ln for ln in comp_tag_result.stdout.splitlines() if ln.strip()]
        if comp_lines:
            comp_tag = comp_lines[0]
            comp_count_result = subprocess.run(
                ["git", "-C", str(repo_root), "rev-list", "--count", f"{comp_tag}..HEAD"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if comp_count_result.returncode == 0:
                comp_commits_since = int(comp_count_result.stdout.strip())
        else:
            # No composition tag exists — use full-history commit count.
            comp_count_result = subprocess.run(
                ["git", "-C", str(repo_root), "rev-list", "--count", "HEAD"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if comp_count_result.returncode == 0:
                comp_commits_since = int(comp_count_result.stdout.strip())
    except (OSError, subprocess.TimeoutExpired, ValueError):
        pass

    return {
        "generated_by": GENERATED_BY,
        "tree": tracked,
        "entrypoints": _detect_entrypoints(repo_root),
        "env_vars": sorted(_detect_env_vars(repo_root, tracked)),
        "audit_anchor": {"tag": tag, "commits_since": commits_since},
        "composition_anchor": {"tag": comp_tag, "commits_since": comp_commits_since},
    }


# ---------------------------------------------------------------------------
# Per-check execution
# ---------------------------------------------------------------------------


def _write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _normalize_finding_paths(findings: list[dict], repo_root: Path) -> None:
    """Rewrite each finding's ``path`` to repo-relative, in place, when it is
    absolute AND resolves to a location under ``repo_root``. An absolute path
    outside the repo root is left unchanged (already-relative paths pass
    through untouched too). Centralizing this here — the one place every
    builtin-parsed check's outcome flows through — means all seven parsers
    (ruff, gitleaks, osv-scanner, deptry, radon, jscpd, vulture) are covered
    without duplicating the logic per-runner. Portable baselines depend on
    this: task 4.6's fingerprint is keyed on repo-relative ``path``, so an
    absolute path would silently break cross-checkout/cross-machine delta
    diffing (D6)."""
    root = repo_root.resolve()
    for finding in findings:
        path_str = finding.get("path") or ""
        if not path_str:
            continue
        p = Path(path_str)
        if not p.is_absolute():
            continue
        try:
            rel = p.resolve().relative_to(root)
        except ValueError:
            continue  # absolute but outside repo root — unchanged
        finding["path"] = str(rel)


def _run_builtin_tool_json(name: str, cmd: list[str], out_path: Path, timeout: int = 300) -> dict:
    """Run a tool that prints JSON to stdout; parse -> normalized findings."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return {"status": "INFRA-FAIL", "error": f"{cmd[0]} not found"}
    except subprocess.TimeoutExpired:
        return {"status": "INFRA-FAIL", "error": f"{cmd[0]} timed out"}
    try:
        findings = _PARSERS[name](result.stdout)
    except (json.JSONDecodeError, AttributeError, TypeError) as exc:
        return {"status": "INFRA-FAIL", "error": f"{cmd[0]} produced unparsable output: {exc}"}
    _write_json(out_path, findings)
    return {"status": "FINDINGS" if findings else "ok", "findings": findings}


def _run_gitleaks(check: dict, config: dict, out_path: Path) -> dict:
    cmd = [
        "gitleaks",
        "detect",
        "--report-format",
        "json",
        "--no-banner",
        "--exit-code",
        "2",
        "--report-path",
        str(out_path),
        *_check_args("gitleaks", config),
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except FileNotFoundError:
        return {"status": "INFRA-FAIL", "error": "gitleaks not found"}
    except subprocess.TimeoutExpired:
        return {"status": "INFRA-FAIL", "error": "gitleaks timed out"}
    if not out_path.exists():
        return {"status": "INFRA-FAIL", "error": "gitleaks produced no report"}
    try:
        raw = out_path.read_text(encoding="utf-8")
        findings = _parse_gitleaks(raw)
    except (json.JSONDecodeError, OSError) as exc:
        return {"status": "INFRA-FAIL", "error": f"gitleaks report unparsable: {exc}"}
    _write_json(out_path, findings)  # re-write normalized shape over raw report
    return {"status": "FINDINGS" if findings else "ok", "findings": findings}


def _run_deptry(check: dict, config: dict, out_path: Path) -> dict:
    cmd = [
        "deptry",
        *_check_paths("deptry", config),
        "-o",
        str(out_path),
        *_check_args("deptry", config),
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except FileNotFoundError:
        return {"status": "INFRA-FAIL", "error": "deptry not found"}
    except subprocess.TimeoutExpired:
        return {"status": "INFRA-FAIL", "error": "deptry timed out"}
    if not out_path.exists():
        return {"status": "INFRA-FAIL", "error": "deptry produced no report"}
    try:
        raw = out_path.read_text(encoding="utf-8")
        findings = _parse_deptry(raw)
    except (json.JSONDecodeError, OSError) as exc:
        return {"status": "INFRA-FAIL", "error": f"deptry report unparsable: {exc}"}
    _write_json(out_path, findings)
    return {"status": "FINDINGS" if findings else "ok", "findings": findings}


def _run_jscpd(check: dict, config: dict, out_path: Path) -> dict:
    tmp_out = Path(tempfile.mkdtemp(prefix="jscpd-"))
    cmd = [
        "jscpd",
        "--reporters",
        "json",
        "--output",
        str(tmp_out),
        *_check_args("jscpd", config),
        *_check_paths("jscpd", config),
    ]
    try:
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        except FileNotFoundError:
            return {"status": "INFRA-FAIL", "error": "jscpd not found"}
        except subprocess.TimeoutExpired:
            return {"status": "INFRA-FAIL", "error": "jscpd timed out"}
        report = tmp_out / "jscpd-report.json"
        if not report.exists():
            return {"status": "INFRA-FAIL", "error": "jscpd produced no report"}
        try:
            raw = report.read_text(encoding="utf-8")
            findings = _parse_jscpd(raw)
        except (json.JSONDecodeError, OSError) as exc:
            return {"status": "INFRA-FAIL", "error": f"jscpd report unparsable: {exc}"}
    finally:
        shutil.rmtree(tmp_out, ignore_errors=True)
    _write_json(out_path, findings)
    return {"status": "FINDINGS" if findings else "ok", "findings": findings}


def _run_vulture(check: dict, config: dict, out_path: Path) -> dict:
    cmd = ["vulture", *_check_args("vulture", config), *_check_paths("vulture", config)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except FileNotFoundError:
        return {"status": "INFRA-FAIL", "error": "vulture not found"}
    except subprocess.TimeoutExpired:
        return {"status": "INFRA-FAIL", "error": "vulture timed out"}
    findings = _parse_vulture(result.stdout)
    _write_json(out_path, findings)
    return {"status": "FINDINGS" if findings else "ok", "findings": findings}


def _run_ruff(check: dict, config: dict, out_path: Path) -> dict:
    cmd = [
        "ruff",
        "check",
        "--output-format",
        "json",
        *_check_args("ruff", config),
        *_check_paths("ruff", config),
    ]
    return _run_builtin_tool_json("ruff", cmd, out_path)


def _run_osv_scanner(check: dict, config: dict, out_path: Path) -> dict:
    cmd = ["osv-scanner", "--format", "json", "-r", ".", *_check_args("osv-scanner", config)]
    return _run_builtin_tool_json("osv-scanner", cmd, out_path)


def _run_radon(check: dict, config: dict, out_path: Path) -> dict:
    cmd = ["radon", "cc", "-j", *_check_args("radon", config), *_check_paths("radon", config)]
    return _run_builtin_tool_json("radon", cmd, out_path)


def _module_under_test(filename: str) -> str | None:
    """Derive the module-under-test from a test filename.

    ``test_<m>.py`` -> ``<m>``, ``<m>_test.py`` -> ``<m>``.
    Returns ``None`` when no module name is derivable.
    """
    base = Path(filename).stem
    if base.startswith("test_"):
        return base[5:]
    if base.endswith("_test"):
        return base[:-5]
    return None


def _is_advisory_clock_call(node: ast.Call) -> bool:
    """Check if *node* is a call to a non-deterministic clock: ``datetime.now()``,
    ``datetime.utcnow()``, ``time.time()``, or ``time.monotonic()``."""
    func = node.func
    # datetime.now / datetime.utcnow
    if isinstance(func, ast.Attribute) and func.attr in ("now", "utcnow"):
        if isinstance(func.value, ast.Name) and func.value.id == "datetime":
            return True
        if isinstance(func.value, ast.Attribute) and func.value.attr == "datetime":
            # e.g. datetime.datetime.now()
            if isinstance(func.value.value, ast.Name) and func.value.value.id == "datetime":
                return True
    # time.time / time.monotonic
    if isinstance(func, ast.Attribute) and func.attr in ("time", "monotonic"):
        if isinstance(func.value, ast.Name) and func.value.id == "time":
            return True
    return False


def _run_test_quality(check: dict, config: dict, out_path: Path) -> dict:
    """In-process AST detector for test-quality smells.

    Scans test files (``test_*.py`` / ``*_test.py``) for forced-green assertions,
    empty tests, unfrozen clocks, self-mocking, and discarded return values.
    """
    repo_root = _resolve_repo_root()
    scan_paths = _check_paths("test-quality", config)
    findings: list[dict] = []
    check_name = "test-quality"

    for py_path in _iter_py_files(repo_root, scan_paths, tests_only=True):
        try:
            tree = ast.parse(py_path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue

        rel = str(py_path.relative_to(repo_root))

        for node in ast.walk(tree):
            # --- assert-true ---
            if isinstance(node, ast.Assert):
                if isinstance(node.test, ast.Constant) and node.test.value is True:
                    findings.append(
                        {
                            "check": check_name,
                            "rule": "assert-true",
                            "path": rel,
                            "line": node.lineno,
                            "message": "tautological `assert True`",
                        }
                    )
                elif isinstance(node.test, ast.BoolOp) and isinstance(node.test.op, ast.Or):
                    for operand in node.test.values:
                        if isinstance(operand, ast.Constant) and operand.value is True:
                            findings.append(
                                {
                                    "check": check_name,
                                    "rule": "assert-or-true",
                                    "path": rel,
                                    "line": node.lineno,
                                    "message": "forced-green `assert ... or True`",
                                }
                            )
                            break

            # --- empty-test ---
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test"):
                body = node.body
                # Drop leading docstring
                if (
                    body
                    and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)
                ):
                    body = body[1:]
                # Check if body is empty or only pass
                if not body or all(isinstance(stmt, ast.Pass) for stmt in body):
                    findings.append(
                        {
                            "check": check_name,
                            "rule": "empty-test",
                            "path": rel,
                            "line": node.lineno,
                            "message": "empty test body (no assertions)",
                        }
                    )

        # Second pass: scope-sensitive checks (inside test functions)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                _check_test_func_for_clock_and_discard(node, findings, check_name, rel)

        # --- self-mock (file-level, not scope-constrained) ---
        module_under_test = _module_under_test(py_path.name)
        if module_under_test is not None:
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    func_name = None
                    if isinstance(func, ast.Name):
                        func_name = func.id
                    elif isinstance(func, ast.Attribute):
                        # func.attr is "patch" for mock.patch / unittest.mock.patch;
                        # "object" for patch.object (a non-string first arg — skipped below).
                        func_name = func.attr
                    if func_name in ("patch",):
                        args = node.args
                        if (
                            args
                            and isinstance(args[0], ast.Constant)
                            and isinstance(args[0].value, str)
                        ):
                            target_root = args[0].value.split(".")[0]
                            if target_root == module_under_test:
                                findings.append(
                                    {
                                        "check": check_name,
                                        "rule": "self-mock",
                                        "path": rel,
                                        "line": node.lineno,
                                        "message": "test mocks the module under test (self-mock)",
                                    }
                                )

    _write_json(out_path, findings)
    return {"status": "FINDINGS" if findings else "ok", "findings": findings}


def _check_test_func_for_clock_and_discard(
    func_node: ast.FunctionDef, findings: list[dict], check_name: str, rel: str
) -> None:
    """Check a single test function body for unfrozen-clock and discarded-return-flag."""
    for node in ast.walk(func_node):
        # --- unfrozen-clock (ADVISORY) ---
        if isinstance(node, ast.Call) and _is_advisory_clock_call(node):
            findings.append(
                {
                    "check": check_name,
                    "rule": "unfrozen-clock",
                    "path": rel,
                    "line": node.lineno,
                    "message": "advisory: unfrozen clock in test — freeze it for determinism",
                }
            )
        # --- discarded-return-flag (ADVISORY) ---
        if isinstance(node, ast.Assign):
            if node.targets and isinstance(node.targets[0], ast.Tuple):
                target = node.targets[0]
                if any(isinstance(el, ast.Name) and el.id == "_" for el in target.elts):
                    if isinstance(node.value, ast.Call):
                        findings.append(
                            {
                                "check": check_name,
                                "rule": "discarded-return-flag",
                                "path": rel,
                                "line": node.lineno,
                                "message": "advisory: discarded return value (`, _ =`) — a returned status may be dropped (many uses are legitimate, e.g. `x, _ = divmod(...)`)",
                            }
                        )


def _run_data_scale(check: dict, config: dict, out_path: Path) -> dict:
    """In-process AST detector for unbounded data materialization.

    Scans non-test Python source for ``.fetchall()`` calls.
    """
    repo_root = _resolve_repo_root()
    scan_paths = _check_paths("data-scale", config)
    findings: list[dict] = []
    check_name = "data-scale"

    for py_path in _iter_py_files(repo_root, scan_paths, source_only=True):
        try:
            tree = ast.parse(py_path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue

        rel = str(py_path.relative_to(repo_root))

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "fetchall"
            ):
                findings.append(
                    {
                        "check": check_name,
                        "rule": "unbounded-fetchall",
                        "path": rel,
                        "line": node.lineno,
                        "message": (
                            "unbounded `.fetchall()` — record an at-scale run or a"
                            " bounded-domain argument in notes.md, or add a LIMIT/pagination"
                        ),
                    }
                )

    _write_json(out_path, findings)
    return {"status": "FINDINGS" if findings else "ok", "findings": findings}


def _iter_py_files(
    repo_root: Path, paths: list[str], *, tests_only=False, source_only=False
) -> list[Path]:
    """Walk *paths* (relative to *repo_root*) and yield Python source files.

    Keyword-only bool params (exactly one True per call):
      *tests_only*  — yield only test files (``test_*.py`` / ``*_test.py``).
      *source_only* — yield only non-test files (the complement of tests_only).
    """
    assert tests_only != source_only, "exactly one of tests_only/source_only must be True"
    exclude_dirs = {".venv", ".git", "__pycache__"}
    result: list[Path] = []
    for rel in paths:
        scan_dir = (repo_root / rel).resolve()
        if not scan_dir.is_dir():
            continue
        for py_path in sorted(scan_dir.rglob("*.py")):
            # Skip excluded directories
            if any(
                part in exclude_dirs or part.startswith(".")
                for part in py_path.relative_to(scan_dir).parts
            ):
                continue
            basename = py_path.name
            is_test = basename.startswith("test_") or basename.endswith("_test.py")
            if tests_only and not is_test:
                continue
            if source_only and is_test:
                continue
            result.append(py_path)
    return result


_BUILTIN_RUNNERS = {
    "ruff": _run_ruff,
    "gitleaks": _run_gitleaks,
    "osv-scanner": _run_osv_scanner,
    "deptry": _run_deptry,
    "radon": _run_radon,
    "jscpd": _run_jscpd,
    "vulture": _run_vulture,
    "test-quality": _run_test_quality,
    "data-scale": _run_data_scale,
}


def _coerce_config_str_list(value) -> tuple[list[str] | None, str | None]:
    """Coerce a TOML config value that should be a ``list[str]`` to one,
    tolerating the common scalar-string footgun: a bare string value naively
    indexed (``paths[0]`` grabs a CHARACTER) or iterated (``for q in
    queries`` yields one character per ``--queries`` flag) silently no-ops
    the check instead of raising. Returns ``(coerced_list, error_message)``
    — ``error_message`` is ``None`` on success. Anything that is neither a
    string nor a list (int, bool, dict, ...) is an explicit config-type
    error rather than a silent pass-through."""
    if isinstance(value, str):
        return [value], None
    if isinstance(value, list):
        return value, None
    return None, f"expected a string or list of strings, got {type(value).__name__}: {value!r}"


def _last_nonempty_line(text: str, fallback: str = "no error output captured") -> str:
    """Last non-blank line of *text*, or *fallback* if there is none."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    return lines[-1] if lines else fallback


def _run_delegate(check: dict, config: dict, out_path: Path) -> dict:
    name = check["name"]
    buf = StringIO()
    err_buf = StringIO()

    if name == "scope":
        with redirect_stdout(buf), redirect_stderr(err_buf):
            rc = audit_scope.main(["scan", "--json", str(out_path)])
        count = None
        if out_path.exists():
            try:
                count = len(json.loads(out_path.read_text()).get("files", []))
            except (json.JSONDecodeError, OSError):
                pass
        status = "INFRA-FAIL" if rc == 3 else "ok"
        outcome = {"status": status, "count": count}
        if status == "INFRA-FAIL":
            outcome["error"] = _last_nonempty_line(err_buf.getvalue())
        return outcome

    if name == "data-lint":
        argv = ["--json", str(out_path)]
        raw_paths = config.get("checks", {}).get("data-lint", {}).get("paths")
        if raw_paths:
            paths, err = _coerce_config_str_list(raw_paths)
            if err is not None:
                return {
                    "status": "INFRA-FAIL",
                    "count": None,
                    "error": f"[checks.data-lint].paths: {err}",
                }
            if len(paths) > 1:
                return {
                    "status": "INFRA-FAIL",
                    "count": None,
                    "error": (
                        "[checks.data-lint].paths: only a single checks "
                        f"directory is supported (first entry used; extra "
                        f"entries are a config error, not silently "
                        f"dropped), got {len(paths)} entries: {paths!r}"
                    ),
                }
            argv = ["--checks-dir", paths[0]] + argv
        with redirect_stdout(buf), redirect_stderr(err_buf):
            rc = data_lint.main(argv)
        count = None
        if out_path.exists():
            try:
                data = json.loads(out_path.read_text())
                count = sum(c["rows"] for c in data.get("checks", []) if c["status"] == "fail")
            except (json.JSONDecodeError, OSError, KeyError):
                pass
        status = "INFRA-FAIL" if rc == 3 else ("FINDINGS" if rc == 2 else "ok")
        outcome = {"status": status, "count": count}
        if status == "INFRA-FAIL":
            outcome["error"] = _last_nonempty_line(err_buf.getvalue())
        return outcome

    if name == "repo-lint":
        argv = ["--json", str(out_path)]
        raw_paths = config.get("checks", {}).get("repo-lint", {}).get("paths")
        if raw_paths:
            paths, err = _coerce_config_str_list(raw_paths)
            if err is not None:
                return {
                    "status": "INFRA-FAIL",
                    "count": None,
                    "error": f"[checks.repo-lint].paths: {err}",
                }
            if len(paths) > 1:
                return {
                    "status": "INFRA-FAIL",
                    "count": None,
                    "error": (
                        "[checks.repo-lint].paths: only a single checks "
                        f"directory is supported (first entry used; extra "
                        f"entries are a config error, not silently "
                        f"dropped), got {len(paths)} entries: {paths!r}"
                    ),
                }
            argv = ["--checks-dir", paths[0]] + argv
        with redirect_stdout(buf), redirect_stderr(err_buf):
            rc = repo_lint.main(argv)
        count = None
        if out_path.exists():
            try:
                data = json.loads(out_path.read_text())
                count = sum(c["findings"] for c in data.get("checks", []) if c["status"] == "fail")
            except (json.JSONDecodeError, OSError, KeyError):
                pass
        status = "INFRA-FAIL" if rc == 3 else ("FINDINGS" if rc == 2 else "ok")
        outcome = {"status": status, "count": count}
        if status == "INFRA-FAIL":
            outcome["error"] = _last_nonempty_line(err_buf.getvalue())
        return outcome

    if name == "index-coverage":
        idx_cfg = config.get("checks", {}).get("index-coverage", {})
        raw_schema = idx_cfg.get("schema")
        raw_queries = idx_cfg.get("queries", [])
        if not raw_schema:
            return {
                "status": "skipped",
                "count": None,
                "note": "no [checks.index-coverage].schema configured",
            }

        schema_list, err = _coerce_config_str_list(raw_schema)
        if err is not None:
            return {
                "status": "INFRA-FAIL",
                "count": None,
                "error": f"[checks.index-coverage].schema: {err}",
            }
        schema = schema_list[0]

        queries, err = _coerce_config_str_list(raw_queries)
        if err is not None:
            return {
                "status": "INFRA-FAIL",
                "count": None,
                "error": f"[checks.index-coverage].queries: {err}",
            }

        argv = ["--schema", schema, "--json", str(out_path)]
        for q in queries:
            argv.extend(["--queries", q])
        with redirect_stdout(buf), redirect_stderr(err_buf):
            rc = index_coverage.main(argv)
        count = None
        if out_path.exists():
            try:
                count = len(json.loads(out_path.read_text()).get("leads", []))
            except (json.JSONDecodeError, OSError):
                pass
        # index-coverage NEVER gates, even though rc could be 3 on infra
        # issues upstream — but a schema-glob failure IS still infra.
        status = "INFRA-FAIL" if rc == 3 else "ok"
        outcome = {"status": status, "count": count}
        if status == "INFRA-FAIL":
            outcome["error"] = _last_nonempty_line(err_buf.getvalue())
        return outcome

    if name == "outstanding":
        root = _resolve_repo_root()
        with redirect_stdout(buf), redirect_stderr(err_buf):
            outstanding.run(root, config, out_path)
        return {"status": "ok", "count": 0}

    raise ValueError(f"unknown delegate check: {name}")  # pragma: no cover


def _run_custom(check: dict, out_path: Path) -> dict:
    command = check.get("command", [])
    if not command:
        return {"status": "INFRA-FAIL", "error": "no command configured"}
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=300)
    except FileNotFoundError:
        return {"status": "INFRA-FAIL", "error": f"{command[0]} not found"}
    except subprocess.TimeoutExpired:
        return {"status": "INFRA-FAIL", "error": f"{command[0]} timed out"}
    out_path.write_text((result.stdout or "") + (result.stderr or ""), encoding="utf-8")
    if not check.get("gate", True):
        return {"status": "ok", "count": None}
    return {"status": "ok" if result.returncode == 0 else "FINDINGS", "count": None}


def _execute_check(
    check: dict, config: dict, out_dir: Path, repo_root: Path, avail: dict | None = None
) -> dict:
    name = check["name"]
    kind = check["kind"]

    if kind == "custom":
        out_path = out_dir / f"{name}.txt"
        outcome = _run_custom(check, out_path)
    elif name == "inventory":
        out_path = out_dir / f"{name}.json"
        payload = _run_inventory(repo_root)
        _write_json(out_path, payload)
        outcome = {"status": "ok", "count": 0}
    elif kind == "delegate":
        out_path = out_dir / f"{name}.json"
        outcome = _run_delegate(check, config, out_path)
    else:
        out_path = out_dir / f"{name}.json"
        outcome = _BUILTIN_RUNNERS[name](check, config, out_path)
        if "findings" in outcome:
            # Normalize -> repo-relative paths, then rewrite the artifact
            # the runner already wrote (all seven builtin parsers funnel
            # through this one point via their shared "findings" key).
            _normalize_finding_paths(outcome["findings"], repo_root)
            _write_json(out_path, outcome["findings"])
            outcome["count"] = len(outcome["findings"])

    record = {
        "check": name,
        "status": outcome["status"],
        "count": outcome.get("count"),
        "artifact": str(out_path),
    }
    # Record the probed tool version for EVERY builtin check (binary tools
    # already gated on mismatch before we got here; Python-ecosystem tools
    # are pinned per-repo, not here — their version is only ever *recorded*,
    # never gated, and `null` when unprobeable, per task 4.3).
    if kind == "builtin" and avail is not None:
        record["version"] = avail.get("version")
    if "findings" in outcome:
        record["_findings"] = outcome["findings"]  # internal-only, stripped before manifest write
    if "error" in outcome:
        record["error"] = outcome["error"]
    return record


def _summary_line(record: dict) -> str:
    status_display = {
        "ok": "ok",
        "FINDINGS": "FINDINGS",
        "INFRA-FAIL": "INFRA-FAIL",
        "skipped": "skipped",
    }.get(record["status"], record["status"])
    count = record["count"]
    count_display = "?" if count is None else str(count)
    return f"{record['check']}: {status_display} — {count_display} findings -> {record['artifact']}"


# ---------------------------------------------------------------------------
# Baseline diff (4.6)
# ---------------------------------------------------------------------------


def _fingerprint(finding: dict) -> str:
    message = re.sub(r"\s+", " ", (finding.get("message") or "").strip())
    parts = [
        finding.get("check") or "",
        finding.get("rule") or "",
        finding.get("path") or "",
        message,
    ]
    return hashlib.sha1("\0".join(parts).encode("utf-8")).hexdigest()


def _baseline_diff(current: list[dict], baseline: list[dict]) -> dict:
    current_by_fp = {_fingerprint(f): f for f in current}
    baseline_by_fp = {_fingerprint(f): f for f in baseline}

    new_fps = set(current_by_fp) - set(baseline_by_fp)
    resolved_fps = set(baseline_by_fp) - set(current_by_fp)
    unchanged_count = len(set(current_by_fp) & set(baseline_by_fp))

    return {
        "new": [current_by_fp[fp] for fp in new_fps],
        "resolved": [baseline_by_fp[fp] for fp in resolved_fps],
        "unchanged_count": unchanged_count,
    }


# ---------------------------------------------------------------------------
# Run-manifest helpers (checkpointing, 4.4)
# ---------------------------------------------------------------------------


def _write_manifest(path: Path, meta: dict, records: list[dict]) -> None:
    clean_records = [{k: v for k, v in r.items() if not k.startswith("_")} for r in records]
    array = [{"meta": True, **meta}, *clean_records]
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(array, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _read_manifest(path: Path) -> tuple[dict, list[dict]]:
    if not path.exists():
        return {}, []
    try:
        array = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}, []
    meta = {}
    records = []
    for item in array:
        if item.get("meta"):
            meta = {k: v for k, v in item.items() if k != "meta"}
        else:
            records.append(item)
    return meta, records


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------


def _all_checks(config: dict) -> list[dict]:
    return [*_REGISTRY, *_custom_checks(config)]


def _mode_list(config: dict, defaults: dict, pins: dict, repo_root: Path) -> int:
    unavailable_enabled_checks = 0
    for check in _all_checks(config):
        name = check["name"]
        tier = check["tier"]
        family = check.get("family", "check")
        if check["kind"] == "custom":
            enabled = True  # a custom check's presence in checks.toml IS the opt-in
        else:
            enabled = _is_enabled(name, config, defaults)
        avail = _availability_for_check(check, pins)
        print(
            f"{name}  {tier}  {family}  {'enabled' if enabled else 'disabled'}  {avail['status']}"
        )
        if enabled and family == "check" and avail["status"] in ("unavailable", "version-mismatch"):
            unavailable_enabled_checks += 1
    if unavailable_enabled_checks:
        print(
            f"checks: {unavailable_enabled_checks} enabled check(s) unavailable"
            f" — --floor/--report will fail preflight until installed or disabled."
        )
    return 0


def _mode_check(
    name: str, config: dict, defaults: dict, pins: dict, repo_root: Path, out_dir: Path
) -> int:
    all_checks = {c["name"]: c for c in _all_checks(config)}
    if name not in all_checks:
        print(f"checks: INFRA-FAIL — unknown check {name!r}", file=sys.stderr)
        return 3
    check = all_checks[name]

    avail = _availability_for_check(check, pins)
    out_dir.mkdir(parents=True, exist_ok=True)

    if avail["status"] == "unavailable":
        record = {"check": name, "status": "skipped", "count": None, "artifact": ""}
        print(_summary_line(record))
        return 0
    if avail["status"] == "version-mismatch":
        print(
            f"checks: INFRA-FAIL — {name}: version mismatch "
            f"(expected {avail['expected']}, found {avail['version']})",
            file=sys.stderr,
        )
        return 3

    record = _execute_check(check, config, out_dir, repo_root, avail)
    print(_summary_line(record))
    if record["status"] == "INFRA-FAIL":
        return 3
    if record["status"] == "FINDINGS":
        return 2
    return 0


def _mode_multi(
    tiers: set[str],
    config: dict,
    defaults: dict,
    pins: dict,
    repo_root: Path,
    out_dir: Path,
    resume: bool,
    baseline_path: str | None,
    date_str: str,
    config_source: str,
    enforce_empty_out_dir: bool = False,
    include_list: list[str] | None = None,
) -> int:
    all_checks = _all_checks(config)

    # Validate --include names before selecting checks.
    if include_list:
        registered_names = {c["name"] for c in all_checks}
        for name in include_list:
            if name not in registered_names:
                print(
                    f"checks: INFRA-FAIL — unknown check {name!r} in --include",
                    file=sys.stderr,
                )
                return 3

    selected = []
    for check in all_checks:
        if check["tier"] not in tiers:
            continue
        if tiers == {"floor"} and check.get("family") != "check":
            continue
        if check["kind"] == "custom":
            enabled = True
        else:
            enabled = _is_enabled(check["name"], config, defaults)
        # Force-enable if the name appears in --include (for this run only).
        if include_list and check["name"] in include_list:
            enabled = True
        if enabled:
            selected.append(check)

    if not selected and tiers == {"floor"}:
        print("checks: no floor checks enabled")
        return 0

    # The non-empty---out refusal is a --report-only guarantee (task 4.4) —
    # --floor writes into the CWD by default, which is always non-empty.
    if enforce_empty_out_dir and out_dir.exists() and any(out_dir.iterdir()) and not resume:
        print(
            f"checks: INFRA-FAIL — --out {out_dir} already exists and is non-empty "
            "(use --resume or a different --out)",
            file=sys.stderr,
        )
        return 3
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = out_dir / "run-manifest.json"
    _prior_meta, _raw_prior_records = _read_manifest(manifest_path) if resume else ({}, [])
    # A prior INFRA-FAIL record is the abort point, not a completion — retry
    # it on resume rather than skipping it forever. Only genuinely finished
    # checks (ok/FINDINGS/skipped) count as "completed" for --resume.
    prior_records = [r for r in _raw_prior_records if r.get("status") != "INFRA-FAIL"]
    completed_names = {r["check"] for r in prior_records}

    records: list[dict] = list(prior_records)
    all_findings: list[dict] = []
    for r in prior_records:
        # `_findings` is never persisted in the manifest (kept lean) — recover
        # a completed builtin-parsed check's contribution from its own JSON
        # artifact on disk instead.
        if r["check"] in _PARSERS and r.get("artifact"):
            try:
                all_findings.extend(json.loads(Path(r["artifact"]).read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                pass

    meta = {"config": config_source, "date": date_str}
    aborted = False

    # Preflight: check availability for all selected check-family entries
    # before executing any. Fact-family entries are exempt (graceful degradation).
    preflight_failures = []
    for check in selected:
        name = check["name"]
        if name in completed_names:
            continue
        if check.get("family") != "check":
            continue
        avail = _availability_for_check(check, pins)
        if avail["status"] in ("unavailable", "version-mismatch"):
            preflight_failures.append((check, avail))

    if preflight_failures:
        for check, avail in preflight_failures:
            name = check["name"]
            trigger = check.get("trigger", "auto-detected")
            coverage_note = check.get("coverage_note", "")
            if avail["status"] == "unavailable":
                reason = "not on PATH"
                install_part = f"Install {name}"
            else:
                reason = (
                    f"version mismatch (expected {avail['expected']}, found {avail['version']})"
                )
                install_part = f"Install {name} {avail['expected']}"
            print(
                f"checks: INFRA-FAIL — {name}: {reason}"
                f" (enabled by trigger: {trigger})."
                f" {install_part}, or"
                f" disable in checks.toml: [checks.{name}] enabled = false"
                f" — {coverage_note}.",
                file=sys.stderr,
            )
            error_msg = (
                "unavailable"
                if avail["status"] == "unavailable"
                else f"version mismatch: expected {avail['expected']}, found {avail['version']}"
            )
            record = {
                "check": name,
                "status": "INFRA-FAIL",
                "count": None,
                "artifact": "",
                "error": error_msg,
            }
            records.append(record)
        _write_manifest(manifest_path, meta, records)
        return 3

    for check in selected:
        name = check["name"]
        if name in completed_names:
            # Already completed in a prior run — replay its summary line,
            # do NOT re-execute it.
            prior_record = next(r for r in prior_records if r["check"] == name)
            print(_summary_line(prior_record))
            continue

        avail = _availability_for_check(check, pins)
        if avail["status"] in ("unavailable", "version-mismatch"):
            is_fact = check.get("family") == "fact"
            if avail["status"] == "unavailable":
                reason = "not on PATH" if not is_fact else "unavailable (graceful degradation)"
                error_detail = "unavailable"
            else:
                reason = (
                    f"version mismatch (expected {avail['expected']}, found {avail['version']})"
                )
                error_detail = (
                    f"version mismatch: expected {avail['expected']}, found {avail['version']}"
                )
            if is_fact:
                # Fact-family: degrade gracefully — record as skipped and continue.
                record = {"check": name, "status": "skipped", "count": None, "artifact": ""}
                print(_summary_line(record))
                records.append(record)
                _write_manifest(manifest_path, meta, records)
            else:
                # Check-family: INFRA-FAIL with install-or-disable guidance.
                print(
                    f"checks: INFRA-FAIL — {name}: {reason}"
                    f" (enabled by trigger: {check.get('trigger', 'auto-detected')})."
                    f" Install {name}{' ' + avail['expected'] if avail['expected'] else ''}, or"
                    f" disable in checks.toml: [checks.{name}] enabled = false"
                    f" — {check.get('coverage_note', '')}.",
                    file=sys.stderr,
                )
                record = {
                    "check": name,
                    "status": "INFRA-FAIL",
                    "count": None,
                    "artifact": "",
                    "error": error_detail,
                }
                records.append(record)
                _write_manifest(manifest_path, meta, records)
                aborted = True
                break
        else:
            record = _execute_check(check, config, out_dir, repo_root, avail)
            print(_summary_line(record))
            records.append(record)
            _write_manifest(manifest_path, meta, records)

            if record["status"] == "INFRA-FAIL":
                if check.get("family") == "check":
                    print(
                        f"  (enabled by trigger: {check.get('trigger', 'auto-detected')})."
                        f" Install {name}, or"
                        f" disable in checks.toml: [checks.{name}] enabled = false"
                        f" — {check.get('coverage_note', '')}.",
                        file=sys.stderr,
                    )
                    aborted = True
                    break
                # Fact-family INFRA-FAIL degrades gracefully — continue.
            else:
                all_findings.extend(record.get("_findings", []))

    findings_path = out_dir / "findings.json"
    _write_json(findings_path, all_findings)

    exit_code = 3 if aborted else 0

    if not aborted:
        if baseline_path:
            try:
                baseline = json.loads(Path(baseline_path).read_text(encoding="utf-8"))
            except OSError as exc:
                print(f"checks: INFRA-FAIL — could not read baseline: {exc}", file=sys.stderr)
                return 3
            diff = _baseline_diff(all_findings, baseline)
            _write_json(out_dir / "delta.json", diff)
            print(
                f"delta: {len(diff['new'])} new, {len(diff['resolved'])} resolved vs {baseline_path}"
            )
            exit_code = 2 if diff["new"] else 0
        else:
            exit_code = 2 if any(r["status"] == "FINDINGS" for r in records) else 0

    print(f"checks: {len(all_findings)} findings across {len(records)} checks -> {out_dir}")
    return exit_code


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check-only audit orchestrator (D1, D2, D3, D6, D8)."
    )
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--list", action="store_true", help="Enumerate registered checks.")
    mode_group.add_argument("--check", metavar="NAME", help="Run exactly one check.")
    mode_group.add_argument("--floor", action="store_true", help="Run all enabled floor checks.")
    mode_group.add_argument(
        "--report", action="store_true", help="Run floor+heavy+snapshot checks."
    )

    parser.add_argument("--out", default=None, help="Output directory.")
    parser.add_argument("--date", default=None, help="Audit date, YYYY-MM-DD (default: today).")
    parser.add_argument(
        "--resume", action="store_true", help="Resume a --report run (skip completed checks)."
    )
    parser.add_argument(
        "--baseline", default=None, help="Prior findings.json to diff against (--report only)."
    )
    parser.add_argument(
        "--include",
        action="append",
        default=None,
        metavar="NAME",
        help="Force-enable a registered-but-disabled check for this run (--report only).",
    )

    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    if args.baseline and not args.report:
        print("checks: INFRA-FAIL — --baseline is only valid with --report", file=sys.stderr)
        return 3
    if args.resume and not args.report:
        print("checks: INFRA-FAIL — --resume is only valid with --report", file=sys.stderr)
        return 3
    if args.include and not args.report:
        print("checks: INFRA-FAIL — --include is only valid with --report", file=sys.stderr)
        return 3

    repo_root = _resolve_repo_root()
    config, config_source = _load_config(repo_root)
    defaults = _autodetect_defaults(repo_root)
    pins = {**EXPECTED_TOOL_VERSIONS, **config.get("tools", {})}

    date_str = args.date or date.today().isoformat()

    if args.list:
        return _mode_list(config, defaults, pins, repo_root)

    if args.check:
        out_dir = Path(args.out) if args.out else Path(".")
        return _mode_check(args.check, config, defaults, pins, repo_root, out_dir)

    if args.floor:
        out_dir = Path(args.out) if args.out else Path(".")
        return _mode_multi(
            {"floor"},
            config,
            defaults,
            pins,
            repo_root,
            out_dir,
            resume=False,
            baseline_path=None,
            date_str=date_str,
            config_source=config_source,
            include_list=None,
        )

    # --report
    if args.out:
        out_dir = Path(args.out)
    else:
        out_dir = Path("output") / "checks" / date_str
    return _mode_multi(
        {"floor", "heavy", "snapshot"},
        config,
        defaults,
        pins,
        repo_root,
        out_dir,
        resume=args.resume,
        baseline_path=args.baseline,
        date_str=date_str,
        config_source=config_source,
        enforce_empty_out_dir=True,
        include_list=args.include,
    )


if __name__ == "__main__":
    sys.exit(main())
