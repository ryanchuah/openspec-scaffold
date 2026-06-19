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
| verify | fix-executor | `-k 30 600` | 600 | 30s | Scoped single-defect fix; 10-minute floor matches the apply/archive budget. |
| verify | verifier (pro pass) | `-k 15 780` | 780 | 15s | Independent verification pass; both platforms use this budget. |
| verify | verifier (flash pass) | `-k 15 780` | 780 | 15s | Same as pro pass; both platforms. |
| propose | reviewer | `-k 15 780` | 780 | 15s | Per the `reviewer-budget` capability spec — cross-referenced, not duplicated here. |

The budgets above are extraction-faithful — this table is the single authoritative source for all
phase timeout values. Cross-reference: the propose reviewer's 780s / `-k 15` budget is codified in
the `reviewer-budget` capability spec.

---

## Carve-out: verify's in-process self-review

Verify's **in-process self-review pass** (the primary agent's own review) is a Task-tool spawn,
not `opencode run` — there is no separate process and no TTY-stdin. It is therefore **exempt**
from the `< /dev/null` / `--dir` hardening (§a) and the bounded-wait/surgical-kill wrapper (§c).
The delegated verifier passes (pro + flash, both platforms) use `opencode run` and are NOT exempt.
