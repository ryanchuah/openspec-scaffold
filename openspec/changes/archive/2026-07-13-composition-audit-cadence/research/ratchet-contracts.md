# Ratchet contracts digest — for OW-6 (composition-audit-cadence)

Source: `openspec/changes/lesson-check-ratchet/` (frozen, **NOT YET APPLIED** — confirmed on
disk: no `scripts/repo_lint.py`, no `_check_ratchet_log` in `scripts/knowledge_lint.py`, no
`knowledge/ratchet-log.md`. `notes.md:67-73`: "PAUSED AT APPLY per operator instruction."
This digest extracts frozen spec-level contracts, not verified implementation.) All quotes
verbatim, `file:line` cited.

---

## 1. Ratchet ledger — file, format, dispositions, closure rule

**File (single home):** `knowledge/ratchet-log.md` (`design.md:39`,
`specs/finding-closure-ratchet/spec.md:16`).

**Entry format (verbatim registry-line, one per finding-class):**

```
- **YYYY-MM-DD** · <class-slug> · <disposition> — <essence / source refs>
```
(`design.md:44-45`; restated with the slug pinned to kebab-case at `tasks.md:60-61` and
`specs/finding-closure-ratchet/spec.md:47-49`)

**Class slug:** kebab-case, names the finding CLASS not the instance (e.g.
`ratchet-ledger-format`, `delegation-timeout-budget-drift`). Lint flags a non-kebab slug
(`specs/finding-closure-ratchet/spec.md:55`).

**Disposition taxonomy — all five values (table verbatim, `design.md:49-55`):**

| Disposition | Form | Lint verification |
|---|---|---|
| check | `check:<pointer>` | pointer resolves (see D3) |
| frozen test | `test:<path>[::<name>]` | file exists; `::<name>` appears in file text |
| waiver | `waiver:review-by YYYY-MM-DD` | reason present; valid ISO date; not past |
| open | `open:since YYYY-MM-DD` | valid ISO date; flagged when older than age threshold |
| grandfathered | `grandfathered` | format only |

Meanings: `check:` = enforcing deterministic check exists, two pointer forms —
`check:checks/<file>` (per-repo invariant) or `check:<script>.py::<name>` (named function in
a scaffold script, verified by grepping the name) (`design.md:65-67`). `test:` = frozen
regression-test linkage; SHOULD include `::<name>` — "a bare file path verifies only file
existence, which is weak for a suite file" (`design.md:61-63`). `waiver:` = domain-judgment
class, "carries a reason plus a re-review trigger so they cannot silently become the new
write-only memory" (`proposal.md:25-26`). `open:` = "temporary state for 'fix shipped,
enforcement deferred' so archive is never blocked ... 30-day age flag ... stops it from
becoming a parking lot" (`design.md:68-70`). `grandfathered` = "legal only for pre-ratchet
legacy lessons" (`design.md:71`), distinguishes "reviewed and deferred" from "never triaged"
(`proposal.md:27-28`).

**Preference ordering (normative):** check > test > waiver (`design.md:68`,
`proposal.md:19-21`).

**Closure rule (SHALL, verbatim):**

> A generalizable finding (a defect class that could recur in sibling code, not a one-off
> instance) SHALL NOT be treated as closed until `knowledge/ratchet-log.md` records exactly
> one disposition for its class: an enforcing deterministic check (`check:`), a frozen
> regression-test linkage (`test:`), an explicit waiver (`waiver:review-by YYYY-MM-DD` with
> a reason), a temporary `open:since YYYY-MM-DD` state, or `grandfathered` (legal only for
> pre-ratchet legacy lessons). The normative preference ordering is check > frozen test >
> waiver.
(`specs/finding-closure-ratchet/spec.md:15-21`)

**Dangling-pointer / staleness enforcement (SHALL, verbatim):**

> The deterministic knowledge linter SHALL verify that every `check:` and `test:`
> disposition points at an artifact that exists: the pointed-at file path must exist, and
> when a `::<name>` suffix is present it must appear textually in the pointed-at file (a
> bare file path is legal and verifies file existence only). Waivers past their
> `review-by` date and `open` entries older than the configured age threshold (default 30
> days, configurable as `ratchet_open_max_age_days` under the `[knowledge_lint]` table of
> `checks.toml`) SHALL be flagged. `grandfathered` entries receive format validation only —
> no liveness checks.
(`specs/finding-closure-ratchet/spec.md:66-74`)

