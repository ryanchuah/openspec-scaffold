# Tasks — single-source-rules (C2 / "W7")

MEDIUM change. **Apply-phase work ONLY** — precise golden-source edits plus one doc-content
addition. Every edit is **extraction, not redesign**: the established rule text is preserved
**verbatim** at its chosen canonical home (golden-source rule, `ai-docs/workflow-lessons.md` §2);
at every other site only the per-context specifics + a citation remain. No behavior changes.

**HARD GUARD — do NOT touch operational config.** `--model deepseek/deepseek-v4-*` invocation
lines inside skill code blocks, and `model:` fields in agent frontmatter, are *executable config*,
not prose restatements. They stay byte-for-byte. Only **prose that re-explains a rule** is collapsed
to a citation.

Canonical homes, the per-site edit intent, the preserve-verbatim guardrails, and the acceptance
criteria are in **`notes.md`** (read it before applying). Rule-family groups (2–6) are independent —
delegate apply **one group at a time** (avoid the monolithic-dispatch timeout from W2/dedup-scaffold).
The per-section-summary cleanup in `open-questions.md` is **archive-phase** (see `notes.md`), NOT a
task here.

## 1. Convention + registry — the self-enforcing mechanism (`ai-docs/workflow-lessons.md`)

- [x] 1.1 In `ai-docs/workflow-lessons.md` §2 "Golden-source edit rules", add a new numbered rule: each single-sourced rule has ONE canonical home; cite it, never re-expand the rule text at another site (re-expansion is what `sync_scaffold.py` would then propagate as drift to all three repos).
- [x] 1.2 In `ai-docs/workflow-lessons.md` §2, add a **Single-source registry** table mapping each of the five rules below to its canonical home (the five rows in `notes.md` § "Canonical-home registry"), so a future scaffold editor has one place to find every home.

## 2. Rule 1 — "tasks.md = apply-phase only" → home: `openspec/config.yaml` `rules.tasks`

- [x] 2.1 Add a `# CANONICAL: tasks-md-apply-only — cite, do not restate` YAML comment on the line directly above the `tasks:` key in `openspec/config.yaml` (a `#` comment OUTSIDE the injected string, so it does not leak into artifact prompts).
- [x] 2.2 In `.claude/skills/openspec-propose/SKILL.md`, replace the near-verbatim restatement of the full "tasks.md contains ONLY apply-phase work …" rule with a one-line citation to `openspec/config.yaml` `rules.tasks`. (The restatement is byte-near-identical to the config.yaml rule — there is no propose-specific wording to preserve.)
- [x] 2.3 In `.claude/skills/openspec-verify-change/SKILL.md` and `.claude/skills/openspec-archive-change/SKILL.md`, leave the *interpretive* use ("an incomplete task means real implementation work remains, because tasks.md is apply-only") in place but append "(canonical: `openspec/config.yaml` `rules.tasks`)" so the convention is visible at the citation site.

## 3. Rule 2 — model-assignment matrix → home: `AGENTS.md` `## Roles`

- [x] 3.1 Add an HTML comment marker `<!-- CANONICAL: model-assignment-matrix — cite, do not restate -->` at the top of `AGENTS.md` `## Roles`.
- [x] 3.2 In `AGENTS.md` `## Change tiers`, keep the tier→process text and the per-tier model *names* (they are intrinsic to the tier rule). Confirm it does not re-explain the "deepseek-flash via `opencode run`, Sonnet subagent as fallback" delegation ladder — the tail (line ~160) already cites the apply skill for the ladder; if any re-explanation remains, collapse it to that cite + a `## Roles` cite. Likely a near no-op.
- [x] 3.3 In `openspec/config.yaml` `rules.tasks`, keep the delegation instruction and the model name (prompt-injected; the executor needs it), but reduce any re-explanation of the fallback rationale to "(see `AGENTS.md` `## Roles`)".
- [x] 3.4 In the apply / verify / archive / propose skills, where **prose** re-explains the role→model assignment or the fallback rationale, reduce it to a citation of `AGENTS.md` `## Roles` + the per-phase specifics. **Preserve every `--model …` code-block invocation and every frontmatter `model:` field verbatim** (guard above).

## 4. Rule 3 — "never record test/doc/row counts" → home: `AGENTS.md` (the "Tests green before any commit" bullet)

