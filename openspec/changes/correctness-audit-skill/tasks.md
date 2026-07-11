# Tasks — correctness-audit-skill

Sequencing note for the orchestrator (not a task): this change has an apply-order
dependency on `lesson-check-ratchet` (OW-2) — do not start these tasks until OW-2's
apply has landed `knowledge/ratchet-log.md`, its lint, and the triage text in the live
tree. The skill file cites that interface as live behavior. After apply, verify
includes `openspec validate correctness-audit-skill --strict` per design § Verification.

## 1. Skill file

- [ ] 1.1 Create `.claude/skills/correctness-audit/SKILL.md` with: frontmatter matching
      the audit-family siblings exactly (`name: correctness-audit`; a one-sentence
      `description` stating it standardizes the deep LLM correctness-audit protocol,
      is Operator-invoked and pull-only, and never fixes product code; `license: MIT`;
      `compatibility: Requires openspec CLI.`; `metadata: author: openspec,
      version: "1.0", generatedBy: "1.4.1"` — copy the field set from
      `.claude/skills/run-audit/SKILL.md:1-10`); an opening restatement paragraph; a
      bold-lead cadence callout (**Operator-invoked / pull-only.** — never wired into
      session boot, archive, or any automatic trigger); and the named
      **Interpreter convention** block copied in form from
      `.claude/skills/run-audit/SKILL.md:23-28` — included because the skill invokes
      Python directly for census seeding (`<py> scripts/facts.py` inventory) and the
      dossier lint (`<py> scripts/knowledge_lint.py`), not only `opencode run`.
