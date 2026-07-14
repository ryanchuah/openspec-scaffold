# Premise review — direction gate (explore) — product-audit-skill

Reviewer: `openspec-reviewer` @ `deepseek/deepseek-v4-pro` · phase=explore-gate · fallback=no · marker_ok=yes

### Premise Verdict

```
PREMISE: AGREE
```

Zero 🔴. Direction sound: problem is genuinely structural (portfolio-level code-facing bias, not
symptomatic); three root causes specific + evidenced; solution maps cleanly to each; method validated
n=3 incl. first non-code domain; scope well-bounded.

### 🟡 Should Fix (folded into brief / carried to design)
1. **Ratchet triage fit for non-code findings.** Ratchet Q3 ("mechanically detectable / test-freezable?")
   was designed for code defects; a promise-surface finding ("copy claims X, code lacks X") may not map
   onto the five dispositions cleanly (what is a `check:`/`test:` for a marketing claim?). → carried as
   explicit design question; consider a leaf carve-out for promise-surface classes.
2. **Claims-ledger staleness lint shouldn't default to "optional."** The ledger suffers the same
   copy↔code drift the skill detects; its maintenance mechanism shouldn't stay optional indefinitely. →
   reframed as a tension: ship the guarded lint now, or explicitly defer with a re-audit date.

### 💡 Suggestions (carried to design)
1. **Reciprocal awareness pointer** — product-audit SKILL should point back at correctness-audit
   (a built-but-unsold finding may warrant a correctness-audit of the undisclosed feature), closing the
   bidirectional handoff correctness-audit already opened.
2. **Operator dual-literacy** — a product-audit operator needs both business-thesis and code-surface
   literacy; consider a light "dual-literacy" scaffold (parity with the correctness-audit charter walk).

Verdict: PASS — ready to advance to propose. 🟡 concerns to be addressed in the brief/design, neither
challenges the premise.
