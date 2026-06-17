# Tasks — dedup-scaffold (W2: C1 delegation-harness extraction + B3 timeout table)

> MEDIUM tier: this `tasks.md` is the only propose artifact (reviewed by deepseek-v4-pro before
> freeze); acceptance criteria live in `notes.md`. **Extraction, not redesign** — preserve behavior
> byte-for-byte; assemble the canonical doc from the EXACT existing skill text, do not paraphrase.

## 1. Canonical doc — `ai-docs/delegation-harness.md`

- [x] 1.1 Create `ai-docs/delegation-harness.md` as the single source for the `opencode run`
  delegation contract shared by the propose/apply/verify/archive skills. Before writing, diff the four
  current copies (anchors in `explore-brief.md`) and assemble the **most-complete** version of each
  shared element — apply carries the fullest invocation + assert-ran; do not regress to an abbreviated
  copy. Sections, taken verbatim from existing text where they already agree:
  - **(a) Hardened invocation** — `< /dev/null` + `--dir <repoRoot>`; cite the
    `noninteractive-delegation-safety` capability spec for rationale (do NOT duplicate that rationale).
  - **(b) Assert the real agent ran** — `opencode run` exits 0 even on silent fallback; grep stderr for
    `Falling back to default agent`; extract the last `"type":"text"` JSONL record's `part.text`;
    confirm it carries the agent's own output format. Do NOT self-review on failure → escalate.
  - **(c) Bounded wait + surgical kill** — the `timeout` wrapper kills ONLY the process it launched;
    **never** `pkill opencode` / `killall opencode` (other concurrent opencode jobs must survive).
  - **(d) EXIT-sentinel completion detection** — the `echo "EXIT=$?" > …exit` file pattern and the
    "never poll with pgrep / never judge from a mid-run snapshot" rule for detecting real completion.
    **Scope it explicitly:** the sentinel applies ONLY to `opencode run` calls launched with
    `run_in_background: true` (apply executor, verify's verifier passes). A *synchronous* call that
    blocks on the command needs no sentinel — propose's reviewer call is synchronous and correctly has
    none. Note the pre-existing drift: archive backgrounds its executor (`:161`) but its invocation
    omits the sentinel; record this in the reconciliation log and leave it as-is here (extraction, not
    redesign) unless the operator scopes the fix in.
- [x] 1.2 Add a **canonical timeout-budget table** (fixes B3) with columns
  **Phase · Call · `timeout` flags · Budget (s) · Kill-grace · Notes**, one row per delegated call —
  apply 600s, fix-executor 300s (verify), verifier 780s (verify), reviewer 780s (propose), archive 600s.
  Values stay distinct per phase (this only centralizes them). **Kill-grace authority: preserve the
  existing values** (`-k 30` for the longer-running apply/archive executors, `-k 15` for verify/propose)
  — this is extraction, not redesign; do NOT flip a coin or contradict the `reviewer-budget` spec (which
  already codifies the reviewer's `-k 15` / 780s). Just record the per-phase rationale in the Notes
  column and the reconciliation log. Cross-reference (do not duplicate) the `reviewer-budget` spec.
- [x] 1.3 State the carve-out explicitly in the doc: verify's **in-process self-review pass** is a
  Task-tool spawn, NOT `opencode run`, and is therefore exempt from the `< /dev/null` / `--dir`
  hardening (no separate process, no TTY-stdin). A skill citing this doc for an in-process pass must not
  apply (a)/(c).

## 2. Reduce the four skills to a citation + per-phase specifics

For each skill below: replace the inline harness **prose** (invocation-hardening rationale, assert-ran,
bounded-wait/surgical-kill, EXIT-sentinel explanation, and the raw timeout-budget restatements) with a
one-line citation of `ai-docs/delegation-harness.md`, keeping ONLY that phase's specifics. **Use the
explore-brief.md anchor table as the map of exactly which lines to remove from each skill** — it
includes the easy-to-miss variants (verify's abbreviated assert-ran at `:88`, verify's inline
bounded-wait at `:27`). The actual `timeout … opencode run …` **invocation command stays inline** in
every skill (it carries the per-phase agent/model/budget/prompt) — only the surrounding explanatory
prose moves. Do not remove any genuinely phase-specific failure ladder.

- [x] 2.1 `.claude/skills/openspec-apply-change/SKILL.md` — keep: apply-executor agent + flash model,
  600s budget (referencing the table), the **convergence-blocker triage ladder**, the apply prompt.
- [x] 2.2 `.claude/skills/openspec-verify-change/SKILL.md` — keep: fix-executor agent/model + 300s,
  the two openspec-verifier passes + 780s, the **escalate-to-Sonnet** path, and the in-process
  self-review pass (with its hardening carve-out per 1.3) unchanged in intent.
- [x] 2.3 `.claude/skills/openspec-propose/SKILL.md` — keep: openspec-reviewer agent + deepseek-v4-pro
  model + 780s, the re-run-once-vs-escalate salvage logic, the propose prompt.
- [x] 2.4 `.claude/skills/openspec-archive-change/SKILL.md` — keep: archive-executor agent/model + 600s,
  the reconciliation-recovery path, the archive prompt.
- [x] 2.5 For every line removed from a skill, confirm it is either (a) now in the canonical doc, or
  (b) a previously-drifted variant deliberately reconciled to the canonical version. Record **all three**
  reconciliation decisions in `notes.md` — the `-k 30`/`-k 15` kill-grace, the full vs abbreviated
  assert-ran, AND the EXIT-sentinel scope (which calls it applies to + archive's missing sentinel).
  Nothing safety-critical may be silently dropped.

## 3. Manifest — register the new shared doc

- [x] 3.1 Add `ai-docs/delegation-harness.md` to `scripts/scaffold_manifest.txt` in the `# AI docs`
  group (with `fast-track-workflow.md` / `research-fetch-convention.md`), so W6 propagates it
  byte-identical to extrends + psc-monitor.
- [x] 3.2 Confirm the manifest is still honest: run `python scripts/test_sync_scaffold.py` (all pass),
  and verify every manifest-listed path — including the new `ai-docs/delegation-harness.md` — exists in
  the scaffold source (read the manifest, check each path resolves). Do **not** run
  `sync_scaffold.py <target> --check` against a real downstream repo here — extrends/psc-monitor are not
  present in the scaffold tree and the command aborts on a missing/non-`.git` target; the live
  downstream `--check` is a W6 concern. If a `--check` smoke is wanted, run it against a throwaway local
  git repo, not a real downstream.

## 4. Verify the dedup (grep invariants — instruction surface, not runtime code)

- [x] 4.1 The harness **prose** now appears in exactly ONE place. Grep each distinctive string across
  `.claude/skills/` and confirm it resolves only to `ai-docs/delegation-harness.md` (plus the
  `noninteractive-delegation-safety` spec it cites), NOT the four skills:
  `pkill opencode`, `Falling back to default agent`, and `never poll with pgrep` (use this last phrase
  for the EXIT-sentinel prose — do NOT grep `echo "EXIT="`, which legitimately remains in the skills'
  inline invocation commands and would be a false positive).
- [x] 4.2 Every timeout literal (600 / 300 / 780 and the chosen `-k` grace) appears once, in the table;
  the four skills reference the table rather than restating raw numbers (B3 closed).
- [x] 4.3 Read all four skills end-to-end and apply the concrete self-sufficiency test: a primary agent
  reading any one skill must be able, **without opening the canonical doc**, to determine (1) the exact
  `opencode run` invocation to use, (2) how to verify the output, and (3) what to do on failure. If any
  of the three requires opening `delegation-harness.md`, the citation alone is insufficient — that
  skill must keep the invocation command + its per-phase failure ladder inline. Also confirm: no
  behavioral semantics lost in extraction, and the in-process self-review carve-out (1.3) is intact.
