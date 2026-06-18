# add-status-lint — notes

**Tier:** MEDIUM (operator-confirmed). Propose emits `tasks.md` + this `notes.md`; reviewed by deepseek-v4-pro before freeze; applied by deepseek-v4-flash; verified (self → pro → flash) by the primary.

## Context / why
This change mechanizes the **forward-only** state-file bounds that `lean-boot-context` (archived 2026-06-18) shipped as prose rules in `AGENTS.md §"State, write discipline, and the archive-as-handoff rule"`. That change's own `notes.md` flagged the open gap verbatim: *"Enforcement is untested against a live archive … watch the next real archive to confirm the archive-executor actually applies the ≤150-word STATUS budget"* and *"extrends STATUS remaining entries unchecked."* A later external review of `extrends` independently surfaced the same drift — its three retained STATUS entries measure **324 / 280 / 289** words against the ≤150 budget — and recommended a lint script. `add-status-lint` converts that remembered discipline into an automated gate, run at archive time, in the scaffold and propagated to both downstream repos.

## Scope (this change)
Scaffold-authored, propagated:
- `scripts/status_lint.py` — stdlib linter for the mechanical STATUS.md + decisions.md invariants.
- `scripts/test_status_lint.py` — stdlib unittest coverage.
- Archive-flow wiring: a `#### 3d. Lint the reconciled state files` self-check in BOTH archive-executor bodies, and a primary "lint before committing" gate in the archive SKILL.
- Manifest + propagation to `psc-monitor` and `extrends` (both `--check` + `--check-refs` green).

