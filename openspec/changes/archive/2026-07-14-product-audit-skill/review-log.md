# Review log — product-audit-skill

## Direction gate (explore) — `explore-brief.md` — 2026-07-14
Reviewer: openspec-reviewer @ deepseek/deepseek-v4-pro. **PREMISE: AGREE**, zero 🔴. Two 🟡
(ratchet-fit for non-code findings; claims-ledger staleness-lint not default-optional) + two 💡
(reciprocal awareness pointer; operator dual-literacy) folded into the brief. Full record:
`premise-review.md`.

## proposal.md — Round 1 — 2026-07-14
Reviewer: openspec-reviewer @ deepseek/deepseek-v4-pro. Verdict: **NEEDS REVISION**; **PREMISE: AGREE**.

**🔴 addressed (all three):**
1. *Ratchet compatibility asserted despite "do not assert compatibility."* → Reframed the ratchet
   bullet to **flag the tension and defer to design**; carried my mapping only as an explicit "working
   hypothesis," dropped the "no new close-out machinery" claim.
2. *Staleness lint underspecified — no discovery mechanism for "promise-surface files."* → Added an
   explicit open-for-design item: design SHALL specify the discovery mechanism (e.g. an in-ledger file
   manifest) or the detector is unimplementable.
3. *In-progress visibility not addressed.* → Added a "single-session ceremony, not multi-wave dossier"
   bullet stating product-audit's posture (composition-audit parity → **no** liveness obligation),
   flagged for design to justify the asymmetry explicitly.

**🟡 addressed:**
1. Tier not stated → added `<!-- Tier: COMPLEX ... -->` header with rationale + artifact expectation.
2. `scaffold_lint` token "optionally" → corrected to **required** with rationale.
3. Acknowledge ratchet tension → done as part of 🔴-1.

**💡 folded:** enumerated the four dispositions in the Capability section (💡-1); noted operator
dual-literacy as a design consideration (💡-2); named the detector `claims-ledger-staleness` per the
existing convention (💡-3).

→ Re-review required (mandatory after 🔴 fixes).

## proposal.md — Round 2 — 2026-07-14
Reviewer: openspec-reviewer @ deepseek/deepseek-v4-pro. Verdict: **PASS**; **PREMISE: AGREE**; zero 🔴;
D10 drift: none. All three Round 1 🔴 confirmed resolved at proposal altitude.

**Sole 🟡 (factual correction, applied):** the `_NON_OPENSPEC_SKILL_TOKENS` rationale was wrong.
Verified against `scripts/scaffold_lint.py:403-419` myself: `check_dangling_skill_refs` only *collects*
a non-openspec token when it is in the set, so omitting `product-audit` leaves it un-scanned (NOT
flagged) — no lint failure either way. Corrected the proposal to frame adding it as a **consistency
task** (validates the `correctness-audit/SKILL.md` cross-ref against the real dir; honors the set's
"keep in step" comment), not a failure-avoidance requirement. Reviewer and the earlier extraction
subagent disagreed on this; code is the tiebreak — proposal now matches code.

**FROZEN.** → proceeding to design.md + specs.

## design.md — Round 1 — 2026-07-14
Reviewer: openspec-reviewer @ deepseek/deepseek-v4-pro. Verdict: **PASS**; **PREMISE: AGREE**; zero 🔴.
All three proposal-flagged 🔴 resolutions judged sound (ratchet mapping total; content-sha256 manifest a
workable discovery mechanism; liveness asymmetry justified).

**Three 🟡 folded into design (no re-review — clarifications, not 🔴):**
1. `check:`/`test:` pointer target ambiguous → clarified: the pointer is the claim's **ledger
   proving-check cell** (a real resolvable test/detector), NOT the staleness lint (which is the ledger's
   meta-guard). Keeps the ratchet `enforcement-pointers-are-verified-live` requirement satisfiable.
2. Manifest completeness boundary implicit → stated explicitly: detector checks staleness of *listed*
   files only; coverage (a promise file dropped from the manifest) is out of scope by design.
3. "malformed manifest" undefined → parse contract added: a line not matching `- <path> —
   sha256:<64-hex>` is silently skipped, never flagged; vacuous/empty manifest → zero findings.

**💡 folded:** SKILL inlines the `sha256sum` reconciliation command (💡-1); test plan gains
vacuous-ledger edge cases (💡-2); glob+marker discovery scope stated explicitly (💡-3).

**FROZEN.** → proceeding to specs.

## specs (product-audit + knowledge-lint deltas) — Round 1 — 2026-07-14
Reviewer: openspec-reviewer @ deepseek/deepseek-v4-pro. Verdict: **PASS**; zero 🔴. `openspec validate
--strict` clean. Both deltas well-formed, SHALL-first-line, ≥1 scenario each; design→spec mapping
complete; no contradiction with existing knowledge-lint / finding-closure-ratchet specs.

