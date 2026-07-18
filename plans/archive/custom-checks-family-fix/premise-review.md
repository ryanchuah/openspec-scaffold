# SMALL premise review — `_custom_checks` `family=` fix

Reviewer: `openspec-reviewer` @ `deepseek/deepseek-v4-flash` (flash SMALL premise pass, 2026-07-18).
Raw log: `/tmp/small-premise-out.jsonl` (verdict recovered from raw parts — the wrapper's
`extract_text` hit the known last-part-only defect and falsely reported `marker-missing`; the
`### Premise Verdict` block WAS emitted; see `knowledge/questions/opencode-delegate-extract-text-last-part-only.md`).

### Premise Verdict

PREMISE: AGREE

- **Root, not symptom**: Yes. The hardcoded `family="check"` in `_custom_checks()` is the genuine
  root cause — forcing every custom entry to check-family regardless of config.
- **Solution targets the root**: Yes. Honor `spec.get("family", "check")` with a validation
  guardrail (invalid → `"check"`, never `"fact"`). Opens fact-family custom checks while keeping the
  footgun closed.
- **Scope right-sized**: Yes. Three concrete edits with a clear, genuine out-of-scope list.
- **Blind spots**: None critical. The `family`-usage-map claim was re-verified against the code
  (lines 1945, 2028, 2085, 2139, 2150–2151, 2182+; `kind == "custom"` at 487 is family-agnostic).

VERDICT: PASS

### Non-blocking findings folded into the plan

- 🟡 Docstring target clarity — the `family` bullet is added to the existing module-level
  `[checks.custom.<name>]` docstring, right after the `gate` bullet (~line 65). Instruction sharpened.
- 💡 Case/whitespace sensitivity — the strict `in ("check", "fact")` check would let `"Fact"` /
  `" fact"` silently fall back to `check`. Incorporated: normalize with `str(...).strip().lower()`
  before validating, so a capitalized/padded valid value is honored while a genuine typo still
  falls back to `check` (gating-safe property preserved). `str(...)` also guards a non-string TOML
  value from raising in the membership test.

No operator override needed — AGREE clears the SMALL apply gate under the standing autonomy grant.
