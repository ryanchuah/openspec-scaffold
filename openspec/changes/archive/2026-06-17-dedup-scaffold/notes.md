# Notes — dedup-scaffold (W2)

## Acceptance criteria

1. **Behavior preserved byte-for-byte.** This is extraction, not redesign. After the change, the
   delegation semantics — hardened invocation, assert-real-agent-ran, surgical-kill (never `pkill`),
   EXIT-sentinel completion detection, and each phase's timeout budget — are identical in effect to
   before. No new rule is invented ([[golden-source-edit-rules]]).
2. **Single source.** `ai-docs/delegation-harness.md` is the only place the shared harness contract
   lives. `grep -rn "pkill opencode"`, the `Falling back to default agent` assertion, and the
   EXIT-sentinel text each resolve to that doc only (+ the `noninteractive-delegation-safety` spec),
   not to the four skills.
3. **Timeouts centralized (B3).** All budgets (600/300/780) and the kill-grace appear once, in the
   doc's table; the skills reference it. The `reviewer-budget` spec's 780s is cross-referenced, not
   contradicted.
4. **Skills shrink, specifics stay.** Each of the four skills carries a one-line citation plus only its
   per-phase specifics (agent, model, budget, prompt) and its genuinely phase-specific failure ladder
   (apply convergence-blocker triage; verify escalate-to-Sonnet; archive reconciliation recovery).
5. **Carve-out intact.** verify's in-process Task-tool self-review pass remains explicitly exempt from
   the `< /dev/null` / `--dir` hardening.
6. **Manifest honest.** `ai-docs/delegation-harness.md` is in `scripts/scaffold_manifest.txt`;
   `test_sync_scaffold.py` passes and `--check` resolves the new entry.
7. **No drift lost.** Every reconciliation decision (below) is recorded; nothing safety-critical dropped.

## Reconciliation log (fill during apply — task 2.5)

The four copies had drifted. Record the canonical choice for each:

- **Kill-grace `-k 30` (apply/archive) vs `-k 15` (verify/propose):** Preserved existing values — extraction, not redesign. `-k 30` for longer-running executor phases (apply 600s covering full `tasks.md`, archive 600s covering multi-step reconciliation) where an extra 15s grace reduces the chance of SIGKILL during a legitimate slow step. `-k 15` for shorter/focused phases (propose's reviewer 780s, verify's fix-executor 300s and verifier passes 780s) where a faster kill after the budget expires is appropriate and the work is scoped to a single artifact or defect.
- **Assert-ran block — full (apply/propose/archive) vs abbreviated (verify):** Canonical form = the full version (grep stderr for `Falling back to default agent`, extract `part.text` via `jq`, confirm output is parseable). The canonical doc carries this full version from apply. Verify's previously abbreviated version ("grep stderr for `Falling back to default agent`. If found, do NOT use the output — escalate") was an acceptable simplification but the canonical doc uses the full form for completeness. Verify now cites the doc and adds only its phase-specific format checks (`## Verify Pass` / `VERDICT:`).
- **EXIT-sentinel scope:** The sentinel applies ONLY to `opencode run` calls launched with `run_in_background: true` — apply executor (has it), verify's fix-executor (has it), verify's verifier passes (have it). Propose's reviewer call is **synchronous** → no sentinel (correct by design). **Pre-existing drift documented:** Archive backgrounds its executor (`run_in_background: true`, line 161) but its invocation omits the sentinel — left as-is (extraction, not redesign) unless the operator scopes the fix in. The canonical doc explicitly notes this drift.

## Out of scope (deferred, per operator scope cut 2026-06-17)

- **C2** — rule restatements (tasks.md=apply-only, model-matrix ×5, no-counts ×5, web-research ×2).
  Overlaps W6/scaffold-sync's planned war-story + model-matrix single-sourcing; own change or W6 prep.
