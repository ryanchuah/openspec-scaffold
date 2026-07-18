# Notes — graduate-sast-scanners (MEDIUM)

## Tier + routing
- **MEDIUM**, self-classified under this session's explicit operator autonomy grant (grant covers
  through archive; downstream propagation + push remain operator-gated). Tasks-only propose per the
  AGENTS.md MEDIUM rule, plus a `shared-lint-gate` delta spec because the change alters that specced
  capability's normative surface (`install-tools.sh` provisioning + `security-scanners.md` + the
  built-in check registry). Not COMPLEX-security: the change ADDS security tooling but does not
  itself touch auth/credentials/network surfaces, so the verify security pass is not triggered.
- **Direction gate:** ran on `explore-brief.md` before tasks — `PREMISE: AGREE`, `VERDICT: PASS`,
  zero 🔴 (review-log round 0). Its 🟡 items were design-detail questions (exact Semgrep/Bandit
  invocation + JSON key-paths, stdout-vs-file, pip degrade posture); all are resolved explicitly in
  `tasks.md` (there is no design.md at MEDIUM, so the apply contract carries the pinned argv/keys).
- **Provenance:** this is the "S-G upstream graduation" step deferred by
  psc-monitor/plans/security-audit-ap1 (s0-tooling.md Deferred section; audit-plan.md S-G).

## Critical-judgment calls (psc-monitor is not a scaffold expert — its plan was pressure-tested)
- **Kept:** graduate Semgrep + Bandit as first-class built-in *parsed* checks (not `[checks.custom.*]`),
  so their findings normalize and participate in `findings.json`/baseline-diff — the real upstream value.
- **Corrected #1:** psc-monitor said "wire into `install-tools.sh`" as if trivial. `install-tools.sh`
  is **Go-only**; Semgrep/Bandit are pip tools. This change adds a *new* pip-provisioning path and
  restructures the Go-absent guard so it no longer short-circuits the script. (Under-specified in the
  source plan; resolved here.)
- **Corrected #2:** psc-monitor lumped "root Python lockfile → osv activation" into the same deferral.
  That is **S-E psc-monitor remediation** (generate a root lockfile + a tool-choice decision), NOT
  scaffold work — osv-scanner is already scaffold-wired. Excluded from this change (out of scope).
- **Design choice — default-disabled, not auto-enabled:** auto-enabling on Python/`.git` presence
  (the gitleaks/osv-scanner pattern) would run the scanners on every downstream repo the moment sync
  lands and could red floors on open findings. Default-disabled (the jscpd/vulture pattern) makes the
  graduation sync-safe; each repo opts in and controls report-vs-gate via `--baseline`.
- **Design choice — version recorded-not-gated:** Semgrep/Bandit are Python-ecosystem tools; kept out
  of `EXPECTED_TOOL_VERSIONS` so a version drift never INFRA-FAILs a repo that pins its own version.

