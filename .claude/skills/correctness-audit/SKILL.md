---
name: correctness-audit
description: Standardize the deep LLM correctness-audit protocol — operator-invoked, pull-only, never fixes product code. Standardizes charter/census/findings protocol, routes findings into the finding-closure ratchet.
license: MIT
compatibility: Requires openspec CLI.
metadata:
  author: openspec
  version: "1.0"
  generatedBy: "1.4.1"
---

Deep LLM correctness-audit protocol — a scaffold-owned standard for running multi-wave correctness audits, owned by the operator and never boot-wired. Standardizes the audit method (charter, census, findings entry contract, wave mechanics, close-out routing into the finding-closure ratchet) and leaves product judgment per-repo. Implements the correctness-audit capability spec.

**Operator-invoked / pull-only.** — never wired into session boot, archive, or any automatic trigger. Deterministic audit ceremony is the sibling `run-audit` skill; this skill covers the deep LLM correctness audit only.

**Interpreter convention.** Use `<py>` below as a placeholder for the repo's Python interpreter. Resolve it in this try-order:
1. A repo task-runner `audit-*` target, if one exists (e.g. `just audit-floor`);
2. `.venv/bin/python` if the virtual environment exists;
3. `python3` if available;
4. `python` otherwise.

## Protocol procedure

### Wiring/resume

On invocation, detect whether a correctness-audit dossier already exists under `knowledge/research/correctness-audit-<YYYY-MM>/`:

- **If a dossier exists with a `CHARTER.md` whose per-wave status shows unfinished waves** → resume mode. Read the charter's wave status and the census dispositions from disk. The dossier is the durable checkpoint state (D2): no work is lost beyond the in-flight slice. Resume from the first incomplete wave.
- **If no dossier exists** → walk the operator through instantiating the inlined templates below:
  1. Create `knowledge/research/correctness-audit-<YYYY-MM>/` with the `CHARTER.md` skeleton (below), `CENSUS.md` (below), and a `FINDINGS-wave1.md` file.
  2. Derive the severity taxonomy from the product's worst *invisible* failure mode — the derivation question both repos converged on: "what is the worst bug class that would never be caught by the per-change verify gate, and what severity axis best captures its impact?"
  3. Seed the census skeleton from the inventory fact (`<py> scripts/facts.py` — run it and read its output; the inventory fact lists modules and surfaces). The orchestrator prunes to in-scope surfaces and assigns census slices to waves in the charter.
  4. Set the wave plan, verification-method map (fixed per-lead before execution), and prior-knowledge register path in the charter. The register path defaults to `knowledge/reference/known-findings-ledger.md` — the charter records the actual path so the D7 dedup grep has a deterministic target.
  5. **Never auto-provision.** The skill walks through these steps with the operator and writes files only on explicit instruction. (D10)

### Wave 0 — instrument verification

Before any findings work, run Wave 0 (no findings are filed in this wave):
- Prove snapshot/scratch tooling works.
- Capture the deterministic baseline (`<py> scripts/checks.py --floor` and `<py> scripts/facts.py` — both must run clean on the live tree).
- Verify any invariant "ruler" the audit will cite against a known-good fixture before it is applied.
- If any audit instrument is found defective, **fix it now** (fix-now criterion: mid-audit code changes are admitted ONLY to harden audit instruments, NEVER the product; D9).
- Populate `knowledge/research/correctness-audit-<YYYY-MM>/` with empty/template files for census and findings. Create the triage file at `knowledge/questions/correctness-audit-<YYYY-MM>-triage.md` (empty, to be appended at every wave gate — D11).
- Wave 0 is complete when instruments are proven and the dossier skeleton is in place. It does not present a wave gate (no findings were filed); the operator confirms readiness to proceed.

Wave 0's status in the charter SHALL be `WAVE-0: done` when complete.

### Waves

