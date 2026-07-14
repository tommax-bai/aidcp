## Why

The canonical checkout of a sibling application repository can be left on a
release or feature branch, after which a task launcher may start work from the
wrong source tree. This recently caused the local Edge runtime to execute an
OL release tree instead of the Facebook-capable default branch. The task
workflow needs a hard preflight gate before creating or launching any new
task.

## What Changes

- Add a read-only task preflight that checks every available canonical checkout
  (`aidcp`, `aidcp-edge`, `aidcp-cloud`, and `aidcp-console`) is on its configured
  default branch.
- Make `scripts/new-change` and `scripts/spawn-change` fail before creating or
  launching a worktree when any canonical checkout is on a non-default branch.
- Keep the gate limited to task admission; it does not switch branches, clean
  worktrees, change runtime behavior, or override existing user changes.
- Record the rule in the Codex development guide, parallel worktree handbook,
  and helper-script README so future task execution follows the same mandatory
  preflight.

## Capabilities

### New Capabilities

- `canonical-default-branch-guard`: task admission is blocked when a canonical
  repository checkout is not on its configured default branch.

### Modified Capabilities

- None. This is a local task-workflow guard and does not change application or
  protocol behavior.

## Impact

- A new `scripts/task-preflight` helper in the control repo, using the existing
  `scripts/lib.sh` repository and default-branch helpers.
- `scripts/new-change` and `scripts/spawn-change` task entrypoints.
- `AGENTS.md`, `docs/parallel-dev-worktrees.md`, and `scripts/README.md`
  workflow guidance.
- OpenSpec contract and validation only; no sibling application source or
  running service is changed.
