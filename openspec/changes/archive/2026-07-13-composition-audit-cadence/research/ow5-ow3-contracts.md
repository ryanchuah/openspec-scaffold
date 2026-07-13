# OW-5 / OW-3 contracts and the boundary they leave for OW-6

Digest for `composition-audit-cadence` (OW-6). Source changes are FROZEN (propose complete,
artifacts reviewed, apply paused) — text below is contract, not yet live in the tree.

- OW-5 = `openspec/changes/correctness-audit-skill/` (the deep LLM correctness-audit protocol)
- OW-3 = `openspec/changes/verify-stack-redirect/` (the per-change verify multi-model chain)

---

## 1. OW-5 protocol shape (quoted, load-bearing formats)

**Skill identity.** Operator-invoked, pull-only, sibling of `run-audit` /
`knowledge-drift-review` / `outstanding-work-review`. Spec requirement (verbatim):

> "The deep LLM correctness-audit protocol SHALL be owned by the scaffold as a single
> skill (`.claude/skills/correctness-audit/SKILL.md`), operator-invoked and pull-only —
> never wired into session boot, archive, or any automatic trigger."
(`specs/correctness-audit/spec.md:5-8`)

**Charter + format marker.** Durable state lives in
`knowledge/research/correctness-audit-<YYYY-MM>/` (`CHARTER.md`, `CENSUS.md`,
`FINDINGS-wave<N>.md`). The charter must carry the literal marker line
`format: correctness-audit/v1` (`design.md:31-32`, `specs/correctness-audit/spec.md:31-32`).
Audit waves are explicitly **not** OpenSpec changes (`design.md:51-63`, D2).

**Census as stopping rule.** Fixed disposition set, exactly one per in-scope surface:
`AUDITED-clean` / `AUDITED-finding` / `LEAD-deferred` / `N/A-<reason>`. Verbatim:

> "A wave SHALL be declared complete only when its census slice has no undispositioned
> rows; the audit SHALL be declared complete only when no census row anywhere is
> undispositioned. Census rows are enumerated, never tallied (never-record-counts)."
(`specs/correctness-audit/spec.md:46-50`)

**FINDINGS entry contract.** ID pattern `CA-W<wave>-<seq>` (matches the shipped
`outstanding.py` default ID regex `\b[A-Z]{2,}(?:-[A-Z0-9]+)?-\d+\b`,
`design.md:17-18`). Fields: Statement; Evidence (`VERIFIED-BY-{repro|trace|test}` /
`LEAD` / `REFUTED` / `UNVERIFIABLE-HERE(<missing resource>)`); Severity (PROVISIONAL
until graduation); `Prior:` (mandatory dedup field); `Class:` (mandatory-to-fill); Fix
sketch; Effort. Verbatim on the dedup/class fields:

> "`Prior:` (mandatory — `none (grep clean)` or `<ID> — distinct because <reason>`,
> produced by grepping the dossier and the prior-knowledge register for the finding's
> file path, function name, and candidate class slug before write-up); `Class:`
> (mandatory-to-fill — a kebab-slug shared with the ratchet ledger's class slugs, or the
> literal sentinel `none (one-off)` declaring the triage outcome Q2=no)."
(`specs/correctness-audit/spec.md:69-74`)

