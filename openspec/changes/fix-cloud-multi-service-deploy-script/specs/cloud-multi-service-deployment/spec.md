## ADDED Requirements

### Requirement: Deployment shell variables are lexically bounded
The multi-service deployment script MUST use an unambiguous expansion form whenever a shell variable is immediately followed by non-ASCII text.

#### Scenario: Deployment log contains localized punctuation
- **WHEN** a deployment log message places Chinese punctuation immediately after a shell variable
- **THEN** the variable SHALL use braced expansion and SHALL NOT be parsed as an unset extended name under `set -u`

### Requirement: Hazardous source patterns are rejected
Automated validation MUST reject an ASCII shell identifier immediately followed by a non-ASCII code point in the multi-service deployment script.

#### Scenario: A future unbraced localized expansion is introduced
- **WHEN** the deployment script contains `$NAME` directly followed by a non-ASCII character
- **THEN** the focused deployment contract test SHALL fail before an ECS deployment is attempted

### Requirement: Existing topology safety remains intact
The fix MUST preserve the existing backup-before-sync, capability probe, AIDCP-only unit control, ordered three-process startup, and monolith rollback behavior.

#### Scenario: Three-process startup fails
- **WHEN** any content, automation, or API service fails its existing health gate
- **THEN** the deployment script SHALL stop the multi-service units and restore the monolith without operating on isales
