# Project Knowledge Taxonomy

**Classification rule:** Store knowledge that cannot be recovered from the source code. Do not store knowledge that merely duplicates or describes the code — it rots.

---

## Knowledge Types and Homes

| Type | Question it answers | Home | Load |
|---|---|---|---|
| State | Where are we right now? | `knowledge/STATUS.md` + `knowledge/questions/INDEX.md` (Active) | boot |
| Mid-session handoff | What in-flight work must I resume? | `knowledge/HANDOFF.md` (ephemeral; deleted on absorption) | boot-if-present |
| Decisions | What did we choose, and why? | `knowledge/decisions/INDEX.md` (rolling newest-tail window; one line per decision → archive; rationale inline when no archive exists) + `knowledge/decisions/HISTORY.md` (older entries, on demand) | on-demand |
| Questions | What is open / parked? | `knowledge/questions/` (Active = boot; Parked + per-item files = on-demand) | split |
| Lessons | What did we learn about how to work? | `knowledge/lessons.md` (single file) | on-demand |
| Reference | Durable facts not in the code (runbook, external-API semantics, empirical findings) | `knowledge/reference/`; `knowledge/audit-log.md` (bounded one-line-per-audit registry ledger, same registry-line discipline as `knowledge/decisions/INDEX.md` — full audit outputs live untracked under `output/checks/<date>/` and are disposable per-audit build artifacts); `knowledge/ratchet-log.md` (second bounded one-line-per-entry registry ledger, same format class, tracking finding-closure dispositions) | on-demand |
| Research | Hard-won synthesized investigation (e.g. vendor comparisons, protocol analysis) | `knowledge/research/` (indexed) | on-demand |
| Roadmap | Where are we headed long-term? | `knowledge/roadmap.md` | on-demand |
| History | What did we do? | `openspec/changes/archive/` (the sole archive) | search-only |
| Contracts | What must each subsystem guarantee? | `openspec/specs/` | on-demand |
| Rules | How do agents behave? | `.claude/skills/`, `openspec/config.yaml`, AGENTS standing rules | phase-entry |

---

## Usage Notes

- **Boot reads:** `AGENTS.md`, `knowledge/STATUS.md`, and the Active section of `knowledge/questions/INDEX.md` — plus `knowledge/HANDOFF.md` when it is present (see Mid-session handoff above; ephemeral, so normally absent). All other types load on demand.
- **Mid-session handoff write side:** a session writes `knowledge/HANDOFF.md` when it must hand off before archive (e.g. context exhausted mid-change). `knowledge/STATUS.md` is the wrong home because it is reconciled only at archive. The next session absorbs the handoff and deletes it. There is exactly one such file — this supersedes ad-hoc multiple root-level HANDOFF files.
- **History is search-only:** Never load the full archive at boot. Search `openspec/changes/archive/` when you need to look something up.
- **`knowledge/README.md` is scaffold-managed** (synced byte-identical to every repo). All other files under `knowledge/` are per-repo and are never synced.
- **Deliberate forward-references:** a knowledge doc that deliberately cites a not-yet-created path SHALL put `<!-- lint:planned -->` on that line to suppress the broken-citation finding (`scripts/knowledge_lint.py`). The suppression is line-scoped — it only opts out the line it appears on.
- **Decisions registry rolling window:** `knowledge/decisions/INDEX.md` holds only the newest tail
  of the registry, byte-budgeted (`decisions-index-budget` check, default 16,000 bytes, per-repo
  overridable via `checks.toml`); older entries roll verbatim into `knowledge/decisions/HISTORY.md`
  — same one-line format, same chronological order, never part of the mandatory boot set, loaded
  on demand (grep `knowledge/decisions/`). `scripts/roll_decisions.py` (dry-run supported) performs
  the roll, shrinking INDEX.md down to a 12,000-byte hysteresis target. Raising either budget is an
  operator decision recorded in the decisions registry.
