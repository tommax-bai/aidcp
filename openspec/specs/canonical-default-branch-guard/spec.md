# canonical-default-branch-guard Specification

## Purpose
TBD - created by archiving change canonical-default-branch-guard. Update Purpose after archive.
## Requirements
### Requirement: Task admission checks canonical default branches

The task workflow MUST inspect every available canonical repository checkout
before a task worktree is created or a task session is launched.
`aidcp` MUST be on `main`; `aidcp-edge`, `aidcp-cloud`, and
`aidcp-console` MUST be on `master`. If any available canonical checkout is on
another branch, detached, or is itself a linked worktree, the workflow MUST
exit nonzero before creating or launching the task.

#### Scenario: All canonical checkouts are on defaults

- **WHEN** the task preflight sees `aidcp` on `main` and every available
  sibling canonical checkout on `master`
- **THEN** task admission SHALL pass and the caller MAY continue to create or
  reuse the requested task worktree

#### Scenario: Canonical sibling is on a release branch

- **WHEN** the task preflight sees an available canonical sibling checkout on a
  `release/*` branch
- **THEN** task admission SHALL fail before worktree creation or task launch
  and SHALL identify the repository, current branch, and expected default
  branch

#### Scenario: Canonical sibling is detached

- **WHEN** the task preflight cannot resolve a symbolic branch for an available
  canonical checkout
- **THEN** task admission SHALL fail before worktree creation or task launch
  with an explicit detached-or-unknown branch reason

#### Scenario: Sibling repository is not cloned

- **WHEN** a known sibling repository is not present at its canonical path
- **THEN** the global preflight SHALL report that repository as skipped and
  SHALL continue checking other available repositories; a task targeting the
  missing repository SHALL still fail through the existing repository
  availability check

### Requirement: All task entrypoints use the admission gate

The `new-change` and `spawn-change` task entrypoints SHALL invoke the canonical
default-branch preflight before creating a new worktree or reusing an existing
task worktree. A failed preflight MUST prevent both paths from launching a
session or mutating worktree state.

#### Scenario: New worktree is blocked

- **WHEN** `new-change` is invoked while any available canonical checkout is
  not on its configured default branch
- **THEN** the command SHALL exit nonzero before running `git worktree add`

#### Scenario: Existing worktree reuse is blocked

- **WHEN** `spawn-change` is invoked while any available canonical checkout is
  not on its configured default branch and the requested worktree already
  exists
- **THEN** the command SHALL exit nonzero before reusing the worktree or
  launching the task session

