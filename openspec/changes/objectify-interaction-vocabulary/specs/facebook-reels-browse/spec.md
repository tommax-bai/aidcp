## MODIFIED Requirements

### Requirement: Facebook Reels like is a single verified action

When Cloud authorizes a like on the active Reel it SHALL send `facebook.video.like` — the command name declares the video object; Cloud MUST NOT send `facebook.note.like` for a Reel. Edge SHALL verify the declared object against the live page: on `facebook.video.like` it SHALL require the command noteId to match the active canonical Reel, locate exactly one like action in the active video's right-side action rail by structural relationship, and perform at most one trusted click; if the session is not on an active video/Reel it SHALL report the mismatch honestly and MUST NOT silently fall back to the post-level like executor (and symmetrically, `facebook.note.like` arriving while on a Reel MUST NOT be silently executed as a video like). Object routing SHALL follow the declared command name, not a runtime list-mode guess. `ok:true` SHALL require the same Reel to expose a positive selected-state witness such as an unlike semantic or selected reaction icon after the click. Rounded count text alone MUST NOT prove success; ambiguous target, already-liked state, identity drift, missing witness, or timeout MUST be reported honestly and MUST NOT be recorded as success. The completion receipt correlation key remains `like` for both object variants.

#### Scenario: One click produces an unlike state
- **WHEN** exactly one unselected active-Reel like control is found and one trusted click changes it to a positive selected state on the same Reel
- **THEN** Edge reports a successful like with DOM-derived noteId and observation for existing Cloud arbitration and risk recording

#### Scenario: Rounded count does not change
- **WHEN** the selected-state witness is positive but a rounded count such as `5.8K` remains unchanged
- **THEN** the like may still be confirmed from the selected state, and the count is not used as the proof

#### Scenario: Like target is ambiguous or stale
- **WHEN** the requested noteId differs from the active Reel or more than one structural like candidate remains
- **THEN** Edge clicks nothing and returns `no_target` or `ambiguous_target`

#### Scenario: Declared object does not match the live surface
- **WHEN** a Facebook session receives `facebook.video.like` while no video/Reel is active, or `facebook.note.like` while a Reel is the active context
- **THEN** Edge reports the object mismatch honestly and MUST NOT execute the other object's like executor
