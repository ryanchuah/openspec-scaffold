# HANDOFF — wave-2 backlog, mid-batch (2026-07-14)

> **Read this right after `knowledge/STATUS.md`.** A session with an explicit operator autonomy grant
> worked the wave-2 remainder and shipped **OW-7 + OW-10** and **froze OW-11**, then stopped here (the
> operator asked for a handoff). Absorb this, continue from **Remaining work**, and **delete this file
> once the whole wave-2 batch (OW-8/11/12/13) is done**. Its normal state is absent.
>
> **You have NO standing autonomy grant.** The prior grant was in-session only. Confirm tier+plan with
> the operator per change unless they re-grant autonomy. (Everything below was done under that grant.)

## DONE this session — order OW-7 → OW-10, then OW-11 frozen
| OW | change (archive dir) | commits | status |
|----|----------------------|---------|--------|
| OW-7 | delegation-wrapper-telemetry | `6b3759f` (impl) + `f3a3fee` (archive) | **SHIPPED** |
| OW-10 | apply-throughput-resume | `0a4dc7d` (impl) + `8f1666a` (archive) | **SHIPPED** |
| OW-11 | skill-debloat-gates (scoped) | — (uncommitted) | **FROZEN — ready to APPLY** |

All gates green; zero Sonnet fallback anywhere; every review/verify pass ran deepseek via `opencode`.

## ⭐ OW-7 shipped a tool you should USE: `scripts/opencode_delegate.py`
OW-7 built + tested the **delegation post-processing wrapper**. After running ANY `opencode run`
delegation, pipe its outputs through it instead of hand-rolling grep/jq/exit-interpretation:
```bash
python3 scripts/opencode_delegate.py --phase <apply|verify-pro|propose-review|archive|…> \
  --agent <name> --model <model> --change <slug> \
  --out /tmp/<p>-out.jsonl --err /tmp/<p>-err.log (--exit $? | --exit-file /tmp/<p>-out.exit) \
  [--require-marker "..." --verdict-regex "VERDICT: (READY|NEEDS REVISION)"] [--tag lens=…] --quiet
```
It detects fallback, extracts the last text part → `<out>.text.txt`, classifies status
(`ok|fallback|timeout|crash|marker-missing`), captures the verdict, and appends one telemetry line to
`output/delegation-log.jsonl` (untracked, append-only). Exit 0 iff status==ok. The 8 skill sites now
cite it, but the **orchestrator invokes it manually** after each delegation — do that (it's the
telemetry source for the two scheduled downgrade decisions). It does NOT judge disk state or run the
failure ladder — those stay yours. `delegation-wrapper` is a promoted spec capability now.

## OW-11 exact state (FROZEN) + how to apply
- **Dir:** `openspec/changes/archive/2026-07-14-skill-debloat-gates/` (UNTRACKED on disk — frozen artifacts: `notes.md`,
  `tasks.md` T1-T9, `review-log.md` [3 rounds, PASS], `recon-ow11.md`, and two spec deltas under
  `specs/`: ADDED `defect-prevention-detectors`, MODIFIED `verify-multimodel-gate`).
