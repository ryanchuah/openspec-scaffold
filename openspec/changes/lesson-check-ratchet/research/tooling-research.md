# Tooling research: code-shape-detector slot for the lesson→check ratchet

**Status:** subagent-produced research input (not a decision document)
**Produced:** 2026-07-10
**Scope:** battle-tested options for the "static code-shape detector" slot in the lesson→check ratchet (Python 3.11+ repos, ruff + pytest, `scripts/checks.py` custom-command runner, `checks/*.sql` data-invariant convention). Web research only; no tool choice is made here.

All research was done via `python3 scripts/fetch_clean.py <url>` (never the built-in WebSearch tool), discovering pages through fetched DuckDuckGo search result pages and then fetching only the specific pages cited below.

---

## 1. Semgrep / Opengrep

### What happened (licensing controversy), verified

- Semgrep's **engine** (Semgrep Community Edition, formerly "Semgrep OSS") has been LGPL-2.1 licensed since Semgrep, Inc. began development in early 2020, and **remains LGPL-2.1 today** — this did not change. Source: Semgrep's own FAQ, `docs.semgrep.dev/faq/comparisons/opengrep`.
- What changed in **December 2024**: the license on Semgrep-authored **rules** (the community rules registry) moved from "Commons Clause + LGPL-2.1" to a new proprietary "Semgrep Rules License," which restricts commercial/SaaS/competing use of those rules. The engine license was unaffected. Source: same Semgrep FAQ page, corroborated by Socket.dev's writeup.
- In direct response, a consortium of AppSec vendors (Aikido, Amplify Security, Endor Labs, Kodem, Orca Security, and others — Jit was also an early backer per the InfoQ/thenewstack coverage found in search, not separately fetched) launched **Opengrep** on **2025-01-23** as a hard fork of Semgrep CE. Opengrep's engine is **also LGPL-2.1** (same license family as upstream — it forked the code, not just the rules). Source: `socket.dev/blog/opengrep-forks-semgrep` (published 2025-01-28) and the Opengrep GitHub README.
- Both projects are described by Semgrep itself as "actively adding new features and bug fixes" (i.e., Semgrep does not consider Opengrep dead or vice versa). Source: Semgrep's own FAQ page.
- **Safe-to-adopt read:** for a "just run static code-shape rules on Python, no SaaS login, no rules-registry dependency" use case (which is what the ratchet needs — hand-authored, in-repo rules, not Semgrep's proprietary registry content), **both Semgrep CE and Opengrep are safe**: the engine license (LGPL-2.1) never changed, and hand-written custom rules you author yourself are not subject to the "Semgrep Rules License" restriction (that license only covers Semgrep, Inc.'s own published registry rules). Opengrep exists specifically as an escape hatch if an organization wants zero exposure to Semgrep, Inc.'s commercial roadmap; it claims full backward compatibility with Semgrep rule syntax.

### Rule-authoring ergonomics (Python AST patterns)

- Rules are YAML with a `pattern:` field that looks like ordinary source code (not a DSL, not raw AST/S-expressions), using `$UPPERCASE` metavariables as wildcards, e.g. `$X == $X` to catch a Python equality-with-itself bug. Source: Semgrep GitHub README / PyPI project page (identical content).
- Semgrep's own README lists a "Codify project-specific knowledge" use-case row (e.g., "Verify transactions before making them") — this is explicitly the lesson→check pattern this OpenSpec change is designed around, and it's presented as a first-class supported use case, not an edge case. Source: `github.com/semgrep/semgrep` README / PyPI page.
- Opengrep's README confirms full compatibility: "your existing rules and rulesets work unchanged," so this ergonomics story is identical to Semgrep's.

### Install weight

