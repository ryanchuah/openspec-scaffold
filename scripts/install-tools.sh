#!/usr/bin/env bash
# install-tools.sh — Provision security scanners via go install and pip.
#
# Installs the following:
#   Go binaries:
#     gitleaks    — secrets scanner (github.com/zricethezav/gitleaks/v8)
#     osv-scanner — dependency-CVE (vulnerability) scanner
#                   (github.com/google/osv-scanner/v2/cmd/osv-scanner)
#   Python SAST (pip):
#     semgrep     — SAST pattern scanner (requires --config ruleset)
#     bandit      — Python security linting
#
# Go tools: go install places binaries in $(go env GOPATH)/bin — ensure
# that directory is on your PATH.
#
# Python scanners: installed unpinned (latest) via pip, version-recorded-
# not-gated by checks.py.  A repo needing version-exactness pins them in
# its own dev extras.
#
# For CI use the official actions instead of this script:
#   gitleaks       → gitleaks/gitleaks-action
#   osv-scanner    → google/osv-scanner-action
#   semgrep        → semgrep/semgrep-action
#
# deptry — NOT installed here.  It comes via pip dev extras
# (e.g. `pip install -e ".[dev]"` with a pyproject.toml extras
# group).
#
# See also: knowledge/reference/security-scanners.md
#
# Exit conventions:
#   0  → success (Go toolchain and/or pip may be absent — degrade, don't block)
#   ≠0 → a go install or pip install command failed

set -euo pipefail

INSTALL_NAME="install-tools"

# ---- Pinned versions (edit here to bump) ----
GITLEAKS_VERSION="v8.30.1"
OSV_SCANNER_VERSION="v2.4.0"

# ---- Go toolchain block (degrade-don't-block when absent) -------------------
if command -v go >/dev/null 2>&1; then
    echo "${INSTALL_NAME}: installing gitleaks ${GITLEAKS_VERSION} via go install..."
    go install "github.com/zricethezav/gitleaks/v8@${GITLEAKS_VERSION}"

    echo "${INSTALL_NAME}: installing osv-scanner ${OSV_SCANNER_VERSION} via go install..."
    go install "github.com/google/osv-scanner/v2/cmd/osv-scanner@${OSV_SCANNER_VERSION}"

    echo "${INSTALL_NAME}: all go tools installed successfully"
    echo "${INSTALL_NAME}: ensure \$(go env GOPATH)/bin is on your PATH"
else
    echo "${INSTALL_NAME}: WARNING — Go toolchain not found; skipping Go tool installation" >&2
    echo "${INSTALL_NAME}: For CI, use the official GitHub Actions:" >&2
    echo "${INSTALL_NAME}:   - gitleaks/gitleaks-action" >&2
    echo "${INSTALL_NAME}:   - google/osv-scanner-action" >&2
    echo "${INSTALL_NAME}: For local use, install Go or use your system package manager." >&2
    echo "${INSTALL_NAME}: See knowledge/reference/security-scanners.md for details." >&2
fi

# ---- Python SAST scanners (pip block; degrade-don't-block when absent) -----
if python3 -m pip --version >/dev/null 2>&1; then
    echo "${INSTALL_NAME}: installing semgrep + bandit via pip..."
    python3 -m pip install --upgrade semgrep bandit
else
    echo "${INSTALL_NAME}: WARNING — python3 pip not found; skipping semgrep/bandit installation" >&2
    echo "${INSTALL_NAME}: See knowledge/reference/security-scanners.md for details." >&2
fi

echo "${INSTALL_NAME}: finished provisioning scanners — ensure Go binaries are on PATH and semgrep+bandit are accessible via pip"
