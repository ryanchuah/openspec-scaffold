# Synthesis — openspec-scaffold vs. industry standards (2026-06-13)

Orchestrator synthesis of the four research-subagent findings. **Read-only research phase — nothing
in the scaffold has been edited.** Detail lives in the per-bucket files; this is the decision-grade
digest with my (principal-engineer) own judgment layered on top, *not* a passthrough of subagent claims.

Detail files: [`A-spec-driven-change-mgmt.md`](A-spec-driven-change-mgmt.md) ·
[`B-orchestration-delegation.md`](B-orchestration-delegation.md) ·
[`C-agent-config-interop.md`](C-agent-config-interop.md) ·
[`D-knowledge-memory-verification.md`](D-knowledge-memory-verification.md)

## Headline

The scaffold is **not behind** the industry — on its core quality gates it is **ahead**. All four
subagents independently converged on this: pre-implementation spec review by a *separate model*,
behavioral verification beyond tests, trust-gated fast-track, and archive-as-fresh-context have **no
equivalent** in the surveyed commercial tools (Spec Kit, Kiro, CodeRabbit, Greptile, BMAD). So this is
a **polish + selective-adoption** exercise, not a catch-up.

Consequently the single largest *class* of recommendation is **"name / document / teach behavior the
scaffold already does well"** — low-risk, high-clarity, makes the scaffold self-documenting and stops
future agents/maintainers from re-litigating or accidentally breaking deliberate choices.

> Framing vs. the golden-source edit rules: the prior session's "established-rules-only" applied to the
> *generalization* phase. This phase is *explicitly* "compare to industry & adopt" — so industry-sourced
> additions are in scope, but I have kept every item below **source-traceable** and **constraint-checked**
> (agent-neutral, no native-memory dependence, autonomy stays opt-in, respect prior decisions).

---

## ✅ VERIFIED — both high-stakes claims RESOLVED (no scaffold defect)

Verification done 2026-06-13 (subagent + `gh` + local opencode-bundle inspection; detail in
[`VERIFY-opencode-claims.md`](VERIFY-opencode-claims.md)). **Both claims dissolved — the golden source
is NOT broken for its OpenCode/DeepSeek half.** This is precisely why we verified instead of acting.

1. **B / OQ-5 — DeepSeek `reasoning_content` multi-turn fallback → REAL BUG, but FIXED; operator not
   exposed.** The 7 cited `sst/opencode` issues exist but are all **CLOSED**. Fix = PR **#24146**
   ("preserve empty reasoning_content for DeepSeek V4 thinking mode"), MERGED 2026-04-24, shipped in
   **v1.14.24** — below the installed **1.17.4**. Operator runs the built-in `deepseek` provider with
   no custom block; the fix covers that config. The `"Falling back to default agent"` assert
   (propose:138 / apply:149 / archive:163) stays as cheap belt-and-suspenders. **No fix needed.**
2. **C / R2 — OpenCode can't see `.claude/skills/` → REFUTED.** OpenCode added skill discovery in
   **v1.16.0** ("skill discovery and file-based agent loading"); the installed `~/.opencode/bin/opencode`
   binary contains the literal `claude/skills/` scan path and the `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS`
   gate, which is **unset** (default = load). **OpenCode loads the scaffold's 7 skills today.** The
   "put skills in `.opencode/skills/`" convention was a hallucination.

**Two verified, low-risk improvements fell out of this** (fold into Tier 1):
- **T1-9 — Harness-neutral skill wording.** AGENTS.md:81 says "via the **Skill** tool" (Claude's
  PascalCase harness term); under OpenCode the mechanism is the model-callable lowercase `skill` tool.
  Reword harness-neutrally ("via your harness's skill tool"). Source: opencode.ai/docs/skills + bundle
  evidence. Agent-neutral, zero risk.
- **T1-10 — Document the cross-load in `decisions.md`.** Record WHY skills live only under
  `.claude/skills/` (OpenCode ≥1.16 auto-discovers `.claude/skills/**/SKILL.md`, gated by
  `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS`=false) — so a future agent never duplicates them into
  `.opencode/skills/` or assumes OpenCode is blind to them. Same class as T1-2/T1-5.

Also treat all *quantitative* claims (memory-tool "39% / 84%", CodeRabbit "2M+ repos", Greptile "82%")
as **per-source, unverified** — fine as motivation, not as load-bearing facts.

---

## Recommendations — consolidated, de-duplicated, prioritized

