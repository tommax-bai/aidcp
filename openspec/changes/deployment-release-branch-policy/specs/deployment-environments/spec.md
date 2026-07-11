## ADDED Requirements

### Requirement: Trunk development, branch release model

The project SHALL operate a trunk-development, branch-release model. Each sub-repo default branch (`master` for aidcp-cloud, aidcp-edge, aidcp-console; `main` for the control repo) SHALL be the development trunk. Trunk MAY carry unstable content, including experimental features and freshly merged isolated feature branches; deploying a production-facing trunk landing to `dev` is governed by the existing dev auto-deploy requirement. `ol` is the stable production environment; the requirement that its ECS runtime deploy only from a release branch is governed by the existing ol-release-branch requirement (this requirement adds the trunk/branch role model and the merge discipline, not a second copy of that mandate).

When an isolated feature branch is merged back into trunk and an existing or planned `ol` release MUST remain free of that feature's content, the `ol` release branch MUST be created from the pre-merge trunk commit and deployed BEFORE the feature is merged into trunk. Merging a feature branch SHALL only advance trunk; it MUST NOT retroactively change any pinned release branch or the `ol` runtime already deployed from it. Advancing `ol` onto later work SHALL require an explicit new deployment from an eligible release ref.

#### Scenario: Dev carries freshly merged feature work

- **WHEN** an isolated feature branch is merged back into a sub-repo trunk and the required tests pass
- **THEN** trunk MAY be deployed to `dev` even though the feature is still stabilizing
- **AND** `dev` is allowed to run this unstable trunk content

#### Scenario: Ol release cut before feature merge stays clean

- **WHEN** an isolated feature must be kept out of the current `ol` production
- **THEN** the `ol` release branch MUST be created from the pre-merge trunk commit and deployed before the feature is merged into trunk
- **AND** the subsequent trunk merge MUST NOT alter that already-deployed `ol` release ref or the `ol` runtime
- **AND** moving `ol` onto later trunk work MUST require an explicit new deployment from an eligible release ref

### Requirement: Release branches are append-only, retained refs of record

Every `ol` release branch SHALL be named `release/<yyyymmdd>-<scope>` and SHALL be created from a clean, committed trunk commit, identified by a branch tip, tag, or SHA, with no dirty worktree and no uncommitted files. A release branch that backs a live `ol` deployment is the ref of record for that deployment and SHALL be retained; it MUST NOT be deleted while it remains the deployed ref.

A release branch MAY be advanced only by append-only forward progress on the branch itself. When a needed fix has landed on trunk as a strict descendant of the current release tip (trunk has not diverged with content that must stay out of `ol`), the branch MAY be advanced by fast-forward. When the fix is NOT a strict descendant — for example because trunk now carries feature work `ol` must exclude — the fix MAY be applied as a new commit appended to the release branch (such as a cherry-pick), and that append MUST NOT drag the excluded trunk content into `ol`. In all cases the branch MUST NOT be force-pushed, rebased, reset, or otherwise have its already-published history rewritten; its history MUST remain append-only. A superseded release branch MAY be archived or deleted only after a newer release branch backs `ol` and the old branch is no longer the deployed ref.

#### Scenario: Release branch is named and cut from a clean commit

- **WHEN** a release branch is created for an `ol` deployment
- **THEN** it SHALL follow the `release/<yyyymmdd>-<scope>` naming convention
- **AND** it SHALL be created from a clean, committed trunk commit (branch tip, tag, or SHA) with no uncommitted changes

#### Scenario: Fast-forward advance when the fix is a clean descendant

- **WHEN** a fix has landed on trunk as a strict descendant of the current release tip and must reach `ol`
- **THEN** the release branch MAY be advanced by fast-forward to that commit
- **AND** the advance MUST NOT rewrite any existing release history

#### Scenario: Isolated hotfix that is not a descendant is appended

- **WHEN** an `ol` hotfix is needed but the fix is not a strict descendant of the release tip because trunk carries work `ol` must exclude
- **THEN** the fix MAY be applied as a new append-only commit on the release branch (such as a cherry-pick)
- **AND** the append MUST NOT pull the excluded trunk content into `ol`
- **AND** the branch history MUST still never be force-pushed, rebased, or reset

#### Scenario: History rewrite of a release branch is rejected

- **WHEN** an operation would force-push, rebase, reset, or otherwise rewrite the published history of an `ol` release branch
- **THEN** the operation MUST be rejected
- **AND** the release branch history MUST remain append-only

#### Scenario: Live release branch is retained

- **WHEN** a release branch is the ref of record for a currently deployed `ol` runtime
- **THEN** it MUST be retained and MUST NOT be deleted while it remains the deployed ref

#### Scenario: Superseded release branch may be cleaned up

- **WHEN** a newer release branch backs `ol` and an older release branch is no longer the deployed ref
- **THEN** the older release branch MAY be archived or deleted

### Requirement: Online edge installer selects its target by build-time flag, not a long-lived branch

The `ol` edge installer is a distribution artifact, not an `ol` ECS runtime deployment; the release-branch deployment mandate governs the `ol` ECS cloud and console runtime, and the edge installer is the explicit exception to it. The `ol` edge installer's default cloud target SHALL be selected at build time from trunk source, not from a long-lived branch. Trunk SHALL keep the `dev` default, so an ordinary trunk build carries zero regression, and the online target SHALL be produced by building trunk with an online build selection. The system MUST NOT maintain a long-lived edge branch whose only purpose is to carry the `ol` default endpoint. For a cross-repo `ol` release record, the edge artifact's ref of record SHALL be the trunk commit it was built from together with the online build selection, so edge provenance can be pinned without a release branch.

#### Scenario: Ol edge target comes from a build-time selection on trunk

- **WHEN** an `ol` edge installer is produced
- **THEN** its default cloud target SHALL be set by an online build selection applied to trunk source
- **AND** an ordinary trunk build with no online selection SHALL default to the `dev` cloud target

#### Scenario: No long-lived branch for the default endpoint

- **WHEN** the online installer's default endpoint needs to differ from trunk's default
- **THEN** it SHALL be achieved by the build-time selection
- **AND** the project MUST NOT maintain a long-lived edge branch solely to carry the `ol` default endpoint
- **AND** the edge artifact's ref of record for an `ol` release SHALL be recorded as the trunk commit plus the online build selection
