# Premise review — day-to-day-tooling (direction gate, deepseek-v4-pro, 2026-07-03)

Reviewer: `openspec-reviewer` via hardened `opencode run` (no fallback-agent line in stderr;
real reviewer asserted). Full transcript retained in session scratch only; verdict and
actionable findings recorded here.

## Findings

### 🔴 Blocking Issues
None.

### 🟡 Should Fix
1. **`checks.toml` ownership boundary unspecified** — scaffold-managed vs per-repo glue must
   be resolved at design time (could change scope of A or C).
   → RESOLVED in brief §Post-review clarifications: per-repo one-time glue with a seed
   convention (it encodes per-repo realities: installed tools, enable/disable, paths).
2. **Incident framing** — the extrends escalation is fixed by A's preflight +
   self-explaining failures; the checks/facts/audit rename is structural hygiene, not the
   incident fix. Implementers should not over-rotate on naming.
   → Noted in brief.
3. **Doc-lint wiring claim needed verification** — `knowledge_lint.py`/`status_lint.py` ARE
   scaffold-managed and shipped downstream; verify whether the pytest suite already runs
   them live-tree before scoping C.
   → VERIFIED 2026-07-03: `test_knowledge_lint.py`/`test_status_lint.py` are entirely
   `tmp_path`-fixture based; nothing runs the linters against the real tree at commit time.
   C's gap is precisely "shipped but not wired as a live-tree gate."

### 💡 Suggestions
1. Make the B→A→C→(sync)→D1/D2 dependency chain explicit. → Done in brief.
2. Security-scanner CI cadence: adopt a starting default (e.g. blocking on push to `main`)
   rather than leaving fully open. → Default adopted in brief, final call in C's design.
3. Note that the brief is portfolio-level; each change gets its own
   `openspec/changes/<name>/` artifacts at propose. → Noted in brief.

## Verdict

### Premise Verdict

```
PREMISE: AGREE
```
- **Root, not symptom**: AGREE — three-tier layering (gates/facts/audit) correctly
  diagnoses why five symptoms share one architectural cause.
- **Solution targets root**: AGREE — A + C resolve the audit-first collapse; B and D1/D2
  are necessary infrastructure/deployment.
- **Scope right-sized**: AGREE — out-of-scope items reasonable; five tiered changes
  appropriate for the risk.
- **Blind spots**: `checks.toml` ownership and doc-lint wiring status — both resolved
  above; neither invalidates the direction.
