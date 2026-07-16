## Context

The scaffold-managed `outstanding-work-review` skill conflates two cost tiers behind one entry
point: a sub-second deterministic gather (`facts.py --check outstanding`) plus cheap
untriaged-bucket judgment, and a heavy full-repo prose crawl (its step-3 "Residual sweep" bullet).
The first real-world run (psc-monitor, 2026-07-15) demonstrated the split is load-bearing: the
deterministic collector is point-only/heading-only by design and structurally cannot read prose
bodies, so a manual 5-subagent crawl surfaced ~13 genuinely uncaptured items it missed.

This change splits the skill in two, mirroring the repo's own established
deterministic-detector-vs-deep-LLM-audit separation (`checks.py`/`facts.py` vs `correctness-audit`).
Because the skill is scaffold-managed, the rename is not a simple `mv` — it touches the manifest, a
removal tombstone, the AGENTS.md shared span, `knowledge/decisions/INDEX.md`, and the capability
spec, and (later, operator-gated) propagates to downstream repos. The source plan
(`plans/outstanding-work-review-residual-sweep.md`) holds the fully-written five-category checklist
and calibration evidence — this design condenses, it does not re-derive.

## Goals / Non-Goals

**Goals:**
- Keep the cheap "what's open right now?" path cheap **by construction** — a renamed
  `outstanding-work-scan` skill that never invites the heavy sweep.
- Give the deep residual sweep a documented, repeatable, pull-only procedure
  (`outstanding-work-deep-sweep`) with the same guardrails as `correctness-audit`.
- Execute the scaffold-rename cleanly: no orphaned old dir upstream, a tombstone so downstream sync
  deletes the stale dir, and every naming site updated in one batched pass.

**Non-Goals:**
- No change to `scripts/outstanding.py` enumeration, `finding_id_pattern` defaults, or any automated
  prose-body parsing — the deliverable is documenting the human/LLM judgment step, not automating it.
- No auto-run/boot wiring for either skill — both stay pull-only.
- No downstream `sync_scaffold.py` execution in this change — operator-gated follow-on.

## Decisions

**D1 — Rename the cheap skill to `outstanding-work-scan` (not keep `outstanding-work-review`).**
The source plan's Option B kept the old name; the operator chose to rename so the deterministic/deep
split is self-evident at the skill-list altitude. `outstanding-work-scan` signals the cheap
gather/scan basis. *Alternative considered:* `outstanding-work-deterministic-review` — rejected as
overclaiming, since the cheap skill retains a small untriaged-bucket dedup **judgment** step.

**D2 — Deep skill is a NEW capability spec, not an ADDED requirement on `outstanding-work-view`.**
`outstanding-work-deep-sweep/spec.md` is authored fresh, mirroring how `correctness-audit`,
`composition-audit`, and `product-audit` each own a capability spec. The existing
`outstanding-work-view` spec is MODIFIED only to rename its skill references
(`outstanding-work-review` → `outstanding-work-scan`) in its Purpose and the
`pull-only-agent-neutral-invocation` requirement/scenarios; the capability name and the `outstanding`
fact contract are unchanged. *Alternative considered:* fold the deep sweep into `outstanding-work-view`
as an added requirement — rejected: it mixes a deterministic-fact contract with a deep-LLM-sweep
contract in one capability, blurring exactly the separation this change establishes.

**D3 — Removal handled by the tombstone mechanism, not a bare delete.** The old
`.claude/skills/outstanding-work-review/SKILL.md` manifest line is repointed to the new
`outstanding-work-scan` path, a NEW manifest line is added for
`outstanding-work-deep-sweep/SKILL.md`, and the OLD path is appended to
`scripts/scaffold_manifest_removed.txt` with a dated comment. This is the same tombstone shape as
the existing `lint-knowledge`/`openspec-onboard` entries — it makes downstream sync **delete** the
stale old dir rather than leave both copies. *Alternative considered:* rely on manual downstream
cleanup — rejected: silent drift, exactly what the tombstone mechanism exists to prevent.

**D4 — The deep skill runs `outstanding-work-scan` as its step 1, then fans the five categories out
as parallel subagents.** This preserves the source-run structure (one subagent per blind-spot
category, each checkpointing to disk) and honors the delegation-by-default rule (run-and-extract →
subagent). Step 3 triages into `knowledge/questions/INDEX.md` / `knowledge/roadmap.md` exactly as the
current skill's step 3 does. The category-5 nested-evidence-citation false-positive sentence is
retained verbatim in intent (check *parent-ID disposition* before promoting a child citation) — it
alone was 51 of 52 "untriaged" hits in the source run.

