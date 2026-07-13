# Recon: delegation sites for `scripts/opencode_delegate.py`

Read-only inventory of every `opencode run` delegation site across the OpenSpec skills, produced
to spec the wiring for a Python CLI that mechanizes the hand-rolled post-processing. Line numbers
are anchors into the files as they stood at recon time (2026-07-13); re-grep before relying on them
if the files have since been edited.

Files inventoried:
- `.claude/skills/openspec-propose/SKILL.md`
- `.claude/skills/openspec-apply-change/SKILL.md`
- `.claude/skills/openspec-verify-change/SKILL.md`
- `.claude/skills/openspec-archive-change/SKILL.md`
- `.claude/skills/openspec-explore/SKILL.md`
- `.claude/skills/_shared/delegation-harness.md`
- `AGENTS.md` (SMALL premise pass)

Eight distinct delegation sites were found (not seven — verify's behavioral pass and lens pass are
separate sites with separate output files, and verify's fix-executor is its own site distinct from
apply's apply-executor invocation, even though both use the same agent/model).

---

## 1. propose | reviewer

**File / lines:** `.claude/skills/openspec-propose/SKILL.md:110-227` (step 4c). Invocation at
`:168-176`. Assert-real at `:187-196`. Failure/salvage at `:201-215`.

**Agent / model / budget:** `openspec-reviewer`, `deepseek/deepseek-v4-pro` (user-overridable).
Budget `780s`, kill-grace `15s` (`timeout -k 15 780`).

**Sync/bg:** **Synchronous.** Explicitly called out in `delegation-harness.md:76`: "Propose's
reviewer call is synchronous (the `opencode run` command blocks until it returns) — no sentinel
needed or present." No EXIT-sentinel appears in this invocation.

**Exact invocation:**
```bash
timeout -k 15 780 opencode run \
   --dir <repoRoot> \
   --agent openspec-reviewer \
   --model deepseek/deepseek-v4-pro \
   --format json \
   "Review the artifact at <changeRoot>/<artifact>.md. ..." \
   > /tmp/review-out.jsonl 2> /tmp/review-err.log < /dev/null
```

**Post-processing (literal commands quoted where the SKILL.md text repeats them; otherwise it
cross-references harness §b):**
- Assert-ran (§b, referenced not re-quoted here): `grep -q "Falling back to default agent" /tmp/review-err.log`; extract text via `grep '"type":"text"' /tmp/review-out.jsonl | tail -1 | jq -r '.part.text'`.
- Reviewer-specific format check (line 189-192): confirm extracted text contains a `## Review Round` heading AND at least one severity marker (🔴/🟡/💡).
- **`proposal.md` only** (line 194-196): also assert a line `PREMISE: AGREE` or `PREMISE: DISSENT` is present.
- On failure (non-zero exit / timeout / no review text), salvage partial text:
  ```bash
  grep '"type":"text"' /tmp/review-out.jsonl | jq -r '.part.text' \
    > /tmp/review-partial.txt 2>/dev/null || true
  ```
  If partial text has ≥1 finding OR ran >120s before kill → re-run once; else escalate to user with partial output, exit code, stderr.
- Freeze ladder (shared, not opencode-specific): append review to `review-log.md`; 🔴-required → fix + mandatory re-review; else freeze (proposal.md additionally gated on `PREMISE: AGREE`).

**Marker/format asserted:** `## Review Round` heading + a severity marker (🔴/🟡/💡); for
`proposal.md`, also `PREMISE: AGREE|DISSENT`.

**Output files:** `/tmp/review-out.jsonl`, `/tmp/review-err.log`, `/tmp/review-partial.txt`
(salvage path only).

---

## 2. apply | apply-executor

**File / lines:** `.claude/skills/openspec-apply-change/SKILL.md:88-215` (Step 6, Claude Code
branch). Invocation at `:101-146`. Failure modes at `:151-215`.

**Agent / model / budget:** `apply-executor`, `deepseek/deepseek-v4-flash` (or user-named
override). Budget `600s`, kill-grace `30s` (`timeout -k 30 600`).

**Sync/bg:** **`run_in_background: true`** — explicit at line 128: "Run this Bash call with
`run_in_background: true`; detect completion via `[ -f /tmp/apply-out.exit ]`."

**Exact invocation:**
```bash
timeout -k 30 600 opencode run \
  --dir <repoRoot> \
  --agent apply-executor \
  --model deepseek/deepseek-v4-flash \
  --format json \
  "Implement the OpenSpec change in <changeRoot>. ..." \
  > /tmp/apply-out.jsonl 2> /tmp/apply-err.log < /dev/null; \
echo "EXIT=$?" > /tmp/apply-out.exit
```

**Post-processing (literal commands quoted from SKILL.md):**
- Completion detection: `[ -f /tmp/apply-out.exit ]` (bounded sleep loop or bg-completion notification).
- Assert-ran: `grep` `/tmp/apply-err.log` for `Falling back to default agent`.
- Extract completion report:
  ```bash
  grep '"type":"text"' /tmp/apply-out.jsonl | tail -1 | jq -r '.part.text'
  ```
- Blocker-vs-give-up discrimination (grepped against the **extracted text**, never the raw jsonl,
  to avoid false-positiving on the executor's own tool-read of this SKILL.md's heading):
  ```bash
  extracted_text=$(grep '"type":"text"' /tmp/apply-out.jsonl | tail -1 | jq -r '.part.text' 2>/dev/null) || extracted_text=""
  if echo "$extracted_text" | grep -q "### NON-CONVERGENCE BLOCKER" 2>/dev/null \
     || grep -q "### NON-CONVERGENCE BLOCKER" /tmp/apply-err.log 2>/dev/null; then
    echo "DECLARED_BLOCKER"
  else
    echo "OPAQUE_GIVE_UP"
  fi
  ```
- **Success is judged from disk**, not the report: every task in `tasks.md` is `[x]` AND report
  declares no unresolved blocker. Operational crash = non-zero exit (124/137 included),
  empty/unparseable stdout, or the fallback-warning match.
- Failure ladder: operational crash → retry once (tight brief) → 2nd crash → Sonnet subagent
  fallback (`Agent` tool, `subagent_type: "apply-executor"`). Declared blocker → orchestrator
  triage (brief gap / artifact gap / model-capability gap), never reflexive Sonnet. Opaque give-up
  → immediate Sonnet fallback, no retry.

**Marker/format asserted:** non-empty, non-fallback completion summary; optional
`### NON-CONVERGENCE BLOCKER` heading (failure marker, not a success verdict — apply-executor
emits no discriminable "verdict" token on success).

**Output files:** `/tmp/apply-out.jsonl`, `/tmp/apply-err.log`, `/tmp/apply-out.exit`.

---

## 3. verify | fix-executor

**File / lines:** `.claude/skills/openspec-verify-change/SKILL.md:17-33` (defect/failure-modes
preamble, "Fix-redelegation mechanics" and "Escalation rungs" subsections).

**Agent / model / budget:** `apply-executor` (same agent/role as the apply site, re-delegated with
a self-contained fix-spec instead of the whole `tasks.md`), `deepseek/deepseek-v4-flash`. Budget
`600s`, kill-grace `30s` (`timeout -k 30 600`) — "a scoped single-defect fix has a 10-minute budget
matching the apply/archive floor."

**Sync/bg:** **Background** — uses the EXIT-sentinel pattern (`; echo "EXIT=$?" > /tmp/fix-out.exit`,
detect via `[ -f /tmp/fix-out.exit ]`), which per harness §d is exclusive to
`run_in_background: true` calls.

**Exact invocation (given inline, single line, in SKILL.md:26):**
```bash
timeout -k 30 600 opencode run --dir <repoRoot> --agent apply-executor \
  --model deepseek/deepseek-v4-flash --format json <fix-spec> \
  > /tmp/fix-out.jsonl 2> /tmp/fix-err.log < /dev/null
```

**Post-processing:**
- Sentinel: `; echo "EXIT=$?" > /tmp/fix-out.exit`; detect via `[ -f /tmp/fix-out.exit ]`.
- Assert-ran per harness §b (grep stderr for fallback, extract `part.text` via `jq`, confirm
  parseable) — same generic pattern, not re-quoted with fix-specific paths in this file.
- **One attempt only.** Escalate to Sonnet subagent on (a) operational failure (crash/no usable
  output) or (b) quality failure — the orchestrator's own re-verification (from step 1) still
  finds the defect or a new one.
- Explicit caveat (line 27): scoped fix runs have "repeatedly completed their work and still
  exited 1 at session teardown" — judge success from disk (`git diff`, tests), **not** the exit
  code alone.

**Marker/format asserted:** none specific to fix-executor beyond the generic §b assert-ran check
(no completion-format marker is asserted here) — success/failure is judged by the orchestrator
re-running its own behavioral review (Steps 4-8) against disk state, not by parsing a token in the
fix-executor's output.

**Output files:** `/tmp/fix-out.jsonl`, `/tmp/fix-err.log`, `/tmp/fix-out.exit`.

---

## 4. verify | behavioral pro pass (MEDIUM and COMPLEX)

**File / lines:** `.claude/skills/openspec-verify-change/SKILL.md:35-96` (Multi-model passes
section). Invocation at `:61-66`. Prompt text at `:77-90`.

**Agent / model / budget:** `openspec-verifier` (agent default model per
`.opencode/agents/openspec-verifier.md` is `deepseek/deepseek-v4-flash`, but this pass explicitly
overrides `--model deepseek/deepseek-v4-pro`; `bash`: destructive-command denylist, catch-all
allow; `edit: deny`). Budget `780s`, kill-grace `15s` (`timeout -k 15 780`).

**Sync/bg:** **Background** — EXIT-sentinel appended directly in the one-liner.

**Exact invocation:**
```bash
timeout -k 15 780 opencode run --dir <repoRoot> --agent openspec-verifier \
  --model deepseek/deepseek-v4-pro --format json "<behavioral verifier prompt>" \
  > /tmp/verify-pro-out.jsonl 2> /tmp/verify-pro-err.log < /dev/null ; echo "EXIT=$?" > /tmp/verify-pro-out.exit
```

**Post-processing:**
- Assert real verifier ran (§b, generic): grep stderr for fallback; extract `part.text` via `jq`;
  confirm parseable.
- Format check (line 134-137): confirm extracted output contains a `## Verify Pass` heading AND a
  `VERDICT:` line.
- Findings are **leads to confirm from disk** (`git diff`, re-run tests/output) — orchestrator may
  overrule a demonstrably false finding but must record rationale.
- Gate semantics (lines 143-149): hard gate. `VERDICT: NEEDS REVISION` (confirmed from disk) → fix
  via the existing fix-executor path (site 3 above) → re-run this pass and every pass after it
  (never the ones before). Loop bound: 3 fix cycles on the **same** pass without clearing →
  escalate to operator with accumulated verdicts.

**Marker/format asserted:** `## Verify Pass — <model-id>` heading; `VERDICT: READY` or exactly
`VERDICT: NEEDS REVISION`; a `### Defects` section that is **always present** (uses `- None` when
clean).

**Output files:** `/tmp/verify-pro-out.jsonl`, `/tmp/verify-pro-err.log`, `/tmp/verify-pro-out.exit`.

---

## 5. verify | lens pass (flash, COMPLEX only)

**File / lines:** same file, invocation at `:68-73`. Lens prompt subsection at `:92-130`
(test-quality lens default, data-scale lens alternative, selection rule at `:128`).

**Agent / model / budget:** `openspec-verifier`, `deepseek/deepseek-v4-flash` (this pass matches
the agent's own default model — no override needed, though the invocation still names it
explicitly). Budget `780s`, kill-grace `15s` (`timeout -k 15 780`) — "same budget" as the pro pass.

**Sync/bg:** **Background** — EXIT-sentinel appended directly.

**Exact invocation:**
```bash
timeout -k 15 780 opencode run --dir <repoRoot> --agent openspec-verifier \
  --model deepseek/deepseek-v4-flash --format json "<lens prompt>" \
  > /tmp/verify-lens-out.jsonl 2> /tmp/verify-lens-err.log < /dev/null ; echo "EXIT=$?" > /tmp/verify-lens-out.exit
```

**Post-processing:** identical pattern to site 4 (§b assert-ran, `## Verify Pass` + `VERDICT:`
check, disk-confirm, hard-gate/re-run-forward semantics). Diff from the pro pass: this pass is
**diff-scoped** — not required to re-run the full suite — and its lens choice (test-quality vs
data-scale) plus a one-line rationale must be recorded in `review-log.md`. Each lens prompt also
directs the verifier to FIRST run the corresponding deterministic detector
(`checks.py --check test-quality` or `checks.py --check data-scale`) and confirm its findings from
disk before applying residual judgment.

**Marker/format asserted:** same as site 4 — `## Verify Pass` heading + `VERDICT:` line +
always-present `### Defects`.

**Output files:** `/tmp/verify-lens-out.jsonl`, `/tmp/verify-lens-err.log`, `/tmp/verify-lens-out.exit`.

---

## 6. archive | archive-executor

**File / lines:** `.claude/skills/openspec-archive-change/SKILL.md:90-200` (Step 5). Invocation at
`:137-157`. Failure ladder + recovery at `:186-232`.

**Agent / model / budget:** `archive-executor`, `deepseek/deepseek-v4-pro`. Budget `600s`,
kill-grace `30s` (`timeout -k 30 600`).

**Sync/bg:** **`run_in_background: true`** — explicit at line 163: "run this Bash call with
`run_in_background: true`; detect completion via `[ -f /tmp/archive-out.exit ]`." Note (harness
§d, line 78-80): archive's executor was retrofitted to carry the EXIT-sentinel to match the other
three delegating skills' contract.

