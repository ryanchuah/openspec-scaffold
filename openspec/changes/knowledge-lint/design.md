# Design — knowledge-lint

Implementation design for the two-layer per-repo knowledge drift detector. This document resolves the
three 🟡 and the config 💡 that `proposal.md`'s Round-1 review deferred here (`review-log.md`).

No new external-API surface is introduced (stdlib-only, no network/client) — the propose-skill's
external-API live probe is correctly skipped.

## Context

`knowledge_lint.py` joins the existing scaffold-managed linter family (`status_lint.py`,
`data_lint.py`, `scaffold_check.py`). It is deterministic and detect-only, mirroring `status_lint.py`'s
shape. The LLM `lint-knowledge` skill is the judgment counterpart. Both are scaffold-managed and
propagate downstream via `sync_scaffold.py`.

## Decisions

### D1 — Detect-only everywhere; the archive wider-sweep is flag-only (resolves 🟡1)
Nothing in this change ever rewrites prose. `knowledge_lint.py` mutates no file (asserted by a test).
The `lint-knowledge` skill emits findings only. The widened archive sweep (`knowledge-organization`
delta) **flags** stale claims about the just-shipped change for operator/primary follow-up; it does
**not** auto-correct reference/roadmap/review-backlog bodies. The existing three-tracker reconciliation
(which *does* write STATUS/decisions/questions) is unchanged — "reconciliation" keeps its write meaning
for the three trackers only; the wider bodies are detect-and-flag.

### D2 — `knowledge_lint.py`: scope, checks, exit codes
- **Root & enumeration:** takes `--root <path>` (default: the repo root discovered from the script
  location). It walks the filesystem — **no git *dependency*** — scanning `<root>/knowledge/**/*.md` for
  content checks and `<root>` for orphaned canonical files. Filesystem-walk (not `git ls-files`) keeps
  it trivially testable against a `tmp_path` fixture tree. **Git-ignored paths are skipped** (via
  `git check-ignore` when `<root>` is a git repo) so a vendored/ignored clone (e.g. a local `OpenSpec/`
  reference checkout) is not scanned; when git is unavailable (e.g. a `tmp_path` fixture) nothing is
  skipped. This is an as-built refinement added at verify (see review-log) — the walk stays git-optional.
- **Checks** (each yields zero or more findings; a finding is `(check, path, line|None, message)`):
  1. **orphan/duplicate canonical file** — a fixed map of **single-home** canonical basenames to their
     taxonomy home: `STATUS.md → knowledge/STATUS.md`, `lessons.md → knowledge/lessons.md`,
     `roadmap.md → knowledge/roadmap.md`, `audit-log.md → knowledge/audit-log.md`. A file with a
     canonical basename living outside its home (e.g. a root `STATUS.md`), or a second copy of a
     canonical file, is a finding. **`INDEX.md` and `README.md` are deliberately excluded** from this
     map — they have multiple legitimate homes (`decisions/INDEX.md`, `questions/INDEX.md`;
     `knowledge/README.md` plus skill READMEs), so a basename match would false-positive.
  2. **retired-path token** — per-line substring scan of each in-scope knowledge markdown for any active
     retired-path token (see D5). Finding carries file+line.
  3. **broken prose path citation** — extract backtick-wrapped, repo-relative path-like tokens
     (contain a `/` or end in `.md`; not a URL, not an absolute system path) and flag any that do not
     resolve under `<root>`. **A token is only treated as a citation when its first path segment is an
     existing top-level directory under `<root>`** (e.g. `knowledge/`, `openspec/`, `scripts/`,
     `.claude/`, `.opencode/`, `plans/` — computed dynamically from what exists at `<root>`, not
     hardcoded). This first-segment gate is the load-bearing false-positive control (added at verify —
     see review-log): measured against real prose, unbounded "any repo-relative token" matching was
     ~80% noise — bare filename mentions (`tasks.md`, `SKILL.md`), cross-repo names (`extrends/AGENTS.md`),
     GitHub shorthand (`sst/opencode`), and non-path slashy tokens (`WHEN/THEN/AND`) — while genuine
     in-repo path drift (a moved `plans/…`→`openspec/changes/…`) always starts with a real top-level
     dir. The prior exclusions (URL, absolute, embedded whitespace, `~`-home, `<placeholder>`, glob)
     still apply. Exact behavior is pinned by tests.
  4. **dangling archive pointer** — flag any `openspec/changes/archive/<dir>/` reference whose `<dir>`
     does not exist under `<root>`.
  5. **audit-log registry format (guarded)** — if `<root>/knowledge/audit-log.md` exists, validate each
     registry line against `- **YYYY-MM-DD** · audit/<date> · <short-sha> · <essence>`; if the file is
     absent, skip silently (see D6).
