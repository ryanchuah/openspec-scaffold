# Handoff — propagate scaffold → extrends

**Written:** 2026-07-15, immediately after propagating to psc-monitor.
**For:** the next session that runs `/propagate-scaffold ../extrends`.
**Scaffold source state:** `main` @ `c8d344a` (all four commits below must be present).

This handoff front-loads what the psc-monitor propagation learned so extrends does not
rediscover it. Follow the `propagate-scaffold` skill as the authoritative procedure; this
doc is the extrends-specific overlay + the lessons log. **Nothing here overrides the skill's
load-bearing rule: never delete or bury downstream information — reconcile additively.**

---

## 0. extrends is FURTHER behind than psc-monitor was — expect a big sync

| | psc-monitor (just done) | extrends (this handoff) |
|---|---|---|
| Last sync | `3bafbed` 2026-07-13 | **`e604990` 2026-07-05** (≈10 days older) |
| Boot surface | 109,596 B | **119,527 B** (bigger — `decisions/INDEX.md` alone is 53 KB) |

extrends missed even more scaffold history (the full wave-2 batch OW-1…OW-16, the audit
skills, the deterministic archive/apply-delta + repo-lint + boot-surface + freeze-check +
opencode-delegate tooling, finding-closure-ratchet, etc.). The `--check` MISSING/DIFFERS
list will be long and the per-repo knowledge sweep larger. Budget accordingly.

## 1. Two friction items are ALREADY FIXED upstream — extrends gets them for free

These bit psc-monitor mid-sync and were fixed in the golden source; extrends receives the
fixed files, so it should NOT re-hit them (verify, don't assume):

- **F3 — isort I001 on `test_apply_delta_spec.py`.** extrends HAS a top-level `checks/`
  package (SQL invariants), the exact trigger. But scaffold commit `efdc1fd` added the
  `# noqa: E402, I001` guard, so the synced file is already lint-robust. After sync, still
  run `ruff check .` to confirm. (Only `checks` collides with a scaffold local-import module;
  extrends' other top-level dirs — `src config eval alembic …` — don't.)
- **F5 — `opencode_delegate.py` "Permission denied".** Scaffold commit `c8d344a` marked it
  `100755`; `sync_scaffold.py` uses `shutil.copy2` (preserves mode), so extrends' copy arrives
  executable and the documented bare invocation works. Verify: `scripts/opencode_delegate.py
  --help` after sync. (If it's still 0644, the source lost the mode — re-check the scaffold.)

## 2. Two friction items extrends WILL hit — exact recipes

### F2 — `--check-refs` DANGLING to unseeded `knowledge/ratchet-log.md`
extrends has **no** `knowledge/ratchet-log.md` (confirmed). After sync, the new AGENTS.md +
`knowledge/README.md` reference it, so `--check-refs` will report 2 DANGLING (even though
`--check` is converged). **Seed it** — do not touch the reference. Recipe (identical to the
psc-monitor seed at `../psc-monitor/knowledge/ratchet-log.md`):
- Copy the scaffold's `knowledge/ratchet-log.md` **header/format block ONLY** (through
  "Preference ordering …").
- **ZERO entries.** Do NOT copy the scaffold's own ratchet entries — their `check:`/`test:`
  pointers cite scaffold files (`scripts/scaffold_lint.py`, `scripts/test_repo_lint.py`, …)
  that may not exist in extrends, and `knowledge_lint` would flag them as unresolvable.
- Replace the header's "See `openspec/specs/finding-closure-ratchet/spec.md` …" line with a
  pointer to **AGENTS.md's `Finding closure ratchet` rule** — the capability spec is
  upstream-only (scaffold capability specs are not propagated).
- Add a one-line HTML comment: seeded empty at scaffold sync, no dispositions yet.
- Re-run `--check-refs` (clean) + `knowledge_lint` (OK).

### F4 — `boot_surface_lint` FAIL (extrends boot surface = 119,527 B > 100 KB default)
extrends WILL hard-FAIL the default budget (exit 2 breaks the suite/commit gate). The budget
is now **per-repo configurable** (scaffold decision `boot-budget-per-repo`, commit `c0bdc2f`).
Add a top-level `[boot_surface_lint]` table to extrends' `checks.toml` (per-repo, NOT
scaffold-managed). Recommended, with headroom (its `decisions/INDEX.md` is large and growing):
```toml
[boot_surface_lint]
warn_bytes = 120000
fail_bytes = 140000
```
That makes 119,527 B a clean/near-clean pass (under WARN). **Info-preserving — touches no
knowledge.** The alternative (condensing boot files per the Active/Parked split rule) risks
burying live gates; for a large overage, **surface the raise-vs-condense choice to the
operator** rather than restructuring live knowledge unilaterally. (For psc-monitor the operator
chose the per-repo budget — see below.)

## 3. Pre-flight gotchas specific to extrends

