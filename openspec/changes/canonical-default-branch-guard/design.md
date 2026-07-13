## Context

The control repository already knows the default branch for each repository
and has helper scripts that create sibling worktrees. The missing step is a
single admission check before a task worktree is created or reused. A
canonical checkout left on a release branch can otherwise make a new task or
local runtime start from the wrong source tree.

The check must be read-only and must not try to repair the checkout. Existing
user changes and the current branch owner require human coordination; silently
switching or cleaning a checkout would risk data loss and interrupt another
session.

## Goals / Non-Goals

**Goals:**

- Check the canonical checkout branch for `aidcp`, `aidcp-edge`,
  `aidcp-cloud`, and `aidcp-console` before task admission.
- Fail before worktree creation or task launch when an available canonical
  checkout is not on its configured default branch.
- Reuse the same check from both direct and terminal-launched task entrypoints.
- Make the rule explicit in the Codex development guide and worktree handbook.

**Non-Goals:**

- Do not switch branches, remove worktrees, clean files, stash changes, or
  resolve concurrent ownership.
- Do not change Edge, cloud, console, protocol, deployment, or runtime behavior.
- Do not require repositories that are not cloned locally; an unavailable
  sibling is skipped and the requested repository is still validated by its
  existing preflight.

## Decisions

### 1. Centralize the branch map in `scripts/lib.sh`

The existing `_default_branch` function is the source of truth for `main` vs
`master`. The new guard will use that function instead of duplicating branch
names in multiple scripts.

### 2. Check all available canonical repositories

`scripts/task-preflight` will inspect each known canonical path under the
workspace. For each cloned repository it will read the current symbolic branch
and require the configured default branch. Detached HEAD, a linked worktree at
the canonical path, or a non-default branch is a hard failure. The output will
identify the repository, path, current branch, and expected branch.

Checking all available repositories prevents an unrelated stale canonical
checkout from being carried into a new task session. Missing sibling clones are
skipped because the repository cannot be a source of a local task until the
existing repository-availability checks reject it.

### 3. Invoke before both new and reused task worktrees

`new-change` will call the guard before creating a worktree. `spawn-change`
will call it before deciding whether to reuse an existing worktree, so
`spawn-change` cannot bypass the gate by reusing an already-created directory.
The standalone script remains available for session-start and manual checks.

### 4. Keep the failure non-repairing and non-overridable

The guard exits nonzero and prints the exact remediation direction: restore the
canonical checkout to its default branch only after confirming no active work,
or move the release/feature work into a linked worktree. There is no automatic
override flag in this change; an operator must resolve the state before opening
another task.

## Risks / Trade-offs

- [Risk] A legitimate maintenance session may be blocked while a canonical
  checkout is intentionally on a release branch. → [Mitigation] Use a
  dedicated release worktree; the rule intentionally treats the canonical
  checkout as an integration/deployment boundary.
- [Risk] A missing sibling repo could hide a later problem. → [Mitigation]
  Missing repos are reported as skipped, while the requested repo remains
  required by `new-change`/`spawn-change`.
- [Risk] A warning-only hook is bypassed by task helpers. → [Mitigation] The
  task entrypoints use the nonzero preflight directly, so the task is blocked
  before any worktree mutation.

## Migration Plan

1. Add the guard and invoke it from `new-change` and `spawn-change`.
2. Run the guard against the current workspace; it should identify the existing
   `aidcp-edge` canonical release branch and block new task creation until an
   operator resolves it.
3. Validate shell syntax, negative behavior, and OpenSpec strictly.

Rollback is removing the helper invocation from the two task scripts; no
application or runtime data is changed by the guard itself.

## Open Questions

None for this scope.
