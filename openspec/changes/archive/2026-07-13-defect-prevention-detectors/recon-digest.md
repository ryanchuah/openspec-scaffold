# recon-digest — defect-prevention-detectors (OW-1 + OW-4)

Load-bearing facts from a full `checks.py` recon (Explore subagent, 2026-07-13) + the architecture
decision. Durable so this change is resumable without re-running recon.

## checks.py architecture (the surface both detectors plug into)
- **Registry-driven, NOT class-based.** Every check is a dict in module-level `_REGISTRY`
  (`scripts/checks.py:198-254`). Fields: `name`, `tier` (`floor|heavy|snapshot`), `kind`
  (`builtin|delegate|custom`), `family` (`check|fact`), optional `trigger`/`coverage_note`.
- **Backends:** `builtin` (wraps external binary via `_BUILTIN_TOOL_BIN` + `_run_X` + `_parse_X`),
  `delegate` (imports a sibling script's `main()`), `custom` (config argv). The ONLY in-process
  builtin today is `inventory` (family=fact, zero findings) — special-cased in
  `_availability_for_check` (`:426-427`, always available) and `_execute_check` (`:1130-1134`,
  runs in-process). **No findings-capable in-process builtin exists yet; no `ast` use anywhere in
  scripts/ (these detectors introduce the first).**
- **Finding schema (what every parser emits):** `{check, rule, path, line, message}` — NO
  `severity`, NO `id`. Pick a stable `rule` slug per pattern (e.g. `assert-or-true`,
  `unbounded-fetchall`). Fingerprint is `check|rule|path|message` (`:1185-1193`).
- **family:** both new detectors are findings-capable gates → `family: "check"`. `--floor` runs
  only `family=="check"`. checks.py findings → exit 2 (FINDINGS); **this is the audit tool, NOT
  check.sh** — findings surface in the audit report and do NOT fail pytest/check.sh. So
  enabled-by-default is safe (advisory audit surface, operator-triaged), FP cost is low.
- **Config:** no `checks.toml` in scaffold (per-repo, optional; absent → `"defaults"`).
  New builtins MUST be added to `_autodetect_defaults` (`:301-323`). `_is_enabled` reads
  `[checks.<name>].enabled`.
- **Preflight:** fails whole run (exit 3) if an enabled check-family entry's tool is unavailable.
  A pure-AST detector needs NO preflight → special-case in `_availability_for_check` like
  `inventory` (else a plain builtin does `_BUILTIN_TOOL_BIN[name]` → KeyError).
- **CLI:** argparse `:1538-1566`, mutually-exclusive `--list|--check NAME|--floor|--report`, plus
  `--include NAME` (report-only). No `checks.toml` value flags.
- **Tests that MUST be updated when adding a registry entry:**
  `test_checks.py` `ListModeTest` (`:198-224`, hard-codes full registry name set in `expected_names`)
  AND `AutodetectTest` (`:241-261`, asserts default enabled/disabled per check). New detector tests
  write REAL source files into the temp repo (`self.repo`) and assert on the `{check,rule,path,line,
  message}` finding + `rc==2` FINDINGS contract (pattern: `NormalizedFindingsTest._run_single_check`,
  `:452-486`).

## Scoping / false-positive discipline (house bar: `repo_lint.py:48-55` near-zero-FP)
- **No test-file globbing helper exists** — must be written. Only extension filter today is
  `_detect_env_vars` (`:607-620`).
- **OW-1 test-quality detector runs ONLY on test files** (`test_*.py` / `*_test.py`, pytest
  discovery). BEWARE self-scan: `scripts/test_checks.py` itself contains `assert`/mock patterns that
  will legitimately flag (advisory, fine — but do not let it break an existing "self-clean" test;
  recon found none).
- **OW-4 data-scale detector runs on NON-test source only** (exclude test globs + fixtures).

## Verify-skill hooks — MOSTLY ALREADY PRESENT (this is the big scope-reducer)
- The verify skill ALREADY has BOTH lenses: test-quality (`SKILL.md:98-110`, incl. the OW-1
  "would this test fail if the behavior broke?" at :102) and data-scale (`SKILL.md:112-121`).
- **Forward-compat clause `SKILL.md:125`** (pre-written for exactly OW-1/OW-4): "when a
  corresponding deterministic detector ships (e.g. a test-quality or data-scale check in
  `scripts/checks.py`), the lens prompt SHALL direct the verifier to run and confirm the detector's
  findings rather than rediscover them." → OW-1/OW-4's verify work = **fulfill this hook**: make
  each lens prompt concretely run `checks.py --check <detector>` and confirm findings. NOT new lens
  prose.
- **OW-4 verify RULE** ("data-path change requires an at-scale run OR a recorded bounded-domain
  argument in notes.md"): harden from the current lens *question* (`SKILL.md:118`) into a rule.
  Best home: a conditional block modeled on the security-review gate (`SKILL.md:157-164`). Cite the
  canonical `AGENTS.md:321-325` "Mind data scale" span + `openspec/config.yaml rules.verify` — do
  NOT restate.

## ARCHITECTURE DECISION (Opus, this session) — the open fork from lesson-check-ratchet design.md:261
**DECIDING FACT (verified):** `checks/*.py` (the `repo-invariant-checks` / `repo_lint.py` framework)
are **per-repo and do NOT propagate** — `checks/` is NOT in `scaffold_manifest.txt`; STATUS confirms
the framework "arrives INERT (no `checks/*.py`)" downstream; each repo authors its own. `repo_lint.py`'s
`no_fetchall.py` docstring is a per-repo TEACHING TEMPLATE, not a shipped universal detector. Therefore
the ONLY way to ship a UNIVERSAL, scaffold-owned detector that reaches every repo is an in-process
builtin in the scaffold-managed `checks.py`. The per-repo `checks/*.py` layer stays for repo-SPECIFIC
invariants grown from incidents; OW-1/OW-4 are UNIVERSAL → they belong in the universal layer.
(Nice-to-have: update repo_lint.py's `no_fetchall.py` example to avoid implying repos should
re-implement the now-universal `data-scale` check — OPTIONAL, note only, don't over-scope.)

**Both detectors ship as first-class IN-PROCESS builtins in `scripts/checks.py`** (special-cased
like `inventory`: always-available, no preflight, in-process AST), family=`check`, **enabled by
default** (advisory audit surface, not a CI gate → FP-safe). Rationale: (a) OW-1 says verbatim "new
`checks.py` detector (enabled by default)"; (b) scaffold-owned UNIVERSAL detectors belong in the
scaffold-managed `checks.py` (propagates to all repos), not per-repo `checks/*.py` repo-lint tenants
(which are for repo-SPECIFIC invariants); (c) in-process AST needs no external binary.
- Detector names (proposed): `test-quality` (rules: `assert-or-true`, `assert-true`, `empty-test`,
  `self-mock`, `unfrozen-clock`) and `data-scale` (rule: `unbounded-fetchall`).
- OW-4 near-zero-FP tack: AST-flag `.fetchall()` calls (Attribute call, `attr=="fetchall"`) in
  non-test source — the clearest "materialize entire result set" signal. Keep the rule tight; the
  verify RULE + lens is the judgment layer.

## Manifest / propagation
`scripts/checks.py` (manifest L40), `scripts/test_checks.py` (L52), verify SKILL (L17) are all
scaffold-managed → propagate. If any new sibling script is added it must be added to the manifest —
but the DECISION above keeps everything IN checks.py, so no new manifest entries needed.

## Spec deltas Change 2 will need (CONFIRMED from reading the specs)
- **NEW capability `defect-prevention-detectors`** (ADDED): the scaffold ships two universal
  in-process `checks.py` builtins — `test-quality` (runs on test files only) and `data-scale` (runs
  on non-test source) — family=check, enabled-by-default, special-cased no-preflight like `inventory`,
  emitting the `{check,rule,path,line,message}` contract, held to the near-zero-FP admission bar.
  (No existing spec governs the checks.py builtin registry per-detector; a small new capability is
  the right governance home.)
- **MODIFIED `verify-multimodel-gate`**: the forward-compat clause at `spec.md:100` ("when a
  corresponding detector ships … the lens prompt SHALL direct the verifier to run and confirm the
  detector's findings rather than rediscover them") becomes CONCRETE — the test-quality &
  data-scale lens prompts (`spec.md:97-98`) SHALL instruct the verifier to run
  `checks.py --check test-quality` / `--check data-scale` and confirm findings. Also add/harden the
  OW-4 **data-path verify RULE** (currently a lens *question* at `spec.md:98`): a data-path change
  SHALL record either an at-scale run or a bounded-domain argument in `notes.md` (cite AGENTS.md
  "Mind data scale", don't restate).
- **NOT `repo-invariant-checks`** — that governs the per-repo `checks/*.py`/`repo-lint` framework,
  which these universal builtins do NOT touch. No delta there.
- **Verify-skill prose** (`.claude/skills/openspec-verify-change/SKILL.md:97-100,112-125`): update the
  lens prompts + selection prose to match the concretized spec (run the detector). Scaffold-managed.
- **test_checks.py**: update `ListModeTest.expected_names` + `AutodetectTest` for the 2 new entries;
  add finding-shape + scoping tests (write real source into temp repo, assert `{check,rule,...}` + rc=2).
