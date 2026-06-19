# Boot-time context cost spike — psc-monitor vs extrends

Measured: 2026-06-18. All byte counts from `wc -c`; tokens = `ceil(bytes / 4)`.

---

## Mandatory preamble / boot-routing section (identical in both repos)

Both AGENTS.md files open with this block (quoted from the common preamble at lines 3–34):

```
> **MANDATORY — read before doing anything else**
>
> You are reading this file. Before taking any action, also read **`STATUS.md`** and
> **`ai-docs/open-questions.md`** in full (both stay bounded); for
> **`ai-docs/decisions.md`** read the `## ` section headers (it is append-only
> and grows in a long-lived repo) and then read in full only the entries
> relevant to the current task. If you are
> *resuming an in-progress OpenSpec change*, also read that change's
> `openspec/changes/<name>/` directory (`proposal.md`, `design.md`, `tasks.md`,
> `notes.md`). Otherwise skip `openspec/changes/` and `ai-docs/archive/` — load a
> specific file there only when re-examining the closed decision it covers.
> `ai-docs/parked-follow-ons.md` is likewise NOT part of this mandatory read — it holds
> the deferred/monitored follow-on long tail grouped by `##` area; load only the relevant
> area section on demand when you start work in that area.
```

**Unconditional at boot:** AGENTS.md (self), STATUS.md, ai-docs/open-questions.md, ai-docs/decisions.md §-headers.  
**Conditional (resuming a change):** openspec/changes/<name>/{proposal,design,tasks,notes}.md.  
**Explicitly NOT boot:** openspec/changes/ (unless resuming), ai-docs/archive/, ai-docs/parked-follow-ons.md, ai-docs/research-fetch-convention.md.

Note on `decisions.md`: the agent is told to scan only `##` headers unconditionally; full section bodies are read on-demand per task. The tables below present both a headers-only row (the true unconditional minimum) and a full-file row (worst-case upper bound), since in practice an agent may read more liberally.

---

## psc-monitor

### Always-loaded at boot

| File | Bytes | Est tokens |
|---|---|---|
| AGENTS.md (incl. inlined `# Project reference` appendix) | 47,009 | 11,753 |
| STATUS.md | 9,102 | 2,276 |
| ai-docs/open-questions.md | 7,195 | 1,799 |
| ai-docs/decisions.md — `##` headers only (18 headers) | 1,633 | 409 |
| **TOTAL (headers-only for decisions)** | **64,939** | **16,237** |
| ai-docs/decisions.md — full file (upper bound) | 22,899 | 5,725 |
| **TOTAL (full decisions, upper bound)** | **86,205** | **21,553** |

### Conditional / on-demand

| File | Bytes | Est tokens | Trigger |
|---|---|---|---|
| openspec/changes/invoice-payment-failed-alert/proposal.md | 1,742 | 436 | resuming active change |
| openspec/changes/invoice-payment-failed-alert/tasks.md | 2,460 | 615 | resuming active change |
| openspec/changes/invoice-payment-failed-alert/notes.md | 4,624 | 1,156 | resuming active change |
| ai-docs/decisions.md full sections (beyond headers) | 22,899 | 5,725 | task-relevant entries |
| ai-docs/parked-follow-ons.md | 488 | 122 | working in a specific area |
| ai-docs/research-fetch-convention.md | 1,754 | 439 | web research work |

**psc-monitor headline: 16,237 tokens always loaded at boot** (lower bound, headers-only for decisions); **21,553 tokens upper bound** (full decisions).

---

## extrends

### Always-loaded at boot

| File | Bytes | Est tokens |
|---|---|---|
| AGENTS.md (lean, no inlined appendix) | 22,040 | 5,510 |
| STATUS.md | 28,035 | 7,009 |
| ai-docs/open-questions.md | 28,286 | 7,072 |
| ai-docs/decisions.md — `##` headers only (56 headers) | 3,583 | 896 |
| **TOTAL (headers-only for decisions)** | **81,944** | **20,487** |
| ai-docs/decisions.md — full file (upper bound) | 208,519 | 52,130 |
| **TOTAL (full decisions, upper bound)** | **286,880** | **71,721** |

### Conditional / on-demand

| File | Bytes | Est tokens | Trigger |
|---|---|---|---|
| openspec/changes/<name>/{proposal,design,tasks,notes}.md | 0 (no active changes) | 0 | resuming active change |
| ai-docs/decisions.md full sections (beyond headers) | 208,519 | 52,130 | task-relevant entries |
| ai-docs/parked-follow-ons.md | 63,558 | 15,890 | working in a specific area |
| ai-docs/research-fetch-convention.md | 1,754 | 439 | web research work |

**extrends headline: 20,487 tokens always loaded at boot** (lower bound, headers-only for decisions); **71,721 tokens upper bound** (full decisions).

---

## Summary

| Repo | Always-loaded tokens (lower) | Always-loaded tokens (upper) | Assessment |
|---|---|---|---|
| psc-monitor | 16,237 | 21,553 | Moderate — above "cheap" but managed; large driver is the 47KB inlined AGENTS.md appendix (11,753 tok) |
| extrends | 20,487 | 71,721 | Expensive — STATE FILES have grown large: STATUS.md (7,009 tok) + open-questions.md (7,072 tok) are each already at the single-file "cheap" ceiling; decisions.md is 208KB and if read beyond headers balloons total to 71k tokens |

**Key structural difference:** psc-monitor concentrates cost in AGENTS.md (stable, caches well across sessions in Claude Code's prompt cache). extrends concentrates cost in the mutable state files (STATUS.md, open-questions.md), which change every session and therefore cannot benefit from prompt caching — every boot pays the full reload cost on the state portion. The extrends decisions.md at 56 sections / 208KB is the single largest latent risk: even header-scanning an agent will be tempted to pull full entries, driving costs toward the 71k upper bound.