**Scope note:** "Ledger *format* is scaffold-defined; ledger *content* is per-repo"
(`proposal.md:32`) — never manifest-synced (`design.md:189`, `proposal.md:104`).

**Bootstrap entries (literal, verbatim, `design.md:174-178`, mandated by `tasks.md:84-88`):**

```
- **2026-07-10** · ratchet-ledger-format · check:scripts/knowledge_lint.py::_check_ratchet_log — self-referential bootstrap; the ledger's own format check.
- **2026-07-10** · delegation-timeout-budget-drift · check:scripts/scaffold_lint.py::budget-agreement — pre-existing exemplar of lesson→check conversion (mechanize-invariants, 2026-07-02).
- **2026-07-10** · repo-invariant-runner-contract · test:scripts/test_repo_lint.py::test_stops_on_first_infra_failure — the runner's load-bearing fail-loud behavior, pinned by name.
```

---

## 2. Ingestion interface — how a finding gets INTO the ledger

No API — entries are appended as text by an AGENT at one of exactly two lifecycle gates,
after a bounded 3-question triage (D4, verbatim, `design.md:147-153`):

```
Q1  Real defect (not noise/env)?                 no → stop (no entry)
Q2  Generalizable class (sibling could recur)?   no → stop (point fix suffices)
Q3  Mechanically detectable or test-freezable?
      yes → disposition check: / test: (artifact ships with the fix; open: if deferred)
      no  → waiver:review-by <date> — <why domain-judgment-only>
```

**Gate 1 — archive close-out** (`openspec-archive-change` skill, Step 6, primary's review):

> before committing, scan the change's `notes.md`/`review-log.md` for found-and-fixed
> defects; apply the three questions; append ledger line(s). The **primary** does this, not
> the archive-executor — it is exactly the generalizability judgment the mechanical executor
> cannot make ... the enforcing artifact (check/test) was already built during apply/verify
> when the disposition is `check:`/`test:`.
(`design.md:158-164`)

Placement pinned: "insert the ratchet-triage step as a new sub-bullet BETWEEN the 'Quality
check' block and the 'Lint before committing' bullet (so `knowledge_lint` then catches any
ledger-format error the triage just introduced)" (`tasks.md:105-108`).

**Gate 2 — run-audit triage** (`run-audit` skill, Step 3, Triage):

> findings judged real get the same three questions; entry appended alongside the existing
> audit-log line ceremony.
(`design.md:163-165`; spec scenario at `specs/finding-closure-ratchet/spec.md:124-127`)

**Required fields per entry:** date, kebab class-slug, disposition token, essence text
(free-text rationale/source refs). No schema beyond the `·`-separated positions.

**Actor constraint (SHALL, verbatim):** "The triage is performed by the orchestrating agent
(judgment work), never delegated to the mechanical archive-executor, and never blocks on
building a detector" (`specs/finding-closure-ratchet/spec.md:113-115`).

**Non-qualifying findings (SHALL, verbatim):** "Findings judged not-real (Q1 = no) or
not-generalizable (Q2 = no) SHALL produce no ledger entry — the ledger holds classes, not
noise or one-offs" (`specs/finding-closure-ratchet/spec.md:112-113`).

---

## 3. Per-repo invariant framework — registration mechanics

**Directory contract:** flat `checks/*.py` glob, no recursion, sorted filename order — the
sibling of `data_lint.py`'s `checks/*.sql` convention, same directory, disjoint extensions
(`design.md:99-104`, `specs/repo-invariant-checks/spec.md:16-19`).

**Check-file contract (verbatim):** "Each check file is one standalone script implementing
one invariant: invoked as `<python> <file> <repo-root>` in a subprocess, it prints a JSON
array of findings `[{"path", "line", "message"}]` to stdout (empty array = pass) and exits
0." (`specs/repo-invariant-checks/spec.md:19-21`) — "~10 lines of stdlib Python" for a
minimal real check (`design.md:110`).

