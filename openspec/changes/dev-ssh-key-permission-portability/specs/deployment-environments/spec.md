## MODIFIED Requirements

### Requirement: Deployment targets must be explicit

The project SHALL define explicit deployment targets for aidcp runtime operations. `dev` SHALL refer to ECS `121.89.85.150` with SSH key `~/codes/isales-4.pem` and SHALL be the default target for completed production-facing development deployment, mainline development deployment, and real-machine validation. `ol` SHALL refer to ECS `123.56.253.183` with SSH key `/Users/baitianxing/Downloads/ol.pem` and SHALL be used only when the user explicitly requests stable online deployment.

Any cloud, console, or edge release operation MUST name the target before touching remote state. Deployment tools and docs MUST NOT rely on the legacy assumption that there is only one ECS target.

#### Scenario: Dev target preflight

- **WHEN** an operator requests a deployment to `dev`
- **THEN** the deployment preflight SHALL verify the target IP is `121.89.85.150`
- **AND** the SSH key path is `~/codes/isales-4.pem`
- **AND** the key is a readable regular file
- **AND** the preflight SHALL NOT reject the dev key based on POSIX group/other mode bits

#### Scenario: Ol target preflight

- **WHEN** an operator requests a deployment to `ol`
- **THEN** the deployment preflight SHALL verify the target IP is `123.56.253.183`
- **AND** the SSH key path is `/Users/baitianxing/Downloads/ol.pem`
- **AND** the key is a readable regular file
- **AND** the preflight SHALL NOT reject the ol key based on POSIX group/other mode bits

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
- **THEN** the operation MUST have an explicit user request for `ol` or online deployment
- **AND** a missing explicit request MUST stop the operation before any remote state is touched
