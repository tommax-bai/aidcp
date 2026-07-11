# deployment-environments Specification

## Purpose
TBD - created by archiving change split-dev-ol-deploy-targets. Update Purpose after archive.
## Requirements
### Requirement: Deployment targets must be explicit

The project SHALL define explicit deployment targets for aidcp runtime operations. `dev` SHALL refer to ECS `121.89.85.150` with SSH key `~/codes/isales-4.pem` and SHALL be the default target for completed production-facing development deployment, mainline development deployment, and real-machine validation. `ol` SHALL refer to ECS `123.56.253.183` with SSH key `/Users/baitianxing/Downloads/ol.pem` and SHALL be used only when the user explicitly requests stable online deployment.

Any cloud, console, or edge release operation MUST name the target before touching remote state. Deployment tools and docs MUST NOT rely on the legacy assumption that there is only one ECS target.

#### Scenario: Dev target preflight

- **WHEN** an operator requests a deployment to `dev`
- **THEN** the deployment preflight SHALL verify the target IP is `121.89.85.150`
- **AND** the SSH key path is `~/codes/isales-4.pem`
- **AND** the key permissions are safe for SSH

#### Scenario: Ol target preflight

- **WHEN** an operator requests a deployment to `ol`
- **THEN** the deployment preflight SHALL verify the target IP is `123.56.253.183`
- **AND** the SSH key path is `/Users/baitianxing/Downloads/ol.pem`
- **AND** the key permissions are safe for SSH

#### Scenario: Missing target is rejected

- **WHEN** a deployment command or runbook step would touch ECS state without naming `dev` or `ol`
- **THEN** the operation MUST stop before SSH or rsync and report that the deployment target is missing

#### Scenario: Completed development defaults to dev

- **WHEN** a production-facing development change is complete and deployment is required
- **AND** the user has not named a deployment target
- **THEN** the deployment target SHALL resolve to `dev`
- **AND** the deployment MUST still state the resolved target and pass the `dev` preflight before touching ECS

#### Scenario: Ol requires explicit user request

- **WHEN** a deployment would target `ol`
- **THEN** the operator MUST have an explicit user request for `ol` or online deployment
- **AND** `ol` MUST NOT be selected as an implicit default

### Requirement: Ol deployments must come from release branches

The system SHALL separate development deployment from online release deployment. `dev` deployments SHALL use validated default-branch commits after the relevant repo tests pass. `ol` deployments MUST use a release branch from a clean checkout; they MUST NOT deploy arbitrary dirty worktrees, uncommitted local files, feature branches, default branches, tags, or raw SHAs directly. A tag or exact committed SHA MAY be used only as the source for creating the release branch.

For cross-repo releases, the deployed cloud, console, and edge SHAs SHALL be recorded together when more than one artifact changes.

#### Scenario: Dev auto-deploys validated default branch

- **WHEN** a change has landed on the relevant repo default branch and tests/typecheck required by the change have passed
- **AND** the changed service or artifact is production-facing
- **THEN** it SHALL deploy to `dev` after the normal backup, rsync, restart, and healthcheck sequence unless the user explicitly paused deployment or a safety gate fails

#### Scenario: Ol rejects dirty deployment source

- **WHEN** an operator attempts to deploy `ol` from a checkout with uncommitted changes or from a worktree branch that is not the selected release ref
- **THEN** the deployment MUST stop before remote sync
- **AND** it MUST report the checkout/ref eligibility failure

#### Scenario: Ol rejects direct tag or raw SHA deployment

- **WHEN** an operator attempts to deploy `ol` directly from a tag or raw committed SHA without creating/selecting a release branch
- **THEN** the deployment MUST stop before remote sync
- **AND** it MUST report that `ol` deployment is branch-based

#### Scenario: Ol records exact release version

- **WHEN** an `ol` deployment succeeds
- **THEN** the release note or OpenSpec task SHALL record the release branch and exact committed SHA for each deployed artifact

### Requirement: Dev and ol runtime state must be isolated

`ol` SHALL use a dedicated production PostgreSQL boundary for durable aidcp state. The dedicated boundary MAY be PostgreSQL local to `ol` or managed RDS, but it MUST NOT silently share mutable runtime state with `dev` for normal online operation.

A temporary `ol` to `dev` PostgreSQL bridge MAY be used only as a bootstrap or smoke-test step. Before such a bridge is used, `dev` PostgreSQL network access MUST be restricted to local connections plus the specific ol source, and docs/tasks MUST mark the bridge as temporary. The bridge MUST NOT be treated as the final online topology.

#### Scenario: Normal ol uses dedicated database

- **WHEN** `ol` is marked ready for online service
- **THEN** its cloud process SHALL connect to an ol-owned database boundary rather than the dev development database

