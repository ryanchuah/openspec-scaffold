# Consolidation Plan — scaffold hardening + propagation (2026-06-16)

**Status:** holistic MAP, not a change. **Supersedes** `openspec/changes/scaffold-sync`.
**Delivery shape (operator-chosen 2026-06-16):** ONE holistic design (this doc) → an **ordered
family of small changes** (W1…W6), each independently reviewable and applied in sequence.
**Scope cut** (which findings land in which change, and which defer) is decided **per-change at
propose time** — this doc captures *every* finding so the cut line can be drawn later with full
context, but commits to none.

**Sources folded in (read these before proposing any W):**
- `openspec/changes/scaffold-sync/` — proposal.md, design.md (D1–D10), specs/scaffold-sync-mechanism/spec.md, review-log.md (7 deepseek rounds), explore-brief.md
- `openspec/changes/scaffold-sync/principal-review.md` — principal review of scaffold-sync (B1/B2/M-1/M-2 + minors)
- `ai-docs/workflow-audit-2026-06-16.md` — principal audit of the whole workflow (§A–§E)
- `ai-docs/decisions.md`, `ai-docs/open-questions.md` — durable decisions + the BLOCKING hook-wiring smoke

> Every finding below is a **claim to re-confirm from disk** at propose time, not gospel — that is the
> discipline the audit itself preaches.

---

## 1. The reframe — there are TWO single-sourcing problems, not one

scaffold-sync and the audit's biggest finding (C1) look like the same problem. They are not.

```
  (a) CROSS-REPO single-sourcing            (b) WITHIN-SCAFFOLD single-sourcing
      = scaffold-sync's job                     = audit C1 / C2 / C4

   scaffold/_convergence.py                  ┌─ openspec-apply/SKILL.md ─┐
        │  copy                              │  ...delegation harness... │ ← copy
        ├──────▶ extrends/_convergence.py    ├─ openspec-verify/SKILL.md │ ← copy
        └──────▶ psc/_convergence.py         ├─ openspec-propose/SKILL.md│ ← copy
                                             └─ openspec-archive/SKILL.md│ ← copy
   "make a file byte-identical               "the SAME content pasted across
    across repos, then dumb-copy it"          4 files INSIDE one repo"
```

scaffold-sync makes files identical **across repos** and copies them. It does nothing about content
duplicated **across files within** the scaffold — and (audit C3) it would faithfully propagate all
four drifted copies of the delegation harness to each downstream repo. So the dominant maintainability
liability (C1) survives scaffold-sync untouched. **That is why these are consolidated:** you do not
build a propagation pipe and then pump duplicated content through it.

---

## 2. The ordering insight — propagation is a SNAPSHOT event

scaffold-sync's "Why" is urgency: 4 changes are inert, re-sync debt compounds, propagate **now**. The
audit changes the sequencing logic. The one-time propagation snapshots whatever is in the shared files
at that moment.

```
   ┌──────────────────────────────────────────────────────────────────────┐
   │ W0  BLOCKING hook-wiring smoke (audit E2 + A5 + scaffold-sync exit)    │
   │     gates TRUST in every hook · pure verification · gated session      │
   └───────────────────────────────┬──────────────────────────────────────┘
                                    ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │ W1  Fix the MECHANISM (scaffold-sync, de-gold-plated)                 │
   │     exit-2 hook (B1) · DROP header subsystem (M-1 ⇒ kills B2) · tests  │
   │     HARD PREREQ: B2 corrupts AGENTS.md on the SECOND sync — so you     │
   │     cannot iterate (propagate-then-fix) until this lands.              │
   └───────────────────────────────┬──────────────────────────────────────┘
                                    ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │ W2  Within-scaffold DEDUP   (C1 harness→1 doc · C2 rules · C4 · B3)    │
   │     changes the MANIFEST + shrinks the skills → do before final manifest│
   ├──────────────────────────────────────────────────────────────────────┤
   │ W3  CORRECTNESS  (_convergence.py A1–A4 · test-gate.sh cwd A5)         │
   │ W4  MISSING GATES (E1 simplify · D-i RENAMED · B2/D-ii tier · E3 sec)  │
   │ W5  CLEANUP (B1 happy-path · D-iii header · E4 rollback · E5 smoke)    │
   │     all edit scaffold-managed files → land BEFORE the snapshot         │
   └───────────────────────────────┬──────────────────────────────────────┘
                                    ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │ W6  ONE-TIME PROPAGATION → extrends + psc-monitor (the snapshot)       │
   └──────────────────────────────────────────────────────────────────────┘
```

