## ADDED Requirements

### Requirement: Resolved cloud environment controls Facebook automatic browse mode

For every core spawn, the desktop client SHALL use the same resolved cloud environment key used to select and display the actual cloud connection to derive `AIDCP_FB_BROWSE_AUTO`. It SHALL apply the derived value only after the final child environment has been assembled, so the mode and the actual connection target cannot diverge due to inherited process environment variables. Applying a new mode SHALL require a core restart and SHALL NOT interrupt an already-running core merely because settings were saved.

#### Scenario: Restart applies dev mode to every Facebook child
- **WHEN** the resolved cloud environment is `dev` and the operator starts or explicitly restarts Facebook environments
- **THEN** each replacement core receives the dev Facebook browse mode while the cloud endpoint remains the resolved dev endpoint

#### Scenario: Existing core is not silently retargeted
- **WHEN** a Facebook environment is already running and the client code or a cloud selection changes
- **THEN** its current core is not silently mutated; the derived mode is applied only to a subsequently spawned core through the existing explicit restart behavior