**Exact invocation:**
```bash
timeout -k 30 600 opencode run \
  --dir <repoRoot> \
  --agent archive-executor \
  --model deepseek/deepseek-v4-pro \
  --format json \
  "Archive the OpenSpec change. changeRoot: <changeRoot>. ..." \
  > /tmp/archive-out.jsonl 2> /tmp/archive-err.log < /dev/null; \
echo "EXIT=$?" > /tmp/archive-out.exit
```

**Post-processing:**
- Completion detection: `[ -f /tmp/archive-out.exit ]`.
- Assert-ran (§b, generic): grep stderr for `Falling back to default agent`; extract `part.text`
  via `jq`; confirm parseable → operational crash if empty/unparseable.
- **Success judged from disk**, not the report: `<archivePath>/` exists on disk AND
  `knowledge/STATUS.md` / `knowledge/decisions/INDEX.md` / `knowledge/questions/INDEX.md` contain
  new reconciled content AND report declares no unresolved blocker.
- Failure ladder restores a pre-handoff git checkpoint (Step 5.0) **before** any retry/fallback:
  ```bash
  git reset --hard HEAD
  git clean -fd <planningHome.changesDir>/archive/YYYY-MM-DD-<name>
  ```
  Operational crash → restore baseline → retry once → 2nd crash → restore baseline → Sonnet
  subagent fallback (`subagent_type: "archive-executor"`). Non-crash failure → restore baseline →
  immediate Sonnet fallback (no retry).

