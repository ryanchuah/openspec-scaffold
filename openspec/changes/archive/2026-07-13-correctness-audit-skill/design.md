# Design — correctness-audit-skill

## Context

Both downstream repos hand-rolled the same deep-audit protocol (extrends authored it,
psc-monitor ported and re-derived it); the frozen proposal commits to a scaffold-owned
`correctness-audit` skill standardizing the protocol while leaving product judgment
per-repo. Full prior-art extraction lives in `research/` (psc-audit-method.md,
extrends-audit-method.md); integration contracts with the frozen-but-unapplied OW-2
ratchet in `research/ratchet-and-verify-contracts.md`; scaffold constraints (manifest,
lint SEAL, budget table, FINDINGS glob/ID pattern) in `research/scaffold-conventions.md`.

Constraints that bind this design: stdlib-only Python 3.13 scripts; skills are
scaffold-managed and propagate byte-identical; `scaffold_lint.py`'s `budget-agreement`
check rejects unsanctioned `timeout -k` pairs; `knowledge_lint.py` runs on the live tree
via a pytest gate in every repo; `outstanding.py` already gathers
`knowledge/research/**/FINDINGS*.md` with ID pattern `\b[A-Z]{2,}(?:-[A-Z0-9]+)?-\d+\b`
and `knowledge_lint.py` flags untriaged findings older than 14 days.

**External-API live probe: skipped — zero external-API surface** (a markdown skill plus
stdlib lint additions; no client libraries, no network calls introduced).

## Goals / Non-Goals

**Goals**
- One skill any repo can invoke to run the audit protocol with zero method re-derivation.
- Each documented hand-rolled failure mode maps to a named mechanism (not prose warning).
- Findings route into OW-2's ratchet interface verbatim; nothing closes silently.
- Deterministic enforcement of the dossier format core, without touching legacy dossiers.

**Non-Goals**
- OW-6's cadence/trigger machinery; OW-1/OW-4 detectors; back-porting downstream
  dossiers; auto-provisioning per-repo config; remediation execution (ordinary OpenSpec
  changes own that).

## Decisions

**D1 — Single self-contained SKILL.md with inlined templates.** Charter skeleton, census
row format, and FINDINGS entry template are fenced blocks inside
`.claude/skills/correctness-audit/SKILL.md` (the OW-3 inlined-lens-prompt precedent).
*Alternative rejected:* `_shared/` sub-docs — each needs its own manifest line and no
second consumer exists. The skill will exceed the 87–117-line sibling norm; accepted — it
standardizes a multi-week program, and one long canonical file beats prose split across
files that drift independently. Registration edits ship with the skill file:
`scripts/scaffold_manifest.txt` gains the `.claude/skills/correctness-audit/SKILL.md`
line, and `correctness-audit` is added to `scaffold_lint.py`'s
`_NON_OPENSPEC_SKILL_TOKENS` — required because the AGENTS.md disambiguation sentence and
the `run-audit/SKILL.md` cross-pointer reference the skill by name, and the SEAL
(`test_live_repo_lints_clean`) runs `dangling-skill-refs` over exactly those files.

**D2 — The dossier is the checkpoint state; waves are NOT OpenSpec changes.** Audit state
lives entirely in the dossier dir `knowledge/research/correctness-audit-<YYYY-MM>/`:
`CHARTER.md` (single governing doc — scope, ground rules, severity taxonomy, wave plan
with per-wave status, verification-method map, prior-knowledge register pointer),
`CENSUS.md`, `FINDINGS-wave<N>.md`. Probe scripts/JSON/snapshots go to untracked
`tmp/`/`output/` ("regenerable evidence, not a record" — extrends convention). Resumption
after any interruption = re-read charter status + census dispositions.
*Alternative rejected:* one OpenSpec change per wave (what both repos did) — the change
lifecycle's premise gates, multi-model verify, and archive reconciliation exist to guard
production-code changes; an audit wave ships findings only, and psc's own dossier names
the per-wave lifecycle overhead as its top weakness. Operator control is preserved by the
skill's own gates: invocation is explicit (pull-only), and every wave boundary is an
operator gate (D6). Remediation changes still run the full lifecycle at their tier.

