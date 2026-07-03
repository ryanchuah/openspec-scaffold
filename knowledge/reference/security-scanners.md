# Security scanners — required tools & provisioning

Agent-neutral reference for the two security scanners the scaffold expects, their pinned
versions, and how to provision them **per environment**. The scaffold *documents and provisions*
these tools; per-repo **CI enforcement** (making a scan failure block a merge) is downstream
wiring, deferred to D1/D2 — this doc is the single source for *what* to install and *how*.

## The two scanners

| Tool | Detects | Pinned version | Go module path (`go install …@<version>`) |
|---|---|---|---|
| `gitleaks` | Secrets / credentials committed to the repo | `v8.30.1` | `github.com/zricethezav/gitleaks/v8` |
| `osv-scanner` | Known CVEs in declared dependencies (OSV database) | `v2.4.0` | `github.com/google/osv-scanner/v2/cmd/osv-scanner` |

Both are **Go binaries** — hence `go install` is the canonical local provisioning path. Pinned
versions are the current latest as of 2026-07-03 (verified against each project's GitHub releases);
bump them by editing the variables at the top of `scripts/install-tools.sh` **and** this table
together.

> **Gotcha — gitleaks module path.** gitleaks' Go module path is `github.com/zricethezav/gitleaks/v8`
> (the original author's namespace), **not** `github.com/gitleaks/gitleaks` (the current repo owner).
> A path built naively from the repo owner fails to resolve. `osv-scanner`'s CLI main package lives
> under `/v2/cmd/osv-scanner`, per its own README.

`deptry` (unused-/missing-dependency linter) is **not** in this table: it is a Python tool provisioned
via pip dev extras, not a standalone binary.

## Provisioning per environment

**CI — use the official GitHub Actions (recommended).** Do not run the local helper in CI; wire the
maintained actions, which handle download, checksum, and caching:
- gitleaks → `gitleaks/gitleaks-action`
- osv-scanner → `google/osv-scanner-action`

The actual CI wiring (workflow steps that fail the build on a finding) is **per-repo** and is tracked
as downstream work D1/D2 — it is not shipped by the scaffold itself.

**Local development — `go install` via the helper.** Run `bash scripts/install-tools.sh`. It requires
the Go toolchain (`go`) on PATH and installs both scanners at the pinned versions into
`$(go env GOPATH)/bin` (make sure that dir is on your PATH). It is idempotent — `go install` at a
pinned version reinstalls the same build. If `go` is absent the helper **warns and points here, then
exits 0** (degrade-don't-block, mirroring `scripts/check.sh`'s posture on absent tooling) rather than
hard-failing a bootstrap.

**Local development — package manager (alternative).** Both tools are widely packaged (e.g. Homebrew:
`brew install gitleaks osv-scanner`). A package-manager install will not honor the exact pins above,
so prefer `go install` (or the CI actions) where version-exactness matters.

## Notes

- **No automatic CVE-drift bump.** The pinned versions are updated by hand; there is no
  dependabot/renovate auto-bump wired for them (a parked operator decision). Re-check the latest
  releases periodically and bump the table + `scripts/install-tools.sh` together.
- **Bootstrap order.** Provisioning these scanners is step 6 of
  `knowledge/reference/new-repo-bootstrap.md`; ruff (the lint/format engine behind `scripts/check.sh`)
  is a separate Python dev dependency (step 7), not covered here.
