# Composition/whole-repo audit surface — research digest

Scope: existing scaffold machinery relevant to wiring a new "cadenced
composition-audit" pass. Read-only research; no source files modified.

## 0. Important framing fact

**`checks.toml` is not a file that exists in this scaffold repo, and it is
NOT in `scripts/scaffold_manifest.txt`.** It is a per-downstream-repo config
file (extrends, psc-monitor each carry their own). The scaffold ships the
*engine* (`scripts/checks.py`) that reads `checks.toml` if present, or falls
back to auto-detected defaults if absent. Its entire schema is documented in
`scripts/checks.py`'s module docstring (`scripts/checks.py:23-70`) —
deliberately the only documentation, per the repo's "no standing doc for a
code-derivable schema" convention. So "every checks.toml entry" (research
brief item 1) does not exist as a literal file to read; the registry that
*would* populate it lives in `scripts/checks.py:177-232` (`_REGISTRY`) and
`scripts/checks.py:279-299` (`_autodetect_defaults`). This digest treats that
registry as the canonical checks.toml-equivalent.

## 1. The check registry (`scripts/checks.py:177-232`)

Registry order is load-bearing (drives `--list`, `--report`, run-manifest
ordering). Each entry: `name`, `tier` (`floor|heavy|snapshot`), `kind`
(`builtin|delegate|custom`), `family` (`check|fact`), plus `trigger` /
`coverage_note` for auto-detected check-family entries.

| name | tier | kind | family | default enabled | scope |
|---|---|---|---|---|---|
| scope | floor | delegate | fact | has `.git` | whole-repo (delta since last `audit/*` tag, or full if none) |
| ruff | floor | builtin | check | has pyproject.toml | paths-scoped (default `.`) |
| gitleaks | floor | builtin | check | has `.git` | whole-repo |
| osv-scanner | floor | builtin | check | has lockfile | whole-repo (`-r .`) |
| deptry | floor | builtin | check | has pyproject.toml | paths-scoped |
| data-lint | floor | delegate | check | has `checks/*.sql` | DB-scoped, not file-scoped |
| radon | heavy | builtin | fact | **disabled by default** | paths-scoped, also folded into `scope`'s hotspot calc |
| **jscpd** | heavy | builtin | check | **disabled by default** ("always (enabled explicitly)") | **whole-repo duplication scan** |
| **vulture** | heavy | builtin | check | **disabled by default** ("always (enabled explicitly)") | **whole-repo dead-code scan** |
| index-coverage | heavy | delegate | fact | **disabled by default** (no schema by default) | DB-schema-scoped |
| outstanding | snapshot | delegate | fact | always on | whole-repo prose/questions/roadmap scan |
| inventory | snapshot | builtin | fact | always on | **whole-repo tree snapshot** (zero-findings) |

Auto-detect defaults (`_autodetect_defaults`, `scripts/checks.py:279-299`):
checks with no external tool dependency (`scope`, `outstanding`, `inventory`)
are unconditionally enabled; the four heavy-tier checks (`radon`, `jscpd`,
`vulture`, `index-coverage`) are **unconditionally `False`** absent explicit
`[checks.<name>] enabled = true` in a repo's `checks.toml` — there is no
trigger-file heuristic for them at all, unlike ruff/gitleaks/osv-scanner/
deptry/data-lint. Docstring rationale (`scripts/checks.py:30-34`): heavy-tier
checks are "on-demand/audit-time," and `index-coverage` additionally has no
sane default `--schema` path to guess.

**Whole-repo vs diff-scoped, explicitly:**
- Whole-repo-scoped by construction: `gitleaks` (`gitleaks detect` over the
  full working tree), `osv-scanner` (`-r .`, recursive from root),
  **`jscpd`** (duplication needs cross-file comparison, `paths` defaults to
  `["."]`), **`vulture`** (dead-code detection needs the whole graph, `paths`
  defaults to `["."]`), `inventory` (full `git ls-files` tree +
  entrypoints + env-var scan), `outstanding` (scans `knowledge/`,
  `openspec/`, code TODOs repo-wide).
- Diff/delta-scoped by construction: `scope` (`audit_scope.py scan` — only
  files changed since the last `audit/*` tag, or full-repo if no tag exists
  yet; see §3).
- Paths-configurable, defaulting to whole-repo but overridable narrower:
  `ruff`, `deptry`, `radon` — `paths` config key, default `["."]`
  (`scripts/checks.py:326-330`).

