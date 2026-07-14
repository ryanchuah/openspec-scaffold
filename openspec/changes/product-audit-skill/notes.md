# Notes — product-audit-skill

**Tier:** COMPLEX (greenfield capability + new scaffold-managed skill + a new durable cross-repo
convention + a guarded lint). Autonomy grant active this session.

**Change-specific acceptance criteria:** design.md `## Verification` (7 items). Verify results go here.

## Assumptions (recorded defaults — non-blocking, batch-surface at next operator gate)
- **A1 — Claims-ledger home.** Canonical path `knowledge/reference/claims-ledger.md`; the staleness
  detector globs `knowledge/reference/*.md` and gates on the `format: product-audit/v1` marker (tolerates
  an alternate filename within `knowledge/reference/`). Chosen because `knowledge/reference/` is the
  scaffold's per-repo reference home and the marker-gate is the real guard.
- **A2 — Ship the lint now.** Resolved the direction-gate 🟡-2 tension toward shipping the guarded
  staleness detector this change (mechanism-over-docs) rather than deferring; the marker-guard keeps this
  repo + un-adopted downstream repos clean.
- **A3 — No ratchet spec change.** The five existing finding-closure-ratchet dispositions cover all
  product-audit finding shapes (design Decision 1); no `finding-closure-ratchet` delta.
- **A4 — Content-hash on raw bytes.** The detector hashes `path.read_bytes()` (matches `sha256sum`
  output), git-independent, robust to checkout mtime resets (design Decision 2).
- **A5 — Manifest parse is delimiter-tolerant.** Canonical row is `- <path> — sha256:<64-hex>` but the
  parser matches `[—–-]+` so em-dash/hyphen both work; unparseable lines are silently skipped.

## Apply plan (mixed prose + code → split; HANDOFF lesson #1)
- **Group 1 (SKILL.md prose): orchestrator-applied by the primary** — fence-heavy, downstream-propagated;
  checked off BEFORE delegating flash, so the executor resumes at the first `[ ]`.
- **Groups 2–4 (Python/config): flash apply-executor** via `opencode run` (Sonnet fallback per ladder).

## VERIFY outcome — 2026-07-14 — READY FOR ARCHIVE
1. **Verdict:** READY for archive. All gates green.
2. **Confirmed by eyeballing live output:** ran the real detector (`knowledge_lint.py --root <fixture>`)
   on scratch fixtures — a marked ledger with a matching sha256 is silent; drifting the covered file's
   content produces exactly the "stale: <file> content changed" finding on the right line; a manifest row
   for a non-existent file produces the "missing promise-surface file" finding; and the live repo tree
   lints clean (detector correctly inert — no `product-audit/v1` ledger exists). The operator's inlined
   `sha256sum` reconciliation workflow round-trips through the detector. Adversarial boundary fixtures
   (hyphenated filename, ASCII-hyphen delimiter, manifest-at-EOF flush, multi-entry mixed) all behaved
   correctly.
3. **Defects found & fixed:** none in the implementation (self-review, test-quality lens, and the
   behavioral pass all found zero defects; the simplicity gate found no over-engineering/duplication/
   dead-code). **Process note:** the `deepseek/deepseek-v4-pro` behavioral verifier emitted tool calls
   but ZERO text/verdict in BOTH attempts (original + focused re-run) — an operational output failure of
   that model tier this session (the deepseek-flash lens pass worked fine). Per the verify ladder, the
   behavioral pass was completed by a **Sonnet subagent fallback**, which returned VERDICT: READY with a
   thorough independent review (green suite, live-tree clean, its own drift/missing fixture, detect-only
   confirmed via the module's static write-guard test). No product defect was involved.
4. **As-built deltas vs artifacts:** none. Implementation matches the frozen spec/design exactly
   (detector at `scripts/knowledge_lint.py` `_check_claims_ledger_staleness`; registered once in
   `collect_findings`; 9 tests; SKILL.md per design Verification item 1).
5. **Forward-looking items (fold into knowledge/questions at archive — recorded NOWHERE else):**
   - **product-audit-follow-ons** (create `knowledge/questions/product-audit-skill-follow-ons.md`):
     (a) optional `sha256`-recompute helper script to reduce claims-ledger maintenance friction (design
     Open Questions; non-blocking); (b) claims-ledger location is fixed to the `knowledge/reference/*.md`
     glob — a repo needing an alternate home is a future extension (assumption A1); (c) the staleness lint
     fires on ANY content change of a covered file, incl. trivial edits (design Risk — conservative
     false-positive bias, by design; monitored); (d) manifest *completeness* (a promise-surface file on
     disk but absent from the manifest) is deliberately un-linted — coverage is operator judgment (design
     Decision 2); revisit only if drift is observed downstream.
   - **Infra/process monitored risk (NOT a product item):** `deepseek/deepseek-v4-pro` verifier emitted
     no text in 2 runs this session → behavioral pass fell back to Sonnet. If the pro verifier tier keeps
     failing to emit verdicts across sessions, the verify multi-model chain (and the pro premise/proposal
     reviews, which DID work here) needs investigation. Belongs in the HANDOFF + possibly a
     verify-adversarial-fixtures / delegation follow-on.

**Still owned by archive (reconcile at archive, do NOT edit here):** `knowledge/STATUS.md` (add
product-audit-skill / OW-16 SHIPPED section, respect the ≤3-section cap); `knowledge/decisions/INDEX.md`
(registry line for `product-audit-skill`); `knowledge/questions/INDEX.md` (park the product-audit
follow-ons pointer above); promote both delta specs into `openspec/specs/` (`product-audit` new +
`knowledge-lint` ADDED requirement); reconcile the backlog (`OUTSTANDING-WORK.md` OW-16 → SHIPPED;
`knowledge/roadmap.md` "Product-audit skill" → shipped); refresh `HANDOFF.md`; append the pending
downstream-propagation entry.

## Downstream propagation — DEFERRED + operator-gated
Scaffold-managed surfaces touched: `.claude/skills/product-audit/SKILL.md` (new),
`scripts/knowledge_lint.py` + `scripts/test_knowledge_lint.py` (+1 guarded detector),
`scripts/scaffold_manifest.txt`, `scripts/scaffold_lint.py`. Spec is golden-source-only (not synced).
Both new lint behaviors are marker-guarded → no new downstream lint failures on first sync. NOT synced
to extrends/psc-monitor without fresh operator authorization. Running ledger:
`knowledge/reference/pending-downstream-propagation.md`.
