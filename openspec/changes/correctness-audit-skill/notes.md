# Notes — correctness-audit-skill

## Acceptance criteria
Change-specific acceptance criteria live in `design.md` § Verification (authored and
reviewed at propose). Verify results will be recorded here at verify time.

## Sequencing (load-bearing)
- **Apply-order dependency on `lesson-check-ratchet` (OW-2):** do not apply this change
  until OW-2's apply lands `knowledge/ratchet-log.md`, its `_check_ratchet_log` lint,
  and the archive/run-audit triage text in the live tree. The skill text cites that
  interface as live behavior.
- **OW-2's apply session must first make its one-word normative fix** (its closure
  requirement fails `openspec validate --strict` SHALL-detection; gap-analysis
  OUTSTANDING-WORK.md finding 1). OW-5 cites OW-2 by requirement names and interface
  shapes (triage questions, ledger line format, disposition keywords), which that fix
  does not alter; if OW-2's apply changes anything beyond that word, re-check this
  change's citations before applying.
- **No dependency in either direction on `verify-stack-redirect` (OW-3).** If OW-3
  applies before this change (recommended batch order: OW-2 → OW-3 → OW-5), this
  change's verify runs under the post-OW-3 contract: COMPLEX = self → pro behavioral →
  flash lens pass (test-quality default). If OW-3 has not applied, verify runs under
  the pre-OW-3 contract (self → pro → flash same-checklist).

## Carried caveats (from review rounds — for verify/archive)
- **Graduation log is not lint-enforced.** The D8 dossier lint checks IDs, census
  dispositions, and `Prior:`/`Class:` presence; the graduation log (spec-required,
  append-only evidence trail) has no deterministic check — by design (D8 scopes to
  core format checks). The verify pass should eyeball the skill text's graduation-log
  template; a future audit that ships without one is a drift signal for
  knowledge-drift-review, not knowledge_lint.
- **First-real-audit manual check** (design § Verification, not unit-testable):
  confirm wave-gate triage-file appends keep graduated findings out of the
  `untriaged-finding-stale` bucket during a live audit.
- **Requirement-split suggestion declined** (specs round 2 💡2): the triage-file and
  ratchet-routing behaviors are one invariant ("no ID leaves untriaged, nothing closes
  silently") — recorded here so archive doesn't reopen it.

## Post-freeze input (2026-07-11, from psc-monitor — does NOT reopen the freeze)
A downstream coverage-gap review (psc-monitor
`plans/audit-correctness-quality/coverage-gaps-2026-07-11.md`) surfaced two audit-protocol
failure modes outside this change's frozen scope: **silent wave-drop** (chartered discovery
waves fell off every tracker when a remediation program took over the "wave" namespace —
pull-only invocation + dossier-internal state can't defend against the dossier not being read)
and **scope blind spots** (census-as-stopping-rule proves completeness within the chartered
surface list; it cannot row a dimension the charter never enumerated — psc had five such, one an
S4-class live gate). Queued as **OW-15** (apply strictly after this change), evidence at
`knowledge/research/scaffold-gap-analysis-2026-07/psc-coverage-gap-review-2026-07-11.md`.
Verify session: awareness only — do not fold into this change without operator direction.

**Second convergence (2026-07-12, extrends):** extrends independently executed the same blind
close-out review against its four-wave audit (method validated n=2; psc's backup blind-spot
class fired against extrends on first cross-repo use). OW-15 widened in place — notably
**Delta 4: post-close coverage-liveness ledger** (code shipped after a clean close-out is
unaudited by construction; ledger + mini-wave trigger, reference impl in extrends) and several
Delta-3 checklist widenings. Evidence:
`knowledge/research/scaffold-gap-analysis-2026-07/extrends-coverage-gap-review-2026-07-12.md`.
Same rule: awareness only — OW-15's apply consumes this, not this change's verify.

**Third input (2026-07-12, psc CG9 strategy pressure-test):** the blind-diff method validated a
third time, first in a NON-code domain (business thesis) — and found a launch-gate defect class
structurally invisible to this skill's object/oracle direction (pricing copy selling unbuilt or
unreachable features; code-as-object audits pass a dead-but-correct path by construction). OW-15
widened again in place (Delta-3 classes 9–12: copy↔capability claims ledger; entitlement-state
reachability; severity-taxonomy completeness prompt; source-class labeling for durable
web-sourced claims) plus a Delta-2 method note (evidence fan-out and blind list are BOTH
load-bearing — the top-severity findings came from evidence, not the blind list). The inverse
audit class itself is registered as **OW-16** (`product-audit` skill) — no interaction with this
change's frozen scope in either direction. Evidence:
`knowledge/research/scaffold-gap-analysis-2026-07/psc-strategy-pressure-test-2026-07-12.md`.
Same rule: awareness only.

## Orchestrator routing (operator-recorded verdicts, 2026-07-11)
- **Park verdict:** parked apply blocks nothing — OW-3 has no dependency on OW-5, and
  no backlog item waits on OW-5's apply. OW-5 itself waits on OW-2's apply.
- **Apply/verify orchestrator: Opus** (Fable not needed). Artifacts pin contracts,
  formats (verbatim ledger/triage/label sets), anchors, and budgets; apply is delegated
  to deepseek-flash regardless. **Escalation caveat:** implementation bugs and prose
  deviations from the frozen templates are normal defect-path work (fix-forward); a
  DESIGN-level defect (ratchet interface doesn't fit as frozen, lens/verify-chain
  interaction surprises, census/stopping-rule contract wrong) → stop and escalate to
  the operator or a Fable session rather than redesigning mid-verify.

## VERIFY CHECKPOINT (2026-07-13, Opus orchestrator) — READY for archive

