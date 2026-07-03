# Tasks — delegated-agent-safety

Context for every task: this is the golden-source repo. All paths are repo-relative. **Do NOT run
`sync_scaffold.py` against any downstream repo** — propagation is frozen; scaffold-managed edits here
join the pending-sync queue. Implement sequentially, top to bottom, checking off each task as it
lands. Acceptance criteria are in `notes.md`; the normative contracts are the three delta specs under
`specs/`.

## 1. (a) Verifier data-safety — permission denylist + preamble

- [ ] 1.1 In `.opencode/agents/openspec-verifier.md`, replace the single frontmatter line
      `  bash: allow` with a `bash:` pattern-map denylist. Catch-all FIRST (opencode is
      last-match-wins), then deny the destructive verbs. Use exactly this block (2-space indent,
      matching the sibling `task:`/`external_directory:` maps):
      ```yaml
        bash:
          "*": allow
          "rm *": deny
          "rmdir *": deny
          "mv *": deny
          "dd *": deny
          "truncate *": deny
          "shred *": deny
          "tee *": deny
          "sqlite3 *": deny
          "psql *": deny
          "mysql *": deny
          "mongo *": deny
          "mongosh *": deny
          "redis-cli *": deny
          "git push*": deny
          "git commit*": deny
          "git reset*": deny
          "git checkout*": deny
          "git restore*": deny
          "git clean*": deny
          "git rebase*": deny
          "git merge*": deny
          "bash -c*": deny
          "sh -c*": deny
          "python -c*": deny
          "python3 -c*": deny
          "node -e*": deny
          "node --eval*": deny
          "ruby -e*": deny
          "perl -e*": deny
      ```
      (The interpreter `-c`/`-e` eval forms are denied because they are the primary wrapper-evasion
      path for a destructive command; the verifier never needs them for its legitimate work — it runs
      the suite via `pytest`/`scripts/test-cmd`/`python -m pytest`, none of which use `-c`/`-e`. A
      denied command fails LOUD and recoverable, never a silent data loss. Known trade-off, documented
      in notes.md: a downstream repo whose canonical test/eyeball command is itself a `bash -c`/
      `python -c` wrapper will surface a permission denial the orchestrator must grant an exception for.)
      Leave `read/edit/glob/grep/list/task/webfetch/websearch/external_directory` exactly as they are
      (do NOT touch the existing `external_directory: {"*": deny, "/tmp/**": allow}` — it is retained).
- [ ] 1.2 In the same file's prompt body, add a `## Data safety` section (place it immediately before
      the existing `## Prohibitions` section) stating, as the judgment layer: never issue writes to a
      live or production data store; when eyeballing a real-output sample, read via read-only queries
      against a copy or a test fixture, never the live store; the frontmatter `bash` denylist blocks
      the sharp direct/piped/substituted destructive commands AND interpreter-eval wrappers, but is a
      backstop, not a license — the vectors it still cannot cover are: writes performed *inside* an
      allowed test/smoke command (the real backstop is repo-level test isolation — test-DB fixtures +
      blanked live credentials), output redirection to a data-store path, and determined multi-step
      evasion. State plainly that no single control fully closes the hazard. Keep it tight (a short
      paragraph or bullet list), in the file's existing voice.
- [ ] 1.3 Fix the now-stale accuracy claim in `.claude/skills/openspec-verify-change/SKILL.md`: the
      parenthetical that reads `bash: allow`, `edit: deny` for the verifier agent (around the line
      that introduces "The verifier agent is defined in `.opencode/agents/openspec-verifier.md`")
      SHALL be updated to describe `bash` as "a destructive-command denylist (catch-all allow)" rather
      than a blanket `bash: allow`; keep `edit: deny`. Do not otherwise alter that line or the skill.
- [ ] 1.3b Fix the same now-stale claim in `AGENTS.md` **Roles section** (the `## Roles` shared span):
      the `openspec-verifier` bullet's parenthetical that reads `(`bash: allow`, `edit: deny`)` on the
      "**read-only on files**" line SHALL be updated to `(bash restricted to a destructive-command
      denylist, `edit: deny`)` so the boot-read authority matches the actual agent definition. Do NOT
      rename the `## Roles` anchor or alter other Roles content. This edits the shared span (joins the
      frozen queue). After this edit `python3 scripts/scaffold_lint.py` must still exit 0.
