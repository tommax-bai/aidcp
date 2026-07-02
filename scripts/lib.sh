#!/usr/bin/env bash
# Shared helpers for aidcp parallel-dev worktree fleet scripts.
# See docs/parallel-dev-worktrees.md and CLAUDE.md §7.
# Convention: worktree / branch / openspec-change share ONE name;
# worktrees live at ../<repo>.wt/<name> (sibling of the sub-repo checkout).
set -euo pipefail

# Resolve dirs from this file's location (robust to cwd / relative or abs invocation).
_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # .../aidcp/scripts
CONTROL_REPO="$(dirname "$_LIB_DIR")"                       # .../aidcp
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