**🟡 folded:** added the standard "SHALL be wired into `collect_findings()`" clause to the
`linter-detects-claims-ledger-staleness` requirement (convention parity with the five existing detector
requirements).
**💡 folded:** "charter walk" → "audit protocol" in product-audit Requirement 6 (product-audit has no
formal CHARTER.md — it's composition-audit altitude).

Re-validated `--strict` clean. **FROZEN.** → proceeding to tasks.md.

## tasks.md — Round 1 — 2026-07-14
Reviewer: openspec-reviewer @ deepseek/deepseek-v4-pro. Verdict: **PASS**; zero 🔴. Apply-split correctly
declared (Group 1 orchestrator-applied prose, Groups 2–4 flash); detector algorithm correct and mirrors
the guarded-detector idiom; task→design→spec mapping complete; no orphan/missing tasks.

**Wrapper note:** the wrapper reported `marker-missing` because the reviewer emitted the full `## Review
Round` block PLUS a trailing one-line summary, and `opencode_delegate.py` extracts only the LAST text
part (the summary). Full review recovered by extracting all JSONL text parts manually — verified PASS,
zero 🔴. (Relevant for the verify passes: extract-all when the wrapper reports marker-missing on a
multi-part reviewer response.)

**Two 🟡 + three 💡 folded (test-precision, no re-review — PASS/zero 🔴):**
- 🟡-1 added a wrong-delimiter guard-skip test sub-case; 🟡-2 added a conforming uppercase-hash sub-test
  (exercises case-insensitive comparison a bytewise `!=` would fail).
- 💡-1 noted blank-line skip in task 2.1; 💡-2 sharpened "empty manifest section" wording; 💡-3 rephrased
  task 4.2 for frozenset immutability.

**FROZEN.** `openspec validate --strict` clean; 4/4 artifacts complete. → auto-advancing to apply (autonomy grant).

## APPLY — 2026-07-14
Split apply per HANDOFF lesson #1. **Group 1 (SKILL.md):** orchestrator-applied by the primary (prose,
fence-heavy). **Groups 2–4 (Python/config):** deepseek-v4-flash apply-executor via `opencode run`,
`status=ok fallback=no`, all tasks `[x]`, **zero Sonnet fallback**. Diff: `knowledge_lint.py` (+detector,
registered), `test_knowledge_lint.py` (+9 tests), `scaffold_manifest.txt` (+1), `scaffold_lint.py`
(+token). `check.sh` green (ruff + full pytest); `knowledge_lint.py` live-tree clean (detector inert —
marker-guard confirmed).

## VERIFY — 2026-07-14
**Self-review (behavioral, non-delegable): READY.** Read all diffs + the authored SKILL.md; re-ran
`check.sh` (green); live-tree lint clean; behavioral probe confirmed drift/missing/match end-to-end and
that the `sha256sum` reconciliation workflow round-trips. **Adversarial/boundary fixtures authored by the
orchestrator** (diff carries decision logic — a manifest parser/state machine): (ADV-1) hyphenated
filename + em-dash delim → clean; (ADV-2) ASCII-hyphen delimiter + hyphenated path → clean (riskiest
regex-ambiguity case — the `sha256:` anchor forces correct delimiter selection); (ADV-3) manifest section
at EOF (no trailing `## `) → drift flagged (state-machine EOF flush works); (ADV-4) multi-entry mixed
(clean+drift+missing) → exactly 2 findings, correct line numbers. All passed.

**Lens selected: test-quality** (default) — the diff is a detector + its tests (decision-logic /
test-integrity risk); it is NOT a data-path change, so the data-scale lens does not apply.

**Conditional gates:** security review NOT triggered (read-only detector; no auth/credentials/persisted-
data/external-API surface — reports hash mismatches, never leaks content); data-path rule NOT triggered
(globs a handful of `knowledge/reference/*.md`, bounded manifest entries — no unbounded query/history
growth).

**Multi-model passes (COMPLEX: self → pro behavioral → flash lens):**
- **Self-review (Opus, behavioral):** READY (see above).
- **Lens pass — test-quality (deepseek/deepseek-v4-flash):** `VERDICT: READY`, zero defects. `status=ok`.
- **Behavioral pass (pro tier):** `deepseek/deepseek-v4-pro` emitted tool calls but ZERO text/verdict in
  BOTH the original concurrent run AND a focused re-run (operational output failure of that model tier
  this session; flash worked fine). Per the operational-crash → retry-once → Sonnet ladder, the pass was
  completed by a **Sonnet subagent** (disclosed): thorough independent behavioral review (green `check.sh`,
  live-tree clean, own drift/missing fixture, detect-only confirmed via the static write-guard test) →
  `VERDICT: READY`, zero defects. Mandatory Sonnet-fallback disclosure recorded in notes.md field 3.
- **Simplicity/quality gate (`/code-review --low`, xhigh recall):** no actionable findings — zero
  correctness bugs; zero over-engineering/duplication/dead-code. Two sub-threshold style/nil-impact
  observations noted (in-function regex compile; theoretical out-of-repo ledger path with nil impact —
  detect-only, trusted input), NOT folded per the gate's "does not block on style nits."
- **Structural spec-delta check (`checks.py --check spec-delta-structure`):** 0 findings.

**VERIFY VERDICT: READY FOR ARCHIVE.** → auto-advancing to archive (autonomy grant; no premise DISSENT,
no unresolved NEEDS-REVISION, no operator-named gate — downstream propagation + push remain deferred/gated).