**Runner:** new `scripts/repo_lint.py` (stdlib-only). CLI: `--checks-dir` (default `checks`),
`--json` (default `repo_lint.json`), `--timeout` (default 120s/check), `--max-sample`
(default 5). Exit 0 clean / 2 findings / 3 infra — "byte-consistent with `data_lint.py`'s
contract" (`design.md:111-115`, `tasks.md:9-19`).

**Fail-loud (SHALL, verbatim):** "any check that exits nonzero, prints unparseable stdout,
or exceeds the per-check subprocess timeout ... as an infrastructure failure: it stops
immediately at the FIRST such failure (no later sorted check runs) and exits 3. A missing or
empty `checks/` directory (no `*.py`) is not an error: the runner reports 'no checks
configured' and exits 0." (`specs/repo-invariant-checks/spec.md:37-42`)

**`checks.py` registration (SHALL, verbatim):** "`scripts/checks.py` SHALL register
`repo-lint` as a floor-tier, check-family delegating entry, auto-enabled when `checks/*.py`
exists (trigger-based, like `data-lint`'s `checks/*.sql` trigger) and overridable via
`[checks.repo-lint] enabled`. Invocation follows the data-lint integration pattern:
`checks.py` calls `repo_lint.main()` in-process with `--json` and `--checks-dir` (first
`paths` entry; a second entry is an explicit INFRA-FAIL config error) and reads the
resulting JSON artifact; the runner's findings are NOT merged into the aggregate
`findings.json`." (`specs/repo-invariant-checks/spec.md:57-63`)

`_autodetect_defaults()` gets a NEW separate `*.py` glob (does not reuse the `*.sql` boolean
used for `data-lint`) (`tasks.md:39-41`). JSON artifact `repo_lint.json`:
`generated_by` + per-check `{name, status, findings, sample}` — `sample` capped, `findings`
holds full count (`design.md:113-115`).

**Trust model:** check files are "repo-trusted code, same class as `[checks.custom.*]`
commands" — writes documented as check-only-by-convention, not sandboxed
(`design.md:141-143`, `specs/repo-invariant-checks/spec.md:78-82`).

**Admission bar (Tricorder criteria, verbatim intent):** "near-zero false positives and an
obvious, actionable fix ... noisy checks tuned or demoted to a ledger waiver"
(`specs/repo-invariant-checks/spec.md:83-85`). Target scale (D4): "~5–15 invariants grown
from incidents," "not a general lint suite" (`specs/repo-invariant-checks/spec.md:86-87`).
Graduation path if outgrown: external engine (e.g. ast-grep) via `[checks.custom.*]`.

**Not synced:** `checks.toml` content and `checks/` contents are per-repo, NOT
manifest-synced (`design.md:189-190`).

---

## 4. Lint / enforcement additions

**New check:** `_check_ratchet_log(root)` in `scripts/knowledge_lint.py`, guarded on
`knowledge/ratchet-log.md` existence — absent file = silently clean, same guard shape as
`_check_audit_log` (`design.md:81-83`, `tasks.md:57-59`). Registered directly after
`_check_audit_log` in the run sequence (`tasks.md:71-72`).

**What it flags** (`tasks.md:59-70`): malformed line format; unknown/invalid disposition
keyword; non-kebab slug; invalid ISO calendar dates (`2026-13-01` rejected, not silently
skipped — `design.md:57-58`); dangling `check:`/`test:` pointer (file missing or `::<name>`
absent from file text); stale waiver (`review-by` past); aged `open` entry (past threshold).
`grandfathered` gets format validation only, no liveness check.

**Canonical-map / ephemeral integration:** `knowledge/ratchet-log.md` added to BOTH
`CANONICAL_MAP` (orphan/duplicate coverage) AND `EPHEMERAL_PATHS` — "so prose citations of
the ledger in a repo that has not adopted it yet are not flagged as broken citations"
(`design.md:85-87`, `tasks.md:72`).

**Threshold config (pinned):** `ratchet_open_max_age_days`, default **30**, read from
`checks.toml` `[knowledge_lint]` — "the same configuration surface as
`_check_untriaged_age`'s `untriaged_max_age_days`" (`design.md:59-61`, `tasks.md:66-70`).

**`scaffold_lint.py` explicitly NOT touched** — golden-source-only; enforcement propagates
via `knowledge_lint.py` instead (`design.md:87-88`).

**Semantic-drift residue (NOT covered by deterministic lint):** v1 verifies pointer
LIVENESS only, not that the artifact still exercises the class:

> Semantic drift ("test exists but no longer exercises the class") is delegated to the
> existing `knowledge-drift-review` LLM pass, whose scope note gains one line telling it to
> spot-check ratchet pointers.
(`design.md:93-97`; concretely `tasks.md:116-120` adds a Step-2 bullet to
`.claude/skills/knowledge-drift-review/SKILL.md`: "spot-check `knowledge/ratchet-log.md`
`check:`/`test:` entries whose enforcing artifact (file/symbol) still exists but no longer
exercises the recorded defect class")

---

## 5. Extension points — future consumers (OW-5/OW-6)

The design explicitly anticipates OW-6 as a downstream consumer, not something it builds:

> Future audit skills (OW-5 correctness-audit, OW-6 composition-audit) route into this same
> interface; they are not built here.
(`proposal.md:52-53`; restated as Out-of-Scope at `proposal.md:72-73`)

> [Downstream repos never adopt] → ... mitigations: framework arrives on next sync, named
> seed invariants above, and OW-5/OW-6 route findings into the ledger by construction once
> built.
(`design.md:210-212`, Risks/Trade-offs)

> The future `correctness-audit` skill (OW-5) and composition-audit (OW-6) will route their
> findings into this same interface — this change defines the interface; it does not build
> those skills.
(`explore-brief.md:68-70`)

**Interpretation:** the "interface" is the two-gate triage (archive-review / run-audit-triage)
producing a ledger line via the 3-question test — NOT a distinct API or hook named for
composition-audit specifically. Nothing in `tasks.md` or either spec names a dedicated
"audit close-out" entry point for a future skill; the design only generalizes run-audit's
Step-3 triage as the pattern to mirror. OW-6 must decide: (a) run as a mode within
run-audit's existing cycle and inherit its Step-3 triage automatically, or (b) ship as its
own skill and replicate the same triage-then-append contract as its own close-out step. The
ratchet change is silent on which.

---

## 6. Config keys / exit codes / budgets pinned

- Ledger path: `knowledge/ratchet-log.md` (fixed, single home) — `design.md:39`
- `checks.toml [knowledge_lint].ratchet_open_max_age_days` — default `30` —
  `design.md:59-61`
- `checks.toml [checks.repo-lint].enabled` (bool override) —
  `specs/repo-invariant-checks/spec.md:61`
- `checks.toml [checks.repo-lint].paths` — first entry = checks dir; second = INFRA-FAIL —
  `design.md:117-119`
- `repo_lint.py` CLI defaults: `--checks-dir checks`, `--json repo_lint.json`,
  `--timeout 120`, `--max-sample 5` — `design.md:111-114`
- `repo_lint.py` exit codes: `0` clean / `2` findings / `3` infra — byte-consistent with
  `data_lint.py` — `specs/repo-invariant-checks/spec.md:40-42`
- `checks.py` registry entry: tier `floor`, kind `delegate`, family `check`, placed directly
  after `data-lint` — `tasks.md:37-39`
- Target invariant scale (D4): ~5–15 per repo, grown from incidents —
  `specs/repo-invariant-checks/spec.md:86-87`
- Bootstrap ledger date: `2026-07-10` — `design.md:174-178`

---

## Summary for OW-6 authors

1. Closing a finding permanently means a line in `knowledge/ratchet-log.md`:
   `- **YYYY-MM-DD** · <kebab-slug> · <disposition> — <essence>`, disposition one of
   `check:`, `test:`, `waiver:review-by`, `open:since`, `grandfathered`.
2. Entries are appended by an agent applying the 3-question triage — judgment work reserved
   for the orchestrating agent, never a mechanical executor.
3. OW-6 is named as an anticipated consumer but has no dedicated hook defined for it yet —
   it must either piggyback on run-audit's Step-3 triage or define an equivalent
   triage-then-append close-out step of its own.
4. lesson-check-ratchet is frozen but UNAPPLIED as of this extraction — verify apply status
   before depending on the mechanism being live on disk.
