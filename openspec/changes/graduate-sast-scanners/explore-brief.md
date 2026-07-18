# Explore brief — graduate-sast-scanners

## Problem
The psc-monitor security audit (AP-1, S0 session) built a deterministic SAST detector floor —
**Semgrep** (custom + registry rulesets) and **Bandit** (Python security linting) — but was
constrained not to touch the upstream `openspec-scaffold`. It ran the scanners as *standalone*,
repo-local scripts (`scripts/run_semgrep_security.py`, ad-hoc bandit) whose JSON output never
flows through the scaffold's `checks.py` finding pipeline (no normalized findings, no aggregate
`findings.json`, no baseline diff). The session explicitly deferred the upstream wiring as the
**"S-G upstream graduation"** step:

> "Wire Semgrep + Bandit into scaffold `checks.py` + `install-tools.sh`."
> (psc-monitor/plans/security-audit-ap1/s0-tooling.md, Deferred section)

Because `checks.py` / `install-tools.sh` are scaffold-managed (edited only here, then
`sync_scaffold.py`'d downstream), every downstream repo (`extrends`, `psc-monitor`) is missing a
shared, first-class way to run Semgrep/Bandit through the audit engine. Today the only downstream
option is a `[checks.custom.*]` command entry, which is unparsed (`.txt` output, null
findings-count) — it cannot contribute normalized findings or participate in baseline diffing.

## Root cause
The scaffold's curated built-in **parsed** check set (`ruff`, `gitleaks`, `osv-scanner`, `deptry`,
`radon`, `jscpd`, `vulture`) has no Semgrep or Bandit member, and `install-tools.sh` provisions
only Go binaries (`gitleaks`, `osv-scanner`) — it has no pip path for the two Python security
scanners. So the SAST tooling that psc-monitor proved out cannot be shared upstream without editing
the golden source.

## Solution direction
Graduate Semgrep + Bandit into the scaffold as **built-in parsed checks**, mirroring the existing
`ruff`/`osv-scanner` pattern exactly:
- `checks.py`: add each to `_REGISTRY` (heavy tier, `family="check"`), `_autodetect_defaults`
  (**default-disabled** — the `jscpd`/`vulture` opt-in pattern), `_BUILTIN_TOOL_BIN`, `_PARSERS`
  (normalize each tool's JSON → `{check, rule, path, line, message}`), and `_BUILTIN_RUNNERS`
  (via the existing `_run_builtin_tool_json`). **Not** added to `EXPECTED_TOOL_VERSIONS` → probed
  but version **recorded-not-gated**, the Python-ecosystem-tool posture already used for
  `ruff`/`deptry`/`radon`/`vulture`.
- `install-tools.sh`: add a pip-based provisioning block (guarded on `pip`, degrade-don't-block if
  absent), restructured so the existing Go block's absence no longer short-circuits the pip block.
- `security-scanners.md` + a `shared-lint-gate` delta spec: document the two Python SAST scanners.
- `test_checks.py`: mirror the existing stub-on-PATH tests for the two new checks.

**Why default-disabled + not-gated initially:** psc-monitor's own leads fire on known-unremediated
findings; gating on sync would red downstream floors. Default-disabled makes the graduation
**sync-safe** (verified: `check.sh` runs only ruff + `pytest -q`, never `checks.py --floor`, and
there is no CI — so a default-disabled check cannot red any downstream green gate). Each downstream
repo then opts in via `[checks.<name>].enabled = true` and controls report-vs-gate via `--baseline`;
the flip-to-gating is a per-repo finding-closure-ratchet step, not a scaffold change.

## Alternatives ruled out
1. **Leave them as `[checks.custom.*]` downstream** — the status quo. Rejected: custom checks are
   unparsed (no normalized findings, no baseline diff), and each downstream repo re-wires them by
   hand. The explicit S-G plan step is to graduate them upstream.
2. **Auto-enable on Python/`.git` presence (like gitleaks/osv-scanner)** — rejected: would run
   Semgrep/Bandit on every downstream repo the moment sync lands, potentially reding floors on
   open findings, violating sync-safety. Default-disabled + opt-in is correct.
3. **Provision Bandit via pip dev extras only (like `deptry`), not `install-tools.sh`** — rejected
   for cohesion: Semgrep/Bandit are *security scanners*, and `install-tools.sh` is the scaffold's
   one security-scanner provisioner; the explicit ask names `install-tools.sh`. (They remain
   version-recorded-not-gated, so a repo may still pin them in its own dev extras.)
4. **Also fix `_custom_checks` to honor a `family=` key** (the lessons' "S-G fix candidate" that
   would let downstream register *fact*-family custom entries) — deferred. It is orthogonal to the
   Semgrep/Bandit built-in wiring (both are check-family), adds risk to the preflight/degradation
   logic, and belongs to the separate "facts-snapshot registration" concern. Filed as a follow-on.

## Scope boundary
IN: `checks.py` (2 built-in checks), `install-tools.sh` (pip block), `security-scanners.md`,
`shared-lint-gate` delta spec, `test_checks.py`. OUT: `_custom_checks` family fix; npm-audit
wiring; durable scanner-PATH fix (already tracked in `scanner-provisioning-gaps`); the root-lockfile
→ osv activation (that is **S-E** psc-monitor *remediation*, not scaffold work); flipping the
scanners to gating (downstream, per-repo). Downstream propagation + push remain operator-gated.

## Note on the "diminishing returns" status
`knowledge/STATUS.md` says scaffold *process optimization* is at diminishing returns and future work
is downstream. This change is not speculative process optimization — it is the upstream graduation of
concrete, downstream-**validated** security tooling (psc-monitor S0), which is exactly the
downstream-driven scaffold work the 2026-07-11 audit verdict permits.
