# Single-source file sharing across sibling polyrepos — pattern comparison

Research date: 2026-06-14
Scope: share `.claude/skills/`, `.opencode/agents/`, `AGENTS.md`, `ai-docs/` from `openspec-scaffold` (golden source) into `extrends` and `psc-monitor`.

## The constraint that drives everything

The agent tools (Claude Code, OpenCode) read these files from a **fixed relative path inside each repo's working tree** (e.g. `<repo>/.claude/skills/...`, `<repo>/AGENTS.md`). So whatever we pick, the files (or something the OS transparently resolves to them) must be **physically present on disk at the expected path** in each repo. This single requirement disqualifies any approach that leaves the path empty until an extra fetch step runs, and penalizes any approach whose materialization can silently be skipped.

Three minor practical facts about the toolset:
- Both tools read files via normal filesystem APIs, so a resolved **symlink is read transparently** — the tool never knows it followed a link (UNVERIFIED for OpenCode specifically; verified by general OS semantics — a symlink is "a file with special mode containing the path to the referenced file" and "Knowing how to handle links is the OS job" — https://mokacoding.com/blog/symliks-in-git/).
- Submodule subdirectories are **empty until `git submodule update` runs** — see below.
- Single human operator, occasional edits, likely 1–2 machines, Linux primary.

---

## 1. git submodule

Point a subdir (e.g. `.agent-config/`) in each repo at the scaffold repo, then have `.claude/skills` etc. live inside it (or be symlinked from it).

**Update flow.** Edit + commit + push in the scaffold repo. Then, in *each* consumer repo: `git submodule update --remote`, which "will go into your submodules and fetch and update for you" (https://git-scm.com/book/en/v2/Git-Tools-Submodules). That advances the recorded pointer; you must then `git add` the submodule and commit the new gitlink in the consumer. So an update is **N+1 commits** (1 scaffold + 1 per consumer) plus a fetch in each.

**Files physically present?** Partially / conditionally. After a plain clone the submodule directory exists but is **empty**: "The `DbConnector` directory is there, but empty. You must run two commands from the main project: `git submodule init` ... and `git submodule update` to fetch all the data" (https://git-scm.com/book/en/v2/Git-Tools-Submodules). You avoid this only with `git clone --recurse-submodules`. This is the core risk for our hard requirement: **a fresh clone or a forgetful checkout leaves the agent-config path empty, and the tools silently see no skills.**

**Detached HEAD pain (verbatim).** "Git would get the changes and update the files in the subdirectory but will leave the sub-repository in what's called a 'detached HEAD' state. ... even if you commit changes to the submodule, those changes will quite possibly be lost the next time you run `git submodule update`." (https://git-scm.com/book/en/v2/Git-Tools-Submodules). Because the operator wants to *edit* shared files often, this is exactly the dangerous path: editing inside a detached-HEAD submodule risks losing work unless they first checkout a branch.

**.gitmodules friction.** Adds a tracked `.gitmodules` mapping file plus a special `160000` gitlink entry per consumer. URL choice matters: "the URL in the .gitmodules file is what other people will first try to clone/fetch from, make sure to use a URL that they can access" (same source).

**Verdict for this case:** technically meets "files in repo" only if every clone/checkout is disciplined; the empty-on-clone + detached-HEAD-on-edit behaviors fight directly against "single operator who edits often." Overkill ceremony for 3 repos.

---

## 2. git subtree

Vendor the scaffold contents into a subdir of each consumer with `git subtree add -P <prefix> <repo> <ref>`, update with `git subtree pull`, contribute back with `git subtree push`.

**Files physically present?** **Yes, unconditionally.** The files are committed as ordinary files in the consumer repo. "Unlike submodules, subtrees do not need any special constructions (like *.gitmodules* files or gitlinks) be present in your repository, and do not force end-users of your repository to do anything special... A subtree is just a subdirectory that can be committed to, branched, and merged along with your project" (https://man.archlinux.org/man/git-subtree.1). A plain `git clone` gets everything — no detached HEAD, no init step. This is the big win over submodules for our hard requirement.

**Update flow.** Edit in scaffold → in each consumer `git subtree pull -P <prefix> <repo> <ref> --squash`. `--squash` "import[s] only a single commit from the subproject, rather than its entire history" (https://man.archlinux.org/man/git-subtree.1), keeping consumer history clean. Two-way is possible: `git subtree push` splits the prefix back out to the scaffold — useful if the operator edits the shared files inside a consumer and wants to promote the change up.

**Per-repo ceremony / failure modes.** The `subtree pull` command is long and must carry the right `-P` prefix and `--squash` consistently; forgetting `--squash` once pollutes history. Subtree has no man page in core git and "help calls like `man git-subtree` ... are not implemented" (per Atlassian/community docs; git bundled it since 1.7.11) — so the operator must keep the exact command in a Makefile or alias. Merge conflicts can occur on pull if the consumer locally diverged. Repo size grows by the vendored content (trivial here — config/docs are small).

**Verdict for this case:** strong contender. Files always present, plain-clone-safe, optional push-back. Cost is remembering verbose commands — easily wrapped in a Make target.

---

## 3. Symlinks

Symlink each repo's `.claude/`, `.opencode/`, `AGENTS.md` to a central checkout of the scaffold (e.g. `~/Projects/openspec-scaffold/...`).

**Do tools resolve them?** Yes — the OS resolves the link transparently on read; the tool reads the target file as if it were local (general OS semantics; see source above).

**Do they survive git?** Git *can* version a symlink: "a symbolic link is nothing but a file with special mode containing the path to the referenced file" stored as git mode `120000`. But what gets committed is **the link text, not the target's contents.** So if you commit the symlink, anyone cloning who lacks the central checkout at the same path gets a dangling link → empty config → silent tool failure. If instead you `.gitignore` the links and create them per-machine, then **the shared files are NOT committed into each repo** — which violates the hard requirement that files be physically (content-)present and self-contained in each repo.

**Cross-machine / portability.** Fragile. Absolute symlinks break on any other machine/path. Relative symlinks are "more portable" — "The reference path of the source file should be relative to the repository, not absolute" (https://mokacoding.com/blog/symliks-in-git/) — but a relative link from one sibling repo into another assumes a fixed directory layout. Worst is Windows: per git-config, `core.symlinks` "If false, symbolic links are checked out as small plain files that contain the link text... The default is true, except git-clone or git-init will probe and set core.symlinks false if appropriate when the repository is created" (https://git-scm.com/docs/git-config) — i.e. on filesystems/OSes without symlink support the checkout yields a **plain text file containing the path string**, not a working link, so the agent reads garbage.

**Verdict for this case:** lowest ceremony for a single Linux machine (one `ln -s` setup), but it fails the "self-contained repo" requirement (committed link = no content; ignored link = nothing in repo) and is brittle cross-machine. Acceptable only as a local-only convenience, not as the distribution mechanism.

---

## 4. Sync / generation script (scaffold canonical → copy into each repo, committed)

Keep scaffold as the single source; a script copies canonical files into each consumer where they are **committed as ordinary files**. This is essentially the operator's current manual process, automated.

**Files physically present?** **Yes, unconditionally** — they are real committed files; plain clone is complete and self-contained. No git plumbing, no .gitmodules, no detached HEAD, no symlink resolution.

**Update flow.** Edit scaffold → run `make sync` (or a `sync.py`) that copies the canonical tree into all three repos → review the diff in each → commit. One scaffold edit, then a single command fan-out.

**Best-practice automation (the part worth getting right):**
- **One-way, source-of-truth copy** with a manifest listing exactly which paths are shared (so non-shared per-repo files are never clobbered).
- **Drift detection via checksums:** a `--check` mode that hashes canonical vs. consumer files and exits non-zero on mismatch. Wire it into a **pre-commit hook** (or CI) in each consumer so a drifted/hand-edited copy is caught before commit. (Best-practice pattern; general engineering consensus — UNVERIFIED against a single canonical citation.)
- **Write a "DO NOT EDIT — generated from openspec-scaffold" header** into generated files so a human doesn't edit the wrong copy.
- Optionally a **reverse-promote** mode (consumer edit → copy back to scaffold) for when fixes originate downstream.

**Failure modes.** The script is bespoke code you maintain. Drift if someone edits a consumer copy directly (mitigated by checksum check + header). Forgetting to run it after a scaffold edit (mitigated by a scaffold pre-push hook that warns, or CI). No standard tooling, but the logic is trivial and fully under operator control.

**Verdict for this case:** best fit. It satisfies the hard requirement perfectly (real files, self-contained, plain-clone-safe), has near-zero git friction, works identically on any OS, and the only "cost" is a ~50-line script the operator already conceptually runs by hand. Adds drift safety the manual process lacks.

---

## 5. Package distribution (npm/pip/git-dependency + postinstall materialize)

Publish the scaffold as an installable package; each repo declares it as a dependency and a `postinstall` step copies the files into place.

**Files physically present?** Only **after install + after a postinstall copy runs.** They live in `node_modules`/site-packages until the hook materializes them — and you'd typically still need to commit the materialized copy (or re-run install on every clone), reintroducing a sync step anyway.

**Critical, current failure mode (load-bearing).** npm is removing automatic install scripts. Per GitHub's June 2026 announcement of npm v12 (release "next month," i.e. July 2026): "npm install will no longer execute preinstall, install, or postinstall scripts from dependencies unless they are explicitly allowed in the project" and "npm install will no longer resolve Git dependencies, either direct or transitive, unless explicitly allowed via --allow-git" (https://thehackernews.com/2026/06/github-to-disable-npm-install-scripts.html). GitHub calls install-time scripts "the single largest code-execution surface in the npm ecosystem." **This means the postinstall-materialize trick is becoming opt-in/blocked by default, and git-URL deps are blocked by default** — exactly the two mechanisms this approach relies on. (Python/pip has long had analogous discouragement of arbitrary build-time code; UNVERIFIED for an exact pip citation here.)

**Update flow / ceremony.** Bump version in scaffold → publish to a registry (or tag a git dep) → `npm update`/`pip install -U` in each consumer → re-materialize → commit. Heaviest ceremony of all options: versioning, publishing, a registry or git-dep config, plus a postinstall that is now adversarial to the ecosystem's secure-by-default direction.

**Verdict for this case:** worst fit. Massive overhead (publishing pipeline, version bumps) for 3 personal repos, files not natively present, and the core materialization mechanism is being disabled by default in the npm ecosystem this very month. Only makes sense if the scaffold were a widely-distributed public product, which it is not.

---

## Comparison table

| Pattern | Update flow | Per-repo ceremony | Files physically present? | Cross-machine | Failure modes | Fit for this case |
|---|---|---|---|---|---|---|
| **git submodule** | scaffold commit → `submodule update --remote` + commit gitlink in each | High (.gitmodules + gitlink; init/update on clone) | **Conditional** — empty until `submodule update`; needs `--recurse-submodules` | OK if everyone runs update; clone discipline required | Empty-on-clone; **detached HEAD loses edits**; URL must be reachable | Poor — fights "edit often" + self-contained |
| **git subtree** | scaffold commit → `subtree pull -P … --squash` in each | Medium (verbose commands; wrap in Make) | **Yes** — committed real files, plain clone complete | Good (no special checkout) | Verbose/forgotten flags pollute history; pull conflicts; no man page | Good — plain-clone-safe, optional push-back |
| **Symlinks** | edit central checkout once; all repos see it instantly | Lowest (one-time `ln -s`) | **No** (content) — committed link = link text only; ignored link = nothing in repo | **Poor** — abs paths break; Windows checks out as plain text file | Dangling links → silent empty config; `core.symlinks` false on some FS | Local-only convenience, not a distribution mechanism |
| **Sync script** | scaffold edit → `make sync` fan-out → review diff → commit | Low (one command; pre-commit checksum guard) | **Yes** — real committed files, self-contained | **Excellent** (OS-agnostic plain files) | Bespoke code; drift if hand-edited (mitigated by checksum + header) | **Best** — meets hard req, minimal friction, adds drift safety |
| **Package dist** | version bump → publish → `npm/pip update` → re-materialize → commit | Highest (registry/version/postinstall) | Only after install + postinstall copy | Depends on registry access | **npm v12 disables postinstall + git deps by default (Jul 2026)**; pip analogous | Worst — heavy + mechanism being disabled |

---

## Prose verdict — ranked for THIS use case

1. **Sync/generation script (RECOMMEND).** A canonical scaffold plus a `make sync` (or `sync.py`) that copies a manifest of shared paths into each consumer, committed as ordinary files, with a `--check` checksum mode wired into a pre-commit hook and a "generated — do not edit" header. It is the only option that perfectly satisfies the hard requirement (real, self-contained, plain-clone-safe files), is OS-agnostic, has trivial per-edit ceremony, and adds the drift detection the current manual process lacks. It is also closest to what the operator already does, so adoption cost is near zero.
2. **git subtree.** The best *git-native* option: files are always physically present and a plain clone is complete, with optional `subtree push` to promote downstream fixes back up. Loses to the script only on the verbose/error-prone command surface and merge-conflict handling. A reasonable pick if the operator prefers pure-git over maintaining a script.
3. **git submodule.** Native and explicit, but the empty-on-clone behavior and detached-HEAD edit-loss directly conflict with "single operator who edits the shared files often." Too much foot-gun for a 3-repo personal setup.
4. **Symlinks.** Fine as a *local* developer convenience on one Linux box, but cannot be the committed distribution mechanism without violating self-containment, and breaks cross-machine / on Windows.
5. **Package distribution.** Heaviest machinery for the smallest benefit, files not natively present, and the npm ecosystem is actively disabling the exact postinstall + git-dependency mechanisms this approach needs (npm v12, July 2026).

**Biggest risk of the top pick (sync script):** *silent drift / wrong-copy editing* — the operator (or an agent) edits a generated copy in a consumer repo instead of the scaffold, and the next `make sync` either clobbers the fix or the copies quietly diverge. Mitigation is mandatory, not optional: a checksum `--check` mode enforced by a pre-commit hook in each consumer plus a conspicuous "DO NOT EDIT — generated from openspec-scaffold" header in every synced file (and ideally a reverse-promote command so downstream fixes have a sanctioned path back up).

---

## Sources

- git submodules (empty-on-clone, detached HEAD, .gitmodules, `update --remote`): https://git-scm.com/book/en/v2/Git-Tools-Submodules
- git subtree (no .gitmodules/gitlinks, `--squash`, split/merge): https://man.archlinux.org/man/git-subtree.1
- symlinks in git (mode, relative-path caveat): https://mokacoding.com/blog/symliks-in-git/
- `core.symlinks` behavior / plain-file fallback: https://git-scm.com/docs/git-config
- npm v12 disabling install scripts + git deps by default (Jul 2026): https://thehackernews.com/2026/06/github-to-disable-npm-install-scripts.html
- subtree vs submodule overview (context only): https://www.atlassian.com/git/tutorials/git-subtree

### Claims I could not fully verify (labeled UNVERIFIED in text)
- That **OpenCode specifically** resolves symlinks transparently (relied on general OS semantics, not an OpenCode doc).
- The exact **checksum/pre-commit drift-detection** workflow as a single citable "best practice" (it is general engineering consensus, not one authoritative page).
- An exact **pip/Python** citation for build-time-code discouragement analogous to the npm change.
