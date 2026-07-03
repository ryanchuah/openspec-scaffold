#!/usr/bin/env bash
# install-tools.sh — Install pinned development security scanners.
#
# Installs to ~/.local/bin (should be on PATH). Skips tools that already
# match the pinned version (idempotent).
#
# Pinned versions (bump by editing the variables below):
#   GITLEAKS_VERSION="v8.30.1"
#   OSV_SCANNER_VERSION="v2.4.0"
#
# deptry — NOT installed here. It comes via pip dev extras
# (e.g. `pip install -e ".[dev]"` with a pyproject.toml extras
# group). This script handles only standalone binary installations.
#
# Exit 0 on success or if pinned versions are already present.
# Exits non-zero on download or install failure.

set -euo pipefail

INSTALL_NAME="install-tools"

# ---- Pinned versions (edit here to bump) ----
GITLEAKS_VERSION="v8.30.1"
OSV_SCANNER_VERSION="v2.4.0"

# ---- Install location ----
INSTALL_DIR="${HOME}/.local/bin"
mkdir -p "$INSTALL_DIR"

# ---- OS / arch detection ----
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

# Normalise arch names for download URLs
case "$ARCH" in
    x86_64)  ARCH="amd64" ;;
    aarch64) ARCH="arm64" ;;
esac

# ---- Helper: check version, download + extract if missing ----

_ensure_binary() {
    local name="$1"         # tool name (e.g. gitleaks)
    local pinned="$2"       # full pinned version with v prefix
    local url_template="$3" # URL template with {version} and {arch} placeholders
    local extract_cmd="$4"  # command to extract binary from download (or "cp" for raw binary)

    local installed=""
    if command -v "$name" >/dev/null 2>&1; then
        installed="$("$name" version 2>/dev/null || "$name" --version 2>/dev/null || echo "unknown")"
    fi

    # Normalise: strip leading 'v' before comparing
    local pinned_stripped="${pinned#v}"
    local installed_stripped="${installed#v}"
    installed_stripped="${installed_stripped%% *}"  # take first word only

    if [ -n "$installed" ] && [ "$installed_stripped" = "$pinned_stripped" ]; then
        echo "${INSTALL_NAME}: ${name} ${pinned} already installed at $(command -v "$name")"
        return 0
    fi

    echo "${INSTALL_NAME}: installing ${name} ${pinned}..."

    # Build download URL: substitute {version} (with v) and {ver} (without v)
    local pinned_nov="${pinned#v}"
    local url
    url=$(echo "$url_template" | sed \
        -e "s|{version}|${pinned}|g" \
        -e "s|{ver}|${pinned_nov}|g" \
        -e "s|{os}|${OS}|g" \
        -e "s|{arch}|${ARCH}|g")

    local tmpdir
    tmpdir="$(mktemp -d)"
    # shellcheck disable=SC2064
    trap "rm -rf '${tmpdir}'" EXIT

    if [ "$extract_cmd" = "cp" ]; then
        # Raw binary — download directly
        if ! curl -fsSL "$url" -o "${tmpdir}/${name}"; then
            echo "${INSTALL_NAME}: ERROR — failed to download ${name} from ${url}" >&2
            return 1
        fi
        chmod +x "${tmpdir}/${name}"
        bin_candidate="${tmpdir}/${name}"
    else
        # tar.gz archive
        local archive="${tmpdir}/${name}.tar.gz"
        if ! curl -fsSL "$url" -o "$archive"; then
            echo "${INSTALL_NAME}: ERROR — failed to download ${name} from ${url}" >&2
            return 1
        fi
        tar -xzf "$archive" -C "$tmpdir"

        # Find the binary (some archives put it in a subdir, some at root)
        bin_candidate="$(find "$tmpdir" -maxdepth 2 -type f -name "$name" 2>/dev/null | head -1)"
        if [ -z "$bin_candidate" ]; then
            echo "${INSTALL_NAME}: ERROR — binary '${name}' not found in downloaded archive" >&2
            return 1
        fi
    fi

    cp "$bin_candidate" "${INSTALL_DIR}/${name}"
    chmod +x "${INSTALL_DIR}/${name}"
    echo "${INSTALL_NAME}: ${name} ${pinned} installed to ${INSTALL_DIR}/${name}"
}

# ---- gitleaks ----
# URL pattern: https://github.com/gitleaks/gitleaks/releases/download/v{version}/gitleaks_{ver}_{os}_{arch}.tar.gz
_ensure_binary \
    "gitleaks" \
    "$GITLEAKS_VERSION" \
    "https://github.com/gitleaks/gitleaks/releases/download/{version}/gitleaks_{ver}_{os}_{arch}.tar.gz" \
    "tar"

# ---- osv-scanner ----
# URL pattern: https://github.com/google/osv-scanner/releases/download/v{version}/osv-scanner_{ver}_{os}_{arch}
_ensure_binary \
    "osv-scanner" \
    "$OSV_SCANNER_VERSION" \
    "https://github.com/google/osv-scanner/releases/download/{version}/osv-scanner_{ver}_{os}_{arch}" \
    "cp"

echo "${INSTALL_NAME}: all tools installed successfully"
