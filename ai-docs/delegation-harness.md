# Delegation harness — shared `opencode run` contract

The four delegating OpenSpec skills — propose, apply, verify, archive — share this operational
contract for every `opencode run` delegation. Each skill cites this doc and keeps only its own
per-phase invocation command, agent/model/budget, and failure ladder.

---

## (a) Hardened invocation

Every delegated `opencode run` closes stdin (`< /dev/null`) and passes `--dir <repoRoot>`.
See the `noninteractive-delegation-safety` capability spec for the full rationale.

---

## (b) Assert the real agent ran

Do this BEFORE trusting any output — `opencode run` exits 0 even on silent agent fallback.

- `grep -q "Falling back to default agent" /tmp/<phase>-err.log` — if it matches, the
  intended agent was **not** loaded. Do NOT use the output — treat as an **operational crash**.
- Confirm `/tmp/<phase>-out.jsonl` is non-empty and parseable, and extract the completion text:
  ```bash
  grep '"type":"text"' /tmp/<phase>-out.jsonl | tail -1 | jq -r '.part.text'
  ```
  Empty/unparseable → operational crash.
- Confirm the extracted text carries the agent's own output format (phase-specific — see each skill
  for what format to confirm).

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
verify's fix-executor, and verify's verifier passes.

Append `; echo "EXIT=$?" > /tmp/<phase>-out.exit` to the wrapped command. Detect completion by
`[ -f /tmp/<phase>-out.exit ]` in a bounded sleep loop (or simply wait for the harness
background-completion notification); the `timeout` wrapper guarantees the sentinel appears within
~N+grace seconds.

**NEVER poll with `until ! pgrep -f "<pattern>"`** — the pattern self-matches the poller's own
`bash -c` command line, so the loop exits while the run is still going. **Never judge a run from a
mid-execution jsonl snapshot** — deepseek-v4-flash/pro can legitimately take >5 minutes and a short
jsonl mid-run is NORMAL. Conclude crash/timeout ONLY if the exit file shows nonzero (124 = timeout,
137 = SIGKILL), OR no opencode PID remains AND no exit file was ever written (genuine truncation).

**Scope notes:**
- **Propose's reviewer call is synchronous** (the `opencode run` command blocks until it returns) —
  no sentinel needed or present. This is correct by design.
- **Archive's executor is launched with `run_in_background: true`** (because reconciliation can run
  several minutes) but its invocation **omits the `echo "EXIT=$?"` sentinel** — this is a
  pre-existing drift, documented here and left as-is (extraction, not redesign).

---

## (e) Timeout budget table

| Phase | Call | `timeout` flags | Budget (s) | Kill-grace | Notes |
|-------|------|-----------------|------------|------------|-------|
| apply | apply-executor | `-k 30 600` | 600 | 30s | Full `tasks.md` can run several minutes; extra grace reduces SIGKILL risk during a legitimate slow step. |
| archive | archive-executor | `-k 30 600` | 600 | 30s | Multi-step reconciliation; same rationale as apply. |
| verify | fix-executor | `-k 15 300` | 300 | 15s | Scoped single-defect fix; finishes well inside 5 minutes; faster kill appropriate. |
| verify | verifier (pro pass) | `-k 15 780` | 780 | 15s | Independent verification pass; focused scope makes faster kill appropriate. |
| verify | verifier (flash pass) | `-k 15 780` | 780 | 15s | Same as pro pass. |
| propose | reviewer | `-k 15 780` | 780 | 15s | Per the `reviewer-budget` capability spec — cross-referenced, not duplicated here. |

The budgets above are extraction-faithful — this table is the single authoritative source for all
phase timeout values. Cross-reference: the propose reviewer's 780s / `-k 15` budget is codified in
the `reviewer-budget` capability spec.

---

## Carve-out: verify's in-process passes

Verify's **in-process self-review pass** (the primary agent's own review) and the **OpenCode
Task-tool verifier spawn** (`subagent_type: openspec-verifier`) are Task-tool spawns, not
`opencode run` — there is no separate process and no TTY-stdin. They are therefore **exempt**
from the `< /dev/null` / `--dir` hardening (§a) and the bounded-wait/surgical-kill wrapper (§c).
A skill citing this doc for an in-process pass must not apply (a) or (c) to it.