**Marker/format asserted:** none — no completion-format token is asserted for archive-executor's
own report; success is entirely disk-state-driven (archive dir existence + doc-content diff),
which is a materially different post-processing shape from the other executors.

**Output files:** `/tmp/archive-out.jsonl`, `/tmp/archive-err.log`, `/tmp/archive-out.exit`.

---

## 7. explore | direction gate

**File / lines:** `.claude/skills/openspec-explore/SKILL.md:16-49` (advancement steps 1-5).
Invocation at `:22-33`.

**Agent / model / budget:** `openspec-reviewer`, `deepseek/deepseek-v4-pro`. Budget `780s`,
kill-grace `15s` (`timeout -k 15 780`).

**Sync/bg:** **Synchronous** — explicit at line 34: "This is a **synchronous** call (blocks until
return)." No EXIT-sentinel in the invocation, consistent with harness §d's applicability list
(which does not name explore).

**Exact invocation:**
```bash
timeout -k 15 780 opencode run \
  --dir <repoRoot> \
  --agent openspec-reviewer \
  --model deepseek/deepseek-v4-pro \
  --format json \
  "Review the explore brief at plans/<slug>/explore-brief.md. \
   This is a premise review — assess the direction. Emit a \
   ### Premise Verdict block (PREMISE: AGREE|DISSENT)." \
  > /tmp/explore-review-out.jsonl 2> /tmp/explore-review-err.log < /dev/null
```

