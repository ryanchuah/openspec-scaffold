# Apply reference — verbatim SKILL.md insertion blocks (correctness-audit-meta-hardening)

This file holds the **exact** text the apply-executor inserts into
`.claude/skills/correctness-audit/SKILL.md`. Each block gives an ANCHOR (existing text to
locate) and the EDIT (replace / insert-after). Insert verbatim — do not paraphrase or
re-flow. These are authored by the orchestrator; the executor's job is mechanical placement.

---

## EDIT 1 — Charter status line (Delta 1)

**ANCHOR** (in the `### CHARTER.md skeleton` fenced block, the closing marker lines):
```
---
format: correctness-audit/v1
```

**REPLACE WITH:**
```
---
format: correctness-audit/v1
status: in-progress
```

(At close-out the `status:` line is changed to `status: closed` — see EDIT 6.)

---

## EDIT 2 — Charter wave-plan namespace note (Delta 1)

**ANCHOR** (in the `### CHARTER.md skeleton` fenced block, immediately after the wave-plan table,
i.e. after the `| 3 | <slice> | WAVE-3: planned | CA-W3-* |` row and its trailing blank line, before
`## Verification-method map`):

**INSERT** this line right after the wave-plan table (inside the fenced skeleton):
```
Discovery waves use the `WAVE-N` namespace. A remediation program that follows the
audit MUST use a distinct namespace (e.g. `REMEDIATION-N`) — never a second run of the
`WAVE-N` labels — so the discovery tail cannot be silently overwritten and dropped.
```

---

## EDIT 3 — Wave 0 seeds the liveness Active item (Delta 1)

**ANCHOR** (in `### Wave 0 — instrument verification`, the triage-file bullet):
```
- Populate `knowledge/research/correctness-audit-<YYYY-MM>/` with empty/template files for census and findings. Create the triage file at `knowledge/questions/correctness-audit-<YYYY-MM>-triage.md` (empty, to be appended at every wave gate — D11).
```

**INSERT-AFTER** (new bullet directly below it):
```
- **Seed audit liveness (D-liveness).** Set the charter's `status:` line to `in-progress` and add an Active item to `knowledge/questions/INDEX.md` referencing the dossier directory (e.g. `correctness-audit-<YYYY-MM>` — audit in progress, waves N..M outstanding). This item stays Active until close-out. A deterministic `knowledge_lint` check flags a marked, non-`closed` dossier that no Active item references, so the unfinished audit cannot fall off every tracker (the psc silent-wave-drop failure mode).
```

---

## EDIT 4 — Close-out: coverage-gap review step (Delta 2)

**ANCHOR** (in `### Close-out`, the numbered list — insert a new step between step 5 and step 6,
renumbering is NOT required if inserted as step "5b"; place it immediately before
`6. **Produce a ranked remediation queue**`):

**INSERT-BEFORE** step 6:
```
6. **Run the blind coverage-gap review.** Before producing the remediation queue, run a coverage-gap review that checks the audit's *scope* (the census only proves completeness *within* scope):
   - **Write the full-audit dimension taxonomy BLIND** — before re-reading this charter or dossier. Reading them first anchors the reviewer to the charter's own blind spots. Seed the blind list from the **Scope-seeding checklist** appendix below.
   - **Diff the blind taxonomy against chartered-and-executed coverage**, classifying each dimension as exactly one of: `✅ covered` / `🟡 partial` / `📋 planned-never-run` / `⬜ never-planned`. Every `📋` and `⬜` is a scope gap the census could not have detected.
   - **Both halves are load-bearing.** The blind taxonomy defends against inherited blind spots; an **evidence fan-out** over the real implementation (not just the lead list) finds gaps armchair reasoning cannot predict. Observed across three runs: the highest-severity gaps came from the evidence fan-out, not the blind list — a review that writes the taxonomy but skims the evidence pass is half a method.
   - Record the classified dimension table and any new leads in the dossier. New `⬜`/`📋` gaps either open leads (mini-wave) or are dispositioned by the operator at the close-out gate.
   - This review MAY also be run on demand for a stalled audit, not only at close-out.
```

(The subsequent "Produce a ranked remediation queue" / "Remediation ships as ordinary OpenSpec
changes" bullets keep their existing numbers; a duplicated step number is acceptable — the list is
prose, not parsed.)

---

## EDIT 5 — Close-out: seed the post-close ledger (Delta 4)

**ANCHOR** (in `### Close-out`, immediately after the (new) coverage-gap review step from EDIT 4):

**INSERT-AFTER** the EDIT-4 block:
```
7. **Seed the post-close coverage-liveness ledger (D-postclose).** Every wave audits a point-in-time snapshot; code shipped after close-out is unaudited by construction and wave-level scrutiny never re-fires. Seed `POST-CLOSE-LEDGER.md` in the dossier directory (template below). Thereafter, any change whose diff touches a **persistence path, a publish path, or writes evaluation ground truth** appends one ledger line at verify/archive time: `<commit> | <subsystem> | <wave-owner> | <spec?> | <review-tier>`. When the ledger's open set accumulates several persistence-touching entries, **cut a mini-wave from the ledger** rather than trusting per-change verify passes alone. A deterministic `knowledge_lint` check validates the ledger's line format when it is present. This ledger is the mirror image of the D-liveness Active item: one defends the unfinished dossier, the other the finished one.
```