- [x] 4.1 Add `<!-- CANONICAL: never-record-counts — cite, do not restate -->` at the "Never record test, doc, or row counts …" sentence in `AGENTS.md`.
- [x] 4.2 Confirm the existing citations already point home (verify skill, archive skill, and both archive-executor bodies say "see `AGENTS.md`"); add the same "(see `AGENTS.md`)" cite to any site found restating the rule without one. `openspec/config.yaml` `context:` keeps its prompt-injected short form (load-bearing for executors that do not load `AGENTS.md`) — leave its wording, no marker inside the injected string.

## 5. Rule 4 — mock-encoded-idealized-API war-story → home: apply-executor body

- [x] 5.1 Confirm the full mock-contract rule + war-story stays in `.claude/agents/apply-executor.md` AND `.opencode/agents/apply-executor.md` (byte-identical per the `test_executor_body_agreement.py` guard); add `<!-- CANONICAL: mock-api-war-story — cite, do not restate -->` to both, identically (so the guard stays green).
- [x] 5.2 In `.claude/skills/openspec-verify-change/SKILL.md`, keep the verifier-specific action ("run the change's opt-in live test and inspect a real response") but replace the re-told narrative ("an integration shipped with wrong sort semantics and a 500-ing backfill …") with a one-line reference to the apply-executor mock-contract rule.
- [x] 5.3 In `.claude/skills/openspec-propose/SKILL.md`, **LEAVE the live-probe story intact** (the "a constructor kwarg was assumed available … crashed on the first request" example, ~line 79). It is a **distinct companion** illustration of a *different* facet — the live-probe mandate (constructing a client is not proof; failures defer to request time) — NOT a retelling of the apply-executor mock-contract story, so it is not a Rule-4 duplicate. Optionally add a one-line "see also the apply-executor mock-contract rule for the companion mock-side hazard" cross-ref. **Do not collapse it.**

## 6. Rule 5 — web-research convention → home: `ai-docs/research-fetch-convention.md`

- [x] 6.1 Add `<!-- CANONICAL: web-research-convention — cite, do not restate -->` at the top of `ai-docs/research-fetch-convention.md`.
- [x] 6.2 In `AGENTS.md` `## Web research convention`, replace the full restatement of rules (a)–(d) with a tight one/two-line summary that keeps the single load-bearing guardrail — (d) "never call the built-in `WebSearch` tool from the main thread; route all web research through subagents using `scripts/fetch_clean.py`" — and cites `ai-docs/research-fetch-convention.md` for the full four-rule convention.
- [x] 6.3 In `openspec/config.yaml` `context:` "Web research:" line, keep the one-liner (prompt-injected) and append "(full convention: `ai-docs/research-fetch-convention.md`)".

## 7. Post-edit self-checks (apply-executor runs before reporting)

- [x] 7.1 `git diff --stat` touches only: `AGENTS.md`, `openspec/config.yaml`, `ai-docs/workflow-lessons.md`, `ai-docs/research-fetch-convention.md`, the four named skills, and the two apply-executor bodies. No other file changed.
- [x] 7.2 No operational config changed. Run `git diff -- .claude .opencode | grep -E '^[-+].*--model|^[-+]model:'` as a **conservative tripwire** — it may also catch a prose citation that mentions `--model`. Manually adjudicate each hit: a changed line inside a fenced code block, or a frontmatter `model:` field, is a **DEFECT** (revert it); a prose citation that merely mentions `--model` is allowed. The bar is zero changes to code-block invocations and frontmatter `model:` fields.
- [x] 7.3 `.venv`-free repo: run the existing guards that do not need a venv — `python scripts/test_executor_body_agreement.py` (apply-executor pair still byte-identical after 5.1) and `openspec validate --all` both pass.
- [x] 7.4 Info-loss backstop for the citation collapses: for each rule-family, grep-confirm the substantive rule text still appears **verbatim at its canonical home** after the edits — the "tasks.md contains ONLY apply-phase" sentence in `config.yaml` `rules.tasks`; the role→model prose in `AGENTS.md` `## Roles`; the "never record … counts" sentence in `AGENTS.md`; the mock-contract war-story in both apply-executor bodies; the four web-research rules in `ai-docs/research-fetch-convention.md`. No home lost its rule text.
