# Notes — composition-audit-cadence (OW-6)

**STATUS 2026-07-11: PROPOSE COMPLETE — PAUSED AT APPLY (operator-mandated pause).**
All 4 artifacts frozen; every review round PASSed with zero 🔴 on round 1 (proposal
AGREE, design, specs, tasks — see `review-log.md`); all 🟡 fixed pre-freeze;
`openspec validate --strict` clean at freeze. No reviewer-invocation crashes this
session (contrast OW-5's two salvaged kills — no operational debt carried).

## Apply-order gates (hard)

1. **OW-2 (`lesson-check-ratchet`) MUST apply first** — the skill's close-out cites the
   finding-closure-ratchet spec and appends to `knowledge/ratchet-log.md`, which OW-2
   creates.
2. **OW-5 (`correctness-audit-skill`) applies before OW-6** — the ESCALATE verdict
   recommends chartering via the correctness-audit skill, which OW-5 ships.
3. Recommended single Opus batch: **apply OW-2 → OW-3 → OW-5 → OW-6.**

## Verify-semantics note (for the apply session)

If the recommended batch order holds, OW-3 lands before OW-6, so OW-6's verify runs
under the NEW tier-keyed chain: COMPLEX = self → pro → **lens** pass. Lens choice:
**test-quality** (this change ships four test batteries; no data-path → data-scale not
applicable). If OW-3 has not applied when OW-6 verifies, the current chain
(self → pro → flash) applies instead.

## Post-freeze edit disclosure

One consistency edit to frozen `design.md` during the specs round (K-default ownership
wording: spec is normative, skill cites — one line, disclosed in `review-log.md` specs
entry). No other frozen artifact was touched after its freeze.

## Long-term paths (departing-principal notes, not this change)

- **The trigger machinery generalizes.** The same anchor+count staleness pattern can
  later drive `knowledge-drift-review` cadence and OW-5 correctness-audit scheduling —
  the composition-audit spec's trigger semantics were written to be reusable
  (anchor-glob + threshold + advisory placement). D8's 30-day revisit trigger is the
  named escalation path for signal visibility.
- **Future absorber:** the roadmap item "cross-change spec-conflict detection at
  archive" is composition-shaped; a later version of the composition ceremony could
  host it (the ceremony already reads repo-wide state at a cadence).
- **First downstream ceremony = live exercise of the shared audit surfaces.** It walks
  tag/log-line/wiring-detection end-to-end, providing partial closure evidence for
  `knowledge/questions/run-audit-untested.md` — feed findings back to the scaffold.
- **Threshold calibration is a guess to be corrected by data.** N=10/M=100 are
  evidence-anchored judgment, not derivation; the first two downstream cycles should
  revisit them (per-repo keys exist for exactly this).

## Verify checkpoint (2026-07-13, Opus orchestrator) — READY FOR ARCHIVE

Full verify walkthrough is in `review-log.md` (Verify phase section). Summary of the five
required fields:

**1. Verdict:** READY FOR ARCHIVE. COMPLEX chain ran clean: self-review → pro behavioral pass
(`deepseek-v4-pro`, READY/none) → flash test-quality lens pass (`deepseek-v4-flash`, READY/none)
→ simplicity gate. No Sonnet fallback anywhere. Full `scripts/check.sh` green.

**2. Live output eyeballed (behavior, no counts):** built a real tmp git repo and exercised the
whole surface — the `outstanding` due-signal read `due` at the archive-count threshold boundary
with the archive-count reason; a plain `audit/<date>` tag laid AFTER the composition anchor did
NOT reset the composition clock (the load-bearing premise-🟡1 regression); OR co-fire tripped on
the commit threshold with sparse archives; a git-absent input degraded to `status:no-git /
due:false` while the fact still rendered; `checks.py` inventory `composition_anchor` read the
full-history count when no composition tag existed and the composition tag (diverging from
`audit_anchor`) after a later plain tag; `audit_scope.py --kind composition` produced the
`audit/<date>-composition` annotated tag + the matching log-line; `knowledge_lint` accepted both
plain and composition audit-log lines and flagged a foreign `-security` suffix. The pro pass
independently reproduced all of these on its own tmp repo.

**3. Defects found + fixes (attributed):**
- **self-review, 🔴:** `checks.py` `_run_inventory` composition_anchor returned `commits_since:
  None` when no composition tag exists; spec requires the full-history count. The AC4 test also
  allowed `None`. → **re-delegated to a fresh deepseek `apply-executor`** (no Sonnet): no-tag
  branch now computes `git rev-list --count HEAD`; test asserts `int` == full-history count.
- **self-review, 💡:** `composition-audit/SKILL.md` step 4 told the read-only `openspec-reviewer`
  (`edit: deny`) to WRITE `pre-digest.md`. → **fixed inline**: reviewer emits the shortlist as
  text, orchestrator writes the checkpoint (idiomatic pattern).
- **self-review, 💡:** `knowledge_lint.py` docstring item-5 list indent drifted 3→4 spaces. →
  **fixed inline.**
- **simplicity gate:** a never-record-counts slip I introduced in `review-log.md` (a passing test
  tally). → **fixed inline.**
- pro pass and lens pass: no defects.

**4. As-built delta:** none beyond the fixes — the implementation conforms to all three spec
deltas. One frozen-`design.md` doc nit (NOT changed): its `archived_changes_since` counting note
says a "post-archive edit to an existing archived dir never inflates the count," but a post-archive
ADD of a new file would (diff-filter=A catches adds); the impl still matches the spec's literal
rule. Recorded as forward-looking below rather than editing frozen design.

**5. Forward-looking items (fold into `knowledge/questions/INDEX.md` Parked at archive; new
`composition-audit-cadence-follow-ons.md` pointer):**
- **Advisory-signal edge #1:** `archived_changes_since` counts a pre-anchor archive dir if a NEW
  file is added to it after the anchor. Impl matches the spec's literal "dir with ≥1 file added in
  range"; benign on an advisory never-gating signal; trigger violates the immutable-archive rule.
  If real repos hit it, tighten the spec rule/impl. Also fix design.md's edit/add conflation.
- **Advisory-signal edge #2:** the no-anchor branch counts on-disk dirs via `iterdir()` (incl.
  untracked) while the anchored branch uses git — inconsistent basis on untracked WIP dirs
  (benign-advisory, transient). Consider a git-based no-anchor count for a consistent basis.
