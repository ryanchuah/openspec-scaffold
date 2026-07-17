---
name: composition-audit
description: Run a bounded composition-audit ceremony — deterministic sweep (jscpd/vulture/radon) + bounded LLM judgment pass over top-K hotspots, with a machine-discriminable verdict. Operator-invoked, pull-only.
license: MIT
metadata:
  author: openspec
  version: "1.0"
  generatedBy: "1.4.1"
---

Run a bounded composition-audit ceremony: a whole-repo review of accreted
composition drift (sibling/near-duplicate code, dead-code clusters, doc/code
drift) over a closed set of top-K hotspots. The ceremony NEVER runs
autonomously, NEVER gates any process, and its close-out routes generalizable
findings into the finding-closure ratchet (frozen format).

**Pull-only.** This skill is never wired into session boot or `AGENTS.md`.
Invoke it explicitly when you need to review composition health.

**Normative ceremony sequence:** see `openspec/specs/composition-audit/spec.md`
(composition-ceremony-contract, 7 steps). This file adds only per-step
operational detail. K defaults to 5 — the spec is normative for the default.

**Interpreter convention.** Use `<py>` below as a placeholder for the repo's
Python interpreter. Resolve it in this try-order:
1. A repo task-runner `audit-*` target, if one exists (e.g. `just audit-floor`);
2. `.venv/bin/python` if the virtual environment exists;
3. `python3` if available;
4. `python` otherwise.

**Hardened delegation harness.** The pre-digest step (step 4 below) delegates
to a cheap model via the standard delegation pattern in
`.claude/skills/_shared/delegation-harness.md`. Use `--format json` and a
timeout of 780 s.

---

## Steps

### 1. Wiring detection

Check whether the audit layer is wired in this repo (presence of
`checks.toml` with the `[checks]` table). If not wired, print the standard
build-out guidance from the `run-audit` skill's wiring-detection branch and
STOP. Do not proceed to step 2.

### 2. Signal read

Regenerate the `outstanding` fact:

```bash
<py> scripts/facts.py --check outstanding
```

Report the composition-audit due-state from the output. The ceremony does
NOT require `due` to be true — an early run is always allowed and also
resets the clock at close-out.

### 3. Deterministic sweep

Run the heavy-tier composition detectors in one-shot mode:

```bash
<py> scripts/checks.py --report --include jscpd --include vulture --include radon \
    [--baseline output/checks/composition-baseline.json] \
    --out output/checks/<date>
```

  - Omit `--baseline` when no standing baseline pointer exists (first run
    or post-clean checkout). The sweep states this explicitly: the delta
    degrades to "everything is new."
  - An INFRA-FAIL (missing tool, version mismatch) stops the ceremony with
    the preflight guidance printed verbatim. Surface it to the operator.
  - After the check run succeeds, collect the hotspot ranking:

```bash
<py> scripts/audit_scope.py scan --json output/checks/<date>/audit-scope.json
```

Because `audit_scope` runs outside `checks.py`, its scan is independent of
the check run's INFRA-FAIL path. If it also fails, report the error and
STOP.

### 4. Pre-digest (delegated)

Delegate a cheap model (via the hardened harness) to cluster and deduplicate
the three detector outputs + baseline delta + hotspot ranking into a
shortlist. Use the D5-campaign shape from `deterministic-tooling-layer`:
merge findings by path/rule, annotate with hotspot score, flag items that
are new vs carried from the baseline delta. The **orchestrator** checkpoints
the returned shortlist to `output/checks/<date>/pre-digest.md` — the read-only
reviewer emits it as text and never writes files.

Delegation command shape (adapt paths per run):

```bash
timeout -k 15 780 opencode run \
  --dir <repoRoot> \
  --agent openspec-reviewer \
  --model deepseek/deepseek-v4-flash \
  --format json \
  "Read the findings at <path>/findings.json, the delta at
   <path>/delta.json (if present), and the hotspot ranking at
   <path>/audit-scope.json. Cluster and deduplicate by path/rule,
   annotate each group with hotspot score, and flag items new vs
   baseline-carried. Emit the shortlist as your final message (you are
   read-only — do NOT write any file)." \
  > /tmp/composition-predigest-out.jsonl 2> /tmp/composition-predigest-err.log \
  < /dev/null
```

The read-only reviewer returns the shortlist as text; the orchestrator writes
the checkpoint from the captured completion output:

```bash
grep '"type":"text"' /tmp/composition-predigest-out.jsonl | tail -1 \
  | jq -r '.part.text' > output/checks/<date>/pre-digest.md
```