**D3 — Census: seeded mechanically, judged by the orchestrator, and it IS the stopping
rule.** Skeleton generated from the existing inventory fact (`facts.py` / `checks.py`
inventory output lists modules); the orchestrator prunes to in-scope surfaces and assigns
census slices to waves in the charter. Exactly one disposition per row:
`AUDITED-clean` / `AUDITED-finding` / `LEAD-deferred` / `N/A-<reason>` (fixed set for v1;
`N/A-<reason>` carries free text). A wave is complete when its slice has no undispositioned
rows; the audit is complete when no row is undispositioned. Rows are enumerated, never
tallied (never-record-counts). This fixes the no-stopping-rule failure mode extrends
documented.

**D4 — FINDINGS entry contract.** Per finding: `## CA-W<N>-<seq> — <title>` then fields
`Statement`, `Evidence` (`VERIFIED-BY-{repro|trace|test}` / `LEAD` / `REFUTED` /
`UNVERIFIABLE-HERE(<missing resource>)`; a repro label requires a named snapshot/fixture
path or it is disqualified; `UNVERIFIABLE-HERE` is a graduated label — its census row
becomes `LEAD-deferred` and it is dispositioned by the operator at close-out; its `Class:`
takes the safe default `none (one-off)` — an unconfirmed mechanism must not seed a ratchet
class, and the operator can re-open with a real class slug if later evidence surfaces),
`Severity`
(per-repo taxonomy value; PROVISIONAL until graduation), `Prior:` (mandatory —
`none (grep clean)` or `<ID> — distinct because <reason>`), `Class:` (mandatory-to-fill —
kebab-slug shared with ratchet-ledger class slugs, or literal `none (one-off)`, which
declares the OW-2 triage outcome Q2=no — point fix suffices, no ledger entry),
`Fix sketch`, `Effort` (S/M/L). A **graduation log** is appended at the top of each
FINDINGS file (append-only history of refutation sessions), separate from in-place field
updates. IDs match `outstanding.py`'s default pattern, so the outstanding fact and the
14-day untriaged-age lint pick every finding up with zero wiring.

**D5 — Graduation: refute, then re-check the refuter.** Every finding starts `LEAD`; no
severity is final until an adversarial refutation pass (fresh context, explicit brief to
refute) has run AND the orchestrator has re-checked the refuter's verdict against source —
psc's record shows refuter verdicts wrong ~4/9 in one batch, so the skill encodes the
overrule discipline as protocol: *a refuter's verdict is itself a claim to verify; the
orchestrator forms its own read of the crux before opening the refuter's verdict.*
Decision rule: false premise → `REFUTED`; real-but-milder mechanism → `VERIFIED-BY-*` with
severity overruled downward. Graduation writes back to the census: the finding's row takes
its final disposition (`AUDITED-finding`, or `LEAD-deferred` for `UNVERIFIABLE-HERE`).
Refutation has discovery value (psc found a real sibling defect during one), so the skill
instructs it: *if you discover a materially similar real defect during refutation, file it
as a new lead immediately.*

**D6 — Wave mechanics: sliced, checkpointed, operator-gated.** Investigation and
refutation slices are delegated via `opencode run` under the shared delegation harness
§a–e — the SKILL.md cites `_shared/delegation-harness.md` for invocation mechanics,
matching the propose/apply/verify/archive precedent — so every such slice is
timeout-bounded by construction. In-process subagents are reserved for orchestrator-local
mechanical steps (greps, census-skeleton generation, section assembly), where the
operator is present and a hang is recoverable; they are not the path for unattended
investigation work. Work is sliced into bounded invocations — one lead investigation, one
census slice sweep, or one refutation batch per invocation — each reusing a sanctioned
budget pair (`-k 15 780` review-class for investigation/refutation; `-k 30 600`
executor-class for mechanical slices). Each slice checkpoints one-line dispositions to
the dossier before returning (extrends' two-stage buffer: disposition lines first, prose
assembly later).
No new harness budget row; `delegation-harness.md` untouched. Every wave ends at an
explicit operator gate (psc's `⛔ WAVE GATE` marker pattern); an actively-occurring
critical finding may be escalated immediately past the gate (emergency clause).
Model routing is protocol, not guidance: judgment slices (investigation, refutation,
evidence labeling) → pro-tier; mechanical slices (greps, skeleton generation, assembly) →
flash-tier; severity/evidence labels are finalized only by the orchestrator regardless of
executor model; platform fallback (e.g. Sonnet) requires operator acknowledgment.

**D7 — Dedup is a format requirement, not a memory.** Before any finding is written up,
the author greps the dossier dir and the prior-knowledge register for the finding's file
path, function name, and candidate class slug; the result lands in `Prior:`. The
prior-knowledge register is a per-repo markdown file — suggested default
`knowledge/reference/known-findings-ledger.md` (durable, cross-audit, on-demand per the
knowledge taxonomy), with an inlined template in the skill (FIXED / ACCEPTED-BY-DESIGN /
ADMITTED-OPEN sections plus a prior-audit coverage map — the format both repos converged
on); the charter records the actual path so the D7 grep has a deterministic target. Each
wave opens with a mechanical re-read of all prior waves' `Class:` lines (a grep,
flash-tier).
This converts both repos' documented cross-wave duplicates (W3-E3/W4-M2a; CA-W1-20/
CA-W2-30) into a mechanically-checkable field. Uniqueness of IDs across the dossier is
enforced by the lint (D8).

