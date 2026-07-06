## ADDED Requirements

### Requirement: Deployment targets must be explicit

The project SHALL define explicit deployment targets for aidcp runtime operations. `dev` SHALL refer to ECS `121.89.85.150` with SSH key `~/codes/isales-4.pem` and SHALL be used for mainline development deployment and real-machine validation. `ol` SHALL refer to ECS `123.56.253.183` with SSH key `/Users/baitianxing/Downloads/ol.pem` and SHALL be used for stable online deployment.

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

### Requirement: Ol deployments must come from release-eligible commits

The system SHALL separate development deployment from online release deployment. `dev` deployments MAY use validated default-branch commits after the relevant repo tests pass. `ol` deployments MUST use a release branch, release tag, or exact committed SHA from a clean checkout; they MUST NOT deploy arbitrary dirty worktrees or uncommitted local files.

For cross-repo releases, the deployed cloud, console, and edge SHAs SHALL be recorded together when more than one artifact changes.

#### Scenario: Dev accepts validated default branch

- **WHEN** a change has landed on the relevant repo default branch and tests/typecheck required by the change have passed
- **THEN** it MAY be deployed to `dev` after the normal backup, rsync, restart, and healthcheck sequence

#### Scenario: Ol rejects dirty deployment source

- **WHEN** an operator attempts to deploy `ol` from a checkout with uncommitted changes or from a worktree branch that is not the selected release ref
- **THEN** the deployment MUST stop before remote sync
- **AND** it MUST report the checkout/ref eligibility failure

#### Scenario: Ol records exact release version

- **WHEN** an `ol` deployment succeeds
- **THEN** the release note or OpenSpec task SHALL record the exact committed SHA or tag for each deployed artifact

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
