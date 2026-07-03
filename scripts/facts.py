#!/usr/bin/env python3
"""facts.py — thin facts-only CLI (cache-semantics repo snapshots).

Checks/facts/audit trichotomy:
  **facts** = can't-fail repo snapshots (cache semantics, undated output,
  regenerate-on-use). ``scope``, ``radon``, ``index-coverage``, ``inventory``.

Entry point: ``facts.py`` (facts only, no tag/log/baseline surface).

Imports the engine from ``scripts/checks.py``. Does NOT call ``_mode_multi``
and is therefore never subject to preflight. Runs its own loop calling
``_execute_check`` directly for each selected fact with
``out_dir = Path("output") / "facts"`` (undated, artifacts overwritten each
run). Exit code is always 0 once arguments parse; per-fact tool degradation
is recorded in the artifact JSON, never a process failure.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from checks import (  # noqa: E402
    EXPECTED_TOOL_VERSIONS,
    _all_checks,
    _autodetect_defaults,
    _availability_for_check,
    _execute_check,
    _is_enabled,
    _load_config,
    _resolve_repo_root,
    _summary_line,
)


def _fact_checks(config: dict) -> list[dict]:
    """Return all registered entries with family == 'fact'."""
    return [c for c in _all_checks(config) if c.get("family") == "fact"]


def _mode_list_facts(config: dict, defaults: dict, pins: dict) -> int:
    """List fact-family entries only (same line shape as checks.py --list)."""
    for check in _fact_checks(config):
        name = check["name"]
        tier = check["tier"]
        family = "fact"
        if check["kind"] == "custom":
            enabled = True
        else:
            enabled = _is_enabled(name, config, defaults)
        avail = _availability_for_check(check, pins)
        print(
            f"{name}  {tier}  {family}  {'enabled' if enabled else 'disabled'}  {avail['status']}"
        )
    return 0


def _mode_facts(config: dict, defaults: dict, pins: dict, repo_root: Path) -> int:
    """Run all enabled fact-family entries."""
    out_dir = Path("output") / "facts"
    out_dir.mkdir(parents=True, exist_ok=True)
    for check in _fact_checks(config):
        name = check["name"]
        if check["kind"] == "custom":
            enabled = True
        else:
            enabled = _is_enabled(name, config, defaults)
        if not enabled:
            continue
        avail = _availability_for_check(check, pins)
        record = _execute_check(check, config, out_dir, repo_root, avail)
        print(_summary_line(record))
    return 0


def _mode_fact_check(name: str, config: dict, defaults: dict, pins: dict, repo_root: Path) -> int:
    """Run a single fact by name. A check-family name is a usage error."""
    all_checks = {c["name"]: c for c in _all_checks(config)}
    if name not in all_checks:
        print(f"facts: unknown fact {name!r}", file=sys.stderr)
        return 2
    check = all_checks[name]
    if check.get("family") != "fact":
        print(
            f"facts: {name!r} is a check-family detector, not a fact — use checks.py",
            file=sys.stderr,
        )
        return 2
    out_dir = Path("output") / "facts"
    out_dir.mkdir(parents=True, exist_ok=True)
    avail = _availability_for_check(check, pins)
    record = _execute_check(check, config, out_dir, repo_root, avail)
    print(_summary_line(record))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Facts-only CLI (cache-semantics repo snapshots).")
    parser.add_argument("--list", action="store_true", help="Enumerate fact entries.")
    parser.add_argument(
        "--check", metavar="NAME", help="Run exactly one fact (default: all enabled facts)."
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    repo_root = _resolve_repo_root()
    config, _config_source = _load_config(repo_root)
    defaults = _autodetect_defaults(repo_root)
    pins = {**EXPECTED_TOOL_VERSIONS, **config.get("tools", {})}

    if args.list:
        return _mode_list_facts(config, defaults, pins)

    if args.check:
        return _mode_fact_check(args.check, config, defaults, pins, repo_root)

    # No flag = default mode: run all enabled facts
    return _mode_facts(config, defaults, pins, repo_root)


if __name__ == "__main__":
    sys.exit(main())