**Live check today (this repo):** confirmed no `checks.toml` exists here, so
`ruff`/`gitleaks`/`osv-scanner`/`deptry`/`scope`/`outstanding`/`inventory`
run at auto-detected defaults; `radon`/`jscpd`/`vulture`/`index-coverage` are
off. This matches `knowledge/reference/audit-runbook.md`'s per-repo table
(§9 below), which shows only floor-tier checks live in extrends/psc-monitor
today — no evidence either downstream repo has flipped `jscpd`/`vulture` on.

## 2. `scripts/checks.py` engine mechanics (no code pasted; described)

- **Registration.** A built-in check is a dict literal appended to
  `_REGISTRY` (`scripts/checks.py:177-232`) with `name`/`tier`/`kind`/
  `family` (+ `trigger`/`coverage_note` if it's an auto-detected check-family
  entry). A **delegate** check additionally needs: an entry in
  `_availability_for_check` treating `kind == "delegate"` as always-available
  (`scripts/checks.py:393-399`, since delegate scripts are always-present
  scaffold siblings), a branch inside `_run_delegate`
  (`scripts/checks.py:885-996`) with its own JSON-shape contract (not merged
  into the parsed-findings aggregate), and if it's a **builtin parsed**
  check, both an entry in `_PARSERS` (native-output → normalized-finding
  regex/JSON parser) and `_BUILTIN_RUNNERS` (subprocess invocation), plus a
  binary name in `_BUILTIN_TOOL_BIN` if it's a real external tool. A
  **custom** check needs no code change at all — it's fully declared in
  `[checks.custom.<name>]` in a repo's `checks.toml` (`command`, `tier`,
  `gate`); output is captured verbatim to `<check>.txt`, no parser exists,
  findings count is always `?`.
- **Preflight (`--floor`/`--report`).** Before executing any selected
  check-family entry, every one is probed for tool availability
  (`_availability_for_check` → `_tool_status`, two-step `<tool> --version`
  then `<tool> version` probe, `scripts/checks.py:347-371`). If *any*
  enabled check-family tool is `unavailable` or `version-mismatch`, **all**
  gaps are reported at once and the run **exits 3 before running anything**
  (`scripts/checks.py:1266-1314`, "self-explaining message" pattern: install
  the tool or flip `[checks.<name>] enabled = false`). Fact-family entries
  are exempt from this hard-stop — an unavailable fact tool degrades to a
  `skipped` record and the run continues (`scripts/checks.py:1338-1343`).
- **Output landing.** `--report [--out DIR] [--date YYYY-MM-DD]` defaults
  `--out` to `output/checks/<date>/` (`scripts/checks.py:1476-1479`);
  `--floor` (no date stamp) defaults to CWD. Each check writes
  `<out>/<check>.json` (or `.txt` for custom); a stdout summary line per
  check; after a full run, an aggregate `<out>/findings.json` (parsed
  built-ins only, delegate/snapshot checks excluded) plus
  `<out>/run-manifest.json` (checkpoint state for `--resume`) and, if
  `--baseline PATH` given, `<out>/delta.json` (new/resolved/unchanged vs a
  prior findings.json, fingerprinted by `{check, rule, path, message}` sha1,
  `scripts/checks.py:1079-1102`).
- **Adding a NEW check** (summarizing the above): pick `kind` — `custom` for
  zero-code (`[checks.custom.<name>]` in `checks.toml` alone); `builtin`
  parsed for a new external tool with structured output (registry entry +
  parser + runner + tool-bin mapping); `delegate` for a scaffold-owned
  Python script with its own JSON contract (registry entry + `_run_delegate`
  branch). Tier + family determine when/how it runs and whether it can abort
  a `--floor`/`--report` run.

## 3. `scripts/audit_scope.py` — scan/tag/log-line surface

Three subcommands, `scan` is the default (`scripts/audit_scope.py:9-74`,
`371-405`):
- **`scan`** (read-only). Finds the latest `audit/*` git tag via
  `git tag --list 'audit/*' --sort=-creatordate` (most-recent first). No tag
  → `scope: "full"`, diff against the git empty-tree SHA (every tracked file
  is pure insertion). Tag exists → `scope: "delta"`, `git diff --numstat
  <tag>..HEAD`. Complexity via batched `radon cc -j` (only if radon on
  PATH — `complexity_available` flag). Hotspot score = `churn * (1 +
  complexity)` (or `churn * 1` without radon), files ranked descending.
  Writes `{generated_by, tag, anchor_commit, commits_since, scope,
  complexity_available, files: [{path, churn, complexity, hotspot_score}]}`
  to `--json PATH` (default `audit_scope.json` in CWD).
