# tasks — delegation-wrapper-telemetry (OW-7)

Apply-phase edits only. Acceptance criteria + design rationale: `notes.md`. Delegation-site inventory
(file:line anchors, exact current post-processing, the 3 success-evidence shapes): **`recon-delegation-sites.md`**
— read it before Group 3. Spec delta authored under `specs/delegation-wrapper/` — implement to match it,
do NOT re-author it. **Tests pin exact behavior.** Re-grep the recon anchors before editing (files may
have shifted since recon).

## Group 1 — `scripts/opencode_delegate.py` (the ingest wrapper)

- [x] **T1 — Module + pure helpers.** Create `scripts/opencode_delegate.py` (executable, `#!/usr/bin/env python3`,
  `from __future__ import annotations`). Implement these PURE functions (no subprocess, no I/O beyond
  what's stated) so tests can exercise them directly:
  - `extract_text(out_jsonl_text: str) -> str | None` — parse the stdout as JSON-lines; for each line
    that parses to an object, collect it if `obj.get("type") == "text"`. Return the LAST such object's
    `obj["part"]["text"]` (mirror the existing `grep '"type":"text"' | tail -1 | jq -r '.part.text'`
    chain). Tolerate non-JSON / blank lines (skip them). Return `None` if no text part found or the
    text is empty/whitespace.
  - `detect_fallback(err_text: str) -> bool` — `True` iff `err_text` contains the substring
    `Falling back to default agent`.
  - `parse_exit_file(text: str) -> int | None` — given an EXIT-sentinel file body like `EXIT=124`,
    return the int after `EXIT=`; `None` if unparseable.
  - `assert_markers(text: str | None, markers: list[str]) -> bool` — `True` iff `text` is not None and
    every regex in `markers` matches (via `re.search`, `re.MULTILINE`). Empty `markers` → `True`.
    **Catch `re.error` per marker** (a malformed `--require-marker` regex → treat that marker as
    not-matched, do NOT raise — the wrapper is shared by all 8 sites and MUST never crash on bad
    input; same discipline T3 requires for `--verdict-regex`).
  - `extract_verdict(text: str | None, regex: str | None) -> str | None` — if `regex` and `text`, return
    `m.group(1)` when the pattern has a group else `m.group(0)`, using `re.search(..., re.MULTILINE)`;
    else `None`.
  - `classify_status(exit_code: int | None, fallback: bool, text: str | None, marker_ok: bool) -> str`
    — precedence: `fallback`→`"fallback"`; `exit_code in (124, 137)`→`"timeout"`; `text` empty/None →
    `"crash"`; `not marker_ok`→`"marker-missing"`; else `"ok"`. **Note the exit-code lie:** a nonzero
    `exit_code` NOT in (124,137) with present text and marker_ok does NOT downgrade from `"ok"` — the
    raw exit is recorded separately, not used to force `crash`. **`exit_code=None`** (unreadable
    exit-file) is likewise not in (124,137), so it falls through to the text/marker checks — an
    all-clean run with an unreadable exit-file classifies `ok`; a text-less one classifies `crash`.
  - `best_effort_duration(out_jsonl_text: str) -> float | None` — if parseable text-part objects carry
    a numeric `time`/`timestamp` (top-level or under `part`), return `last_ts - first_ts` (seconds,
    coercing ms→s if values look like epoch-ms, i.e. > 1e12); else `None`. Keep it defensive — ANY
    parse issue returns `None`. (Best-effort per notes A2. **Assumption:** the exact opencode jsonl
    timestamp field name/format is uncited — add a code comment flagging this so a maintainer can tell
    "no timestamp in output" from "parse bug"; probe the real format at verify.)
  - `build_ledger_record(*, ts: str, phase, agent, model, change, exit_code, fallback, status,
    marker_ok, verdict, retry, duration_s, tags: dict) -> dict` — assemble the dict with EXACTLY these
    keys: `ts, phase, agent, model, change, exit, fallback, status, marker_ok, verdict, retry,
    duration_s`, then merge `tags` (tags never overwrite a core key — if a tag collides, prefix it
    `tag_`). `ts` is a REQUIRED parameter (injected — do NOT call a clock inside this function; tests
    depend on determinism).

- [x] **T2 — CLI + main.** Implement `main(argv=None) -> int` with argparse:
  `--phase` (req), `--agent` (req), `--model` (req), `--change` (req), `--out` (req: stdout jsonl path),
  `--err` (req: stderr log path), `--exit` (int) XOR `--exit-file` (path; body `EXIT=<n>`) — exactly one
  required, `--require-marker` (append, repeatable, regex), `--verdict-regex` (str), `--retry` (int,
  default 0), `--tag` (append, repeatable, `k=v`), `--ledger` (path, default
  `<repo-root>/output/delegation-log.jsonl`), `--repo-root` (path, default = parent of script dir),
  `--text-out` (path, default `<out>.text.txt`), `--result-out` (path, default `<out>.result.json`),
  `--quiet` (flag).
  Flow: read `--out` and `--err` files (missing/empty file → treat contents as `""`). Resolve exit code
  from `--exit` or by reading+`parse_exit_file(--exit-file)`. Compute `fallback`, `text`, `marker_ok`
  (over `--require-marker`), `verdict`, `status`, `duration_s`. Write `text` (or empty string) to
  `--text-out`; write the result dict `{phase, status, exit, fallback, text_present, marker_ok, verdict,
  duration_s, text_path, out, err}` as JSON to `--result-out`. Parse `--tag k=v` into a dict (split on
  first `=`; a malformed tag with no `=` → argparse error). Build the ledger record with
  `ts=datetime.now(timezone.utc).isoformat()` (real clock is correct here — this is a live script, not
  a workflow; and it is NOT a test file so the `unfrozen-clock` detector does not apply). `mkdir -p` the
  ledger's parent, then append the record as one `json.dumps(...)+"\n"` line (open `"a"`, write, flush).
  Print `DELEGATE_RESULT: phase=<phase> status=<status> exit=<exit> fallback=<yes|no> marker_ok=<yes|no> verdict=<verdict-or-->`
  to stdout; unless `--quiet`, also print the extracted text (or `<no text extracted>`). Return `0` iff
  `status == "ok"`, else `1`.

- [x] **T3 — Robustness.** Never raise on malformed inputs: a missing `--out` file, non-JSON lines, an
  unreadable `--exit-file`, a bad `--verdict-regex`, OR a bad `--require-marker` (catch `re.error` on
  EACH regex use → verdict: no verdict; marker: treat that marker as not-matched; log a one-line
  warning to stderr, do not crash) must all degrade gracefully to a recorded status, never a
  traceback. The wrapper is post-processing infrastructure shared by all 8 sites — a crash here would
  break every delegation.

## Group 2 — `scripts/test_opencode_delegate.py` (behavioral contract)

- [x] **T4 — Pure-function unit tests.** Cover, with literal fixture strings:
  - `extract_text`: multi-line jsonl with several `type:"text"` parts → returns the LAST; interleaved
    non-text parts + blank/non-JSON lines skipped; no text part → `None`; whitespace-only text → `None`.
  - `detect_fallback`: err containing the phrase → `True`; clean err → `False`.
  - `parse_exit_file`: `"EXIT=124\n"` → 124; `"EXIT=0"` → 0; garbage → `None`.
  - `assert_markers`: all-present → `True`; one-missing → `False`; empty list → `True`; `text=None` → `False`;
    a malformed regex (e.g. `"("`) → does NOT raise, returns `False` for that marker (T3 grace).
  - `extract_verdict`: `r"PREMISE: (AGREE|DISSENT)"` on text with `PREMISE: AGREE` → `"AGREE"`;
    grouped vs ungrouped pattern; no match → `None`; `regex=None` → `None`.
  - `classify_status`: table across `(exit, fallback, text, marker_ok)`:
    `(0,False,"x",True)→ok`; `(0,True,"x",True)→fallback`; `(124,False,"x",True)→timeout`;
    `(137,False,"x",True)→timeout`; `(0,False,None,True)→crash`; `(0,False,"x",False)→marker-missing`;
    **`(1,False,"x",True)→ok`** (exit-code lie); `(1,True,None,True)→fallback` (precedence);
    `(None,False,"x",True)→ok` and `(None,False,None,True)→crash` (unreadable exit-file →
    `parse_exit_file` returns `None`; `None` is not in `(124,137)` so it falls through to the
    text/marker checks — call this out in the T1 contract so it is not implicit).
  - `build_ledger_record`: has exactly the 12 core keys + merged tags; a tag colliding with a core key
    is stored as `tag_<k>`; `ts` echoed verbatim; result is `json.dumps`-able.

- [x] **T5 — main() pipeline test (temp fixtures, no opencode).** Write a temp dir with an
  `out.jsonl` (2 text parts + a non-text part), an `err.log` (clean), and an `exit` file (`EXIT=0`).
  Run `main([...])` with `--phase verify-pro --agent openspec-verifier --model deepseek/deepseek-v4-pro
  --change demo --out … --err … --exit-file … --require-marker "VERDICT:" --verdict-regex "VERDICT: (READY|NEEDS REVISION)"
  --ledger <tmp>/led.jsonl --text-out … --result-out …`. Assert: return 0; `--text-out` holds the LAST
  text; `--result-out` JSON has `status=="ok"`, `verdict=="READY"` (given the fixture text carries
  `VERDICT: READY`); the ledger file has exactly ONE line that `json.loads` to a dict with the 12 core
  keys and `phase=="verify-pro"`. Add a SECOND `main()` run appending to the SAME ledger → assert TWO
  lines (append-only). Add a fallback case: `err.log` containing "Falling back to default agent" →
  `status=="fallback"`, return 1. Add a marker-missing case (`--require-marker "NOPE"`) →
  `status=="marker-missing"`, return 1.

- [x] **T6 — No self-finding.** Ensure the test file freezes/injects any clock it needs (pass fixed
  `ts` to `build_ledger_record`; never call `datetime.now()` in a `test_*` body) so
  `checks.py --check test-quality` reports no `unfrozen-clock` on this file. Use `tmp_path` (pytest) for
  all fixture I/O. Do not mock `opencode_delegate` itself (no self-mock).

## Group 3 — Wire the 8 delegation sites (see `recon-delegation-sites.md`)

For EACH site: leave the literal `timeout -k <grace> <budget> opencode run … < /dev/null > <out> 2> <err> [; echo "EXIT=$?" > <exit>]`
invocation UNCHANGED. Replace ONLY the site's hand-rolled post-processing block (fallback-grep + jq
extraction + marker/format assert + exit-code interpretation) with a single documented
`opencode_delegate.py` call, preserving the site's `--phase/--agent/--model/--change`, its markers, and
its verdict regex. **Keep** each site's failure ladder, salvage/re-run rule, disk-state success
judgment, and (archive) git-checkpoint restore in the prose — the wrapper does not own those. Where a
skill currently cross-references harness §b for the extraction mechanics, repoint that to
"post-processing via `scripts/opencode_delegate.py` (see its `--help` / the harness §b note)".

