## ADDED Requirements

### Requirement: AdsPower-first environment creation is constrained by OS family

When creating an AdsPower environment, the desktop shell SHALL treat the operator selection as an OS-family constraint rather than a fixed complete-machine template. The shell SHALL call AdsPower `user/create` with a minimal `fingerprint_config` that constrains the requested desktop OS family and required safety policy, and it SHALL let AdsPower generate the remaining fingerprint details. The shell MUST NOT pin a small fixed set of complete machine shapes such as stable CPU, memory, screen, and renderer combinations for every new profile.

The minimal `fingerprint_config` SHALL keep only fields required for consistency and safety: the requested desktop OS family through AdsPower-supported UA OS constraints, proxy-safe WebRTC, IP-based timezone/location, blocked geolocation prompts, required noise fields, language policy, and browser kernel compatibility when required by the bundled runtime. The shell MAY keep deterministic validation for the requested OS family and for mutually exclusive WebGL modes, but it MUST NOT use that validation to reintroduce a fixed list of complete machine templates.

#### Scenario: Windows creation does not pin one complete machine shape
- **WHEN** the operator selects Windows and creates an environment
- **THEN** the `user/create` payload constrains the fingerprint to a Windows desktop UA OS family
- **AND** the payload does not include fixed `device_memory`, `hardware_concurrency`, `screen_resolution`, or fixed WebGL renderer fields from one of a small set of complete templates
- **AND** AdsPower is left responsible for generating those remaining fingerprint details

#### Scenario: macOS creation does not pin one complete machine shape
- **WHEN** the operator selects macOS and creates an environment
- **THEN** the `user/create` payload constrains the fingerprint to a macOS desktop UA OS family
- **AND** the payload does not include fixed `device_memory`, `hardware_concurrency`, `screen_resolution`, or fixed WebGL renderer fields from one of a small set of complete templates
- **AND** AdsPower is left responsible for generating those remaining fingerprint details

#### Scenario: unsafe OS requests are rejected before AdsPower writes
- **WHEN** the creation request names an unsupported OS family
- **THEN** the shell rejects the request before calling `user/create`
- **AND** it reports the unsupported OS honestly instead of falling back to a different OS

### Requirement: Facebook batch creation chooses OS families, not fixed machine templates

Facebook batch creation SHALL assign each planned account an OS family independently from the supported OS-family set. The batch planner MUST ignore renderer-provided fixed machine-template values, and MUST NOT sample from a five-item complete-machine template list. The selected OS family SHALL be carried through the same single-profile creation path and the same AdsPower-first fingerprint construction used by ordinary single creation.

#### Scenario: batch planning samples only OS families
- **WHEN** Facebook batch planning is requested for multiple accounts
- **THEN** each planned item carries one supported OS-family key
- **AND** no planned item carries a fixed complete-machine template key such as CPU/memory/screen/renderer shape

#### Scenario: renderer template values cannot override batch OS-family planning
- **WHEN** the renderer submits a stale fixed machine-template value with a Facebook batch request
- **THEN** the main process ignores that value
- **AND** it uses only the supported OS-family set for each planned account
