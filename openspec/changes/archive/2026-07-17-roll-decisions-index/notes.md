# Notes — roll-decisions-index (MEDIUM)

## Tier + routing
- **MEDIUM, self-classified under this session's explicit operator autonomy grant** (grant covers
  through archive). Tasks-only propose per the AGENTS.md MEDIUM rule; delta specs included because
  the change alters two specced capabilities (`knowledge-lint`, `knowledge-organization`).
- **Apply pre-routed to a Sonnet subagent apply-executor** by operator instruction this session
  ("for apply-executor and archive, use sonnet subagent instead of deepseek"). Archive likewise
  Sonnet-first. Reviewer/verifier passes stay deepseek via `opencode run` (not overridden).
- **Direction gate:** ran on `explore-brief.md` before propose — `PREMISE: AGREE`, zero 🔴
  (review-log round 0). Its three 🟡 design flags are addressed in tasks.md: block-extent rule
  (1.2), calibration reporting (1.6 summary prints entries retained/rolled), header preservation
  (1.2/1.5).

## Assumptions
- Both repos' current INDEX files hold strictly single-line entries (verified by scan here and by
  the psc-monitor structural analysis). The reviewer's claim of existing multi-line entries did
  not reproduce; continuation-line handling (tasks 1.2/2.4) is kept as a defensive requirement
  regardless.
- `boot_surface_lint` has no capability spec, so its remedy-line change ships without a delta
  spec; the two deltas cover the check and the convention.
- Downstream sequencing: each downstream repo performs its own roll during its operator-gated
  propagation session (ledger entry, task 6.4). psc-monitor's separate un-red change this session
  uses the scaffold's script against its tree without propagating any file.

## Verification (acceptance criteria — judged at verify)
1. `python3 scripts/roll_decisions.py --dry-run` then the real run on this repo: summary figures
   match between the two; INDEX.md ends ≤ 12,000 bytes, retains the newest entries + header +
   pointer line; HISTORY.md holds the rolled entries verbatim in chronological order (spot-check
   oldest and boundary entries against git HEAD's INDEX).
2. Re-running the script is a no-op; `git diff` shows entries moved, never edited (byte
   conservation).
3. `python3 scripts/boot_surface_lint.py .` exits 0 on the rolled tree (was WARN at 83,925); WARN
   and FAIL outputs (exercised via tests, not the live tree) carry the remedy line naming
   `roll_decisions.py`.
4. `python3 scripts/knowledge_lint.py` exits clean on the rolled tree; planted over-budget fixture
   flags `decisions-index-budget` with the remedy named; `checks.toml` override honored; invalid
   override falls back.
5. `bash scripts/check.sh` fully green; `openspec validate roll-decisions-index --strict` exits 0.
6. `knowledge/README.md` documents the convention; `scripts/scaffold_manifest.txt` lists both new
   files; the propagation ledger records the downstream per-repo roll requirement; OW-13(b) item 1
   reads as resolved by this change.

## Verify checkpoint

1. **Verdict:** ready for archive.
2. **Confirmed by eyeballing live output:** the live roll's INDEX.md keeps the header + pointer line
   (correctly placed after the `---`) + the newest tail, and HISTORY.md holds the rolled entries
   verbatim under its own header; anchor conservation is exact between git HEAD's INDEX and the
   INDEX+HISTORY split, and an independent byte-reconstruction (header + HISTORY tail + retained
   entries, pointer line removed) reproduces HEAD's INDEX text exactly; `boot_surface_lint` returns
   OK on the rolled tree (back under the default WARN threshold, no remedy line on OK) and WARN/FAIL
   fixtures carry the remedy line; a repeat `roll_decisions.py --dry-run` is a no-op; orchestrator
   adversarial fixtures (no-`---` header fallback, positional no-sort roll on out-of-order dates,
   exact-budget boundary at the default, `--target-bytes 0` never-empty guard, orphan pointer line,
   re-roll on a live-tree copy) all behaved to spec. `check.sh` green; `knowledge_lint`,
   `status_lint`, `openspec validate --type change --strict`, and the `spec-delta-structure`
   detector all clean.
3. **Defect found and how it was fixed:** (a) self-review — the executor's OW-13(b) closure and propagation
   ledger recorded entry-count/byte figures, violating the never-record-counts rule; trivially
   reworded inline by the orchestrator. (b) pro behavioral pass (deepseek-v4-pro) — READY,
   zero defects. (c) simplicity gate (/code-review low) — one confirmed-but-accepted finding:
   a crash between the INDEX write and the HISTORY write would momentarily lose the rolled
   entries from both files; accepted because both files are git-tracked (fully recoverable),
   the window is microseconds, and inverting the write order only trades loss for duplication.
   No fix-redelegation was needed; Sonnet fix-executor never invoked.
4. **As-built delta:** the pointer line is inserted after the FIRST `---` line in the header, not
   the last/"closing" one as tasks.md phrased it — indistinguishable on every current repo's
   single-`---` header; divergent only on a hypothetical multi-`---`/front-matter header. Left
   as-built deliberately; noted as a follow-on (below).
5. **Forward-looking items for the project docs (to fold in at archive):**
   - Pointer-line insertion position (first vs closing `---`) — harden `_insert_pointer_line` to
     the LAST header separator if a repo ever adopts front-matter-style INDEX headers; cosmetic
     until then. Park as a one-line follow-on.
   - The 16,000/12,000 defaults are judgment calls not yet validated against months of real
     growth — tune only if rolls become too frequent/rare; fold into the EXISTING parked
     "Budget/threshold tuning" item (knowledge-surface-bounding-2-follow-ons item 2), do not
     file a new item.
   - Downstream propagation of this change requires the per-repo roll BEFORE each repo's
     live-tree gate sees the new check — already recorded in
     `knowledge/reference/pending-downstream-propagation.md` (no new filing needed; listed here
     for the archive-executor's cross-check).
   - Data-path determination: the roll reads one bounded tracked file (tens of KB) fully into
     memory — bounded-domain argument, no at-scale run required.

**Still owned by archive:** reconcile `knowledge/STATUS.md` (new Latest change section; cap),
`knowledge/decisions/INDEX.md` (one registry line for this change — note it lands in the freshly
ROLLED index), `knowledge/questions/INDEX.md` (nothing new expected — follow-ons above route to an
existing parked item or are already recorded), promote the two delta specs into `openspec/specs/`
(knowledge-lint ADDED requirement; knowledge-organization ADDED requirement), and the archive move
itself.