- [x] **T7 — delegation-harness.md (§b, §d).** In `.claude/skills/_shared/delegation-harness.md`, rewrite
  §b ("Assert the real agent ran") and the §d completion-detection prose so they state that
  fallback-detection, completion-text extraction, status classification, verdict capture, and the
  telemetry-ledger append are performed by `scripts/opencode_delegate.py` (the canonical
  post-processor), fed the run's `--out/--err/--exit|--exit-file`. Keep §a (stdin-close/--dir), §c
  (timeout wrapper), §e (budget table) UNCHANGED — those describe the literal invocation, which stays.
  Add a short "Ledger" note: each post-processed run appends one line to `output/delegation-log.jsonl`
  (untracked, append-only local telemetry). Give ONE canonical example invocation of the wrapper.

- [x] **T8 — Background executor/verifier sites (5).** Rewire the post-processing of, per recon:
  - apply | apply-executor (`openspec-apply-change/SKILL.md`, recon §2): `--phase apply --exit-file /tmp/apply-out.exit`, no marker (disk-judged). Keep the `### NON-CONVERGENCE BLOCKER` discrimination + failure ladder in prose (grep the wrapper's `--text-out`, not raw jsonl).
  - verify | fix-executor (`openspec-verify-change/SKILL.md`, recon §3): `--phase verify-fix --exit-file /tmp/fix-out.exit`, no marker (disk-judged). Keep "one attempt only" + exit-code-lie caveat note.
  - verify | behavioral pro pass (recon §4): `--phase verify-pro --exit-file /tmp/verify-pro-out.exit --require-marker "## Verify Pass" --require-marker "VERDICT:" --verdict-regex "VERDICT: (READY|NEEDS REVISION)"`.
  - verify | lens pass (recon §5, COMPLEX only): `--phase verify-lens --exit-file /tmp/verify-lens-out.exit` + same markers/verdict as pro + `--tag lens=<test-quality|data-scale>`.
  - archive | archive-executor (`openspec-archive-change/SKILL.md`, recon §6): `--phase archive --exit-file /tmp/archive-out.exit`, no marker (disk-judged). Keep the git-restore-before-retry ladder in prose.

- [x] **T9 — Synchronous reviewer sites (3).** Rewire the post-processing of:
  - propose | reviewer (`openspec-propose/SKILL.md`, recon §1): `--phase propose-review --exit $?`
    (synchronous — no exit-file) `--require-marker "## Review Round"` `--require-marker "(🔴|🟡|💡)"`;
    for the `proposal.md` variant also `--verdict-regex "PREMISE: (AGREE|DISSENT)"`. Keep the salvage/
    re-run-once rule and the freeze ladder in prose.
  - explore | direction gate (`openspec-explore/SKILL.md`, recon §7): `--phase explore-gate --exit $?
    --require-marker "### Premise Verdict" --verdict-regex "PREMISE: (AGREE|DISSENT)"`. The durable
    `premise-review.md` write + DISSENT/AskUserQuestion handling stay in prose.
  - SMALL | premise reviewer (`AGENTS.md` SMALL bullet, recon §8): `--phase small-premise --exit $?
    --require-marker "### Premise Verdict" --verdict-regex "PREMISE: (AGREE|DISSENT)"`. This is the
    least-specified site today (AGENTS.md never quoted the jq command) — give it the same explicit
    wrapper call, keeping the PARTIAL-salvage + verdict-routing prose.
  **Note:** `AGENTS.md` is span-replace scaffold-managed — edit only the SMALL premise bash block; do
  not touch surrounding canonical spans.

## Group 4 — Gate

- [x] **T10 — Green gate + self-check.** Run `ruff check --fix` + `ruff format` on
  `scripts/opencode_delegate.py` + `scripts/test_opencode_delegate.py`. Run `bash scripts/check.sh` →
  exit 0 (ruff + format + pytest, incl. the live-tree `knowledge_lint` gate that was RED on the
  `scripts/opencode_delegate.py` HANDOFF citation and now resolves). Run
  `/usr/bin/python3 scripts/checks.py --check test-quality` on this repo and confirm the new test file
  adds NO `unfrozen-clock`/`self-mock` finding (advisory is fine, but the new file should be clean).
  Do NOT commit. Report in the completion summary: the ledger schema keys emitted, and confirmation
  that no skill's literal `timeout -k`/`< /dev/null` invocation line was altered (budget-agreement +
  delegation-safety guards intact).
