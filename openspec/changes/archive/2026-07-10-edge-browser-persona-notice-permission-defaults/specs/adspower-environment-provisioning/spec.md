## ADDED Requirements

### Requirement: New AdsPower profiles block geolocation permission prompts by default
The desktop shell SHALL include `location='block'` in the `fingerprint_config` sent through AdsPower `user/create` for every newly provisioned profile. It SHALL also retain `location_switch='1'` so the profile's fingerprint location follows the proxy IP. The shell MUST NOT represent `location='block'` as disabling IP-based fingerprint location, and MUST NOT broaden the proxy-only `user/update` wrapper to retrofit existing profiles.

#### Scenario: New profile receives both location settings
- **WHEN** the operator creates an AdsPower environment from any supported device template
- **THEN** the `user/create` payload contains `fingerprint_config.location='block'`
- **AND** it contains `fingerprint_config.location_switch='1'`

#### Scenario: Existing profile is not silently rewritten
- **WHEN** the application loads an AdsPower profile created before this change
- **THEN** it does not send a fingerprint update through the proxy-only `user/update` path
- **AND** the existing profile remains unchanged unless the operator explicitly recreates or configures it outside that path
