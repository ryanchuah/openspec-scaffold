#!/usr/bin/env python3
"""freeze_check.py — deterministic freeze determination from a review text.

CLI::

    freeze_check.py --artifact {proposal,design,tasks} --review <path>

Parses the last whole-line-anchored ``VERDICT: PASS|NEEDS REVISION`` and,
for ``proposal``, the last ``PREMISE: AGREE|DISSENT``. Optional ``**``
markdown emphasis around the label and/or the value is tolerated (e.g.
``**VERDICT:** PASS``, ``**VERDICT: PASS**``, ``VERDICT: **PASS**``) — the
line remains otherwise strictly anchored, so a token quoted mid-prose is
still not accepted. Prints exactly one machine-distinguishable line and
exits accordingly:

- ``FREEZE: READY``  (exit 0)
- ``FREEZE: BLOCKED — needs-revision``  (exit 1)
- ``FREEZE: BLOCKED — premise-dissent``  (exit 1)
- ``FREEZE: BLOCKED — missing-verdict``  (exit 1)
- Bad args / unreadable file => exit 3 + stderr.

Design D3 — single source of truth for freeze policy, decoupled from
reviewer judgment. stdlib-only, zero dependencies.
"""

from __future__ import annotations

import argparse
import re
import sys


def _last_anchored(text: str, pattern: str) -> str | None:
    """Return the content of the last whole-line match of *pattern* in
    *text*, or ``None`` if no match. The pattern is matched with
    ``re.MULTILINE`` and ``re.fullmatch`` semantics per line (anchored
    to start/end of line)."""
    matches = re.findall(pattern, text, re.MULTILINE)
    if not matches:
        return None
    return matches[-1]


def freeze_check(artifact: str, review_text: str) -> tuple[str, int]:
    """Determine freeze status from the review *text* for *artifact* type.

    Returns ``(output_line, exit_code)``.
    """
    verdict = _last_anchored(
        review_text, r"^\s*\*{0,2}VERDICT:\*{0,2}\s*\*{0,2}(PASS|NEEDS REVISION)\*{0,2}\s*$"
    )

    if verdict is None:
        return "FREEZE: BLOCKED — missing-verdict", 1

    if verdict == "NEEDS REVISION":
        return "FREEZE: BLOCKED — needs-revision", 1

    # verdict is PASS
    if artifact == "proposal":
        premise = _last_anchored(
            review_text, r"^\s*\*{0,2}PREMISE:\*{0,2}\s*\*{0,2}(AGREE|DISSENT)\*{0,2}\s*$"
        )
        if premise is None:
            return "FREEZE: BLOCKED — missing-verdict", 1
        if premise == "DISSENT":
            return "FREEZE: BLOCKED — premise-dissent", 1
        # PASS + AGREE
        return "FREEZE: READY", 0

    # design or tasks: PASS is sufficient
    return "FREEZE: READY", 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Determine freeze status from a review artifact.")
    parser.add_argument(
        "--artifact",
        required=True,
        choices=["proposal", "design", "tasks"],
        help="Artifact type being reviewed.",
    )
    parser.add_argument(
        "--review",
        required=True,
        help="Path to the extracted review text file.",
    )

    try:
        args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    except SystemExit:
        # argparse calls sys.exit(2) on bad args — convert to our INFRA exit (3).
        return 3

    try:
        with open(args.review, encoding="utf-8") as f:
            review_text = f.read()
    except OSError as exc:
        print(f"freeze_check: INFRA-FAIL — cannot read {args.review}: {exc}", file=sys.stderr)
        return 3

    line, code = freeze_check(args.artifact, review_text)
    print(line)
    return code


if __name__ == "__main__":
    sys.exit(main())
