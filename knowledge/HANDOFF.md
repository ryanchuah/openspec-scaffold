# HANDOFF — OW-16 (product-audit-skill) shipped; wave-2 remaining OW-12 + OW-11 residual (2026-07-14)

> **Read this right after `knowledge/STATUS.md`.** A session shipped **`product-audit-skill` (OW-16,
> COMPLEX)** end-to-end — explore(+direction gate) → propose → apply → verify → archive, committed on
> `main`, local & **unpushed** (push is operator-gated). Downstream propagation is **DEFERRED +
> operator-gated**. Absorb this, pick up from **Remaining work**, and **delete this file once absorbed**
> (its normal state is absent).
>
> **You have NO standing autonomy grant.** Confirm tier+plan per change unless the operator re-grants
> autonomy. (This session HAD an explicit grant; it does not carry over.)

## DONE this session — product-audit-skill (OW-16)
The seventh audit class: a new operator-invoked, pull-only **`product-audit`** skill whose object is the
product's promise surface (pricing/landing/README copy) and business thesis, and whose oracle is the code
and the market — the inverse of the six code-facing audit classes. Protocol: blind attack-list (committed
before evidence) → five-lane evidence fan-out (impl-as-sold · cost/critical-path · repo+git+GTM sweep ·
live-web regulatory · live-web competitive; web lanes on the research convention) → per-attack disposition
diff (CONFIRMED/PARTIAL/SURVIVED-BY-THESIS/OPEN) → operator ratification menu → `PRODUCT:
CLEAN|FINDINGS-ROUTED|ESCALATE` verdict. Ships the **claims-ledger convention** (promise → delivering
surface → proving check) with a **content-sha256 covered-file manifest**, guarded by a new marker-gated
`knowledge_lint` **`claims-ledger-staleness`** detector. Operationalizes OW-15's carried-forward classes
9–12. New `product-audit` capability spec + `knowledge-lint` ADDED requirement; **no
`finding-closure-ratchet` change** (existing dispositions suffice). Full record: decisions —
`knowledge/decisions/INDEX.md` (`product-audit-skill`); follow-ons —
`knowledge/questions/product-audit-skill-follow-ons.md`; archive —
`openspec/changes/archive/2026-07-14-product-audit-skill/`.

Verify: premise AGREE at every altitude (direction gate + proposal); self-review + 4 orchestrator-authored
adversarial boundary fixtures + flash test-quality lens all READY; simplicity gate clean; `check.sh` green;
live-tree lint clean; **zero Sonnet fallback on apply**.

## Hard-won lessons (process — carried forward)
1. **Apply-split worked again (HANDOFF lesson, re-confirmed).** The fence-heavy `SKILL.md` prose was
   **orchestrator-authored** (checked off `[x]` before delegating), then the deterministic Python
   (detector + tests + registration) went to the flash apply-executor, which resumed at the first `[ ]`.
   Clean, zero flash fallback. Keep splitting mixed prose+code applies this way.
2. **⚠️ `deepseek/deepseek-v4-pro` VERIFIER emitted zero text this session.** In BOTH the concurrent
   behavioral pass and a focused re-run, the pro-tier *verifier* ran tool calls but produced NO
   text/verdict (exit 0, but empty). The flash lens pass and the pro *reviewer* (premise/proposal/design/
   specs/tasks) all worked fine — only the pro `openspec-verifier` behavioral pass failed to emit. Per the
   verify ladder this fell back to a **Sonnet subagent** for the behavioral pass (clean independent READY).
   If you hit the same: don't burn 3 retries — one focused re-run, then Sonnet. Monitor whether this is a
   persistent pro-verifier-tier degradation (routed to the follow-ons file + here).
3. **`checks.py --check <name>` litters cwd.** Running a single check (e.g. `checks.py --check
   spec-delta-structure`) writes `<name>.json` to the repo root, NOT `output/`. A `git add -A` after that
   sweeps the stray json into the commit — I caught and amended it out. Either run checks with
   `--report --out output/...`, or `git add` specific paths (not `-A`) after a bare `--check`. Candidate
   tiny follow-on: gitignore `*.json` at repo root, or make `--check` write to a temp/output path.
4. **Fold-by-coherence, re-confirmed (prior HANDOFF lesson).** OW-16 was shipped ALONE — it is a greenfield
   capability sharing only the blind-diff *method* with OW-15, so it was never a fold candidate with OW-12
   (archive tooling) or OW-11-residual (skill de-bloat). "Fold as much as you can" = maximal *coherent*
   unit (one capability/concern), not maximal count. OW-12 and OW-11-residual are two *separate*
   mechanization concerns — do not fold them together just because both are "lifecycle tooling."

## Remaining work — OW-12, OW-11 residual (the wave-2 tail)
- **OW-12 · Archive mechanization · SMALL–MEDIUM · lowest priority · no recon yet.** `archive_move.py`
  for the dir move; a deterministic delta-applier for ADDED/REMOVED/RENAMED spec promotion (LLM only for
  MODIFIED merge + the doc reconciliation narrative). Keep the archive-executor on pro — what remains IS
  the judgment. Backlog: `OUTSTANDING-WORK.md` OW-12.
- **OW-11 residual (fuzzy de-bloat half)** → `knowledge/questions/skill-debloat-gates-follow-ons.md`:
  replace verify steps 12–16 with deterministic CLI coverage + a coherence note; trim explore's gallery
  prose; a `freeze-check` script (parse review verdict → FREEZE-OK/BLOCKED, needs a `FREEZE:` token); a
  `notes_lint.py` five-field gate. Independent; nothing blocks on them.
- **After these, scaffold optimization is at diminishing returns** (2026-07-11 workflow-audit verdict) —
  further sessions should spend downstream (extrends' ~33 open defect classes), not new scaffold mechanism.
- **OW-16 residual follow-ons** (monitored, none blocking) →
  `knowledge/questions/product-audit-skill-follow-ons.md`: optional sha256-recompute helper; ledger-home
  fixed to `knowledge/reference/*.md`; staleness fires on any content change (by-design); manifest
  completeness deliberately un-linted; + the pro-verifier-no-output infra note.

## Downstream propagation — DEFERRED + operator-gated
OW-16 edited scaffold-managed surfaces: `.claude/skills/product-audit/SKILL.md` (new),
`scripts/knowledge_lint.py` + `scripts/test_knowledge_lint.py` (new `claims-ledger-staleness` detector),
`scripts/scaffold_manifest.txt`, `scripts/scaffold_lint.py`. The two capability specs are golden-source-
only (never synced). The new lint is guarded on `format: product-audit/v1` — no downstream repo has a
claims ledger yet, so **no new downstream lint failures on first sync**. NOT synced to extrends/psc-monitor
without fresh operator authorization. Running ledger: `knowledge/reference/pending-downstream-propagation.md`.

## Pointers
- Backlog + per-item STATUS: `knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md`.
- OW-16 evidence: `knowledge/research/scaffold-gap-analysis-2026-07/psc-strategy-pressure-test-2026-07-12.md`.
- This change (full record): `openspec/changes/archive/2026-07-14-product-audit-skill/`.
