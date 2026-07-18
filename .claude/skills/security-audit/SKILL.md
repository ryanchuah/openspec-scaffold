---
name: security-audit
description: Run a lane-split adversarial security audit — charter (lane select + attacker persona + secrets-exclusion) → deterministic scanner floor → per-lane adversarial passes (empirical-probe-first, confirm-the-negatives) → delegated refuter verification → cross-lane completeness critic → SECURITY CLEAN/FINDINGS-ROUTED/ESCALATE verdict → finding-closure ratchet. Operator-invoked, pull-only, never fixes product code.
license: MIT
metadata:
  author: openspec
  version: "1.0"
  generatedBy: "1.4.1"
---

Run a whole-repo **adversarial security audit** as a set of focused, resumable **lanes**, each read
with hostile intent. It is the missing counterpart to the per-change, diff-scoped security pass in
`openspec-verify-change`: that pass sees one diff; this ceremony reads the whole security surface as
an attacker would. A repo can pass every chartered correctness audit and still ship an
account-takeover misconfiguration, because no correctness charter's universe contains the security
surface — this skill names the occasion and the method to close that gap.

**Pull-only.** This skill is NEVER wired into session boot, `AGENTS.md`, archive, CI, or any auto-run
trigger, and it NEVER gates a commit / verify / CI / lifecycle step. Invoke it explicitly. **Cadence:**
a pre-launch gate for a repo with an external attack surface (auth, customer data, money), and a
re-run before a major surface change — not a recurring count-based ceremony.

**Audit-then-fix.** The audit produces findings only and modifies **no product code**. Remediation
ships later as ordinary OpenSpec changes citing finding IDs. The sole admitted mid-audit code change
is the **fix-now criterion** — hardening an audit *instrument* (a detector, a probe fixture), never
product code.

**Model routing — important.** Some hyper-capable tiers are guardrailed against cybersecurity-risk
work and will refuse or degrade on an adversarial security audit. Run this under a capable,
non-guardrailed tier (Opus or equivalent); do not route it to a guardrailed tier. (This is why the
proving-ground run was operator-confirmed off the Fable tier.)

**Normative protocol:** `openspec/specs/security-audit/spec.md` (the `security-audit` capability).
This file adds operational detail; the spec is normative for the sequence, the disposition set, the
verdict values, and the liveness/deferral rules.

**Interpreter convention.** Use `<py>` below as a placeholder for the repo's Python interpreter,
resolved in try-order: (1) a repo task-runner `audit-*` target if one exists; (2) `.venv/bin/python`
if the venv exists; (3) `python3`; (4) `python`.

**Hardened delegation harness.** Every delegated verification (step 5) uses the standard
`opencode run` contract in `.claude/skills/_shared/delegation-harness.md` (§a hardened invocation,
§b `scripts/opencode_delegate.py` post-processing, §c bounded wait + surgical kill, §d background
completion, §e budgets, §g variable-content-last for prefix caching).

**Never send secrets to an external model.** A delegated model is an **external API**. No delegated
prompt may include `.env`, real secrets, private keys, or PII fixtures. A known-safe placeholder or
dev-default secret MAY be discussed; a real production secret never enters a prompt. Prefer redacted
or synthetic fixtures.

---

## Steps

### 1. Wiring detection

Check whether the deterministic security floor is wired in this repo: the `checks.py` security
check-family (`gitleaks`, `osv-scanner`, `semgrep`, `bandit`) and a `checks.toml` enabling the SAST
pair. If the audit layer is not wired, print the build-out guidance from the `run-audit` skill's
wiring-detection branch and STOP. If the scanners are wired but the binaries are not installed,
point at `knowledge/reference/security-scanners.md` (provision via `bash scripts/install-tools.sh`;
`semgrep` additionally needs a ruleset via `[checks.semgrep] args`) and note which lanes lose their
deterministic floor until it is installed.

### 2. Charter + dossier

Create the audit dossier `knowledge/research/security-audit-<YYYY-MM>/` and write `CHARTER.md`:

