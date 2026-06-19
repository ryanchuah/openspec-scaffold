# Project Knowledge Taxonomy

**Classification rule:** Store knowledge that cannot be recovered from the source code. Do not store knowledge that merely duplicates or describes the code — it rots.

---

## Knowledge Types and Homes

| Type | Question it answers | Home | Load |
|---|---|---|---|
| State | Where are we right now? | `memory/STATUS.md` + `memory/questions/INDEX.md` (Active) | boot |
| Decisions | What did we choose, and why? | `memory/decisions/INDEX.md` (one line per decision → archive; rationale inline when no archive exists) | on-demand |
| Questions | What is open / parked? | `memory/questions/` (Active = boot; Parked + per-item files = on-demand) | split |
| Lessons | What did we learn about how to work? | `memory/lessons.md` (single file) | on-demand |
| Reference | Durable facts not in the code (runbook, external-API semantics, empirical findings) | `memory/reference/` | on-demand |
| Research | Hard-won synthesized investigation (e.g. vendor comparisons, protocol analysis) | `memory/research/` (indexed) | on-demand |
| Roadmap | Where are we headed long-term? | `memory/roadmap.md` | on-demand |
| History | What did we do? | `openspec/changes/archive/` (the sole archive) | search-only |
| Contracts | What must each subsystem guarantee? | `openspec/specs/` | on-demand |
| Rules | How do agents behave? | `.claude/skills/`, `openspec/config.yaml`, AGENTS standing rules | phase-entry |

---

## Usage Notes

- **Boot reads:** `AGENTS.md`, `memory/STATUS.md`, and the Active section of `memory/questions/INDEX.md` only. All other types load on demand.
- **History is search-only:** Never load the full archive at boot. Search `openspec/changes/archive/` when you need to look something up.
- **`memory/README.md` is scaffold-managed** (synced byte-identical to every repo). All other files under `memory/` are per-repo and are never synced.