#### Scenario: Temporary bridge requires allowlist

- **WHEN** `ol` is configured to connect to `dev` PostgreSQL for bootstrap or smoke testing
- **THEN** `dev` PostgreSQL access MUST be restricted away from `0.0.0.0/0`
- **AND** only local dev access plus the ol source SHALL be allowed for the aidcp app role
- **AND** the deployment note SHALL state that the bridge is temporary

#### Scenario: Shared mutable state is not final topology

- **WHEN** dev and ol cloud processes would both process real traffic against the same database
- **THEN** the setup MUST be treated as a temporary bridge or rejected
- **AND** it MUST NOT be documented as the steady-state online architecture

### Requirement: Runtime credentials must remain target-local and out of git

Each target SHALL load runtime credentials from its own ECS-local env file via systemd `EnvironmentFile`. The repository MAY document env key names, env file paths, service names, and config loading methods, but MUST NOT record credential values, database passwords, private keys, API tokens, or Feishu secrets.

Operators SHOULD use target-specific Feishu credentials for `dev` and `ol`; if the same Feishu app is reused during bootstrap, only one target SHALL be allowed to process real Feishu command traffic unless the operator explicitly marks the duplicate-handler risk as accepted for a temporary test.

#### Scenario: Env values stay out of repo

- **WHEN** docs, tasks, deployment notes, or commits are created for `dev` or `ol`
- **THEN** they MAY list env key names and file paths
- **AND** they MUST NOT include actual secret values

#### Scenario: Target-local env file is authoritative

- **WHEN** `aidcp-cloud.service` starts on either target
- **THEN** it SHALL load runtime config from that target's `/opt/aidcp/cloud/.env`
- **AND** the env file SHALL be maintained outside git

#### Scenario: Feishu duplicate ingestion is controlled

- **WHEN** dev and ol are configured with the same Feishu app credentials
- **THEN** at most one target SHALL process real Feishu command traffic unless a temporary duplicate-handler test is explicitly recorded

### Requirement: Edge and console must select the intended target

Edge clients SHALL connect to the intended cloud target explicitly. Dev edge clients SHALL connect to `ws://121.89.85.150:8787` unless overridden by a dev domain. Ol edge clients SHALL connect to `ws://123.56.253.183:8787` or a configured ol domain. A packaged or operator-run edge release MUST NOT silently connect to dev when it is intended for ol.

Console deployments SHALL serve each target's console from that target's nginx/static path and proxy `/api` and `/ws` to the same target's panel API. Console MUST NOT proxy ol operators to the dev panel API by accident.

#### Scenario: Ol edge uses ol cloud URL

- **WHEN** an edge instance is launched for online/ol operation
- **THEN** its effective cloud URL SHALL be the ol cloud endpoint
- **AND** it MUST NOT use the dev default endpoint silently

#### Scenario: Dev edge remains explicit

- **WHEN** an edge instance is launched for development validation
- **THEN** its effective cloud URL SHALL be the dev cloud endpoint or a clearly documented override

#### Scenario: Console proxies to same target panel

- **WHEN** the console is deployed on `ol`
- **THEN** its `/api` and `/ws` routes SHALL proxy to the ol cloud panel API on that ECS
- **AND** they MUST NOT proxy to the dev panel API

### Requirement: First ol deployment must bootstrap and validate the clean host

The first `ol` deployment SHALL be treated as a bootstrap operation. It MUST install or verify required runtime dependencies, create `/opt/aidcp` directories, install `aidcp-cloud.service`, install nginx console routing, create the target-local env file outside git, deploy committed cloud and console artifacts, and run health checks before declaring success.

The health check SHALL verify at least: `aidcp-cloud.service` active state, `8787` listening for edge-cloud WebSocket, panel API on local `8090`, console HTTP response through nginx, PostgreSQL connectivity for the configured ol database boundary, and Feishu readiness if Feishu is enabled on ol.

#### Scenario: Clean ol host bootstrap

- **WHEN** `ol` has no aidcp runtime dependencies installed
- **THEN** the bootstrap SHALL install or verify Node.js/npm, rsync, nginx, and service prerequisites before deploying aidcp files
- **AND** it SHALL create the required `/opt/aidcp` runtime directories

#### Scenario: Bootstrap success requires health checks

- **WHEN** files have been synced and services started on `ol`
- **THEN** deployment MUST NOT be marked successful until cloud, panel, console, database, and enabled Feishu checks pass

#### Scenario: Bootstrap failure leaves dev untouched

- **WHEN** the first `ol` deployment fails
- **THEN** rollback or cleanup SHALL affect only `ol`
- **AND** it MUST NOT restart, modify, or delete services, directories, ports, or databases belonging to `dev` or unrelated isales services

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