**Wave gates + per-wave triage file.** Every wave ends at an explicit operator gate
(psc's `⛔ WAVE GATE` marker pattern, `design.md:119`); a triage file
`knowledge/questions/correctness-audit-<YYYY-MM>-triage.md` is created at Wave 0 and
**appended at every wave gate** (not just close-out) — load-bearing because the shipped
untriaged-finding mechanism treats an ID as triaged only when the ID string appears
under `knowledge/questions/`, and appending only at close-out would let an audit
running past 14 days trip the `untriaged-finding-stale` lint mid-flight
(`design.md:169-182`, D11).

**Refuter-overrule graduation + graduation log.** Verbatim decision rule:

> "a refuter's verdict is itself a claim to verify; the orchestrator forms its own read
> of the crux before opening the refuter's verdict. Decision rule: false premise →
> `REFUTED`; real-but-milder mechanism → `VERIFIED-BY-*` with severity overruled
> downward."
(`design.md:94-99`, D5)

An append-only **graduation log** sits at the top of each FINDINGS file, separate from
in-place field edits (`specs/correctness-audit/spec.md:96-98`). Per `notes.md:25-30`,
the graduation log is **not lint-enforced** — a deliberate D8 scope decision, flagged as
a future `knowledge-drift-review` concern rather than a `knowledge_lint` one.

**Marker-gated dossier lint (`knowledge_lint.py` `_check_audit_dossier`).** Only
dossiers whose `CHARTER.md` contains the literal marker line are checked; markerless or
missing-`CHARTER.md` dossiers are skipped entirely — "load-bearing" because both
downstream repos already have nonconforming `correctness-audit-2026-07/` dirs that would
otherwise fail their live-tree pytest gate on first sync (`design.md:140-152`, D8).
Checks: duplicate finding IDs across FINDINGS files, invalid census dispositions,
graduated findings (non-`LEAD` evidence label) missing `Prior:`/`Class:`.

**Ratchet-routed close-out.** At close, every graduated finding runs OW-2's frozen
Q1/Q2/Q3 triage; qualifying classes land as `knowledge/ratchet-log.md` lines in OW-2's
exact format:

> `- **YYYY-MM-DD** · <kebab-class-slug> · <disposition> — <essence>`

with the five disposition keywords verbatim: `check:<pointer>`, `test:<path>[::<name>]`,
`waiver:review-by YYYY-MM-DD`, `open:since YYYY-MM-DD`, `grandfathered`
(`specs/correctness-audit/spec.md:149-155`). `intentional-by-design`/`doc-only` closes
must carry a ledger disposition (typically `waiver:`) rather than closing as silent
prose; `REFUTED` and one-off (`Class: none (one-off)`) findings get no ledger entry but
their IDs are already triage-referenced.

**Multi-model verify exemption (D12).** Audit waves are explicitly exempt from the
change-lifecycle multi-model verify stack — refutation-graduation IS the audit's
verification:

> "Audit waves ship findings, not production code, so a wave does not run the
> multi-model verify stack — adversarial refutation IS the audit's verification.
> Remediation changes run the normal lifecycle at their tier."
(`proposal.md:70-73`; spec text `specs/correctness-audit/spec.md:161-162`)

---

## 2. Triggering / cadence — OW-5 does NOT define it

OW-5 explicitly does not own when an audit runs. The skill is invoked, not scheduled.
Direct quotes:

- Spec requirement text: "operator-invoked and pull-only — never wired into session
  boot, archive, or any automatic trigger" (`specs/correctness-audit/spec.md:5-8`).
- `tasks.md:17-19`: "a bold-lead cadence callout (**Operator-invoked / pull-only.** —
  never wired into session boot, archive, or any automatic trigger)."
- `design.md` Non-Goals (verbatim): "**Non-Goals** ... OW-6's cadence/trigger machinery;
  OW-1/OW-4 detectors; back-porting downstream dossiers; auto-provisioning per-repo
  config; remediation execution" (`design.md:31-34`).
- `explore-brief.md` Out of scope (verbatim): "OW-6's cadenced composition-audit
  (different trigger and scale; shares only the ratchet close-out seam, which this skill
  establishes)." (`explore-brief.md:106-109`)
- D10 (`design.md:160-167`): the skill "checks for an in-progress dossier... If none
  exists, it walks the operator through instantiating the inlined templates" — i.e.
  invocation-time detection of resume-vs-fresh state, not a scheduling mechanism.
- `notes.md:38-41` (orchestrator routing note): "parked apply blocks nothing — OW-3 has
  no dependency on OW-5, and no backlog item waits on OW-5's apply." No cadence
  commitment is made anywhere in the frozen artifacts.

**Conclusion: OW-5 leaves cadence/triggering entirely to OW-6.** There is no staleness
check, no periodic reminder, no "run every N days" logic in OW-5 at all — the skill is a
protocol standard for a manually-initiated, multi-week program.

---

## 3. Scope boundary OW-5 leaves for OW-6 (quoted)

The single clearest boundary statement is in `explore-brief.md`'s "Out of scope" section:

> "OW-6's cadenced composition-audit (different trigger and scale; shares only the
> ratchet close-out seam, which this skill establishes)."
(`explore-brief.md:107-109`)

This is echoed in `design.md`'s Non-Goals list (`design.md:31-34`, quoted above) and in
two `review-log.md` scope-check entries:

