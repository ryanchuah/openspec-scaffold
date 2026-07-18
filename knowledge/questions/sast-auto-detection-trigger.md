# SAST auto-detection trigger — TBD

Deferred follow-on from `graduate-sast-scanners` (shipped 2026-07-18).

## What
Both `bandit` and `semgrep` ship **default-disabled** with no auto-detection trigger — the
`jscpd`/`vulture` opt-in pattern. A future operator may want to add an auto-enable trigger (e.g.
`.semgrep.yml` present in the repo, or Python source), but the trigger must preserve sync-safety:
nothing auto-enables on a downstream repo the moment the scaffold sync lands.

## Why deferred
Default-disabled is the safe starting point. The gitleaks/osv-scanner pattern (auto-enable on tool
presence) would run scanners on every downstream repo on sync and could red floors on open findings.
A trigger is a deliberate, later design decision — not needed for this graduation.

## When
Revisit when a downstream repo asks for it or when operator adds trigger logic.
