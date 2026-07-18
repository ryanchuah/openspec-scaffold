#!/usr/bin/env python3
"""opencode_delegate — ingest wrapper for delegated ``opencode run`` post-processing.

Reads the stdout JSONL, stderr log, and exit source of one completed
``opencode run`` invocation, then: detects silent agent fallback, extracts the
completion text (last ``type:"text"`` part), asserts optional required-marker
regexes, optionally captures a verdict token via a regex, classifies the run
status (``ok|fallback|timeout|crash|truncated-stream|marker-missing``), appends one telemetry
line to the ledger at ``output/delegation-log.jsonl``, and writes the extracted
text + a machine-readable result file.

Exit code: 0 iff status == "ok", else 1.

The wrapper reports facts about ONE run.  It does NOT judge disk state, does
NOT implement the failure ladder (retry/Sonnet fallback/git-restore), and does
NOT gate anything — those remain orchestrator judgment.

Usage
-----
::

    opencode_delegate.py \\
        --phase <phase> --agent <agent> --model <model> --change <change> \\
        --out <out.jsonl> --err <err.log> \\
        (--exit <int> | --exit-file <file>) \\
        [--require-marker <regex> ...] [--verdict-regex <regex>] \\
        [--retry <n>] [--tag <k=v> ...] \\
        [--ledger <path>] [--repo-root <path>] \\
        [--text-out <path>] [--result-out <path>] [--quiet]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Pure helpers (no subprocess, no I/O beyond stated params)
# ---------------------------------------------------------------------------


def extract_text(out_jsonl_text: str) -> str | None:
    """Parse the stdout as JSON-lines and return the last ``type:"text"`` part's text.

    Tolerates non-JSON / blank lines (skip them).  Returns ``None`` if no text
    part is found or the text is empty/whitespace-only.
    """
    last_text: str | None = None
    for raw_line in out_jsonl_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and obj.get("type") == "text":
            part = obj.get("part")
            if isinstance(part, dict):
                text = part.get("text")
                if isinstance(text, str) and text.strip():
                    last_text = text
    return last_text


def detect_truncated_stream(out_jsonl_text: str) -> bool:
    """Detect a silently-truncated opencode stream by counting step events.

    A healthy run balances ``step_start`` / ``step_finish`` events.  When the
    provider stream returns an empty completion, opencode may exit 0 with an
    unterminated final step, leaving ``step_start > step_finish``.

    Parses each JSONL line from *out_jsonl_text*; skips blank / non-JSON /
    non-dict lines.  Returns ``True`` when ``step_start`` count exceeds
    ``step_finish`` count.  Returns ``False`` on balanced counts, no step
    events, or any parse degradation.
    """
    starts = 0
    finishes = 0
    for raw_line in out_jsonl_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict):
            continue
        t = obj.get("type")
        if t == "step_start":
            starts += 1
        elif t == "step_finish":
            finishes += 1
    return starts > finishes


def detect_fallback(err_text: str) -> bool:
    """Return True iff *err_text* contains the fallback-warning substring."""
    return "Falling back to default agent" in err_text


def parse_exit_file(text: str) -> int | None:
    """Parse an EXIT-sentinel file body (``EXIT=124``) and return the int.

    Returns ``None`` if the text is unparseable.
    """
    text = text.strip()
    if text.startswith("EXIT="):
        try:
            return int(text[len("EXIT=") :])
        except (ValueError, IndexError):
            return None
    return None


def assert_markers(text: str | None, markers: list[str]) -> bool:
    """Return True iff *text* is not None and every regex in *markers* matches.

    Each regex is tested with ``re.search(re.MULTILINE)``.  Malformed regexes
    (``re.error``) are caught and treated as not-matched — the wrapper NEVER
    raises on bad input.
    """
    if text is None:
        return False
    if not markers:
        return True
    for marker in markers:
        try:
            if not re.search(marker, text, re.MULTILINE):
                return False
        except re.error:
            # T3: malformed marker regex → treat as not-matched
            return False
    return True


def extract_verdict(text: str | None, regex: str | None) -> str | None:
    """Extract a verdict token using *regex* from *text*.

    If the regex has a capture group, return ``m.group(1)``; otherwise return
    ``m.group(0)``.  Return ``None`` when *regex* or *text* is ``None``, or no
    match is found.  ``re.error`` is caught and returns ``None``.
    """
    if regex is None or text is None:
        return None
    try:
        m = re.search(regex, text, re.MULTILINE)
    except re.error:
        return None
    if m is None:
        return None
    try:
        return m.group(1)
    except IndexError:
        return m.group(0)


def classify_status(
    exit_code: int | None,
    fallback: bool,
    text: str | None,
    marker_ok: bool,
    truncated: bool = False,
) -> str:
    """Classify the run status.

    Precedence:
        1. ``fallback`` → ``"fallback"``
        2. ``exit_code in (124, 137)`` → ``"timeout"``
        3. ``text`` is empty/``None`` → ``"crash"``
        4. ``truncated`` → ``"truncated-stream"``
        5. ``not marker_ok`` → ``"marker-missing"``
        6. Otherwise → ``"ok"``

    Note the **exit-code lie**: a nonzero exit code NOT in (124, 137) with
    present text and marker_ok does NOT downgrade from ``"ok"`` — the raw exit
    is recorded separately.  ``exit_code=None`` (unreadable exit-file) is also
    not in (124, 137), so it falls through to the text/marker checks.
    """
    if fallback:
        return "fallback"
    if exit_code is not None and exit_code in (124, 137):
        return "timeout"
    if not text:  # None or empty/whitespace
        return "crash"
    if truncated:
        return "truncated-stream"
    if not marker_ok:
        return "marker-missing"
    return "ok"


def best_effort_duration(out_jsonl_text: str) -> float | None:
    """Best-effort run duration (seconds) from JSONL part timestamps.

    Gathers every numeric timestamp found across all parseable lines and
    returns ``max - min``, coercing epoch-ms → s (any value ``> 1e12``).
    Returns ``None`` if fewer than two timestamps are found or the span is
    negative.  Any parse issue degrades to ``None`` — this is best-effort
    telemetry (notes A2), never a hard signal.

    Observed opencode format (probed 2026-07-13): a text part carries
    ``part.time = {"start": <epoch-ms>, "end": <epoch-ms>}``.  This function
    reads those, and also tolerates a scalar ``time`` / ``timestamp`` at the
    top level or under ``part`` for forward/backward compatibility.
    """
    stamps: list[float] = []
    for raw_line in out_jsonl_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        stamps.extend(_extract_timestamps(obj))
    if len(stamps) < 2:
        return None
    coerced = [s / 1000.0 if s > 1e12 else s for s in stamps]
    duration = max(coerced) - min(coerced)
    return duration if duration >= 0 else None


def _is_number(val: Any) -> bool:
    """True iff *val* is a real number (int/float) and not a bool."""
    return isinstance(val, (int, float)) and not isinstance(val, bool)


def _extract_timestamps(obj: dict) -> list[float]:
    """Return every numeric timestamp found in a JSONL object.

    Handles the observed ``part.time = {"start", "end"}`` object form plus
    scalar ``time`` / ``timestamp`` at top level or under ``part``.
    """
    found: list[float] = []
    if not isinstance(obj, dict):
        return found
    for key in ("time", "timestamp"):
        if _is_number(obj.get(key)):
            found.append(float(obj[key]))
    part = obj.get("part")
    if isinstance(part, dict):
        for key in ("time", "timestamp"):
            val = part.get(key)
            if _is_number(val):
                found.append(float(val))
            elif isinstance(val, dict):
                # Observed form: part.time = {"start": ms, "end": ms}
                for sub in ("start", "end"):
                    if _is_number(val.get(sub)):
                        found.append(float(val[sub]))
    return found


CORE_LEDGER_KEYS = frozenset(
    {
        "ts",
        "phase",
        "agent",
        "model",
        "change",
        "exit",
        "fallback",
        "status",
        "marker_ok",
        "verdict",
        "retry",
        "duration_s",
    }
)


def build_ledger_record(
    *,
    ts: str,
    phase: str,
    agent: str,
    model: str,
    change: str,
    exit_code: int | None,
    fallback: bool,
    status: str,
    marker_ok: bool,
    verdict: str | None,
    retry: int,
    duration_s: float | None,
    tags: dict,
) -> dict:
    """Assemble the ledger dict with exactly the 12 core keys plus merged *tags*.

    *ts* is a REQUIRED parameter (injected — do NOT call a clock inside this
    function; tests depend on determinism).  Tags that collide with a core key
    are prefixed with ``tag_``.
    """
    record: dict[str, Any] = {
        "ts": ts,
        "phase": phase,
        "agent": agent,
        "model": model,
        "change": change,
        "exit": exit_code,
        "fallback": fallback,
        "status": status,
        "marker_ok": marker_ok,
        "verdict": verdict,
        "retry": retry,
        "duration_s": duration_s,
    }
    for k, v in tags.items():
        if k in CORE_LEDGER_KEYS:
            k = f"tag_{k}"
        record[k] = v
    return record


# ---------------------------------------------------------------------------
# CLI + main
# ---------------------------------------------------------------------------


def _resolve_repo_root() -> str:
    """Return the parent of the script's directory (fallback repo root)."""
    return str(Path(__file__).resolve().parent.parent)


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        description="Post-process one delegated ``opencode run`` invocation.",
    )
    parser.add_argument("--phase", required=True, help="Phase identifier (e.g. apply, verify-pro)")
    parser.add_argument("--agent", required=True, help="Agent name")
    parser.add_argument("--model", required=True, help="Model identifier")
    parser.add_argument("--change", required=True, help="Change identifier")
    parser.add_argument("--out", required=True, help="Path to stdout JSONL file")
    parser.add_argument("--err", required=True, help="Path to stderr log file")

    # Exit code source: exactly one of --exit or --exit-file required
    exit_group = parser.add_mutually_exclusive_group(required=True)
    exit_group.add_argument("--exit", type=int, default=None, help="Literal exit code")
    exit_group.add_argument(
        "--exit-file", type=str, default=None, help="Path to EXIT-sentinel file"
    )

    parser.add_argument(
        "--require-marker",
        action="append",
        default=[],
        dest="markers",
        help="Regex that must match in extracted text (repeatable)",
    )
    parser.add_argument(
        "--verdict-regex", type=str, default=None, help="Regex to capture verdict token"
    )
    parser.add_argument("--retry", type=int, default=0, help="Retry ordinal (default 0)")
    parser.add_argument(
        "--tag",
        action="append",
        default=[],
        dest="tags_raw",
        help="Tag in k=v format (repeatable)",
    )
    parser.add_argument(
        "--ledger",
        type=str,
        default=None,
        help="Path to ledger file (default: <repo-root>/output/delegation-log.jsonl)",
    )
    parser.add_argument(
        "--repo-root",
        type=str,
        default=None,
        help="Repository root (default: parent of script directory)",
    )
    parser.add_argument(
        "--text-out",
        type=str,
        default=None,
        help="Path for extracted text (default: <out>.text.txt)",
    )
    parser.add_argument(
        "--result-out",
        type=str,
        default=None,
        help="Path for result JSON (default: <out>.result.json)",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress extracted-text printing")
    return parser


def _read_file(path: str) -> str:
    """Read a file, returning empty string on missing/unreadable (T3)."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except (FileNotFoundError, PermissionError, OSError):
        return ""


def _resolve_tags(tags_raw: list[str]) -> dict:
    """Parse ``k=v`` tags into a dict.  A tag without ``=`` raises argparse error."""
    tags: dict = {}
    for tag in tags_raw:
        if "=" not in tag:
            raise argparse.ArgumentTypeError(f"Malformed tag {tag!r}: must be k=v format")
        k, _, v = tag.partition("=")
        tags[k] = v
    return tags


def main(argv: list[str] | None = None) -> int:
    """Entry point.

    Returns 0 iff ``status == "ok"``, else 1.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # Resolve repo root
    repo_root = args.repo_root or _resolve_repo_root()

    # Resolve default paths
    out_path: str = args.out
    err_path: str = args.err
    text_out_path: str = args.text_out or (out_path + ".text.txt")
    result_out_path: str = args.result_out or (out_path + ".result.json")
    ledger_path: str = args.ledger or os.path.join(repo_root, "output", "delegation-log.jsonl")

    # Resolve tags
    tags = _resolve_tags(args.tags_raw)

    # ---- Read inputs (T3: missing files → empty string) ----
    out_text = _read_file(out_path)
    err_text = _read_file(err_path)

    # ---- Resolve exit code ----
    exit_code: int | None
    if args.exit is not None:
        exit_code = args.exit
    else:
        # args.exit_file is guaranteed non-None because mutually exclusive
        exit_file_text = _read_file(args.exit_file)  # type: ignore[arg-type]
        exit_code = parse_exit_file(exit_file_text)

    # ---- Compute derived values ----
    fallback = detect_fallback(err_text)
    text = extract_text(out_text)
    marker_ok = assert_markers(text, args.markers)
    truncated = detect_truncated_stream(out_text)
    verdict = extract_verdict(text, args.verdict_regex)
    status = classify_status(exit_code, fallback, text, marker_ok, truncated=truncated)
    duration_s = best_effort_duration(out_text)

    # ---- Write extracted text ----
    try:
        with open(text_out_path, "w", encoding="utf-8") as fh:
            fh.write(text or "")
    except OSError:
        # Degrade gracefully (T3): warn to stderr, continue
        print(f"WARNING: could not write text-out to {text_out_path}", file=sys.stderr)

    # ---- Write result JSON ----
    result = {
        "phase": args.phase,
        "status": status,
        "exit": exit_code,
        "fallback": fallback,
        "text_present": text is not None,
        "marker_ok": marker_ok,
        "truncated": truncated,
        "verdict": verdict,
        "duration_s": duration_s,
        "text_path": text_out_path,
        "out": out_path,
        "err": err_path,
    }
    try:
        with open(result_out_path, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
    except OSError:
        print(f"WARNING: could not write result-out to {result_out_path}", file=sys.stderr)

    # ---- Build and append ledger record ----
    now_ts = datetime.now(timezone.utc).isoformat()
    record = build_ledger_record(
        ts=now_ts,
        phase=args.phase,
        agent=args.agent,
        model=args.model,
        change=args.change,
        exit_code=exit_code,
        fallback=fallback,
        status=status,
        marker_ok=marker_ok,
        verdict=verdict,
        retry=args.retry,
        duration_s=duration_s,
        tags=tags,
    )
    ledger_parent = os.path.dirname(ledger_path)
    try:
        os.makedirs(ledger_parent, exist_ok=True)
    except OSError:
        print(f"WARNING: could not create ledger parent {ledger_parent}", file=sys.stderr)
    try:
        with open(ledger_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, sort_keys=True) + "\n")
            fh.flush()
    except OSError:
        print(f"WARNING: could not append to ledger {ledger_path}", file=sys.stderr)

    # ---- Print status line ----
    fallback_label = "yes" if fallback else "no"
    marker_ok_label = "yes" if marker_ok else "no"
    verdict_label = verdict or "-"
    print(
        f"DELEGATE_RESULT: phase={args.phase} status={status} exit={exit_code} "
        f"fallback={fallback_label} marker_ok={marker_ok_label} "
        f"verdict={verdict_label}",
    )
    if not args.quiet:
        print(text if text else "<no text extracted>")

    return 0 if status == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