## Assumptions (non-blocking; recorded defaults)
- **Bandit `-f json` and Semgrep `--json` both write their report to stdout** (Bandit's human/log
  output and Semgrep's deprecation notices go to stderr), so both fit the generic
  `_run_builtin_tool_json` stdout-parse path; neither needs a bespoke file-then-read runner. Semgrep
  and Bandit are not installed in this session's environment (both absent from PATH), so this is
  asserted from their documented JSON contract, and the tests use stubbed stdout — not a live probe.
  If a live run later shows either tool writing JSON only to a file, the runner for that tool must
  switch to the deptry-style file-then-read shape (localized change; parser unaffected).
- Both tools exit non-zero when they find issues (Bandit exit 1, Semgrep exit 1); this is benign
  because `_run_builtin_tool_json` parses stdout regardless of exit code.
- Semgrep needs a ruleset; the scaffold does NOT bake one in — the repo supplies `--config` via
  `[checks.semgrep] args`. An enabled Semgrep with no `--config` will surface Semgrep's own error as
  an INFRA-FAIL (acceptable misconfiguration signal).

## Verification / acceptance criteria (checked by the orchestrator at verify — NOT executor tasks)
1. `scripts/checks.py --list` lists `bandit` and `semgrep` as `heavy check disabled <availability>`;
   `check.sh`/`pytest -q` stays green.
2. With a stubbed/available tool, `scripts/checks.py --check bandit` and `--check semgrep` each
   normalize a representative finding to `{check, rule, path, line, message}` and write `<name>.json`.
3. `bandit`/`semgrep` do NOT run under `--floor` (heavy tier) and do NOT run in `--report` unless
   enabled (default-disabled) — confirm a default config run does not execute them.
4. `--report --include bandit` (and `--include semgrep`) force-enables and runs the check for one run.
5. A version mismatch on either tool does NOT INFRA-FAIL (recorded-not-gated).
6. `install-tools.sh`: with Go absent but pip present, the Python scanners are still provisioned and
   the script exits 0 (Go-absence no longer short-circuits); with pip absent it warns + continues.
   Eyeball via a shellcheck/dry read + a `bash -n` parse; a live pip install is not required to verify
   the control-flow restructure.
7. `openspec validate graduate-sast-scanners --strict` exits 0.
8. Adversarial/boundary fixtures the orchestrator adds at verify (executor tests are a single blind
   source): empty `{"results": []}` → zero findings/ok; missing optional keys (`start`/`extra`
   absent for semgrep; `line_number` absent for bandit) → no crash, `line` = None; malformed
   non-JSON stdout → INFRA-FAIL (not a silent empty pass).

## Deferred (follow-ons — record in questions/INDEX.md at archive; NOT in this change)
- **`_custom_checks` `family=` fix** (the lessons' "S-G fix candidate"): let a `[checks.custom.<name>]`
  entry register a *fact*-family (preflight-exempt, graceful-degrade) check by honoring
  `spec.get("family", "check")`. Orthogonal to this change (Semgrep/Bandit are check-family); would
  let downstream register app-specific facts snapshots (e.g. psc-monitor's route-authz) without
  standalone scripts. Separate SMALL change.
- **npm-audit durable wiring** and the **durable scanner-PATH fix** — psc-monitor/operator items,
  already tracked (`scanner-provisioning-gaps`; questions "Audit scanner PATH").
- **Flip Semgrep/Bandit to gating** once downstream leads remediate — per-repo
  finding-closure-ratchet step, not a scaffold change.

## Downstream propagation (operator-gated — do NOT run without authorization)
After archive, `checks.py`, `install-tools.sh`, and `test_checks.py` are scaffold-managed and
propagate byte-identically via `sync_scaffold.py`. `knowledge/reference/security-scanners.md` is
per-repo knowledge (manual sweep, not the manifest) — each downstream copy needs the same
semgrep/bandit documentation added by hand during the propagation sweep. Record in
`knowledge/reference/pending-downstream-propagation.md`.

## Verify checkpoint

**1. Verdict:** READY for archive. My behavioral review (diff read, full suite, self-authored
boundary fixtures, real-tool live smoke) found zero defects; the independent deepseek-v4-pro
behavioral verifier pass returned READY/no-defects; the simplicity gate passed; the security and
data-path gates were not triggered (recorded below).

**2. Confirmed by eyeballing live output** (behavior, not counts): I installed the real tools
(bandit 1.9.4, semgrep 1.170.0) and ran them through the exact runner argv. Real `bandit -f json
-q -r` emits JSON to stdout (exit 1 on findings) in the `results[]` shape; real `semgrep --json
--quiet --config <rule>` emits JSON to stdout (exit 0) in the `results[]` shape; both parsers
normalized every real finding to `{check, rule, path, line, message}`. End-to-end through
`checks.py --check bandit`/`--check semgrep` in an isolated temp git repo returned FINDINGS (rc 2)
with normalized artifacts. `checks.py --list` shows both as `heavy check disabled`. Boundary
fixtures: empty/blank/missing-`results`/null-`results` → no findings, no crash; a finding missing
its optional line key → `line` = None; malformed non-JSON stdout → INFRA-FAIL (rc 3). Both are
absent from `EXPECTED_TOOL_VERSIONS`, so an arbitrary version is recorded and never gates.

**3. Defect found and how fixed:** None. No re-delegation was needed — the apply-executor
(deepseek-v4-flash, no Sonnet fallback) implemented every task verbatim; self-review, the
boundary probe, the real-tool smoke, and the pro verifier pass were all clean.

**4. As-built delta discovered during verify:** (a) The executor added a
`semgrep → semgrep/semgrep-action` line to `install-tools.sh`'s CI-actions comment (a benign,
correct extra beyond the literal task). (b) Real bandit emits ABSOLUTE finding paths;
`checks.py`'s existing `_normalize_finding_paths` rewrites them to repo-relative downstream of the
parser, so the parser correctly leaves `path` as-emitted — verified end-to-end. Neither needs an
artifact change. The external-tool JSON contract was validated against bandit 1.9.4 / semgrep
1.170.0 specifically.

**5. Forward-looking items (fold into knowledge/questions/INDEX.md and pending-downstream ledger at archive):**
- **`_custom_checks` `family=` fix** — deferred S-G follow-on (let `[checks.custom.*]` register a
  fact-family entry). Orthogonal to this change; separate SMALL change. → questions/INDEX.md.
- **Downstream propagation PENDING (operator-gated):** `checks.py`, `install-tools.sh`,
  `test_checks.py` are scaffold-managed (byte-identical sync); `knowledge/reference/security-scanners.md`
  is per-repo knowledge needing a manual sweep to extrends + psc-monitor. → pending-downstream-propagation.md.
- **Semgrep has no scaffold default ruleset (by design):** a repo enabling `semgrep` MUST supply
  `--config` via `[checks.semgrep] args`, else the check INFRA-FAILs. Monitored — a downstream repo
  could enable semgrep without a ruleset. → questions/INDEX.md.
- **Auto-detection trigger deliberately TBD:** both ship default-disabled (no trigger); a future
  operator may add a trigger (e.g. `.semgrep.yml` present) but must preserve sync-safety. → questions/INDEX.md.
- **Flip-to-gating is a per-repo downstream step** (finding-closure-ratchet) once a repo's leads
  remediate — not a scaffold change.
- **Tool JSON contract is version-sensitive:** validated at bandit 1.9.4 / semgrep 1.170.0; a future
  major bump could change the JSON shape. Low risk (parsers key on stable top-level fields). Monitored. → questions/INDEX.md.

**Still owned by archive (do NOT reconcile here):** promote the `shared-lint-gate` delta into
`openspec/specs/shared-lint-gate/spec.md`; reconcile `knowledge/STATUS.md`,
`knowledge/decisions/INDEX.md`, `knowledge/questions/INDEX.md`; add the pending-downstream-propagation
ledger entry; move the change dir to `openspec/changes/archive/<date>-graduate-sast-scanners/`.
