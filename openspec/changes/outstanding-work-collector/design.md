## Context

The proposal splits "what work is outstanding?" into a mechanical **gather** (a deterministic
snapshot) and a judgment **judge** (an LLM, whose durable output stays in `knowledge/questions/` +
`roadmap.md`). This design fixes HOW the gather works, where per-repo variation lives, and which
drift the deterministic layer catches.

**Prose-gap measurement (opens the design, per the premise review).** A read-only scan of the two
downstream repos measured how much outstanding work is mechanically extractable vs. prose-only:

| Source | extrends | psc-monitor | Extractable? |
|---|---|---|---|
| `questions/INDEX.md` Active | ~16 (in **tables**) | 30 (bullets) | yes — but **format-plural** |
| `questions/INDEX.md` Parked pointers | 15 | 7 | yes (one-liners w/ `→ path`) |
| audit `FINDINGS*` IDs | 4 files, **non-`CA-W` scheme** | 56 `CA-W…` IDs / 2 files | yes — but **per-repo ID scheme** |
| `roadmap.md` entries | 4 (**3 closed-but-unpruned**) | 2 (1 closed) | yes |
| non-archive `tasks.md` boxes | 0 | 0 | yes when present |
| `questions/` per-item files | 11 | 10 | **point-only** (prose) |
| `plans/` files | 60 | 25 | **point-only** (prose) |
| in-code `TODO/FIXME` | 2 | 1 | negligible |

