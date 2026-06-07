#!/usr/bin/env python3
"""Harden the OpenSpec-generated /opsx command + skill files with project rules.

Run this AFTER `openspec init` and after every `openspec update` (both regenerate the
command/skill files from the stock OpenSpec templates, overwriting any edits). Idempotent:
re-running is safe and skips files already hardened.

The stock OpenSpec `verify` is a document/spec-mapping checklist, the stock `apply`
implements inline, and the stock `propose` batch-creates all artifacts in one pass. This
script injects three blocks so the generated commands match the behaviour required by
AGENTS.md and openspec/config.yaml:

  - propose: a sequential-creation mandate — finalize each artifact before starting the
    next; self-review guidance — rigorous defect-hunting before finalizing (no separate
    reviewer on Claude); concrete-fix guidance — decisions must be specific choices, not
    paraphrases.
  - verify:  a MANDATORY behavioral-review preamble — read diffs, re-run the full suite,
    eyeball real output, re-delegate fixes to a fresh executor.
  - apply:   a delegation override — delegate to the apply-executor; do not implement inline.

Compatibility: built and tested against OpenSpec 1.4.1. This script depends on the layout
of the generated files — the `**Input**` anchor line and the
`.claude/commands/opsx/{propose,apply,verify}.md` +
`.claude/skills/openspec-{propose,apply,verify}-change/SKILL.md` paths. If a newer
OpenSpec changes those templates, the script may no-op or mis-place the block; re-check
the anchors/paths and bump TESTED_OPENSPEC_VERSION below. It warns at runtime if your
installed `openspec --version` differs.

Usage:  python scripts/harden_opsx.py [repo-root]   (default: current directory)
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

# The generated /opsx template layout this script targets. Bump only after re-verifying
# the anchors/paths against the new OpenSpec output.
TESTED_OPENSPEC_VERSION = "1.4.1"

VERIFY_MARKER = "MANDATORY — behavioral review"
APPLY_MARKER = "MANDATORY — delegation override"
PROPOSE_MARKER = "MANDATORY — sequential artifact creation"

VERIFY_BLOCK = """\
> **MANDATORY — behavioral review. This is the core of verify, not optional, and runs BEFORE the artifact/spec checklist below.**
> Per `AGENTS.md` and `openspec/config.yaml`, verifying a change is the orchestrator's own review of the apply-executor's work — a substantive behavioral review, not a checklist rubber-stamp. Before generating the verification report, the main agent MUST itself do all of the following — do not delegate this, and do not trust the executor's completion summary:
>
> 1. **Read the actual diffs and changed files.** Run `git diff` (and open the files) for everything the executor touched. Trust the code, not the summary.
> 2. **Re-run the FULL test suite yourself:** `.venv/bin/python -m pytest -q`. It must be green (pre-existing skips OK). A green exit is **necessary but not sufficient.**
> 3. **Eyeball the real output the code produces.** Render a concrete sample of what the change actually generates — the actual digest rows, the prompt sent to the LLM/relevance gate, the terms/spans extracted, the DB rows selected — not just that tests pass. Run the relevant project command or a `scripts/_*_oneoff.py` probe against the live DB and inspect a real sample. Bugs that logic-reading misses are often visible the instant you render real output.
> 4. **If the change touches an external API / network service, RUN ITS LIVE SMOKE yourself against the real endpoint.** The mock-based suite is *structurally blind* to whether the mocks match reality — a fully green suite can encode a **wrong** API contract (wrong sort semantics, wrong field types, wrong error codes) and so pass while the real integration collects nothing. This has already happened on real projects: a collector shipped with `order=volume` (string-sorts) and a 500-ing backfill, with mocks that encoded the *idealized* API, so 600+ tests passed green over a non-functional collector. Therefore: run the change's opt-in live test (e.g. `LIVE_TESTS=1 .venv/bin/python -m pytest tests/test_<x>.py -k live -v`) and inspect a real response. **A *skipped* live smoke is NOT a *passed* one.** If an external-API change has no live smoke at all, that is itself a **CRITICAL** gap — require one to be added before archive.
> 5. **On any defect:** diagnose and scope it yourself (reproduce it, run DB queries, read diffs), then **re-delegate the fix to a FRESH apply-executor** with a self-contained fix-spec. Do **not** hand-fix beyond a trivial typo / comment / one-line rename — if you would write more than ~2 lines of implementation, stop and re-delegate. Then re-verify from step 1.
>
> Only after this behavioral review passes, proceed to the artifact/spec mapping checks below and emit the report. If the behavioral review fails, the verdict is **NEEDS REVISION** regardless of the checklist.
"""

PROPOSE_BLOCK = """\
> **MANDATORY — sequential artifact creation. Read before writing any artifact.**
> Create artifacts in dependency order, finalizing each before it is used as context for the next:
> - proposal.md (what & why) → complete & finalize → use as context for design.md
> - design.md (how) → complete & finalize → use as context for tasks.md
> - tasks.md (implementation steps) → complete & finalize → proceed to apply
>
> **Do NOT batch-create all artifacts.** Downstream artifacts written before upstream ones are finalized will reference stale decisions, causing implementation to diverge from intent. Complete each artifact fully before starting the next.
>
> **Self-review each artifact before finalizing it.** Claude Code has no separate reviewer — you are the sole reviewer. Be genuinely rigorous, not a rubber-stamp:
> - Re-read the artifact you just wrote. Check every claim against the dependencies, template, and context.
> - Verify every scope boundary is explicit, every decision resolves an ambiguity, and every choice is concrete and implementable.
> - Actively hunt for defects: gaps in edge cases, contradictions with upstream artifacts, vague or untestable success criteria, design choices that silently commit to unvalidated assumptions.
> - Fix any issues you find before proceeding to the next artifact.
>
> **Decisions must be concrete and implementable** — not paraphrases of the problem. E.g., instead of "return value semantics differ" (vague), write: "returns 0 — zero Document rows inserted" (concrete). For every gap or ambiguity, close it with a specific choice.
"""

APPLY_BLOCK = """\
> **MANDATORY — delegation override. Read before the implementation step; it changes who implements.**
> Per `AGENTS.md` and `openspec/config.yaml` `rules.tasks`, the primary agent does **not** implement tasks inline. Delegate implementation to the **apply-executor**:
> - **Claude Code:** spawn a **Sonnet subagent** as the apply-executor, passing the paths to the change's `proposal.md`, `design.md`, and `tasks.md`. It works `tasks.md` sequentially and checks off each task as it lands.
> - **OpenCode:** delegate to `@apply-executor` (DeepSeek V4 Flash).
>
> Any step below that says "make the code changes" therefore describes what the **apply-executor** does — not the primary. The primary delegates, then reviews the executor's completion report and proceeds to `/opsx:verify`. The primary must not write implementation code itself (trivial typo / one-line exception only).
"""


def inject(path: Path, block: str, marker: str) -> str:
    text = path.read_text(encoding="utf-8")
    if marker in text:
        return "already hardened"
    lines = text.splitlines(keepends=True)
    insert_at = next(
        (i for i, line in enumerate(lines) if line.lstrip().startswith("**Input**")),
        None,
    )
    if insert_at is None:
        return "SKIPPED (no '**Input**' anchor — file structure changed?)"
    new_lines = lines[:insert_at] + [block.rstrip("\n") + "\n\n"] + lines[insert_at:]
    path.write_text("".join(new_lines), encoding="utf-8")
    return "hardened"


def check_openspec_version() -> None:
    """Warn (non-fatally) if the installed OpenSpec differs from the tested version."""
    exe = shutil.which("openspec")
    if not exe:
        print("  note: `openspec` not on PATH — cannot verify version; proceeding.")
        return
    try:
        result = subprocess.run(
            [exe, "--version"], capture_output=True, text=True, timeout=15
        )
    except Exception as exc:  # environment-dependent; never fatal
        print(f"  note: could not run `openspec --version` ({exc}); proceeding.")
        return
    installed = (result.stdout or result.stderr).strip()
    if installed and installed != TESTED_OPENSPEC_VERSION:
        print(
            f"  WARNING: installed OpenSpec is '{installed}', but this script was tested\n"
            f"           against {TESTED_OPENSPEC_VERSION}. If the generated /opsx templates\n"
            f"           changed, re-check the '**Input**' anchor and file paths, then bump\n"
            f"           TESTED_OPENSPEC_VERSION. Inspect the hardened files before relying on them.\n"
        )


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    check_openspec_version()
    targets: list[tuple[Path, str, str]] = []
    for pattern in ("**/commands/opsx/propose.md", "**/openspec-propose/SKILL.md"):
        targets += [(p, PROPOSE_BLOCK, PROPOSE_MARKER) for p in root.glob(pattern)]
    for pattern in ("**/commands/opsx/verify.md", "**/openspec-verify-change/SKILL.md"):
        targets += [(p, VERIFY_BLOCK, VERIFY_MARKER) for p in root.glob(pattern)]
    for pattern in ("**/commands/opsx/apply.md", "**/openspec-apply-change/SKILL.md"):
        targets += [(p, APPLY_BLOCK, APPLY_MARKER) for p in root.glob(pattern)]

    if not targets:
        print("No /opsx command or skill files found. Run `openspec init` first.")
        return 1

    for path, block, marker in sorted(targets, key=lambda t: str(t[0])):
        print(f"  {inject(path, block, marker):42s} {path}")
    print("Done. Re-run this after any `openspec update`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