- **SCOPED to 4 items** (of OW-11's chartered 8): #7 `spec-delta-structure` checks.py detector
  (**closes ratchet `medium-change-spec-delta-unvalidated`** — the class that makes MEDIUM spec deltas
  invisible to `openspec validate`), #6 `model-id-agreement` scaffold_lint check, #5 concurrent COMPLEX
  verifier passes, #4 explore→propose slug-match warning. **DEFERRED 4** (#1 verify steps-12-16
  de-bloat, #2 notes_lint, #3 freeze-check, #8 explore-prose trim) → an OW-11-residual follow-on
  (record in `knowledge/questions/` at archive; they're independent, nothing blocks on them).
- **Next: delegate apply** (deepseek-flash — tasks are precise; #7/#6 are code w/ tests, #5/#4 are
  prose). **Apply-order gotcha:** T7 (verify prose reorder) before T4 (verify one-line add), then
  re-grep T4's anchor. **Verify** must independently exercise the detector (build a temp change dir
  under `openspec/changes/` with a delta `spec.md` fixture carrying a SHALL-not-first-line requirement,
  a missing section header, a missing scenario) and the model-id lint, and **dogfood**
  `checks.py --check spec-delta-structure` on
  OW-11's OWN deltas (T9) — they must report clean. #7 follows the OW-1/OW-4 `checks.py` builtin pattern
  exactly (see
  `openspec/changes/archive/2026-07-13-defect-prevention-detectors/tasks.md` + Lesson 7 below).

## Remaining work — recommended order OW-8 → OW-13 → OW-12
- **OW-8 · Delegated-context caching hygiene · SMALL-MEDIUM.** Variable-paths-LAST in the
  apply/archive/reviewer prompt templates (prefix-cache credit); single-source the triplicated premise
  prompt (explore / propose / AGENTS.md SMALL bullet); test `OPENCODE_DISABLE_PROJECT_CONFIG=1` for
  executors (verify no agent.md depends on AGENTS.md content — AGENTS.md is auto-injected into every
  deepseek call and is the highest-churn boot file); treat AGENTS.md edits as cache-invalidation
  events (batch them). AUDIT finding 2 + §caching. **NO recon yet — do one first** (map the current
  prompt templates post-OW-7/OW-11, which reshaped several).
- **OW-13 · Knowledge-surface bounding round 2 · SMALL.** **RECON DONE →**
  `openspec/changes/knowledge-surface-bounding-2/recon-ow13.md` (UNTRACKED). Key findings: scaffold
  boot surface ~77KB (**under** the 80KB warn line IF `boot_surface` is scoped to the 4 core mandatory
  files and EXCLUDES the ephemeral HANDOFF); **year-split (decisions) + plans-count lint are NO-OPS on
  the scaffold** (all-2026 decisions, only 10 plans files) — they're propagated mechanisms, build+test
  via fixtures. status_lint word-budgets for exempt sections need STATUS.md "Immediate next action"
  trimmed first — but the archives this session rewrote STATUS repeatedly, so **re-measure** before
  setting a budget. A new `boot_surface_lint.py` under `scripts/` + a test in `test_doc_lint_gate.py` + manifest
  entry. AUDIT finding 7 + addendum. Self-contained, low-risk.
- **OW-12 · Archive mechanization · SMALL-MEDIUM · lowest priority.** `archive_move.py` for the dir
  move; deterministic delta-applier for ADDED/REMOVED/RENAMED (LLM only for MODIFIED merge +
  reconciliation narrative). Keep the archive-executor on pro. AUDIT finding 6. NO recon yet.

Late additions (chain-independent, slot anywhere): **OW-15** (correctness-audit meta-hardening, amends
OW-5) + **OW-16** (product-audit skill) — see `roadmap.md` + `OUTSTANDING-WORK.md`.

## HARD-WON PROCESS LESSONS (carried forward + updated — these save real time)
1. **opencode delegations MUST run `run_in_background: true`** (Bash foreground SIGTERMs at 120s;
   opencode budgets are 600-780s). Pattern: background + `; echo "EXIT=$?" > /tmp/<p>-out.exit`, wait
   for the completion notification, then run `opencode_delegate.py` (Lesson above) to post-process.
2. **`openspec validate <medium-change> --strict` is VACUOUS** (CLI discovers changes via
   `proposal.md`; MEDIUM has none → "Unknown item", exit 1 for the wrong reason). Green gate =
   `bash scripts/check.sh` ONLY. Spec deltas DO get validated after promotion at archive, so ensure
   each requirement's **SHALL/MUST is on its FIRST physical line** before archive. **OW-11's
   `spec-delta-structure` detector — once it lands — catches this deterministically pre-archive.**
3. **Interpreter:** bare `pytest`/`python3 -m pytest` is NOT available. `bash scripts/check.sh`
   (pytest -q). One-off detector run: `/usr/bin/python3 scripts/checks.py --check <name>`.
4. **The pro review earns its cost on code-heavy changes** — this session it caught 3 real 🔴 in
   OW-11 (notes↔tasks approach drift + advisory/hard-gate mislabel) that green tests would hide.
   Budget 2-3 rounds; a 🔴 mandates a re-review round (max 3). Documentation-consistency 🔴s still
   need the re-review — check EVERY section that references the fixed thing (Round 2 caught a spot I
   missed in Round 1).
5. **At verify, INDEPENDENTLY exercise code changes** — build your own fixtures, run the real code;
   never trust the executor's own green tests. This session: hand-ran `opencode_delegate.py` through 9
   scenarios + probed the real opencode jsonl timestamp shape (`part.time={start,end}` epoch-ms) to
   fix a duration bug the frozen tasks.md had guessed wrong (disclosed inline at verify).
6. **Apply routing:** deepseek-flash worked cleanly on every precise tasks.md this session (OW-7's
   ~300-line script + 8-site prose wiring; OW-10's byte-synced executor edits). A precise spec is what
   makes flash viable. No Sonnet fallback needed. Executors sometimes forget to flip `tasks.md`
   checkboxes — check + flip them yourself before commit.
7. **checks.py detector architecture** (OW-11 #7 needs this): registry = dicts in `_REGISTRY`;
   in-process builtins register in `_BUILTIN_RUNNERS` + `_PARSERS` (value MUST be CALLABLE, e.g.
   `lambda _stdout: []`) + special-case `_availability_for_check` (always-available) +
   `_autodetect_defaults` (enabled). Adding a registry entry REQUIRES updating `test_checks.py`
   `ListModeTest.expected_names` + `AutodetectTest` + `SummaryLineFormatTest`. checks.py findings are
   ADVISORY (don't fail check.sh). scaffold_lint.py checks (budget-agreement, and OW-11's new
   model-id-agreement) are golden-source-only (NOT in the manifest, don't propagate).
8. **Archive-executor (deepseek-pro) is reliable** — handled a NEW capability (OW-7) and a MODIFIED
   requirement promotion (OW-10) cleanly. It uses plain `mv`, so stage the move with
   `git add -A <old-dir> <new-archive-dir>`. Its wider-drift sweep is flag-only — reconcile
   `roadmap.md` + `OUTSTANDING-WORK.md` yourself (this session did, per each archive).
9. **Commit rhythm:** two commits per change — "Implement …" then "Archive … and reconcile project
   docs". Commit to `main` directly. **Push stays operator-gated (NOT done this session).**
10. **STATUS 3-section cap is enforced at each archive** — the archive-executor drops the oldest
    change section. This session dropped composition-audit-cadence (at OW-7 archive) and
    instruction-surface-coherence (at OW-10 archive). Full record lives in the archive dirs.

## In-progress artifacts committed with this handoff (pick these up, don't delete)
- `openspec/changes/archive/2026-07-14-skill-debloat-gates/` — OW-11 FROZEN artifacts, committed (apply from here; the
  next "Implement OW-11" commit adds the code + flips the `tasks.md` checkboxes).
- `openspec/changes/knowledge-surface-bounding-2/` — OW-13 recon (`recon-ow13.md`), committed.
- `output/delegation-log.jsonl` — the OW-7 telemetry ledger (this session's verify-pro + archive
  dogfood runs). Untracked by design (gitignored `output/`).
- `.claude/worktrees/analyze/` — a LOCKED, gitignored stale git worktree (`worktree-analyze`). NOT
  ours — leave it; any new file-walking check must exclude it.

## Downstream propagation — DEFERRED + operator-gated (unchanged)
OW-7 + OW-10 edited scaffold-managed files (AGENTS.md span, 6 skills, delegation-harness, checks.py's
sibling manifest, apply-executor agent bodies, apply-convergence-guard spec). NOT synced to
extrends/psc-monitor without fresh operator authorization. OW-11 (when shipped) adds checks.py +
delegation-harness §(f) to the propagation set.

## Pointers
- Design sources: `knowledge/research/workflow-audit-2026-07-11/AUDIT.md` (wave-2 design calls);
  `knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md` (backlog + per-item STATUS).
- The scaffold's own `checks.py --check test-quality` reports ~13 advisory self-findings on its own
  tests — EXPECTED, not a defect (audit-triage material).
