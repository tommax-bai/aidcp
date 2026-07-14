# facebook-dev-autobrowse-policy Specification

## Purpose
TBD - created by archiving change facebook-dev-autobrowse-enable. Update Purpose after archive.
## Requirements
### Requirement: Facebook automatic browsing is enabled only for dev fleet children

When the desktop edge spawns a core child, it SHALL derive an explicit Facebook browse mode from the normalized platform and resolved cloud environment. A Facebook child targeting `dev` SHALL receive `AIDCP_FB_BROWSE_AUTO=on`. A Facebook child targeting `ol` or a custom endpoint SHALL receive `AIDCP_FB_BROWSE_AUTO=off`. Non-Facebook children SHALL receive `off`. The final assignment MUST occur after environment merging so an inherited shell value cannot weaken this boundary.

#### Scenario: All Facebook profiles start real browse on dev
- **WHEN** the operator starts one or more Facebook AdsPower profiles while the resolved cloud environment is `dev`
- **THEN** every spawned Facebook core receives `AIDCP_FB_BROWSE_AUTO=on` and may enter the existing browse-and-like loop subject to its normal risk controls

#### Scenario: Production and custom endpoints remain disabled
- **WHEN** the operator starts a Facebook AdsPower profile while the resolved cloud environment is `ol` or `custom`
- **THEN** the spawned core receives `AIDCP_FB_BROWSE_AUTO=off` even if the outer Electron process inherited an enabled browse-mode variable

#### Scenario: Non-Facebook profile is unaffected
- **WHEN** the operator starts a non-Facebook profile while the resolved cloud environment is `dev`
- **THEN** the spawned core receives `AIDCP_FB_BROWSE_AUTO=off` and its platform behavior is otherwise unchanged

