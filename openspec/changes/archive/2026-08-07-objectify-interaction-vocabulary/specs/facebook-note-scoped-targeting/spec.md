## MODIFIED Requirements

### Requirement: Reel follow commands carry and enforce canonical note identity

`facebook.user.follow` MAY carry an optional `noteId` for Reel execution. When the Facebook session is in Reels mode, `noteId` MUST be present and MUST resolve to the canonical `https://www.facebook.com/reel/<id>` identity currently reported by the active Reel reader. The Edge MUST re-check this identity immediately before acting and MUST NOT treat `authorId`, current DOM order, or a generic Follow label as a substitute. Existing non-Reel follow callers that use `authorId` remain wire-compatible.

#### Scenario: Delayed follow command cannot hit the next Reel
- **WHEN** Cloud sends a follow command for Reel A but Reel B is active when Edge reaches the command
- **THEN** Edge returns `no_target` and performs zero clicks
- **AND** Reel B's author is not followed

#### Scenario: Existing profile follow payload remains compatible
- **WHEN** a non-Facebook-Reels caller sends the existing `{platform}.user.follow` payload with `authorId` and no `noteId`
- **THEN** protocol decoding remains valid
- **AND** the existing non-Reel execution path is unchanged