- [ ] 1.4 Confirm no stale `bash: allow` verifier claim survives: `grep -rn "bash: allow" .`
      repo-wide. The only legitimate remaining `bash: allow` occurrences are the apply/archive
      executors (`.claude`/`.opencode`, unchanged) and historical mentions under
      `openspec/changes/archive/` (immutable — leave them). Any hit in a NON-archive instruction file
      or an in-flight `openspec/changes/<other>/` describing THIS verifier must be reconciled.
      `pytest -q` stays green after 1.1–1.3b.

## 2. (b) Sanctioned mid-session handoff — `knowledge/HANDOFF.md`

- [ ] 2.1 Edit `AGENTS.md` **inside the MANDATORY blockquote** (the shared span). Insert the new
      instruction as its OWN `>`-quoted sentence immediately after the sentence that ends
      "…scan the entries relevant to the current task." and BEFORE the sentence beginning
      "If you are *resuming an in-progress OpenSpec change*". Exact content (one sentence): if
      `knowledge/HANDOFF.md` exists, read it right after `knowledge/STATUS.md` — it is an ephemeral
      mid-session, pre-archive handoff from a session that ran out of context; absorb it, continue the
      work it describes, and **delete it once absorbed** (its normal state is absent). **Anchor safety
      (load-bearing):** the new line MUST begin with the `>` quote prefix followed by ordinary prose —
      it must NOT begin with any of the three anchor strings (`> **MANDATORY`, `## Roles`,
      `## After reading this file`) and must NOT open with a bold span that could form a false anchor
      match; `scaffold_lint`'s anchor-uniqueness check keys on `line.startswith(anchor)`. Do NOT rename
      or move any anchor heading — the span-merge and `scaffold_lint` depend on them.
- [ ] 2.2 Edit `knowledge/README.md` (scaffold-managed, synced byte-identical): (a) add a taxonomy
      table row — `| Mid-session handoff | What in-flight work must I resume? | `knowledge/HANDOFF.md`
      (ephemeral; deleted on absorption) | boot-if-present |` — placed directly under the `State` row;
      (b) add a short **Usage Note** bullet describing the write side and lifecycle: a session writes
      `knowledge/HANDOFF.md` when it must hand off before archive (e.g. context exhausted mid-change);
      STATUS.md is the wrong home because it is reconciled only at archive; the next session absorbs
      and deletes it; there is exactly one such file (superseding ad-hoc multiple root HANDOFF files).
- [ ] 2.3 Verify the AGENTS.md span-merge still reconstructs cleanly after 2.1:
      `python3 scripts/scaffold_lint.py` exits 0 (anchors intact), and
      `python3 scripts/sync_scaffold.py --check ../psc-monitor` (READ-ONLY check — this does not write)
      reports the AGENTS.md shared-span behavior unchanged. **Do not run a real sync.** If `--check`
      cannot reach a downstream repo in this environment, instead assert idempotence locally by
      confirming `scaffold_lint` passes and the anchors are unique.

## 3. (c) Sync drift beacon — `.scaffold-version`

