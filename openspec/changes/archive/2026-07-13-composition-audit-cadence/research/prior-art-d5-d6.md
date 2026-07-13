# Prior art: D5/D6 from deterministic-tooling-layer (archived 2026-07-02)

Source: `openspec/changes/archive/2026-07-02-deterministic-tooling-layer/` — read-only
extraction for OW-6 (cadenced composition-audit). No files in that archive or elsewhere
were modified to produce this digest.

Naming note up front: the archive's design vocabulary (`audit_bundle.py`, `audit.toml`)
was renamed in a later change, `2026-07-03-checks-facts-split` (`audit_bundle.py` →
`checks.py`; config file is `checks.toml` today, not `audit.toml`). All D5/D6 mechanics
below still apply to the current `scripts/checks.py`; only the filenames changed.

## 1. Decision D5 — dead-code/duplication/complexity triage campaign

Verbatim, `explore-brief.md:118-122`:

> **D5 — Dead code/duplication/complexity promoted** (operator override of the initial ranking):
> LLM-authored code accumulates orphaned helpers and re-implementations, and ~10.5k lines landed
> since June with no inventory. Delivery: audit-bundle report + ONE triage campaign
> (cheap-model pre-digest → shortlist → operator/Fable rules → vulture whitelist) — **not** a CI
> gate (gates on these metrics cause endless bikeshedding).

Restated in the follow-ons section, `notes.md:177-178`:

> **Dead-code/duplication/complexity triage campaign** (brief D5): one-time cheap-model pre-digest →
> shortlist → operator/Fable rules → vulture whitelist.

Also in the tool roster table, `explore-brief.md:181`:

> | Dead code / duplication / complexity | vulture / jscpd / radon | report + one campaign, per D5 |

**Intended shape (four stages, explicit in the quote):**
1. Detectors run (vulture, jscpd, radon) and dump a report — this is what `checks.py`
   produces today (`checks.toml` heavy tier, disabled by default per D8e).
2. **Cheap-model pre-digest** — a cheap/fast model clusters and dedupes the raw detector
   wall and drafts summaries. Per D2 (`explore-brief.md:105-107`), these are explicitly
   "**labeled as unverified claims/leads, never ground truth**" — never trusted output.
3. **Shortlist** — the pre-digest narrows the wall to a small candidate list for a human/
   stronger-model pass.
4. **Operator/Fable rules** — a judgment pass decides real defects vs. false positives vs.
   deliberate patterns (e.g. pytest magic, unpacked-but-unused test variables).
5. **Vulture whitelist** — the outcome is encoded as a vulture whitelist file so the
   *same* false positives never resurface as findings in later runs.

This was explicitly scoped as **ONE campaign, not a recurring gate** — "gates on these
metrics cause endless bikeshedding" (D5 rationale). OW-6 wiring a *recurring* composition
pass over these same detectors is a deliberate departure from D5's "one-time" framing and
should be justified against this rationale.

**Whitelist mechanics seeded** — `notes.md:151-152` (forward-looking items):

> **Vulture whitelist campaign seeds (D5):** `conftest.py collect_ignore` (pytest magic) and one
> unused unpacked test variable — deliberately left.

No dedicated `checks.toml` key exists for "vulture whitelist path" — `scripts/checks.py`
has no `whitelist` config key (grepped; zero hits). The whitelist mechanism is vulture's
own native one: a whitelist `.py` file is passed as an extra scan path/arg. In
`checks.toml` terms this means adding the whitelist file to `[checks.vulture].paths` or
`.args` — there's no purpose-built whitelist field in the engine.

## 2. Decision D6 — first cycle is a full re-audit; delta-scoping pays off from cycle 2

Verbatim, `explore-brief.md:123-125`:

> **D6 — First cycle is a full re-audit.** Build bundle → run detectors → triage first-run wall
> ONCE (this produces the tuned configs + baseline) → `git tag audit/<date>` + append
> `knowledge/audit-log.md` → Fable audits with the bundle as index. Delta-scoping pays from cycle 2.

Restated in the follow-ons section, `notes.md:174-176`:

> **First audit cycle (operator-driven):** full `--report` run → first-run wall triage ONCE →
> tuned configs + baseline committed downstream → `audit_scope.py tag` + audit-log line → Fable
> audit with the bundle as index. Delta-scoping pays from cycle 2 (brief D6).

