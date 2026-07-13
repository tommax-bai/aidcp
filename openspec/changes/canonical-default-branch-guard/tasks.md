## 1. Preflight Helper

- [x] 1.1 Add a read-only `scripts/task-preflight` command that checks every available canonical repository against `_default_branch`.
- [x] 1.2 Fail on non-default, detached, or linked-worktree canonical states with repository/path/current/expected details; skip only missing sibling clones.

## 2. Task Entry Points

- [x] 2.1 Invoke the preflight before `scripts/new-change` creates a worktree.
- [x] 2.2 Invoke the preflight before `scripts/spawn-change` reuses a worktree or launches a task.

## 3. Norms And Validation

- [x] 3.1 Update `AGENTS.md`, `docs/parallel-dev-worktrees.md`, and `scripts/README.md` with the mandatory task-admission gate and non-repairing behavior.
  <!-- control repo: documented mandatory preflight and read-only failure behavior; implementation commit 845062a. -->
- [x] 3.2 Validate shell syntax, the current workspace failure path, the clean/default positive path in a temporary fixture, and `openspec validate canonical-default-branch-guard --strict`.
  <!-- control repo: bash -n and diff check pass; current canonical drift blocks with exit 1; temporary default and drift fixtures pass; OpenSpec strict validation passes. -->