- **`tag --date YYYY-MM-DD`**. Creates an **annotated** tag `audit/<date>`
  at HEAD (message `"audit anchor <date>"`). `--date` is required, no
  implicit "today." Refuses (exit 3) if the tag already exists — never
  silently mints a second anchor. **This is the only mutating git operation
  anywhere in the audit surface.**
- **`log-line --date YYYY-MM-DD --essence "<text>"`**. PRINTS (never writes)
  `- **<date>** · audit/<date> · <short-HEAD-sha> · <essence>`. The caller
  (the `run-audit` skill) is responsible for appending it to
  `knowledge/audit-log.md`.

**Commits-since-last-tag computation:** `git rev-list --count
<tag>..HEAD` (`scripts/audit_scope.py:248`), same primitive
`checks.py`'s `inventory` fact reuses independently (see §4).

## 4. `scripts/facts.py` fact-family entries

`facts.py` is a thin, always-exit-0 CLI over the `family == "fact"` subset
of `checks.py`'s registry (`scripts/facts.py:40-42`): `scope`, `radon`,
`index-coverage`, `outstanding`, `inventory`. Writes undated to
`output/facts/` (overwritten every run — cache, not audit-log, semantics).
Not subject to preflight (`scripts/facts.py:14`).

**`inventory` fact** (`scripts/checks.py:638-676`, `_run_inventory`).
Exact payload:
```
{
  "generated_by": "checks.py",
  "tree": [<sorted `git ls-files` output>],
  "entrypoints": [<pyproject [project.scripts], Makefile/justfile targets, package.json scripts>],
  "env_vars": [<sorted os.environ/os.getenv/process.env names, anchored regex>],
  "audit_anchor": {"tag": <str|null>, "commits_since": <int|null>}
}
```
`audit_anchor` is computed independently inside `_run_inventory` (its own
`git tag --list 'audit/*' --sort=-creatordate` + `git rev-list --count
<tag>..HEAD` calls, `scripts/checks.py:648-668`) — it does **not** call
`audit_scope.py`; it's a parallel, duplicate computation of the same
tag-lookup logic. `tag`/`commits_since` are both `null` if no `audit/*` tag
exists yet.

**`outstanding` fact** (`scripts/outstanding.py:569-611`, `run()`). Exact
JSON payload:
```
{
  "generated_by": "outstanding.py",
  "config": {"findings_globs": [...], "finding_id_pattern": "..."},
  "open_work": [<items from knowledge/questions/INDEX.md, tasks.md files,
                 roadmap.md, code TODOs, prose files — each carries source,
                 line, content, bucket="triaged", section>],
  "untriaged": [<FINDINGS*.md items not yet cross-referenced into
                 knowledge/questions/, each with an age_days field>],
  "summary": {"open_work_count": <int>, "untriaged_count": <int>}
}
```
Also writes a markdown sibling (`output/facts/outstanding.md`) via
`_render_md`. Config keys live under `[facts.outstanding]` in `checks.toml`
(`findings_globs`, default `["knowledge/research/**/FINDINGS*.md"]`;
`finding_id_pattern`, default `\b[A-Z]{2,}(?:-[A-Z0-9]+)?-\d+\b`).

## 5. `run-audit` skill flow (`.claude/skills/run-audit/SKILL.md`)

1. **Step 0 pre-check** — confirm `scripts/checks.py` and
   `scripts/audit_scope.py` exist and run; stop immediately if not.
2. **Discover** — `<py> scripts/checks.py --list`.
3. **Run** — either quick `--floor` (check-family only, undated, CWD) or
   full `--report --date YYYY-MM-DD` (both families, dated, lands in
   `output/checks/<date>/`).
4. **Triage** — read the JSON artifacts in `output/checks/<date>/`; apply
   judgment on real defects vs. noise. **"The skill's LLM value is in this
   step"** (SKILL.md:57) — this is the seam a new composition pass would
   plug judgment into.
5. **Anchor (operator-gated)** — `audit_scope.py tag --date ...`, only if
   the operator explicitly says "tag"/"anchor this audit." Sole repo-state
   mutation.
