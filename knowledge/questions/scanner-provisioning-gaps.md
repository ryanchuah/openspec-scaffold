# Security-scanner provisioning gaps — parked

Two gaps surfaced by the extrends + psc-monitor agents while enabling gitleaks/osv
in their audit layers (2026-07-04). Both touch scaffold-managed surfaces, so a fix
belongs upstream here. Neither blocks the Fable audit — both have live workarounds.

## Gap 1 — `install-tools.sh` installs gitleaks with no embedded version (scaffold bug)
`scripts/install-tools.sh` provisions gitleaks via
`go install github.com/zricethezav/gitleaks/v8@v8.30.1`. gitleaks stamps its version
through a build-time ldflag that **`go install` does not set**, so the resulting binary
reports `unknown`/dev and `checks.py`'s version-pin preflight sees a **version mismatch**.

- **Consequence:** re-running `bash scripts/install-tools.sh` overwrites
  `~/go/bin/gitleaks` with a go-install build and **re-breaks** any working version match.
- **Live workaround (both repos):** install the official **release** binary (gitleaks
  8.30.1) into `~/go/bin` by hand, not via `go install`. Recorded in each repo's
  `checks.toml` gitleaks header.
- **Candidate fix (needs lifecycle):** have `install-tools.sh` download the pinned
  release binary (or pass the ldflag, or drop the version-pin check for go-install
  gitleaks). osv-scanner does NOT have this problem — `go install` versions it fine.

## Gap 2 — `$(go env GOPATH)/bin` not on non-interactive PATH (operator env + doc nicety)
Agents reported `checks.py` reporting gitleaks/osv **unavailable** in the non-interactive
shell even though the interactive shell resolved them.

- **Root cause (confirmed 2026-07-04):** NOT a "forgot to source .bashrc" timing issue.
  `~/.bashrc` returns early for non-interactive shells (the standard Debian guard,
  `case $- in *i*) ;; *) return;; esac`), and the `export PATH="$HOME/go/bin:$PATH"`
  line sits **after** that guard. So interactive shells get `~/go/bin`; non-interactive
  ones (`opencode run` subshells, cron, CI, harness Bash) hit `return` first and never
  reach the export. **Re-sourcing `.bashrc` would not help** — the guard fires first.
- **Fix (operator env):** move the go PATH export to `~/.profile` (or above the guard),
  or set `PATH` explicitly in any cron/CI/opencode invocation.
- **Scaffold angle (minor):** `install-tools.sh` already says "ensure $(go env GOPATH)/bin
  is on your PATH" but doesn't warn about the non-interactive gotcha; `checks.py`
  preflight could hint it. Low priority — mostly an operator-env fix, not a scaffold bug.