### Tier 1 — Make the scaffold self-documenting (low risk, high clarity, all constraint-compatible)
| # | Rec | Source | Conf | Note |
|---|-----|--------|------|------|
| T1-1 | Rename EXIT-file "sentinel" → **liveness sentinel**; promote disk end-state (`tasks.md` all `[x]`) as the *primary* completion signal in apply/archive skills | B-R1 (Anthropic: evaluate end-state, not turns) | High | Conceptual correctness of last session's own backport |
| T1-2 | Seed `decisions.md` with the **no-native-memory decision + rationale + cost** | D-R4 | High | Stops re-litigation; ties to known extrends/psc-monitor memory inconsistency |
| T1-3 | Name **EARS** notation in the spec-delta template/config (the WHEN/THEN format already *is* EARS) | A-R1 (Spec Kit, Kiro) | High | Teachability; zero behavioral change |
| T1-4 | Name the **separate-verifier / "adversarial agent"** pattern in the verify skill (why verify isn't delegated) | A-R4 | High | One paragraph; self-documents a deliberate rule |
| T1-5 | One-line `decisions.md` note: **hook-absence is deliberate** (OpenCode has no hook equivalent; agent-neutral) | C-R5 | High | Prevents operator confusion |
| T1-6 | Promote **fold-fix** to a cross-cutting AGENTS.md rule (today only in apply skill, for large changes) | B-R4 | High | Already partially present; needs promotion |
| T1-7 | Add the **"when NOT to delegate"** guardrail to AGENTS.md (dependency-laden work degrades under fan-out) | B-R5 | Med-High | Prevents a future maintainer adding harmful parallelism |
| T1-8 | Name the AGENTS.md hard-constraints block as the project **"constitution"** in the onboard skill | A-R5 (Spec Kit) | Med | Cold-start discoverability |

### Tier 2 — Small new guidance/templates (low–medium risk, good value, constraint-compatible)
| # | Rec | Source | Conf | Note |
|---|-----|--------|------|------|
| T2-1 | Add a **retry tight-brief template** to the apply skill (exact files, verified facts front-loaded, no re-exploration) | B-R2 | High | Skill says "tight brief" but gives none |
| T2-2 | Define the **executor brief as a named structure** (required fields) | B-R3 (OpenAI Agents SDK typed handoffs) | Med | Makes the convention explicit |
| T2-3 | AGENTS.md rule: **"write non-obvious choices to `decisions.md` at archive"** + seed one example | D-R2 | High | Fixes the perpetually-empty decisions.md |
| T2-4 | Add a **context-budget trigger** heuristic to AGENTS.md (when to delegate to a fresh sub-agent) | D-R1 (Anthropic context-eng) | Med | Compaction lever for harness-neutral use |
| T2-5 | Add a **session-resume staleness check** (`git log -5` + verify STATUS.md current before proceeding) | D-R3 | Med | Guards "stale context injection" |
| T2-6 | Add an explicit **change-tier classification** step in propose (nominal in normal flow; fast-track still gated) | A-R3 | Med | Right-sizing; must NOT relax gates (constraint #4) |

### Tier 3 — Optional / needs operator judgment (more surface, external deps, or marginal)
| # | Rec | Source | Conf | My lean |
|---|-----|--------|------|---------|
| T3-1 | Commented `.claude/settings.json` template stub | C-R1 | Med | Claude-only surface — partial constraint-#1 tension; only if clearly labelled |
| T3-2 | Commented **MCP** stanza example in README (cross-tool extension point) | C-R3 (MCP near-universal) | Med | Reasonable as a documented extension point; don't bake project config |
| T3-3 | Optional **external review hook** (CodeRabbit/Greptile) as `<FILL:>` in verify skill | D-R5 | Med | OK as opt-in placeholder per project type |
| T3-4 | Add a `/clarify` pre-design step | A-R2 (Spec Kit) | Low-Med | Reviewer already covers some; bloat risk — lean *defer* |
| T3-5 | Context-health field in notes.md (6th field) | D-R6 | Low | **I'd drop this** — ceremony with marginal value |

---

## Where the scaffold is already ahead (don't "fix" these)
- **Pre-implementation spec review by a separate model** (@openspec-reviewer) — no commercial analog; all others are post-code PR review.
- **Behavioral verification beyond tests** (eyeball real output + live external-API smoke; explicit "green mocks can encode wrong contracts").
- **Trust-gated fast-track** — matches Anthropic's own empirical finding (experienced users auto-approve *and* interrupt more).
- **Archive-as-fresh-context sub-agent** (write-deferred reconciliation from the compact change dir, not the transcript).
- **Hard phase gates + explicit approval** — a deliberate divergence from upstream OpenSpec's "no gates"; correct for multi-session production.
- **Sequential single-writer executor + anti-pgrep + baseline-restore-before-retry** — more operationally rigorous than public guidance.

## Open decisions for the operator
1. **No-native-memory rule (constraint #2):** validated as correct for a dual-harness template, but the
   cost is real and *widening* as Anthropic invests in the memory tool. Decision: keep file-only +
   document the trade-off (T1-2), or revisit if the dual-harness requirement ever relaxes. Connects to
   the pending extrends/psc-monitor inconsistency (they use `~/.claude` memory despite forbidding it).
2. **Scope of this pass:** Tier 1 only? Tier 1+2? Include Tier 3 picks? (My lean: verify the two ⚠️
   claims → apply Tier 1 → discuss Tier 2 → cherry-pick Tier 3.)
3. **Verification pass** for the two ⚠️ claims before any related edit — yes/no.
