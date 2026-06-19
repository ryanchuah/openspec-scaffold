# OpenSpec Skill Regeneration: Footgun Analysis & Mitigation Options

**Date:** 2026-06-18  
**Status:** READ-ONLY research — scaffold/skill source files were not modified.

---

## Task 1 — Regeneration Mechanics (with file:line citations)

### 1a. What set of skills does `openspec update` regenerate?

The skill set is keyed on a **hardcoded `SKILL_NAMES` array** at
`OpenSpec/src/core/shared/tool-detection.ts:14-26`:

```
'openspec-explore', 'openspec-new-change', 'openspec-continue-change',
'openspec-apply-change', 'openspec-ff-change', 'openspec-sync-specs',
'openspec-archive-change', 'openspec-bulk-archive-change',
'openspec-verify-change', 'openspec-onboard', 'openspec-propose'
```

The mapping of workflow ID → directory name lives in
`OpenSpec/src/core/profile-sync-drift.ts:14-26` (`WORKFLOW_TO_SKILL_DIR`).
`getSkillTemplates()` at `OpenSpec/src/core/shared/skill-generation.ts:56-75`
returns templates from an identical hardcoded list, optionally filtered to
the active profile's workflow IDs.

**The `generatedBy` stamp plays NO role in choosing which directories to write.**
It is only read for version comparison (see §1c). Removing or altering the stamp
does not take a directory out of the managed set.

### 1b. Conditional vs. unconditional? Where is the version compared?

`openspec update` (`OpenSpec/src/core/update.ts`) has a two-gate smart-update
detection before it writes anything:

**Gate 1 — version mismatch** (`update.ts:127-139`):  
For each configured tool, `getToolVersionStatus()` is called at
`tool-detection.ts:160-198`. It:
1. Scans `SKILL_NAMES` in order and reads the **first SKILL.md found**.
2. Extracts `generatedBy` via the regex at `tool-detection.ts:145`:
   `content.match(/^\s*generatedBy:\s*["']?([^"'\n]+)["']?\s*$/m)`
3. Returns `needsUpdate = configured && (generatedByVersion === null || generatedByVersion !== currentVersion)` (`tool-detection.ts:189`).
   — Comparison is **strict string equality**.
   — If `generatedBy` is absent/null, `needsUpdate` is `true` (makes it WORSE to remove the stamp).

