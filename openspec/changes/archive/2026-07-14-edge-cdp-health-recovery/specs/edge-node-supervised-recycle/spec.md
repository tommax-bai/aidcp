## ADDED Requirements

### Requirement: Exhausted CDP control-stall recovery SHALL honor browser ownership during recycle

When recovery from an input-control stall reaches an unrecoverable terminal state, the edge SHALL use the existing honest shutdown and supervised recycle semantics. If the browser is owned by the edge, the recycle path MUST establish a fresh browser boundary before future work. If the browser is external or reused, the edge MUST only honestly stop and leave it untouched; it MUST NOT terminate, force-stop, or otherwise interfere with that browser.

#### Scenario: Owned browser reaches unrecoverable control-stall state
- **WHEN** an edge-owned browser cannot recover from a CDP input-control stall within the bounded recovery policy
- **THEN** the edge follows its existing recyclable terminal path and future work is admitted only by the restarted node

#### Scenario: External browser reaches unrecoverable control-stall state
- **WHEN** an external or reused browser cannot recover from a CDP input-control stall
- **THEN** the edge honestly stops and requires operator recovery, while leaving that browser process untouched
