#!/usr/bin/env python3
"""apply_delta_spec.py — deterministic promoter for ADDED/REMOVED/RENAMED spec deltas.

Parses change-dir delta specs (``<change-dir>/specs/<cap>/spec.md``), plans
operations against the main specs (``<specs-root>/<cap>/spec.md``), and writes
all-or-nothing: any anomaly → write nothing, exit 2; clean plan → write each
touched main spec atomically, exit 0.

Operation semantics (D4 truth table):

| Operation | Main-spec state | Action |
|-----------|----------------|--------|
| ADDED X | X absent | apply — append block under ## Requirements |
| ADDED X | X present, body norm-equal | skip (already added) |
| ADDED X | X present, body differs | ANOMALY |
| REMOVED X | X present | apply — delete the block |
| REMOVED X | X absent | skip (target-absent) |
| RENAMED X→Y | X present, Y absent | apply — rewrite header X→Y |
| RENAMED X→Y | X absent, Y present | skip (already-renamed) |
| RENAMED X→Y | X absent, Y absent | ANOMALY (target does not exist) |
| RENAMED X→Y | X present, Y present | ANOMALY (ambiguous) |
| MODIFIED X | (any) | defer — report, never applied |

Exit codes: 0 = clean plan (applied or nothing-to-do); 2 = ≥1 anomaly
(nothing written). ``--dry-run`` uses the same exit code without writing.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import IO

# ---------------------------------------------------------------------------
# Parser grammar — own copies of the three checks.py regex patterns (D2)
# + a separate RENAMED list-item parser (D3).
# ---------------------------------------------------------------------------

_SECTION_HEADER_RE = re.compile(r"^## (ADDED|MODIFIED|REMOVED|RENAMED) Requirements$")
_REQUIREMENT_HEADER_RE = re.compile(r"^### Requirement:\s*(.*)")
_SCENARIO_HEADER_RE = re.compile(r"^#### Scenario:")

# RENAMED list-item format: "- FROM: `### Requirement: <name>`"
# "- TO: `### Requirement: <name>`"
_RENAMED_FROM_RE = re.compile(r"^-\s+FROM:\s+`(### Requirement:\s*(.*))`$")
_RENAMED_TO_RE = re.compile(r"^-\s+TO:\s+`(### Requirement:\s*(.*))`$")


# ---------------------------------------------------------------------------
# Requirement block representation
# ---------------------------------------------------------------------------


class RequirementBlock:
    """A single requirement block with its header line, scenarios, and raw lines."""

    __slots__ = ("name", "header", "lines")

    def __init__(self, name: str, header: str, lines: list[str]) -> None:
        self.name = name
        self.header = header  # the "### Requirement: ..." line
        self.lines = lines  # all lines including the header

    @property
    def body(self) -> str:
        """The full block content minus leading/trailing blank lines,
        per-line trailing whitespace stripped, as a single string for comparison."""
        # Strip trailing whitespace per line, then strip leading/trailing blank lines
        stripped_lines = [line.rstrip() for line in self.lines]
        while stripped_lines and stripped_lines[0] == "":
            stripped_lines.pop(0)
        while stripped_lines and stripped_lines[-1] == "":
            stripped_lines.pop()
        return "\n".join(stripped_lines)


# ---------------------------------------------------------------------------
# Main-spec parsing
# ---------------------------------------------------------------------------


class MainSpec:
    """Parsed main spec: preamble + requirement blocks by name + postamble."""

    __slots__ = (
        "preamble",
        "requirements_by_name",
        "requirement_order",
        "has_requirements_header",
        "postamble",
    )

    def __init__(self) -> None:
        self.preamble: list[str] = []  # lines before first `## ` that is Requirements
        self.requirements_by_name: dict[str, RequirementBlock] = {}
        self.requirement_order: list[str] = []
        self.has_requirements_header: bool = False
        self.postamble: list[str] = []  # lines after ## Requirements (DEFECT 3)


def parse_main_spec(path: Path) -> MainSpec | None:
    """Parse a main spec file into a MainSpec object.

    Returns None if the file does not exist (caller handles per D9).
    """
    if not path.exists():
        return None
    lines = path.read_text(encoding="utf-8").splitlines()
    spec = MainSpec()
    # Split lines into preamble, then requirement blocks.
    # The preamble runs from line 0 until we hit `## Requirements` or
    # the first `### Requirement:` (block before any section header).
    # After `## Requirements` (or the first `### Requirement:`), subsequent
    # `### Requirement:` blocks are parsed.

    # State: "preamble" | "in_requirements" | "in_block" | "postamble"
    state = "preamble"
    current_block_lines: list[str] | None = None
    current_name: str | None = None
    current_header: str | None = None

    for line in lines:
        if state == "preamble":
            section_m = _SECTION_HEADER_RE.match(line)
            if section_m:
                section_name = section_m.group(1)
                if (
                    section_name == "MODIFIED"
                    or section_name == "ADDED"
                    or section_name == "REMOVED"
                    or section_name == "RENAMED"
                ):
                    # This would be a delta section in a main spec — shouldn't happen,
                    # but treat it as end of preamble gracefully.
                    spec.preamble.append(line)
                    continue
            if line.strip() == "## Requirements":
                spec.has_requirements_header = True
                state = "in_requirements"
                continue
            req_m = _REQUIREMENT_HEADER_RE.match(line)
            if req_m:
                # A requirement block before ## Requirements header — treat as
                # implicit requirements section
                spec.has_requirements_header = True
                spec.preamble.append(line)
                state = "in_requirements"
                continue
            spec.preamble.append(line)
        elif state == "in_requirements":
            req_m = _REQUIREMENT_HEADER_RE.match(line)
            if req_m:
                if (
                    current_block_lines is not None
                    and current_name is not None
                    and current_header is not None
                ):
                    block = RequirementBlock(current_name, current_header, current_block_lines)
                    spec.requirements_by_name[current_name] = block
                    spec.requirement_order.append(current_name)
                current_name = req_m.group(1).strip()
                current_header = line
                current_block_lines = [line]
                state = "in_block"
            elif line.strip() == "## Requirements":
                # Duplicate header — just keep going
                pass
            elif line.startswith("## "):
                # A new ## section after the requirements section
                # goes into the postamble (DEFECT 3)
                spec.postamble.append(line)
                state = "postamble"
            else:
                # Lines before first requirement block (blank lines, comments)
                # go into preamble
                spec.preamble.append(line)
        elif state == "in_block":
            # Check for boundary: next `### Requirement:` or next `## ` header
            if _REQUIREMENT_HEADER_RE.match(line):
                # Save current block
                if (
                    current_block_lines is not None
                    and current_name is not None
                    and current_header is not None
                ):
                    block = RequirementBlock(current_name, current_header, current_block_lines)
                    spec.requirements_by_name[current_name] = block
                    spec.requirement_order.append(current_name)
                current_name = _REQUIREMENT_HEADER_RE.match(line).group(1).strip()
                current_header = line
                current_block_lines = [line]
            elif line.startswith("## "):
                # End of requirements — save current block and add this line to
                # postamble (DEFECT 3)
                if (
                    current_block_lines is not None
                    and current_name is not None
                    and current_header is not None
                ):
                    block = RequirementBlock(current_name, current_header, current_block_lines)
                    spec.requirements_by_name[current_name] = block
                    spec.requirement_order.append(current_name)
                current_block_lines = None
                current_name = None
                current_header = None
                spec.postamble.append(line)
                state = "postamble"
            else:
                if current_block_lines is not None:
                    current_block_lines.append(line)
        elif state == "postamble":
            spec.postamble.append(line)

    # Flush last block
    if current_block_lines is not None and current_name is not None and current_header is not None:
        block = RequirementBlock(current_name, current_header, current_block_lines)
        spec.requirements_by_name[current_name] = block
        spec.requirement_order.append(current_name)

    return spec


# ---------------------------------------------------------------------------
# Delta parsing
# ---------------------------------------------------------------------------


class DeltaOp:
    """A single delta operation."""

    __slots__ = ("op_type", "name", "new_name", "block_lines", "from_header", "to_header")

    def __init__(
        self,
        op_type: str,
        name: str,
        new_name: str | None = None,
        block_lines: list[str] | None = None,
        from_header: str | None = None,
        to_header: str | None = None,
    ) -> None:
        self.op_type = op_type  # "ADDED" | "MODIFIED" | "REMOVED" | "RENAMED"
        self.name = name
        self.new_name = new_name
        self.block_lines = block_lines
        self.from_header = from_header  # full "### Requirement: Old" line
        self.to_header = to_header  # full "### Requirement: New" line


def parse_delta(path: Path) -> list[DeltaOp]:
    """Parse a delta spec file into a list of DeltaOps.

    Returns an empty list for empty/no-op deltas (never returns None).
    """
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    ops: list[DeltaOp] = []

    # State machine: we iterate through lines tracking the current section type
    section_type = None  # None | "ADDED" | "MODIFIED" | "REMOVED" | "RENAMED"
    current_block_lines: list[str] | None = None
    current_name: str | None = None

    # For RENAMED pair tracking
    rename_from: str | None = None
    rename_from_header: str | None = None
    rename_to: str | None = None
    rename_to_header: str | None = None

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for section header
        section_m = _SECTION_HEADER_RE.match(line)
        if section_m:
            # Flush any in-progress block
            if section_type == "RENAMED":
                # Flush pending rename pair
                if rename_from is not None and rename_to is not None:
                    ops.append(
                        DeltaOp(
                            "RENAMED",
                            name=rename_from,
                            new_name=rename_to,
                            from_header=rename_from_header,
                            to_header=rename_to_header,
                        )
                    )
                elif rename_from is not None or rename_to is not None:
                    # Incomplete rename pair — skip; the archive skill validates
                    pass
                rename_from = None
                rename_from_header = None
                rename_to = None
                rename_to_header = None
            elif current_block_lines is not None and current_name is not None:
                block = list(current_block_lines)
                ops.append(DeltaOp(section_type, name=current_name, block_lines=block))
                current_block_lines = None
                current_name = None

            section_type = section_m.group(1)
            i += 1
            continue

        if section_type is None:
            i += 1
            continue

        if section_type == "RENAMED":
            from_m = _RENAMED_FROM_RE.match(line)
            to_m = _RENAMED_TO_RE.match(line)
            if from_m:
                # Flush pending pair
                if rename_from is not None and rename_to is not None:
                    ops.append(
                        DeltaOp(
                            "RENAMED",
                            name=rename_from,
                            new_name=rename_to,
                            from_header=rename_from_header,
                            to_header=rename_to_header,
                        )
                    )
                    rename_from = None
                    rename_from_header = None
                    rename_to = None
                    rename_to_header = None
                rename_from = from_m.group(2).strip()
                rename_from_header = from_m.group(1)
            elif to_m:
                rename_to = to_m.group(2).strip()
                rename_to_header = to_m.group(1)
                # If we have a complete pair, add it immediately
                if rename_from is not None:
                    ops.append(
                        DeltaOp(
                            "RENAMED",
                            name=rename_from,
                            new_name=rename_to,
                            from_header=rename_from_header,
                            to_header=rename_to_header,
                        )
                    )
                    rename_from = None
                    rename_from_header = None
                    rename_to = None
                    rename_to_header = None
            i += 1
            continue

        # ADDED / MODIFIED / REMOVED
        req_m = _REQUIREMENT_HEADER_RE.match(line)
        if req_m:
            # Save previous block
            if current_block_lines is not None and current_name is not None:
                block = list(current_block_lines)
                ops.append(DeltaOp(section_type, name=current_name, block_lines=block))

            current_name = req_m.group(1).strip()
            current_block_lines = [line]
            i += 1
            continue

        # Inside a requirement block
        if current_block_lines is not None:
            current_block_lines.append(line)

        i += 1

    # Flush at EOF
    if section_type == "RENAMED":
        if rename_from is not None and rename_to is not None:
            ops.append(
                DeltaOp(
                    "RENAMED",
                    name=rename_from,
                    new_name=rename_to,
                    from_header=rename_from_header,
                    to_header=rename_to_header,
                )
            )
    elif current_block_lines is not None and current_name is not None and section_type is not None:
        block = list(current_block_lines)
        ops.append(DeltaOp(section_type, name=current_name, block_lines=block))

    return ops


# ---------------------------------------------------------------------------
# Planner — D4 truth table
# ---------------------------------------------------------------------------


def _normalize_body(block: RequirementBlock) -> str:
    """Normalize a requirement body for comparison: strip trailing whitespace
    per line, then strip leading/trailing blank lines."""
    lines = [line.rstrip() for line in block.lines]
    while lines and lines[0] == "":
        lines.pop(0)
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


class PerSpecPlan:
    """Plan for a single capability spec."""

    __slots__ = (
        "capability",
        "main_spec_path",
        "is_created",
        "applied_added",
        "applied_removed",
        "applied_renamed",
        "skipped",
        "deferred_modified",
        "anomalies",
        "post_preamble",
        "post_requirements",
        "post_postamble",
    )

    def __init__(self, capability: str, main_spec_path: Path) -> None:
        self.capability = capability
        self.main_spec_path = main_spec_path
        self.is_created = False
        self.applied_added: list[str] = []
        self.applied_removed: list[str] = []
        self.applied_renamed: list[tuple[str, str]] = []
        self.skipped: list[dict] = []
        self.deferred_modified: list[str] = []
        self.anomalies: list[dict] = []
        # Computed post-promotion content
        self.post_preamble: list[str] = []
        self.post_requirements: list[list[str]] = []  # list of requirement blocks (lines)
        self.post_postamble: list[str] = []  # trailing sections after requirements (DEFECT 3)


def plan_spec(
    capability: str,
    delta_ops: list[DeltaOp],
    main_spec: MainSpec | None,
    main_spec_path: Path,
) -> PerSpecPlan:
    """Plan operations for one capability spec.

    Returns a PerSpecPlan with the plan. If any anomaly is found, the plan
    carries it (the caller checks and halts).
    """
    plan = PerSpecPlan(capability, main_spec_path)

    if main_spec is None:
        # No main spec exists — only ADDED is valid
        plan.is_created = True
        has_anomaly = False
        # In-memory tracking for self-collision detection (DEFECT 1)
        added_seen: dict[str, list[str]] = {}
        for op in delta_ops:
            if op.op_type == "ADDED":
                if op.name in added_seen:
                    # Self-collision within the delta
                    existing_lines = added_seen[op.name]
                    delta_block = RequirementBlock(
                        op.name, f"### Requirement: {op.name}", op.block_lines or []
                    )
                    existing_block = RequirementBlock(
                        op.name, f"### Requirement: {op.name}", existing_lines
                    )
                    if _normalize_body(delta_block) == _normalize_body(existing_block):
                        plan.skipped.append(
                            {
                                "op": "ADDED",
                                "name": op.name,
                                "reason": "body-equal",
                            }
                        )
                    else:
                        plan.anomalies.append(
                            {
                                "op": "ADDED",
                                "name": op.name,
                                "reason": "present with different body",
                            }
                        )
                        has_anomaly = True
                else:
                    plan.applied_added.append(op.name)
                    if op.block_lines is not None:
                        added_seen[op.name] = list(op.block_lines)
            elif op.op_type == "MODIFIED":
                plan.deferred_modified.append(op.name)
            elif op.op_type == "REMOVED":
                plan.anomalies.append(
                    {
                        "op": "REMOVED",
                        "name": op.name,
                        "reason": "target capability has no main spec file",
                    }
                )
                has_anomaly = True
            elif op.op_type == "RENAMED":
                plan.anomalies.append(
                    {
                        "op": "RENAMED",
                        "name": f"{op.name}->{op.new_name}",
                        "reason": "target capability has no main spec file",
                    }
                )
                has_anomaly = True

        if not has_anomaly:
            plan.post_preamble = ["## Purpose", "", "<!-- TODO: document purpose -->", ""]
            plan.post_requirements = []
            for name in plan.applied_added:
                lines = added_seen[name]
                plan.post_requirements.append(list(lines))
        return plan

    # Build in-memory state from the main spec
    current_requirements: dict[str, RequirementBlock] = {}
    current_order: list[str] = []
    for name in main_spec.requirement_order:
        block = main_spec.requirements_by_name[name]
        current_requirements[name] = block
        current_order.append(name)

    for op in delta_ops:
        if op.op_type == "ADDED":
            if op.name in current_requirements:
                existing = current_requirements[op.name]
                if op.block_lines:
                    delta_block = RequirementBlock(
                        op.name, f"### Requirement: {op.name}", op.block_lines
                    )
                    if _normalize_body(delta_block) == _normalize_body(existing):
                        plan.skipped.append(
                            {
                                "op": "ADDED",
                                "name": op.name,
                                "reason": "body-equal",
                            }
                        )
                    else:
                        plan.anomalies.append(
                            {
                                "op": "ADDED",
                                "name": op.name,
                                "reason": "present with different body",
                            }
                        )
            else:
                # Apply — add to current state
                block = RequirementBlock(
                    op.name, f"### Requirement: {op.name}", op.block_lines or []
                )
                current_requirements[op.name] = block
                current_order.append(op.name)
                plan.applied_added.append(op.name)

        elif op.op_type == "REMOVED":
            if op.name not in current_requirements:
                plan.skipped.append(
                    {
                        "op": "REMOVED",
                        "name": op.name,
                        "reason": "target-absent",
                    }
                )
            else:
                del current_requirements[op.name]
                current_order = [n for n in current_order if n != op.name]
                plan.applied_removed.append(op.name)

        elif op.op_type == "RENAMED":
            from_name = op.name
            to_name = op.new_name or ""
            from_present = from_name in current_requirements
            to_present = to_name in current_requirements

            if from_present and not to_present:
                # Apply rename
                block = current_requirements.pop(from_name)
                current_order = [n if n != from_name else to_name for n in current_order]
                # Rewrite the header line
                new_header = f"### Requirement: {to_name}"
                new_lines = [new_header] + block.lines[1:]
                renamed_block = RequirementBlock(to_name, new_header, new_lines)
                current_requirements[to_name] = renamed_block
                plan.applied_renamed.append((from_name, to_name))
            elif not from_present and to_present:
                plan.skipped.append(
                    {
                        "op": "RENAMED",
                        "name": f"{from_name}->{to_name}",
                        "reason": "already-renamed",
                    }
                )
            elif not from_present and not to_present:
                plan.anomalies.append(
                    {
                        "op": "RENAMED",
                        "name": f"{from_name}->{to_name}",
                        "reason": "rename source does not exist in main spec",
                    }
                )
            else:  # both present
                plan.anomalies.append(
                    {
                        "op": "RENAMED",
                        "name": f"{from_name}->{to_name}",
                        "reason": "rename target already exists in main spec (ambiguous)",
                    }
                )

        elif op.op_type == "MODIFIED":
            plan.deferred_modified.append(op.name)

    # Build post-promotion content
    plan.post_preamble = list(main_spec.preamble)
    plan.post_requirements = []
    plan.post_postamble = list(main_spec.postamble)
    for name in current_order:
        block = current_requirements[name]
        plan.post_requirements.append(list(block.lines))

    return plan


# ---------------------------------------------------------------------------
# Writer — all-or-nothing (D6)
# ---------------------------------------------------------------------------


def write_spec(plan: PerSpecPlan, specs_root: Path) -> None:
    """Write a single spec's post-promotion content atomically.

    Spacing invariants (DEFECT 2, DEFECT 3):
    - Strip trailing blank lines from preamble, each requirement block,
      and postamble.
    - Exactly one blank line between structural elements.
    - Postamble (trailing ``## `` sections) emitted AFTER requirements.
    - No ``\\n\\n\\n`` runs in the output.
    """
    cap_dir = specs_root / plan.capability
    cap_dir.mkdir(parents=True, exist_ok=True)
    target = cap_dir / "spec.md"

    out_lines: list[str] = []

    # -- Preamble -----------------------------------------------------------
    preamble = list(plan.post_preamble)
    while preamble and preamble[-1] == "":
        preamble.pop()
    out_lines.extend(preamble)

    has_req_in_preamble = any(line.strip() == "## Requirements" for line in preamble)
    has_requirements = bool(plan.post_requirements)
    has_postamble = bool(plan.post_postamble)

    # -- Requirements header ------------------------------------------------
    if has_requirements:
        if preamble:
            out_lines.append("")
        if not has_req_in_preamble:
            out_lines.append("## Requirements")
            out_lines.append("")

    # -- Requirement blocks -------------------------------------------------
    for idx, block_lines in enumerate(plan.post_requirements):
        cleaned = list(block_lines)
        while cleaned and cleaned[-1] == "":
            cleaned.pop()
        if idx > 0:
            out_lines.append("")
        out_lines.extend(cleaned)

    # -- Postamble (trailing sections) --------------------------------------
    if has_postamble:
        if out_lines:
            out_lines.append("")
        postamble = list(plan.post_postamble)
        while postamble and postamble[-1] == "":
            postamble.pop()
        out_lines.extend(postamble)

    content = "\n".join(out_lines)
    if content:
        content += "\n"

    # Atomic write: temp file in same dir + os.replace
    fd, tmp_path = tempfile.mkstemp(
        dir=str(cap_dir),
        prefix=".tmp_",
        suffix=".spec.md",
    )
    try:
        os.write(fd, content.encode("utf-8"))
        os.close(fd)
        os.replace(tmp_path, str(target))
    except BaseException:
        # Clean up temp file on error
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# Report (D11)
# ---------------------------------------------------------------------------


class ChangePlan:
    """Plan for an entire change (all capabilities)."""

    __slots__ = ("spec_plans",)

    def __init__(self, spec_plans: list[PerSpecPlan]) -> None:
        self.spec_plans = spec_plans

    @property
    def has_anomaly(self) -> bool:
        return any(len(p.anomalies) > 0 for p in self.spec_plans)

    def build_report(self) -> dict:
        """Build the D11 JSON report."""
        specs: list[dict] = []
        for p in self.spec_plans:
            specs.append(
                {
                    "capability": p.capability,
                    "main_spec": str(p.main_spec_path) if p.main_spec_path else "",
                    "created": p.is_created,
                    "applied": {
                        "added": list(p.applied_added),
                        "removed": list(p.applied_removed),
                        "renamed": [[a, b] for a, b in p.applied_renamed],
                    },
                    "skipped": list(p.skipped),
                    "deferred_modified": list(p.deferred_modified),
                    "anomalies": list(p.anomalies),
                }
            )
        status = "anomaly" if self.has_anomaly else "ok"
        return {"status": status, "specs": specs}

    def print_human_report(self, file: IO[str] | None = None) -> None:
        """Print a human-readable report (anomalies first)."""
        if file is None:
            file = sys.stdout
        has_any_work = False
        for p in self.spec_plans:
            if p.anomalies:
                print(f"  Capability: {p.capability}", file=file)
                for a in p.anomalies:
                    print(f"    ANOMALY: {a['op']} {a['name']} — {a['reason']}", file=file)
                print(file=file)
                has_any_work = True

        if self.has_anomaly:
            print("--- ANOMALIES FOUND — no changes written ---", file=file)
            print(file=file)
            return

        for p in self.spec_plans:
            if p.is_created:
                print(f"  Capability: {p.capability} (created)", file=file)
            else:
                print(f"  Capability: {p.capability}", file=file)

            if p.applied_added:
                print(f"    APPLIED — added: {', '.join(p.applied_added)}", file=file)
                has_any_work = True
            if p.applied_removed:
                print(f"    APPLIED — removed: {', '.join(p.applied_removed)}", file=file)
                has_any_work = True
            if p.applied_renamed:
                items = [f"{a}→{b}" for a, b in p.applied_renamed]
                print(f"    APPLIED — renamed: {', '.join(items)}", file=file)
                has_any_work = True
            if p.skipped:
                for s in p.skipped:
                    print(f"    SKIPPED: {s['op']} {s['name']} — {s['reason']}", file=file)
            if p.deferred_modified:
                print(f"    DEFERRED (LLM merge): {', '.join(p.deferred_modified)}", file=file)
                if not has_any_work:
                    has_any_work = True

        if not has_any_work:
            print("  (no operations to apply)", file=file)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic promoter for ADDED/REMOVED/RENAMED spec deltas.",
        epilog=(
            "Operation semantics:\n"
            "  ADDED (absent)  → apply        ADDED (present, eq)  → skip\n"
            "  ADDED (present, diff) → ANOMALY\n"
            "  REMOVED (present) → apply      REMOVED (absent) → skip\n"
            "  RENAMED (from,not to) → apply  RENAMED (not from,to) → skip\n"
            "  RENAMED (neither|both) → ANOMALY\n"
            "  MODIFIED (any) → deferred (LLM merge)\n\n"
            "Any anomaly across any spec → write nothing, exit 2."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--change-dir",
        required=True,
        help="Path to the change directory containing specs/<cap>/spec.md",
    )
    parser.add_argument(
        "--specs-root",
        default="openspec/specs",
        help="Root directory for main specs (default: openspec/specs)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan and report without writing any changes",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit report as JSON instead of human-readable",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    change_dir = Path(args.change_dir)
    specs_root = Path(args.specs_root)
    dry_run = args.dry_run
    use_json = args.json

    if not change_dir.is_dir():
        print(f"apply_delta_spec: change directory not found: {change_dir}", file=sys.stderr)
        return 2

    # Discover delta specs
    delta_dir = change_dir / "specs"
    if not delta_dir.is_dir():
        # No specs at all — clean no-op
        plan = ChangePlan([])
        if use_json:
            print(json.dumps(plan.build_report(), indent=2))
        else:
            plan.print_human_report()
        return 0

    spec_plans: list[PerSpecPlan] = []

    for cap_dir_entry in sorted(delta_dir.iterdir()):
        if not cap_dir_entry.is_dir():
            continue
        capability = cap_dir_entry.name
        delta_path = cap_dir_entry / "spec.md"
        if not delta_path.exists():
            continue

        delta_ops = parse_delta(delta_path)
        if not delta_ops:
            continue

        main_spec_path = specs_root / capability / "spec.md"
        main_spec = parse_main_spec(main_spec_path)

        p = plan_spec(capability, delta_ops, main_spec, main_spec_path)
        spec_plans.append(p)

    # Also check for capabilities in the main specs that have no delta
    # (they are fine — just no changes)

    change_plan = ChangePlan(spec_plans)
    report = change_plan.build_report()

    if use_json:
        print(json.dumps(report, indent=2))
    else:
        change_plan.print_human_report()

    if change_plan.has_anomaly:
        return 2

    # Write (unless dry-run)
    if not dry_run:
        for p in spec_plans:
            if not p.anomalies and (
                p.applied_added or p.applied_removed or p.applied_renamed or p.is_created
            ):
                write_spec(p, specs_root)

    return 0


if __name__ == "__main__":
    sys.exit(main())
