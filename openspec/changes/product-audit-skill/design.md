## Context

The scaffold owns six code-facing audit classes (correctness, test-quality, composition,
workflow-efficiency, knowledge-drift, per-repo security). None takes *copy* or *thesis* as its object,
so promise-surface and business-thesis defects are structurally invisible — proven by psc-monitor CG9,
where a launch-gate pricing defect survived three chartered code audits (evidence:
`knowledge/research/scaffold-gap-analysis-2026-07/psc-strategy-pressure-test-2026-07-12.md`). This
change adds the seventh class as a scaffold-owned skill, sibling to `correctness-audit`. The proposal
(frozen) fixes scope and flagged three questions for this design to settle: the ratchet-disposition fit
for non-code findings, the staleness-lint discovery mechanism, and the liveness asymmetry.

Two structural siblings bound the design space: `correctness-audit` (multi-wave, durable resumable
dossier, in-progress *liveness* obligation, heavy protocol) and `composition-audit` (single-session,
ephemeral output, machine verdict, light). `product-audit` is modeled on the **composition-audit
altitude** (single-session, verdict-to-disk) but is even lighter on tooling — its value is judgment, not
mechanical detection, so it ships **prose protocol + one guarded lint**, no `checks.py` sweep and no
anchor tag.

## Goals / Non-Goals

**Goals:**
- A pull-only, operator-invoked `product-audit` skill standardizing: blind attack-list → five-lane
  evidence fan-out → per-attack disposition diff → operator ratification menu → `PRODUCT:` verdict.
- A durable, cross-repo **claims-ledger** convention (promise → delivering surface → proving check)
  with a self-declaring covered-file manifest, and one **guarded** `knowledge_lint` staleness detector
  that keeps the ledger honest.
- Operationalize OW-15 classes 9–12 (copy↔capability conformance, entitlement reachability,
  severity-taxonomy completeness, source-class labeling) that `correctness-audit` explicitly hands off.

**Non-Goals:**
- No product code; no changes to the `finding-closure-ratchet` capability (its existing dispositions
  suffice — Decision 1); no in-progress liveness obligation or liveness lint (Decision 3).
- Not folded: OW-12 (archive mechanization), OW-11-residual (skill de-bloat), the OW-6
  revealed-vs-stated-priority lens (routed to composition-audit). No downstream propagation, no push
  (operator-gated).
- Not a recurring ceremony; never wired into boot/AGENTS.md/any auto-run.

## Decisions

### Decision 1 — Reuse the existing ratchet dispositions; NO carve-out (resolves proposal 🔴-1 / direction-gate 🟡-1)
The direction gate warned "do not assert compatibility." Having now walked each finding shape against
the five frozen ratchet dispositions (`check:`, `test:`, `waiver:review-by`, `open:since`,
`grandfathered`) and the sibling `close-out-gates-route-findings-into-the-ledger` requirement, the
mapping is total — **no new close-out machinery, no ratchet spec delta**:

