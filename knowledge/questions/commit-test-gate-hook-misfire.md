# commit-test-gate hook misfires on complex non-commit Bash commands

Discovered live during the `checks-facts-split` apply phase (2026-07-03). The Claude `PreToolUse`
commit-test-gate hook (`.claude/settings.json`, matcher `Bash(git commit*)`) fires on some
**non-commit** Bash calls that are structurally complex — reproduced with a harmless `true` payload
carrying file redirections plus an EXIT-sentinel echo. Plain probes (`echo`, `git status`, a
single-line `opencode run --help`) do **not** trigger it. The matcher appears to be keying on some
shape of the command string (heredocs / multiple redirections / multi-statement chains) rather than
reliably on the literal `git commit` prefix it's supposed to gate.

**Impact:** while the suite is red mid-change, this can intermittently block the orchestrator's own
delegation launches (`opencode run` invocations), not just actual commit attempts.

**Workaround (used this session):** put the launch in a script file and invoke it as a single plain
command, avoiding the complex inline shape that seems to trip the matcher.

**Monitored, not blocking** — the workaround is reliable and no in-flight work is currently stuck on
this. Root-cause fix (tighten the matcher so it only fires on actual `git commit` invocations, not
adjacent complex Bash shapes) is earmarked for the lint-layer portfolio change (`plans/day-to-day-tooling/explore-brief.md`
change C) or its own SMALL, whichever comes first.
