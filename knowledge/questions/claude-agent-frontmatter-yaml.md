# Parked: `.claude` fallback-agent `description:` lines aren't strict YAML

**Status:** Parked / low-priority cleanup. Not breaking anything today. Do this once the
backlog is otherwise clear.

## What

Two `.claude` fallback-agent files have a `description:` whose value starts with a bracket:

- `.claude/agents/apply-executor.md` (line 3) — `description: [FALLBACK — used when …] Executes …`
- `.claude/agents/archive-executor.md` (line 3) — `description: [FALLBACK — used when …] Executes …`

In strict YAML a scalar starting with `[` is parsed as a flow sequence, and the trailing
prose after the closing `]` makes it invalid — `python3 -c "import yaml; yaml.safe_load(<frontmatter>)"`
raises `ParserError: while parsing a block mapping` on both files. The `.opencode/agents/`
counterparts do NOT have this (their descriptions don't lead with `[`), so only the two
`.claude` files are affected.

## Why it isn't breaking now

The Claude Code harness loads these agents fine in practice — it evidently uses a lenient /
custom frontmatter parser, not strict `yaml.safe_load`. So this is latent, not active. It
would only bite a future tool that parses these files with a strict YAML loader.

## The fix (when picked up)

Quote the description scalar (or drop the brackets). E.g.:
`description: "[FALLBACK — used when …] Executes …"`
Verify with the per-file parse loop in this repo's history (loads `---`-delimited frontmatter
through `yaml.safe_load`); all `.claude` + `.opencode` agent files should then parse OK.

## Caveats for whoever fixes it

- These are **scaffold-managed** files (`scripts/scaffold_manifest.txt`). Fix them HERE in the
  golden source, then propagate with `scripts/sync_scaffold.py` to **extrends** and
  **psc-monitor** (and review/commit there). Don't edit them downstream.
- The fix is **frontmatter-only**, so `scripts/test_executor_body_agreement.py` (which strips
  frontmatter before comparing bodies) is unaffected — it stays green.
- Discovered 2026-06-26 during the `pro-agent-flash-delegation` change; the verifier flagged
  the archive-executor instance, and a sweep found apply-executor has the same shape.