- **Scan exclusion — `knowledge/research/`:** the content checks (2 retired-path and 3 broken-citation)
  SHALL skip `knowledge/research/`, mirroring `sync_scaffold.py`'s `_REF_SCAN_EXCLUDE`. That directory
  holds **period-correct historical analyses** whose citations and path mentions legitimately reference
  pre-restructure paths that no longer resolve — scanning them would emit false positives an operator
  cannot distinguish from real drift. (Checks 1/4/5 are structural, not prose-content, so they are not
  affected by this exclusion.)
- **Exit codes:** `0` = no findings; `1` = one or more findings. **Rationale (resolves 💡6):** this
  follows `sync_scaffold.py --check`'s drift-diagnostic convention (`1`), NOT `status_lint.py`'s `2`,
  deliberately — (a) `knowledge_lint.py` is a drift *diagnostic* like `--check`, and (b) `argparse`
  itself exits `2` on a bad flag, so using `1` for findings keeps "found drift" cleanly distinct from
  "bad invocation." Every finding prints one stdout line; a trailing count-free summary line is fine
  (never record counts in tracked docs, but stdout is not a tracked doc).

### D3 — Boundary with `sync_scaffold.py --check-refs` (resolves 🟡2): coexist, not replace
`--check-refs` is untouched. It is a **scaffold-compliance** check: it validates `knowledge/*.md` path
citations and the `` `file.md` §"Section" `` form **in synced files**, run during sync. `knowledge_lint.py`
is a **drift-detection** check: it validates *any* repo-relative path cited in *any* tracked knowledge
prose, plus orphans / retired-paths / dangling pointers, run at archive / CI / on demand. They overlap
only in "both look at path citations" but serve different purposes and run at different times. No
functionality is removed from or re-implemented against `--check-refs`.

### D4 — Division of labor with `status_lint.py`'s archive-pointer check (resolves premise 🟡3)
`status_lint.py` keeps its `decisions/INDEX.md`-specific registry-line + archive-pointer-resolution
check (part of the STATUS/decisions bounds linter). `knowledge_lint.py`'s dangling-archive-pointer
check (D2 check 4) scans **all** tracked knowledge markdown. The two overlap on `decisions/INDEX.md`;
that redundancy is deliberate defense-in-depth, not a bug — no attempt is made to carve `decisions/INDEX.md`
out of `knowledge_lint.py`. Neither linter is modified by the other's existence.

### D5 — Retired-path tokens: hardcoded defaults + optional per-repo config (resolves config 💡)
Built-in default token set: `ai-docs/`, `plans/open-issues.md`, `docs/reviews/`, `/home/me/` (the known
universal reorg residue). Because the script is scaffold-managed (never edited downstream), per-repo
extension is read from an optional `[knowledge_lint]` table in a repo-root `audit.toml` via `tomllib`
(already the established per-repo config file + stdlib parser from `deterministic-tooling-layer`). The
**exact key is `retired_paths`** — an array of strings, e.g. `[knowledge_lint]\nretired_paths = ["old-docs/", "legacy/"]` — whose values are **merged with** (not replacing) the built-in defaults.
`tomllib` requires Python ≥3.11, which those repos already assume. When `audit.toml` is absent, has no
`[knowledge_lint]` table, or no `retired_paths` key, only the defaults apply. `audit.toml` is **not**
added to the manifest.

### D6 — audit-log registry check is file-exists-guarded
`knowledge/audit-log.md` does not exist in the scaffold and is created per-repo as audits run, so the
check runs only when the file is present and is a silent no-op otherwise. No dependency on
`deterministic-tooling-layer` shipping the file first.

### D7 — `lint-knowledge` skill: structure & cadence
Ships at `.claude/skills/lint-knowledge/SKILL.md` **only** (both harnesses discover `.claude/skills/**`;
per the `skills-in-dot-claude-only` decision, no `.opencode/` copy). It is an **operator-invoked
periodic** pass — NOT run on every archive (the LLM cost/latency is unfit for every-archive). Its body
directs the agent to: (a) first run `knowledge_lint.py` to clear the deterministic findings; then do the
judgment sweeps — Class B stale-"not-built" vs shipped `archive/`/`STATUS.md`, Class D intra-doc
contradictions, and the buried-gate sweep (README/runbook items missing from `questions/INDEX.md`
Active). Detect-only: it reports; it never edits prose.

