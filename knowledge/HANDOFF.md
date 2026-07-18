# HANDOFF — curated next-session work queue (written 2026-07-18, trimmed 2026-07-18)

> Not a context-exhaustion dump. A deliberately-curated queue of follow-ons the operator asked to hand
> forward. Priority 1 (commit-gate bypass) is now **DONE** — shipped by `git-native-commit-gate`
> (`openspec/changes/archive/2026-07-18-git-native-commit-gate/`); see
> `knowledge/decisions/INDEX.md` and `knowledge/questions/commit-gate-bypass.md` (marked RESOLVED).
> Absorb the remaining items, do the work they describe (starting with Priority 2), and **delete this
> file** once they are either done or re-parked. Its normal state is absent.

---

## Priority 2 — `_custom_checks` `family=` fix (SMALL — RECON DONE, ready to apply)

See `knowledge/questions/custom-checks-family-fix.md`. Let a `[checks.custom.<name>]` entry in
`checks.toml` register a **fact**-family (preflight-exempt, graceful-degrade) check by honoring
`spec.get("family", "check")` — today `_custom_checks` hardcodes `family="check"`. Unblocks downstream
repos registering app-specific fact snapshots (e.g. psc-monitor's route-authz) without standalone
scripts. **Not blocked. SMALL tier** (parked question confirms).

**Recon completed this session (2026-07-18) — do NOT re-derive, apply directly:**

- **The fix** — `scripts/checks.py`, `_custom_checks()` at **line ~387–401**. Change the hardcoded
  `"family": "check"` (line ~396) to honor the config, WITH validation to close a footgun:
  ```python
  family = spec.get("family", "check")
  if family not in ("check", "fact"):
      family = "check"   # gating-safe default; a typo ("chek") must NOT silently become fact-exempt
  ```
  then use `family` in the dict. **Why the validation matters:** everywhere downstream, `family != "check"`
  is treated as fact-like (preflight-exempt + graceful-degrade). Without validation, a typo would
  silently exempt a check from gating — a real footgun. Default invalid → `check` (safe), not `fact`.
  (Optional: emit a one-line stderr warning on an invalid value. Author's call.)

- **Why the change is SAFE — the full `family` usage map (verified this session).** `family` is
  consulted only at these sites, all keying on `== "check"` vs not, and a custom `family="fact"` flows
  correctly through every one: `--list` display (~1945); `--floor` filter `family != "check"` excludes
  facts (~2028 — correct, facts aren't floor checks); preflight availability gate skips non-check
  (~2085); execution `is_fact = family == "fact"` degrades gracefully (~2139/2151/2194). No other code
  path branches on `family`. The custom-check execution path (`kind == "custom"`, ~line 487) is
  family-agnostic — it captures stdout to `<check>.txt`; family only governs preflight/degradation.

- **Docstring** — the `[checks.custom.<name>]` docstring (`scripts/checks.py` ~line 60–66) lists
  `command`, `tier`, `gate` but NOT `family`. Add `family` (`check|fact`, default `check`;
  `fact` = preflight-exempt, degrades gracefully).

- **Test** — add to `scripts/test_checks.py` (custom-check tests live at ~line 280–310): a
  `[checks.custom.<name>]` with `family = "fact"` (a) registers as fact-family (assert via `--list`
  output showing `fact`), and (b) is preflight-EXEMPT — with an unavailable/missing `command`, the run
  degrades gracefully (skipped, run continues) instead of INFRA-FAILing. Add a companion test that an
  invalid `family = "banana"` falls back to `check`. Reuse the existing tmp `checks.toml` fixture
  pattern in that test class.

- **No spec delta needed.** No `openspec/specs/*` requirement pins custom checks to check-family
  (checked `defect-prevention-detectors`, `repo-invariant-checks`); `repo-invariant-checks` mentions
  `[checks.custom.*]` only as the ast-grep graduation escape hatch (line ~83), not a family constraint.
  SMALL tier ⇒ no spec/proposal artifacts anyway.

- **Process (SMALL):** write a plan (problem/approach/out-of-scope) to `plans/custom-checks-family-fix/`
  → orchestrator runs the flash **SMALL premise pass** → apply (**operator pre-routed apply/archive to a
  Sonnet subagent this session — honor that unless the operator says otherwise**) → own verification +
  the single `deepseek/deepseek-v4-flash` verifier pass → commit. The commit runs through the
  now-live git-native `pre-commit` hook (this repo dogfoods `core.hooksPath=scripts/githooks`) → full
  suite must be green. **After it lands:** mark `knowledge/questions/custom-checks-family-fix.md`
  RESOLVED, remove its Parked pointer from `knowledge/questions/INDEX.md`, add a `decisions/INDEX.md`
  line, and reconcile `STATUS.md` (respect the ≤3 cap).

---

## The other 3 graduate-sast-scanners follow-ons — event-triggered, NOT actionable now

None are blocked; each is *waiting for a trigger event* — do nothing until it happens:
- **`semgrep-needs-config`** (`knowledge/questions/semgrep-needs-config.md`) — monitor. Add a
  preflight WARNING ("semgrep enabled but no `--config` in args") only **if operator confusion
  recurs** during downstream propagation.
- **`sast-auto-detection-trigger`** (`knowledge/questions/sast-auto-detection-trigger.md`) — deferred
  by design. Revisit only **when a downstream repo asks** to auto-enable; any trigger must preserve
  sync-safety (nothing auto-enables on a downstream repo the moment sync lands).
- **`sast-tool-json-version-sensitivity`** (`knowledge/questions/sast-tool-json-version-sensitivity.md`)
  — monitor. Update parser key-paths only **if a bandit/semgrep major bump** produces empty/nonsensical
  findings. Parsers validated at bandit 1.9.4 / semgrep 1.170.0; version-recorded-not-gated so a bump
  never INFRA-FAILs.

---

## Also outstanding (operator-gated — not for the agent to run unprompted)

Downstream propagation of **three** shipped-but-unpropagated changes is pending in
`knowledge/reference/pending-downstream-propagation.md`: `graduate-sast-scanners` (scaffold files
byte-identical; `security-scanners.md` needs a manual per-repo sweep), `roll-decisions-index`
(extrends needs its own pre-roll first), and `git-native-commit-gate` (scaffold files byte-identical
incl. exec bit; each downstream must run `bash scripts/setup-hooks.sh` once; `new-repo-bootstrap.md`
is scaffold-local so its bootstrap step is repeated by hand). Push to remote is also operator-gated.
Do these only on explicit operator instruction (via the `propagate-scaffold` skill).
