# SMALL change — `_custom_checks` `family=` fix

Tier: **SMALL**. Source: `knowledge/questions/custom-checks-family-fix.md` + `knowledge/HANDOFF.md`
Priority 2 (recon completed 2026-07-18). Not blocking anything.

## Problem statement

A `[checks.custom.<name>]` entry in `checks.toml` can only ever register as a **check**-family
entry: `scripts/checks.py:_custom_checks()` hardcodes `"family": "check"` (line ~396). There is no
way to register a custom **fact**-family check (preflight-exempt, graceful-degrade). This blocks
downstream repos (e.g. psc-monitor's route-authz) from registering app-specific *fact snapshots*
via config alone — they must ship a standalone script instead.

`family` governs only preflight/degradation semantics: check-family entries INFRA-FAIL a
`--report`/`--floor` run when their tool is unavailable; fact-family entries are preflight-exempt
and degrade gracefully (recorded skipped, run continues). Verified this session that `family` is
consulted only at `--list` display, the `--floor` fact-exclusion, the multi-mode preflight gate,
and the multi-mode execution `is_fact` branch — every site keys on `== "check"` vs not, and a
custom `family="fact"` flows correctly through all of them. The custom execution path itself
(`kind == "custom"`) is family-agnostic.

## Proposed approach / fix

**1. `scripts/checks.py` — `_custom_checks()` (~line 387–401).** Honor `spec.get("family",
"check")`, WITH validation so a typo cannot silently exempt a check from gating. Normalize
case/whitespace (folded in from the premise 💡) so a valid-but-padded/capitalized value is honored
while a genuine typo still falls back to `check`:

```python
family = str(spec.get("family", "check")).strip().lower()
if family not in ("check", "fact"):
    # Gating-safe default: an unrecognized value (typo like "chek") must NOT
    # silently become fact-exempt. Invalid -> "check" (gated), never "fact".
    family = "check"
```

then use `family` in the appended dict instead of the hardcoded `"check"`. (`str(...)` also guards a
non-string TOML value from raising in the membership test.)

**Why the validation matters:** everywhere downstream, `family != "check"` is treated as fact-like
(preflight-exempt + graceful-degrade). Without validation, a typo would silently exempt a check
from gating — a real footgun. Invalid → `check` (gating-safe), never `fact`.

**2. `scripts/checks.py` — `[checks.custom.<name>]` docstring (~line 60–66).** This is a bullet in
the existing module-level docstring, not a standalone block. It lists `command`, `tier`, `gate` but
not `family`. Add `family` right after the `gate` clause (~line 65): `family` (`check|fact`, default
`check`; `fact` = preflight-exempt, degrades gracefully).

**3. `scripts/test_checks.py` — `CustomCheckTest` (~line 279–315).** Add three tests, reusing the
existing tmp `checks.toml` fixture pattern in that class:
  - `family = "fact"` registers as fact-family — assert via `--list` output (family is column 3:
    `line.split()[2] == "fact"`).
  - `family = "fact"` is **preflight-EXEMPT** — with a missing `command` binary and `tier =
    "heavy"`, a `--report` run degrades gracefully (custom check recorded skipped, `rc == 0`, no
    `INFRA-FAIL` on stderr) instead of INFRA-FAILing. Mirror `test_fact_family_missing_does_not_
    trigger_preflight` (line ~886).
  - Invalid `family = "banana"` falls back to `check` AND still gates — assert `--list` shows
    `check` in the family column, and a `--report` run with a missing `command` binary INFRA-FAILs
    (`rc == 3`, `INFRA-FAIL` on stderr). This proves the footgun is closed.

## Out of scope

- No spec delta. No `openspec/specs/*` requirement pins custom checks to check-family (verified
  `defect-prevention-detectors`, `repo-invariant-checks`); SMALL tier ⇒ no spec/proposal artifacts.
- No change to the custom execution path, preflight loop, or any other `family` call site — they
  already handle `fact` correctly; this only stops `_custom_checks` from force-overriding to `check`.
- No new stderr warning on invalid `family` (optional per recon; omitted to keep the change minimal
  — the gating-safe fallback is the load-bearing behavior).
- No downstream propagation (operator-gated) — `checks.py` is scaffold-managed; propagation is a
  separate operator-invoked step.

## Verification

- Own: `bash scripts/check.sh` green (ruff + ruff-format + `pytest -q`), including the 3 new tests.
- Single `deepseek/deepseek-v4-flash` verifier pass (SMALL requirement).
- Commit runs through the git-native `pre-commit` hook (repo dogfoods `core.hooksPath`).

## Post-landing reconciliation (delegated to Sonnet archive-executor per operator pre-route)

Mark `knowledge/questions/custom-checks-family-fix.md` RESOLVED, drop its Parked pointer from
`knowledge/questions/INDEX.md`, add a `knowledge/decisions/INDEX.md` registry line, reconcile
`knowledge/STATUS.md` (respect the ≤3 cap), and delete `knowledge/HANDOFF.md` (Priority 2 was its
last actionable item; the rest are event-triggered/operator-gated and already parked elsewhere).
