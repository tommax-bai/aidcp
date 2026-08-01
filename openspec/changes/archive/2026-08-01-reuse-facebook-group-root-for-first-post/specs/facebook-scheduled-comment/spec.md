## MODIFIED Requirements

### Requirement: First-post selection is a bounded read-open operation

Cloud SHALL request first-post selection through the existing `note.open` protocol message with a Facebook-only selection discriminator, the target group container, and the current task lease ID. Edge SHALL establish the canonical group discussion root before selecting the first post. Edge SHALL skip the root navigation when one fresh probe on the current CDP target proves that the page is the exact target-group root, the document and group scope are ready and unblocked, the feed is not loading, no modal obscures the surface, and the actual feed scroller is at its origin. Missing, malformed, failed, or mismatched reuse evidence SHALL fall back to one navigation to the canonical group root, except that an observed cancellation or task takeover SHALL terminate without navigation. Edge SHALL then select one eligible permalink or session-bound target, open or bind it as required, and emit the existing `note.detail` shape with the selected target as `noteId`. This operation MUST NOT emit a search activity receipt or be counted/reported as keyword search.

Before accepting a first-post candidate, Edge MUST prove in that candidate probe that the candidate still comes from the exact requested canonical group root, including origin, path, empty query/hash, surface, and group scope. A context change after an in-place reuse SHALL trigger the one canonical root navigation and a fresh candidate probe using only the command's remaining fixed scroll-round budget. A context mismatch after that navigation MUST end honestly without another navigation loop. Once Edge accepts a candidate, existing permalink or session-bound target binding rules remain authoritative and Edge MUST NOT navigate back to the group root to substitute another post.

When the container is invalid, the group feed cannot be opened, the page is blocked, no eligible post hydrates within the bounded window, or the selected target cannot be opened and bound, Edge SHALL return an honest `open_note` failure and MUST NOT emit a fabricated detail.

#### Scenario: Exact ready group root is reused
- **WHEN** the current CDP target is the exact requested group root, its document and unique group scope are ready and unblocked, its feed is settled, and its actual feed scroller is at the origin
- **THEN** Edge skips the canonical group-root navigation
- **AND** Edge freshly probes and binds the first eligible post on that current target

#### Scenario: Uncertain current page falls back to canonical navigation
- **WHEN** any current-page reuse field is missing, malformed, failed, or does not prove an exact reusable target-group root
- **THEN** Edge navigates to the canonical group root exactly once before first-post selection
- **AND** the reuse uncertainty itself is not reported as a completed or failed Facebook action

#### Scenario: Cancellation does not become a navigation fallback
- **WHEN** cancellation or task takeover is observed before or after the reuse probe
- **THEN** Edge terminates the command without navigating the current page

#### Scenario: Reused page changes context before candidate acceptance
- **WHEN** the initial group root was reused but the first-post candidate probe no longer proves the exact requested canonical group root
- **THEN** Edge performs the one canonical group-root navigation and continues with only the command's remaining fixed scroll-round budget
- **AND** if the context still mismatches after navigation, Edge returns `target_context_mismatch` without accepting a candidate, commenting, or navigating again

#### Scenario: First-post read returns the selected permalink as detail identity
- **WHEN** the first eligible group post is successfully selected and opened
- **THEN** Edge emits `note.detail` whose `noteId` is that post's canonical navigable permalink and whose content belongs to the same post

#### Scenario: Cloud accepts an equivalent multi-permalink identity
- **WHEN** Edge returns `https://www.facebook.com/groups/<group>?multi_permalinks=<post>` for the selected first post
- **THEN** Cloud accepts it as a canonical group-post permalink when `<post>` derives a stable Facebook post identity
- **AND** Cloud continues to reject non-group posts, empty identities, and unknown URL shapes

#### Scenario: No eligible feed post is an honest non-submit
- **WHEN** no top-level post with a stable group-post permalink or safely bound session target and comment affordance hydrates within the bounded selection window
- **THEN** Edge returns an explicit open failure and Cloud does not compose, approve, or submit a comment

#### Scenario: First post starts below the initial viewport
- **WHEN** the canonical target group is open but its first feed cards begin below the cover/composer and outside the initial viewport
- **THEN** Edge performs a fixed bounded sequence of same-container downward scroll-and-probe rounds
- **AND** it opens the first eligible hydrated card without navigating home, searching, changing groups, or substituting a later targeting mode

#### Scenario: Native decoding preserves first-post intent
- **WHEN** Cloud sends `note.open` with `selection=first_commentable_group_post` and a canonical group container
- **THEN** every active Edge command-mapping and decoding layer preserves both fields and routes the bounded first-post operation
- **AND** the request MUST NOT degrade into a generic current-page `note.open`

#### Scenario: First-post failures remain distinguishable
- **WHEN** first-post opening ends because no candidate hydrated, the selected post has no uniquely bound comment editor, target context mismatches, or Cloud times out waiting for detail
- **THEN** the result and user-facing receipt preserve the corresponding reason
- **AND** Cloud MUST NOT report all of those outcomes as “群内未找到合适的可评论帖子”
