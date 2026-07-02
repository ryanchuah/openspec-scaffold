---
name: lint-knowledge
description: Detect per-repo knowledge drift — stale "not yet built" claims, intra-doc contradictions, and buried operator gates — that the deterministic linter cannot see. Use when the operator asks to audit/lint the knowledge tree, or periodically as a standalone maintenance pass. Not run automatically on every archive.
license: MIT
compatibility: Requires openspec CLI.
metadata:
  author: openspec
  version: "1.0"
  generatedBy: "1.4.1"
---

Detect per-repo knowledge drift — the semantic drift a deterministic linter cannot see — across
the tracked `knowledge/` tree and any other repo-relative prose the operator names.

**Cadence — operator-invoked / periodic, NOT every archive.** This is a judgment-layer, LLM-cost
pass. It is deliberately **not** wired into every `openspec-archive-change` run (that would spend
LLM tokens re-litigating drift unrelated to the change just archived); the archive step instead
runs only the cheap deterministic `scripts/knowledge_lint.py` plus a narrow, just-shipped-change
re-check (see `AGENTS.md` and the `openspec-archive-change` skill). This skill is the periodic,
whole-tree sweep — invoke it on operator request or on a recurring cadence the operator sets.

**Detect-only.** This skill produces findings only. It never edits, rewrites, or deletes any
tracked file — every finding is reported for the operator/primary to act on separately.

**Steps**

1. **Run the deterministic linter first.**

   ```bash
   python scripts/knowledge_lint.py
   ```

   Read every reported finding (orphan/duplicate canonical files, retired-path tokens, broken
   prose path citations, dangling `openspec/changes/archive/<dir>/` pointers, malformed
   `knowledge/audit-log.md` registry lines). Report these findings verbatim in the summary —
   do **not** re-derive them by hand, and do **not** spend judgment-pass effort on drift this
   cheap deterministic pass already caught.

2. **Class B — stale "not yet built" / planned claims.**

   Read `knowledge/STATUS.md` and the directory listing of `openspec/changes/archive/` to build a
   picture of what has actually shipped. Then scan the wider tracked knowledge bodies —
   `knowledge/reference/` (runbooks, compliance drafts), `knowledge/roadmap.md`, and the
   `knowledge/questions/` bodies (both `INDEX.md` and the individual per-item files) — for any
   passage that describes a feature as "not yet built", "planned", "designed but not built", or
   similar, when a shipped `archive/` entry or `knowledge/STATUS.md` already records it as done.
   Flag each contradiction with: the file/line making the stale claim, and the archive
   entry/STATUS.md line that contradicts it.

3. **Class D — intra-doc contradictions.**

   Within each tracked knowledge doc (not just the trackers — reference/roadmap/review-adjacent
   bodies too), look for two passages that assert incompatible facts about the same subject: e.g.
   two lists of different length or membership for the same set, two different counts/states for
   the same tracked item, or a "done" claim followed later in the same doc by an "in progress"
   claim for the same thing. Flag each contradiction with both passage locations (file + line or
   section).

4. **Buried-gate sweep.**

   Read any README/runbook-style docs under `knowledge/reference/` (and the repo-root `README.md`
   if it documents operator/pre-production gates) for real operator-facing or pre-production
   checklist items — e.g. "before shipping to prod, do X" or "an operator must confirm Y". Cross
   check each such item against `knowledge/questions/INDEX.md` **Active** section. Flag any real
   gate item that is named only in the README/runbook and absent from Active (it is "buried" —
   not tracked where a returning operator would see it).

5. **Report findings — do not fix.**

   Produce a single findings report covering steps 1–4. For each finding, include: class
   (deterministic / Class B / Class D / buried-gate), file(s) + line/section, and a one-line
   description of the drift. Do **not** edit any tracked file — correcting the content is a
   separate, manual per-repo follow-on (per the `knowledge-lint` capability's detect-only scope).
   If the operator wants specific findings fixed, that is a distinct, explicit follow-up request.

**Output**

```
## Knowledge Lint Report

**Deterministic (`scripts/knowledge_lint.py`):** <N> finding(s) — <exit code>
<list, or "none">

**Class B — stale "not yet built" claims:** <N> finding(s)
<list, or "none">

**Class D — intra-doc contradictions:** <N> finding(s)
<list, or "none">

**Buried-gate items:** <N> finding(s)
<list, or "none">

Detect-only pass complete. No files were modified. Fixing any of the above is separate,
operator-directed follow-up work.
```

**Guardrails**
- Always run `scripts/knowledge_lint.py` first — do not begin the judgment sweeps before it.
- Never edit, create, or delete a tracked file. This skill reports; it does not rewrite.
- Do not treat this as part of the archive flow — it is a separate, operator-invoked pass.
- When judging "shipped", trust `openspec/changes/archive/` and `knowledge/STATUS.md` over prose
  elsewhere — those are the load-bearing records of what actually happened.
