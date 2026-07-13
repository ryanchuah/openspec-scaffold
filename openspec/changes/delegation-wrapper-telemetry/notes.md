# notes — delegation-wrapper-telemetry (OW-7)

**Tier:** MEDIUM. **Orchestrator:** Opus (design pre-made — OW-7 in
`knowledge/research/workflow-audit-2026-07-11/AUDIT.md` finding 1 + §deterministic-script; site
inventory in this dir's `recon-delegation-sites.md`). **Apply:** delegated (deepseek-flash default —
the wrapper contract + tests are precise; the skill-wiring edits are mechanical block-replacements).

Closes **OW-7** in `knowledge/research/scaffold-gap-analysis-2026-07/OUTSTANDING-WORK.md`.

## Problem
Six OpenSpec skills each hand-roll the identical post-processing after an `opencode run` delegation
— fallback-grep, `jq` text extraction, marker/format assert, EXIT-sentinel poll, exit-code
interpretation — and **nothing records what delegated runs actually do**. The "exit codes lie"
lesson is re-learned every session because each session re-interprets exit codes by hand; wave-1 and
wave-2 yield analysis had to be reconstructed from narrative review-logs. The two scheduled
evidence-gated decisions (premise-gate downgrade at ~50 reviews; MEDIUM pro-pass downgrade at ~20
verifies — AUDIT §"how many verify reviewers") have no data source.

## Design (decided)
**A post-processing / "ingest" wrapper, NOT a full-invocation wrapper.** Each skill keeps its literal
`timeout -k <grace> <budget> opencode run --dir <root> ... < /dev/null > out.jsonl 2> err.log`
invocation UNCHANGED — this is load-bearing: it preserves scaffold_lint's `budget-agreement` guard
(scans literal `timeout -k <G> <B>` pairs against the §e table) and `noninteractive-delegation-safety`
(the literal `< /dev/null` + `--dir` stay in the documented invocation). Only the messy, error-prone
POST-processing collapses into one call to `scripts/opencode_delegate.py`, which reads the run's
`out.jsonl` / `err.log` / exit source and:
- detects silent agent fallback (grep for "Falling back to default agent");
- extracts the completion text (last `type:"text"` part — Python json, replacing the `grep|tail|jq`
  chain);
- classifies the run status from exit code + fallback + text presence (+ optional required markers);
- optionally captures a verdict token (`PREMISE:`, `VERDICT:`) via a regex;
- appends **exactly one JSONL telemetry line** to `output/delegation-log.jsonl` (untracked).

The wrapper reports facts about ONE run. It **does NOT** judge disk state (apply/archive/fix success
is disk-judged by the orchestrator), **does NOT** implement the failure ladder (retry / Sonnet
fallback / git-checkpoint restore stay orchestrator judgment), and **does NOT** gate anything.

### Why post-processing-only (the pivotal call)
scaffold_lint `budget-agreement` extracts `timeout -k <G> <B>` from every skill/agent file and
requires each pair be sanctioned by the harness §e table. `noninteractive-delegation-safety` requires
the documented invocation include `< /dev/null` and `--dir`. A full-invocation wrapper would hide
both behind flags, going blind on the budget guard and forcing a hardening-spec rewrite. Keeping the
invocation literal keeps every existing guard fully effective; the wrapper touches only the ~80% of
the toil that IS boilerplate (the post-processing dance) and 100% of the "exit codes lie" archaeology.

## Acceptance criteria
1. **`scripts/opencode_delegate.py`** exists — a tested CLI that ingests one completed delegated run
   (`--out`, `--err`, and either `--exit <int>` for sync sites or `--exit-file <path>` for bg
   sentinel sites) plus its identity (`--phase --agent --model --change`) and:
   - detects fallback, extracts completion text, classifies status
     (`ok|fallback|timeout|crash|marker-missing`), captures an optional `--verdict-regex` group,
     asserts optional `--require-marker` regex(es);
   - writes the extracted text to `--text-out` (default `<out>.text.txt`) and a machine-readable
     `<out>.result.json`;
   - **appends one JSON line** to the ledger (`--ledger`, default
     `<repo-root>/output/delegation-log.jsonl`) with at minimum: `ts, phase, agent, model, change,
     exit, fallback, status, marker_ok, verdict, retry`, plus any `--tag k=v` extras (e.g.
     `lens=test-quality`) and a best-effort `duration_s`;
   - exits 0 iff `status == ok`, nonzero otherwise (quick orchestrator check).
