## ADDED Requirements

### Requirement: Release-branch changes must be forward-ported to trunk

Any change landed on an `ol` release branch — hotfix, cherry-pick append, or direct commit — SHALL also be forward-ported to trunk (`main` for the control repo, `master` for `aidcp-edge` / `aidcp-cloud` / `aidcp-console`) as part of landing it. A fix MUST NOT be left living only on a release branch.

Forward-porting is judged by **behaviour on trunk, not by commit identity**: applying the same patch, resolving conflicts, or re-implementing the fix on top of code trunk has since changed are all acceptable, provided trunk ends up with the equivalent behaviour and test coverage. `git cherry` symbols are therefore evidence, not verdict — a conflict-resolved or re-implemented port legitimately carries a different patch-id.

When a forward-port cannot be completed at landing time (it is blocked, already superseded on trunk, or needs re-implementation), it SHALL be recorded explicitly — in the change's `tasks.md` and in the real-machine/backlog ledger — naming the commit and the reason. Leaving it silently on the release branch is not an outcome.

The one exception is a **release-artifact pointer** — a value whose meaning is "which binary is sitting in *this host's* directory" (installer version, download-page version, artifact filename). These describe deployment state, not code, and mechanically copying them to trunk would make trunk point at an artifact that does not exist on the other host. They MUST still be reconciled explicitly and recorded, but MUST NOT be blindly forward-ported.

#### Scenario: Hotfix appended to a release branch reaches trunk

- **WHEN** a fix is committed to an `ol` release branch
- **THEN** the same fix is also landed on trunk before the work is considered done
- **AND** trunk's test suite covers the fixed behaviour

#### Scenario: Trunk has diverged, so the fix is re-implemented rather than cherry-picked

- **WHEN** a release-branch fix conflicts with trunk because trunk has since replaced the surrounding code
- **THEN** the fix MAY be re-implemented on trunk's current code instead of cherry-picked
- **AND** the port is still considered complete once trunk has the equivalent behaviour and test coverage

#### Scenario: Blocked forward-port is recorded, never silently dropped

- **WHEN** a release-branch fix cannot be forward-ported at landing time
- **THEN** the blocked port is recorded with its commit and reason in the change's tasks and the backlog ledger
- **AND** it MUST NOT be left only on the release branch with no record

#### Scenario: Artifact pointers are reconciled, not copied

- **WHEN** a release branch carries an installer version or download-page pointer describing the artifact published to `ol`
- **THEN** it MUST NOT be mechanically forward-ported to trunk, because the referenced artifact may not exist on the other host
- **AND** the divergence MUST be reconciled explicitly (sync the artifact to both hosts, or make the pointer host-configurable) and recorded

#### Scenario: A cut release branch never becomes a place fixes go to die

- **WHEN** an `ol` release is cut and later hotfixed
- **THEN** every hotfix on that branch is present on trunk before the next release is cut from trunk
- **AND** cutting the next release from trunk therefore cannot reintroduce a bug that was already fixed for `ol`
