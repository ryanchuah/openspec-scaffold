# HANDOFF — finish shared-lint-layer: install-tools descope → re-verify → archive

**Ephemeral pre-archive handoff** (session ran long). Absorb, do the three tasks, then **delete this
file** (its normal state is absent). Written 2026-07-03.

## State

`shared-lint-layer` (portfolio Change **C**, MEDIUM) is **APPLIED and its immediate changes VERIFIED
green**. One verify defect remains open (install-tools) — do it here, re-verify, then archive.

- Commits on `main` (unpushed): `cbad9cc` propose → `4bae0b7` `3045022` `b5e9a6f` `9d8ba28` (apply
  §1–12) → `ddbeb65` (verify fix: matcher `:N` + class-6 `<!-- lint:planned -->` marker). Tree clean.
- **Deepseek reviews were WAIVED by the operator** this session (propose premise + verify multi-model
  pro/flash passes). The orchestrator's own self-review is the review of record. Keep the waiver unless
  the operator says otherwise.
- Artifacts: `openspec/changes/shared-lint-layer/` — `notes.md` (acceptance criteria + design record +
  verify outcome), `tasks.md` (all `[x]`), `specs/{shared-lint-gate,commit-test-gate,knowledge-lint}/`.
  Read `notes.md` first — its "Verify outcome" section has the full defect list + forward items.

## TASK 1 — install-tools descope (Option A, operator-approved)

**Why:** the two security scanners are Go binaries — **gitleaks** (secrets scanner) and **osv-scanner**
(dependency-CVE scanner). The shipped `scripts/install-tools.sh` curl-installs release tarballs with
hardcoded asset URLs (**both 404'd in verify**) and no checksum verification — fragile + supply-chain
risk. Operator chose to descope the bespoke installer in favor of a reference doc + a `go install`
helper (CI provisioning via official actions, deferred to D1/D2).

Do:
1. **Replace `scripts/install-tools.sh`** body with a thin, robust helper that uses `go install`
   (both tools are Go), guarded on `command -v go` (warn + point to the reference doc if go is absent).
   Keep it idempotent and executable. Keep it in the manifest (so no deletion-manifest dance).
2. **Add a provisioning reference** — `knowledge/reference/security-scanners.md` <!-- lint:planned --> (new): the two tools +
   what they detect, pinned versions, and recommended provisioning per environment — **CI = official
   actions** (`gitleaks/gitleaks-action`, `google/osv-scanner-action`), **local = `go install` / brew**.
   Note actual CI wiring is per-repo (D1/D2).
3. **Update `knowledge/reference/new-repo-bootstrap.md`** step 6 (currently "Run `bash
   scripts/install-tools.sh`") to the new approach.
4. **Rework the delta spec** `specs/shared-lint-gate/spec.md`: the `### Requirement: install-tools.sh
   provisions pinned security scanners` (≈line 55) → reword to "the scaffold documents the required
   scanners + pinned versions + recommended per-environment provisioning, and ships a `go install`
   helper" with matching scenarios. Also reconcile the `check.sh` degradation scenario mention
   (≈line 35, "install-tools.sh + dev extras + CI") and the scaffold-managed requirement (≈lines 82/89).
   Then `openspec validate shared-lint-layer --type change --strict` must be clean.
5. **Update `notes.md` AC#8** to match the chosen approach.
6. **Green + commit:** `pytest -q`, `bash scripts/check.sh`, `python3 scripts/scaffold_lint.py`,
   `python3 scripts/sync_scaffold.py --check-refs .` — all exit 0. (Note: `--check-refs` needs the `.`
   target arg.) Commit.

## TASK 2 — re-verify (behavioral, my own; multi-model still waived)

Behavioral review of the install-tools change: reference doc accurate; `go install` helper's
`command -v go` guard behaves and the install commands are correct (shellcheck / dry-run). Then:
full suite green, `check.sh` 0, `scaffold_lint` 0, `knowledge_lint`+`status_lint` clean,
`sync_scaffold.py --check-refs .` 0. Update `notes.md` "Verify outcome" → **verdict READY**.

## TASK 3 — archive (openspec-archive-change skill)

Delegate to the **archive-executor** (deepseek-v4-pro via `opencode run`, Sonnet subagent fallback):
- Move `openspec/changes/shared-lint-layer/` → `openspec/changes/archive/2026-<MM-DD>-shared-lint-layer/`.
- **Promote delta specs to main specs:** NEW capability `openspec/specs/shared-lint-gate/spec.md` <!-- lint:planned -->
  (add a `## Purpose`); MODIFY `openspec/specs/commit-test-gate/spec.md` (test-gate→check.sh rewire +
  hook-matcher fix); MODIFY `openspec/specs/knowledge-lint/spec.md` (citation-matcher hardening +
  root-handoff check + `lint:planned` marker).
- Reconcile `knowledge/STATUS.md` (new shared-lint-layer section; respect the ≤3-section cap — drop the
  oldest), `knowledge/decisions/INDEX.md` (one registry line), `knowledge/questions/INDEX.md` (park the
  forward items below).
- Primary reviews + commits. **Do not push** (operator-gated).

## Forward items to park in knowledge/questions/INDEX.md at archive

- **`<!-- lint:planned -->` marker is SHIPPED** — document the convention for authors; extrends' 2
  forward-references (`scripts/_autolabel_v2_oneoff.py`, `config/subreddits_general.yaml`) <!-- lint:planned -->
  should get the marker (or be reworded) in **D1** once C syncs.
- `output/` ephemeral skip is a hardcoded prefix — consider the `.gitignore`-aware general form.
- `data_lint` strict row-validation: whether `zip(strict=True)` (fail-loud on ragged CSV) is wanted is a
  deferred deliberate call (kept `strict=False`, behavior-preserving, this session).
- **E501 is ignored** in ruff — marginally narrower than "all of E"; ratchet back if a manual reflow pass
  is ever done.
- Pinned scanner versions have no CVE-drift auto-bump (dependabot/renovate is a parked operator decision).
- commit-test-gate wiring-smoke doc (`tests/commit-gate-smoke/README.md`) could note verifying the new
  stdin command-detection layer.

## Downstream / parallel context (NOT this change)

- A parallel **extrends knowledge-drift burn-down** ran; its gap report was `/tmp/extrends-lint-gap-report.md`
  (may be gone after reboot; its findings are summarized in `notes.md` and above). extrends commits are
  local/unpushed.
- **D1** (extrends wiring) + **D2** (psc-monitor, still frozen) propagate this lint layer downstream —
  operator-gated, AFTER C archives. They inherit `check.sh`/`ruff.toml`/`knowledge_lint` by sync and
  wire per-repo CI (check.sh step + official scanner actions) + `checks.toml` + `lint:planned` markers.
- All pushes remain operator-gated.