- [ ] 3.1 In `scripts/sync_scaffold.py`, add two helpers near the other `_`-helpers:
      `_scaffold_version()` → returns a one-line provenance string from the scaffold HEAD by running
      `git` with the argv list `["git", "-C", str(_scaffold_root()), "show", "-s",
      "--format=%h %cI %s", "HEAD"]` (the `--format=%h %cI %s` is ONE argv element; `.stdout.strip()`;
      deterministic per commit — uses the commit's committer date `%cI`, NOT wall-clock). It returns
      the literal string `"unknown"` on `FileNotFoundError`/`subprocess.CalledProcessError`/empty
      output. `_write_provenance_beacon(target_path)` → best-effort writes `<target>/.scaffold-version`
      containing `f"scaffold-sync: {_scaffold_version()}\n"` (so an unresolvable HEAD yields exactly
      `scaffold-sync: unknown\n`), swallowing `OSError` so beacon failure never raises.
- [ ] 3.2 Call `_write_provenance_beacon(target_path)` at the END of `sync()` (after the copy loop and
      the existing `_warn_if_hook_unwired(target_path)` call). Do NOT call it from `check()` or
      `check_references()` — the beacon is written only by the full `sync` action.
- [ ] 3.3 Confirm the beacon is NOT added to `scripts/scaffold_manifest.txt` and is NOT compared by
      `check()` (it iterates manifest lines only, so no change to `check()` is needed). This preserves
      the `check-mode-reports-drift` contract.
- [ ] 3.4 Add tests to `scripts/test_sync_scaffold.py`. **Fixture caveat (from review — do not skip):**
      `SyncIntegrationTest.setUp` patches `sync_scaffold._scaffold_root` to a fixture dir that has NO
      real `.git` repo, so inside that class `_scaffold_version()` returns `"unknown"`. Therefore split
      the tests by what each needs:
      (a) **real-SHA path — NO `_scaffold_root` patch.** A standalone test (own class, not
          `SyncIntegrationTest`) calls `sync_scaffold._scaffold_version()` directly against the real
          repo and asserts the returned string STARTS WITH the real short-SHA from
          `subprocess.run(["git","-C",<real scaffold root>,"rev-parse","--short","HEAD"])` and contains
          a space (SHA + date + subject). This validates the helper against a real git HEAD.
      (b) **beacon content + idempotence — monkeypatch `_scaffold_version` to a STABLE FAKE** (e.g.
          `"abc1234 2026-01-01T00:00:00+00:00 fake subject"`) so the test asserts a KNOWN value, not
          the accidental `"unknown"`: after two `sync(target)` runs the `<target>/.scaffold-version`
          file is byte-identical AND equals `"scaffold-sync: abc1234 2026-01-01T00:00:00+00:00 fake subject\n"`.
      (c) **non-manifest / check-unaffected — no git dependency.** After a `sync(target)`,
          `check(target)`'s captured stdout does NOT contain `.scaffold-version` and its return code is
          identical to a `check` run where no beacon was written. (Beacon is non-manifest, so `check`
          — which iterates manifest lines only — is structurally blind to it.)
      (d) **best-effort/unknown — monkeypatch `_scaffold_version` → `"unknown"`;** assert
          `_write_provenance_beacon(target)` does not raise and writes exactly `scaffold-sync: unknown\n`.
      Read the existing fixture helpers first and reuse `_make_fixture_target` where a target is needed.

## 4. (d) New-repo bootstrap checklist reference

- [ ] 4.1 Create `knowledge/reference/new-repo-bootstrap.md` (scaffold-LOCAL on-demand reference — do
      NOT add to the manifest). Document the manual per-repo wiring a `cp -r`/sync does not perform,
      each step verified against the real repo: (1) wire `.claude/settings.json` `PreToolUse` →
      `scripts/scaffold_check.py` (the sync-time warning from `sync_scaffold.py` flags its absence —
      reference that warning); (2) arm the commit-test gate: create `scripts/test-cmd` invoking the
      repo's test command and confirm `scripts/test-gate.sh` runs it; (3) fill the per-repo AGENTS.md
      `## Project context` and `openspec/config.yaml` `context:` block; (4) seed `knowledge/STATUS.md`
      and `knowledge/questions/INDEX.md`; (5) run `python3 scripts/scaffold_lint.py` and
      `python3 scripts/knowledge_lint.py` clean. Cross-reference the drift beacon `.scaffold-version`
      (task 3) as the provenance stamp a fresh repo carries after its first sync. Keep it a concise
      checklist, not a handbook.
- [ ] 4.2 Confirm `python3 scripts/knowledge_lint.py` stays clean with the new file present (no stale
      path tokens, no dangling citations introduced).

## 5. Whole-change verification gate (pre-handoff to verify phase)

- [ ] 5.1 Full suite green: `pytest -q` from repo root (NOT `python3 -m pytest`).
- [ ] 5.2 `python3 scripts/scaffold_lint.py` exits 0 (anchors, dangling-refs, budgets all clean).
- [ ] 5.3 `git status` clean except the intended edits and the new files
      (`knowledge/reference/new-repo-bootstrap.md`, the change dir). No stray `.scaffold-version`
      written into THIS repo (the beacon is only written into a *sync target*, never the scaffold).