**Conclusions that drive the decisions below:** (1) structured extraction is **load-bearing**, not
marginal (~95 items in psc), so the gather is worth more than a file list; (2) extraction is
**format-plural** (extrends' Active is tables, psc's is bullets) and (3) the finding-ID handle is
**per-repo** (extrends does not use psc's `CA-W…`), so both need per-repo config; (4) `plans/` and
per-item files are **point-only** — the gather enumerates them with provenance/metadata, it does not
parse items from them; (5) unpruned-closed roadmap entries are a **real, present** drift (3/4 in
extrends).

## Goals / Non-Goals

**Goals:**
- One command yields a **provably complete** snapshot of outstanding work (never silently skips a
  source), with `source:line` provenance and a **separate untriaged-findings bucket**.
- The snapshot is **regenerate-on-use** (never stale) and **never crashes** (fact-family contract).
- Per-repo variation (finding location, ID scheme, extra dirs) is **configured, not hardcoded**.
- Deterministic drift (duplicate blocks, unpruned-closed) is caught **automatically in CI**.
- Everything is **agent-neutral** and **pull-only** (zero boot-context cost).

**Non-Goals:**
- Parsing item-level state out of prose bodies (per-item files, plan narratives) — those are
  point-only.
- Producing priority/dependency judgment — that stays with the LLM/`questions/`.
- A new tracked backlog document; retroactive cleanup of existing duplicate/stale/`plans/` debt
  (per-repo hygiene, tracked separately).
- In-code TODO scanning as a load-bearing source (optional, lowest-priority).

## Decisions

**D1 — The gather is a `facts.py` fact named `outstanding`, dispatched as `kind="delegate"`.**
Registered in `scripts/checks.py` `_REGISTRY` as
`{"name": "outstanding", "tier": "snapshot", "kind": "delegate", "family": "fact"}` — matching the
existing delegate facts `scope` and `index-coverage`. A new `if name == "outstanding":` arm in
`_run_delegate` calls a dedicated stdlib module `scripts/outstanding.py` (`main(argv)`) that holds all
gather logic and is the **single home** of source-enumeration + finding-extraction (imported by the
`knowledge_lint` untriaged check too — see D8, so the two never diverge). Run via
`facts.py --check outstanding`. It is unconditionally enabled in `_autodetect_defaults`
(`"outstanding": True`, like `inventory` — no external dependency), so the all-facts run includes it,
not only `--check`. Rationale: the fact family is already "regenerate-on-use, never-fails,
output under `output/facts/`", and `delegate` is how every non-builtin fact plugs in.
**`kind="custom"` is rejected because it is incompatible with the engine:** `_run_custom` expects a
`command` to run as a subprocess (else INFRA-FAIL) and emits `.txt`, and `_custom_checks` hardcodes
`family="check"` — a custom entry can never be a fact. A standalone script (not registered) is also
rejected: it would re-implement the fact runner and lose the `facts.py`/`output/facts/` plumbing.

**D2 — Malformed source → skip-and-flag (resolves the never-fails vs. completeness tension).** A
source that cannot be parsed is **not** dropped and does **not** crash the fact: it is emitted as an
explicit `UNPARSEABLE — read manually: <path> (<reason>)` line in the snapshot. This preserves both
the fact-family "never-fails" contract **and** the completeness guarantee (nothing is silently lost;
the gap is made visible). Alternative (skip silently) rejected — breaks completeness; (crash)
rejected — breaks the fact contract.

**D3 — Structured extraction is format-plural and per-repo-configured.** The `questions/INDEX.md`
Active+Parked extractor parses **both** markdown list items **and** table rows (a `| … |` line that
is not a header/separator) — extrends uses tables, psc uses bullets. Concrete extraction rules
(pinned so the executor does not improvise): a **list item** is a line matching `^\s*[-*]\s+\S` or
`^\s*\d+\.\s+\S`; a **table row** is a `|`-delimited line that is neither the header row nor a
separator (`^\s*\|?\s*:?-{3,}`); **Active vs Parked** is decided by the enclosing `## Active` /
`## Parked` heading. Finding extraction reads a per-repo `finding_id_pattern` and `findings_globs`
(D10). Where a source has no recognized structure, the gather falls back to **point-only** (enumerate
the file + first heading + git `mtime`/tracked state), never fabricating items.

**D4 — Untriaged bucket = findings not yet cross-referenced into `questions/`.** A finding ID that
appears in a configured `FINDINGS*` glob but **nowhere under `knowledge/questions/`** is "newly
surfaced — untriaged." The `questions/` scan covers **`INDEX.md` and every `knowledge/questions/*.md`
per-item file** (same scope the gather enumerates), so promoting a finding into any question file
triages it. Mechanical, no state file. The snapshot renders two buckets: **Open work
(triaged)** and **Newly surfaced — untriaged (N; oldest <git-date>)**. Triage (promoting the ID into
`questions/`) is what moves it between buckets. Rationale: gives the operator's "first-class the
moment Fable writes it" requirement without treating raw leads (often refuted on graduation) as
confirmed backlog.

**D5 — Output: a markdown snapshot plus a JSON sibling.** `output/facts/outstanding.md` (human/LLM
orientation) and `output/facts/outstanding.json` (structured, for the judging LLM / the skill to
consume). **Split responsibility:** the engine provides `out_path`
(`out_dir/outstanding.json`) and the delegate arm *fills* it (same as `scope`/`index-coverage`); the
`.md` sibling is written by `outstanding.py` itself. Both regenerated each run; undated; overwritten. Rationale: markdown for
reading, JSON so the judge consumes a clean structure instead of re-parsing prose.

**D6 — `plans/` live-vs-archived convention: a `plans/archive/` subdir.** Top-level `plans/*.md` =
**live**; `plans/archive/**` = shipped/closed (excluded from the gather's live list). The gather
lists live plans point-only. Rationale: the measured `plans/` swamp (60 / 25 files) mixes live work
with permanent citation-anchors; a subdir is the lowest-ceremony split that a script and a human both
read unambiguously, and it does not orphan `decisions/INDEX.md` citations (they repoint to
`plans/archive/…`). Alternative (per-file status frontmatter) rejected for v1 — heavier, and every
legacy file would need editing; the subdir needs only a move.

**D7 — `knowledge_lint.py` gains two detect-only checks** (rides the existing live-tree pytest gate +
CI; detect-only, never rewrites). Both are implemented as new functions —
`_check_duplicate_blocks(...)` and `_check_closed_unpruned(...)` — and **must be added to
`collect_findings()`** (the aggregator at `knowledge_lint.py:535`) to actually execute:
- **duplicate-content-block:** flags ≥ 8 consecutive non-trivial lines identical (whitespace-
  normalized) across 2+ files in a **narrow** compared set — markdown under `knowledge/` + top-level
  `*.md` + a per-repo-configurable `duplicate_scan_dirs` (read from the existing **`[knowledge_lint]`**
  config table, e.g. `compliance/`). **Excludes** `knowledge/research/` (period history) and
  `openspec/specs/` (legitimately shares scaffold spans). A `<!-- lint:dup-ok -->` marker suppresses a
  finding **when the marker line falls inside the detected duplicate window** (a distinct mechanism
  from the line-scoped `<!-- lint:planned -->` — it correlates the marker's position with the
  duplicate span, not a single line). Rationale: the measured harm was a
  verbatim triple-copy of a to-do list; an 8-line floor + narrow scope bounds false positives.
- **closed-but-unpruned:** flags a `roadmap.md` `## ` entry or a top-level `plans/*.md` file whose
  heading / `**Priority:**` / `**Status:**` line carries a closed-token (`CLOSED`, `DONE`,
  `COMPLETE`, `✅`, or a `~~…~~` heading) — signalling it should graduate to the archive/`plans/archive/`.
  Flag-only (a warning finding, same exit-1 family), with a `<!-- lint:keep -->` opt-out for a
  deliberately-retained short-lived closed note.

**D8 — Accumulation safety-net for the pull-only tension.** Because invocation is pull-only, a third
`knowledge_lint.py` function `_check_untriaged_age(...)` (also wired into `collect_findings()`) flags
when an **untriaged finding is older than `untriaged_max_age_days`** — converting silent accumulation
into an automatic CI signal with **zero boot-context cost**. Flag-only. **Shared implementation (no
divergence):** the finding-extraction + untriaged cross-reference lives once in `scripts/outstanding.py`
(D1); `knowledge_lint.py` **imports** it rather than re-implementing (both are stdlib-only
scaffold-managed scripts in `scripts/`; `knowledge_lint` already belongs to the linter family). The
shared API surface is `outstanding.extract_untriaged(root: Path, config: dict) -> list[dict]` returning
`[{"id": str, "file": str, "age_days": int}, ...]` — consumed by both the fact's snapshot render and
the linter's age check. **Age
proxy:** the git last-commit date of the containing `FINDINGS*` file (`git log -1 --format=%ct`,
degrading to filesystem `mtime` when git is unavailable — consistent with the linter's existing
git-optional walk). Config (`untriaged_max_age_days`, default 14) lives under **`[knowledge_lint]`**;
the `findings_globs`/`finding_id_pattern` it needs are read from `[facts.outstanding]` via the shared
module. Rationale: answers the reviewer's "is the untriaged pile a sufficient signal if nobody looks"
— the CI check looks, cheaply. Alternative (a session-boot nudge) rejected — boot-context tax +
Claude-only.

**D9 — Invocation: the `outstanding-work-review` skill, pull-only.** Lives in
`.claude/skills/outstanding-work-review/SKILL.md`; auto-discovered by both harnesses; loaded on
demand. It runs `facts.py --check outstanding`, reads the JSON, and guides the orchestrator through
judging (into `questions/`/`roadmap`, reconciled durably at archive by the existing archive-executor
— no spec change to `knowledge-organization`). No session hook, no AGENTS.md procedure (at most a
one-line pointer, decided at apply).

**D10 — Per-repo config surface, split by consumer.** Fact-consumed keys go under
**`[facts.outstanding]`**: `findings_globs` (default `["knowledge/research/**/FINDINGS*.md"]`) and
`finding_id_pattern` (a permissive default; repos with a scheme like `CA-W\d+-\d+` override).
Linter-consumed keys go under the existing **`[knowledge_lint]`** table: `duplicate_scan_dirs`
(default `[]`) and `untriaged_max_age_days` (default `14`). Splitting by consumer avoids the linter
reading a fact's config section. **Unconfigured behavior is graceful:** this repo has **no
`checks.toml` today** and the loader returns defaults on absence, so defaults must suffice for a clean
run; a repo creates `checks.toml` only for non-default settings. No matching findings → an empty
untriaged bucket (not an error). Rationale: the measurement proved finding schemes differ per repo;
hardcoding would silently miss extrends' findings entirely.

## Risks / Trade-offs

- **Prose-only sources stay point-only** → the gather guarantees you *read* every per-item file and
  plan, but the LLM still reads their bodies. *Mitigation:* that is the honest, correct boundary;
  completeness (never skip a source) is the guarantee, not item extraction. Accepted.
- **Per-repo config drift** — a repo mis-configures `finding_id_pattern` and its findings silently
  don't surface. *Mitigation:* the snapshot prints the active config + a count of findings-files
  scanned vs. IDs matched, so a zero-match against non-empty files is visible.
- **duplicate-block false positives** on legitimately-repeated boilerplate. *Mitigation:* 8-line
  floor, narrow scope, `<!-- lint:dup-ok -->` opt-out, detect-only (never rewrites).
- **closed-token heuristic** could miss an idiosyncratic "done" phrasing or over-flag. *Mitigation:*
  flag-only + `<!-- lint:keep -->`; the fixed token set is documented and extendable per-repo later.
- **Scaffold propagation** — the fact/skill/linter changes must land byte-identical downstream.
  *Mitigation:* add new managed files to `scaffold_manifest.txt`; verify via `sync_scaffold.py
  --check`; per-repo `checks.toml` `[facts.outstanding]` is per-repo (not synced), like other
  per-repo check config.

## Migration Plan

1. Land the fact, skill, `knowledge_lint` checks, and the `plans/archive/` convention in
   openspec-scaffold; add new managed files to `scaffold_manifest.txt`; green suite (incl. the
   `scaffold_lint` SEAL and the live-tree knowledge_lint gate).
2. Propagation (operator-gated, separate authorization): `sync_scaffold.py <repo>` for each
   downstream repo; each repo adds its `[facts.outstanding]` config and (optionally) moves shipped
   plans into `plans/archive/`.
3. Rollback: the fact and checks are additive and detect-only; disable via `checks.toml`
   `enabled=false` (fact) or revert the `knowledge_lint` extension. No data migration, no destructive
   step.

## Verification (change-specific acceptance criteria)

- `facts.py --check outstanding` on this repo and on a synthetic fixture tree **exits 0** and writes
  both `output/facts/outstanding.{md,json}`; a deliberately malformed source yields an `UNPARSEABLE`
  line and **still exits 0** (D2).
- On a fixture with a finding ID absent from `questions/`, that ID appears in the **untriaged**
  bucket; after adding a `questions/` reference to it, a re-run moves it to **triaged** (D4).
- The extractor pulls Active items from **both** a bullet-form and a table-form `INDEX.md` fixture
  (D3).
- `plans/archive/**` files are excluded from the live list; top-level `plans/*.md` are listed (D6).
- `knowledge_lint.py` **flags** a planted ≥8-line duplicate block across two in-scope files and a
  planted closed-but-unpruned roadmap entry; **does not flag** the same under a `<!-- lint:dup-ok -->`
  / `<!-- lint:keep -->` marker, nor a <8-line incidental repeat, nor content in
  `knowledge/research/` (D7).
- `knowledge_lint.py` flags an untriaged finding older than `untriaged_max_age_days` and does not
  flag one within the window (D8).
- `sync_scaffold.py --check <repo>` reports convergence after the new managed files are added
  (propagation invariant).
- Full `pytest -q` green including `scaffold_lint` and the live-tree knowledge_lint gate.

## Open Questions

- Exact default `finding_id_pattern` — permissive-but-useful without over-matching prose. To pin
  during apply against both repos' real findings files.
- Whether `duplicate-content-block` compares across the whole in-scope set pairwise (O(n²) over a
  small file set — fine) or hashes N-line windows (cheaper). An apply-time implementation choice;
  behavior (what counts as a duplicate) is fixed above.
- Whether the one-line AGENTS.md pointer to the skill is worth its (tiny, permanent) boot cost — an
  apply-time call, defaulting to **no pointer** unless it proves needed.