- **Working tree not clean.** `git status` shows untracked `.coverage` and `tmp/` (NOT
  gitignored). These are build/junk artifacts, not local WIP — confirm that, then either add
  them to `.gitignore` or leave them (they won't be staged by the sync). The skill's "stop if
  dirty" rule is about *tracked* local edits; untracked junk is fine once confirmed.
- **Tests:** run via extrends' `scripts/test-cmd` (`.venv/bin/python -m pytest -q`). extrends
  uses SQLite (`trendscope.db*` files), so unlike psc-monitor it needs **no Postgres** — but
  blank any external creds if its suite touches network/email (check its test-cmd env prefix).
- **Larger `knowledge_lint` sweep expected** (older, bigger knowledge tree). Reconcile every
  finding **additively** per skill Step 5 — truthful dispositions, `<!-- lint:keep -->` with a
  rationale, never false-close open debt.

## 4. Lessons / pitfalls from the psc-monitor session (read before starting)

1. **`--check` converged ≠ done. ALWAYS re-run `--check-refs` after the sync** — a byte-converged
   tree can still dangle a reference to a per-repo file the sync doesn't create (F2). This is the
   single easiest thing to miss.
2. **A stricter *synced check* can fail the downstream suite against pre-existing content** — not
   a sync bug, it's the "manual per-repo sweep." psc-monitor hit `boot_surface_lint` (F4). Run the
   FULL downstream suite (Step 4), don't just eyeball `--check`.
3. **Correctness trap with the delegation wrapper (F5, now mitigated):** the wrapper writes
   `<out>.jsonl.text.txt`. If the wrapper ever FAILS (or you skip it) and a **stale** `.text.txt`
   from a prior run sits at the reused `/tmp` path, a naive `grep` reads the WRONG run's verdict —
   in this session it briefly surfaced a confident premise verdict for an unrelated change.
   Defenses: invoke via `python3 scripts/opencode_delegate.py …` (or rely on the now-+x bare form),
   `rm -f <out>.text.txt` before re-running, and sanity-check that the extracted verdict actually
   discusses YOUR change. (Residual scaffold hardening — wrapper should truncate/namespace its
   output or fail-loud on a stale artifact — is recommended but NOT yet built; see §6.)
4. **Downstream commit uses `git commit --no-verify`** and bundles sync + reconciliation in one
   commit. Run every gate manually first (`ruff check .`, `ruff format --check .`, full suite,
   `--check`, `--check-refs`, `knowledge_lint`) since `--no-verify` skips the test gate. Note: when
   you propagate FROM an openspec-scaffold session, psc-monitor/extrends' own `scaffold_check.py`
   PreToolUse hook is NOT loaded (only the scaffold's hooks fire), so the scaffold-file guard won't
   block you regardless — but keep `--no-verify` for correctness and in case of a repo-rooted session.
5. **Fix byte-identical-file lint failures UPSTREAM, never downstream** (skill Step 6). If extrends
   surfaces a NEW environmental lint failure on a shared file (some collision psc-monitor didn't
   have), add the targeted `# noqa` in the scaffold + re-sync — do not edit the downstream copy.

## 5. Verification checklist (all must be green before the downstream commit)
- [ ] `python3 scripts/sync_scaffold.py --check ../extrends` → exit 0 (converged)
- [ ] `python3 scripts/sync_scaffold.py --check-refs ../extrends` → exit 0 (after F2 seed)
- [ ] `cd ../extrends && ruff check . && ruff format --check .` → clean
- [ ] extrends full suite (its `scripts/test-cmd`) → green (boot-surface WARN/exit-1 is OK; only FAIL/exit-2 blocks)
- [ ] `python3 scripts/knowledge_lint.py` (run in extrends) → OK
- [ ] `scripts/opencode_delegate.py --help` (in extrends) → runs (F5 mode propagated)

## 6. Recommended scaffold follow-ons (surfaced this session, NOT yet built)
Judgement: worth doing, but deferred to keep the propagation focused. Route through the normal
SMALL/MEDIUM lifecycle when picked up.
- **Wrapper stale-output hardening (from F5):** `opencode_delegate.py` should truncate its
  `<out>.text.txt` at start (or write to a run-namespaced path), or fail-loud when the source
  `.jsonl` is older than a pre-existing `.text.txt`, so a stale artifact can never masquerade as
  the current run. Also consider switching the AGENTS.md/skill wrapper invocations to the explicit
  `python3 scripts/opencode_delegate.py` form for belt-and-suspenders (independent of the exec bit).
- **isort-collision guard (from F3):** a scaffold test asserting that any scaffold test-module
  doing `import checks` (or another name colliding with a plausible downstream top-level package)
  after a `sys.path.insert` carries the `# noqa: … I001` guard — stops the whack-a-mole per new
  file. `scripts/test_facts.py` also carries the bare guard without the rationale comment (F3).
- **Sync summary output (from F1, low priority):** `sync_scaffold.py` runs silently (exit 0, no
  stdout); a one-line "copied N / added M / deleted K, span-merged AGENTS.md" summary would make
  the sync legible without a follow-up `git status`.

## 7. What was committed for psc-monitor (reference)
- Scaffold: `efdc1fd` (F3 noqa), `c0bdc2f` (F4 boot-budget-per-repo, SMALL), `c8d344a` (F5 exec
  bit + this skill's playbook hardening).
- psc-monitor: `274c0e4` (main sync + ratchet-log seed + `[boot_surface_lint]` 100k/120k override),
  `7d0875d` (exec-bit propagation). Operator chose the per-repo-budget route (F4) over condensing
  live deploy knowledge.
- **Neither repo was pushed** — push is operator-gated.