And in the D8 agent-consumption contract, `explore-brief.md:139-141`:

> (d) **Baseline diffing kills the wall** — after the
> D6 first-cycle triage produces tuned configs + a baseline, agents and audits see *deltas*, not
> the full detector wall; D2's cheap-model pre-digest handles the one remaining wall (audit time).

**What "delta-scoping" concretely means** — a literal prior-findings JSON file, diffed by
content fingerprint, not a git diff of source:

- `checks.py --report --baseline <prior-findings.json>` (design spec in
  `tasks.md:166-176`, task 4.6 "Baseline diff (D6/D8d)"; implemented in
  `scripts/checks.py` — `_baseline_diff` at line 1090, CLI wiring at 1394-1401, 1434-1440).
- Each finding is fingerprinted as
  `sha1("\0".join([check, rule, path, message]))` over normalized fields — **deliberately
  line-number-insensitive so pure code moves don't churn the delta** (`tasks.md:168-172`;
  restated `notes.md:53-54`: "Baseline fingerprints are line-number-insensitive... so pure
  code moves don't churn the delta; exit code follows NEW findings only").
- Output: `<out>/delta.json` = `{new: [...], resolved: [...], unchanged_count}` plus a
  one-line summary `delta: <n> new, <m> resolved vs <baseline-path>` (`tasks.md:173-175`;
  implemented `checks.py:1394-1401`).
- **Exit code is governed by NEW findings only** — a repo with old unresolved findings but
  zero new ones still exits 0 (`tasks.md:175-176`). This is the actual "wall killer": once
  a baseline exists, every subsequent run only surfaces what changed.
- `--baseline` is valid ONLY with `--report` (usage error / exit 3 otherwise —
  `tasks.md:166-167`, `checks.py:1439-1440`). A floor-mode baseline was explicitly
  deferred ("not v1", `tasks.md:167`).

Concretely: the "baseline" IS the prior run's `findings.json` (or a curated subset of it),
not a git ref and not a separate schema — comparison is run N's `findings.json` against a
file path the caller supplies for run N-1 (or whichever run was last triaged). There is no
automatic "always diff against last run" default; the caller must pass `--baseline`
explicitly each time, meaning OW-6's cadenced wiring needs to decide/own how it tracks and
supplies "the current baseline path" between scheduled runs — that plumbing does not exist
yet.

## 3. Other cadence / recurrence / triage / whitelist / LLM-layering notes

**D9 — drift-prevention posture** (`explore-brief.md:145-159`) ties audit-log to a
recurring maintenance loop, not just the first cycle:

> Maintenance loop, explicit: when a pinned tool
> breaks or is upgraded, the operator bumps the pin and re-runs the baseline triage to absorb the
> changed findings — tool rot always surfaces as a loud bundle failure, and recovery is a pin bump
> plus re-baseline, never a silent drift.

**D2 — three-level prep pyramid** (`explore-brief.md:105-107`), the shape LLM judgment
layers onto detector output, reused verbatim by D5's campaign shape:

> **D2 — Three-level prep pyramid for the audit:** free scripts → cheap-model pre-digestion
> (flash/Sonnet clusters + dedupes the detector wall, drafts summaries **labeled as unverified
> claims/leads, never ground truth**) → Fable does judgment only.

**D8 tiered drill-down** (`explore-brief.md:138-139`): "exit code → per-check counts →
filtered JSON query → raw findings; agents descend only where nonzero."