- **Park to `ratchet-lint-cleanup`** (behavior-preserving, propagates later): `outstanding.py`
  duplicate `rev-list` blocks + duplicate no-git degraded-dict; `checks.py`
  `composition_anchor`↔`audit_anchor` shared-helper extraction (touches pre-existing
  out-of-scope `audit_anchor`); centralize the `audit/<date>-composition` literal across the 4
  modules that hardcode it; the `audit_scope.py` `getattr(args,"kind")` defensive fallback.
- **`audit_anchor` asymmetry:** `composition_anchor` returns the full-history count when no tag
  (its spec requires it); `audit_anchor` keeps its pre-existing null-when-no-tag. Align in a
  separate change if the operator wants parity (out of OW-6 scope).
- **Threshold calibration:** N=10 / M=100 are evidence-anchored guesses; the first two downstream
  cycles should revisit via the per-repo `[facts.outstanding]` keys (design D4).
- **D8 30-day revisit trigger:** if a downstream repo sits `due` >30 days unseen, add the
  recurring-surface notice as a SMALL change.
- **run-audit-untested partial closure:** the first downstream composition ceremony exercises the
  shared tag/log-line/wiring-detection surfaces end-to-end → feeds
  `knowledge/questions/run-audit-untested.md`.
- **Ratchet self-application (archive Step 6 — primary's job):** OW-6 ships templates/anchors/
  parsers (skill templates, the composition audit-log line format, the `knowledge_lint` regex).
  The OW-5 `open:since skill-template-parser-roundtrip` ratchet entry (template↔parser drift;
  enforcement = an extract-template lint test, not yet built) applies to OW-6 too. Verify did the
  eyeball round-trip manually (probe K + the pro pass) but did NOT build the extract-template lint
  test → the OW-5 `open:` entry stays open and age-flagged; OW-6 adds no new closeable disposition.

**Still owned by archive (delegated archive-executor reconciles; primary reviews + commits):**
- `knowledge/STATUS.md` — new OW-6 shipped section (≤150 words; ≤3-cap → drop the oldest change
  section).
- `knowledge/decisions/INDEX.md` — registry line(s) for OW-6 (composition anchor family D1/D2,
  count-based due-signal D3, `--include` D5, signal-visibility D8).
- `knowledge/questions/INDEX.md` — Parked: add a `composition-audit-cadence-follow-ons.md` pointer
  carrying the field-5 items above.
- **Spec promotion into `openspec/specs/`:** `composition-audit` (NEW → promote as `## Purpose` +
  `## Requirements`, NOT a bare title — `--type spec` requires Purpose); `outstanding-work-view`
  (confirm new-vs-merge); `knowledge-lint` (merge the regex-widening requirement on top of OW-5's
  set). Validate each with `openspec validate <cap> --type spec --strict`.
- `knowledge/ratchet-log.md` — archive Step 6 self-application (the OW-5 `open:` entry stays open;
  no new OW-6 disposition unless the extract-template test is built).
- Wider flag-only sweep (`knowledge_lint.py` + re-check `knowledge/roadmap.md`, `reference/`,
  Parked `questions/<item>` bodies) for stale claims re composition-audit.
- Downstream propagation of the scaffold-managed edits (manifest already updated) is
  **operator-gated and DEFERRED** — do not sync without fresh authorization.
- `HANDOFF.md` — the PRIMARY rewrites/deletes it (OW-6 is the last frozen item); the
  archive-executor does NOT touch it. Archive-executor also does NOT commit.