**D5 — Batch every AGENTS.md/instruction-surface edit into one commit.** AGENTS.md is injected into
every delegated executor's prompt, so each edit invalidates the DeepSeek prefix cache for all
delegated agents. The single shared-span edit (the "Working process" bullet renaming the skill) is
batched with the rest of this change's landing.

**D6 — Version bump `metadata.version` on the renamed skill: `1.0` → `1.1`.** Confirmed convention:
`openspec-archive-change/SKILL.md` is the one skill in the tree at `"1.1"`, having bumped `1.0` →
`1.1` on a content change — the same shape as this rename. Hard-coded here so apply does not stall to
re-derive it.

## Risks / Trade-offs

- **Tombstone doesn't fire downstream (stale old dir survives)** → the downstream propagation
  (operator-gated, out of this change) explicitly verifies the old dir is deleted after sync; T-level
  acceptance for that lives with the propagation follow-on, not here. Within this repo, `scaffold_lint`
  + the manifest/tombstone consistency are checked by `check.sh`.
- **AGENTS.md prefix-cache invalidation** → mitigated by D5 (batch the shared-span edit).
- **Scope creep into `outstanding.py`/`finding_id_pattern`** → explicitly a Non-Goal; the
  nested-citation issue is documented as judgment, not automated. A tighter per-repo
  `finding_id_pattern` remains a per-repo config decision, not a scaffold default change.
- **Capability-name confusion** (spec capability `outstanding-work-view` vs skill
  `outstanding-work-scan`) → acceptable: the spec name describes the snapshot/view contract, the skill
  name describes the invocation surface; the MODIFIED spec's text makes the mapping explicit.

## Migration Plan

1. Rename skill dir + narrow step 3; add new deep-sweep skill.
2. Manifest repoint + new entry + tombstone; update AGENTS.md span, decisions entry, capability spec.
3. Author spec deltas (MODIFIED + NEW).
4. Verify: `check.sh`, `scaffold_lint.py`, `openspec validate --strict`.
5. Archive reconciles trackers + records the decision + the `freeze_check` bold-tolerance follow-on;
   downstream propagation queued on `pending-downstream-propagation.md`.

**Rollback:** the change is additive-plus-rename within one repo, no data migration. If wrong after
archive, `git revert` the commit(s) and open a corrective change (per AGENTS.md rollback rule); the
tombstone and manifest revert together with the skill dirs.

## Verification (change-specific acceptance criteria)

1. `.claude/skills/outstanding-work-scan/SKILL.md` exists; frontmatter `name: outstanding-work-scan`;
   `metadata.version` bumped; step 3 narrowed to the untriaged-bucket dedup-by-parent-ID judgment only
   (residual-prose-body scope removed and pointed at the deep skill). Old
   `.claude/skills/outstanding-work-review/` dir no longer exists.
2. `.claude/skills/outstanding-work-deep-sweep/SKILL.md` exists: step 1 runs `outstanding-work-scan`;
   step 2 = the five-category residual sweep as parallel subagents; step 3 triages into
   `knowledge/questions/INDEX.md` / `knowledge/roadmap.md`. Marked pull-only with
   `correctness-audit`-style guardrails — critically, **never wired into boot / AGENTS.md / any
   auto-run path**, and read-only w.r.t. repo state until the step-3 triage writes. Category-5
   nested-citation false-positive discipline present.
3. `scripts/scaffold_manifest.txt`: skill line repointed to `outstanding-work-scan`; NEW line for
   `outstanding-work-deep-sweep/SKILL.md`. `scripts/scaffold_manifest_removed.txt`: OLD
   `outstanding-work-review/SKILL.md` path appended with a dated comment.
4. AGENTS.md "Working process" bullet renamed to `outstanding-work-scan`;
   `knowledge/decisions/INDEX.md` reference updated; `openspec/specs/outstanding-work-view/spec.md`
   references updated. Research-dir mention left as-is (period-correct, lint-excluded).
5. Spec deltas present: MODIFIED `outstanding-work-view` (rename refs) + NEW
   `outstanding-work-deep-sweep` capability.
6. `scripts/check.sh` green; `scripts/scaffold_lint.py` clean; `openspec validate
   split-outstanding-work-skills --strict` exits 0 (confirmed syntax: `validate [item-name]` takes
   the change name positionally; add `--type change` only if a same-named spec makes it ambiguous).

## Open Questions

None blocking. (The `freeze_check.py` bold-`**`-tolerance robustness gap surfaced during this
change's own proposal review is recorded as an out-of-scope follow-on, not a decision for this change.)