**D8 — Dossier lint: one new `knowledge_lint.py` check, marker-gated for legacy safety.**
New `_check_audit_dossier`: scans `knowledge/research/correctness-audit-*/` dirs whose
`CHARTER.md` contains the literal marker line `format: correctness-audit/v1`; for those
dossiers only, flags (a) duplicate finding IDs across the dossier's FINDINGS files,
(b) census disposition values outside the D3 set, (c) graduated findings (any non-`LEAD`
evidence label) missing `Prior:` or `Class:`. Absent dossier → clean; dossier without
marker → skipped entirely; a dossier dir with no `CHARTER.md` at all → treated as
markerless and skipped (never a crash). **The marker gate is load-bearing:** both downstream repos
already have `knowledge/research/correctness-audit-2026-07/` dirs in nonconforming
formats — an unguarded lint would fail their live-tree pytest gates on the first sync.
*Alternatives rejected:* date cutoffs (arbitrary, silent) and per-repo config excludes
(pushes scaffold breakage onto every downstream repo's config). Detect-only, zero new
config keys for v1; same "absent → clean" shape as OW-2's `_check_ratchet_log`.

**D9 — Wave 0 verifies the audit's own instruments.** The charter template mandates a
Wave 0 (no findings): snapshot/scratch tooling proven, deterministic baseline captured,
and any invariant "ruler" the audit will cite verified against known-good fixtures first.
The fix-now criterion admits mid-audit code changes ONLY to harden audit instruments,
never the product. (Resolves premise-review 🟡2; both repos independently ran this phase.)

**D10 — Per-repo wiring: detect-and-explain, never auto-provision.** On invocation the
skill checks for an in-progress dossier (charter with unfinished waves → resume mode). If
none exists, it walks the operator through instantiating the inlined templates: severity
taxonomy derived from the product's worst *invisible* failure mode (the derivation
question both repos converged on), wave plan from the census skeleton, verification-method
map fixed per-lead before execution (no rubric-guessing at finding time). The skill never
writes per-repo config files silently (run-audit's wiring-detection precedent). (Resolves
premise-review 🟡3.)

**D11 — Close-out routes into OW-2's ratchet interface verbatim, and every finding ID is
triage-referenced at each wave gate.** The audit maintains one triage file,
`knowledge/questions/correctness-audit-<YYYY-MM>-triage.md`, created at Wave 0 and
**appended at every wave gate** — a concrete wave-gate checklist step in the skill, before
the gate is presented — with each newly graduated finding's ID and current disposition,
one line each: `- <ID>: <disposition> — <one-line essence>`. At audit close, findings
still ungraduated (`LEAD-deferred` census rows, including `UNVERIFIABLE-HERE`) get their
IDs appended the same way as part of operator dispositioning — no ID leaves the audit
without a triage reference. This is load-bearing for two reasons: (1) the shipped untriaged-finding
mechanism treats a finding ID as triaged only when the ID string appears somewhere under
`knowledge/questions/` — without this file, `REFUTED` and `Class: none (one-off)`
findings would have no triage reference and the 14-day `untriaged-finding-stale` lint
would break the repo's gate after every audit; (2) appending per wave gate (not only at
close-out) means an audit that runs longer than 14 days cannot trip the lint mid-flight
on its own early waves. At audit close, every graduated finding runs the frozen Q1/Q2/Q3
triage (real? → generalizable? → mechanically detectable or test-freezable?); qualifying
classes land as `knowledge/ratchet-log.md` registry lines using OW-2's exact line format
and disposition keywords (`check:` / `test:` / `waiver:review-by` / `open:since` /
`grandfathered`). `intentional-by-design` / `doc-only` closes are Q1=yes findings and
MUST carry a ledger disposition (typically `waiver:` with the design rationale) — the
silent-prose-closure gap psc named. `REFUTED` and Q2=no one-offs get no ledger entry
(the ledger holds classes), but their IDs are already in the triage file, so nothing
lints stale. The skill then produces a ranked remediation queue grouped by shared code
surface; the operator chooses posture (fix-promptly vs. defer-all — both are legal
precedents) at the close-out gate. Triage is orchestrator judgment, never delegated to a
mechanical executor (OW-2 spec requirement).

