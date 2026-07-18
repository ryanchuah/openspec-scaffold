# Delegation harness — shared `opencode run` contract

The four delegating OpenSpec skills — propose, apply, verify, archive — share this operational
contract for every `opencode run` delegation. Each skill cites this doc and keeps only its own
per-phase invocation command, agent/model/budget, and failure ladder.

---

## (a) Hardened invocation

Every delegated `opencode run` closes stdin (`< /dev/null`) and passes `--dir <repoRoot>`.
See the `noninteractive-delegation-safety` capability spec for the full rationale.

---

## (b) Assert the real agent ran (post-processing via ``scripts/opencode_delegate.py``)

Do this BEFORE trusting any output — `opencode run` exits 0 even on silent agent fallback.

Fallback-detection, completion-text extraction, status classification, verdict capture,
and the telemetry-ledger append are performed by a single deterministic tested script —
**`scripts/opencode_delegate.py`** (the canonical post-processor).  See its ``--help``
for the full contract; this section documents what it does conceptually.

The wrapper is invoked with the run's ``--out`` (stdout JSONL), ``--err`` (stderr log),
and exit source (``--exit`` for synchronous calls or ``--exit-file`` for background
calls).  It:

- Detects silent agent fallback: reads stderr for the literal string
  ``Falling back to default agent`` — if found, the intended agent was **not** loaded.
- Extracts the completion text: parses stdout as JSON-lines, collects every
  ``type:"text"`` part, and returns the **last** one's ``part.text`` (mirroring the
  historical ``grep | tail | jq`` chain, but as a tested Python function).
- Classifies the run status: ``ok``, ``fallback``, ``timeout``, ``crash``,
  ``truncated-stream``, or ``marker-missing`` — respecting the exit-code lie
  (non-zero-but-not-timeout with present text is NOT ``crash``). ``truncated-stream``
  flags a silently-truncated run (stdout JSONL shows more ``step_start`` than
  ``step_finish`` events — an unterminated step), caught on every phase regardless of
  markers; it exits nonzero and routes to the failure ladder like the other non-``ok``
  statuses.
- Asserts optional ``--require-marker`` regex(es) against the extracted text, and
  optionally captures a verdict token via ``--verdict-regex``.
- Appends one JSONL telemetry line to ``output/delegation-log.jsonl`` (see Ledger
  note below).
- Writes the extracted text to ``--text-out`` and a machine-readable result to
  ``--result-out``.
- Exits 0 iff ``status == "ok"``.

Each skill that delegates an ``opencode run`` replaces its hand-rolled
post-processing (fallback-grep, ``jq`` extraction, marker assert, exit-code
interpretation) with one wrapper call, passing the phase-specific
``--require-marker`` / ``--verdict-regex`` flags.  The failure ladder, disk-state
success judgment, and salvage/re-run rules remain in the skill prose — the wrapper
owns neither.

**Conceptual reference** (what the wrapper replaces — the historical hand-rolled
sequence that was identical across all delegating skills):

```bash
grep -q "Falling back to default agent" /tmp/<phase>-err.log
grep '"type":"text"' /tmp/<phase>-out.jsonl | tail -1 | jq -r '.part.text'
```

**Cross-repo `--dir` gotcha (root cause of silent fallback):** `opencode run --agent <name>`
discovers the agent from `.opencode/agents/` **relative to `--dir`**. For cross-repo changes it
is tempting to set `--dir` to the common parent (e.g. `/home/user/Projects`) so the executor can
reach all repos — but that breaks agent discovery: opencode logs `agent "<name>" not found.
Falling back to default agent` and runs the **default** agent. The `--model` flag still applies
(right model, WRONG role prompt), so the run looks fine and even passes gates. This bit the
`lean-boot-context` apply: Slice A ran on the default agent; Slice B, run with `--dir` = the
target repo, loaded the real executor correctly.

For a cross-repo change: set `--dir` to a repo that actually contains `.opencode/agents/<agent>.md`
(scaffold or the target repo). Bash calls inside the agent use absolute paths and are NOT
`--dir`-restricted, so a per-repo `--dir` still lets the executor read/edit sibling repos.
Run **one slice per repo** (`--dir` = that repo) rather than one run at a bare parent.

