#!/usr/bin/env bash
# Shared helpers for aidcp parallel-dev worktree fleet scripts.
# See docs/parallel-dev-worktrees.md and CLAUDE.md §7.
# Convention: worktree / branch / openspec-change share ONE name;
# worktrees live at ../<repo>.wt/<name> (sibling of the sub-repo checkout).
set -euo pipefail

# Resolve dirs from this file's location (robust to cwd / relative or abs invocation).
# When scripts run from an aidcp control-repo worktree, the script directory itself is under
# aidcp.wt/<name>. Git's common dir still points at the canonical aidcp/.git, so use that as
# the stable anchor for all sibling repositories and worktree roots.
_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_SCRIPT_CONTROL_REPO="$(dirname "$_LIB_DIR")"
_COMMON_GIT_DIR="$(git -C "$_SCRIPT_CONTROL_REPO" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)"
if [ -n "$_COMMON_GIT_DIR" ]; then
  CONTROL_REPO="$(dirname "$_COMMON_GIT_DIR")"              # .../aidcp canonical checkout
else
  CONTROL_REPO="$_SCRIPT_CONTROL_REPO"
fi
CODES_DIR="$(dirname "$CONTROL_REPO")"                      # .../codes

# Repo -> default branch. Control repo (aidcp) = main; sub-repos = master.
_default_branch() {
  case "$1" in
    aidcp) echo main ;;
    aidcp-edge|aidcp-cloud|aidcp-console) echo master ;;
    *) return 1 ;;
  esac
}

repo_path()     { echo "$CODES_DIR/$1"; }
worktree_path() { echo "$CODES_DIR/$1.wt/$2"; }            # ../<repo>.wt/<name>
repo_cloned()   { [ -e "$CODES_DIR/$1/.git" ]; }

# Is <name> an active (non-archived) openspec change in the control repo?
change_active() { [ -d "$CONTROL_REPO/openspec/changes/$1" ]; }

die()  { echo "ERROR: $*" >&2; exit 1; }
warn() { echo "WARN: $*" >&2; }
info() { echo ">> $*"; }

# Worktrees apply to sub-repos only; control repo uses openspec propose.
require_subrepo() {
  case "$1" in
    aidcp-edge|aidcp-cloud|aidcp-console) : ;;
    aidcp) die "aidcp 是控制仓，change 用 openspec propose、不开 worktree（见 CLAUDE.md §7）。" ;;
    *) die "未知 repo: $1（应为 aidcp-edge|aidcp-cloud|aidcp-console）。" ;;
  esac
}