6. **Log** — `audit_scope.py log-line --date ... --essence "..."`, printed
   line appended to `knowledge/audit-log.md`. Sole tracked-file write.

**Staleness cadence line already present** (SKILL.md:86-88, verbatim):
> "Trigger a full audit from the inventory signal (`audit_anchor.commits_since`),
> not a calendar — run one when `commits_since` grows large enough that the
> baseline may be stale."

This is prose guidance only — no numeric threshold, no automated trigger, no
check that reads it and fires. See Direct-answer §2 below.

Guardrails: `checks.py` never mutates repo state; `audit_scope.py tag` is
the sole mutation; the `knowledge/audit-log.md` append is the sole tracked
write; the skill never edits/creates/deletes code or tracked files itself.

## 6. `knowledge-drift-review` skill (brief)

Trigger: operator-invoked or periodic; explicitly **not** run on every
archive (that's reserved for the cheap deterministic `knowledge_lint.py`
plus a narrow just-shipped-change re-check). Flow: run
`scripts/knowledge_lint.py` first (deterministic), then four judgment
sweeps — Class B (stale "not yet built" claims vs. shipped `archive/`
entries), Class D (intra-doc contradictions), buried-gate sweep (README/
runbook gates absent from `knowledge/questions/INDEX.md` Active). **Detect-
only** — never edits/rewrites/deletes tracked files; produces a structured
findings report grouped by class. This is the closest sibling pattern to
what a "composition-audit" judgment pass would look like: whole-tree sweep,
periodic/pull cadence, detect-only, explicit non-inclusion in the archive
hot path.

## 7. `outstanding-work-review` skill (shape only)

Pull-only, never wired into session boot or `AGENTS.md`
(SKILL.md:18-19,84-86). Steps: gather (`facts.py --check outstanding` →
regenerates `output/facts/outstanding.{md,json}`) → read (JSON's
`open_work`/`untriaged` buckets) → judge (orchestrator triages untriaged
into `knowledge/questions/INDEX.md`, updates `knowledge/roadmap.md`) →
verify (re-run snapshot). Explicit staleness note: "there is no automated
trigger" for this skill itself, though `knowledge_lint.py`'s
`_check_untriaged_age` provides a CI safety-net when untriaged findings age
past a configured window (default 14 days) — i.e., a real
deterministic-cadence check exists, but only for the untriaged-findings
sub-problem, not for "time since last full audit" in general.

## 8. `scripts/scaffold_manifest.txt` confirmation

Grepped for the six research-brief targets:
- `checks.toml` — **absent** (per-repo config, not scaffold-managed; §0).
- `run-audit` — present: `.claude/skills/run-audit/SKILL.md` (line 17).
- `knowledge-drift-review` — present: `.claude/skills/knowledge-drift-review/SKILL.md` (line 9).
- `facts.py` — present: `scripts/facts.py` (line 40).
- `audit_scope.py` — present: `scripts/audit_scope.py` (line 37).
- `outstanding-work-review` — present: `.claude/skills/outstanding-work-review/SKILL.md` (line 16).

`scripts/checks.py` itself is also listed (line 38). Everything a new
composition-audit skill would touch except `checks.toml` is scaffold-owned
and propagated via `scripts/sync_scaffold.py` from this repo.

## 9. `knowledge/reference/audit-runbook.md` digest

Operator-facing runbook for running the Fable end-to-end audit against a
downstream repo (extrends, psc-monitor): preconditions (PATH for go-installed
scanners, venv activation, `AUDIT_DB_URL` for data-lint) → `check.sh` green
gate → `checks.py` detector bundle via task-runner targets (`just
audit-report` / `make audit-report`) → `facts.py` orientation snapshots →
`data_lint.py` domain invariants → `knowledge_lint.py`/`status_lint.py` doc
integrity → scaffold-drift check run *from the scaffold repo* (not
downstream) via `sync_scaffold.py --check`. Includes a live per-repo state
table (as of 2026-07-04) showing which floor-tier checks are actually wired
per repo — no downstream repo shown with `jscpd`/`vulture`/`radon` enabled.

## Direct answers