**Post-processing:**
- Assert-ran (§b): grep stderr for `Falling back to default agent`; confirm output contains
  `### Premise Verdict` heading.
- Extract verdict block from stdout (the reviewer is `edit: deny`, so it can only report), write to
  `plans/<slug>/premise-review.md`.
- Salvage rule (same as propose): on timeout/crash, extract partial text; if ≥1 finding or >120s
  elapsed → re-run once; else escalate. On salvage, mark the written file `PARTIAL`.
- DISSENT handling: present cited concerns via AskUserQuestion (re-think / re-scope /
  override-to-proceed); on override, append `### Resolution` with `OVERRIDE: proceed — <rationale>`
  to `premise-review.md`.

**Marker/format asserted:** `### Premise Verdict` heading containing `PREMISE: AGREE` or
`PREMISE: DISSENT`.

**Output files:** `/tmp/explore-review-out.jsonl`, `/tmp/explore-review-err.log` (transient); durable
output `plans/<slug>/premise-review.md`.

---

## 8. SMALL | premise reviewer (flash)

**File / lines:** `AGENTS.md:188-231` (SMALL tier bullet, "SMALL premise pass" subsection).
Invocation at `:205-215`.

**Agent / model / budget:** `openspec-reviewer`, `deepseek/deepseek-v4-flash` (flash, not pro —
this is the one reviewer invocation that downgrades tier for a SMALL change). Budget `780s`,
kill-grace `15s` (`timeout -k 15 780`), per the harness §e "SMALL | premise reviewer (flash)" row.

