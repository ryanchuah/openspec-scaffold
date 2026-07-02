## Why

Per-repo knowledge prose rots because nothing systematically re-checks it against reality. The scaffold
workflow layer is byte-synced and measured drift-free, but the per-repo knowledge bodies the scaffold
deliberately does **not** manage — reference runbooks, compliance drafts, roadmap, review-backlog, and even
the prose bodies of the trackers themselves — sit outside every reconciliation and lint loop. So shipped
features stay described as "not yet built", retired paths keep being cited, and intra-doc contradictions
persist unseen. A 2026-07-01 audit of a downstream repo measured four concrete drift classes (orphan
duplicate file; stale "not-built" claims for shipped work; retired-path citations; intra-doc contradiction);
no existing mechanism — `sync_scaffold.py --check`/`--check-refs`, `scaffold_check.py`, `status_lint.py`, or
the archive-executor's three-tracker reconciliation — can catch any of them. This change ships the detection
and reconciliation machinery in the scaffold so `sync_scaffold.py` propagates it to every downstream repo.
Direction was premise-reviewed `AGREE` (2026-07-02, see `premise-review.md`); tier COMPLEX/UNCERTAIN.

## What Changes

- Add **`scripts/knowledge_lint.py`** — a stdlib-only, CI-able **deterministic** linter over tracked
  per-repo knowledge, modeled on `status_lint.py`. Checks: orphan/duplicate canonical-file detection (e.g.
  a `STATUS.md` outside `knowledge/`, a second copy of a canonical file); retired-path token detection
  (`ai-docs/`, `plans/open-issues.md`, `docs/reviews/`, `/home/me/`, and similar); prose path-citation
  resolution broadened beyond `knowledge/*.md` to any repo-relative `*.md`/dir cited in prose; dangling
  `openspec/changes/archive/<dir>/` pointer detection; and a file-exists-guarded `knowledge/audit-log.md`
  registry-line format check. It **detects and reports only — it never writes to or fixes files.**
- Add a **`lint-knowledge` skill** at `.claude/skills/lint-knowledge/SKILL.md` (one path, discovered by
  both harnesses per the `skills-in-dot-claude-only` decision) — an **LLM judgment pass** for the drift a
  linter cannot see: "not yet built / planned / designed-not-built" claims that contradict a shipped
  `archive/` entry or `STATUS.md`; intra-doc contradiction sweeps; and a buried-gate sweep for real
  operator/pre-prod items living only in a README/runbook and absent from `questions/INDEX.md` Active.
- **Widen the archive-time reconciliation brief** — an `AGENTS.md` span edit plus an
  `openspec-archive-change` skill edit — so the archive step re-checks the reference/compliance/roadmap/
  review-backlog bodies for claims about the just-shipped change, not only the three named trackers.
- **Register** `scripts/knowledge_lint.py` and its test file, plus the new skill, in
  `scripts/scaffold_manifest.txt` so the sync propagates them downstream.
- **Not in scope:** correcting any per-repo drift *content*. Burning down the measured backlog in the
  downstream repo stays a manual per-repo follow-on; this change ships only detection + reconciliation
  machinery. The linter never rewrites prose.

## Capabilities

### New Capabilities
- `knowledge-lint`: deterministic + judgment-layer detection of drift in per-repo tracked knowledge — the
  deterministic script (orphans/duplicates, retired-path tokens, broadened prose path-citation resolution,
  dangling archive pointers, audit-log registry format) and the LLM skill (stale-claim, intra-doc
  contradiction, and buried-gate sweeps). Detect-and-report only; run at archive and on operator demand.

### Modified Capabilities
- `knowledge-organization`: the `archive-step-reconciles-into-new-structure` requirement widens — the
  archive step SHALL re-check the reference/compliance/roadmap/review-backlog **bodies** for claims about
  the just-shipped change, not only `knowledge/STATUS.md` / `knowledge/decisions/INDEX.md` /
  `knowledge/questions/`. (The three-tracker reconciliation is unchanged; this adds the wider body sweep.)

## Impact

- **New files:** `scripts/knowledge_lint.py`, `scripts/test_knowledge_lint.py`,
  `.claude/skills/lint-knowledge/SKILL.md`.
- **Edited scaffold-managed files:** `AGENTS.md` (reconciliation-brief span), the
  `.claude/skills/openspec-archive-change/SKILL.md` skill, and `scripts/scaffold_manifest.txt`.
- **Propagation:** on the next `sync_scaffold.py` each downstream repo (extrends, psc-monitor) receives the
  linter and skill; each then runs a first `lint-knowledge` pass to burn down its own drift backlog — a
  separate per-repo follow-on change, not this one.
- **No product/runtime code; stdlib-only; no new dependencies.** Relationship to the existing
  `sync_scaffold.py --check-refs` path-citation scan and `status_lint.py`'s archive-pointer check is
  coexist-not-replace; the exact division of labor and cadence split (deterministic = CI/every-archive; LLM
  = periodic/operator-invoked) are settled in `design.md`.
- **Detect-only posture** means zero risk to knowledge content: no automated prose rewriting anywhere.