- `pip install semgrep` works and is the documented Ubuntu/Linux/macOS install path (also available via brew, pipx, uv tool, Docker). Requires Python **>=3.10** (compatible with this project's 3.11+ floor). Current version as of fetch: **1.168.0** (released 2026-06-24), license classifier `LGPL-2.1-or-later`. Source: `pypi.org/project/semgrep/`.
- Semgrep bundles a statically-linked native (OCaml) binary inside the pip wheel. Concrete historical evidence of size: Semgrep, Inc. filed a PyPI package-size **limit-increase request in 2020** because they "recently hit the 100MB upload limit," requesting 110MB (later set to 200MB by PyPI) specifically because "we include a statically linked manylinux binary of the core static analysis engine. As we support more languages the size of that binary will increase." Source: `github.com/pypi/support/issues/681`. **Exact current wheel size not directly re-verified today (PyPI's file-size listing wasn't retrievable from the fetch tool) — treat "still a large (tens-to-100+ MB) binary-bearing wheel" as verified-in-kind but the precise current MB figure as UNVERIFIED.**
- Opengrep, by contrast, ships **self-contained binaries via Nuitka** (no Python runtime required), distributed via a shell/PowerShell installer or direct binary download, with **signed releases (Cosign)**. Source: Opengrep GitHub README.

### Version pinning story

- Semgrep: standard pip pinning (`semgrep==1.168.0`), pipx/uv tool upgrade commands documented. Weekly-ish release cadence (observed on PyPI release history: dozens of releases across 2025–2026, often multiple per month).
- Opengrep: `install.sh` supports `-v <version>` for an exact pinned version install, plus `--verify-signatures` for Cosign signature verification, and `-l` to list the latest 3 available versions. Source: `raw.githubusercontent.com/opengrep/opengrep/main/install.sh` (fetched directly, confirmed in script source).

### Named real-world adopters (custom rules / general use)

- Semgrep's own README/PyPI page states: "Join hundreds of thousands of other developers and security engineers already using Semgrep at companies like **GitLab, Dropbox, Slack, Figma, Shopify, HashiCorp, Snowflake, and Trail of Bits**." Source: `github.com/semgrep/semgrep` README (also mirrored verbatim on the PyPI page).
- This is a general-adoption claim, not specifically "named companies with a custom per-repo rule directory" — I could not find a fetched, named case study of a specific company's custom-rules-directory setup (this narrower claim is **UNVERIFIED**; the closer artifact is Semgrep's own official rule-ideas doc showing the "codify project-specific knowledge" pattern as a supported first-class use case, which is verified).
- Opengrep's backers (Aikido, Amplify Security, Endor Labs, Kodem, Orca Security) are themselves AppSec vendors adopting it as their scan engine, per the Opengrep README and Socket.dev article — this is vendor-adoption evidence, not enterprise-customer-with-custom-rules evidence.

---

## 2. ast-grep

### Maturity / adoption evidence

