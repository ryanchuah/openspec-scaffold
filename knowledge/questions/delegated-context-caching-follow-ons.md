# delegated-context-caching follow-ons (OW-8, shipped 2026-07-14)

Full decision → `knowledge/decisions/INDEX.md` (`delegated-context-caching`). Full evidence → the
archived change's `notes.md` (`openspec/changes/archive/2026-07-14-delegated-context-caching/notes.md`).

## (a) B revisit trigger — AGENTS.md-injection strip, currently blocked

`OPENCODE_DISABLE_PROJECT_CONFIG` was proven (binary `strings` + empirical `opencode agent list`,
opencode v1.17.18) to couple stripping the AGENTS.md system-prompt injection with disabling
`.opencode/agents/` discovery entirely — setting it would silently swap `--agent apply-executor`
for a built-in default agent (right model, wrong role). No per-agent instruction-scoping opt-out
exists in the v1.17.18 schema.

Re-attempt B only if:
- opencode adds a targeted per-agent instruction-scoping mechanism (a frontmatter field or flag
  that disables project-instruction injection WITHOUT disabling agent discovery), or
- AGENTS.md is deliberately split so its injected footprint shrinks (separate, larger work with its
  own downstream blast radius).

Re-test the coupling on any opencode major-version bump regardless — evidence cited:
`OPENCODE_DISABLE_PROJECT_CONFIG=1 opencode agent list` → 0 project agents listed (only built-ins),
tested on v1.17.18.

## (b) C-drop lint idea — premise marker drift-prevention

"Single-source the triplicated premise prompt" was dropped as over-engineering (only ~7 words —
`### Premise Verdict block (PREMISE: AGREE|DISSENT)` — are byte-identical across the 3 call sites;
verdict format and invocation skeleton are already single-sourced elsewhere). If drift-prevention
for those markers is ever wanted, the better shape is a deterministic lint (cf.
`model-id-agreement` in `scaffold_lint.py`) asserting every premise call-site uses the sanctioned
marker spellings, not a refactor/extraction. Low priority — not folded into OW-8.