**Sync/bg:** **Synchronous** (inferred, not restated as a caveat in AGENTS.md the way propose/explore
call it out explicitly) — no EXIT-sentinel appears in the invocation, and harness §d's
`run_in_background: true` applicability list explicitly excludes this call (it names only apply
executor, archive executor, verify's fix-executor, and verify's two verifier passes). This is the
same shape as the propose and explore reviewer calls.

**Exact invocation:**
```bash
timeout -k 15 780 opencode run \
  --dir <repoRoot> \
  --agent openspec-reviewer \
  --model deepseek/deepseek-v4-flash \
  --format json \
  "Review the plan at <planPath>. This is a SMALL change plan — NOT a \
   structured proposal.md. Emit a ### Premise Verdict block (PREMISE: \
   AGREE|DISSENT) assessing problem/root-cause/solution." \
  > /tmp/small-premise-out.jsonl 2> /tmp/small-premise-err.log < /dev/null
```

**Post-processing:** **Notably, AGENTS.md does not re-quote the literal grep/jq extraction
command here** — it only says (line 219) "The orchestrator extracts the `### Premise Verdict` block
from stdout and writes it to `premise-review.md` (in the plan dir)," implicitly deferring to the
same harness §b mechanics used everywhere else. Salvage identical to explore/propose: on
timeout/crash, if partial output has ≥1 finding or >120s elapsed → re-run once; else escalate;
partial written to `premise-review.md` marked `PARTIAL`. Verdict routing differs from explore only
in where the DISSENT surfaces (folded into the operator's tier+plan confirmation prompt, or — under
an autonomy grant — still escalated because the grant does not cover overriding a premise dissent).

**Marker/format asserted:** `### Premise Verdict` heading (PREMISE: AGREE|DISSENT) — identical
contract to explore's direction gate and propose's premise check.

**Output files:** `/tmp/small-premise-out.jsonl`, `/tmp/small-premise-err.log` (transient); durable
output `premise-review.md` in the plan dir.

---

## SUMMARY TABLE

