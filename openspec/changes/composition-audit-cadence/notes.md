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
