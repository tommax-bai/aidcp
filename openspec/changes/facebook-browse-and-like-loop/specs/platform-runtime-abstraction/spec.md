## ADDED Requirements

### Requirement: Facebook declares browse and interact capabilities and the session-start gate admits its browse loop

The platform registry and the Facebook edge driver SHALL add the `browse` and `interact` capabilities for Facebook, and the cloud session-start platform gate SHALL correspondingly admit the Facebook browse loop (previously refused because Facebook did not declare `browse`). The edge driver capability vocabulary and the cloud registry capability vocabulary for Facebook MUST be aligned word-for-word — this change MUST eliminate any pre-existing `join`-vocabulary mismatch rather than adding a new divergence. The `browse` capability MUST NOT be declared for Facebook unless a Facebook-specific BrowseSession is present in the same change (per the atomic co-landing requirement), so the assembly gate never mounts the xhs BrowseSession on a Facebook edge.

#### Scenario: Facebook account can start a browse session after capabilities are added

- **WHEN** the Facebook registry entry and driver declare `browse` and `interact`, and a Facebook account starts a session
- **THEN** the cloud session-start platform gate admits the Facebook browse loop instead of refusing it

#### Scenario: Edge and cloud capability vocabularies match word-for-word

- **WHEN** the edge Facebook driver capability list and the cloud registry capability list for Facebook are compared
- **THEN** they are word-for-word identical, including the pre-existing `join` entry, with no divergence introduced or left in place

#### Scenario: Session-start gate still refuses a platform without browse

- **WHEN** an account's platform registry entry does not declare `browse`
- **THEN** the session-start gate refuses to start the browse loop with a named reason and does not spin up a zombie session
