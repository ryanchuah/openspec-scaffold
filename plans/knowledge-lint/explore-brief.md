# Explore brief: knowledge-lint (per-repo knowledge drift detection)

**Type:** explore-brief for the direction gate.
**Created:** 2026-07-02.
**Source:** transplanted from `psc-monitor/plans/knowledge-doc-drift-analysis.md`, written 2026-07-01
by the buried-open-items audit session in psc-monitor. That doc is a diagnostic + proposal that names
itself transitional and instructs its own deletion once this change archives — **delete it from
psc-monitor at that point** (not before; this session did not touch psc-monitor).
**Status:** direction gate PASSED (`PREMISE: AGREE`, 2026-07-02 — see `premise-review.md`);
propose NOT started — deferred to a fresh session (operator decision 2026-07-02).

---

## 1. Problem statement

Per-repo knowledge prose rots because nothing systematically re-checks it against reality. The
scaffold layer itself measured **zero drift** on 2026-07-01 in psc-monitor: `sync_scaffold.py --check`
found every scaffold-managed file byte-identical to the golden source, and `--check-refs` found no
dangling references. So the scaffolded workflow layer is in perfect sync — **all observed drift is in
per-repo knowledge bodies**, exactly the category `AGENTS.md` ("Scaffold-managed files & propagation")
says is **not** auto-propagated and needs a manual per-repo sweep. A reorg that retired old paths
updated the trackers and scaffold files but left prose elsewhere referring to the old state.

> **Operator, 2026-07-01 (psc-monitor):** "I suspect that we need to update the scaffold itself to
> prevent drift, but also create a `lint-knowledge` skill to detect these issues from time to time."

## 2. Verified facts

**Drift inventory (psc-monitor, 2026-07-01 audit — taken on trust, not re-measured here):**
- **Class A (orphan/duplicate):** a stale root `STATUS.md` duplicates `knowledge/STATUS.md` and still
  points at pre-reorg paths; invisible to normal use (boot reads only `knowledge/STATUS.md`) but wrong
  if opened.
- **Class B (stale "not yet built" claims):** suppression, pipeline-failure alerting, and off-machine
  backups are all described as planned/not-built in various docs while shipped in reality (e.g.
  `compliance/README.md:27,92-96`, `home-server-deploy.md:563-567`, `dpia.md:45`).
- **Class C (stale path citations):** references to retired paths (`plans/open-issues.md`, `ai-docs/`)
  and a stale absolute local path (`landing-page.md:119`).
- **Class D (intra-doc contradiction):** `stripe-billing.md:197-205` lists 3 webhook events against an
  authoritative 8-event table at `:44-53` in the same file — material, since an operator reading the
  wrong section under-subscribes real events.

**Coverage-gap table (why nothing caught the above):**

| Mechanism | Covers | Blind to |
|---|---|---|
| `sync_scaffold.py --check` | byte-convergence of manifest files | all per-repo knowledge, by design |
| `sync_scaffold.py --check-refs` | `knowledge/*.md` path citations in synced files, and canonical `` `file.md` § "Section" `` citations | non-`knowledge/` prose paths, bare mentions, orphans, freshness, contradictions (Classes A–D) |
| `scaffold_check.py` (pre-commit guard) | blocks staged edits to scaffold-managed files | orthogonal to content rot |
| `status_lint.py` | `STATUS.md` section-count/word-budget bounds + `decisions/INDEX.md` registry-line format & archive-pointer resolution | `questions/INDEX.md` content, reference/compliance/roadmap/review-backlog bodies, orphans, freshness, contradictions |
| archive-executor reconciliation | `STATUS.md`/`decisions/INDEX.md`/`questions/INDEX.md` for the change just shipped | reference runbooks, compliance, roadmap, review-backlog; cross-doc mentions of a shipped feature; orphan files |

**Scaffold-side verification performed 2026-07-02 (this repo):**
- `.claude/skills/` contains exactly the seven `openspec-*` skills (apply-change, archive-change,
  explore, onboard, propose, sync-specs, verify-change) plus `_shared` — **confirmed**, no
  `lint-knowledge` skill exists yet.
- `scripts/status_lint.py`, `scripts/sync_scaffold.py`, `scripts/scaffold_check.py` all **exist**; read
  in full/skimmed and their coverage matches the table above exactly — `status_lint.py` checks only
  `STATUS.md` bounds and `decisions/INDEX.md` line format/pointer resolution; `--check-refs` matches
  only `knowledge/*.md` paths (in synced files) and the `` §"Section" `` citation form.
- Both `.claude/agents/` and `.opencode/agents/` exist. **Correction to the source doc's plan:** these
  are agent *role definitions* (apply-executor, archive-executor, plus opencode-only
  openspec-reviewer/openspec-verifier/explore-flash), not skills — there is no `.opencode/skills/`
  directory at all, and per the `skills-in-dot-claude-only` decision (`knowledge/decisions/INDEX.md`,
  2026-06-13), opencode auto-discovers `.claude/skills/**` directly, so a second `.opencode/skills/`
  copy would be a divergence hazard, not a requirement. The source doc's §5 plan to ship the skill "both
  `.claude` and `.opencode`" is **superseded by this decision** — see §4.