---

## (c) Bounded wait + surgical kill

Wrap every delegated `opencode run` with `timeout -k <grace> <budget>`. The wrapper kills
**only the opencode process it launched** — other concurrent opencode processes are left untouched
and no children are orphaned (verified). **Never** `pkill opencode` / `killall opencode`: other
opencode processes routinely run, and that would kill them too. A `timeout` kill surfaces as exit
code 124 (or 137 if SIGKILL was needed) — treat as an operational crash in the failure ladder.

See §e for per-phase budgets and kill-grace values.

---

## (d) EXIT-sentinel completion detection

**Applies only to `opencode run` calls launched with `run_in_background: true`** — apply executor,
archive executor, verify's fix-executor, and verify's verifier passes (behavioral pro pass +
COMPLEX-only lens flash pass).

Append `; echo "EXIT=$?" > /tmp/<phase>-out.exit` to the wrapped command. Detect completion by
`[ -f /tmp/<phase>-out.exit ]` in a bounded sleep loop (or simply wait for the harness
background-completion notification); the `timeout` wrapper guarantees the sentinel appears within
~N+grace seconds.

**NEVER poll with `until ! pgrep -f "<pattern>"`** — the pattern self-matches the poller's own
`bash -c` command line, so the loop exits while the run is still going. **Never judge a run from a
mid-execution jsonl snapshot** — deepseek-v4-flash/pro can legitimately take >5 minutes and a short
jsonl mid-run is NORMAL. Conclude crash/timeout ONLY if the exit file shows nonzero (124 = timeout,
137 = SIGKILL), OR no opencode PID remains AND no exit file was ever written (genuine truncation).

**Post-processing note:** once the exit-file exists, the orchestrator invokes
`scripts/opencode_delegate.py` with ``--exit-file /tmp/<phase>-out.exit`` (or
``--exit <int>`` for synchronous calls), together with ``--out`` and ``--err``.
The wrapper reads the exit-file, interprets the exit code via its
`parse_exit_file` helper, and feeds the result into `classify_status` (which
recognizes 124/137 as ``timeout``).

**Ledger.** Each post-processed run appends exactly one JSONL line to
``output/delegation-log.jsonl`` (untracked, append-only, created on demand).
The line carries at minimum: ``ts``, ``phase``, ``agent``, ``model``, ``change``,
``exit``, ``fallback``, ``status``, ``marker_ok``, ``verdict``, ``retry``, and
``duration_s``, plus any ``--tag k=v`` extras.  This is local operational
telemetry — the durable per-change record remains ``review-log.md`` / ``notes.md``.

**Canonical wrapper invocation example** (background site with exit-file):

```bash
scripts/opencode_delegate.py \
  --phase verify-pro --agent openspec-verifier --model deepseek/deepseek-v4-pro --change demo \
  --out /tmp/verify-pro-out.jsonl --err /tmp/verify-pro-err.log \
  --exit-file /tmp/verify-pro-out.exit \
  --require-marker "## Verify Pass" --require-marker "VERDICT:" \
  --verdict-regex "VERDICT: (READY|NEEDS REVISION)" \
  --quiet
```

**Scope notes:**
- **Propose's reviewer call is synchronous** (the `opencode run` command blocks until it returns) —
  no sentinel needed or present. This is correct by design. Synchronous sites use ``--exit $?``
  instead of ``--exit-file``.
- **Archive's executor is launched with `run_in_background: true`** (because reconciliation can run
  several minutes) and its invocation now carries the `echo "EXIT=$?"` sentinel — archive matches
  this §d contract like the other three delegating skills.

---

## (e) Timeout budget table

