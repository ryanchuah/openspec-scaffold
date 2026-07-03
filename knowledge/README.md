# Project Knowledge Taxonomy

**Classification rule:** Store knowledge that cannot be recovered from the source code. Do not store knowledge that merely duplicates or describes the code — it rots.

---

## Knowledge Types and Homes

| Type | Question it answers | Home | Load |
|---|---|---|---|
| State | Where are we right now? | `knowledge/STATUS.md` + `knowledge/questions/INDEX.md` (Active) | boot |
| Mid-session handoff | What in-flight work must I resume? | `knowledge/HANDOFF.md` (ephemeral; deleted on absorption) | boot-if-present |
| Decisions | What did we choose, and why? | `knowledge/decisions/INDEX.md` (one line per decision → archive; rationale inline when no archive exists) | on-demand |
| Questions | What is open / parked? | `knowledge/questions/` (Active = boot; Parked + per-item files = on-demand) | split |
| Lessons | What did we learn about how to work? | `knowledge/lessons.md` (single file) | on-demand |
| Reference | Durable facts not in the code (runbook, external-API semantics, empirical findings) | `knowledge/reference/`; `knowledge/audit-log.md` (bounded one-line-per-audit registry ledger, same registry-line discipline as `knowledge/decisions/INDEX.md` — full audit outputs live untracked under `output/audit/<date>/` and are disposable per-audit build artifacts) | on-demand |
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