Wave work is sliced into bounded, checkpointed invocations:
- **One lead investigation**, **one census slice sweep**, or **one refutation batch** per invocation.
- Each invocation uses `opencode run` under `.claude/skills/_shared/delegation-harness.md` §a–e with only sanctioned timeout budget pairs:
  - Investigation and refutation (judgment work) → pro-tier model with `-k 15 780`.
  - Mechanical slices (greps, census-skeleton generation, section assembly) → flash-tier model with `-k 30 600`.
- Each slice checkpoints one-line dispositions to the dossier **before returning** (disposition lines first, prose assembly later — the two-stage buffer from extrends' practice).
- Model routing is protocol: judgment slices (investigation, refutation, evidence labeling) → pro-tier; mechanical slices → flash-tier. Severity/evidence labels are finalized ONLY by the orchestrator regardless of executor model. Platform fallback (e.g. Sonnet) requires operator acknowledgment.

**Wave opening (D7):** Each wave OPENS with a mechanical re-read of all prior waves' `Class:` lines — a flash-tier grep across all `FINDINGS-wave*.md` files in the dossier. The result feeds the `Prior:` field of each new finding before write-up. This dedup is a format requirement, not memory.

**During the wave:** The author of each finding (before write-up) greps the dossier dir AND the prior-knowledge register (path recorded in the charter) for the finding's file path, function name, and candidate class slug. The result lands in `Prior:` as `none (grep clean)` or `<ID> — distinct because <reason>`.

### Wave gate

At the end of each wave, before the next wave starts:

1. ✅ Confirm the wave's census slice is **fully dispositioned** — no undispositioned rows remain. A wave whose census slice still has undispositioned rows is NOT complete (D3/D6).
2. ✅ Confirm all findings in the wave have been **graduated** (run through adversarial refutation — see Graduation below).
3. ✅ **Append the triage file** (`knowledge/questions/correctness-audit-<YYYY-MM>-triage.md`) with one line per newly graduated finding:
   `- <ID>: <disposition> — <one-line essence>`
   This is load-bearing (D11): without this append, graduated findings would have no triage reference, and the 14-day `untriaged-finding-stale` lint would break the repo's gate mid-audit.
4. Present the wave-gate report to the operator at a literal marker:
   ```
   ⛔ WAVE GATE — operator confirmation required.
   ```
   Include: the completed wave's summary (census rows dispositioned, findings IDs + severity, findings graduated), the current triage-file snapshot, and the proposed next wave's scope.
5. **Stop** — does not proceed past the wave gate unattended. The operator confirms or redirects.

**Emergency escalation:** An actively-occurring critical finding (one that the auditor judges requires immediate operator attention) may be escalated past the wave gate immediately. The escalation report SHALL include the finding ID, severity, and the reason it cannot wait for the gate.

### Graduation (D5)

Every finding starts as `LEAD`. No severity is final until:

1. **Adversarial refutation pass** — a fresh `opencode run` invocation (pro-tier, `-k 15 780`) with an explicit brief to refute the finding. The refuter is given the finding's Statement, Evidence, and supporting materials, and instructed to find counter-evidence, alternative explanations, or false premises.
2. **Orchestrator re-check** — the orchestrator forms its own read of the finding's crux **before opening the refuter's verdict**. A refuter's verdict is itself a claim to verify. Decision rule:
   - False premise → `REFUTED`
   - Real-but-milder mechanism → `VERIFIED-BY-*` with severity overruled downward
3. Apply the verdict and severity (finalized only by the orchestrator):
   - Set the finding's Evidence label and Severity.
   - Update `Class:` (kebab-slug) or confirm `none (one-off)`.
   - `UNVERIFIABLE-HERE` findings default to `Class: none (one-off)` — an unconfirmed mechanism must not seed a ratchet class.
4. **Append to graduation log** at the top of the finding's `FINDINGS-wave<N>.md` file — an append-only history entry (date, IDs adjudicated, verdicts, orchestrator overrules).
5. **Write back to census** — the finding's census row takes its final disposition: `AUDITED-finding`, or `LEAD-deferred` for `UNVERIFIABLE-HERE`.

**Refuter discovery value:** If the refuter discovers a materially similar real defect during refutation, file it as a new lead immediately.

### Close-out

When the census is fully dispositioned (no undispositioned row anywhere), the audit is complete:

1. **Run the finding-closure-ratchet three-question triage** (orchestrator judgment, never delegated — per OW-2/OW-5 spec) on every graduated finding:
   - Q1: Real defect (not noise/env)? No → stop (no ledger entry).
   - Q2: Generalizable class (sibling could recur)? No → stop (point fix suffices); `Class: none (one-off)`.
   - Q3: Mechanically detectable or test-freezable?
     - Yes → disposition `check:<pointer>` or `test:<path>[::<name>]`.
     - No → disposition `waiver:review-by YYYY-MM-DD` or `open:since YYYY-MM-DD` or `grandfathered`.

2. Append **one `knowledge/ratchet-log.md` registry line per qualifying class** using the exact line format:
   `- **YYYY-MM-DD** · <kebab-class-slug> · <disposition> — <essence>`
   With the five disposition keywords verbatim (OW-2 interface):
   - `check:<pointer>` — enforcing deterministic detector exists.
   - `test:<path>[::<name>]` — frozen regression test exists.
   - `waiver:review-by YYYY-MM-DD` — domain judgment only, with a re-review trigger.
   - `open:since YYYY-MM-DD` — deferred with age-flagging.
   - `grandfathered` — inherited, no active enforcement.

3. **`intentional-by-design` / `doc-only` closes** (Q1=yes findings closed by documentation correction with no enforcing check/test) MUST carry a ledger disposition (`waiver:review-by` with rationale) — never a silent prose close.

4. **`REFUTED` findings and Q2=no one-offs** get no ledger entry. Their IDs are already in the triage file (appended per wave gate), so nothing lints stale.

5. Append remaining ungraduated findings (`LEAD-deferred` census rows, including `UNVERIFIABLE-HERE`) to the triage file as part of operator dispositioning — same format, one line per ID. No finding ID leaves the audit without a triage reference.

6. **Produce a ranked remediation queue** grouped by shared code surface. The operator chooses posture at the close-out gate: fix-promptly or defer-all (both are legal precedents).

7. Remediation ships as ordinary OpenSpec changes citing finding IDs — never inside the audit (D11).

### Ground rules

- **Audit-then-fix.** The audit produces findings only. No product code is modified during the audit. The sole exception is the fix-now criterion (Wave 0 / mid-audit instrument hardening only — D9).
- **Read-only + one canonical snapshot per wave.** The dossier is the only tracked state; probe scripts, scan JSON, and snapshots go to untracked `tmp/`/`output/` (regenerable evidence, not a record). Each wave has exactly one canonical snapshot.
- **Orchestrator-only severity/evidence finalization.** The executor tier (pro or flash) drafts; the orchestrator finalizes. Severity labels set by an executor are PROVISIONAL until the orchestrator confirms them. The refuter's verdict is itself a claim to verify — the orchestrator forms its own read of the crux before opening the verdict (D5).
- **Never record counts.** Census rows are enumerated, never tallied. The coverage-percentage trap is named: "95% audited" is a meaningless summary — list the remaining 5%. Each surface has exactly one disposition.
- **Audit waves are exempt from the multi-model verify stack** (D12). The refutation-graduation pipeline (D5) is the audit's verification mechanism. Findings-only activity re-verified by the change-lifecycle stack would duplicate D5. Dossier commits still pass the commit-test-gate (trivially — no production code). Remediation changes get the full lifecycle at their tier, including multi-model verify.

## Inlined templates

### CHARTER.md skeleton

```markdown
# Correctness Audit Charter — <product-name> — <YYYY-MM>

## Scope
<List of surfaces in scope for this audit, derived from the census skeleton.
One brief line per surface or surface group.>

## Ground rules
This audit follows the `correctness-audit` skill protocol.
- Audit-then-fix: no product code is modified during the audit.
- Read-only + snapshot discipline: the dossier is the only tracked state;
  regenerable evidence goes to `tmp/`/`output/`.
- Orchestrator-only severity/evidence finalization.
- Never record counts: census rows are enumerated, never tallied.
- Audit waves are exempt from the multi-model verify stack — the
  refutation-graduation pipeline is the audit's verification.

## Severity taxonomy
Derived from the product's worst invisible failure mode:

| Severity | Meaning | Typical trigger |
|----------|---------|-----------------|
| <label> | <definition> | <example trigger> |
| <label> | <definition> | <example trigger> |
| <label> | <definition> | <example trigger> |
| <label> | <definition> | <example trigger> |

(Replace the table with the per-repo taxonomy.)

## Wave plan

| Wave | Census slice | Status | Findings |
|------|-------------|--------|----------|
| 0 | Instrument verification | WAVE-0: done | — |
| 1 | <slice> | WAVE-1: active / done | CA-W1-* |
| 2 | <slice> | WAVE-2: planned / active / done | CA-W2-* |
| 3 | <slice> | WAVE-3: planned | CA-W3-* |

## Verification-method map
Each lead's verification method is fixed here, before execution:

| Verification method | When to apply | Entry label |
|--------------------|---------------|-------------|
| `repro` | Scripted reproduction with a named fixture/snapshot path | `VERIFIED-BY-repro` |
| `trace` | Manual code trace with documented path | `VERIFIED-BY-trace` |
| `test` | Unit/integration test that exercises the codepath | `VERIFIED-BY-test` |
| `refute` | Adversarial refutation (finding premise verified false) | `REFUTED` |
| `unverifiable` | Cannot be verified with available resources | `UNVERIFIABLE-HERE(<missing>)` |

## Prior-knowledge register
Path: `knowledge/reference/known-findings-ledger.md`
(Default suggestion; replace with the actual path.)

---
format: correctness-audit/v1
```

### CENSUS.md row format

One line per in-scope surface. Pipe-separated:

```
<surface-path/name> | <disposition> | <finding-IDs> | <notes>
```

Where `<disposition>` is exactly one of:
- `AUDITED-clean` — inspected, no finding.
- `AUDITED-finding` — finding filed and graduated; IDs column lists the finding IDs.
- `LEAD-deferred` — surface has one or more leads not yet graduated (including `UNVERIFIABLE-HERE` findings); IDs column lists the deferred finding IDs.
- `N/A-<reason>` — not applicable (outside scope, deprecated, etc.); reason is free text.

The `AUDITED-finding` and `LEAD-deferred` dispositions SHALL carry at least one ID in the IDs column.

Example:
```
knowledge/reference/notes.md       | AUDITED-clean    | —              | No issues
scripts/ingestion.py               | AUDITED-finding  | CA-W1-3        | Silent data truncation on field overflow
scripts/validation.py              | LEAD-deferred    | CA-W2-7        | Needs deeper trace, deferred
vendor/old-lib/                    | N/A-no-source    | —              | No source available for review
```

A wave is complete when its slice has no undispositioned rows. The audit is complete when no row is undispositioned.

### FINDINGS entry template

```markdown
## CA-W<N>-<seq> — <title>

**Statement**
<One-paragraph description of the defect or concern.>

**Evidence**
LEAD
(PROVISIONAL — label set by the executor, replaced at graduation. Final labels: `VERIFIED-BY-repro`, `VERIFIED-BY-trace`, `VERIFIED-BY-test`, `REFUTED`, `UNVERIFIABLE-HERE(<missing resource>)`.)
A bare `confirmed` is not a valid label. A `VERIFIED-BY-repro` label without a named snapshot/fixture path is disqualified.

**Severity**
<Per-repo taxonomy value> (PROVISIONAL until graduation)

**Prior:**
none (grep clean)
(or: `<ID> — distinct because <reason>`)

**Class:**
<kebab-class-slug>
(or: `none (one-off)` — the triage outcome Q2=no; no ratchet ledger entry.)

**Fix sketch**
<Brief description of how to fix this.>

**Effort:** <S/M/L>
```

Filled example:
```markdown
## CA-W1-3 — Silent data truncation in ingestion.field_write()

**Statement**
When `field_write()` receives a value whose encoded length exceeds the target field's schema limit, it truncates the value at the limit boundary without logging or returning an error. Downstream consumers read silently incorrect data.

**Evidence**
VERIFIED-BY-repro
Repro snapshot: `tmp/correctness-audit-2026-07/repro/field_write_truncation.py`

**Severity**
HIGH — corrupts persisted data without detection. The per-change verify gate never exercises this code path because test fixtures use small values.

**Prior:**
none (grep clean)

**Class:**
silent-truncation

**Fix sketch**
Add a length check before the `cursor.copy()` call; raise `DataError` on overflow. Wire a test that exercises the overflow path.

**Effort:** S
```

### Graduation-log block format

Appended at the top of each `FINDINGS-wave<N>.md` file. Append-only history; each refutation session produces one block:

```markdown
### Graduation log

- **YYYY-MM-DD** — Refutation session
  - Adjudicated: CA-W1-3, CA-W1-4
  - Verdicts: CA-W1-3 → VERIFIED-BY-repro (H → M — orchestrator overruled severity downward: mechanism real but exploitable only under admin credentials); CA-W1-4 → REFUTED (premise false — the target field is schema-validated at a higher layer)
  - Overrules: CA-W1-3 severity H→M
```

### Triage-file line format

File path: `knowledge/questions/correctness-audit-<YYYY-MM>-triage.md`

Each line:
```
- <ID>: <disposition> — <one-line essence>
```

Example:
```
- CA-W1-3: AUDITED-finding — Silent data truncation in ingestion.field_write()
- CA-W1-4: REFUTED — Field overflow in validation layer (premise false)
- CA-W2-7: LEAD-deferred — Validation.py needs deeper trace
```

### Known-findings-ledger template

Suggested path: `knowledge/reference/known-findings-ledger.md`

```markdown
# Known Findings Ledger — <product-name>

Durable, cross-audit record of known findings, grouped by closure category.
Findings IDs reference the originating correctness audit dossier.
This file is the **prior-knowledge register** for the `Prior:` dedup field.

## FIXED

| ID | Class | Fix | Audit |
|----|-------|-----|-------|
| CA-W1-3 | silent-truncation | Length check + DataError in ingestion.py | 2026-07 |

## ACCEPTED-BY-DESIGN

| ID | Class | Rationale | Ledger disposition |
|----|-------|-----------|--------------------|
| CA-W2-1 | soft-fail | Domain decision: silent skip is preferred over hard error in this path; documented in `docs/design/soft-fail.md`. | `waiver:review-by 2027-01-01` |

## ADMITTED-OPEN

| ID | Class | Open since | Notes |
|----|-------|------------|-------|
| CA-W2-7 | deferred-validation | 2026-07 | Needs deeper code trace; deferred by operator at close-out. |

## Prior-audit coverage map

| Audit | Coverage | Key classes filed |
|-------|----------|-------------------|
| 2026-07 | scripts/ingestion.py, scripts/validation.py | silent-truncation, soft-fail, deferred-validation |
```

## Guardrails

- The correctness-audit skill may write to **the dossier dir** (`knowledge/research/correctness-audit-<YYYY-MM>/`), **the triage questions file** (`knowledge/questions/correctness-audit-<YYYY-MM>-triage.md`), and **`knowledge/ratchet-log.md`** at close-out, and — only under the fix-now criterion (D9) — **audit-instrument code**.
- Everything else is read-only: the skill does not modify product code, config files, or other tracked knowledge.
- The skill never proceeds past a wave gate unattended. Each wave boundary is an explicit operator gate.
- The skill never auto-provisions per-repo files. Wiring is detect-and-explain (D10).
- Never record counts: census rows are enumerated, never tallied (D3).
- Remediation never ships inside the audit: it ships as ordinary OpenSpec changes citing finding IDs (D11).
- The multi-model verify stack exemption applies to audit waves only, NEVER to remediation changes (D12).
