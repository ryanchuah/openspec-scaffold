## Context

Frozen proposal: this change creates the missing whole-repo *occasions* — a deterministic
composition-audit due-signal plus a cheap operator-invoked ceremony — over instruments the
scaffold already ships. Evidence and contracts in `research/` (five digests). Constraints:
stdlib-only Python; both harnesses load the skill; never a gate; no autonomy; findings
route into `lesson-check-ratchet`'s frozen ledger seam; escalation names
`correctness-audit-skill`'s protocol. Key present-state facts (verified against source):

- `checks.py --check NAME` already runs a registered-but-disabled check (`_mode_check`
  consults availability only, checks.py:1168–1198); `--baseline` is `--report`-only
  (checks.py:1439); baseline diffing is fingerprint-based (`_baseline_diff`,
  checks.py:1090).
- `audit_scope.py` lays annotated `audit/<date>` tags (`cmd_tag`, :309–310), prints the
  registry line `- **<date>** · audit/<date> · <short-sha> · <essence>` (:363); anchor
  discovery is `git tag --list 'audit/*' --sort=-creatordate` (:131–132).
- `knowledge_lint.py` pins the audit-log line to regex
  `^- \*\*\d{4}-\d{2}-\d{2}\*\* · audit/\d{4}-\d{2}-\d{2} · [0-9a-f]{7,40} · \S.*$` (:147).
- The `outstanding` fact reads `[facts.outstanding]` from the per-repo `checks.toml`
  (outstanding.py:40–51) and emits a JSON payload + rendered markdown (outstanding.py:569–607).

## Goals / Non-Goals

**Goals:**
- G1 — a deterministic, advisory, count-based due-signal (SC1/SC2 of the proposal).
- G2 — a bounded, cheap, operator-invoked `composition-audit` ceremony with a
  machine-discriminable verdict (SC3).
- G3 — close-out that routes generalizable findings into the frozen ratchet seam and
  resets the cadence clock via a composition-discriminable anchor.
- G4 — reuse of existing surfaces (checks report machinery, audit_scope tag/log-line,
  D5 pre-digest shape, D6 baseline diffing) over any parallel invention.

**Non-Goals:**
- Any gate, CI wiring, cron, or autonomous invocation.
- OW-5's charter/census/wave machinery (shared vocabulary only: `Class:` slugs, ratchet
  routing).
- Changes to the per-change verify chain (OW-3 owns it).
- Enabling jscpd/vulture/radon by default in any repo.
- Auto-remediation; the ceremony reports and routes, never fixes.

## Decisions

**D1 — Composition anchor = `audit/<date>-composition`, laid by `audit_scope.py tag
--kind composition`.** Same `audit/*` family, same annotated-tag mechanics, same
operator-gated sole-mutation contract. `cmd_tag` and `cmd_log_line` gain an optional
`--kind composition` (default `plain`, emitting today's exact behavior byte-for-byte).
Because `_latest_audit_tag()` globs `audit/*`, a composition anchor automatically also
counts as a general audit anchor (deliberate superset — a composition ceremony subsumes a
checks report). The converse is blocked by construction: composition-anchor discovery
globs `audit/*-composition` only, so a plain run-audit tag can never reset the
composition clock (premise-review 🟡1). Same-date collisions are impossible (distinct tag
names). *Alternative rejected:* a separate `composition/*` namespace — breaks the
superset property, needs new lint/log formats and a second discovery path.

**D2 — Audit-log line formats (exact, for the lint and the collision check):**
- plain (unchanged): `- **YYYY-MM-DD** · audit/YYYY-MM-DD · <short-sha> · <essence>`
- composition: `- **YYYY-MM-DD** · audit/YYYY-MM-DD-composition · <short-sha> · <essence>`
`knowledge_lint.py` line-147 regex changes to accept `audit/\d{4}-\d{2}-\d{2}(-composition)?`.
This is the entire `knowledge-lint` delta (see D8 for the declined notice), and it cannot
collide with `correctness-audit-skill`'s dossier-lint delta (different requirement,
different code region); the archive-order manual check from the proposal still applies.