- **C4** — `.claude`/`.opencode` executor body-agreement guard. Batched into W4, which already edits
  those executor bodies (D-i, dropped RENAMED).

## Review focus (for the deepseek-v4-pro reviewer)

- Did extraction pick a **stale/abbreviated** copy and thereby regress the safety-critical machinery?
- Is anything genuinely **per-phase** (apply's triage ladder) wrongly pulled into the shared doc?
- Is the **in-process self-review carve-out** preserved, or does the citation wrongly impose `</dev/null`
  hardening on a non-`opencode run` pass?
- Is the manifest entry placed so W6 propagates the doc (not left scaffold-only)?

## Verify checkpoint (2026-06-17)

Passes run: **self-review (orchestrator, opus)** → **deepseek-v4-flash verifier pass**. The
deepseek-v4-pro pass was **skipped at operator instruction** (note: that leaves two independent views
rather than the default three). Flash verifier ran clean (real agent asserted: no fallback, `## Verify
Pass` + `VERDICT:` present); it independently re-ran both suites.

1. **Verdict:** READY for archive. Both passes READY, zero defects, nothing overruled.
2. **Live output eyeballed (behavior, no counts):** read the rendered instruction surface of all four
   skills post-extraction — each delegation step still reads as a self-sufficient procedure: the inline
   `timeout … opencode run …` invocation is present, the assert-output check is reachable, and the
   per-phase failure ladder is intact (apply's convergence-blocker triage, verify's escalate-to-Sonnet,
   archive's judge-from-disk recovery, propose's re-run-once salvage). `ai-docs/delegation-harness.md`
   renders the full shared contract (§a–e + the in-process carve-out + the archive sentinel-drift note).
   Full suite green (`test_sync_scaffold.py` and `test_convergence.py` both OK); the three distinctive
   harness phrases resolve only to the doc, not the skills.
3. **Defects found + fixes:** none (neither pass; nothing re-delegated; no Sonnet used at verify).
4. **As-built deltas (not behavior-changing):**
   - Propose's fallback handling is now leaner than the pre-change copy — it dropped the inline
     `mode: all`/"must be a primary" regression hint and the explicit "escalate to user with the stderr
     line" wording, now deferring to `delegation-harness.md` §b (treat fallback as an operational crash)
     plus propose's existing salvage path + the top-of-section "review must come from a different model"
     rule. Equivalent in effect; the diagnostic *hint* is the only thing not carried over.
   - The archive-executor's missing EXIT-sentinel (it backgrounds but omits `echo "EXIT=$?"`) is now
     **explicitly surfaced** inline in the archive skill and in doc §d — previously silent drift, now
     documented (still not fixed — out of scope for this extraction).
5. **Forward-looking items (fold into project docs at archive):**
   - **Archive EXIT-sentinel omission** → candidate for `ai-docs/open-questions.md`: archive backgrounds
     its executor but omits the sentinel, so completion detection there can't use the `[ -f …exit ]`
     check. Decide: add the sentinel to the archive invocation (a small follow-up change) or confirm it's
     intentional. Surfaced by this change; recorded nowhere else.
   - **Deferred W2 scope** (already tracked in "Out of scope" above + the consolidation-plan ledger, so
     not lost): **C2** rule-restatements → W6/scaffold-sync prep; **C4** `.claude`/`.opencode` executor
     body-agreement guard → W4 (alongside D-i RENAMED).
   - **Propagation dependency:** `ai-docs/delegation-harness.md` is now manifest-managed → W6 must carry
     it byte-identical to extrends + psc-monitor (the reason W2 precedes W6).

**Still owned by archive:** STATUS.md, `ai-docs/decisions.md`, `ai-docs/open-questions.md` (fold the
archive-sentinel item above), and cleanup. **Spec promotion: NONE** — this MEDIUM change has no delta
specs (`specs/` absent). The frozen `openspec/changes/scaffold-sync/` and the two untracked audit docs
are pre-existing, not this change's to reconcile.
