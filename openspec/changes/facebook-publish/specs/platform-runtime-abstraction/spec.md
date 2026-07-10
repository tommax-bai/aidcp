## ADDED Requirements

### Requirement: Facebook declares the publish capability

The platform registry and driver SHALL add the `publish` capability to
Facebook. The edge Facebook driver capability vocabulary and the cloud platform
registry Facebook capability vocabulary MUST be kept byte-for-byte aligned so a
Facebook account can only reach the publish path after both ends declare
`publish`. A Facebook account whose declared capabilities do not include
`publish` MUST NOT reach the Facebook publish executor, and the system MUST
report an honest unsupported outcome rather than falling back to the xhs publish
path.

#### Scenario: Facebook account can publish once the publish capability is added

- **WHEN** the Facebook driver and the cloud registry both declare `publish` for `facebook`
- **THEN** a Facebook account can run the Facebook publish path
- **AND** before the capability is declared, a publish attempt on a Facebook account returns an honest unsupported outcome and never runs the xhs publish path

#### Scenario: Edge and cloud publish capability vocabularies stay byte-for-byte aligned

- **WHEN** the Facebook `publish` capability string is added to the edge driver and the cloud registry
- **THEN** the two capability vocabularies are byte-for-byte identical for the `publish` string, so capability assembly agrees on both ends
