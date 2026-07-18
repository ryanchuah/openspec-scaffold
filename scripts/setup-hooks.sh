#!/usr/bin/env bash
# setup-hooks.sh — clone-safe wiring for the git-native commit-test gate.
#
# Sets `core.hooksPath` (repo-local, `--local`) to `scripts/githooks` so git
# runs scripts/githooks/pre-commit on every commit (the git-native primary
# enforcement layer for the commit-test gate). Idempotent and conflict-safe:
#   - already `scripts/githooks` -> no-op, report "already configured"
#   - unset/empty                -> set it, report confirmation
#   - any OTHER existing value   -> WARN and ABORT without overwriting (the
#                                    developer has custom hooks; reconcile
#                                    manually)
#
# `core.hooksPath` is `.git/config` state, not tracked or copied on clone —
# run this once per clone (see knowledge/reference/new-repo-bootstrap.md).

set -euo pipefail

HOOKS_PATH="scripts/githooks"

if ! command -v git >/dev/null 2>&1; then
    echo "setup-hooks: ERROR — git is not available on PATH" >&2
    exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "setup-hooks: ERROR — not inside a git repository" >&2
    exit 1
fi

cur="$(git config --local --get core.hooksPath 2>/dev/null || true)"

if [ "$cur" = "$HOOKS_PATH" ]; then
    echo "setup-hooks: already configured (core.hooksPath=${HOOKS_PATH})"
    exit 0
fi

if [ -z "$cur" ]; then
    git config --local core.hooksPath "$HOOKS_PATH"
    echo "setup-hooks: set core.hooksPath=${HOOKS_PATH}"
    exit 0
fi

echo "setup-hooks: WARNING — core.hooksPath is already set to '${cur}' (not '${HOOKS_PATH}')" >&2
echo "setup-hooks: refusing to overwrite a custom hooks path — reconcile manually:" >&2
echo "setup-hooks:   merge your existing hooks into ${HOOKS_PATH}, then re-run this script," >&2
echo "setup-hooks:   or set it yourself: git config --local core.hooksPath ${HOOKS_PATH}" >&2
exit 1
