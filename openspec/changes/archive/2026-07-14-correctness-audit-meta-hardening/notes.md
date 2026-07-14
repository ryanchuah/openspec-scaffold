# Notes — correctness-audit-meta-hardening (OW-15)

MEDIUM change. Amends the shipped `correctness-audit` capability (OW-5) with four downstream-evidence-driven
deltas, plus two guarded `knowledge_lint` detectors. Source backlog:
`knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md` (OW-15); evidence:
`psc-coverage-gap-review-2026-07-11.md`, `extrends-coverage-gap-review-2026-07-12.md`,
`psc-strategy-pressure-test-2026-07-12.md`.

## Blocker cleared before proposing
OW-15 was marked "BLOCKED on unshipped OW-5" in the prior HANDOFF and STATUS, but OW-5
(`correctness-audit`) **shipped 2026-07-13** (`openspec/changes/archive/2026-07-13-correctness-audit-skill/`;
capability spec + skill both live; OW-6 which depends on it also shipped). The stale block traced to the
`OUTSTANDING-WORK.md` OW-5 STATUS line still reading "PAUSED AT APPLY". OW-15 is therefore unblocked. The
archive reconciliation must fix that stale line and the STATUS/HANDOFF claim.

## Acceptance criteria
1. **Delta 1 (liveness):** the `correctness-audit` spec requires an in-progress dossier to be surfaced as an
   Active `knowledge/questions/INDEX.md` item until close-out, with a charter `status:` marker
   (`in-progress`→`closed`) and discovery/remediation wave-namespace separation. `knowledge_lint` flags a
   marked, non-`closed` dossier that no Active item references (`audit-liveness` check).
2. **Delta 2 (coverage-gap review):** close-out includes a blind-taxonomy → diff-against-coverage review with
   the four markers (`✅`/`🟡`/`📋`/`⬜`) and the "both halves load-bearing" note. Skill step present; spec
   requirement present.
3. **Delta 3 (scope-seeding checklist):** the skill carries a bounded inlined checklist (11-group dimension
   seed + 12 named blind-spot classes + widenings), consulted at charter instantiation. Classes 9–12 are
   awareness pointers only — no claims-ledger mechanism is built (that is OW-16).
4. **Delta 4 (post-close ledger):** close-out seeds a `POST-CLOSE-LEDGER.md`; the spec requires post-close
   persistence/publish changes to append a 5-field line; `knowledge_lint` validates line format when the
   ledger is present (`post-close-ledger-format` check).
5. **Guarded / live-tree clean:** both new detectors follow the guarded-existence idiom — this repo (no live
   dossier) and every un-adopted downstream repo lint clean. `scripts/test_doc_lint_gate.py` stays green.
6. **Detect-only preserved:** `test_module_source_has_no_write_calls` stays green; the linter still never writes.
7. `bash scripts/check.sh` green (ruff + full pytest).