**1. Which detectors are composition/whole-repo-scoped but DISABLED by
default, and what does enabling them require?**
`jscpd` (whole-repo duplication detection) and `vulture` (whole-repo
dead-code detection) are both heavy-tier, `family: "check"`, and
unconditionally `enabled: False` in `_autodetect_defaults`
(`scripts/checks.py:293-295`) — there is no trigger-file heuristic for them
at all (unlike ruff/gitleaks/osv-scanner/deptry, which auto-enable off
pyproject.toml/.git/lockfile presence). `radon` (whole-repo-ish complexity
fact, also feeds `scope`'s hotspot ranking) and `index-coverage` (DB-schema
fact, needs `[checks.index-coverage].schema` configured — no sane default
path exists) are likewise off by default. Enabling any of the four requires
**both** a config flip (`[checks.<name>] enabled = true` in the target
repo's `checks.toml`) **and** the underlying tool installed on PATH
(`jscpd`, `vulture`, `radon` binaries — version-pinned for `jscpd` via
`EXPECTED_TOOL_VERSIONS`, `scripts/checks.py:169-173`; `radon`/`vulture`
version is only ever recorded, never gated). Since they're `family:
"check"` (except radon, which is `family: "fact"`), enabling jscpd/vulture
also puts them under hard preflight — a missing/mismatched tool aborts the
entire `--floor`/`--report` run before anything executes.

**2. Is there any existing cadence/staleness mechanism?**
Partial, and split into two independent pieces that do not talk to each
other automatically. (a) `inventory.audit_anchor` (`{tag, commits_since}`,
`scripts/checks.py:670-676`) and `audit_scope.py scan`'s own
`commits_since` field (`scripts/audit_scope.py:238-301`) both compute
"commits since the last `audit/*` tag" — the raw signal exists and is
written to disk on every `--report`/`facts.py` run. (b) The `run-audit`
skill's prose says to "trigger a full audit... when `commits_since` grows
large enough" (`.claude/skills/run-audit/SKILL.md:86-88`) — but this is
judgment-only guidance with **no numeric threshold, no automated check, and
no code that reads `audit_anchor.commits_since` and fires/flags anything.**
(c) The one genuinely automated cadence check in the repo is narrower and
unrelated: `knowledge_lint.py`'s `_check_untriaged_age` flags untriaged
findings older than a configured window (default 14 days) — a real
deterministic staleness gate, but scoped to the outstanding-work sub-problem,
not to "time since last composition/whole-repo audit." **What's missing for
a cadence trigger:** a deterministic check (or a `checks.toml`/`facts.py`
gate) that reads `audit_anchor.commits_since` (or wall-clock days since the
tag's commit date) against a configured threshold and surfaces/gates on it —
today that arithmetic exists nowhere except as advisory prose for the LLM
operator to eyeball.

**3. How does `run-audit` decide scope today?**
It doesn't choose per-check scope itself — it just runs whatever the
registry says. `checks.py --floor`/`--report` always execute enabled checks
over their own configured `paths` (default `.`, i.e. whole-repo, for
ruff/deptry/radon/jscpd/vulture) or their tool-native full-repo scope
(gitleaks, osv-scanner, inventory). The one check that *is* delta-scoped is
`scope` itself (`audit_scope.py scan`): full-repo if no `audit/*` tag
exists yet, else delta since the last tag. So today's "scope decision" is
binary per-check-type, not a single cadence-driven repo-wide switch: most
checks are always whole-repo every run; only the `scope`/hotspot-ranking
fact is delta-aware, and only for ranking purposes (it never gates or
narrows what other checks scan).

**4. What convention must a NEW skill + NEW checks.toml entry follow to be
scaffold-managed and propagate downstream?**
Scaffold-managed status is purely a `scripts/scaffold_manifest.txt`
membership question (`scripts/checks.py:37-45` for skills already listed as
the pattern): add the new skill's path (e.g.
`.claude/skills/<new-skill>/SKILL.md`) to the manifest under the "Skills
(.claude)" section, and any new supporting script (e.g. a new
`scripts/composition_audit.py`) under "Scripts." `sync_scaffold.py`
(invoked from the scaffold repo, not downstream — see §9) then propagates
listed files verbatim into extrends/psc-monitor. **`checks.toml` itself is
explicitly NOT scaffold-managed** (§0/§8) — a new registry entry
(`jscpd`/`vulture`-style heavy check, or a wholly new composition-audit
check) must be added to `_REGISTRY` in `scripts/checks.py` (scaffold-owned,
propagates via the manifest) but its `enabled`/`args`/`paths` values stay
per-repo, set in each downstream repo's own `checks.toml` — the scaffold
change only ships the capability + auto-detect default, never flips it on
in a specific repo.
