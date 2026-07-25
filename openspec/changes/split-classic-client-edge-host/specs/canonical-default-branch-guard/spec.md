## MODIFIED Requirements

### Requirement: Task admission checks canonical default branches

The task workflow MUST inspect every available canonical repository checkout
before a task worktree is created or a task session is launched.
`aidcp` MUST be on `main`; every sibling business repository MUST be on
`master`. The sibling roster SHALL name each repository explicitly. After this
repository split the roster SHALL be `aidcp-classic-client`, `aidcp-edge-host`,
`aidcp-cloud` and `aidcp-console`; for the duration of the split window it SHALL
additionally include `aidcp-edge`, so that neither the pre-rename nor the
post-rename layout is left unguarded while the migration is in flight. If any
available canonical checkout is on another branch, detached, or is itself a
linked worktree, the workflow MUST exit nonzero before creating or launching the
task.

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

#### Scenario: Both the old and the new repository layout exist during the split

- **WHEN** the task preflight runs while `aidcp-edge` has not yet been renamed
  but `aidcp-classic-client` or `aidcp-edge-host` already exists on disk
- **THEN** every checkout that is present SHALL be checked against its expected
  default branch, and the presence of one layout SHALL NOT cause the other to
  be skipped

## ADDED Requirements

### Requirement: The canonical repository roster MUST stay complete across renames

Absence MUST NOT be the only input that decides how much the guard covers. In
addition to skipping a repository that is genuinely not cloned, the preflight
SHALL fail admission when it finds, beside the control repository, a Git
checkout that belongs to this project but is absent from its roster. Renaming or
splitting a canonical repository therefore fails admission until the roster, the
default-branch table and every task entrypoint have been updated, rather than
silently reducing the number of repositories that are guarded.

This requirement exists because a rename would otherwise open the guard exactly
when it is most needed: the roster entry for the old path becomes a skip, the
new paths are not yet roster members, and admission keeps passing while nothing
is checked. The incident this whole capability was created for — a canonical
execution-side checkout left on a release branch for about a day, so that the
locally launched desktop client ran the release tree instead of the default
branch — is precisely what a silently narrowed roster would allow to recur.

#### Scenario: Roster is updated before the rename

- **WHEN** the roster, the default-branch table and the task entrypoints already
  name the new repositories, and the rename then happens
- **THEN** admission continues to pass, the old path is reported as skipped once
  it disappears, and both new checkouts are branch-checked from the moment they
  exist

#### Scenario: Rename happens before the roster is updated

- **WHEN** a project checkout exists beside the control repository under a name
  the preflight does not know
- **THEN** admission SHALL fail and SHALL name the unregistered repository and
  its path, rather than passing on the strength of the repositories it does
  happen to know about

#### Scenario: A repository is genuinely not cloned on this machine

- **WHEN** a roster repository has no checkout beside the control repository and
  no unregistered project checkout is present either
- **THEN** admission SHALL continue to skip it and pass, so that a machine
  holding only some of the repositories can still start tasks
