#!/usr/bin/env bash
# install-tools.sh — Provision pinned security scanners via go install.
#
# Installs the following (both are Go binaries):
#   gitleaks    — secrets scanner (github.com/zricethezav/gitleaks/v8)
#   osv-scanner — dependency-CVE (vulnerability) scanner
#                 (github.com/google/osv-scanner/v2/cmd/osv-scanner)
#
# Requires the Go toolchain.  go install places binaries in
# $(go env GOPATH)/bin — ensure that directory is on your PATH.
#
# For CI use the official actions instead:
#   gitleaks       → gitleaks/gitleaks-action
#   osv-scanner    → google/osv-scanner-action
#
# deptry — NOT installed here.  It comes via pip dev extras
# (e.g. `pip install -e ".[dev]"` with a pyproject.toml extras
# group).
#
# See also: knowledge/reference/security-scanners.md
#
# Exit conventions:
#   0  → success, or Go toolchain absent (degrade, don't block)
#   ≠0 → go install failed

set -euo pipefail

INSTALL_NAME="install-tools"

# ---- Pinned versions (edit here to bump) ----
GITLEAKS_VERSION="v8.30.1"
OSV_SCANNER_VERSION="v2.4.0"

# ---- Guard: Go toolchain required ------------------------------------------
if ! command -v go >/dev/null 2>&1; then
    echo "${INSTALL_NAME}: WARNING — Go toolchain not found; skipping tool installation" >&2
    echo "${INSTALL_NAME}: For CI, use the official GitHub Actions:" >&2
    echo "${INSTALL_NAME}:   - gitleaks/gitleaks-action" >&2
    echo "${INSTALL_NAME}:   - google/osv-scanner-action" >&2
    echo "${INSTALL_NAME}: For local use, install Go or use your system package manager." >&2
    echo "${INSTALL_NAME}: See knowledge/reference/security-scanners.md for details." >&2
    exit 0
fi

# ---- Install (idempotent: go install at a pinned version re-checks the
#      same module version; re-running reinstalls the same bits) -------------
echo "${INSTALL_NAME}: installing gitleaks ${GITLEAKS_VERSION} via go install..."
go install "github.com/zricethezav/gitleaks/v8@${GITLEAKS_VERSION}"

echo "${INSTALL_NAME}: installing osv-scanner ${OSV_SCANNER_VERSION} via go install..."
go install "github.com/google/osv-scanner/v2/cmd/osv-scanner@${OSV_SCANNER_VERSION}"

echo "${INSTALL_NAME}: all tools installed successfully"
echo "${INSTALL_NAME}: ensure \$(go env GOPATH)/bin is on your PATH"
