## Why

Per-change verify is single-diff-scoped by design, so a subsystem accreted from many
individually-approved changes is never reviewed as a whole — and nothing in the scaffold
ever names the occasion to do so. Downstream evidence (see `research/gap2-evidence.md`):
extrends accumulated ~45 archived changes with zero whole-repo review until a hand-provoked
audit found ~33 live defect classes that had each passed green per-diff verify; defect
shapes re-shipped in sibling modules days-to-weeks apart. The instruments already exist
(jscpd/vulture/radon in `checks.py`, `audit_scope.py scan` hotspot ranking,
`knowledge-drift-review`) and the staleness signal (`commits_since` the last audit tag) is
already computed — but the detectors are off-by-default, the signal is read by nothing, and
composition findings have no routed close-out. The scaffold has whole-repo *instruments*
but no whole-repo *occasions*; composition review currently depends on operator heroics.

## What Changes

- **New `composition-audit` capability**: a deterministic, count-based, advisory staleness
  signal ("composition audit due") plus an operator-invoked `composition-audit` skill — a
  cheap recurring ceremony (one-shot heavy-detector sweep + bounded LLM composition pass
  over top-ranked hotspots) with a machine-discriminable verdict
  (`COMPOSITION: CLEAN | FINDINGS-ROUTED | ESCALATE`) and a close-out that routes
  generalizable findings into the finding-closure ratchet (frozen in `lesson-check-ratchet`).
- **Composition-discriminable anchor**: the ceremony concludes with an operator-gated
  composition-anchor tag in the existing `audit/*` family (laid via `audit_scope.py`), which
  is the only event that resets the composition cadence clock. A plain `run-audit` tag never
  resets it (it runs no composition detectors — letting it satisfy the trigger would
  silently mask composition debt).
- **`outstanding` fact surfaces the due-signal**: the trigger computation
  (archived-changes-since-composition-anchor ≥ N, commits-since fallback) is exposed in the
  pull-only `outstanding` fact snapshot, where outstanding work is already enumerated.
  **Signal-visibility trade-off (carried to design, explore-brief open question 5):** a
  pull-only surface depends on operator attention — the same failure mode this change
  addresses. Design MUST explicitly decide whether the signal also gets a non-gating notice
  on a recurring surface (never a gate); if declined, the residual attention-dependence is
  stated in the skill, not left implicit. Design must also resolve the signal's structural
  shape in the fact — a standalone due-signal block vs a virtual source in the enumeration
  — since a computed trigger does not fit the existing "configured source with
  `source:line` provenance" model as-is.
- **Small engine plumbing** (exact shape in design): a one-shot mechanism to run disabled
  heavy-tier checks without flipping per-repo config; a standing composition-baseline
  pointer so `checks.py --baseline` delta-diffing works across ceremony runs without
  hand-carried paths; the anchor/count computation; a per-repo threshold config key.
- **Escalation seam to `correctness-audit`**: an `ESCALATE` verdict is a recommendation to
  charter a heavyweight correctness audit (frozen in `correctness-audit-skill`) —
  recommendation only; chartering stays operator-gated.
- **Never a gate**: the signal and ceremony never block commits, verify, or CI; no
  autonomous invocation; heavy detectors are not enabled by default downstream.

**Success criteria (headline; design derives acceptance criteria from these):**
- SC1 — the `outstanding` fact exposes a deterministic due-signal computed from
  archived-changes (and commits-since fallback) since the last composition anchor.
- SC2 — a plain `run-audit` tag does NOT reset the composition cadence clock; only a
  composition-anchor tag does.
- SC3 — the ceremony emits exactly one of the three machine-discriminable verdicts, and a
  FINDINGS-ROUTED close-out produces ratchet-ledger lines conforming to the frozen OW-2
  format plus one audit-log line.

## Capabilities

### New Capabilities
- `composition-audit`: cadence-trigger semantics (composition anchor, counting rules,
  per-repo threshold, advisory placement), ceremony contract (preconditions, deterministic
  sweep, bounded judgment pass, verdict values), and close-out routing (ratchet
  triage-then-append, audit-log line, operator-gated anchor tag, escalation
  recommendation).

### Modified Capabilities
- `outstanding-work-view`: the `outstanding` fact gains a composition-audit due-signal
  section (deterministic, provenance-carrying, advisory-only).
- `knowledge-lint`: the audit-log registry-line check accepts the composition-anchor
  variant (stays lintable); whether a **non-gating** composition-staleness notice is added
  (parallel to the untriaged-age check, but never failing the run) is a design decision —
  if design adopts it, its requirement lands in this delta.

## Impact

- **New files**: `.claude/skills/composition-audit/SKILL.md` (scaffold-managed;
  `scripts/scaffold_manifest.txt` entry).
- **Modified scripts**: `scripts/outstanding.py` (due-signal), `scripts/audit_scope.py`
  (composition-anchor tag variant), `scripts/checks.py` (one-shot heavy-check mechanism,
  baseline pointer, config-key schema note in the docstring), `scripts/knowledge_lint.py`
  (audit-log line variant; possibly the non-gating notice). Tests beside each in
  `scripts/test_*.py`.
- **Frozen-contract seams consumed (no edits to them)**: `lesson-check-ratchet`'s ledger
  format + 3-question triage (OW-2); `correctness-audit-skill`'s protocol marker as the
  escalation target (OW-5). Apply is therefore **gated on OW-2's apply and ordered after
  OW-5's** (recommended batch: OW-2 → OW-3 → OW-5 → OW-6). **Rework risk:** OW-2 is frozen
  but not yet exercised in apply; if its apply surfaces a contract change (ledger format,
  triage questions, disposition taxonomy), OW-6's close-out design needs rework — the
  freeze boundary is the contract, not the artifact.
- **Cross-change spec-collision note**: `correctness-audit-skill` (frozen, unapplied) also
  carries a `knowledge-lint` delta. The two deltas touch different requirements (dossier
  lint vs audit-log-line variant) but land in the same capability spec — archive them in
  apply order and manually check for collision at each archive (the known roadmap gap
  "cross-change spec-conflict detection at archive" applies). Design MUST state the exact
  audit-log-line formats the lint accepts (plain and composition-anchor variants) so the
  collision surface is visible before either change archives.
- **Downstream**: propagates via `sync_scaffold.py`; per-repo `checks.toml` remains the
  place a repo tunes the threshold or opts out; no downstream behavior changes until an
  operator invokes the skill or pulls the fact.
