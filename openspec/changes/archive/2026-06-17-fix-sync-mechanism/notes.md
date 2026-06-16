# Verify notes — fix-sync-mechanism (W1)

## Verdict
**READY for archive.** Self-review (Claude orchestrator) clean; one delegated multi-model pass
(deepseek-v4-flash) returned `VERDICT: READY` / `- None`. The deepseek-v4-pro pass was **skipped at
operator instruction** for this change (normally run; recorded here so archive knows it was a
deliberate omission, not a miss).

## Multi-model passes
1. **Self-review (Claude Code orchestrator)** — READY. Read all four files; re-ran the full suite
   (`python3 scripts/test_sync_scaffold.py` green; `python3 scripts/test_convergence.py` still green);
   ran a real-data eyeball (below).
2. **deepseek-v4-flash verifier pass** (`opencode run --agent openspec-verifier`) — READY, `- None`.
   Real verifier confirmed (no "Falling back to default agent"; emitted a `## Verify Pass` block with a
   `VERDICT:` line).
3. **deepseek-v4-pro verifier pass** — **NOT RUN** (operator-directed skip for this change).

## What I confirmed by eyeballing live output (behavior, not counts)
- Ran `sync_agents_md` against the **real** scaffold `AGENTS.md` and both real downstream files
  (extrends, psc-monitor). Both ran without raising, were **idempotent on real data** (applying the
  span-replace to its own output returned a byte-identical string), and preserved each repo's title and
  `## Project context`. Both currently show `would_change=True` — i.e. their shared spans legitimately
  differ from scaffold today (expected: the downstream repos lag; propagation is W6).
- Rendered the concrete psc-monitor diff (646-line file with a `# Project reference` appendix). The
  per-repo **tail is preserved byte-identical** (`out.endswith(real_tail)` true). The `## After reading
  this file` *section body* correctly updates from scaffold — it is shared span 2 by design; only the
  trailing `---` + `# Project reference` appendix is the per-repo tail. The tail-boundary regex
  (`\n(---\s*\n|# \w)`) correctly anchors on the `---` separator and is **not** fooled by an earlier
  in-prose mention of the literal string "# Project reference" (which occurs at line 52 inside a shared
  span). This was the R1 mis-slice risk — confirmed handled on real data.
- Guard + check exit codes verified behaviorally: `scaffold_check.py` returns **2** when a
  manifest-listed path is staged (blocks) and **0** otherwise; `--check` exits **1** on drift / missing,
  **0** when identical.

## Defects found and how fixed
**None.** No fix delegation was needed; no Sonnet fallback was used. (One initial false alarm during my
own eyeball — a naive `.index("# Project reference")` matched the line-52 prose mention and reported the
tail as changed; re-checked against the real tail anchor and confirmed byte-identical preservation. This
was a probe artifact, not a code defect.)

## As-built deltas vs the artifacts
- None material. The implementation faithfully transcribes design D2 (manifest), D3 (`sync_agents_md`),
  D5 (guard), D6 (`--check`). Minor as-built detail worth noting for archive: bad-target / missing-source
  aborts are implemented as `sys.exit(1)` (the spec/design specify "exit non-zero"; 1 satisfies it and is
  distinct from the guard's blocking 2 and consistent with `--check`'s diagnostic 1). No spec change needed.

## Forward-looking items (fold into ai-docs/open-questions.md at archive)
1. **Guard coverage limit (M1) — carried, not closed.** `scaffold_check.py` only intercepts Claude
   Bash-tool commits; operator-terminal and opencode/deepseek executor commits bypass it; `--no-verify`
   is the sanctioned escape. Documented in the module docstring + spec. The W6 manual diff is the
   backstop. Operator may later want a repo-wide `core.hooksPath`/`.git/hooks/pre-commit` (considered and
   rejected for W1) — revisit only if silent downstream drift actually occurs.
2. **`--check` AGENTS.md first-run cosmetic DIFFERS (D6 caveat).** A formatting mismatch at the
   span2/tail join boundary can cause a one-time `AGENTS.md DIFFERS` on the first `--check`; running
   `sync_scaffold.py` once normalizes it. Cosmetic, not a correctness bug — but W6 should expect it and
   not treat the first-run AGENTS.md DIFFERS as real drift.
3. **Manifest staleness (R3).** The manifest is self-managed; a newly-added shared file that nobody lists
   is invisible to sync until added. No automated catch in W1 — W6's drift check is the backstop. Also:
   `ai-docs/opencode-delegation-notes.md` is deliberately **absent** from the manifest (it does not exist
   in scaffold yet); it must be promoted into scaffold + added to the manifest in the later dedup/
   propagation change before it can sync.
4. **R1 line-anchored span risk (accepted).** A downstream `## Project context` that itself contained a
   literal line `## Roles` would mis-slice; accepted as low-risk (project context is short, hand-curated)
   and noted in design R1. No guard added by choice.
5. **Live guard hook smoke is W6.** The guard's `git diff --cached` integration is unit-stubbed here; the
   live `git commit` hook smoke in downstream repos is W6, riding the W0-verified exit-2 mechanism.

## Still owned by archive (do NOT edit those docs here)
- `STATUS.md` — reflect W1 shipped.
- `ai-docs/decisions.md` — record the header-cut (D4) + exit-2 guard decisions if not already captured.
- `ai-docs/open-questions.md` — fold in the five forward-looking items above; clear anything W1 resolved.
- `ai-docs/improvement-roadmap.md` / consolidation-plan — mark W1 done; note `scaffold-sync` is now
  safe to delete once W6 lands (W1 superseded it).
- Spec promotion: promote `specs/scaffold-sync-mechanism/spec.md` into `openspec/specs/` (new capability).
- The uncommitted W0 working-tree edits to `ai-docs/decisions.md` / `open-questions.md` still need a
  commit decision (standalone vs folded into W1's commit) — operator call.
- Cleanup: the four new files are untracked/uncommitted (local-only convention) pending operator commit.
