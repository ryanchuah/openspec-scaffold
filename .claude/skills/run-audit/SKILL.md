---
name: run-audit
description: Run the deterministic audit cycle — list, floor/report, triage, optional tag, log. Operator-invoked. Writes report artifacts to output/checks/<date>/ and appends one line to knowledge/audit-log.md (tag + log-line). Never fixes code.
license: MIT
compatibility: Requires openspec CLI.
metadata:
  author: openspec
  version: "1.0"
  generatedBy: "1.4.1"
---

Run the deterministic audit cycle — `checks.py` to discover or run checks,
`audit_scope.py` to anchor and log. Operator-invoked; the cycle writes report
artifacts (untracked) and, on explicit request, appends one tracked log line.

**Ceremony vs day-to-day.** The audit ceremony covers both families:
check-family detectors (findings-capable, gated by preflight) and fact-family
snapshots (always degrade gracefully, never fail a run). Both write dated output
under `--report`. For quick orientation snapshots that regenerate on use, use
`facts.py` directly — it runs fact-family entries undated to `output/facts/`
and is not part of the audit ceremony.

**Interpreter convention.** Use `<py>` below as a placeholder for the repo's
Python interpreter. Resolve it in this try-order:
1. A repo task-runner `audit-*` target, if one exists (e.g. `just audit-floor`);
2. `.venv/bin/python` if the virtual environment exists;
3. `python3` if available;
4. `python` otherwise.

**Step 0 — pre-check.** Before entering the cycle, confirm that both
`scripts/checks.py` and `scripts/audit_scope.py` exist and run under
`<py>`. If either is missing or fails, stop immediately with a clear message
— do not discover the gap mid-cycle.

**Cycle steps**

1. **Discover.** List available checks:
   ```bash
   <py> scripts/checks.py --list
   ```

2. **Run.** Execute the audit. Choose one:
   - Quick floor (no date-stamped output) — check-family entries only:
     ```bash
      <py> scripts/checks.py --floor
     ```
   - Full report with date-stamped output directory — both
     check-family and fact-family entries, all dated:
     ```bash
      <py> scripts/checks.py --report --date YYYY-MM-DD
     ```
     Results land in `output/checks/<date>/` (untracked, single-use).

3. **Triage.** Read the JSON artifacts written to `output/checks/<date>/`.
   Apply judgment to determine which findings are real defects vs.
   environment/configuration noise. The skill's LLM value is in this step.

4. **Anchor (operator-gated).** Tag this audit only when the operator's
   invocation explicitly asks to "tag" or "anchor this audit". Otherwise
   run the cycle read-only and report findings without anchoring.
   ```bash
   <py> scripts/audit_scope.py tag --date YYYY-MM-DD
   ```
   This is the **sole repo-state mutation** in the audit cycle.

5. **Log.** Print the registry line and append it to `knowledge/audit-log.md`:
   ```bash
   <py> scripts/audit_scope.py log-line --date YYYY-MM-DD --essence "..."
   ```
   Append the printed line to `knowledge/audit-log.md`. This is the **sole
   tracked-file write** — operator-review it.

**Preflight semantics (enabled vs installed).** Before executing any
check-family entry, `checks.py --floor`/`--report` preflights every selected
enabled tool. If one or more tools are unavailable (not on PATH or version
mismatch), all missing tools are reported at once in a self-explaining message,
**nothing is run**, and the process exits 3. Install the missing binary, or
disable the check in `checks.toml` — disabling a security tool (e.g.
gitleaks, osv-scanner) drops that coverage, which is the operator's call.

Fact-family entries are **exempt** from preflight: they degrade gracefully if
a tool is absent (e.g. radon missing produces an empty result, not a failure).
For day-to-day fact snapshots that do not need the ceremony, run
`scripts/facts.py` directly.

**Staleness cadence.** Trigger a full audit from the inventory signal
(`audit_anchor.commits_since`), not a calendar — run one when
`commits_since` grows large enough that the baseline may be stale.

**Annual re-justify.** Once per year (at minimum), re-justify every entry in
the suppression baseline / whitelist — tools and configurations drift, and
suppressions that were correct at baseline may mask regressions.

**Error handling**
- Stop the cycle on the first non-zero script exit and report the failure.
  Do not proceed to later steps.
- If `output/checks/<date>/` already exists when you attempt to run a full
  report, report it and do **not** overwrite or re-run without explicit
  operator direction.

**Wiring-detection branch**
- Before running, check whether the per-repo audit layer is wired:
  - `checks.toml` (check configuration)
  - `checks/` directory (check definitions)
  - A task-runner `audit-*` target (convenience entry point)
- If any are absent, say so and provide concise inline guidance on what each
  is for — but do **not** auto-create them. Wiring is per-repo,
  operator-directed work.

**Guardrails**
- `checks.py` writes reports only — it never mutates repo state.
- `audit_scope.py tag` is the sole repo-state mutation, and it is
  operator-gated (step 4).
- The `knowledge/audit-log.md` append is the sole tracked-file write; the
  operator reviews it before commit.
- Never edit, create, or delete code or tracked files from this skill.