| Phase | Call | `timeout` flags | Budget (s) | Kill-grace | Notes |
|-------|------|-----------------|------------|------------|-------|
| apply | apply-executor | `-k 30 600` | 600 | 30s | Full `tasks.md` can run several minutes; extra grace reduces SIGKILL risk during a legitimate slow step. |
| archive | archive-executor | `-k 30 600` | 600 | 30s | Multi-step reconciliation; same rationale as apply. |
| verify | fix-executor | `-k 30 600` | 600 | 30s | Scoped single-defect fix; 10-minute floor matches the apply/archive budget. |
| verify | verifier (behavioral pass, pro) | `-k 15 780` | 780 | 15s | Independent verification pass; both platforms use this budget. |
| verify | verifier (lens pass, flash — COMPLEX only) | `-k 15 780` | 780 | 15s | Same budget; COMPLEX-only lens pass. |
| propose | reviewer | `-k 15 780` | 780 | 15s | Per the `reviewer-budget` capability spec — cross-referenced, not duplicated here. |
| explore | direction gate (pro) | `-k 15 780` | 780 | 15s | Keyed by stage because it runs outside the named phases — the explore skill's premise gate on a load-bearing brief. |
| SMALL | premise reviewer (flash) | `-k 15 780` | 780 | 15s | Keyed by tier because it runs outside the named phases — the pre-apply SMALL premise pass. |

The budgets above are extraction-faithful — this table is the single authoritative source for all
phase timeout values. Cross-reference: the propose reviewer's 780s / `-k 15` budget is codified in
the `reviewer-budget` capability spec.

---

## (f) Sanctioned delegation model IDs

| Model ID | Form | Notes |
|----------|------|-------|
| `deepseek/deepseek-v4-pro` | model-flag form (preferred) | Used in `--model` flags |
| `deepseek/deepseek-v4-flash` | model-flag form (preferred) | Used in `--model` flags |
| `deepseek-v4-pro` | bare form | Used in prose descriptions |
| `deepseek-v4-flash` | bare form | Used in prose descriptions |

This table is the single source of truth for the `model-id-agreement` scaffold_lint check. Any
`deepseek[-/]v4[-a-z]*`-shaped token appearing in the live instruction surface (AGENTS.md,
`.claude/skills/**`, `.claude/agents/*`, `.opencode/agents/*`) MUST be one of the four sanctioned
ids above — no other spelling, version drift, or bare suffixless token (e.g. `deepseek`-`v4` with
no tier) is permitted.

---

## (g) Prompt-template shape — variable content last

Every delegated `opencode run` prompt string places its **fixed instruction text first and all
per-change variable substitutions (paths, names, flags) LAST**, so the byte-identical instruction
body forms a shared prefix eligible for DeepSeek prefix-caching across invocations. A variable placed
early zeroes cache credit for every boilerplate word after it, even though that text is identical
across every apply/archive/review call.

The **verifier prompts are the reference shape**: they inline no path at all (`<repoRoot>` rides the
`--dir` flag; `<model-id>` is an output token), so the whole prompt is a shared prefix. The apply,
archive, and reviewer prompts bind their variables in a trailing clause (`… in the change directory:
<changeRoot>.`, or a trailing `key: <value>;` block).

When editing any delegated prompt, keep variables at the tail **and** do not drop any wrapper-asserted
output marker the prompt requests: `### Premise Verdict` + `PREMISE: AGREE|DISSENT` (premise passes)
and `## Verify Pass` + `VERDICT:` + `### Defects` (verifier). (The reviewer's `## Review Round` +
`(🔴|🟡|💡)` markers come from the agent role prompt, not the call string.) Dropping a requested marker
breaks the `scripts/opencode_delegate.py --require-marker` assert at runtime.

---

## Carve-out: verify's in-process self-review

Verify's **in-process self-review pass** is the **orchestrator's own review pass, performed
inline by the primary** (Steps 4–8: "run `git diff` yourself," "re-run the FULL suite yourself") —
it is neither an `opencode run` delegation nor a Task-tool spawn; there is no separate process and
no TTY-stdin. It is therefore **exempt** from the `< /dev/null` / `--dir` hardening (§a) and the
bounded-wait/surgical-kill wrapper (§c) — those exist to harden a *separate delegated process*,
which this pass simply is not. The delegated verifier passes (behavioral pro pass for MEDIUM and COMPLEX; lens flash pass for COMPLEX only, identical on both platforms) use `opencode run` and are NOT exempt.