**D12 — Audit waves are exempt from the multi-model verify stack, by rule stated in the
skill.** The refutation-graduation pipeline (D5) is the audit's verification mechanism;
a findings-only activity re-verified by the change-lifecycle stack would duplicate D5 at
the token cost psc's dossier names as its top weakness. Dossier commits still pass the
commit-test-gate (trivially — no production code). Remediation changes get the full
lifecycle at their tier, including multi-model verify.

## Risks / Trade-offs

- **[Skill is long prose; downstream agents may skim]** → the format core is
  lint-enforced (D8); the untriaged-age ratchet is already deterministic; wave gates force
  operator contact at every boundary.
- **[780s slices fragment deep investigations]** → slicing unit is one lead/one batch
  (D6) with disposition-line checkpointing; psc ran multi-invocation waves successfully
  under the same budgets.
- **[Marker-gated lint means nonconforming new dossiers escape linting]** → the skill's
  charter template ships with the marker line included; a dossier created by the skill is
  always lint-visible. Hand-rolled dossiers bypassing the skill are out of scope (that is
  today's status quo).
- **[OW-2 not yet applied when this change freezes]** → apply-order dependency recorded in
  proposal + tasks; OW-5 cites OW-2 by requirement names/interface shapes, robust to
  OW-2's pending one-word validator fix.
- **[Findings-ID pattern collision with prose]** (e.g. `OW-5` matches the default ID
  regex) → FINDINGS files contain only audit content by contract; the graduation log and
  fields sections use the IDs deliberately. No change to `outstanding.py` defaults.
- **[Terminology confusion with `run-audit`]** → one-sentence disambiguation at the end of
  AGENTS.md's audit-tooling section naming the two families; cross-pointer in
  run-audit/SKILL.md (both already committed to in the proposal).

## Migration Plan

1. Land in scaffold (skill + lint + manifest + token set + AGENTS/run-audit pointers);
   full suite green (SEAL includes manifest-completeness and budget-agreement).
2. Propagate via normal operator-gated `sync_scaffold.py` run; downstream repos are inert
   until an operator invokes the skill (pull-only; legacy dossiers skipped by the marker
   gate).
3. Rollback: remove the skill file + manifest line + token entry + pointer sentences;
   `_check_audit_dossier` is inert wherever no marked dossier exists.

## Verification (change-specific acceptance criteria)

- `_check_audit_dossier` fixture tests: conforming dossier → clean; duplicate IDs across
  wave files → flagged; invalid census disposition → flagged; graduated finding missing
  `Prior:`/`Class:` → flagged; `LEAD` findings missing them → NOT flagged; dossier without
  the `format: correctness-audit/v1` marker → skipped; no dossier dir → clean.
- The SKILL.md's inlined template examples round-trip the lint: a dossier instantiated
  verbatim from the templates lints clean.
- Live tree passes `knowledge_lint.py` (this repo has no dossier → check inert).
- Full pytest suite green including the scaffold SEAL (manifest-completeness with the new
  skill line; budget-agreement with only sanctioned pairs embedded in the skill;
  dangling-skill-refs with `correctness-audit` in `_NON_OPENSPEC_SKILL_TOKENS`).
- Skill text contains: all six failure modes' mechanisms (census stopping rule, `Prior:`
  field, `Class:` slugs, refuter-overrule rule, wave gates, ratchet close-out with OW-2's
  verbatim triage/ledger formats), the per-wave-gate triage-file append (D11), the Wave-0
  mandate, the wiring-discovery walk-through, and the model-routing protocol.
- `openspec validate correctness-audit-skill --strict` passes before freeze is declared.
- First-real-audit manual check (not unit-testable — depends on real dates): confirm that
  wave-gate triage-file appends keep graduated findings out of the
  `untriaged-finding-stale` lint bucket during a live audit.

## Open Questions

None blocking. Deferred by design: per-repo extensibility of the census disposition set
(v1 fixed); a per-wave mini-triage default-on vs. close-out-only (v1: close-out required,
wave-gate triage optional).