**Gate 2 — profile/delivery drift** (`update.ts:140-149`):  
`getToolsNeedingProfileSync()` at `profile-sync-drift.ts:166-176` checks
whether any expected skill files are missing or unexpected ones are present
(relative to the active profile's workflow set). This check is **independent of
the stamp**; if all 7 skill files exist and all match profile, drift is false.

If **both gates are empty** and `--force` is NOT set, `update.ts:152-161`
returns early without writing anything. `--force` bypasses both gates entirely
and always regenerates all skills for all configured tools.

### 1c. Commands too?

Yes. `update.ts:213-230`: if `shouldGenerateCommands`, iterates `commandContents`
and calls `FileSystemUtils.writeFile` for each command file — same unconditional
overwrite pattern. Commands are also regenerated on version mismatch or drift.

### 1d. Any user-modified detection (hash, mtime, skip-if-changed)?

**None.** `FileSystemUtils.writeFile` at `utils/file-system.ts:204-208` is:

```typescript
static async writeFile(filePath: string, content: string): Promise<void> {
  const dir = path.dirname(filePath);
  await this.createDirectory(dir);
  await fs.writeFile(filePath, content, 'utf-8');
}
```

Plain `fs.writeFile`, no read-before-write, no hash, no mtime, no diff, no merge.
`FileSystemUtils.updateFileWithMarkers` at `file-system.ts:214-250` does offer
marker-based in-place splicing, but it is **never called** from either `init.ts`
or `update.ts` for skill generation. It is used for other purposes.

### 1e. `openspec init` vs. `update`

`init.ts` (see `generateSkillsAndCommands`, L494-592) calls the identical
`generateSkillContent()` + `FileSystemUtils.writeFile()` path. Key difference:
`init` has **no version-check gate** — it always writes for every selected tool.
`update` at least skips when both gates are empty. For our scenario, `init` is
strictly more dangerous. The scaffold is already past `init`; the daily risk is
`update`.

### 1f. Any extension seam for customisation?

No seam exists for skill body customisation. Specifically:

- **`FileSystemUtils.updateFileWithMarkers`** — not used by skill generation.
- **Schema override dir** (`artifact-graph/resolver.ts`) — overrides workflow
  *schemas* (YAML graph definitions), not skill bodies.
- **`CollectionHooks`** (`collections/runtime.ts`) — applies to collections, not
  skills.
- **CLI `preAction`/`postAction` hooks** (`cli/index.ts`) — Commander hooks for
  the CLI binary, not a template override mechanism.
- **`--profile` / `delivery`** flags — control which workflow subset is written;
  do not allow per-file body customisation.

**Summary:** There is no sanctioned seam. Any customisation must either live
outside the managed set, be protected by a no-update policy, or be re-applied
as a patch after updates.

---

## Task 2 — Mitigation Assessment

### (a) Drop or alter the `generatedBy` stamp

**Mechanics fit:** The stamp is read from the first skill file found
(`tool-detection.ts:180-184`). The comparison at L189 is strict equality.

- Remove stamp → `generatedByVersion` = null → `needsUpdate` = true → update
  triggers on every run. **Makes things worse.**
- Change stamp to a non-existent version string → `needsUpdate` = true always.
  Same problem.
- Pin stamp to the current OpenSpec version (e.g., keep `"1.4.1"`) → version
  gate is false. Profile drift gate is also false if all 7 skill dirs exist.
  Effectively suppresses the non-forced update.
- But on `npm upgrade openspec`, `OPENSPEC_VERSION` changes → stamp mismatch →
  regeneration triggers again. Must manually bump stamp on every upgrade.
- `--force` bypasses the check entirely regardless.

**Works?** Partly — suppresses accidental `openspec update` at the same version,
but fails on version bump and on `--force`. Requires per-upgrade manual stamp
maintenance.  
**Effort:** LOW initial, recurring per upgrade.  
**UX cost:** LOW (invisible), HIGH maintenance risk due to recurring chore.

---

### (b) Vendor skills under non-OpenSpec directory names

**Mechanics fit:** `getSkillTemplates()` iterates the hardcoded `dirName` list
(all `openspec-*`). `update.ts:191` writes to `path.join(skillsDir, dirName, 'SKILL.md')`.
If our directories are named differently (e.g. `scaffold-apply-change`), OpenSpec
writes fresh `openspec-apply-change/SKILL.md` files ALONGSIDE ours — not instead
of them. We'd end up with both directories on disk, and Claude Code would load
both skill IDs (the upstream plain one and our customised one under a different ID).

More critically: Claude Code resolves skills by directory name = skill ID. Our
7 skills are in `openspec-*` directories and are registered as `openspec-apply-change`
etc. in the `system-reminder`. Renaming them would:
1. Break existing slash-command muscle memory (`/openspec-apply-change`).
2. Require updating every reference in AGENTS.md, downstream READMEs, and
   practitioner documentation.
3. Still leave the `openspec-*` directories to be recreated by OpenSpec with
   vanilla content at the next update.

**Works?** No — does not prevent upstream skill files appearing; causes ID
divergence and breaks invocation.  
**Effort:** HIGH (rename + reference sweep across all repos).  
**UX cost:** HIGH (breaks slash commands, confuses users with duplicate IDs).

---

### (c) Never run `openspec update`; add a CI guard

**Mechanics fit:** Since the scaffold is the single source of truth and
`sync_scaffold.py` copies skills byte-identical to downstream repos (they appear
in `scaffold_manifest.txt`), there is no legitimate reason to run `openspec update`
on the scaffold. The update command is designed to pull OpenSpec CLI changes INTO
a user project; here we want the inverse (we own the canonical bodies).

**Guard design:** The `generatedBy` stamp is a usable, machine-parseable signal.
After any `openspec update` or `openspec init`, the stamp in every SKILL.md
changes to the current OpenSpec CLI version. A CI script can detect this:

```bash
#!/usr/bin/env bash
# scripts/check_skill_stamps.sh
EXPECTED="1.4.1"   # update this intentionally when upgrading OpenSpec
FAIL=0
for f in .claude/skills/openspec-*/SKILL.md; do
  STAMP=$(grep -oP '(?<=generatedBy: ")[^"]+' "$f")
  if [[ "$STAMP" != "$EXPECTED" ]]; then
    echo "FAIL: $f has generatedBy=\"$STAMP\", expected \"$EXPECTED\""
    FAIL=1
  fi
done
exit $FAIL
```

What the guard checks: **stamp value == expected pinned version** for every
skill file in the manifest. Any unintended `openspec update` changes all stamps
to the new CLI version → guard fails → developer is alerted before merge.

When intentionally upgrading OpenSpec:
1. Run `openspec update` on a branch.
2. Manually diff each SKILL.md against the upstream template.
3. Re-apply customisations (delegation block, opencode run invocation, failure
   ladder, NON-CONVERGENCE grep, phase gates).
4. Update `EXPECTED` in `check_skill_stamps.sh`.
5. Merge.

**Works?** YES — fully prevents unintended regeneration from reaching main.  
**Effort:** LOW to set up (one short script + CI entry). LOW per cycle unless
upgrading OpenSpec (then intentional, controlled effort).  
**UX cost:** LOW — zero change to developer invocation or skill IDs. The guard is
only visible when it fires, which is the right time.

---

### (d) Upstream a skill-body extension hook to OpenSpec

**Mechanics fit:** There is no existing seam to hang a PR against. The required
change is non-trivial: add a template override directory resolution step to
`generateSkillContent()`, so that OpenSpec checks (e.g.) `openspec/skill-templates/<dirName>/SKILL.body.md`
before using the built-in template.

This would be a meaningful API addition to OpenSpec. It requires:
- Design and PR to the OpenSpec repo.
- Review/acceptance by OpenSpec maintainers (not under our control).
- Wait for a release.
- Adapt our workflow to use the new mechanism.

Could be worthwhile long-term (benefits everyone with customised deployments),
but is not a near-term solution.

**Works?** Eventually, if PR is accepted. Not now.  
**Effort:** HIGH (upstream PR + negotiation + adaption).  
**UX cost:** LOW once shipped.

---

### (e) Vendor-and-patch (patch-package style)

**Mechanics fit:** Workflow —
1. Keep OpenSpec-generated SKILL.md files as a tracked `base/` branch or
   `patches/base/` snapshot.
2. Store our customisations as unified diff patches in `patches/skills/*.patch`.
3. After any `openspec update`, run `git apply patches/skills/*.patch`.

Patch feasibility: Our customisations are predominantly *prepended* content
(delegation override block at the top, PHASE GATE note, `opencode run` invocation
in Step 6) and specific structural insertions (failure ladder, NON-CONVERGENCE
grep instruction). They are not line-for-line rewrites. This makes patches
relatively stable — conflicts arise only if upstream changes the same section
we touch.

Risks:
- Upstream template body changes near our insertion points → patch conflict →
  manual resolution required.
- Patches must be kept in sync with every OpenSpec release that changes skill
  bodies.
- A developer who forgets to re-apply patches after `openspec update` gets silent
  regression (CI would need to check for this too, e.g., verify delegation block
  present).

**Works?** YES, with ongoing maintenance.  
**Effort:** MEDIUM to set up (create initial patches, write apply script).
MEDIUM ongoing (resolve conflicts per OpenSpec release that touches skill bodies).  
**UX cost:** LOW (no slash-command changes), MEDIUM operational complexity
(extra step in upgrade workflow; patch conflicts need manual resolution).

---

## Task 3 — Recommendation

**Recommended option: (c) — "No-update policy + CI stamp guard."**

### Rationale

The architectural premise of this project is already that the scaffold is the
single source of truth, and `sync_scaffold.py` propagates changes downstream.
This means `openspec update` on the scaffold serves no purpose — its only effect
is to introduce risk. Option (c) codifies this invariant rather than working
around it.

The `generatedBy` stamp is an ideal guard signal: it is present in every SKILL.md,
has a well-defined format (`tool-detection.ts:145`), and changes atomically to the
current CLI version on any `openspec update` or `openspec init`. A simple grep
in CI is sufficient; no additional tooling or dependencies are needed.

This follows the standard "freeze at a known good version + test that freeze"
pattern used by vendored dependency approaches (e.g., `vendor/` directories with
a CI check that `go mod vendor` produces no diff).

### Standard pattern analogy

Closest analogy is **`go mod vendor` with `go mod verify` in CI**: you vendor
the dependency once, pin it, and CI verifies the vendor directory hasn't drifted.
Here the "vendor" is our customised SKILL.md corpus, and the "verify" is the stamp
check. Intentional upgrades follow a controlled process (update → diff → merge
customisations → update stamp → commit).

### Comparison matrix

| Option | Works? | Effort | UX cost |
|--------|--------|--------|---------|
| (a) Alter `generatedBy` stamp | Partial — version-bump & `--force` bypass it | Low initial, recurring | Low, but ongoing maintenance debt |
| (b) Rename skill dirs | No — creates duplicate dirs, breaks skill IDs | High | High — breaks slash commands |
| (c) No-update policy + CI stamp guard | **Yes — fully** | Low setup, low per-cycle | None unless guard fires (correct behaviour) |
| (d) Upstream extension hook to OpenSpec | Eventually, not now | High (upstream PR) | Low once shipped |
| (e) Vendor-and-patch overlay | Yes, with maintenance | Medium setup + medium per upgrade | Low UX, medium ops complexity |

### Strongest objection to (c)

Option (c) **detects** but does not **prevent** the footgun. A developer who runs
`openspec update` locally — without pushing — will silently lose their working copy
of the customised skills. They recover by `git checkout -- .claude/skills/`, but
only if they notice. The CI guard catches it pre-merge, not pre-loss-of-local-work.

Mitigation: add a brief note to CLAUDE.md / AGENTS.md — "Do not run `openspec update`
or `openspec init` on this repo. Skills are managed by the scaffold; use
`sync_scaffold.py` for downstream propagation." — so the policy is visible to any
developer before they act.

---

*End of analysis.*