- [ ] 1.2 Add the protocol procedure as numbered bold-titled steps, sourcing every
      behavior from the frozen spec delta
      (`specs/correctness-audit/spec.md`) and design decisions: **Wiring/resume**
      (detect in-progress dossier → resume from disk; else walk the operator through
      instantiating charter + census from the inlined templates; severity taxonomy
      derived from the product's worst invisible failure mode; census seeded from the
      inventory fact; never auto-provision — design D2/D3/D10), **Wave 0** (instrument
      verification before any findings work; fix-now scope = audit instruments only —
      D9), **Waves** (bounded slices — one lead investigation / one census-slice sweep /
      one refutation batch per invocation; `opencode run` per
      `.claude/skills/_shared/delegation-harness.md` §a–e with only sanctioned pairs
      `-k 15 780` (investigation/refutation) and `-k 30 600` (mechanical); judgment →
      pro-tier, mechanical → flash-tier; disposition-line checkpointing before each
      slice returns; each wave OPENS with a mechanical re-read of all prior waves'
      `Class:` lines — a flash-tier grep, D7 — before any new lead is written up — D6),
      **Wave gate** (checklist: census slice fully dispositioned →
      graduation complete → append triage-file lines → present report at a literal
      `⛔ WAVE GATE — operator confirmation required.` marker; emergency escalation
      clause — D6/D11), **Graduation** (LEAD → adversarial refutation → orchestrator
      re-check with the overrule rule verbatim from D5; graduation log appended at top
      of each FINDINGS file; census write-back; refuter files materially-similar new
      leads immediately), **Close-out** (Q1/Q2/Q3 triage spelled out; ratchet ledger
      lines in the exact format and five disposition keywords quoted in the spec delta;
      `intentional-by-design`/`doc-only` → `waiver:review-by` disposition; LEAD-deferred
      and UNVERIFIABLE-HERE IDs appended to the triage file; ranked remediation queue +
      operator posture choice; remediation ships as ordinary OpenSpec changes — D11),
      and **Ground rules** (audit-then-fix; read-only + one canonical snapshot per wave;
      orchestrator-only severity/evidence finalization; never-record-counts naming the
      coverage-percentage trap; audit waves exempt from the multi-model verify stack
      because refutation-graduation is the audit's verification — D12).
- [ ] 1.3 Add the inlined templates as fenced blocks: CHARTER.md skeleton (scope,
      ground-rules citation, severity-taxonomy table, wave plan with per-wave status,
      verification-method map, prior-knowledge register path, and the literal line
      `format: correctness-audit/v1`), CENSUS.md row format (one line per surface,
      exactly one of `AUDITED-clean` / `AUDITED-finding` / `LEAD-deferred` /
      `N/A-<reason>`), FINDINGS entry template (`## CA-W<N>-<seq> — <title>` +
      Statement / Evidence / Severity / `Prior:` / `Class:` / Fix sketch / Effort, with
      one filled example), graduation-log block format, triage-file line format
      (`- <ID>: <disposition> — <one-line essence>` in
      `knowledge/questions/correctness-audit-<YYYY-MM>-triage.md`), and the
      known-findings-ledger template (FIXED / ACCEPTED-BY-DESIGN / ADMITTED-OPEN
      sections + prior-audit coverage map; suggested path
      `knowledge/reference/known-findings-ledger.md`) — per design D2/D3/D4/D7/D11 and
      both spec deltas.
- [ ] 1.4 End the skill with a **Guardrails** bullet list naming exactly what the audit
      may write (the dossier dir, the triage questions file, `knowledge/ratchet-log.md`
      at close-out, and — only under the fix-now criterion — audit-instrument code);
      everything else read-only; never proceed past a wave gate unattended; never
      auto-provision per-repo files; never record counts; remediation never ships
      inside the audit; the multi-model verify exemption applies to audit waves only,
      never to remediation changes.

## 2. Dossier lint

- [ ] 2.1 Add `_check_audit_dossier` to `scripts/knowledge_lint.py` beside
      `_check_untriaged_age`: iterate `knowledge/research/correctness-audit-*/` dirs;
      skip any dir whose `CHARTER.md` is missing or lacks the literal line
      `format: correctness-audit/v1`; for marked dossiers flag (a) a finding ID
      (heading-level `## CA-` entry ID) appearing more than once across the dossier's
      `FINDINGS*.md` files, reporting both locations, (b) a `CENSUS.md` row whose
      disposition is outside the four-value set (`N/A-` matched as a prefix),
      (c) a findings entry whose Evidence label is not `LEAD` (i.e. `VERIFIED-BY-*`,
      `REFUTED`, or `UNVERIFIABLE-HERE*`) missing a `Prior:` or `Class:` line within
      its entry block. Detect-only, stdlib-only, findings-emitting conventions copied
      from the adjacent checks; add its `findings.extend(_check_audit_dossier(...))`
      call to the flat sequence in `collect_findings()` alongside the other checks.
      Parse the formats exactly as the 1.3 templates define them (design D8).
- [ ] 2.2 Add fixture tests to `scripts/test_knowledge_lint.py` covering every scenario
      of the `knowledge-lint` spec delta: conforming marked dossier → clean; duplicate
      ID across two wave files → flagged with both locations; invalid census
      disposition → flagged; graduated entry missing `Prior:`/`Class:` → flagged; entry
      still `LEAD` missing them → NOT flagged; markerless dossier and
      dossier-dir-without-CHARTER → skipped clean; no dossier dir → clean. Build the
      conforming fixture by instantiating the 1.3 templates verbatim (the round-trip
      acceptance criterion in design § Verification).

## 3. Registration and pointers

- [ ] 3.1 Add `.claude/skills/correctness-audit/SKILL.md` to
      `scripts/scaffold_manifest.txt` in its sorted position among the
      `.claude/skills/` lines.
- [ ] 3.2 Add `"correctness-audit"` to `_NON_OPENSPEC_SKILL_TOKENS` in
      `scripts/scaffold_lint.py` (the set near line 168; keep it sorted/formatted as
      the existing entries are).
- [ ] 3.3 Append one sentence at the END of `AGENTS.md`'s
      `## Deterministic audit tooling` section (inside the synced span, as a new final
      paragraph after the "Discover checks" paragraph): stating that deep LLM
      correctness audits are a separate
      surface owned by the operator-invoked `correctness-audit` skill, which
      standardizes the charter/census/findings protocol and routes findings into the
      finding-closure ratchet — while this section's ceremony remains
      deterministic-detector-only.
- [ ] 3.4 Add one cross-pointer line to `.claude/skills/run-audit/SKILL.md` (in its
      opening boundary callout area): the deterministic ceremony here is distinct from
      the deep LLM audit program, which is the `correctness-audit` skill.

## 4. Gate

- [ ] 4.1 Run `bash scripts/check.sh` (ruff + format + full pytest including the
      scaffold SEAL) and fix any failure caused by these edits — expected sensitive
      checks: `manifest-completeness` (3.1), `dangling-skill-refs` (3.2–3.4),
      `budget-agreement` (only sanctioned pairs may appear in 1.2), and the live-tree
      `knowledge_lint` gate (2.1 must be inert on this repo, which has no dossier).
