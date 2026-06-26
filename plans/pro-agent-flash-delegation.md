# Plan — pro-tier agents may offload exploration to a read-only flash subagent

Status: AWAITING operator tier+plan confirmation. Not yet executed.

## Problem statement
The three deepseek-pro agent roles (`openspec-reviewer`, `openspec-verifier` pro pass,
`archive-executor`) do heavy reading/auditing/reconciliation entirely in their own context.
The operator wants them to be able to offload bulk exploration (reading, searching,
extraction) to cheap deepseek-v4-flash subagents — mirroring how the orchestrator delegates
to subagents to keep its own context lean — without weakening the read-only stance of the
auditor roles.

Feasibility confirmed (opencode docs, see `tmp/opencode-subagent-research.md`):
- `opencode run` agents CAN spawn subagents; `task` permission defaults to `allow`.
- No per-call model override — to pin flash, the subagent must be a dedicated definition
  with `model:` pinned.
- `permission.task` accepts a name→action whitelist; spawned subagents auto-deny `task`
  (no runaway recursion).

## Proposed approach
1. **New read-only flash explorer subagent** `.opencode/agents/explore-flash.md`:
   - `mode: subagent`, `model: deepseek/deepseek-v4-flash`
   - permissions: `read/glob/grep/list: allow`; `edit/bash/task/webfetch/websearch: deny`;
     `external_directory` `/tmp/**` allow. Hard read-only by construction (no edit, no bash).
   - Short body: explore as directed, report concise findings, never mutate, never spawn.
2. **Add it to `scripts/scaffold_manifest.txt`** (`.opencode` agent block) so it propagates.
3. **Enable + nudge the three pro roles** to spawn ONLY `explore-flash` (whitelist), and add
   a prompt line per role:
   - `openspec-reviewer`: add `task:` whitelist (`"*": deny`, `explore-flash: allow`) +
     body line. Stays read-only (`bash/edit: deny` unchanged).
   - `openspec-verifier`: change `task: deny` → whitelist (`"*": deny`, `explore-flash: allow`)
     + body line. Stays read-only on files (`edit: deny` unchanged).
   - `archive-executor`: add `task:` whitelist + body line. **Body line phrased conditionally**
     ("if your harness exposes a subagent tool…") so it stays TRUE for the byte-identical
     Claude Sonnet fallback, which has no Task tool — keeping
     `test_executor_body_agreement.py` green. The identical line is mirrored into
     `.claude/agents/archive-executor.md`.
4. **Verification:** run `python3 scripts/test_executor_body_agreement.py` (must stay green),
   eyeball each edited file, confirm frontmatter YAML validity. Flash verifier pass per SMALL.
5. **Propagation:** these are scaffold-managed — fold into the already-pending downstream
   sync (extrends, psc-monitor) via `sync_scaffold.py`.

## Out of scope
- The flash-tier agents (`apply-executor`, SMALL premise pass) — request is pro-only.
- Letting the explorer itself spawn subagents (recursion) or run bash — kept read-only.
- Changing the orchestrator's own delegation behavior (already delegates).
- Pushing to remote (needs separate operator authorization).
- OPEN DECISION: whether this gets its own capability spec or just a decision-log line.

## Tier
Proposed **SMALL**: doc/config edits (1 new agent file + 3 frontmatter/body edits + 1 mirror
edit + 1 manifest line), no implementation logic, the judgment-heavy design is done here.
Executed directly by the primary as doc/config work (per the "quick doc edits done by the
primary" carve-out), with the SMALL flash premise pass run before execution.
