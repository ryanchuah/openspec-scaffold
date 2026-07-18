# HANDOFF — curated next-session work queue (written 2026-07-18, trimmed 2026-07-18)

> Not a context-exhaustion dump. A deliberately-curated queue of follow-ons the operator asked to hand
> forward. Priority 1 (commit-gate bypass) is now **DONE** — shipped by `git-native-commit-gate`
> (`openspec/changes/archive/2026-07-18-git-native-commit-gate/`); see
> `knowledge/decisions/INDEX.md` and `knowledge/questions/commit-gate-bypass.md` (marked RESOLVED).
> Absorb the remaining items, do the work they describe (starting with Priority 2), and **delete this
> file** once they are either done or re-parked. Its normal state is absent.

---

## Priority 2 — `_custom_checks` `family=` fix (the one actionable graduate-sast-scanners follow-on)

See `knowledge/questions/custom-checks-family-fix.md`. Let a `[checks.custom.<name>]` entry in
`checks.toml` register a **fact**-family (preflight-exempt, graceful-degrade) check by honoring
`spec.get("family", "check")` — today `_custom_checks` (in `scripts/checks.py`) hardcodes
`family="check"`. This unblocks downstream repos registering app-specific fact snapshots (e.g.
psc-monitor's route-authz) without standalone scripts. Clean SMALL change. **Not blocked.**

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