### 5. Bounded judgment pass (orchestrator)

Review the pre-digest shortlist through the composition lens. For the
top-K hotspots (default K=5), assess:

- Sibling or near-duplicate drift (jscpd hits that are not false
  positives for the project's idiom).
- Accreted duplication — same pattern repeated across modules over time.
- Cross-module invariant coherence — do parallel changes in sibling
  modules remain consistent?
- Dead-code clusters (vulture hits that suggest systemic patterns, not
  one-off unused imports).
- Doc/code drift — documentation that no longer matches the
  implementation near the hotspot.

Assign a `Class:` slug to each finding. The vocabulary (shared with the
finding-closure-ratchet and OW-5 correctness-audit) follows the convention
`<area>-<kind>`, e.g. `composition-duplication`, `composition-dead-code`,
`composition-doc-drift`.

### 6. Verdict

Write exactly one of the following verdicts to
`output/checks/<date>/composition-verdict.md`:

- **`COMPOSITION: CLEAN`** — no generalizable findings.
- **`COMPOSITION: FINDINGS-ROUTED`** — findings exist and were routed into
  the ratchet (step 7).
- **`COMPOSITION: ESCALATE`** — findings suggest a systemic class beyond
  the mechanical slice. Named indicators: ≥2 distinct cross-module classes,
  any correctness-suspect finding (not just hygiene), or a baseline delta
  that grew after the previous `FINDINGS-ROUTED` close-out. ESCALATE
  recommends chartering a correctness audit via the
  `correctness-audit` skill (OW-5 protocol); chartering remains
  operator-gated.

### 7. Close-out

For each generalizable finding, perform the finding-closure-ratchet 3-question
triage (frozen format in `specs/finding-closure-ratchet/spec.md`):
"Can this be detected deterministically? → frozen test? → waive?". The
triage is performed by the orchestrating agent (judgment work), never
delegated to a mechanical executor, and never blocks on building a detector.
Append one ratchet-log line per finding in the frozen format.

Then:

1. **Audit-log line.** Print and append one composition audit-log line:
   ```bash
   <py> scripts/audit_scope.py log-line --kind composition \
       --date <YYYY-MM-DD> --essence "<one-line summary>"
   ```
   Append the printed line to `knowledge/audit-log.md` (create the file
   with the `# Audit log` heading if it does not exist yet).

2. **Anchor tag (operator-gated).** Present the tag command — do NOT
   execute it automatically:
   ```bash
   <py> scripts/audit_scope.py tag --kind composition --date <YYYY-MM-DD>
   ```
   The operator runs it to lock the anchor. No tag → no clock reset.

3. **Baseline copy.** Copy the run's `findings.json` to
   `output/checks/composition-baseline.json` (the standing baseline pointer
   for the next ceremony):
   ```bash
   cp output/checks/<date>/findings.json output/checks/composition-baseline.json
   ```
   (The pointer is untracked like all of `output/`; a repo MAY commit it —
   per-repo policy.)

4. **(Optional) knowledge-drift-review.** If the sweep or judgment pass
   surfaced knowledge-tree drift, consider running `knowledge-drift-review`
   as a follow-up. This is outside the mandatory ceremony core (D9).

---

## Honest limits

The deterministic sweep (jscpd, vulture, radon) catches a narrow mechanical
slice — exact or near-exact duplication, trivial dead code, and
cyclomatic-complexity outliers. The judgment pass and the `ESCALATE` seam
carry the rest: systemic patterns, cross-module coherence, and correctness
concerns beyond hygiene. This ceremony is explicitly bounded to an
afternoon (one cheap-model pre-digest + one orchestrator pass over K
hotspots), positioned below the OW-5 correctness-audit in depth and cost.

## Residual attention-dependence

The composition-audit due-signal is surfaced in the pull-only `outstanding`
fact and the `inventory` fact's `composition_anchor` block — both consumed
only when an operator reads them. There is no non-gating recurring-surface
notice (D8). If a downstream repo is observed sitting `due` for >30 days
unseen, a follow-on SMALL change should add the recurring-surface notice
then.

## Guardrails

- This skill is **read-only with respect to repo state** until step 7 (close-out),
  when the orchestrator writes ratchet-ledger lines and an audit-log line,
  and the operator gates the tag creation.
- Do **not** wire this skill into session boot, `AGENTS.md`, or any auto-run
  hook.
- Do **not** edit `scripts/outstanding.py`, `scripts/checks.py`,
  `scripts/audit_scope.py`, or `scripts/knowledge_lint.py` from this skill.