> "**Scope right-sized:** In scope = the skill + dossier lint + propagation wiring. Out
> of scope = OW-6 cadenced audit, OW-1/OW-4 detectors, retroactive remediation,
> back-porting, auto-provisioning — all consistent with the explore-brief."
(`review-log.md:51`)

> "**Scope remains right-sized.** In scope: the skill's protocol contract + dossier
> lint. Out of scope: cadenced audit (OW-6), detectors (OW-1/OW-4), auto-provisioning,
> remediation execution — identical to the frozen design."
(`review-log.md:243`)

**The one explicit shared seam** is OW-2's ratchet close-out interface. From
`research/ratchet-and-verify-contracts.md:101-102` and `:116-117` (quoting OW-2's own
`proposal.md`):

> "**Close-out routing:** the two existing finding close-out points each gain one
> bounded ratchet-triage step — the **archive** skill ... and the **run-audit** skill's
> triage step .... **Future audit skills (OW-5 correctness-audit, OW-6
> composition-audit) route into this same interface; they are not built here.**"

`research/ratchet-and-verify-contracts.md:291-332` (§5 "Integration surface for OW-5")
spells out the reusable vocabulary any future audit skill (named explicitly to include
OW-6) must not reinvent:

- Ledger line format: `- **YYYY-MM-DD** · <kebab-class-slug> · <disposition> — <essence>`
- Disposition keywords: `check:<pointer>`, `test:<path>[::<name>]`,
  `waiver:review-by YYYY-MM-DD`, `open:since YYYY-MM-DD`, `grandfathered`
- The 3-question triage order: Q1 real defect? → Q2 generalizable class? → Q3
  mechanically detectable or test-freezable?
- If a future audit skill ever runs as a verify pass: the verdict-block contract
  (`## Verify Pass — <model>` / `VERDICT:` / `### Defects`).
- The `checks.toml` config-surface precedents (`[knowledge_lint]` table,
  `[checks.<name>]` table) if a config knob is ever needed — "do not invent a third
  config dialect."

This same research file also names OW-6 directly when discussing OW-3's lens menu
(§3/§"What OW-3 says about future lenses"): **"OW-5/OW-6 are not named as lens
candidates anywhere in OW-3's artifacts"** (`research/ratchet-and-verify-contracts.md:249`)
— i.e. neither OW-5 nor a composition-audit is pre-wired into the verify-time lens
mechanism; that door is open but unused.

No other file in `correctness-audit-skill/` mentions `composition`, `jscpd`, `vulture`,
`knowledge-drift-review` as a *dependency* (only as a sibling-skill naming precedent), or
`audit_scope` in a way relevant to OW-6 beyond what's quoted above. `run-audit` is
mentioned extensively only as the sibling skill whose conventions (frontmatter, cadence
callout, wiring-detection precedent) OW-5 borrows — not as a scope boundary.

---

## 4. What OW-5 costs to run (rough weight, for positioning a cheaper OW-6 pass)

OW-5 is explicitly a **heavyweight, multi-week, LLM-judgment program**, not a quick
check. Cost signals from the frozen artifacts:

- **Wave count:** variable per repo/charter (both downstream precedents: extrends ran 4
  subsystem waves + a final spot-check; psc-monitor ran at least 2 waves, W1 and W2, with
  cross-wave duplicates as evidence of scale). OW-5 mandates an additional **Wave 0**
  (instrument-verification-only, no findings) before any wave that produces findings
  (`design.md:154-158`, D9) — so every audit run is "N waves + 1."
- **Slicing/model-pass shape per wave:** work is sliced into bounded, checkpointed
  delegated invocations — "one lead investigation, one census slice sweep, or one
  refutation batch per invocation" — each a full `opencode run` delegation under the
  shared harness, using sanctioned budgets `-k 15 780` (investigation/refutation,
  pro-tier judgment work) or `-k 30 600` (mechanical, flash-tier) (`design.md:105-124`,
  D6). A single wave can therefore comprise many separate delegated invocations (one per
  lead + one per refutation batch + census-sweep slices), not a fixed small number.
- **Every finding requires at least two judgment passes**: the initial investigation
  (pro-tier) and a separate adversarial refutation pass (fresh context, pro-tier) PLUS an
  orchestrator re-check of the refuter's verdict — i.e. graduation is inherently
  ≥3-pass-equivalent per finding, not a single-pass check (`design.md:92-103`, D5).
