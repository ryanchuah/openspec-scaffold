# flash verifier renders verdict block in a non-English language, breaking English --require-marker asserts

Parked from `plans/archive/detect-truncated-stream/`. Adjacent to the parked `extract_text`
last-part-only defect (`knowledge/questions/opencode-delegate-extract-text-last-part-only.md`).
Non-blocking; monitored.

## The finding

During verify of `detect-truncated-stream`, the flash verifier (`deepseek/deepseek-v4-flash`)
completed a substantive, correct review (stream balanced: 15 `step_start` / 15 `step_finish`) but
rendered its final verdict block in Chinese:

```
## 验证通过
裁决：就绪
### 缺陷 - 无
```

This means "## Verify Pass" / "VERDICT: READY" / "### Defects - None" — but the wrapper's English
`--require-marker "## Verify Pass"` and `VERDICT:` literal asserts did not match, so the wrapper
reported `marker-missing`. The run was NOT truncated (balanced steps), and the substance is an
unambiguous READY — this is purely a language-drift artifact of the English-literal marker assert.

This is distinct from the `extract_text` last-part-only defect (which also yields false
`marker-missing`, but for an entirely different reason — extracting only the final text part).

## Candidate follow-ons

- Consider language-agnostic marker matching (e.g. structured JSONL verdict extraction from
  `opencode run --format json` rather than English-literal scraping).
- Add a `LANG` or locale hint to the verifier invocation prompt.
- Monitor for recurrence; if it becomes frequent, raise priority.

## Priority

Low/monitored — the orchestrator independently re-ran the verifier and confirmed the READY verdict
by substance. The marker-literal mechanism is fragile to language drift, but this is the first
observed instance.