**The honest counter-tension:** scaffold-sync's whole value prop is that re-sync is cheap (one
command). If that holds, "fix before snapshot" is an *optimization*, not a law — you could propagate
the baseline now and push fixes later. **Two things pin the ordering anyway:**
1. **W0 + W1 are true hard prereqs.** The header non-idempotency bug (review B2) breaks on the *second*
   sync, so you cannot safely iterate until W1 cuts the header. And until W0 proves the hook fires +
   exit-2 blocks, you cannot trust either the commit-test-gate or the new scaffold guard.
2. **W2 is manifest-changing.** Extracting the harness to one doc shrinks the 4 skills and adds a new
   shared file → the manifest changes. Doing W2 before W6 avoids syncing fat skills then re-syncing thin
   ones. (Preference, not a gate — the working mechanism makes the re-sync cheap.)

W3/W4/W5 are "land before W6 to snapshot once" — preferences enabled by the cheap re-sync, not gates.

---

## 3. scaffold-sync supersession map

scaffold-sync is **superseded, not extended.** It stays on disk (FROZEN) only as source material for
W1/W6; delete it once W1+W6 land.

### What the audit OVERRIDES (prior proposed decisions that change)

| scaffold-sync decision | Override | Source |
|---|---|---|
| D4 — DO-NOT-EDIT header subsystem (7 format rules + strip-invert in `--check`) | **Cut entirely.** Advisory text; real enforcement is the hook. Drags in ~half the script + the AGENTS.md special case (the B2 bug) + an untested insert/strip-inverse invariant. | principal-review M-1; passed 7 deepseek rounds but over-engineered |
| D5 — guard `scaffold_check.py` ends `sys.exit(1)` | **→ `sys.exit(2)`.** Claude Code PreToolUse: exit 2 blocks; other non-zero is non-blocking → as written the guard is a no-op. | principal-review B1 |
| AGENTS.md header reconstruction reads header back out of target | **Disappears with D4 cut** — this is the root of the B2 non-idempotency (second sync ⇒ two header lines). | principal-review B2 |
| "single-source the war-story + model-matrix" (scope) | **Insufficient.** Must also single-source the delegation harness (C1), the "tasks.md=apply-only" rule, the "no counts" rule, the web-research convention (C2), and add a .claude/.opencode body-agreement guard (C4). → that is W2. | audit C3 |
| D9 — phase order: build tooling, then propagate | **Re-sequence** per §2: fix mechanism (W1) + dedup (W2) + correctness/gates (W3–W5) BEFORE the one-time propagation (W6). | audit §2 ordering |

### Spec impact (W1 rewrites the capability, does not inherit it verbatim)

`specs/scaffold-sync-mechanism/spec.md` bakes the header subsystem deep in. Cutting D4 means W1 must:
- **Delete** requirement `do-not-edit-headers` + scenarios `header-format-by-file-type`,
  `scaffold-source-lacks-header`, `check-strips-header-before-diff`.
- **Collapse** `check-mode-reports-drift` to a plain byte-compare (trivially correct once no header).
- **Tighten** `pre-commit-guard-warns-on-scaffold-managed-edit` → "SHALL exit **2**" (was "non-zero").
  Keep `check-exits-nonzero-on-drift` at **exit 1** — `--check` is a diagnostic CLI, not a blocking hook.
- **Add** scenarios for `test_sync_scaffold.py` (review M-2): idempotency (sync twice → `--check` still 0),
  tail-preserved-verbatim, no-`## Project context` case, missing-anchor abort, scaffold-tail-invariant abort.

### What SURVIVES (folds into W1 mechanism + W6 propagation)