| Product-audit finding shape | Disposition |
|---|---|
| Copy↔code claim closed with a real proving check that fails if the promise regresses (a behavioral test, or a detector) | `test:<path>::<name>` or `check:<pointer>` — **the pointer is the proving-check named in that claim's ledger row**, a real resolvable test/detector path |
| Copy↔code claim closed by fixing the copy with no enforcing check possible | `waiver:review-by <date>` + rationale (identical to `correctness-audit`'s doc-only-close rule) |
| Pure business-thesis decision (accepted pricing/regulatory/competitor risk) | `waiver:review-by <date>` — the re-review date is the strategy-reference watch-list expiry |
| `OPEN` attack (unresolved at close) | `open:since <date>` |
| `SURVIVED-BY-THESIS` attack (thesis held) | no ledger entry (first-class outcome, recorded in the disposition table — the analog of `REFUTED`) |

Ratchet Q3 ("mechanically detectable / test-freezable?") already has a "no → `waiver:review-by`" arm
(the doc-only close), so a non-detectable promise-surface finding maps cleanly, and the "yes" arm uses
`test:`/`check:` pointing at the claim's proving check. **The `check:`/`test:` pointer targets the
proving-check cell of the claim's ledger row — a real test or detector path that the ratchet's
`enforcement-pointers-are-verified-live` requirement resolves — NOT the claims-ledger staleness lint,
which is the ledger's own maintenance meta-guard (Decision 2), not a per-claim proving check.** Close-out
reuses the same orchestrator-performed three-question triage the sibling audits use.

**Alternative considered — a promise-surface leaf carve-out (new disposition keyword).** Rejected:
adds a sixth disposition the ratchet lint, the untriaged-age lint, and every downstream repo would have
to learn, to express something the `check:`/`waiver:` pair already expresses. The ratchet is
load-bearing across three repos; widening its vocabulary for one audit class is exactly the
over-engineering the scaffold's cite-don't-restate discipline avoids.

### Decision 2 — Claims-ledger format + self-declaring covered-file manifest with content hashes (resolves 🔴-2)
The ledger is a single per-repo markdown file, default `knowledge/reference/claims-ledger.md`, carrying
the literal marker `format: product-audit/v1`. It has two parts:

```
<!-- format: product-audit/v1 -->
last-reconciled: <YYYY-MM-DD>

## Covered promise-surface files
- <path> — sha256:<64-hex>
- landing/pricing.html — sha256:<64-hex>

## Claims
| Promise (as sold) | Delivering surface | Proving check | Disposition |
|---|---|---|---|
| <promise> | <code path/symbol> | <check: / test: pointer, or "manual @ <date>"> | CONFIRMED / PARTIAL / SURVIVED / OPEN |
```

The **`## Covered promise-surface files` manifest is the discovery mechanism** the reviewer's 🔴-2
required: the ledger itself declares which files constitute the covered promise surface, so the linter
never has to guess "what is a promise-surface file." Each entry records the **sha256 of that file's
content at last reconciliation**.

**Discovery scope (glob + marker, mirroring the existing detectors).** The detector globs
`knowledge/reference/*.md` and, for each file containing the literal `format: product-audit/v1` marker,
parses the manifest — the same glob-a-dir-then-gate-on-marker idiom `_check_audit_dossier` /
`_check_audit_liveness` use. The ledger's canonical home is `knowledge/reference/claims-ledger.md`; the
glob tolerates an alternate filename within `knowledge/reference/`. No marker anywhere → zero findings.

**Manifest-line parse contract (resolves 🟡-3).** A covered-file line matches
`- <path> — sha256:<64-hex>`. Any line under the manifest heading that does **not** parse to a path plus
a 64-hex sha256 (wrong delimiter, short/garbage hash, no sha256 field) is **silently skipped, never
flagged** — the detector is a staleness guard, not a manifest-format linter, and a lenient parse keeps
the live-tree gate and un-adopted repos clean. A validly-marked ledger with no `## Covered
promise-surface files` section, or an empty manifest section, yields **zero findings** (a vacuous ledger
is not a staleness defect).

**Staleness only, not completeness (resolves 🟡-2).** The detector checks staleness of *listed* files
only: a listed file whose content sha256 drifted, or a listed file now missing. Whether the covered-file
list still describes the *full* promise surface (a promise-surface file that exists on disk but was
never added to the manifest) is a **coverage** concern, not a staleness concern, and is deliberately
outside the detector's scope — coverage is the operator's judgment at audit time, which no deterministic
check can adjudicate.

**Why content-hash, not mtime or git.** Filesystem mtime is reset by every `git checkout`/clone — a
staleness check on mtime would false-positive on a fresh worktree. Shelling git into `knowledge_lint.py`
would add a git dependency and a no-git degradation path the other detectors don't have. A recorded
content sha256 is deterministic, stdlib-only (`hashlib`), git-independent, and detects exactly the
target signal: a covered promise-surface file whose content changed since the ledger was reconciled
(the ledger may no longer describe reality). Alternatives (mtime; git-log recency) rejected for the
fragility/complexity above.

**Reconciliation ergonomics (💡).** The SKILL SHALL inline the exact reconciliation procedure and the
literal command (`sha256sum <path>` → paste the hex into the row) so the operator who sees the lint
finding fire has the fix in front of them — the skill is the sole durable source of truth for how to
re-reconcile, and the finding message alone does not carry the procedure.

### Decision 3 — Single-session altitude → NO liveness obligation, NO liveness lint (resolves 🔴-3)
The `correctness-audit` liveness obligation exists because a *multi-wave, resumable, multi-session*
audit can silently fall off every tracker while genuinely in-progress. `product-audit` has no such
state: it runs in one bounded session (composition-audit parity) and either completes (leaving the
durable claims ledger + ratified decisions + ratchet lines) or is abandoned (leaving only ephemeral
scratch, nothing that misrepresents itself as complete). There is no in-progress durable dossier that
could rot on a tracker, so there is nothing for a liveness lint to watch. The durable artifact that
*does* persist — the claims ledger — is guarded by the **staleness** detector (Decision 2), a different
obligation from liveness. This asymmetry is deliberate and is stated in both the skill and the spec.

### Decision 4 — Prose protocol + one guarded lint; no deterministic sweep, no anchor tag
Unlike composition-audit (whose value is running jscpd/vulture/radon), product-audit has no
deterministic detector for "is this pricing claim true" — every lane is judgment (copy↔code reasoning,
live-web scans, thesis attack). So the skill is prose, the web lanes ride the existing research
convention (subagent-only, `scripts/fetch_clean.py`, never main-thread `WebSearch`), and the only
mechanized surface is the claims-ledger staleness lint. No `checks.py --include`, no `audit_scope.py`
anchor, no cadence signal — cadence is operator-driven (pre-launch gate + watch-list expiry).

### Decision 5 — Verdict, disposition set, and source-class labeling
- Machine-discriminable verdict written to disk: exactly one of `PRODUCT: CLEAN`,
  `PRODUCT: FINDINGS-ROUTED`, `PRODUCT: ESCALATE`. `ESCALATE` = recommend a chartered follow-up (a
  correctness-audit of a built-but-unsold feature, or a launch block) and SHALL NOT itself charter one
  (composition-audit ESCALATE parity).
- Per-attack disposition set: `CONFIRMED` / `PARTIAL` / `SURVIVED-BY-THESIS` / `OPEN`; survived attacks
  are recorded, never dropped.
- Durable web-sourced claims carry a **source class** at write time (`official` / `secondary` /
  `vendor-speculation`); the circular-sourcing signature is near-verbatim phrasing match to a
  promotional source. Re-verification burden points at the non-official classes first.
- Charter walk includes the **severity-taxonomy-completeness** prompt (a slot for
  external-promise/trust/legal harm, or a named exclusion — silence is the defect) and the
  **entitlement-state reachability** prompt (for every sold state, a user-reachable path to *enter* it).

### Decision 6 — Both blind-list and evidence-fan-out are load-bearing; operator ratification menu
The blind attack-list is committed before evidence (anchoring defense); the five-lane evidence fan-out
is where the highest-severity findings actually come from (n=3 method note). The skill states both are
required — a run that writes the blind list but skims the evidence pass is half a method. Findings are
surfaced as an **operator ratification menu** (decisions to ratify, not observations): the business
thesis is the operator's to own; the audit surfaces and routes, never auto-decides. A light
**dual-literacy** note records that the operator needs both business-thesis and code-surface literacy,
which the five-lane structure itself scaffolds (the implementation-as-sold lane forces code-reading;
the GTM/web lanes force thesis-reading). The skill also carries a **reciprocal awareness pointer** back
to `correctness-audit` (a built-but-unsold finding may warrant a correctness-audit of the undisclosed
feature), closing the bidirectional handoff correctness-audit opened.

## Risks / Trade-offs
- **[Content-hash manifest is manual to maintain]** → the ledger author records hashes at reconciliation
  (a `sha256sum <file>` per covered file). Mitigation: the skill inlines the exact command; the ledger
  is small at product scale (~10 rows); the staleness lint is precisely what flags a forgotten
  reconciliation, so the friction is self-correcting.
- **[Staleness lint fires on any content change, including trivial edits]** → a promise-surface file
  edit that doesn't touch a claim still trips the detector. Accepted: a conservative false-positive
  (re-reconcile the ledger, cheap) is the correct bias for a promise-surface drift guard; the
  alternative (semantic diff) is not deterministic. The finding message names the drifted file so the
  operator can re-hash in seconds.
- **[No liveness lint means an abandoned mid-audit leaves no tracker trace]** → accepted by Decision 3:
  an abandoned single-session audit leaves only ephemeral scratch, not a durable artifact that
  misrepresents completeness, so there is nothing to track. (A repo that wants standing visibility of
  "product-audit is due" uses the pre-launch-gate cadence guidance, not a lint.)
- **[Cross-repo blast radius]** → the SKILL is scaffold-managed and propagates byte-identical; the spec
  is golden-source-only. Both lint behaviors are marker-guarded, so first downstream sync adds no lint
  failures. Propagation is operator-gated and deferred.

## Migration Plan
Additive greenfield — no migration. Rollback = revert the change commit(s); the guarded detector is
inert wherever no `product-audit/v1` ledger exists, so no downstream repo is disturbed until it
adopts the convention.

## Open Questions
None blocking. All three proposal-flagged questions are resolved above (Decisions 1–3). Residual
non-blocking follow-ons (e.g. an optional `sha256`-recompute helper to reduce ledger-maintenance
friction) are recorded at archive, not built here.

## Verification (change-specific acceptance criteria)
1. **Skill.** `.claude/skills/product-audit/SKILL.md` exists with the convention frontmatter
   (`name/description/license/compatibility/metadata`), the pull-only never-auto-run stance, the full
   protocol (blind attack-list → five-lane fan-out → disposition diff → ratification menu → `PRODUCT:`
   verdict), the claims-ledger template (with `format: product-audit/v1` + covered-file sha256
   manifest), the Decision-1 disposition→ratchet mapping, source-class labeling, the severity-taxonomy
   and reachability prompts, the reciprocal awareness pointer, and the dual-literacy note.
2. **Spec.** `openspec/specs/product-audit/spec.md` exists; `openspec validate product-audit-skill
   --strict` exits 0; every requirement's SHALL/MUST is on its first physical line; each requirement
   carries ≥1 WHEN/THEN scenario.
3. **Detector.** `scripts/knowledge_lint.py` gains `_check_claims_ledger_staleness`, registered in
   `collect_findings`, marker-guarded on `format: product-audit/v1`. It flags (a) a covered file whose
   current sha256 ≠ the recorded hash, and (b) a listed covered file that is missing; it emits zero
   findings when no marker/ledger is present.
4. **Detector tests.** `scripts/test_knowledge_lint.py` gains the triad: conforming ledger (hashes
   match) → clean; drifted ledger (a covered file's content changed) → flagged with the file named;
   missing covered file → flagged; and guard-skip cases → zero findings: no marker; no ledger file;
   malformed manifest line (wrong delimiter / short-or-garbage hash / no sha256 field); marked ledger
   with **no** `## Covered promise-surface files` section; and marked ledger with an **empty** manifest
   section (vacuous-but-valid).
5. **Live-tree gate.** `scripts/test_doc_lint_gate.py` stays green — this repo ships no
   `product-audit/v1` ledger, so the detector is inert on the live tree.
6. **Registration.** `scripts/scaffold_manifest.txt` includes `.claude/skills/product-audit/SKILL.md`;
   `_NON_OPENSPEC_SKILL_TOKENS` includes `product-audit`; `python3 scripts/scaffold_lint.py` passes.
7. **Green gate.** `scripts/check.sh` is green (ruff format+lint, full pytest, all scaffold/knowledge
   lints).