- **Explicitly exempt from the change-lifecycle verify stack** (D12) specifically
  *because* the refutation-graduation pipeline already duplicates that cost — the
  proposal notes this exemption exists "at the token cost psc's dossier names as its top
  weakness" if it were NOT exempted (`design.md:196-201`).
- **Framing from `explore-brief.md:12-16`**: "the deep LLM correctness audit... is not
  owned by the scaffold" and both downstream repos "hand-rolled the same **multi-week**
  audit program independently." The `proposal.md:5-9` reiterates: "extrends wrote a
  playbook + charter + four waves; psc-monitor then ported that playbook and re-derived
  it by hand."
- Per `ratchet-and-verify-contracts.md` §5, OW-5's own backlog framing (`OUTSTANDING-WORK.md`)
  describes it as "a skill standardizing the wave/charter/census shape" — i.e. a
  standalone audit cycle, structurally analogous to `run-audit`'s cycle but at LLM-judgment
  depth and multi-week duration, not a lightweight periodic sweep.

**Positioning takeaway for OW-6:** OW-5 is the heavyweight end of the audit spectrum
(multi-week, many delegated pro-tier passes per finding, operator-gated waves). A
"cadenced composition-audit" pass should be positioned as something structurally
different in scale/trigger — the explore-brief's own words are "different trigger and
scale" (`explore-brief.md:108`) — not a lighter version of the same wave/charter/census
machinery.

---

## 5. OW-3 verify chain shape (brief)

**Per-tier chain** (`specs/verify-multimodel-gate/spec.md:5-6`, MODIFIED requirement
"Verify runs independent multi-model passes after the self-review"):

- **SMALL:** unchanged — a single REQUIRED `deepseek/deepseek-v4-flash` behavioral
  verifier pass, run *outside* the verify skill (does not invoke the verify skill at
  all).
- **MEDIUM:** self-review (orchestrator, non-delegated) → one `deepseek/deepseek-v4-pro`
  **behavioral** verifier pass. The old third same-checklist flash pass is dropped
  ("the recorded three-repo history showed zero non-trivial defects uniquely caught by a
  same-checklist third pass," per the spec's own prose).
- **COMPLEX:** self-review → `deepseek/deepseek-v4-pro` behavioral pass →
  `deepseek/deepseek-v4-flash` **lens** pass.
- Identical sequence on both platforms (Claude Code and OpenCode).

**Lens-pass contract** (`specs/verify-multimodel-gate/spec.md:84-89`, ADDED requirement
"The COMPLEX third pass runs a lens the behavioral stack lacks"):

> "a **lens pass**: a fixed prompt asking questions the behavioral checklist does not
> ask, rather than a third run of the same behavioral checklist."

v1 lens menu (verbatim, both from the spec and `tasks.md:6`):
- **Test-quality / adversarial-oracle lens (default):** "for each test the change adds
  or modifies, would the test fail if the behavior it claims to cover broke — name the
  assertion that would trip; flag tautological or forced-green assertions, empty test
  bodies, mocks that replace the module under test, discarded return values/flags, and
  unfrozen clocks in tests."
- **Data-scale lens (for data-path-dominant changes):** "which input domains are
  unbounded in production; whether the change fully materializes an unbounded query
  result (e.g. `fetchall()` on an unbounded query); whether the change needs an at-scale
  run or a recorded bounded-domain argument."

Both lens types are diff-scoped (no mandatory full-suite rerun — the pro pass already
did that), share the identical verdict-block contract as the behavioral pass (`## Verify
Pass — <model>` / `VERDICT: READY|NEEDS REVISION` / `### Defects` always present), are
served by the **same single agent file** (`.opencode/agents/openspec-verifier.md`) with
only the invocation prompt and `--model` flag varying, and are a hard gate with the
existing fix→re-run-failed-and-after / 3-cycle-escalation recovery ladder. Lens
selection + one-line rationale is recorded in `review-log.md`. MEDIUM changes MAY opt
into a lens pass when risk warrants it (not mandatory).

**Composition/whole-repo scope is explicitly out of OW-3's scope.** From
`explore-brief.md:130-133` (verbatim "Out of scope" list):

> "OW-1/OW-4 detectors (separate changes; lens prompts here are designed to consume them
> later); SMALL-tier chain; **composition-audit cadence (OW-6)**; the near-duplicate
> explore/propose premise reviews (accepted as low-cost in SYNTHESIS); any change to the
> simplicity/security gates (they are the proven part of the stack)."

