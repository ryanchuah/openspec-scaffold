# OpenSpec Customization Audit — Comparison Table

**Purpose:** Factual comparison of what OpenSpec offers natively vs. what our scaffold hand-rolls.
**Date:** 2026-06-18
**Read-only:** yes (no scaffold files modified)

---

## Behavioral Facts — OpenSpec Side

### Q1: Does `openspec update` overwrite or preserve local edits to skills?

**Overwrites.** `src/core/update.ts` lines 194–207:
```typescript
const skillContent = generateSkillContent(template, OPENSPEC_VERSION, transformer);
await FileSystemUtils.writeFile(skillFile, skillContent);
// → fs.writeFile(filePath, content, 'utf-8')   // no merge, plain overwrite
```
`openspec update` checks `generatedBy` version stamps in skill frontmatter to detect staleness; if a tool's skills are behind `OPENSPEC_VERSION`, it regenerates them with `writeFile`. Our skills carry `generatedBy: "1.4.1"` in their frontmatter — OpenSpec will recognize them as managed files and overwrite them on the next version bump.

### Q2: Can a custom schema define arbitrary artifacts + instructions? Cross-project sharing?

Yes. `openspec/schemas/<name>/schema.yaml` defines arbitrary artifact IDs, `generates:`, `instruction:`, `template:`, and `requires:` chains. Templates are markdown files injected into the AI prompt. `openspec schema fork spec-driven my-workflow` copies the built-in schema for local editing. Cross-project sharing: `~/.local/share/openspec/schemas/<name>/` (user-global); community schemas are standalone repos whose bundle is copied into `openspec/schemas/`. **Schema scope:** controls the artifact generation layer (what `openspec instructions <artifact> --json` returns to the skill). It does NOT modify the skill body itself.

### Q3: Does OpenSpec generate or manage AGENTS.md?

No. `openspec init` / `openspec update` create and update only:
- `openspec/` directory structure (specs/, changes/, config.yaml)
- `.claude/skills/openspec-*/SKILL.md` (for claude tool)
- `.opencode/skills/openspec-*/SKILL.md` (for opencode tool)
- Tool-specific command files (`.claude/commands/opsx/*.md`, etc.)

AGENTS.md is never written, read, or referenced by OpenSpec tooling.

### Q4: Does OpenSpec have any concept of `.claude/agents/*.md` or `.opencode/agents/*.md`?

No. OpenSpec's supported-tools.md lists only two artifact types per tool: **skills** (`.../skills/openspec-*/SKILL.md`) and **commands** (`.../commands/opsx-<id>.md`). The `.claude/agents/` and `.opencode/agents/` directory conventions are Claude Code's and OpenCode's own harness features — not an OpenSpec concept at all.

---

## Comparison Table