**D3 — Due-signal computation lives in `outstanding.py` as a standalone top-level block,
not a virtual source** (resolves proposal's structural-shape mandate). New payload key:
```
"composition_audit": {
  "anchor_tag": "audit/2026-07-11-composition" | null,
  "archived_changes_since": <int>, "commits_since": <int>,
  "thresholds": {"changes": N, "commits": M},
  "due": <bool>, "reason": "<one line>", "status": "ok" | "no-git",
  "computed_from": "git"
}
```
(`computed_from` marks the signal's provenance explicitly, since it is computed from git
state rather than enumerated from a configured source like every other outstanding item.)
Rendered markdown gets a `## Composition audit` section (placed directly under the
header when `due`, at the bottom otherwise). Counting rules:
- `archived_changes_since` = count of distinct top-level dirs under
  `openspec/changes/archive/` introduced in `<anchor>..HEAD`
  (`git diff --name-only --diff-filter=A <anchor>..HEAD -- openspec/changes/archive/`,
  first path component under `archive/`, deduplicated — added files only, so a
  post-archive edit to an existing archived dir never inflates the count). No anchor →
  count all archive dirs (a mature never-audited repo reads DUE immediately — correct:
  that is extrends).
- `commits_since` = `git rev-list --count <anchor>..HEAD`; no anchor → from root.
- `due = archived_changes_since ≥ N or commits_since ≥ M` (OR co-fire resolves the
  sparse-archive mixed signal from the premise review's 💡).
- Any git failure → `status: "no-git"`, `due: false`, never crashes the fact (the
  existing D2-degradation house pattern). One named exception: an anchor tag whose
  commit is unreachable (force-push/rebase) degrades to **no-anchor semantics** — count
  all archive dirs, `reason` says why — rather than being mislabeled `no-git`; loud and
  conservative beats silently not-due.
*Alternative rejected:* archive-dirname date parsing (same-day boundary ambiguity;
`git diff` name-listing is exact and rename-stable enough for count purposes).

**D4 — Thresholds: `[facts.outstanding] composition_change_threshold = 10`,
`composition_commit_threshold = 100`** (per-repo overridable; schema documented in the
`checks.py` docstring alongside the existing `[facts.outstanding]` keys). Calibration is
judgment, anchored on the evidence bounds: recurrence shipped days-to-weeks apart and
~45 unaudited changes was catastrophically late, so the defaults aim an order of
magnitude earlier; repos tune from there. The spec is normative for the default values;
the `checks.py` docstring documents the keys (as the sole `checks.toml` schema doc) and
the skill cites the spec.

**D5 — One-shot sweep = `checks.py --report --include <name>` (repeatable flag), not a
new runner.** `--include` treats a registered-but-disabled check as enabled for THIS
report run only; everything else is inherited free: dated `output/checks/<date>/` dirs,
`--resume`, `--baseline` diffing, preflight. If the named check is already enabled,
`--include` is a no-op — the check runs exactly once. Preflight consequence is deliberate: with
composition detectors force-included, a missing jscpd/vulture binary fails the run with
the existing install-or-disable guidance (exit 3) — the ceremony explicitly wants those
tools, so failing loudly beats a silent coverage gap (`--check`'s silent
"skipped/exit 0" is exactly why the ceremony does NOT use it). `--include` with an
unknown name → INFRA-FAIL exit 3. *Alternatives rejected:* per-check `--check` loop (no
baseline support, silent skips, no unified findings.json); permanent config flip
(violates never-enable-by-default).

**D6 — Standing baseline pointer: `output/checks/composition-baseline.json`.** At
close-out the skill copies the run's `findings.json` to that path; the next ceremony
passes it via `--baseline` when present. First run (or post-clean checkout) has no
baseline: the delta degrades to "everything is new," and the skill says so explicitly
(no silent cap). The pointer is untracked like all of `output/`; a repo MAY commit it
(per-repo policy, skill mentions the option once). *Alternative rejected:* discovering
the previous dated report dir via the audit log — output dirs are cleanable, the log is
ephemeral-by-design, and a copy is one `cp`.

**D7 — Ceremony shape (the `composition-audit` skill, operator-invoked):**
1. **Wiring detection** — reuse run-audit's missing-layer branch (absent `checks.toml`
   → guide the build-out, stop).
2. **Signal read** — regenerate the `outstanding` fact; report the due-state. The
   ceremony never requires `due` (an early run is always allowed and also resets the
   clock).
3. **Deterministic sweep** — `checks.py --report --include jscpd --include vulture
   --include radon` (+ `--baseline` per D6), then `audit_scope.py scan` for
   delta-since-anchor hotspot ranking. INFRA-FAIL stops the ceremony with the preflight
   guidance verbatim.
4. **Pre-digest (delegated, cheap model)** — the D5-campaign shape from
   `deterministic-tooling-layer`: cluster/dedupe the detector wall + baseline delta +
   hotspot ranking into a shortlist, checkpointed to the report dir. Delegation uses the
   standard hardened harness; the pre-digest is extraction, not judgment.
5. **Bounded judgment pass (orchestrator)** — top-K hotspots (default K=5; the spec is
   normative for the default, the skill cites it) reviewed through the composition lens: sibling/near-duplicate drift, accreted
   duplication, cross-module invariant coherence, dead-code clusters, doc/code drift.
   Findings get `Class:` slugs (vocabulary shared with the ratchet and OW-5).
6. **Verdict** — exactly one of `COMPOSITION: CLEAN | FINDINGS-ROUTED | ESCALATE`,
   written to `<report-dir>/composition-verdict.md`. ESCALATE is indicated when findings
   suggest a systemic class beyond the mechanical slice — named indicators: ≥2 distinct
   cross-module classes, any correctness-suspect finding (not just hygiene), or a
   baseline delta that grew after the previous FINDINGS-ROUTED close-out. ESCALATE
   recommends chartering a `correctness-audit` (OW-5 protocol); chartering remains
   operator-gated.
7. **Close-out** — per generalizable finding, the frozen OW-2 3-question triage →
   ratchet-ledger line (frozen format, verbatim); one audit-log line (D2 composition
   variant); operator-gated `audit_scope.py tag --kind composition`; copy findings.json
   to the D6 pointer. The close-out step is the skill's own (OW-2 pins no hook; this
   mirrors run-audit's Step-3 triage-then-append shape). Per OW-2's SHALL
   (`lesson-check-ratchet` `specs/finding-closure-ratchet/spec.md`), the triage is
   performed by the orchestrating agent — judgment work, never delegated to a mechanical
   executor, and never blocking on building a detector.
Cost bound stated in the skill: one cheap-model pre-digest + one orchestrator pass over
K hotspots — an afternoon, explicitly positioned below OW-5.

**D8 — Signal visibility: v1 is pull-surfaced; the recurring-surface notice is DECLINED
for v1, with a named revisit trigger** (resolves explore-brief open question 5 /
premise-review 🟡2 / proposal mandate). Where the signal appears: every `outstanding`
fact regeneration (any `outstanding-work-review`), every ceremony, and run-audit's
inventory read (the `inventory` fact's existing `audit_anchor` block gains a sibling
`composition_anchor` with the same fields — near-free since `_latest_audit_tag` already
exists). The two inventory fields are **siblings, not nested**, and deliberately diverge
after a plain run-audit tag: `audit_anchor` tracks the latest `audit/*` tag of any kind
(a composition tag counts — the superset), while `composition_anchor` tracks the latest
`audit/*-composition` tag only. Commit-time lint output is deliberately NOT used: every commit-time surface in
this repo is a gate or feeds one; `knowledge_lint` findings fail the live-tree pytest
gate, so a "warning" there either gates (banned) or requires inventing a non-failing
finding tier that trains operators to ignore lint output. The residual
attention-dependence is stated in the skill. **Revisit trigger (recorded here, actioned
as a follow-on):** if a downstream repo is observed sitting `due` for >30 days unseen,
add the recurring-surface notice then — as its own SMALL change.

**D9 — `knowledge-drift-review` stays outside the mandatory ceremony core** (resolves
brief open question 4): step 7 recommends it when the sweep or judgment pass surfaces
knowledge-tree drift, but the ceremony's mandatory core stays deterministic-plus-one-
bounded-LLM-pass. *Alternative rejected:* embedding it makes the afternoon ceremony a
day and duplicates an existing standalone skill's trigger.

**D10 — Skill file, manifest, and naming.** New `.claude/skills/composition-audit/SKILL.md`
(discovered by both harnesses per the existing decision), plus a
`scripts/scaffold_manifest.txt` entry. The ceremony sequence is stated once in the new
capability spec; the skill cites it (cite-don't-restate; the chain-shape-drift lesson
from the OW-3 session).

### Live Probe

Skipped — zero new external-API surface. All new surfaces are stdlib + git CLI
(`git tag`, `git diff --name-only`, `git rev-list`), and the tag/diff/rev-list
invocation patterns already run in this repo's existing scripts and tests; the new
counting logic is unit-tested on fixture repos (see Verification).

## Risks / Trade-offs

- [OW-2 contract shifts during its apply] → freeze boundary is the contract, not the
  artifact (proposal); apply order OW-2 → … → OW-6; if the ledger format changes, only
  D7 step 7 and the skill's close-out text need rework.
- [First-run detector wall] → D5 pre-digest + top-K bound + D6 baseline from cycle 2;
  the first run's triage cost is stated in the skill, not hidden.
- [jscpd/vulture false-negative risk oversold] → the skill's positioning text carries
  the honest limit verbatim (detectors catch the narrow mechanical slice; the judgment
  pass and the ESCALATE seam carry the rest) — evidence: W4-T4(b) in
  `research/gap2-evidence.md`.
- [Signal unseen if pulls lapse] → D8's revisit trigger; residual dependence stated.
- [Threshold miscalibration] → per-repo keys (D4), advisory-only placement bounds the
  cost of a wrong default to noise in one fact section.
- [`--include` misuse outside the ceremony] → harmless by construction: it only widens
  one explicitly-invoked report run, never persists state, and preflight still guards
  tool presence.

## Migration Plan

Ships as scaffold-managed files; propagates via `sync_scaffold.py` on the next
operator-gated sync. No data migration; no downstream behavior change until an operator
pulls the fact or invokes the skill. Rollback = the standard rollback-branch rule
(revert + corrective change). The first composition ceremony in a downstream repo doubles
as the first end-to-end exercise of the shared tag/log ceremony surface
(`knowledge/questions/run-audit-untested.md` gets partial closure evidence; feed findings
back here).

## Open Questions

None — the explore brief's six open questions and the proposal's three design mandates
all resolve here: Q1→D5, Q2→D6, Q3→D3/D4, Q4→D9, Q5→D8, Q6→D1/D2; signal shape→D3,
exact lint formats→D2, visibility decision→D8.

## Verification

Acceptance criteria (change-specific; the verify phase checks each):

- AC1 (SC1/SC2): unit tests on fixture git repos cover: no anchor at all (due when
  archive count ≥ N; extrends-shape), plain `audit/<date>` anchor only (composition
  clock NOT reset — the premise-review 🟡1 scenario as a frozen regression test),
  composition anchor present (clock reset; counts restart), thresholds honored from
  config, OR co-fire (commits threshold trips with sparse archives), git-absent
  degradation (`status: "no-git"`, `due: false`, fact still renders).
- AC2: `--include` runs a disabled registered check under `--report` (and only then);
  unknown name → INFRA-FAIL exit 3; missing included tool → preflight exit 3 with the
  standard guidance; no `--include` → today's behavior byte-identical.
- AC3: `audit_scope.py tag --kind composition` lays an annotated
  `audit/<date>-composition` tag; `log-line --kind composition` output matches the
  updated `knowledge_lint` regex; plain invocations are byte-identical to today;
  `knowledge_lint` accepts both variants and still rejects malformed lines.
- AC4: `inventory` gains `composition_anchor` with the same fields as `audit_anchor`.
- AC5: the skill file passes `scaffold_lint`; manifest entry present; the ceremony
  sequence appears only in the spec (skill cites it).
- AC6: full suite green (`scripts/check.sh`), including the scaffold SEAL and live-tree
  lint gates.
- AC7 (behavioral, at verify): a scripted end-to-end dry-run on a fixture repo walks
  ceremony steps 2–7 far enough to produce a findings.json, a baseline copy, a
  composition tag, and a lintable audit-log line (LLM steps stubbed as no-op findings).