| # | File | Phase / call | Agent | Model | Budget / grace | Sync\|bg | Extraction cmd | Marker asserted | Ledger fields available at this call site |
|---|------|--------------|-------|-------|-----------------|----------|-----------------|------------------|---------------------------------------------|
| 1 | openspec-propose/SKILL.md:168-176 | propose \| reviewer | openspec-reviewer | deepseek-v4-pro | 780s / 15s | **sync** | `grep '"type":"text"' out.jsonl \| tail -1 \| jq -r '.part.text'` | `## Review Round` + severity marker; proposal.md also `PREMISE:` line | agent✓ model✓ phase✓ change✓(changeRoot known) duration✗(not timestamped) exit✓($? of blocking call) fallback✓(grep) verdict✓(severity+premise) retry~(ladder-defined, not emitted) |
| 2 | openspec-apply-change/SKILL.md:107-120 | apply \| apply-executor | apply-executor | deepseek-v4-flash | 600s / 30s | **bg** (EXIT-sentinel) | `grep '"type":"text"' out.jsonl \| tail -1 \| jq -r '.part.text'` | non-empty summary; optional `### NON-CONVERGENCE BLOCKER` (failure only) | agent✓ model✓ phase✓ change✓ duration✗ exit✓(sentinel file) fallback✓(grep) verdict✗(no success token; disk-judged) retry~ |
| 3 | openspec-verify-change/SKILL.md:26 | verify \| fix-executor | apply-executor (re-delegated) | deepseek-v4-flash | 600s / 30s | **bg** (EXIT-sentinel) | same §b pattern (not re-quoted in-file) | none (disk-judged only) | agent✓ model✓ phase✓ change✓ duration✗ exit✓(sentinel, but noted unreliable — "exits 1 at teardown even on success") fallback✓ verdict✗ retry✓(explicit "one attempt" rule) |
| 4 | openspec-verify-change/SKILL.md:63-65 | verify \| behavioral pro pass | openspec-verifier | deepseek-v4-pro | 780s / 15s | **bg** (EXIT-sentinel) | same §b pattern | `## Verify Pass` heading + `VERDICT: READY\|NEEDS REVISION` + always-present `### Defects` | agent✓ model✓ phase✓ change✓ duration✗ exit✓(sentinel) fallback✓ verdict✓(VERDICT: line) retry✓(3-cycle loop bound explicit) |
| 5 | openspec-verify-change/SKILL.md:70-72 | verify \| lens pass (flash, COMPLEX only) | openspec-verifier | deepseek-v4-flash | 780s / 15s | **bg** (EXIT-sentinel) | same §b pattern | same as #4 + lens choice recorded in review-log.md | same as #4, plus lens-name is an extra ledger-worthy field not in the base 9 |
| 6 | openspec-archive-change/SKILL.md:137-157 | archive \| archive-executor | archive-executor | deepseek-v4-pro | 600s / 30s | **bg** (EXIT-sentinel) | `grep '"type":"text"' out.jsonl \| tail -1 \| jq -r '.part.text'` (via §b) | none (disk-judged: archivePath exists + doc content) | agent✓ model✓ phase✓ change✓ duration✗ exit✓(sentinel) fallback✓ verdict✗ retry~(ladder includes a git-checkpoint restore step other sites lack) |
| 7 | openspec-explore/SKILL.md:24-32 | explore \| direction gate | openspec-reviewer | deepseek-v4-pro | 780s / 15s | **sync** | implied §b pattern (not re-quoted) | `### Premise Verdict` (PREMISE: AGREE\|DISSENT) | agent✓ model✓ phase✓ change~(slug, not changeRoot — pre-change) duration✗ exit✓($?) fallback✓ verdict✓ retry~ |
| 8 | AGENTS.md:206-214 | SMALL \| premise reviewer (flash) | openspec-reviewer | deepseek-v4-flash | 780s / 15s | **sync** (inferred — excluded from §d's bg list, no sentinel in the block) | implied §b pattern (not re-quoted — AGENTS.md is the one site that doesn't even paraphrase the jq command) | `### Premise Verdict` (PREMISE: AGREE\|DISSENT) | agent✓ model✓ phase✓ change✓(planPath) duration✗ exit✓($?) fallback✓ verdict✓ retry~ |

Legend: ✓ = directly extractable from the existing post-processing artifacts at that call site.
✗ = not currently captured by anything in the documented mechanism (would need the wrapper to add
it — e.g. `duration` needs the wrapper to timestamp start/end itself, since no skill currently
does). ~ = governed by a documented ladder/rule but not emitted as a discrete data value at the
call site (a wrapper would need to track it explicitly, e.g. a retry counter across invocations of
the same phase in the same session).

---

## `.gitignore` — is `output/` untracked?

