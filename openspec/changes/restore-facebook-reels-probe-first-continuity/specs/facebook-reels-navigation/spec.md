## MODIFIED Requirements

### Requirement: Ordered trusted-input navigation
The Facebook Reels driver SHALL dispatch exactly one trusted forward key per admitted `page.scroll`, selected by a non-blocking session preference rather than DOM axis classification. A new session SHALL prefer ArrowRight. A delivered key without canonical progress SHALL make the next normally admitted command prefer ArrowDown or ArrowRight, whichever was not just tried; canonical progress SHALL retain the successful key. The driver MUST NOT require a unique active video or structural axis before the key, dispatch wheel input, click a next control, try the opposite key within the same command, or use the preference as an eligibility latch.

#### Scenario: New session probes horizontal navigation
- **WHEN** a new session receives an admitted, explicitly keyboard-safe Reels scroll
- **THEN** the driver SHALL dispatch exactly one ArrowRight gesture regardless of structural-axis availability

#### Scenario: Vertical navigation is learned by bounded probes
- **WHEN** ArrowRight is delivered without canonical progress and the next normally admitted command's ArrowDown produces a canonical next Reel
- **THEN** the driver SHALL report that Reel and SHALL prefer ArrowDown for later scroll commands

#### Scenario: Learned horizontal navigation is reused
- **WHEN** ArrowRight produces a canonical next Reel
- **THEN** the driver SHALL prefer ArrowRight for the next normally admitted scroll

#### Scenario: Structural ambiguity cannot block navigation
- **WHEN** active-video or global-control observations are missing, competing, disabled, occluded, or unable to establish one axis while stable keyboard safety is true
- **THEN** the driver SHALL still dispatch the command's one preferred key

#### Scenario: Prior terminal outcome does not create a latch
- **WHEN** one command ends with missing, unchanged, or ambiguous canonical identity and Cloud later sends another admitted scroll
- **THEN** the driver SHALL freshly verify stable safety and MAY dispatch the later command without waiting for any saved content transition

### Requirement: Per-method movement proof
The one navigation actuation SHALL be followed by bounded observation of the freshly active Reel's canonical `noteId`. Input dispatch, document position, video coordinates, control structure, media URL, DOM identity, and media-segment changes MUST NOT prove progress. For a canonically identified pre-state, success requires a different canonical post-state `noteId`; for an anonymous pre-state, success requires any canonical post-state `noteId`. After trusted input delivery, failure to observe that proof SHALL select the alternate key for the next admitted command; observing the proof SHALL retain the successful key. Either result SHALL end the current command without another write or a pending transition.

#### Scenario: Canonical identity changes after input
- **WHEN** the post-actuation active Reel has a canonical `noteId` different from the canonical pre-state
- **THEN** the driver SHALL report one fresh Reels card batch and retain the successful key

#### Scenario: Anonymous entry gains canonical identity after input
- **WHEN** the pre-state has no canonical `noteId` and bounded post-observation resolves one canonical active Reel
- **THEN** the driver SHALL report that Reel once and retain the successful key

#### Scenario: Media or DOM changes without canonical progress
- **WHEN** media URL, media segments, controls, or active-video DOM selection changes while canonical `noteId` is missing or unchanged
- **THEN** the driver SHALL NOT report navigation success and SHALL select the alternate key for the next admitted command

#### Scenario: Failure before input does not teach a direction
- **WHEN** stable surface, keyboard-safety, cancellation, or deadline admission fails before trusted input is delivered
- **THEN** the driver SHALL perform zero input and SHALL leave its key preference unchanged