**1. Verdict:** READY for archive. COMPLEX chain complete: self-review READY → pro behavioral
(deepseek-v4-pro) READY → flash lens (test-quality) READY → simplicity gate clean. Full gate green.

**2. Confirmed by eyeballing live output (behavioral, not counts):** built a real conforming
dossier from the SKILL's LITERAL inlined template blocks (charter marker + the 4 example census
rows + the filled `CA-W1-3` finding) → `knowledge_lint: OK`. A deliberately-broken dossier flagged
exactly the three contract violations — duplicate finding ID (reported with both file:line
locations), invalid census disposition (with the valid-set message), and a graduated finding
missing `Prior:`+`Class:`. The pro verifier independently reproduced this and ran a mutation probe
(removing `Prior:` fires a finding). The lint fires as designed on real content; the templates
round-trip clean.

**3. Defects found + how fixed + who:**
- Self-review: one skill typo (wave-gate step 5 "des not"→"does not") — fixed inline (trivial).
- Pro behavioral pass (deepseek-v4-pro) surfaced 4 🟡, all confirmed from disk, all fixed via ONE
  re-delegated deepseek-flash fix-spec (one attempt, clean, no Sonnet): (a) dead `_NON_LEAD_EVIDENCE_RE`
  regex removed; (b) skill census prose "Tab-separated or pipe-separated" narrowed to "Pipe-separated:"
  to match the pipe-only lint; (c) skill Evidence template now states the spec's disqualification
  rules (bare "confirmed" invalid; `VERIFIED-BY-repro` without a named path disqualified); (d) skill
  graduation step now states the spec's `UNVERIFIABLE-HERE → Class: none (one-off)` default.
- Simplicity gate (2 parallel finders) surfaced 3 behavior-preserving nits; 2 folded (use `_relpath`
  helper; collapse redundant `startswith`) — re-delegation was killed, so applied inline as trivial
  one-liners + ruff-format; 1 parked (single-pass FINDINGS read).
- Flash lens pass: READY, no defects.
- **No Sonnet fallback used anywhere in this change.**

**4. As-built delta (beyond the frozen artifacts):** the 4 pro-pass fixes make the shipped SKILL/lint
MORE faithfully encode the two frozen spec deltas (which are unchanged) — the skill now explicitly
carries the spec's evidence-label disqualification rules and the UNVERIFIABLE Class default, and the
census delimiter prose matches enforcement. Plus dead-code removal and 2 lint cleanups. None alters
the delta-spec text being promoted; these tighten the implementation to the spec, not vice-versa.

**5. Forward-looking items (fold into knowledge/questions/INDEX.md at archive):**
- **Dossier-lint format-robustness limits (v1, by design):** the census check parses ONLY
  pipe-separated rows with no leading pipe. Tab-separated rows are silently skipped; a markdown-table
  census (leading `|` + a `---` separator row) would mis-column the disposition / false-positive on the
  separator. Documented format is pipe-no-leading-pipe. Candidate future hardening if a downstream
  census is authored as a table.
- **Round-trip is fixture-similarity, not literal-template extraction:** no test extracts the SKILL's
  fenced CENSUS/FINDINGS template block and runs it through the lint, so a future SKILL-template edit
  that drifts from the parser has no deterministic catch (same class as the graduation-log-not-
  lint-enforced gap). Concrete fix available: a test that extracts the fenced template and asserts it
  lints clean. **This is the one genuinely generalizable class from this change — decide its ratchet
  disposition at archive Step 6 (candidate `test:` follow-on, not a waiver).**
- **(c) parser fragility:** a stray `### ` subheading inside a finding body truncates entry-collection
  and could skip the Prior/Class check (false negative); and "graduated" is keyed off the FINDINGS
  evidence label, not the census disposition (a census `AUDITED-finding` left `LEAD` in FINDINGS
  escapes the check). Both require non-template input; noted by the correctness finder. Low priority.
- **Simplicity finding 1 parked:** merge the two `FINDINGS*.md` read loops in `_check_audit_dossier`
  into a single pass — behavior-preserving, low value on tiny files → route to the existing
  `ratchet-lint-cleanup` parked follow-on.
- **Pre-existing README staleness (out of scope):** root `README.md:19` still lists a removed
  `onboard` skill in "the 7 workflow skills". Unrelated to OW-5 (which touched no README vocabulary);
  flag for a future doc cleanup, do NOT fold here.
- **Carried from freeze (reconfirmed):** graduation log is not lint-enforced (D8 scope, by design);
  first-real-audit manual check (wave-gate triage appends keep findings out of the 14-day
  untriaged bucket — not unit-testable); OW-15 amends this capability and applies strictly AFTER it.

**Still owned by archive (do NOT reconcile here — write-discipline):**
- `knowledge/STATUS.md` — add the OW-5 shipped section (≤3-cap: drop oldest narrating section).
- `knowledge/decisions/INDEX.md` — one registry line for `correctness-audit` (new capability) →
  archive dir; note `knowledge-lint` modified (dossier check).
- `knowledge/questions/INDEX.md` — park the field-5 forward items above.
- **Spec promotion:** sync the 2 delta specs → `openspec/specs/`: ADD `correctness-audit/spec.md`
  (new capability), MERGE the `knowledge-lint` ADDED requirement into the existing knowledge-lint spec.
- **Ratchet self-application (archive Step 6, PRIMARY's job):** run the 3-question triage over the
  found-and-fixed defects; the template↔parser round-trip gap (field 5) is the one generalizable
  candidate — decide check/test/waiver/open. Most other slips are Q2=no one-offs (no entry).
- Downstream propagation (extrends/psc-monitor) — operator-gated and DEFERRED.