2. **The exit-code-lie is respected.** A nonzero-but-not-timeout exit with a present completion text
   is NOT classified `crash` (executors legitimately exit 1 at teardown on success); the raw `exit`
   is still recorded. `timeout` (124/137) and `fallback` are the hard operational-fail signals.
3. **Three success-evidence shapes handled** (recon §"Surprises"): verdict-token sites use
   `--require-marker`/`--verdict-regex`; disk-state-judged executor sites pass no marker and are
   `ok` on present-text + no-fallback + no-timeout (orchestrator judges disk); the apply
   `### NON-CONVERGENCE BLOCKER` failure marker is left to the orchestrator (not a wrapper concern).
4. **`scripts/test_opencode_delegate.py`** pins behavior with fixtures (no real opencode): text
   extraction (multi-part, empty, unparseable), fallback detection, status classification across
   exit 0/124/137/1 × marker-present/absent, verdict capture, ledger-line JSON validity + required
   keys, and a full-pipeline test via a temp out/err/exit fixture set. Any clock the ledger uses is
   **injected** (tests pass a fixed `ts`) so the test file trips no `unfrozen-clock` self-finding.
5. **Wiring — all 8 delegation sites** (recon inventory) replace their hand-rolled post-processing
   block with one `opencode_delegate.py` call, preserving each site's agent/model/budget/marker and
   sync-vs-bg shape. The failure ladders (retry/Sonnet/git-restore) and salvage/re-run judgment stay
   in the skill prose. `delegation-harness.md` §b/§d are updated to say post-processing is performed
   by the wrapper (contract cross-referenced), while §a/§c/§e (the literal invocation, timeout,
   budget table) are unchanged.
6. **Green gate:** `bash scripts/check.sh` exits 0 (this also flips the currently-red
   `broken-prose-path-citation` finding — `knowledge/HANDOFF.md:34` cites this script, which now
   exists). `ruff check --fix` + `ruff format` on new/edited `.py`.

## Spec delta
- **NEW `delegation-wrapper`** capability: (R1) delegated-run post-processing is performed by one
  deterministic tested wrapper that does not judge disk state or run the failure ladder; (R2) each
  delegated run appends exactly one telemetry line to an untracked ledger with a pinned minimum
  schema, feeding the scheduled evidence-gated decisions. No MODIFIED delta — the invocation stays
  literal, so `noninteractive-delegation-safety` and `budget-agreement` are untouched.

## Assumptions (batched)
- **A1 — ledger is untracked + append-only local telemetry** (`output/` is gitignored, per the
  AUDIT's own "untracked `output/delegation-log.jsonl`"). Durable per-change records still live in
  `review-log.md`/`notes.md`; the ledger is disposable/locally-regenerable operational history. No
  gitignore carve-out. Reverse only if the operator wants the ledger committed.
- **A2 — `duration_s` is best-effort** (from `out.jsonl` part timestamps when present, else null).
  No site captures duration today; the launcher owns wall-clock and the ingest wrapper runs after.
  The load-bearing fields are phase/agent/model/change/exit/fallback/status/verdict/retry.
- **A3 — the wrapper is ingest-only** (does not launch opencode). Launch stays in the skill's literal
  `timeout ... opencode run` line so the budget/stdin guards keep scanning it. Reverse would require
  the OW-8/OW-11 budget-guard rework — out of scope here.

## Out of scope
- Full-invocation wrapper / moving budgets into flags (would blind `budget-agreement`; see A3).
- The failure ladders, disk-state success judgment, salvage/re-run decisions (orchestrator judgment).
- Consuming the telemetry (the ~50-review / ~20-verify scheduled decisions are future, evidence-gated
  work — this change only produces the data).
- Downstream propagation (scaffold-managed files change; operator-gated, deferred).

## Traceability
Closes **OW-7**. Feeds the two scheduled decisions in AUDIT §"how many verify reviewers do we really
need?". Recon: `recon-delegation-sites.md` (8 sites, 3 success-evidence shapes).
