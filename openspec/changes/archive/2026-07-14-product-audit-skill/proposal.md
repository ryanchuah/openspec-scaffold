<!-- Tier: COMPLEX — greenfield capability + new scaffold-managed skill + a new durable cross-repo
convention (claims ledger) + a guarded lint detector. Parity with its sibling OW-5
(`correctness-audit`, shipped COMPLEX). COMPLEX requires proposal + design + specs + tasks. -->

## Why

Every audit class the scaffold owns is **code-facing** (object = code, oracle = spec): correctness,
test-quality, composition, workflow-efficiency, knowledge-drift, plus the per-repo security sibling.
For a repo that ships a **product**, an entire defect class is structurally invisible to that
portfolio — defects whose object is the **promise surface** (pricing/landing/README/public-docs copy)
or the **business thesis** (pricing/ICP/GTM/regulatory-window/competitors), and whose oracle is the
code or the market. Evidence (psc-monitor CG9, `psc-strategy-pressure-test-2026-07-12.md`): a
launch-gate defect — a pricing page selling three Pro differentiators of which **two did not exist and
the third was unreachable** — survived **three chartered code audits**; the business thesis had **zero**
adversarial review while the code had three, and when finally pressure-tested (24 blind attacks) it
yielded a new launch gate, an unknown live competitor, a mis-sourced regulatory claim in a durable
reference, and six ratified operator decisions. The method is proven and cheap (one session; the
blind-diff core validated n=3, including this first non-code domain).

## What Changes

- **New operator-invoked, pull-only `product-audit` skill** — the promise-surface / business-thesis
  sibling of `correctness-audit`. Standardizes the protocol: blind attack-list committed *before*
  evidence → **five-lane evidence fan-out** (implementation-as-sold · cost/critical-path ·
  repo+git-history+GTM sweep · live-web regulatory · live-web competitive; web lanes ride the existing
  research convention) → **per-attack disposition diff** (CONFIRMED / PARTIAL / SURVIVED-BY-THESIS /
  OPEN, survived attacks recorded not dropped) → **operator ratification menu** (findings surfaced as
  decisions to ratify, never auto-decided) → machine-discriminable `PRODUCT: CLEAN | FINDINGS-ROUTED |
  ESCALATE` verdict. Never wired into boot/AGENTS.md/any auto-run; cadence is pre-launch gate +
  strategy-reference watch-list expiry, **not** a recurring ceremony.
- **A single-session ceremony, not a multi-wave durable-dossier audit.** Unlike `correctness-audit`
  (multi-wave, resumable dossier with an in-progress *liveness* obligation), `product-audit` runs in
  one bounded session like `composition-audit`. **Open question for design (raised by review 🔴-3):**
  confirm product-audit therefore carries **no** in-progress Active-questions liveness obligation and
  needs no liveness lint — and justify that asymmetry explicitly in design, rather than inheriting the
  correctness-audit liveness machinery by default. The durable artifact it leaves (the claims ledger)
  is guarded by a *staleness* lint (below), which is a different obligation from *liveness*.
- **Ships the claims-ledger convention** the skill owns: every externally visible promise → delivering
  code surface → the check that proves it, carried in a per-repo ledger file with a `format:
  product-audit/v1` marker. **Open for design:** the ledger's location, its exact marker, and — so a
  lint can operate — **how the ledger declares the promise-surface files it covers** (an in-ledger
  manifest/glob vs. a fixed convention). See the lint bullet.
- **Operationalizes OW-15's carried-forward classes 9–12**, which `correctness-audit` explicitly hands
  off to this skill: copy↔capability conformance (claims ledger), entitlement-state **reachability**
  (not behavior), severity-taxonomy completeness (a slot for external-promise/trust/legal harm or a
  named exclusion), source-class labeling for durable web-sourced claims (official / secondary /
  vendor-speculation). Adds a **reciprocal awareness pointer** back to `correctness-audit` (a
  built-but-unsold finding may warrant a correctness-audit of the undisclosed feature).