## Non-goals / deliberate exclusions
1. **No per-commit PreToolUse hook.** STATUS.md/decisions.md are reconciled only at archive, so the linter is wired into the archive flow, not a blocking hook on every commit (proportionate — avoids firing on unrelated commits). Exit 0/2 keeps a future hook possible.
2. **No open-questions.md semantic check.** "Is this bullet BLOCKING?" is a judgment call, not a mechanical invariant; the horizon-split rule stays archive-executor-enforced. (Possible v2.)
3. **No AGENTS.md edit.** The invariants already live in `§"State, write discipline…"`; the linter enforces them and the SKILL/executor reference the tool. Keeps the span-merge propagation surface minimal.
4. **No downstream content trimming (= Phase B).** This change ships the *tool*; it does NOT retroactively trim the existing over-budget entries in extrends (324/280/289) or the scaffold's own `split-open-questions` entry (~316w). Those are forward-only debt; trimming them is summarization (judgment-heavy, not flash-safe) and is the **Phase B** follow-on below.
5. **decisions.md enforcement is scoped to entries dated on/after `--since` (default `2026-06-18`, the decisions-entry rule's adoption date)** — honors "no retroactive backfill": legacy entries (which carry a `**Date:**` but predate the `**Status:**` requirement) and the unparseable placeholder template are skipped. A brand-new change-record entry that omits its Date entirely is not caught (acceptable v1 gap; the archive-executor template supplies the field). *(This scoping was corrected from the original "any entry with a Date" spec during apply — see As-built deviations.)*

## Design decisions
- **Name `status_lint.py`, not `_status_lint_oneoff.py`.** It is a permanent, re-runnable gate, so it follows the `scaffold_check.py` / `sync_scaffold.py` naming, not the `_*_oneoff.py` convention (which is for disposable one-shot analyses). (The external review's suggested `_oneoff` name was wrong for a permanent gate.)
- **Reproducible word definition:** word count = `len(re.findall(r"\S+", body))` over the section body after stripping fenced code blocks and excluding the heading line. This reproduces the measured 324/280/289 (extrends) and 141/148/316 (scaffold) counts.
- **Exempt-heading allowlist (exact match):** preamble + an **exact** normalized-heading match against `{current state, immediate next action, done, pointers}`. AGENTS.md's prose names only the preamble and `## Immediate next action`, but real STATUS.md files (scaffold + extrends) also use `## Current state`, `## Done`, and `## Pointers` as structural sections — so those are exempted too. Exact match (not prefix) is deliberate: a change-entry whose title merely *starts with* one of these words (e.g. `## Done-archive migration`) must still count. Everything else `##` is a change-entry (so `## Operations …` correctly counts — it is the rule's named example).
- **Change-record regex matches AGENTS.md exactly:** the decisions.md ≤300-word cap fires only on `^(fix|add|tune)-` headings — exactly the `fix-*`/`add-*`/`tune-*` set the rule names, not a broadened change-verb set (broadening would be a rule change, made in AGENTS.md first per single-sourcing).
- **`--since` date cutoff for decisions.md (default 2026-06-18):** the only robust discriminator between a legacy entry and a new one is its date — the `**Date:**` field itself predates the `**Status:**` requirement, so "has a Date" cannot mean "post-rule." Enforcing only on Date ≥ adoption-date is the minimal correct way to honor "no retroactive backfill." All three repos adopted the rule on 2026-06-18, so one baked default is correct everywhere; `--since` allows override.
- **Exit 0/2** matches `scaffold_check.py` / the PreToolUse convention, so the linter can be wired into a hook later if ever wanted.

## Acceptance criteria
1. `python scripts/status_lint.py <clean-repo>` exits 0; a repo with a 4th change-entry, a >150-word entry, or a dated decisions entry missing `**Status:**` / over 300 words exits 2 with a specific message naming the heading + measured number.
2. `scripts/test_status_lint.py` passes (stdlib unittest), covering cap-count, word-budget (incl. code-fence exclusion + the exactly-150 boundary), `## Operations` counting, decisions Date/Status + 300-cap, legacy-entry skip, graceful file-absence, and the 0/2 exit codes.
3. `test_executor_body_agreement.py` passes after the `#### 3d` edit (both executor bodies stay byte-identical).
4. Both downstream repos: `sync_scaffold.py --check` and `--check-refs` green; `test_sync_scaffold.py`, `test_convergence.py` pass.
5. The linter, run against the scaffold's own `STATUS.md`, correctly **detects** the existing ~316-word `split-open-questions` entry as a C2 violation (proves the detector works on real data) — verified by the primary at verify. The entry itself is NOT trimmed in this change (Phase B).

## Phase B (follow-on, after this ships — NOT in this change)
Once the linter exists, the primary (with the archive-executor on the pro tier where summarization is needed) uses it to drive the one-time cleanup the review called for:
- **extrends:** trim the 3 retained STATUS entries (324/280/289) to ≤150-word headlines (surplus → `status-log.md` verbatim); trim the 1,821-word `## Immediate next action` (the read-floor culprit — DONE work-queue / pending items → `status-log.md` / `done-archive.md`); relocate `ai-docs/improvement-roadmap.md` → `plans/` and update the STATUS pointer + cross-refs.
- **scaffold:** trim its own `split-open-questions` entry to ≤150w.
- **psc-monitor:** run the linter; trim any entries it flags.
Each is reconciliation/summarization (judgment), gated by `status_lint.py` going green — not mechanical flash work, which is why it is split out of this change.

## As-built deviations (apply phase, 2026-06-18)
- **decisions.md check made backfill-safe (Slice-1 smoke finding).** The frozen spec scoped decisions enforcement to "entries that declare `**Date:**`," assuming a Date implied a post-rule entry. The Slice-1 linter run against the scaffold disproved this: `ai-docs/decisions.md` has 13 dated entries but only **1** has `**Status:**` — 12 legacy entries (dated 2026-06-13…06-16, before the 2026-06-18 decisions-entry rule) plus the `**Date:** YYYY-MM-DD` template were all flagged, which would have forced the retroactive backfill the rule explicitly says is not required. Corrected by adding `--since` (default `2026-06-18`) and enforcing only on entries whose Date parses ≥ since (tasks 1.3 / 2.2 amended). Folded into Slice 2 as its first item. **The STATUS.md checks were unaffected** — the Slice-1 smoke flagged exactly the one known 316-word `split-open-questions` entry and nothing spurious.
- **Apply split into 2 slices** for budget + a mid-point linter smoke (Slice 1 = tasks 1–2; Slice 2 = the decisions fix + tasks 3–4). Executor uses `python3` (no `python` on PATH).

## Verify (2026-06-18)
**Verdict: READY.** MEDIUM multi-model chain (self → pro → flash), all three independent views READY:
- **Self-review (primary):** reproduced from disk — all 4 test suites pass (status_lint / sync / convergence / executor-agreement); `python3 scripts/status_lint.py .` flags exactly the one known 316-word `split-open-questions` STATUS entry and reports `ai-docs/decisions.md` OK (backfill-safe `--since`); all four propagation gates (`--check`/`--check-refs` × extrends/psc-monitor) green; `#### 3d` byte-identical across both executor bodies; skill gate bullet correct + cites the executor step.
- **deepseek-v4-pro verifier pass:** VERDICT READY, no defects; independently reproduced all four propagation gates + byte-identical 3d + scripts-present-downstream.
- **deepseek-v4-flash verifier pass:** first run emitted no final text part (operational no-output, exit 0) → re-ran once per the failure ladder → VERDICT READY, no defects.
- **Simplicity/quality gate:** PASS (stdlib-only linter mirroring `scaffold_check.py`; proportionate archive-time wiring; no per-commit hook). **Security gate:** N/A (no auth/cred/network/external-API surface).

**Still owned by archive:** reconcile scaffold `STATUS.md` (a `## Latest change` entry for add-status-lint) + `ai-docs/decisions.md` (the linter + the `--since` backfill-safety decision + the operator decision to drop psc-monitor's SMALL clause) + `ai-docs/open-questions.md`; run `python3 scripts/status_lint.py .` as the new gate before the archive commit; **no delta-spec promotion** (MEDIUM, no `specs/`). Phase B (the linter-driven STATUS/decisions cleanup across all three repos) is a separate follow-on.