- **Lane selection.** From the recommended lane menu below, list the lanes that apply to THIS repo,
  and record each inapplicable lane as **explicitly excluded with a reason** (e.g. "V-uploads: N/A —
  no upload endpoints"). A silently-omitted lane is the defect, not the exclusion.
- **Per-lane persona.** Give each lane an adversarial-researcher charter framed as a concrete attack
  ("forge a token for any user_id"; "bypass the ownership check on this route; show the payload"),
  never a posture question ("is auth secure?"). The attack framing is what surfaces real bugs; the
  posture framing rubber-stamps correct-looking code.
- **Secrets rule.** Record the never-send-secrets-to-an-external-model rule (above) in the charter so
  every delegated call inherits it.
- **Liveness (multi-session).** Because lanes are read one at a time and resumable, add an Active
  `knowledge/questions/INDEX.md` item referencing this dossier and its outstanding lanes. It stays
  Active until close-out (step 8) — so an unfinished audit cannot silently drop off every tracker.

Scanner dumps and probe scripts are **untracked** regenerable evidence → `output/security/`. The
dossier (charter + per-lane findings + the confirm-the-negatives lists) is the only tracked record.

### 3. Deterministic scanner floor (front-loaded)

Run the enabled security detectors ONCE, up front, and dump to disk — the LLM lanes consume the
reports, they do not re-scan:

```bash
<py> scripts/checks.py --report --include gitleaks --include osv-scanner \
    --include semgrep --include bandit --out output/security/<date>
```

(Use `--include` only for detectors this repo leaves disabled-by-default; an INFRA-FAIL on a missing
binary stops with the preflight guidance — surface it and provision per step 1.) Also capture any
`npm audit` / language-native advisory dumps the repo has for its frontend/dependency surface.

**SAST is a floor, not a finder** (load-bearing budgeting rule). Budget the scanner output as "prove
the known-safe patterns stay safe," and spend LLM effort on the data-flow-to-a-sink reasoning a
scanner structurally cannot do. In practice most SAST hits on a hardened repo are false positives
(e.g. B608 on a safe parameterized query the tool can't statically verify); triage each for
true-positive/reachability BEFORE filing — a scanner's severity label is not a finding. Record a
scanner's **silence** as coverage, and a scanner **gap** (e.g. no JS/TS SAST available) as a
manual-coverage caveat so a re-review knows the clearance was by hand, not by tool.

### 4. Per-lane adversarial passes

Work one lane at a time (resumable; checkpoint each lane's findings + confirm-the-negatives to the
dossier before moving on). For each lane:

- **Empirical-probe-first.** When a finding's severity turns on version-specific crypto/library/
  runtime behavior, **run the one-liner** rather than reasoning from memory — memory-based severity
  calls are routinely wrong for a specific version (e.g. whether a hash routine truncates vs. raises
  on oversize input flips a "silent-truncation bug" into an "unhandled-exception 500", or vice
  versa). Two of the proving-ground run's real findings were confirmed by running code, not reading.
- **Gate a boot-time config validator on the test-exempt env.** If a lane's remediation adds a
  fail-loud boot validator (e.g. "refuse to boot on a placeholder secret"), gate it on the env the
  test harness sets to the exempt value (check `conftest.py` first) or it detonates the whole suite
  at import. A placeholder-secret detector must enumerate BOTH the source default AND whatever the
  deploy template ships, plus a length floor — not just the one string a census named.
- **Sweep the class, not just the instance.** Once a lane names a *class* of defect (e.g. "a
  plausible prod misconfig degrades silently to an insecure default"), sweep every other
  config-gated fallback in the repo for the same shape — it recurs across files.
- **Confirm-the-negatives are the deliverable of a clean lane.** A heavily-hardened lane is a
  legitimate CLEAN result — do not manufacture findings. Its deliverable is the **enumerated attack
  list, each cleared, with the control that stops it** (that list is what a re-review inherits).
- **Business-logic/abuse is a distinct lens.** Run an abuse lens (quota/limit races, entitlement
  bypass, replay) over the same route file-set as a *separate* pass from the authz lens — they find
  different classes, and the abuse finding often lives in a different file than the authz lane
  scopes to.
- **Trace each code-level safety to the infra invariant it assumes.** A correct handler can still be
  unsafe if a constraint it depends on (a `UNIQUE`, a role grant) is absent in prod — cross-link to
  the existing deploy gate rather than re-filing.

Finding severities are **provisional** until the orchestrator finalizes them (step 5). A delegated
model may draft a severity but never sets the final label.

### 5. Finding verification (delegated refuter)

Before recording a finding as real, verify it with an **independent adversarial refuter** told to
**refute**, not assess. Delegate to a cheap external tier via the harness — batch a lane's findings
into ONE call (shared cached prefix) and **launch it in the background** per harness §c–d (an
`opencode run` can take >5 min — never run it in a short foreground timeout), then capture a
machine-checkable verdict:

```bash
timeout -k 15 780 opencode run \
  --dir <repoRoot> \
  --agent openspec-verifier \
  --model deepseek/deepseek-v4-flash \
  --format json \
  "Act as an offensive security researcher. Try to REFUTE each finding below: find a false premise,
   an alternative explanation, or a control that already stops the attack. Default to refuted if
   uncertain. Emit a '## Refutation' section and one 'VERDICT: <id> REAL|REFUTED' line per finding.
   Findings (lane-scoped, file:line): <inline the findings LAST>." \
  > /tmp/secaudit-refute-out.jsonl 2> /tmp/secaudit-refute-err.log < /dev/null \
  ; echo "EXIT=$?" > /tmp/secaudit-refute-out.exit
```

Post-process via the wrapper (never trust raw `opencode run` output — it exits 0 on silent
fallback); a backgrounded launch feeds the exit via the §d exit-file sentinel (`--exit-file`), a
synchronous one via `--exit $?`:

```bash
scripts/opencode_delegate.py \
  --phase secaudit-refute --agent openspec-verifier --model deepseek/deepseek-v4-flash \
  --out /tmp/secaudit-refute-out.jsonl --err /tmp/secaudit-refute-err.log \
  --exit-file /tmp/secaudit-refute-out.exit \
  --require-marker "## Refutation" --verdict-regex "VERDICT: \S+ (REAL|REFUTED)" --quiet
```

The **orchestrator forms its own read of each finding's crux BEFORE opening the refuter's verdict** —
the refuter's verdict is itself a claim to verify. Apply the verdict + finalize severity. The
refuter frequently adds a corroborating fact the auditor missed (e.g. that the service runs
`--workers 2`, making a race genuinely cross-process); if it discovers a *new* real defect during
refutation, file it as a new lead.

**Surface money/abuse tradeoffs — don't auto-fix them.** A confirmed finding that is a
monetization-integrity / abuse-ceiling / business tradeoff (e.g. a free-tier quota TOCTOU) is
SURFACED to the operator with a concrete recommended fix for ratify-or-accept — not unilaterally
changed (the abuse-ceiling vs. lock-contention vs. flaky-test-cost tradeoff is the operator's).
Data-exposure and authn/authz defects are fixed under the normal remediation path.

### 6. Cross-lane completeness critic

Before the verdict, run one pass over themes per-lane scoping can miss — checked as **themes, not
files**: auth middleware / CSRF / CORS (touch every route); revenue/entitlement integrity (spans
billing + quota); info/PII leakage (spans handlers + email + logging); supply-chain (touches the
whole app); outbound/SSRF surfaces. Record any theme-level defect as a finding.

### 7. Verdict

Write exactly one verdict to `output/security/<date>/security-verdict.md`:

- **`SECURITY: CLEAN`** — no generalizable findings (every lane's confirm-the-negatives recorded).
- **`SECURITY: FINDINGS-ROUTED`** — findings exist and were routed into the ratchet (step 8).
- **`SECURITY: ESCALATE`** — findings warrant a follow-up beyond this pass: a dynamic pen-test drill
  (running payloads at the live surface), a deploy-time edge audit, or chartering a deeper review.
  ESCALATE **recommends** the follow-up and takes **no** chartering action itself.

### 8. Close-out

1. **Ratchet routing.** For each generalizable finding, run the finding-closure-ratchet 3-question
   triage (real defect? → generalizable class? → detectable/freezable?) — **orchestrator judgment,
   never delegated** — and append one `knowledge/ratchet-log.md` line per qualifying class in the
   frozen format (`check:` > `test:` > `waiver:` > `open:` > `grandfathered`; frozen format in
   `specs/finding-closure-ratchet/spec.md`). A `doc-only` / accepted-by-design close STILL carries a
   ledger disposition (a `waiver:` with rationale) — never a silent prose close.
2. **Deploy-time deferral.** Lanes needing the live deployed edge (rate-limit efficacy through the
   real proxy/tunnel, TLS/HSTS, CORS/CSP as served, open-port surface) are recorded **deferred to
   deploy-time** with a pointer to where they run — never marked `CLEAN` from code inspection alone.
3. **Close liveness.** Remove (or mark resolved) the Active `knowledge/questions/INDEX.md` item that
   referenced this dossier once every non-deferred lane is dispositioned.

Remediation ships as ordinary OpenSpec changes citing finding IDs — never inside the audit.

---

## Recommended lane menu

Prune to what the repo actually has (record N/A lanes as excluded, step 2). Group lanes so each
group shares a file-set that caches once:

| Lane | Scope | Notes |
|---|---|---|
| **Identity & session** | authn, token/session (JWT alg-pinning, TTL, revocation), secrets/config, cookie flags, CSRF/CORS | HIGH — first-customer risk. Empirical-probe the crypto. |
| **Authz / IDOR-BOLA** | ownership on every id-bearing route; tenant isolation; mass-assignment | HIGH — the #1 SaaS vuln class. Dynamic user-A-vs-user-B tests where the app runs locally. |
| **Money / billing** | webhook signature (raw body), idempotency/replay, server-side price, customer↔user mapping, entitlement | HIGH where money exists. A hardened lane is a legitimate CLEAN. |
| **Data layer** | injection (confirm-the-negative on dynamic-clause builders), DB least-privilege, PII/secret in logs & error responses | Injection is usually confirm-negative; the real finds are info-leak and least-privilege. |
| **Frontend + supply-chain** | XSS/DOM sinks, client-side secrets, CSP; dependency CVEs with reachability triage | See supply-chain triage below. |
| **Business-logic / abuse** | quota/limit races, entitlement bypass, subscription-lifecycle abuse | A distinct lens over the route/billing file-sets. |
| **Deploy / edge** (DEFER) | rate-limit efficacy through the real edge, TLS/HSTS, CORS/CSP as served, open ports | Needs the live deployed edge → deferred to deploy-time, never CLEAN from code. |

## Supply-chain reachability triage

Advisory severity labels are near-useless without reachability triage. For every dependency
advisory, classify **shipped-runtime vs. dev/build-only vs. dead-code-eliminated** BEFORE ranking by
severity — most CRITICAL/HIGH counts on a typical repo are dev/build tooling that never ships. Even a
shipped-dep HIGH needs usage-reachability (a browser SPA with no proxy config doesn't reach an
axios proxy-auth vector → "HIGH by advisory, MED effective"); record BOTH the advisory severity and
the effective-in-this-app severity. Activating a lockfile-driven scanner (osv-scanner) is a
**tool-choice** decision, not a mechanical step — do not auto-generate a lockfile that violates a
repo's manifest-singularity rule (prefer a clearly-generated `.lock`, leave the choice to the
operator). When no SAST covers a frontend language, an **exhaustive** (not sampled) injection-sink
grep over the small frontend is a legitimate substitute — but record the manual-coverage caveat.

## Recommended per-repo custom detectors (graduation candidates)

The ceremony ships no per-repo detector code (they are repo-shaped), but these **archetypes** convert
one-time findings into permanent deterministic checks and pre-build a `check:`-tier ratchet
disposition — build them per repo when the shape fits:

- **Route-authz snapshot + auth-coverage gate** — per endpoint: method+path, auth-dependency present?,
  does the handler's SQL filter by the owner key? A gate FAILs if a non-allowlisted route lacks auth
  or a user-scoped mutation omits the owner filter. Key the exempt allowlist on **real AST handler
  names discovered from source**, never on documentation shorthand.
- **SQL-string rule** (f-string / `.format()` / `%` interpolation into SQL). A single Semgrep pattern
  can't separate a safe internal-constant interpolation from a dangerous request-derived one without
  taint mode — ship SQL-string rules **report-only** with a triaged known-safe baseline, or invest in
  taint mode with repo-defined request sources; don't pretend a single-pattern rule is a clean gate.
- **Error-leak rule** (`str(e)`/`repr(e)`/traceback reaching a client response body) and
  **placeholder-config rule** (dev-placeholder defaults like `dev-secret…`/`changeme`) — precise,
  high-signal, but gate them only AFTER the underlying lead is remediated (gating on an open finding
  reds the floor).

## Honest limits

The deterministic floor catches a narrow slice (committed secrets, known-CVE deps, a handful of SAST
patterns); the judgment lanes carry the rest — data-flow reasoning, auth/session logic, business-abuse
state machines — which no scanner reaches. This is a **white-box adversarial review**, not a network
pen-test: it proves a concrete exploit path against the code and produces adversarial regression
tests, but running payloads at a live edge (rate-limit, TLS, open ports) is the deferred deploy-time
drill the `ESCALATE`/deploy-edge lane points to. The audit is a first pass, not a substitute for a
professional pen-test.

## Guardrails

- **Pull-only / never auto-run.** Do NOT wire this skill into session boot, `AGENTS.md`, or any hook,
  and do NOT let it gate any commit / verify / CI / lifecycle step.
- **Audit-then-fix.** Modify no product code from this skill; remediation is a later OpenSpec change.
  The sole exception is the fix-now criterion (audit-instrument hardening only).
- **Never send secrets to an external model** — exclude `.env`/secrets/keys/PII from every delegated
  prompt.
- **Surface, don't decide, money/abuse tradeoffs** — recommend a fix and route to the operator; fix
  data/auth defects under the normal path.
- **Severity/verdict finalized by the orchestrator only** — a delegated refuter drafts; the
  orchestrator confirms after forming its own read of the crux.
- **Ratchet triage is orchestrator judgment**, never delegated to a mechanical executor.
- **Do not edit** `scripts/checks.py`, `scripts/facts.py`, or any detector from this skill — it is a
  ceremony over the detectors, not an editor of them.
