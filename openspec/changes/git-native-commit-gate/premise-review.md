# Premise review — direction gate (deepseek-v4-pro, 2026-07-18)

### Premise Verdict

Problem correctly framed (real, evidenced); root cause correctly diagnosed (prefix-anchored glob +
harness-locked enforcement); solution (git-native pre-commit hook, defense-in-depth Option D) targets
both gaps. One 🔴 is an architectural under-specification of the defer mechanism, to resolve in
design.md — it does not invalidate the direction.

**PREMISE: AGREE**

### Findings carried into design.md (must resolve)

- **🔴 Defer-detection under-specified.** `test-gate.sh` is currently git-free. The Option-D defer
  branch adds git-config/hook-executability detection — a new dependency class with failure modes
  (git absent from PATH; `rev-parse` fails in bare/submodule/detached; relative `core.hooksPath`
  resolution mismatch). A *false deferral* (no-op when git-native will NOT actually run) = silent
  gate gap. **design.md must specify the defer algorithm with fail-safe semantics: defer ONLY on
  positive confirmation git-native will fire; on any uncertainty, run `check.sh`.**
- **🟡 `--no-verify` regression (Claude).** With git-native active, PreToolUse defers, then git skips
  the pre-commit hook on `--no-verify` → no gate. Today the PreToolUse hook gates even `--no-verify`.
  Resolve: the defer branch must NOT defer when the commit carries `--no-verify`/`-n` (test-gate then
  runs `check.sh` itself) — preserving current Claude coverage; the visible `--no-verify` opt-out
  remains only for non-Claude / git-native.
- **🟡 `core.hooksPath` overwrite.** `setup-hooks.sh` must warn (not silently clobber) when an
  existing non-empty `core.hooksPath` differs.
- **🟡 `--local` scope.** Use `git config --local core.hooksPath scripts/githooks`.
- **🟡 Test strategy.** Specify the throwaway-repo fixture concretely (needs `check.sh` + `ruff.toml`
  + a test-cmd, or a minimal stub hook that tests git's invocation mechanism independent of
  `check.sh`).

### Suggestions (design notes)
- Note the downstream split-enforcement surface (test-gate via git-native; scaffold_check via
  PreToolUse) in the follow-on context.
- `git commit --amend` correctly fires the git-native hook (gates amends too) — a perf note.

Full review text: `/tmp/explore-review-out.jsonl.text.txt` (session-local).