---

## EDIT 6 — Close-out: flip status to closed (Delta 1)

**ANCHOR** (in `### Close-out`, the existing final step 7 — "Remediation ships as ordinary OpenSpec
changes citing finding IDs — never inside the audit (D11)."):

**INSERT-AFTER** that final step:
```
8. **Close the audit's liveness.** Set the charter's `status:` line to `closed` and remove (or mark resolved) the Active `knowledge/questions/INDEX.md` item that referenced this dossier. Once `status: closed`, the liveness lint no longer requires an Active item for this dossier.
```

---

## EDIT 7 — Scope-seeding checklist appendix (Delta 3)

**ANCHOR** (append as a new `##`-level section immediately BEFORE the final `## Guardrails` section):

**INSERT** this entire section:
```
## Scope-seeding checklist (consulted at charter instantiation)

Consult this generic, protocol-level checklist when drawing a charter's scope boundary (the
"invocation with no dossier" walk). It is a **bounded coverage-awareness reference, not an
execution handbook** — it prompts the scope decision; it does not replace the per-repo judgment
(severity taxonomy, wave decomposition, verification-method map). A dimension deliberately ruled
out of scope is **recorded as excluded in the charter**, never silently omitted.

### Dimension seed (11 groups)

- **A. Specification:** spec↔intent (specs can be consistent and wrong) · spec↔impl conformance · spec↔test traceability with rot protection · delta-spec sync integrity (specs ≡ sum of applied deltas).
- **B. Data model & data-at-rest:** constraint-completeness census (invariant → schema / app code / nowhere) · core-structure invariants on the REAL store · cross-store orphan census · migration-chain ≡ fresh-schema equivalence · per-column NULL-semantics ledger · unicode/collation/type fidelity.
- **C. Domain semantics:** upstream-contract conformance + format-evolution canary · event/diff taxonomy completeness vs product promise · matching/resolution soundness vs ground truth · output-surface semantics (as-of; does the report answer what the reader thinks) · time/clock semantics (host vs DB clock, boundaries, timezones).
- **D. State machines, concurrency, idempotency:** lifecycle transition tables with no undefined holes · idempotency of every mutating job (re-run after crash at ANY point; run-indexed vs period-indexed derived state under sequential same-period re-runs) · overlap/TOCTOU guards · transaction-boundary walk.
- **E. Failure modes & recovery:** silent-failure census (warn-and-continue, empty-looks-like-success, swallowed exceptions) · crash-recovery per pipeline stage · partial-input handling · backup completeness of non-reconstructible state + tested restore.
- **F. Interface contracts:** API response-shape/error/pagination consistency · frontend correctness (edge values, empty states, validation parity) · outbound-content correctness (what the user sees vs what the system meant) · third-party contract fidelity incl. feedback channels (bounces, replays, reconciliation).
- **G. Money & entitlement:** entitlement matrix (account state × feature × surface, every cell enforced AND reachable) · external-truth reconciliation (missed-event drift repair) · quota/limit arithmetic (boundaries, off-by-one, concurrent consumption).
- **H. Test-suite quality:** mutation resistance / assertion strength · coverage dark spots (and coverage tooling actually running) · fixture realism (scale AND shape) · mock-fidelity ledger (which mocks were ever validated live) · order/isolation robustness · measurement-pipeline parity (does eval grade the identical artifact path prod publishes, or a re-derivation?).
- **I. Operational correctness:** cron/schedule audit vs intent (committed-template vs live drift) · config/env census (silent behavior changes on absent/malformed values; pydantic-settings `extra="ignore"` + no `env_prefix` makes typo'd/prefixed env vars silent no-ops) · deploy-day integrated dry-run · observability sufficiency (failure class → which signal fires; "quiet because healthy" vs "quiet because dead"). Grade hazard-liveness against the **deployed configuration** (.env / activation records), noting the code default separately — not the code default alone.
- **J. Compliance-mechanism correctness (non-security):** suppression/redaction completeness across ALL output surfaces · retention/erasure enforcement mechanisms exist and run · subject-access export completeness.
- **K. Meta/process:** audit-blind-spot review (this very step) · fix-regression protection (every remediation carries a reintroduction-catching test) · knowledge/doc drift vs reality.

### Named recurring blind-spot classes

1. **Backup completeness of NON-reconstructible state** — enumerate stores reconstructible-vs-not; every non-reconstructible store needs an *implemented* (not documented-as-planned) backup; restore drills must exercise the non-reconstructible tier.
2. **Cutover/deploy-day as ONE sequence** — each step verified ≠ the sequence verified; interactions between migrations, sweeps, first-load, and cron installation live between the checklist rows.
3. **Provider feedback channels, not just request paths** — bounce/complaint handling, webhook-miss reconciliation (is external truth ever re-synced, or event-delivery-only?).
4. **Policy-without-mechanism** — retention/erasure policies whose enforcement code doesn't exist; compliance docs presupposing absent infrastructure.
5. **Phantom tooling / phantom capability** — declared ≠ invoked. Verify invocation sites, not declarations — for dev tooling AND for product capability claims (declared extras/backends/features with zero exercised path).
6. **Partial-✅ dispositions** — a "satisfied/complete" claim covering only a subset. A ✅ must name what it excludes. Any tracker claim authorizing a state-mutating operator action ("safe to re-run X; worst case Y") must carry a **VERIFIED-BY** tag or an explicit **UNVERIFIED** marker.
7. **Point-in-time audits with no durable convention** — a property audited once then left to rot needs a convention or an explicit re-audit cadence (see the post-close ledger, D-postclose).
8. **At-rest invariant census at production scale** — the core structure's invariants checked against the real accumulated store, not fixture-scale tests.

**Awareness pointers — full mechanism belongs to the sibling `product-audit` (promise-surface / business-thesis) skill, NOT this protocol.** Carry these as scope prompts only; do not operationalize a claims-ledger here:
9. **Copy↔capability conformance** — externally visible promises (pricing, marketing copy, README claims, public docs) vs the delivering code surface. Both directions observed: sold-but-unbuilt AND built-but-unsold.
10. **Entitlement-state reachability** — for every sold/entitled state, a user-reachable path to *enter* it must exist. A dead-but-correct differentiator passes every behavior audit; only reachability catches it.
11. **Severity-taxonomy completeness** — does the severity scale have a slot for external-promise/trust/legal harm, or is that class explicitly ruled out to a named sibling audit? Silence is the defect.
12. **Source-class labeling for durable web-sourced claims** — tag at write time as official / secondary / vendor-speculation; re-verification points at non-official classes first. Circular-sourcing signature: near-verbatim phrasing match to a promotional source.
```

---

## EDIT 8 — Guardrails: sanction the new writes (Deltas 1, 4)

**ANCHOR** (the first `## Guardrails` bullet):
```
- The correctness-audit skill may write to **the dossier dir** (`knowledge/research/correctness-audit-<YYYY-MM>/`), **the triage questions file** (`knowledge/questions/correctness-audit-<YYYY-MM>-triage.md`), and **`knowledge/ratchet-log.md`** at close-out, and — only under the fix-now criterion (D9) — **audit-instrument code**.
```

**REPLACE WITH:**
```
- The correctness-audit skill may write to **the dossier dir** (`knowledge/research/correctness-audit-<YYYY-MM>/`, including `POST-CLOSE-LEDGER.md` and the charter's `status:` line), **the triage questions file** (`knowledge/questions/correctness-audit-<YYYY-MM>-triage.md`), the **Active liveness item** in `knowledge/questions/INDEX.md` (added at Wave 0, removed at close-out), and **`knowledge/ratchet-log.md`** at close-out, and — only under the fix-now criterion (D9) — **audit-instrument code**.
```

---

## EDIT 9 — POST-CLOSE-LEDGER.md template (Delta 4)

**ANCHOR** (append as a new `### POST-CLOSE-LEDGER.md format` subsection at the END of the
`## Inlined templates` section — i.e. immediately after the `### Known-findings-ledger template`
block's closing fence and before `## Guardrails`; place it before the EDIT-7 checklist section if
EDIT 7 is inserted first, ordering between EDIT-7 and EDIT-9 sections does not matter):

**INSERT** this subsection:
```
### POST-CLOSE-LEDGER.md format

Seeded in the dossier dir at close-out (D-postclose). One line per post-close change whose diff
touches a persistence path, a publish path, or writes evaluation ground truth. Pipe-separated:

​```
<commit> | <subsystem> | <wave-owner> | <spec?> | <review-tier>
​```

- `commit` — short SHA of the post-close change.
- `subsystem` — the persistence/publish surface it touched.
- `wave-owner` — the discovery wave that owned that subsystem (or `none` if unaudited).
- `spec?` — `yes`/`no`: did the change ship a spec?
- `review-tier` — the change's tier (SMALL/MEDIUM/COMPLEX).

Example:
​```
a1b2c3d | publish/digest_writer.py | WAVE-2 | no | MEDIUM
e4f5g6h | eval/gold_labels.py | none | no | SMALL
​```

When the open set accumulates several persistence-touching entries, cut a mini-wave from the
ledger. A `knowledge_lint` check validates that each entry line carries all five non-empty
fields; header, table-separator, comment, and blank lines are not entries.
```
(Note: the three `​``` ` fences above use a zero-width-space guard so this reference file itself
stays valid markdown; in the SKILL.md insertion they are ordinary triple-backtick fences.)
