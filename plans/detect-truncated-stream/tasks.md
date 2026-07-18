# tasks.md — detect-truncated-stream (apply-executor scope)

Implement in `scripts/opencode_delegate.py` and `scripts/test_opencode_delegate.py` ONLY.
Do NOT touch spec/skill/doc files — those are handled by the orchestrator.
Work top-to-bottom; check off each `[ ]` → `[x]` as it lands. Match the file's existing style
(type hints, docstring voice, no new imports needed).

## opencode_delegate.py

- [x] 1. Add a new pure helper `detect_truncated_stream(out_jsonl_text: str) -> bool` in the
  "Pure helpers" section (place it right after `extract_text`, since it parses the same JSONL).
  Behavior: iterate `out_jsonl_text.splitlines()`; skip blank lines; `json.loads` each line inside
  a `try/except json.JSONDecodeError: continue`; skip objects that are not dicts. Count top-level
  `obj.get("type") == "step_start"` into `starts` and `obj.get("type") == "step_finish"` into
  `finishes`. Return `starts > finishes`. Give it a docstring explaining: this is the opencode
  silent-truncation signature (provider stream returns an empty completion, opencode exits 0 with an
  unterminated final step); a healthy run balances `step_start`/`step_finish`, so `starts > finishes`
  means a request opened and never completed. Note it returns `False` on balanced counts, no step
  events, or any parse degradation.

- [x] 2. Extend `classify_status` — add a trailing keyword parameter `truncated: bool = False`
  (default `False` so existing positional callers/tests are unaffected). Insert the new branch in
  precedence: after the `if not text: return "crash"` branch and BEFORE the
  `if not marker_ok: return "marker-missing"` branch, add:
  `if truncated: return "truncated-stream"`. Update the function docstring's numbered precedence
  list to include the new step 4 (`truncated → "truncated-stream"`) and renumber the following
  steps; keep the existing exit-code-lie note.

- [x] 3. Wire into `main()`: after the existing `text = extract_text(out_text)` /
  `marker_ok = ...` lines, compute `truncated = detect_truncated_stream(out_text)`. Pass it to
  `classify_status(exit_code, fallback, text, marker_ok, truncated=truncated)`. Add
  `"truncated": truncated,` to the `result` dict that is written to `--result-out` (place it near
  `"text_present"` / `"marker_ok"`). Do NOT add anything to the ledger record — the `status` field
  already carries `"truncated-stream"`.

- [x] 4. Update the module docstring (top of file): change the status list
  `ok|fallback|timeout|crash|marker-missing` to `ok|fallback|timeout|crash|truncated-stream|marker-missing`.

## test_opencode_delegate.py

- [x] 5. Add a `TestDetectTruncatedStream` class (place after `TestExtractText`) with these cases,
  using top-level underscore `type` (matching the real opencode stream):
  - balanced counts (e.g. one `step_start` + one `step_finish`) → `False`.
  - `starts > finishes` (two `step_start`, one `step_finish`) → `True`.
  - no step events at all (only `text` / `tool_use` lines) → `False`.
  - empty string `""` → `False`.
  - blank + non-JSON lines interleaved, still balanced → `False` (tolerance).
  - more `step_finish` than `step_start` (defensive) → `False`.
  - incident-shaped fixture: a `text` part, then `step_start`, `step_finish`, `tool_use`, a second
    `text`, and a final bare `step_start` (2 starts, 1 finish) → `True`.

- [x] 6. Add cases to `TestClassifyStatus` (use the existing `_c` static helper, passing
  `truncated=` as a keyword):
  - `_c(0, False, "x", True)` with `truncated=True` → `"truncated-stream"`.
  - truncated wins over marker-missing: `_c(0, False, "x", False)` with `truncated=True` →
    `"truncated-stream"`.
  - fallback over truncated: `_c(0, True, "x", True)` with `truncated=True` → `"fallback"`.
  - timeout over truncated: `_c(124, False, "x", True)` with `truncated=True` → `"timeout"`.
  - crash over truncated: `_c(0, False, None, True)` with `truncated=True` → `"crash"`.
  - default param unaffected: `_c(0, False, "x", True)` (no `truncated`) → `"ok"`.
  Note: `_c` currently forwards only 4 args — update `_c` to accept and forward an optional
  `truncated=False` keyword so these cases can pass it through.

- [x] 7. Add `TestMainPipeline.test_truncated_stream_status`: build fixtures via `_make_fixtures`
  with an `out_jsonl` that has text AND unbalanced steps, e.g.:
  `'{"type":"text","part":{"text":"partial work VERDICT: READY"}}\n'` +
  `'{"type":"step_start"}\n{"type":"step_finish"}\n{"type":"step_start"}\n'`
  (2 starts, 1 finish, text present). Run `od.main([...])` with `--require-marker "VERDICT:"`
  (a satisfied marker, to prove truncated wins even when the marker matches). Assert `rc == 1` and
  `json.loads(Path(paths["result_out"]).read_text())["status"] == "truncated-stream"`.

## Completion

- [x] 8. Run `python3 -m pytest scripts/test_opencode_delegate.py -q` and confirm green. Do NOT
  commit. Emit a short completion summary noting the new function, the classify precedence, and that
  the full delegate test file passes.
