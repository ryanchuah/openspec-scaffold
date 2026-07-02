# Notes — knowledge-lint

## Provenance
Transplanted from `psc-monitor/plans/knowledge-doc-drift-analysis.md` (2026-07-01 buried-open-items
audit) → `plans/knowledge-lint/` explore-brief → direction-gate `PREMISE: AGREE` (2026-07-02) → this
change. Tier: COMPLEX/UNCERTAIN. explore-brief.md + premise-review.md relocated into this change dir at
propose (D8 relocation).

## Propose-phase decisions
proposal.md Round-1 review (deepseek-v4-pro) passed clean (zero 🔴, `PREMISE: AGREE`) and deferred three
🟡 + a config 💡 to design. All resolved in `design.md` D1–D9:
- D1 detect-only everywhere; archive wider-sweep is flag-only (🟡1)
- D3 coexist with `sync_scaffold.py --check-refs` (🟡2)
- D2/D8 enumerated body scope (🟡3)
- D4 division of labor with `status_lint.py` archive-pointer check
- D5 retired-path defaults + optional per-repo `audit.toml [knowledge_lint]` (config 💡)
- D6 audit-log check file-exists-guarded
- D7 `lint-knowledge` skill single-path, operator-invoked cadence

## Session workflow overrides (operator, 2026-07-02) — load-bearing for apply
- **Code updates / apply phase:** delegate to a **Sonnet subagent** (Claude Agent tool, model=sonnet),
  NOT the default deepseek-v4-flash apply-executor via `opencode run`.
- **tasks.md review:** performed by a **Sonnet subagent only**, NOT the deepseek `openspec-reviewer`.
- proposal/specs/design reviews used the standard deepseek `openspec-reviewer` (proposal already frozen
  under it; specs + design reviewed under it).

## Verify checkpoint (2026-07-02)

**1. Verdict:** READY for archive. Self-review + deepseek-v4-pro verifier pass + deepseek-v4-flash
verifier pass all clean (VERDICT: READY, no defects); simplicity/quality gate passed (no duplication /
dead code / over-abstraction); security gate N/A (stdlib-only, no auth/creds/persisted-data/network —
the only subprocess is local `git`). tasks.md review was a Sonnet subagent (per operator); the apply and
the verify-phase fix were Sonnet subagents (per operator's code-updates→Sonnet directive).

**2. Live output eyeballed (behavior, not figures):** ran `python3 scripts/knowledge_lint.py` against the
scaffold's own `knowledge/`. Before the verify fix it was dominated by false positives (bare filename
mentions, cross-repo names, GitHub shorthand, non-path slashy tokens, and a git-ignored vendored
`OpenSpec/` clone). After the first-segment gate + git-ignore skip, it surfaces ONLY genuine drift /
forward-references and none of the noise classes. Confirmed detect-only (working tree byte-unchanged after
a run) and clean-vs-dirty exit behavior (0 clean / 1 on findings) directly. No external API → no live
smoke applicable.

**3. Defect found & fixed (attributed):** self-review found the broken-citation check was ~unusable noise
against real prose + the orphan walk scanned a git-ignored vendor clone. Fixed by re-delegation to a
**Sonnet** apply-executor (deepseek NOT used, per operator directive): added a first-segment gate (a
backtick token is a citation only if its first path segment is a real top-level dir under root, computed
dynamically) and a git-optional `git check-ignore` skip. Re-verified from disk: suite green, noise gone.

**4. As-built deltas discovered during verify (artifacts amended pre-archive):** design.md D2 gained the
first-segment gate + git-ignore-skip and VC2/2c/2d; specs/knowledge-lint gained the tightened
broken-citation scenario + `citation-first-segment-must-be-real-top-level-dir` +
`git-ignored-paths-skipped` scenarios. These were amended by the orchestrator (disclosed here + in
review-log) because implementation revealed the frozen "any repo-relative path" scope was unusably broad.
`openspec validate` green after amendment.

**5. Forward-looking items to fold into project docs at archive (fold into `knowledge/questions/INDEX.md`
Parked, and `knowledge/decisions/INDEX.md` where noted):**
- **Scaffold's own pre-existing knowledge drift the linter now surfaces (out-of-scope to fix here per
  proposal, but real):** `knowledge/roadmap.md` still recommends the retired `ai-docs/` path; `knowledge/
  lessons.md` cites `openspec/changes/fix-convergence-guard/` without its `archive/2026-06-17-` prefix;
  `knowledge/decisions/INDEX.md:38` mentions `ai-docs/` (judgment call — may be legitimate historical
  context). These want a per-repo content-cleanup follow-on.
- **Drift THIS change introduced (should be cleaned at archive):** `knowledge/questions/
  deterministic-tooling-layer-follow-ons.md:50` cites `plans/knowledge-lint/`, which this change relocated
  to `openspec/changes/knowledge-lint/`. The widened archive sweep this change ships should itself catch
  this (dogfood); fix the pointer during reconciliation.
- **Known-absent-by-design paths still flag (forward-references):** `knowledge/audit-log.md` (created
  per-repo when audits run), `scripts/test-cmd` (per-repo, legitimately absent here), `.opencode/skills/`
  (deliberately absent per the `skills-in-dot-claude-only` decision), and a cross-repo `plans/
  historical-reports.md` in `parked-psc-monitor.md`. OPEN QUESTION: add a known-absent/allowlist mechanism
  to drive these to zero, or keep enumerate-and-judge? Deliberately NOT added now (simplicity/YAGNI).
- **Downstream propagation (follow-on):** once archived, `knowledge_lint.py` + the `lint-knowledge` skill
  propagate to extrends/psc-monitor via `sync_scaffold.py`; each should then run a first `lint-knowledge`
  pass to burn down its own drift backlog (separate per-repo follow-on, per proposal). Note the
  deterministic-tooling-layer propagation is already frozen pending operator go-ahead (STATUS.md) — this
  change joins that pending-propagation queue.
- **Latent check:** the audit-log registry-format check is guarded on `knowledge/audit-log.md` existence;
  the scaffold has none yet, so that check is untested against real data until a repo grows one — monitor.
- **Simplicity suggestion (non-blocking):** a few token-exclusion predicates (`_is_url`,
  `_is_absolute_system_path`, `_has_whitespace`) are now partly redundant behind the first-segment gate;
  left as belt-and-suspenders, could be pruned in a future pass. Also the skill uses `python` not
  `python3` (mixed convention repo-wide; agents adapt) — minor.

**Still owned by archive (fresh archive-executor must reconcile — do NOT edit these now):**
- `knowledge/STATUS.md` — add a knowledge-lint SHIPPED section (drop oldest per the ≤3 cap).
- `knowledge/decisions/INDEX.md` — add the knowledge-lint decision registry line → this change's archive path.
- `knowledge/questions/INDEX.md` — Parked: fold in the field-5 follow-ons above.
- **Spec promotion:** create `openspec/specs/knowledge-lint/spec.md` (NEW) from the delta; merge the ADDED
  `archive-step-flags-wider-knowledge-drift` requirement into `openspec/specs/knowledge-organization/spec.md`.
- **Cleanup:** delete the untracked root `knowledge-doc-drift-analysis.md` backup and `tmp/`; the
  psc-monitor original of that doc is a separate-repo cleanup (operator/other session) per the explore-brief.
