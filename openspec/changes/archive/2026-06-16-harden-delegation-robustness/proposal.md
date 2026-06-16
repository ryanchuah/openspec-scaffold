## Why

The delegated-work model runs deepseek agents non-interactively via `opencode run`. In a real session a reviewer hung ~30 minutes: with no TTY attached, an opencode permission prompt blocks forever on stdin that never arrives. The cause is now empirically pinned — opencode's `external_directory` permission defaults to `ask`, and an `ask` with no answerer hangs until the `timeout` wrapper kills it (probe: stdin left open → hang; `< /dev/null` → 5 s, auto-rejected). The previously proposed "feed file contents inline" workaround does not scale to large changes and is the wrong fix. Two `harden-delegation` follow-ups also remain open: the non-convergence canary is gameable (its `tasks.md` tells the executor to edit the very file holding the impossible assertion, so an honest executor turns it green and the STOP path is never exercised), and the commit-test-gate's hook wiring was never live-smoked.

## What Changes

- Close stdin (`< /dev/null`) on every delegated `opencode run` invocation (propose / apply / archive / verify). Empirically this is the single reliable fix: it converts an unanswerable prompt into a fail-fast auto-deny — the fail-*safe* direction — and neutralizes every prompt source generically, not just the one confirmed.
- Configure per-agent permissions so the auto-deny never starves legitimate work. The **read-only reviewer** (`bash: deny`, `edit: deny` — no destructive capability) gets `external_directory: allow`, so an out-of-tree artifact read can never be auto-rejected out from under a review. The **two write-capable executors** — apply AND archive, both `bash: allow` + `edit: allow` — instead get `external_directory: { "*": deny, "/tmp/**": allow }`: the apply-executor's `/tmp` convergence-helper write keeps working while every other out-of-tree path is hard-denied, which also contains a stray out-of-tree `rm`. **Pattern order is load-bearing** — opencode is last-match-wins, so the catch-all `"*"` must be listed first. (`question` is another `ask`-capable source, but it is already neutralized generically by the stdin close; explicitly denying it is deferred — its runtime behavior was not probed, so this change does not assert it.)
- Add `--dir <repoRoot>` (an orchestrator-substituted placeholder, like the existing `<changeRoot>`) to the invocations as hygiene so artifact paths resolve in-tree. This does not itself fix the hang.
- Rebuild the non-convergence canary to be non-gameable: move the contradiction into an impl module that a **frozen** test imports. The only editable surface (the impl) cannot satisfy the frozen test, forcing genuine rule-(a) non-convergence instead of an edit-the-assertion shortcut. The test is frozen **by instruction** (`tasks.md` marks it do-not-edit), not by filesystem permission — so this hardens against the honest shortcut an executor would otherwise take, not a malicious rewrite, which is sufficient for the canary's purpose.
- Ship a repeatable commit-test-gate smoke procedure and record that the gate's **script layer is verified** across all five branches (no-cmd / empty / unresolvable → allow; fail → block exit 2; pass → allow); the live **hook-wiring** smoke remains a documented gated-session step (it cannot run from a non-gated session).

## Capabilities

### New Capabilities
- `noninteractive-delegation-safety`: a delegated `opencode run` invocation cannot hang on an unanswerable permission prompt, and a delegated agent has no reachable `ask` permission for the paths or actions it legitimately needs.

### Modified Capabilities
- `apply-convergence-guard`: the convergence guard SHALL ship with a **hardened, instruction-gated** end-to-end canary — the impossibility lives in code the frozen test imports, not in an editable assertion — so an honest executor actually exercises the STOP path instead of editing the assertion green.
- `commit-test-gate`: the gate SHALL ship with a documented, repeatable smoke procedure covering its branches; the script-layer behaviors are verified evidence of the gate's correctness.

## Impact

- **Agent files (the shared surface):** `.opencode/agents/openspec-reviewer.md`, `.opencode/agents/apply-executor.md`, `.opencode/agents/archive-executor.md` — frontmatter `permission` blocks.
- **Skills (invocation text):** `.claude/skills/openspec-propose/SKILL.md`, `.claude/skills/openspec-apply-change/SKILL.md`, `.claude/skills/openspec-archive-change/SKILL.md`, `.claude/skills/openspec-verify-change/SKILL.md` — the `opencode run` lines gain `< /dev/null` and `--dir`.
- **Fixtures:** `docs/test/canary-non-convergence/` restructured (impl module + frozen test + updated `tasks.md`); a new commit-test-gate smoke fixture/procedure under `docs/test/`.
- **Docs:** `ai-docs/open-questions.md` — the canary follow-up is resolved (removed), while the hook-wiring follow-up is **narrowed, not removed** (script layer verified; the live hook-wiring smoke remains a documented gated-session step). `ai-docs/decisions.md` — record the stdin-close decision and the per-agent permission posture.
- **Scope:** scaffold-only — no runtime/app code. The agent and skill files are exactly the shared surface the single-source "change 2" propagates to `extrends` and `psc-monitor`; this change is inert there until then.