| Capability | OpenSpec-native mechanism | What our scaffold does instead | How we distribute it | Verdict |
|---|---|---|---|---|
| **(a) OpenSpec workflow skills** | `openspec init/update` generates `SKILL.md` files from TypeScript templates (e.g. `apply-change.ts`). Content: stock Steps 1–7, standard task loop, no delegation. | We keep the native file paths and frontmatter structure, but the skill bodies are **heavily customized**: added MANDATORY delegation block, `opencode run` invocation with exact `timeout -k 30 600` form, failure ladder (crash→retry→Sonnet), NON-CONVERGENCE BLOCKER protocol, phase gates. Apply, archive, and verify skills all carry substantial custom Step 6 / MANDATORY blocks absent from the generated template. | `sync_scaffold.py` byte-copies customized skills to downstream repos | **REINVENTING — actively fighting the native mechanism.** Skills carry `generatedBy: "1.4.1"` frontmatter. `openspec update` will detect version staleness and overwrite the entire skill body, erasing the delegation machinery. |
| **(b) Per-tool commands** | `openspec init --tools claude` generates `.claude/commands/opsx/<id>.md` command files alongside skills | We do not generate or sync command files. The manifest does not include any `.claude/commands/` entries. | N/A | **ALIGNED** (unused native feature; no conflict) |
| **(c) Multi-tool (claude + opencode) generation/sync** | `openspec init --tools claude,opencode` generates skills for both in one pass. `openspec update` refreshes both on version bump. | For initial setup, we use `openspec init`. For ongoing cross-repo propagation of our *customized* files, `openspec update` is not used — we use `sync_scaffold.py` to push the scaffold's golden copies to downstream repos. | `sync_scaffold.py` + `scaffold_manifest.txt` | **PARTIALLY-REINVENTING.** Initial generation is aligned. Ongoing sync of customized files is bespoke, but necessarily so since `openspec update` would clobber the customizations. |
| **(d) Executor agents** | OpenSpec has no concept of per-tool sub-agents or executor agent files. Not generated, not documented, not a supported extension point. | We invented `.claude/agents/apply-executor.md`, `.claude/agents/archive-executor.md`, `.opencode/agents/apply-executor.md`, `.opencode/agents/archive-executor.md`, `.opencode/agents/openspec-reviewer.md`, `.opencode/agents/openspec-verifier.md`. These define the deepseek delegation targets for apply and archive. | `sync_scaffold.py` byte-copies all six agent files to downstream repos | **LEGITIMATELY-BESPOKE.** Nothing to reinvent; this is pure addition in a gap OpenSpec leaves entirely open. |
| **(e) AGENTS.md roles/workflow text** | Not an OpenSpec artifact type. Not generated, not mentioned in any docs. | We hand-authored AGENTS.md with mandatory-read preamble, cross-agent compatibility rules, harness-memory non-use, role matrix, lifecycle, and delegation instructions. It is the primary context injection for every session. | `sync_scaffold.py` uses `sync_agents_md()` span-replace algorithm — preserves each downstream repo's title + `## Project context` block, syncs shared spans (MANDATORY, ## Roles onward) | **LEGITIMATELY-BESPOKE.** No native mechanism to reinvent. The span-merge is bespoke engineering for a gap OpenSpec doesn't address. |
| **(f) Cross-project sharing of workflow customization** | Two native mechanisms: (1) `~/.local/share/openspec/schemas/<name>/` — user-global custom schema shared across local projects; (2) community schema repos copied into `openspec/schemas/` per-project. Both carry only artifact templates + schema.yaml; neither carries skill bodies, executor agents, AGENTS.md spans, or ai-docs. | Bespoke `sync_scaffold.py` + `scaffold_manifest.txt`: manifest-driven file copy for skills, agents, ai-docs, and scripts; span-merge for AGENTS.md. `--check` enforces byte convergence; `--check-refs` enforces referential integrity. | Run manually from scaffold repo | **LEGITIMATELY-BESPOKE for most payload** (agents, AGENTS.md, ai-docs outside OpenSpec's model). **PARTIALLY-REINVENTING for schema-level items** — if we used a custom schema we could carry it via the global-schemas mechanism, but we don't use a custom schema so there is no active conflict. |
| **(g) Project context/rules injection (config.yaml)** | Native: `openspec/config.yaml` with `context:` (injected into all artifact prompts) and `rules.<artifact-id>:` (per-artifact rule lists). Injected via `openspec instructions <artifact> --json` → consumed by the skill at generation time. | We use `openspec/config.yaml` in all three repos with `context:` (project description, stack, testing philosophy, research convention) and `rules:` for `tasks`, `verify`, and `archive`. This is the correct layer for governing what the AI **creates** in artifacts. | Each repo maintains its own config.yaml (not synced; project-specific). The scaffold's config.yaml is a template with `<FILL>` placeholders. | **ALIGNED.** We use the native mechanism correctly and it is doing its intended job. |
| **(h) Custom workflow artifacts (schemas)** | `openspec/schemas/<name>/schema.yaml` + templates define custom artifact sets, per-artifact instructions, and dependency graphs. `openspec schema fork spec-driven my-workflow` for local customization; `~/.local/share/openspec/schemas/` for global sharing. | We use the stock `spec-driven` schema unchanged. No `openspec/schemas/` directory exists in scaffold or downstream repos. | N/A | **ALIGNED** (unused; no need currently identified). |

---

## Evidence Summary

### Files examined

- `OpenSpec/docs/customization.md` — schema mechanism, config.yaml, global overrides, community schemas
- `OpenSpec/docs/supported-tools.md` — skill/command paths per tool; no agent concept
- `OpenSpec/docs/cli.md` — `init`/`update` behavior; update confirmed to be overwrite via `writeFile`
- `OpenSpec/src/core/update.ts` lines 194–207 — `generateSkillContent` → `FileSystemUtils.writeFile` (unconditional overwrite)
- `OpenSpec/src/core/templates/workflows/apply-change.ts` — upstream apply skill template (stock Step 6: inline task loop, no delegation, no opencode run)
- `OpenSpec/src/utils/file-system.ts` line 207 — `fs.writeFile(filePath, content, 'utf-8')` confirming overwrite
- `.claude/skills/openspec-apply-change/SKILL.md` — our customized apply skill (MANDATORY block, delegation, failure ladder, phase gate)
- `.claude/skills/openspec-archive-change/SKILL.md` — our customized archive skill (MANDATORY block, archive-executor delegation, pre-handoff checkpoint)
- `.claude/skills/openspec-verify-change/SKILL.md` — our customized verify skill (MANDATORY behavioral review block, fix-redelegation mechanics)
- `.claude/agents/apply-executor.md`, `.claude/agents/archive-executor.md` — our executor agents (no OpenSpec equivalent)
- `.opencode/agents/apply-executor.md` + three others — opencode executor agents (no OpenSpec equivalent)
- `openspec/config.yaml` (scaffold), `psc-monitor/openspec/config.yaml`, `extrends/openspec/config.yaml` — native mechanism, correctly used in all three repos
- `scripts/scaffold_manifest.txt` — inventories: 2 `.claude/agents`, 7 `.claude/skills`, 4 `.opencode/agents`, 3 `ai-docs`, 7 scripts, + AGENTS.md
- `scripts/sync_scaffold.py` — byte-copy for all manifest entries except AGENTS.md; span-merge for AGENTS.md
- `AGENTS.md` — not an OpenSpec artifact; no OpenSpec tooling touches it

### Key diff: our apply skill vs upstream template (Step 6)

**Upstream** (`apply-change.ts` line 74–83): "For each pending task: Make the code changes required / Keep changes minimal / Mark task complete"

**Ours** (`.claude/skills/openspec-apply-change/SKILL.md` lines 81–194): Replaces inline task loop with full delegation branch:
- `opencode run --agent apply-executor --model deepseek/deepseek-v4-flash --format json ...`
- `run_in_background: true` + EXIT-sentinel detection
- Crash → retry → Sonnet fallback ladder
- NON-CONVERGENCE BLOCKER grep logic
- Mandatory disclosure when Sonnet runs

This delta is the core customization. `openspec update` would erase it.

### Downstream repos: no schemas, agents present

`psc-monitor` and `extrends`:
- `openspec/config.yaml` — present, project-specific content (not synced)
- `.claude/agents/` — `apply-executor.md`, `archive-executor.md` (synced from scaffold)
- `.opencode/agents/` — four agent files (synced from scaffold)
- `.claude/skills/` — 7 skills (synced from scaffold; byte-identical to scaffold)
- No `openspec/schemas/` in either repo

---

## Sharpest Findings

### Finding 1 (REINVENTING — active collision): Skill bodies vs `openspec update`
Our apply, archive, and verify skill files are substantially modified from the upstream templates and carry `generatedBy: "1.4.1"` in their frontmatter. This version stamp is exactly what `openspec update` uses to detect stale skills — on any OpenSpec version bump, it will regenerate all three skills, erasing the MANDATORY delegation block, `opencode run` invocation, failure ladder, phase gates, and NON-CONVERGENCE BLOCKER protocol. There is no native hook to inject skill-body content; `config.yaml` rules inject into artifact generation prompts, not skill instruction bodies. **The customizations live at a layer OpenSpec does not protect.**

### Finding 2 (LEGITIMATELY-BESPOKE, but fragile): No schema fork to protect skill customizations
The correct long-term answer for "I need to change how the apply skill behaves" in OpenSpec's model would be to fork a custom schema — but custom schemas control artifact templates and instructions, not skill bodies. There is genuinely no OpenSpec-native way to redirect Step 6 of the apply skill to an executor. The bespoke approach is therefore the only option, but it remains vulnerable to clobber. Mitigation: remove `generatedBy` from skill frontmatter so `openspec update` does not detect them as managed (or track the OpenSpec version and manually re-merge on each bump).

### Finding 3 (ALIGNED but scope-limited): config.yaml rules are correct but only reach the artifact layer
We use `config.yaml` rules correctly for the artifact layer: the `rules.tasks`, `rules.verify`, and `rules.archive` entries inject into `openspec instructions --json` output and shape what the AI writes into tasks.md, design.md, etc. This is the intended mechanism and works well. However, these rules do NOT reach the skill body — the skill itself executes before it calls `openspec instructions`. The delegation override must live in the skill body (our approach) or in AGENTS.md (also our approach). Both are bespoke layers. This is not a failure — it is a real gap in OpenSpec's extension model.