## Scope decisions (reviewer: sanity-check these two)
- **OW-16 boundary held.** Classes 9–12 (copy↔capability, reachability, severity-completeness, source-class
  labeling) enter the skill only as awareness prompts. The claims-ledger convention + its optional staleness
  lint, and the promise-surface/business-thesis audit protocol, are **OW-16** ("The promise-surface/thesis
  audit protocol itself is OW-16, not an OW-15 delta" — evidence, verbatim). Not built here.
- **Delta 4 lint scoped to well-formedness only.** The evidence's "ledger exists after close-out" half needs
  git-diff-since-close analysis that is out of scope for a deterministic knowledge_lint check; the lint
  implements only "entries well-formed, guarded on presence." The "should-exist-after-close-out" obligation is
  a protocol SHALL (skill + spec), enforced by the coverage-gap review + operator, not by the lint. This keeps
  the check non-fuzzy and false-positive-free. **If the reviewer judges the Delta-4 lint marginal, it can be
  deferred to a follow-on without touching Deltas 1–3** — Delta 4's protocol prose (skill + spec) is the
  load-bearing half and stands alone.

## Assumptions (recorded defaults — non-blocking)
- **Canonical ledger filename = `POST-CLOSE-LEDGER.md`** (generic; extrends' reference impl used
  `POST-WAVE4-LEDGER.md`, which is final-wave-number-specific and not portable). The lint globs the canonical name.
- **Ledger fields pipe-separated**, matching the dossier CENSUS.md pipe convention: `commit | subsystem |
  wave-owner | spec? | review-tier` (evidence field order verbatim).
- **In-progress signal = charter lacks `status: closed`** (robust, marker-idiom-consistent) rather than parsing
  the wave-plan table statuses (fragile). Adds a `status:` line to the charter template.
- **Liveness reference target = dossier directory basename** appearing in the INDEX `## Active` section
  (substring match), consistent with how the Active section cites on-demand items.

## Apply split (disclosed)
- **Delegated to deepseek-flash apply-executor:** tasks.md sections 1–3 (the two `knowledge_lint` detectors +
  their tests). Deterministic implementation code — must be delegated.
- **Orchestrator-applied directly:** tasks.md section 4 (the `.claude/skills/correctness-audit/SKILL.md` prose,
  verbatim from `skill-additions.md`). Load-bearing, downstream-propagated protocol prose with nested code
  fences; per AGENTS.md ("quick doc edits done by the primary") and the carried HANDOFF lesson, more reliable
  applied directly than relayed through the executor. Keeps "no implementation code by the primary" intact —
  the primary writes prose only; flash writes the Python.

## Verify outcome (2026-07-14)

1. **Verdict: READY for archive.** Self-review PASS; pro behavioral verifier (`deepseek/deepseek-v4-pro`)
   READY with zero defects (real verifier ran — re-ran the suite, examined both new functions and
   `collect_findings`); simplicity gate PASS (no duplication beyond the established per-check re-glob idiom,
   no single-use over-abstraction, no dead code, no over-parameterization); security + data-path gates N/A
   (no auth/creds/persisted-data/external-API/network surface, no data path). `bash scripts/check.sh` green.
2. **Live output eyeballed.** Constructed real correctness-audit dossier fixtures and ran the two detectors
   against them via an orchestrator-authored adversarial boundary probe (9 boundary assertions beyond the
   executor's tier tests, all pass): multi-dossier mixed closed/in-progress → only the in-progress one flagged;
   two in-progress both missing → both flagged; marked-but-no-`status:`-line legacy dossier → treated
   in-progress → flagged; in-Active → clean; ledger 6-cell line → clean (documented tolerance); ledger empty
   middle cell → flagged; ledger mixed file (5-cell header clean, separator/comment skipped, 3-cell line
   flagged) → exactly one malformed; ledger in unmarked dossier → skipped. Both detectors lint clean on this
   repo's real tree (live-tree gate green). The `## Active` extraction correctly distinguishes Active from
   Parked (a Parked-only reference is flagged).
3. **Defects found: none.** No fix re-delegation needed; zero Sonnet fallback anywhere in the lifecycle
   (premise pro-review, flash apply, pro verifier all ran clean first-try).
4. **As-built deltas.** (a) Close-out steps were cleanly renumbered 1–10 in SKILL.md (coverage-gap review = 6,
   post-close ledger = 9, liveness-close = 10) rather than the duplicate-numbered inserts sketched in
   `skill-additions.md` — behavior identical, cleaner. (b) The canonical post-close ledger filename is
   `POST-CLOSE-LEDGER.md` (portable; the extrends reference impl's `POST-WAVE4-LEDGER.md` was final-wave-specific).

5. **Forward-looking items for the project docs (fold into `knowledge/questions/INDEX.md` at archive):**
   - **Liveness substring-match false-negative (monitored, low priority).** `_check_audit_liveness` uses
     substring membership: a dossier `correctness-audit-2026-07` is considered "referenced" if the Active
     section contains any longer token embedding it (e.g. `correctness-audit-2026-07-appendix`, or a reference
     to that audit's own `-triage.md`). Benign under the unique `YYYY-MM` naming and because a same-audit
     triage reference legitimately surfaces the audit; a word-boundary match is the follow-on if it ever bites.
   - **Delta-4 ledger lint is well-formedness-only (deferred scope).** It validates line format when a
     `POST-CLOSE-LEDGER.md` is present; it does NOT enforce "a ledger must exist after close-out" (that needs
     git-diff-since-close analysis, out of scope for a deterministic knowledge_lint check). The
     should-exist obligation rests on the coverage-gap review + operator (protocol SHALL). Candidate follow-on
     if the "audit closed but no ledger seeded" gap is observed downstream.
   - **Ledger "at least five" vs "exactly five" cell tolerance** — chose the false-positive-safe "at least
     five, each non-empty" posture (rationale pinned in tasks.md §2.1 + review-log). Monitored; revisit only
     with the trade-off in hand.
   - **OW-16 remains the natural next change** — the `product-audit` skill (promise-surface/business-thesis),
     the claims-ledger convention, and the operationalization of classes 9–12 (carried here only as awareness
     pointers). Chain-independent; slots anywhere. Already tracked in OUTSTANDING-WORK OW-16.
   - **Stale-tracker fix owed** — OW-5 shipped 2026-07-13 but OUTSTANDING-WORK.md's OW-5 STATUS line, STATUS.md,
     and the prior HANDOFF still implied OW-15 was blocked on it. Archive must correct OW-5's STATUS line to
     SHIPPED and mark OW-15 SHIPPED.

## Still owned by archive
- `knowledge/STATUS.md` — add the OW-15 shipped section (respect ≤3 cap; drop oldest); update Immediate-next-action
  (remaining: OW-12 lowest-priority; OW-16 greenfield; OW-11 residual de-bloat).
- `knowledge/decisions/INDEX.md` — add the `correctness-audit-meta-hardening` registry line.
- `knowledge/questions/INDEX.md` — add the field-5 follow-ons above to Parked (new `correctness-audit-meta-hardening-follow-ons.md`).
- `OUTSTANDING-WORK.md` — mark OW-15 SHIPPED; fix the stale OW-5 STATUS line to SHIPPED.
- `knowledge/reference/pending-downstream-propagation.md` — log this change's scaffold-managed edits (operator-gated sync).
- `knowledge/roadmap.md` — refresh the wave-status line if it names OW-15.
- Spec promotion: sync `specs/correctness-audit/` + `specs/knowledge-lint/` deltas into `openspec/specs/` (ADDED requirements).
- Write a fresh `knowledge/HANDOFF.md`; delete the current one once absorbed.

## Downstream propagation
Edits scaffold-managed surfaces (`scripts/knowledge_lint.py`, `scripts/test_knowledge_lint.py`,
`.claude/skills/correctness-audit/SKILL.md`, and the `correctness-audit` + `knowledge-lint` specs). Propagation
to extrends/psc-monitor is operator-gated and deferred; log to
`knowledge/reference/pending-downstream-propagation.md` at archive.

**Guard keeps the two new checks silent downstream:** both are gated on the `format: correctness-audit/v1`
marker. Both downstream repos' existing `correctness-audit-2026-07` dossiers are **markerless** (they pre-date
OW-5's format — recorded in the `audit-dossier-lint-marker-gated` decision), so the liveness and ledger checks
skip them on first sync. **Migration note for the propagate-scaffold operator:** if a downstream repo later
adopts the `format:` marker on a dossier that is genuinely still in-progress, it must add a `status:` line to
that charter (`in-progress` or `closed`) and, if in-progress, an Active `knowledge/questions/INDEX.md` item — a
one-time reconciliation the liveness check will otherwise (correctly) flag. This is the intended behavior, not
a regression.