- GitHub stats surfaced via its PyPI package page: **15,017 stars, 410 forks, 35 open issues** as of fetch (2026-07-10); latest release `ast-grep-cli 0.44.1` published 2026-07-04 (six days before this research — actively maintained). Source: `pypi.org/project/ast-grep-cli/`.
- Named/attributable adoption evidence found (weaker than Semgrep's named-enterprise-logo claim, but real):
  - ast-grep ships its **own official MCP server and prompting/skill docs** for Claude Code and Cursor ("This skill teaches Claude how to write and use ast-grep rules"), i.e., first-party AI-agent tooling integration. Source: `ast-grep.github.io` and search-result snippet from `ast-grep.github.io/advanced/prompting.html`.
  - A LinkedIn post from the "Codemod" platform states "Codemod platform is built on top of ast-grep, a widely used open source technology for understanding and modifying source code" (found via search snippet only — **not independently fetched/verified beyond the search snippet, treat as weak/UNVERIFIED-depth evidence**).
  - A Medium article on CodeRabbit's AI code-review pipeline states its review agent "investigat[es] by writing shell commands in a sandbox (cat, grep, ast-grep)" (found via search snippet only, same caveat).
  - No fetched source gave a "trusted by [named companies]" logo wall comparable to Semgrep's — ast-grep's adoption story is "widely used in the AI-coding-agent tooling ecosystem" rather than "named enterprise security teams," based on what was fetchable today.

### Single-binary install

- Confirmed: written in Rust, ships as a compiled single binary distributable via `npm`, `pip` (`ast-grep-cli`), `cargo`/`cargo-binstall`, `brew`, `scoop`, `MacPorts`, `nix-shell`, or `mise`. No language runtime dependency beyond the binary itself. Source: `github.com/ast-grep/ast-grep` README.

### YAML rule format for Python patterns

- Confirmed: "YAML configuration to write new linting rules or code modification," patterns are written "as if you are writing ordinary code," using `$UPPERCASE` wildcards (same metavariable convention family as Semgrep). `ast-grep scan` is the linter entry point with "pretty error reporting out of box." Source: `github.com/ast-grep/ast-grep` README and `ast-grep.github.io` homepage.

### Version pinning

- Standard package-manager pinning applies (`pip install ast-grep-cli==0.44.1`, `cargo install ast-grep --locked`, npm version pin). `cargo install ast-grep --locked` and `cargo binstall ast-grep` are explicitly documented, and Repology tracks packaging status across distros. Source: `github.com/ast-grep/ast-grep` README.

### Notable corroborating signal (found while researching ruff, not ast-grep directly)

- On the **live Ruff plugin-system tracking issue** (`astral-sh/ruff#283`), a community member suggested ast-grep on 2026-01-21 as the practical way to get YAML/query-based custom Python pattern matching without a ruff plugin system, and the comment was reacted to by **HerringtonDarkholme, ast-grep's own creator** — i.e., ast-grep is being actively pointed to by the Python tooling community as the answer to "I need a custom rule and ruff can't do it." Source: `github.com/astral-sh/ruff/issues/283`.

---

## 3. Custom ruff rules / plugins — current (2026) status

**Verified: still no, as of the most recent activity found (May 27, 2026).**

- Ruff's own official docs answer the exact question directly: "**Can I write my own linter plugins for Ruff?** Ruff does not yet support third-party plugins, though a plugin system is within-scope for the project. See #283 for more." Source: `docs.astral.sh/ruff/faq/` (live docs, fetched today).
- The tracking issue, `astral-sh/ruff#283` ("Meta issue: plugin system"), was opened **2022-09-29** and is **still open** as of the most recent comment found, **2026-05-27** ("I would be happy to also chat about this too and help implement" — jcampbell05). A Ruff core maintainer (MichaReiser) was actively responding to new comments as recently as 2026-01-21, without committing to a timeline. Source: `github.com/astral-sh/ruff/issues/283`.
- Real-world pain point confirmed directly in that issue: multiple users in 2026 reporting they fall back to Flake8 or `pygrep` alongside Ruff specifically to get custom/internal-standard rules (e.g., "I use Ruff daily... But without plugin support, I had to fall back to Flake8 just for these custom rules... now users need two linters instead of one" — leandrodamascena, 2026-01-21; "My team is adding pygrep for a lower-value version of this until ruff implements this" — davidemerritt, 2026-05-26).
- A separate, older Q&A discussion (`astral-sh/ruff#8409`, Nov 2023) got the same answer from a Ruff-adjacent contributor: "If you mean plugins, there is no plugin system yet (though there may be in the future)."
- **Conclusion: ruff cannot be the code-shape-detector slot for custom/per-repo rules** — it remains a fixed, upstream-curated rule set with no user-defined-rule mechanism, confirmed current as of mid-2026.

---

## 4. flake8 / pylint custom plugins (legacy approach)

Both flake8 and pylint have long-standing, real plugin architectures (flake8's `Flake8Checker` entry-point plugins; pylint's "checkers") — this is the reason flake8 became popular in the first place, since "you can find plugins for every possible type of problem." Ruff's own FAQ acknowledges this directly: "Like Flake8, Pylint supports plugins (called 'checkers'), while Ruff implements all rules natively and does not support custom or third-party rules." Teams have largely moved away from hand-rolling flake8/pylint plugins as their primary linter (toward Ruff, which re-implements most popular flake8-plugin rule sets natively in Rust) mainly for **speed** — Ruff is commonly cited as 10–100x faster, meaningfully cutting CI time on large codebases — and to collapse a multi-tool chain (black+isort+flake8+plugins+pylint) into one binary/one config file. The residual reason teams still keep flake8 or pylint around is precisely custom/internal-only rules that Ruff can't yet host (per §3 above) — several 2026-era comments on ruff#283 describe exactly this "keep flake8 around just for our one in-house custom plugin" pattern, and one pydevtools.com guide explicitly frames its migration guide around "the awkward case of keeping flake8 around to run one in-house custom plugin." Sources: `docs.astral.sh/ruff/faq/`, `pythonspeed.com/articles/pylint-flake8-ruff/`, `github.com/astral-sh/ruff/issues/283` search snippets.

---

## 5. Ratchet-process precedent (turning incidents into permanent checks)

Citable facts, most load-bearing first:

1. **Error Prone (Google's Java compiler-integrated analyzer)** states its own purpose in these words on its official site: *"We use Error Prone in Google's Java build system to **eliminate classes of serious bugs** from entering our code, and we've open-sourced it, so you can too!"* — this is the closest verified paraphrase of "if it's worth fixing, it's worth checking forever": Google's own tool literally frames itself as turning discovered bug **classes** into permanent, build-breaking checks. Source: `errorprone.info` (fetched 2026-07-10; page carries a `Published Time` header of 2026-07-04, i.e., current/live).

2. **Tricorder (Sadowski, van Gogh, Jaspan, Söderberg, Winter — ICSE 2015)**, Google's static-analysis platform paper, documents the underlying discipline: analyses that "break the build" (via Error Prone / Clang) must have an effective false-positive rate of essentially zero and <5% compile overhead; analyses surfaced at code-review time must stay under 10% effective-false-positive rate; and the paper gives explicit **criteria for admitting a new analyzer** into the platform (must be "easy to understand," fix must be "clear," "obvious and actionable when pointed out"). This is the documented, peer-reviewed institutional process by which "a problem we keep finding" becomes "a standing automated check," at Google's scale (tens of thousands of engineers). Source: `www.cs.umd.edu/class/spring2019/cmsc414/papers/tricorder-building-a-program-analysis-ecosystem.pdf` (mirror of the ICSE 2015 paper).

3. **"Software Engineering at Google," Chapter 20 (Static Analysis)** states the same philosophy in book form, written by the Google engineers who built this infrastructure: *"Through static analysis at Google, we codify best practices, help keep code current to modern API versions, and prevent or reduce technical debt... We have also found evidence that static analysis checks can educate developers and actually prevent antipatterns from entering the codebase."* The chapter also documents that analyzer proposals are solicited "from throughout the company" — i.e., any engineer who hits a bug class can propose it become a permanent checker. Source: `abseil.io/resources/swe-book/html/ch20.html`.

4. **Google's own retrospective research paper**, "Lessons from Building Static Analysis Tools at Google," frames the entire infrastructure's value proposition as: "Our tooling detects thousands of issues per day that are fixed by engineers, by their own choice, before the problematic code is checked into the codebase" — i.e., institutionalized, continuously-run checks catching issues before merge is treated as Google's flagship large-scale engineering-quality result, not a niche practice. Source: `research.google/pubs/lessons-from-building-static-analysis-tools-at-google/` (abstract fetched; full text paywalled at CACM, `cacm.acm.org/research/lessons-from-building-static-analysis-tools-at-google/`, returned HTTP 403 and was not read beyond the abstract).

I was **not able to fetch** a source using the exact popular paraphrase "if it's worth fixing, it's worth checking forever" (this phrasing may be a secondary summarization of the above sources rather than a direct quote from Google) — **flag this specific wording as UNVERIFIED**; the underlying practice it describes is well-supported by sources 1–4 above.

---

## Sources actually fetched and cited above

- https://docs.semgrep.dev/faq/comparisons/opengrep
- https://socket.dev/blog/opengrep-forks-semgrep
- https://github.com/opengrep/opengrep (README, via raw.githubusercontent.com rewrite)
- https://github.com/semgrep/semgrep (README, via raw.githubusercontent.com rewrite)
- https://pypi.org/project/semgrep/
- https://github.com/pypi/support/issues/681
- https://raw.githubusercontent.com/opengrep/opengrep/main/install.sh
- https://github.com/ast-grep/ast-grep (README, via raw.githubusercontent.com rewrite)
- https://ast-grep.github.io/
- https://pypi.org/project/ast-grep-cli/
- https://github.com/astral-sh/ruff/discussions/8409
- https://github.com/astral-sh/ruff/issues/283
- https://docs.astral.sh/ruff/faq/
- https://pythonspeed.com/articles/pylint-flake8-ruff/
- https://abseil.io/resources/swe-book/html/ch20.html
- https://research.google/pubs/lessons-from-building-static-analysis-tools-at-google/
- https://www.cs.umd.edu/class/spring2019/cmsc414/papers/tricorder-building-a-program-analysis-ecosystem.pdf
- https://errorprone.info/

## Discovery search pages fetched (DuckDuckGo HTML results, used only to find the above; not cited as evidence themselves)

- https://duckduckgo.com/html/?q=semgrep+opengrep+fork+2025+license+controversy (thin content, no result)
- https://html.duckduckgo.com/html/?q=semgrep+opengrep+fork+2025+license (via `--jina-fallback`)
- https://html.duckduckgo.com/html/?q=semgrep+pypi+package+size+dependencies+pip+install
- https://html.duckduckgo.com/html/?q=ast-grep+adoption+companies+using+ast-grep+production
- https://html.duckduckgo.com/html/?q=ruff+custom+lint+rules+plugin+support+2026
- https://html.duckduckgo.com/html/?q=google+tricorder+static+analysis+paper+bug+class+permanent+check
- https://html.duckduckgo.com/html/?q=%22ast-grep%22+used+by+company+testimonial+case+study
- https://html.duckduckgo.com/html/?q=flake8+pylint+custom+plugin+teams+moved+away+ruff+migration
- https://html.duckduckgo.com/html/?q=Tricorder+Building+a+Program+Analysis+Ecosystem+pdf+sadowski
- https://html.duckduckgo.com/html/?q=%22regression+test%22+for+every+bug+fixed+established+practice+testing+on+the+toilet (no usable results)
- https://html.duckduckgo.com/html/?q=testing.googleblog.com+regression+test+bug+%22write+a+test%22 (no results)
- https://html.duckduckgo.com/html/?q=semgrep+install+size+%22MB%22+ocaml+binary+large

## Fetches attempted that failed (dead ends, for transparency)

- https://api.github.com/repos/opengrep/opengrep, https://api.github.com/repos/semgrep/semgrep, https://api.github.com/repos/ast-grep/ast-grep — GitHub REST API JSON responses are not handled by `fetch_clean.py`'s extraction pipeline (thin/empty content); star counts for semgrep/opengrep were not independently obtained this way (ast-grep's stars were instead obtained via its PyPI page's "GitHub Statistics" block).
- https://cacm.acm.org/research/lessons-from-building-static-analysis-tools-at-google/ — HTTP 403 (paywalled/blocked).
- https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/43322.pdf — HTTP 404 (double-slash in the canonical URL did not resolve through the fetch path).
- https://storage.googleapis.com/pub-tools-public-publication-data/pdf/43322.pdf — HTTP 403.
- https://errorprone.info/about — HTTP 404 (no such page; used the homepage instead).
- https://pypi.org/project/semgrep/#files — no size data returned (likely client-rendered).