OW-3 is scoped strictly to the **per-change** verify pass chain; it makes no claim about
whole-repo or cadenced composition scanning.

---

## 6. Shared infrastructure OW-6 could reuse

- **Lens-prompt convention**: a lens is "a fixed *prompt* (a different checklist), not a
  detector and not a different model or agent" (`ratchet-and-verify-contracts.md:193-195`).
  If OW-6 ever wants a verify-time or audit-time prompt pass, this is the established
  shape: inline fenced-block prompts in the owning skill file, one prompt = one lens,
  selected with a recorded one-line rationale.
- **Verdict-block contract**: `## Verify Pass — <model>` heading, `VERDICT: READY` /
  `VERDICT: NEEDS REVISION`, `### Defects` section always present (`- None` when clean).
  Explicitly "extensible" per OW-3's own success criteria: "Lens prompts inline,
  canonical, and cite-able by OW-1/OW-4 when their detectors land"
  (`verify-stack-redirect/explore-brief.md:162`) — but OW-3 does **not** commit a third
  lens slot to a correctness-audit- or composition-audit-shaped prompt
  (`ratchet-and-verify-contracts.md:249-253`): "the v1 lens menu is exactly two entries
  (test-quality, data-scale)... does not commit to a third lens slot."
- **Two integration points named for a future audit skill** (§5 of
  `ratchet-and-verify-contracts.md`, written with OW-5 in mind but structurally identical
  for OW-6): (1) extend the verify-phase lens menu with a third fixed prompt, sharing the
  verdict-block contract, OR (2) run as a standalone cycle whose close-out plugs directly
  into OW-2's `close-out-gates-route-findings-into-the-ledger` interface — same
  Q1/Q2/Q3 triage, same ledger line format. Plug-in point 2 is called out as primary for
  OW-5 based on backlog framing; the same reasoning likely applies to OW-6 unless OW-6 is
  explicitly designed as a verify-time pass.
- **Delegation harness budgets**: sanctioned timeout pairs `-k 15 780` (judgment/pro-tier)
  and `-k 30 600` (mechanical/flash-tier) are the only pairs `scaffold_lint.py`'s
  budget-agreement check accepts; both OW-5 and OW-3 reuse these exactly, adding no new
  row to `.claude/skills/_shared/delegation-harness.md`. OW-6 should plan to reuse one of
  these two pairs rather than requesting a new budget row.
- **`checks.toml` config precedents**: `[knowledge_lint]` table (e.g.
  `ratchet_open_max_age_days`) and `[checks.<name>]` table (`enabled`, `paths`) are the
  two established config-surface shapes; OW-6 should reuse one rather than invent a third
  (`ratchet-and-verify-contracts.md:329-332`).

---

## Bottom line for OW-6's designer

1. **Cadence is a clean gap, not a conflict.** OW-5 explicitly refuses to define
   trigger/cadence machinery ("OW-6's cadence/trigger machinery" is a named Non-Goal) and
   is itself pull-only/operator-invoked with zero scheduling logic. OW-6 owns cadence
   entirely — there is nothing to reconcile or override.
2. **The only contract OW-6 must not contradict from OW-3**: the verify-multimodel-gate
   chain is tier-keyed and fixed per change (SMALL 1 pass outside the skill; MEDIUM
   self+pro; COMPLEX self+pro+lens) with the lens pass a *prompt*, not a detector, served
   by the single existing `openspec-verifier` agent file with a shared verdict-block
   contract. OW-6, being explicitly out-of-scope for OW-3 ("composition-audit cadence
   (OW-6)" is a named Out-of-scope item) and not a named lens candidate, must not fold its
   whole-repo/cadenced pass into the per-change verify chain as if OW-3 already
   accommodates it — if OW-6 wants a verify-phase presence at all, it would need to be
   proposed as a new lens-menu entry (plug-in point 1), a change OW-3 explicitly declined
   to make and did not reserve space for. OW-6 is otherwise free to define its own
   standalone cadence/trigger and its own cost profile, so long as any findings it
   produces that qualify for the ratchet route through OW-2's identical
   triage/ledger-format interface that OW-5 also uses (shared seam, not a conflict).