### D8 — Archive integration (the `knowledge-organization` delta)
Two edits wire the archive cadence for the *deterministic* layer + the *scoped* just-shipped-change
re-check (NOT the full LLM sweep):
- **AGENTS.md** — the reconciliation-brief span ("State, write discipline, and the archive-as-handoff
  rule") gains one sentence: at archive the archive-executor also runs `knowledge_lint.py` and re-checks
  `knowledge/reference/`, `knowledge/roadmap.md`, and the `knowledge/questions/` Parked backlog for
  now-stale claims about the just-shipped change, flag-only. The Parked re-check covers the **individual
  `knowledge/questions/<item>.md` bodies**, not only the one-line pointers in `questions/INDEX.md`
  (stale claims live in the bodies). This is a scaffold-managed span → propagates.
- **`.claude/skills/openspec-archive-change/SKILL.md`** — the reconciliation step gains the same
  flag-only wider-sweep instruction so the archive-executor actually performs it.

### D9 — Manifest additions
Add three lines to `scripts/scaffold_manifest.txt`: `scripts/knowledge_lint.py`,
`scripts/test_knowledge_lint.py`, `.claude/skills/lint-knowledge/SKILL.md`. (`AGENTS.md`,
`openspec/config.yaml`, and `openspec-archive-change/SKILL.md` are already manifest entries; the edits to
them propagate without new manifest lines.)

## Verification

Change-specific acceptance criteria (checked at verify):
1. **Deterministic checks fire:** a fixture knowledge tree seeded with one instance of each drift class
   (orphan root `STATUS.md`; a retired-path token; a broken `*.md` citation; a dangling
   `archive/<dir>/` pointer; a malformed `audit-log.md` line) yields exactly the expected findings, and
   `knowledge_lint.py` exits `1`.
2. **Clean fixture → exit 0; scaffold self-lint → no linter noise:** run against a drift-free fixture →
   zero findings, exit `0`. Run against the scaffold repo's own `knowledge/` → exit `0`, **OR** every
   remaining finding is genuine **pre-existing content drift / forward-reference** (each enumerated in
   `notes.md`), NOT linter noise. After the broken-citation first-segment gate + git-ignore skip (D2),
   the noise classes (bare filenames, cross-repo names, GitHub shorthand, vendored `OpenSpec/` clone)
   MUST be gone; only real drift may remain — and real per-repo drift is out-of-scope to fix here
   (proposal), so it is documented rather than corrected.
2b. **research exclusion:** a fixture with a broken/pre-restructure path citation inside
   `knowledge/research/` yields **no** finding, while the same citation outside research is flagged.
2c. **first-segment gate:** a backtick token whose first segment is NOT an existing top-level dir under
   `<root>` (bare `tasks.md`; `extrends/AGENTS.md`; `sst/opencode`; `WHEN/THEN/AND`) is NOT flagged; a
   token under a real top-level dir that does not resolve (`plans/gone/`) IS flagged.
2d. **git-ignore skip:** a broken citation placed inside a git-ignored directory is NOT scanned/flagged.
3. **Detect-only:** after any run (drift or clean), the fixture tree is byte-unchanged (no file created,
   modified, or deleted).
4. **audit-log guard:** with no `knowledge/audit-log.md`, the check is skipped and does not error; with a
   present-but-malformed file, it flags the bad line.
5. **Per-repo config:** with no `audit.toml`, only default retired-path tokens flag; with an `audit.toml`
   `[knowledge_lint].retired_paths` extension, the extra tokens also flag.
6. **Skill present & single-path:** `.claude/skills/lint-knowledge/SKILL.md` exists; no `.opencode/`
   copy exists.
7. **Manifest & sync:** the three new entries are in `scaffold_manifest.txt`; `sync_scaffold.py --check`
   semantics remain green for an in-sync downstream (no regression to the sync mechanism).
8. **Full suite green:** `scripts/test-cmd` (or the documented pytest command) passes, including the new
   `test_knowledge_lint.py`.

## Out of scope
- Any per-repo drift *content* fix (the downstream Class A–D burndown) — separate follow-on.
- Any automated prose rewriting.
- Non-markdown files (the linter scans markdown knowledge only).
- Running the full LLM `lint-knowledge` sweep on every archive (operator-invoked only).