**Cadence, as actually implemented downstream of this archive** (not in the archive
itself, but the live mechanism the archive's D6/D9 fed into) — `.claude/skills/run-audit/SKILL.md:86-92`:

> **Staleness cadence.** Trigger a full audit from the inventory signal
> (`audit_anchor.commits_since`), not a calendar — run one when
> `commits_since` grows large enough that the baseline may be stale.
>
> **Annual re-justify.** Once per year (at minimum), re-justify every entry in
> the suppression baseline / whitelist — tools and configurations drift, and
> suppressions that were correct at baseline may mask regressions.

This is the closest existing artifact to a "cadence policy" for OW-6 to build on: trigger
is a commits-since counter (a fact, not a calendar cron), with a separate annual floor for
re-justifying suppressions. `run-audit` is explicitly **operator-invoked**, not scheduled —
OW-6's job of wiring detectors into a "recurring, triggered composition pass" is new
territory relative to what shipped; nothing today auto-triggers `checks.py --report`.

**First-run wall triage** is D6's phrase for the one-time acceptance of full detector
noise on cycle 1 (`explore-brief.md:123`: "triage first-run wall ONCE (this produces the
tuned configs + baseline)"). It is the *general* mechanism D5's campaign is a specific
instance of (D5 = the triage campaign for one detector category; D6 = the overall
first-cycle-absorbs-noise policy for the whole bundle).

## 4. `knowledge/audit-log.md` — current state and exact line format

`knowledge/audit-log.md` **does not exist** in this repo yet (checked directly: file
absent). The format is nonetheless enforced by a guarded linter check and generated by a
CLI subcommand, both already shipped:

**Linter regexes**, `scripts/knowledge_lint.py:145-148`:

```python
_AUDIT_LOG_ANCHOR_RE = re.compile(r"^- \*\*\d{4}-\d{2}-\d{2}\*\*")
_AUDIT_LOG_FULL_RE = re.compile(
    r"^- \*\*\d{4}-\d{2}-\d{2}\*\* · audit/\d{4}-\d{2}-\d{2} · [0-9a-f]{7,40} · \S.*$"
)
```

The check (`_check_audit_log`, `scripts/knowledge_lint.py:499-518`) only runs if the file
exists ("guarded"); any line matching the anchor regex but not the full regex is flagged
`audit-log-registry-format`.

**Exact generator**, `scripts/audit_scope.py:363` (`cmd_log_line`, the `log-line`
subcommand — prints, never writes):

```python
print(f"- **{args.date}** · audit/{args.date} · {short_sha} · {args.essence}")
```

So a real line looks like:
`- **2026-07-11** · audit/2026-07-11 · a1b2c3d · <free-text essence>`

Per the `run-audit` skill (`.claude/skills/run-audit/SKILL.md:66-71`), appending this line
to `knowledge/audit-log.md` is "the **sole tracked-file write**" of the audit cycle, and
happens only when the operator explicitly asks to tag/anchor — never automatically.

## 5. `checks.toml` — baseline/whitelist configuration today

No `checks.toml` exists at this repo's root (confirmed: only `ruff.toml` present) — it is
explicitly **per-repo, not scaffold-managed** (`scripts/checks.py:23-26`, `notes.md:28`).
The schema lives only in the `checks.py` module docstring + `--help` (deliberate — no
standing doc file, per D1/knowledge-recoverability). Relevant keys, quoted from
`scripts/checks.py`:

- `[tools]` (lines 41-42): "version-pin overrides for `EXPECTED_TOOL_VERSIONS` (binary
  tools only: gitleaks/osv-scanner/jscpd by default)."
- `[checks.<name>]` (lines 44-52): `enabled` (bool, overrides auto-detection), `args`
  (list[str]), `paths` (list[str], default `["."]"` — this is where a vulture whitelist
  file would be added, since there is no dedicated whitelist key).
- `[checks.custom.<name>]` (lines 62-68): `command` (argv list), `tier`
  (`floor|heavy|snapshot`, default `heavy`), `gate` (bool, default `true`).
- Heavy tier — `radon`, `jscpd`, `vulture`, `index-coverage` — **default DISABLED absent
  explicit config** (lines 31-34): "on-demand/audit-time per the brief's D8e."
- Baseline is NOT a `checks.toml` key — it is a CLI flag only:
  `--baseline <prior-findings.json>`, valid only with `--report`
  (`scripts/checks.py:1434-1440`).
- `_load_config` (`scripts/checks.py:270-276`) confirms the filename directly:
  `config_path = repo_root / "checks.toml"`; return source is `"checks.toml"` or
  `"defaults"`.

**Implication for OW-6:** there is no standing "last baseline path" or "last run" pointer
in `checks.toml` or anywhere else — every `--baseline` invocation names an explicit prior
`findings.json` path by hand. A cadenced/recurring composition pass needs its own
mechanism (or a small addition here) to track which findings.json is "current baseline"
across runs; that plumbing is a genuine gap, not something D6 already solved end-to-end.