- **New guarded `knowledge_lint` detector** (proposed check name `claims-ledger-staleness`, following
  the `audit-dossier-format` / `audit-liveness` / `post-close-ledger-format` naming convention): a
  covered promise-surface file newer than the claims ledger → staleness finding. Marker-gated on
  `format: product-audit/v1` so this repo and un-adopted downstream repos lint clean (mirrors the three
  existing audit-dossier detectors; the live-tree gate requires the guard). **Open for design (review
  🔴-2):** the detector needs a discovery mechanism — the marker gate prevents false-flagging
  un-adopted repos but does not tell the linter *which files* constitute the covered promise surface;
  design SHALL specify that discovery mechanism (e.g. an in-ledger file manifest) or the detector is
  unimplementable.
- **Findings route into the existing finding-closure ratchet** on close, using its three-question
  triage. **Tension flagged, not resolved here (review 🔴-1; direction-gate 🟡-1 said "do not assert
  compatibility"):** the ratchet's five dispositions were designed for code defects, and a
  promise-surface finding ("copy claims X, code lacks X") may not map cleanly. Design SHALL decide
  whether the existing dispositions suffice (working hypothesis: the claims-ledger *proving-check* row
  serves as the `check:` disposition for copy↔code findings, and pure business-thesis findings take
  `waiver:review-by` with the operator ratification recorded) **or** whether a small leaf carve-out is
  needed — and only then state the mapping. No claim of "no new close-out machinery" is made at
  proposal altitude.

## Capabilities

### New Capabilities
- `product-audit`: the operator-invoked promise-surface / business-thesis audit protocol — blind
  attack-list → five-lane evidence fan-out → per-attack disposition diff (CONFIRMED / PARTIAL /
  SURVIVED-BY-THESIS / OPEN) → operator ratification menu → `PRODUCT:` verdict; the claims-ledger
  convention (promise → delivering surface → proving check); source-class labeling and
  severity-taxonomy-completeness prompts; and close-out routing into the finding-closure ratchet.

### Modified Capabilities
- `knowledge-lint`: add one guarded detector requirement (`claims-ledger-staleness`) validating that a
  `product-audit/v1`-marked claims ledger is not older than the promise-surface files it declares as
  covered; marker-gated so un-adopted repos stay clean.

## Impact

- **New files:** `.claude/skills/product-audit/SKILL.md` (scaffold-managed); `openspec/specs/product-audit/spec.md`.
- **Modified files:** `scripts/knowledge_lint.py` (+1 guarded detector) and `scripts/test_knowledge_lint.py`
  (detector test triad + guard-skip tests); `scripts/scaffold_manifest.txt` (+1 SKILL line);
  `scripts/scaffold_lint.py` `_NON_OPENSPEC_SKILL_TOKENS` (+`product-audit`). This does **not** avert a
  lint failure — `dangling-skill-refs` only *collects* a non-openspec token if it is in this set, so
  omitting `product-audit` leaves prose mentions of it simply un-scanned, not flagged. Adding it is a
  **consistency task** per the set's own "keep in step with actual non-openspec skill dirs" comment: it
  makes the existing cross-reference from `correctness-audit/SKILL.md` (which names `product-audit` as
  the classes-9–12 owner) *actively validated* against the real skill dir.
- **Cross-repo:** the SKILL propagates byte-identical downstream via `sync_scaffold.py` (operator-gated,
  deferred); capability specs are golden-source-only (never synced). Both new lint behaviors are
  guarded — no new downstream lint failures on first sync.
- **Design considerations carried from the direction gate:** a light operator **dual-literacy** note
  (the operator needs both business-thesis and code-surface literacy — parity with the correctness-audit
  charter walk).
- **Non-scope:** no product code; OW-12 (archive mechanization) and OW-11-residual (skill de-bloat) not
  folded (separate concerns); the OW-6 revealed-vs-stated-priority lens is routed to composition-audit,
  not built here; downstream propagation and push are operator-gated.