- `.claude/skills/openspec-archive-change/SKILL.md` **exists**, confirming the archive-skill edit target.

## 3. Design decisions

- **Two-layer split**, both scaffold-managed (mirrors the source doc's §4 assessment):
  - **(a) Deterministic core — `scripts/knowledge_lint.py`**, cheap/CI-able, modeled on
    `status_lint.py`: orphan/duplicate canonical-file detection; retired-path tokens anywhere in
    tracked knowledge (`ai-docs/`, `plans/open-issues.md`, `docs/reviews/`, `/home/me/`, and similar);
    prose path-citation checking broadened beyond `knowledge/*.md` to any repo-relative `*.md`/dir cited
    in prose; dangling `openspec/changes/archive/<dir>/` pointers.
  - **(b) Judgment layer — a `lint-knowledge` skill** (LLM pass, the audit made repeatable): flags
    "not yet built"/"planned" claims that contradict a shipped archive entry or `STATUS.md` (Class B);
    intra-doc contradiction sweeps (Class D); a buried-gate sweep of README/runbook items missing from
    `questions/INDEX.md` Active.
  - Cadence: run at archive (folded into the archive skill) and/or as a periodic operator-invoked pass.
- **The mechanism belongs in the scaffold**, not psc-monitor alone, so `sync_scaffold.py` propagates it
  to every downstream repo. Per-repo *content* corrections (the Class A–D backlog) stay manual per-repo
  follow-on work — this change makes that sweep *triggered and checkable*, not automatic content-fixing.
- **Ship the skill as `.claude/skills/lint-knowledge/SKILL.md` only** (no `.opencode/skills/` copy),
  per the verified `skills-in-dot-claude-only` decision — both harnesses discover it from that one path.
- **One addition beyond the source doc:** once `plans/deterministic-tooling-layer/explore-brief.md` D9
  ships `knowledge/audit-log.md` in its own lintable one-line registry format, `knowledge_lint.py` should
  also check that registry's line format — cross-referenced there as a free add-on for this linter.

## 4. Proposed change scope

- **In scope:** `scripts/knowledge_lint.py` + tests; the `lint-knowledge` skill in `.claude/skills/`
  only (per §3, correcting the source doc's dual-harness assumption); `scaffold_manifest.txt`
  additions for both; the `AGENTS.md` reconciliation-brief span edit widening the archive-time sweep
  beyond the three named trackers; the `openspec-archive-change` skill edit to fold in the judgment pass.
- **Out of scope:** the per-repo Class A–D content burndown in psc-monitor (a follow-on downstream
  change); any automated rewriting of prose — the linter detects, it never fixes.
- **Proposed tier: COMPLEX/UNCERTAIN** (the source doc's own estimate) — touches `AGENTS.md` spans, adds
  a new skill and a new script, edits the archive skill, and propagates to every downstream repo.

## 5. Open items for the operator

- Tier confirmation (COMPLEX/UNCERTAIN) — no other blocking ambiguity carried over from the source doc.
- **New, found during verification:** should `knowledge_lint.py`'s retired-path token list be hardcoded
  in the script, or externalized per-repo (e.g. a small config file), so each downstream repo's own
  retired-path history doesn't require editing the scaffold-managed script upstream every time?
- **New:** the audit-log.md registry-lint addition (§3) depends on `deterministic-tooling-layer` D9
  actually shipping `knowledge/audit-log.md` first — should this change stub that check in behind a
  file-exists guard now, or defer it to a small follow-on once that file exists?
- **New:** "fold into the archive skill" (§3 cadence) could mean the archive-executor always runs
  `knowledge_lint.py`, or only surfaces it as an available check — worth pinning down in propose since
  it affects archive-time latency for every future change.

**From the direction-gate review (2026-07-02, `premise-review.md`) — resolve at propose:**
- Integration: does `knowledge_lint.py` subsume, coexist with, or replace the path-citation
  scanning already in `sync_scaffold.py --check-refs`?
- Cadence split: the deterministic layer is cheap enough for CI/every-archive; the LLM judgment
  layer is not (periodic/operator-invoked) — design the two cadences separately.
- Division of labor with `status_lint.py`'s existing `decisions/INDEX.md` archive-pointer check
  when broadening dangling-pointer detection.
- 💡 candidates: a small known-stale/known-fresh test corpus for smoke-testing the LLM layer;
  an explicit "out of scope: non-markdown files" note; per-repo config for retired-path tokens
  (reviewer recommends the config).

## 6. Provenance & caveats

Transplanted 2026-07-02 by a Sonnet subagent under a Fable orchestrator session. All scaffold-side
claims above (skills listing, script existence and coverage, dual agent dirs, archive-skill existence,
the `skills-in-dot-claude-only` decision) were independently re-verified against this repo on
2026-07-02. The psc-monitor-side findings (the drift inventory in §2) are taken on trust from the
2026-07-01 audit and were **not** re-measured by this session.