Yes. `.gitignore` (repo root) contains:
```
# Deterministic check/fact artifacts (untracked, disposable, regenerated per run)
output/
/run-manifest.json
```
So `output/delegation-log.jsonl` would be **untracked and gitignored** under the existing
convention — the same bucket as `output/checks/<date>/` from the `run-audit` skill. This is worth
flagging as a design tension for the parent change: the existing `output/` comment frames its
contents as "disposable, regenerated per run," which is a different durability contract than a
cumulative delegation ledger (append-only history across sessions) would want. If the ledger is
meant to persist across sessions/commits, either (a) it needs its own gitignore carve-out or a path
outside `output/`, or (b) the ledger's own durability model needs to be explicitly "disposable,
locally regenerable" (e.g. reconstructed from `/tmp/*-out.jsonl` + `notes.md`/`review-log.md`
records that already ARE committed durably per-change).

---

## Surprises / notes for the wiring spec

1. **Eight sites, not seven.** Verify alone contributes three distinct sites (fix-executor,
   behavioral pro pass, lens pass) with three separate output-file triads
   (`fix-out.*` / `verify-pro-out.*` / `verify-lens-out.*`) — a naive per-skill mapping would
   undercount.
2. **Three different "success" evidence shapes**, not one uniform marker:
   - **Verdict-token sites** (propose reviewer, verify pro/lens, explore, SMALL): a literal
     grep-able string (`## Review Round` + severity glyphs, `## Verify Pass` + `VERDICT:`,
     `### Premise Verdict` + `PREMISE:`).
   - **Disk-state-judged sites** (apply-executor, archive-executor, fix-executor): no success
     token at all — success is `tasks.md` all `[x]` / archive dir + doc diffs / re-run
     tests+`git diff`. A wrapper that only watches for a "marker string" will silently misjudge
     these three as failures unless it also has a disk-state check hook.
   - **Failure-only marker** (apply-executor's `### NON-CONVERGENCE BLOCKER`): present exclusively
     on a specific failure mode, not a success/failure discriminator by itself.
3. **Sync vs background is asymmetric and easy to get backwards.** The four reviewer-role calls
   (propose, explore, SMALL, and — by extension — none of the verifier calls) are synchronous with
   no sentinel; the four executor/verifier-role calls (apply, fix, archive, verify pro, verify
   lens — five, actually, all EXIT-sentinel) are background. Harness §d's applicability list is the
   authoritative source: "apply executor, archive executor, verify's fix-executor, and verify's
   verifier passes (behavioral pro pass + COMPLEX-only lens flash pass)" — five bg call **sites**
   (fix-executor + 2 verifier passes + apply + archive), the other three (propose, explore, SMALL)
   are sync by omission from that list plus the explicit sync callouts in propose/explore.
4. **AGENTS.md's SMALL premise pass (site 8) is the least-specified of the eight** — it's the only
   site that doesn't even paraphrase the jq/grep extraction command inline, just says "the
   orchestrator extracts... and writes it." Everything else at least gestures at harness §b. If the
   wrapper CLI standardizes extraction, this site benefits most since today it has zero
   in-document command to drift from (nothing to be inconsistent against, but also nothing to
   verify the current hand-rolled practice against).
5. **`fix-executor` (site 3) has a documented exit-code lie**: "scoped fix runs have repeatedly
   completed their work and still exited 1 at session teardown." Any wrapper that ledgers `exit`
   as authoritative for this site needs to know this is a known-unreliable signal here specifically
   — success must be re-derived from disk (`git diff`, tests), which is a per-site exception the
   wrapper's design needs to carry, not just a blanket "trust exit code" rule.
6. **The lens pass (site 5) carries an extra ledger-worthy field not in the requested 9**: which
   lens was selected (`test-quality` vs `data-scale`) plus the one-line rationale required to be
   recorded in `review-log.md`. Worth deciding whether the wrapper's ledger schema should have a
   `lens` field or leave that to the free-text notes.
7. **Archive is the only site with a recovery/rollback step wired into its failure ladder**
   (`git reset --hard HEAD` + scoped `git clean -fd <archivePath>`) — a wrapper's failure-ladder
   abstraction can't be uniform across all eight sites; archive's ladder does strictly more than
   apply's or fix's.
8. **The propose reviewer prompt varies by artifact type** (adds a premise-verdict request only for
   `proposal.md`, and conditionally a D10 drift-check clause when a verified `explore-brief.md`
   exists) — the same underlying invocation shape produces three prompt variants, so the wrapper's
   "phase/call" identity for site 1 isn't quite one fixed prompt template the way the other seven
   are.