- **Option Y** (war-stories out → byte-identical files → dumb copy; no template engine/submodule) — keep.
- **AGENTS.md span-replace** (D3) — genuinely necessary (per-repo project context + psc-monitor tail). Keep.
- **D10 pre-execution drift-check-then-STOP** before any mutation — keep; it is the apply safety net.
- **Self-managed manifest** (manifest lists itself; excludes volatile state) — keep.
- **D7 settings.json manual hook insertion · D8 per-repo `scripts/test-cmd` creation** — keep (→ W6).
- Drift table (extrends 238 / psc-monitor 646 lines, anchors as described) — verified accurate; keep.

### Minor review items to carry into W1/W6

- M1 (guard is PreToolUse-only → operator/opencode commits bypass it): document the limitation, or install
  a real `.git/hooks/pre-commit`. Decide at W1 propose.
- M2 (tail detection is first-match fragile; could mis-slice psc-monitor's 411-line appendix): lean on the
  manual diff in W6; confirm appendix byte-identical post-sync.

---

## 4. The work-item family (suggested tiers — operator confirms each at propose time)

| W | Name (suggested) | What it folds | Suggested tier | Gate role |
|---|---|---|---|---|
| **W0** | hook-wiring smoke | audit E2 (BLOCKING) + A5 cwd + verify scaffold guard exit-2 + E5 opencode skill-discovery smoke | gated verification task (not a lifecycle change) | **HARD PREREQ** — gates trust in every hook |
| **W1** | fix-sync-mechanism | review B1 (exit-2), M-1 (cut header), M-2 (unit tests), B2 (resolved by cut); spec rewrite; M1/M2 minors | MEDIUM | **HARD PREREQ** for repeated sync |
| **W2** | dedup-scaffold | audit C1 (harness→1 referenced doc), C2 (rules ×3–5), C4 (.claude/.opencode body guard), B3 (timeouts) | MEDIUM→COMPLEX (biggest of the family) | manifest-changing → before W6 |
| **W3** | convergence-fixes | audit A1 (attempt ceiling), A2 (test-scoped signature/key), A3 (derive edits from `git diff`), A4 (signature-quality tests), A5 (test-gate.sh cwd) | MEDIUM | before W6 (preferred) |
| **W4** | lifecycle-gates | audit E1 (simplify/code-review in verify), D-i (RENAMED in archive-executor), B2+D-ii (tier-scale verify; SMALL-tier gate behavior), E3 (security-review for app-code) | MEDIUM | before W6 (preferred) |
| **W5** | cleanup | audit B1 (apply/verify happy-path-first), D-iii (spec header normalize), E4 (rollback lifecycle branch), E5 (version-pin smoke if not in W0) | SMALL→MEDIUM | before W6 (preferred) |
| **W6** | propagate-baseline | scaffold-sync one-time propagation (extrends + psc-monitor); D7 settings.json; D8 test-cmd; D10 drift-check; manual-diff confirm (M2) | MEDIUM | **LAST** — the snapshot |

**Apply order:** W0 (anytime, gates reliance) → W1 → W2 → {W3, W4, W5} → W6.

---

## 5. Findings ledger — every finding mapped (nothing dropped)

In/out of the final scope is **TBD at propose time** (operator chose "let the design decide"); this
ledger only guarantees nothing is lost.

| Finding | Sev | Folds into | Note |
|---|---|---|---|
| review B1 — guard exits 1 not 2 | 🔴 | W1 | exit-2 only on the hook helper |
| review B2 — AGENTS.md header non-idempotent | 🔴 | W1 | killed by M-1 cut |
| review M-1 — header subsystem over-engineered | 🟠 | W1 | cut entirely |
| review M-2 — no unit tests for span-replace | 🟠 | W1 | add `test_sync_scaffold.py` |
| review M1/M2/M3 minors | 🟡 | W1/W6 | guard scope · tail fragility · sequencing |
| audit A1 — no attempt ceiling | 🟡 | W3 | oscillating failure escapes as wall-clock timeout |
| audit A2 — whole-output signature | 🟡 | W3 | scope to failing test's section |
| audit A3 — (b) relies on flash `--editing` | 🟡 | W3 | derive from `git diff --name-only` |
| audit A4 — path-strip too aggressive | 🟡 | W3 | false STOP; add signature-quality tests |
| audit A5 — test-gate.sh cwd no-op | 🟡 | W0 + W3 | smoke proves it; code fix resolves it |
| audit B1 — apply/verify bury happy path | 🟡 | W5 | happy-path-first restructure |
| audit B2 — verify not tier-scaled | 🟡 | W4 | SMALL pays full 3-pass cost |
| audit B3 — timeout magic numbers ×5 files | 💡 | W2 | duplication symptom |
| audit C1 — delegation harness copy-pasted ×4 | 🟠 | W2 | largest liability; safety-critical drift |
| audit C2 — rules restated ×3–5 | 🟡 | W2 | tasks-rule · model-matrix · no-counts · web-research |
| audit C3 — scaffold-sync dedups only 2/5 | 🟡 | drives W2 | the reason W2 exists |
| audit C4 — .claude/.opencode bodies, no guard | 🟡 | W2 | principle already applied in verify-multimodel-gate |
| audit D-i — archive-executor drops RENAMED | 🟡 | W4 | add RENAMED to both bodies |
| audit D-ii — phase-gate/verify vs SMALL undefined | 🟡 | W4 | resolve in Change-tiers |
| audit D-iii — spec headers inconsistent | 💡 | W5 | normalize in sync-specs path |
| audit E1 — NO simplicity/quality gate | 🟠 | W4 | invoke `simplify`/`code-review` in verify |
| audit E2 — hook wiring unverified (BLOCKING) | 🟠 | W0 | gates everything |
| audit E3 — no security gate | 🟠 | W4 | `security-review` for auth/data/external |
| audit E4 — no rollback lifecycle branch | 💡 | W5 | "archived change was wrong" path |
| audit E5 — dual-harness version-pin, no smoke | 🟡 | W0/W5 | opencode still cross-loads `.claude/skills`? |
| scaffold-sync core (Option Y, span-replace, D10, manifest) | — | W1+W6 | survives |

---

## 6. Open decisions deferred to propose time

1. **Scope cut line.** Which W's ship and which defer. Natural cut = the audit's own priority order
   (W0, W1, W2/C1, W3, W4/E1, W6 first; B1/E3/E4/E5/D-iii as a later pass).
2. **propagate-now vs fix-first** for the W3/W4/W5 content (not W1/W2, which are pinned). Cheap re-sync
   makes both viable; pick per the urgency of the 4 inert changes vs. snapshotting clean.
3. **Change names** for W1…W6 (suggested above; operator confirms).
4. **W0 mechanics** — the hook-wiring smoke needs a *gated Claude session*; cannot be done from a
   non-gated session. Procedure: `docs/test/commit-gate-smoke/`.

---

## 7. Risks of the consolidation itself

- **Blast radius.** The family touches `_convergence.py`, `test-gate.sh`, all 7 skills, 4 agents,
  AGENTS.md, new sync tooling, and 3 repos. The decomposition (small changes + per-change review) is
  the mitigation — do NOT collapse back into one monolithic apply (that is the over-engineering the
  audit indicts, and it would be executed by flash with no simplify gate yet — E1).
- **Flash executor.** Each W is implemented by deepseek-flash. Keep each W small enough for one review
  pass; W2 (the biggest) may need to split (harness vs rules vs body-guard).
- **Re-litigation guard.** scaffold-sync's deepseek rounds settled many micro-decisions (review-log).
  The audit overrides only the five in §3 — do not reopen the rest (span anchors, drift-check loop
  source, settings.json shape, etc.).
- **W0 is a hard gate.** Until the live smoke passes, every downstream guarantee that rests on the
  hooks (commit-test-gate AND the scaffold guard) is unproven. Do not rely on either before W0.

---

## 8. Next step (phase gate — do not auto-advance)

This is the explore/design map only. When ready, the operator says **"propose W0"** (or **"propose W1"**)
and the propose skill runs in the scaffold repo for that single change — re-confirming the findings it
touches against disk first. Per the tier-confirmation gate, each W's tier + plan is confirmed before any
execution.
