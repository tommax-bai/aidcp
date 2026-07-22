## ADDED Requirements

### Requirement: Exact AdsPower profile ownership
The Douyin probe SHALL connect only to the explicitly named AdsPower profile and SHALL distinguish a lifecycle-owning API connection from an attach-only fallback connection.

#### Scenario: AdsPower API returns the exact active profile
- **WHEN** the AdsPower API returns a CDP endpoint for the requested profile and the start-page marker contains the same profile id
- **THEN** the probe connects and records that it owns the browser lifecycle for this run

#### Scenario: Attach to an already running exact profile
- **WHEN** the AdsPower active API cannot expose the running browser but `DevToolsActivePort`, the process user-data-dir, and the start-page marker all identify the requested profile
- **THEN** the probe MAY attach in attach-only mode and MUST NOT close the browser after the run

#### Scenario: Profile ownership is uncertain
- **WHEN** the process user-data-dir, dynamic CDP endpoint, or start-page marker is absent or does not uniquely match the requested profile
- **THEN** the probe returns `ownership_unconfirmed` without navigating or acting on a Douyin page

### Requirement: Visible blocker and login classification
The Douyin probe SHALL classify blockers using visible structural evidence and SHALL NOT treat hidden verification frames or login-form wording as an active challenge.

#### Scenario: Hidden verification iframe is present
- **WHEN** a verification iframe exists but has no visible rendered area and no visible blocking dialog exists
- **THEN** the probe does not classify the page as `visible_challenge`

#### Scenario: Visible security verification blocks the page
- **WHEN** a verification iframe or challenge dialog is visible and occupies an interactive page region
- **THEN** the probe returns `visible_challenge` and performs no browse advance or write action

#### Scenario: Access is restricted
- **WHEN** the rendered page uniquely shows an access restriction or unavailable-page state
- **THEN** the probe returns `access_restricted` or `page_unavailable` and performs no action

#### Scenario: Public browse page is logged out
- **WHEN** public Douyin cards are visible but the rendered page shows the login action and no authenticated identity evidence
- **THEN** the probe MAY report public browse observations but returns `login_required` for like, comment, and publishing probes

### Requirement: Surface-aware bounded browsing
The Douyin browse probe SHALL identify the current page surface, use a surface-specific advancement strategy, and prove progress with stable work identifiers.

#### Scenario: Jingxuan grid uses an internal scroll container
- **WHEN** the page exposes a unique vertically scrollable container that owns `data-aweme-id` descendants
- **THEN** the probe advances that container rather than `window` or an unrelated navigation or tab container

#### Scenario: Stable grid work identities are observed
- **WHEN** rendered cards expose `data-aweme-id`
- **THEN** the probe de-duplicates those identifiers and reports only identifiers associated with the selected content surface

#### Scenario: Grid card enters a detail modal
- **WHEN** a trusted pointer event on the unique visible cover for a grid work opens a detail modal
- **THEN** the probe requires the resulting `modal_id` to equal the source `data-aweme-id` and requires the active-feed and modal-ready structures before reporting `video_detail_modal`

#### Scenario: Direct detail route remains a navigation skeleton
- **WHEN** `/video/<id>` or a script `.click()` does not produce both matching identity and detail-ready structures within the bounded hydration window
- **THEN** the probe returns `page_not_hydrated` and MUST NOT infer detail readiness from the URL alone

#### Scenario: Content changes after bounded advancement
- **WHEN** a bounded advancement yields a changed de-duplicated set of work identifiers
- **THEN** the probe returns `advanced` with before and after identifiers and re-probes all target nodes

#### Scenario: Content does not change
- **WHEN** the maximum bounded advancement attempts do not change the stable work identifiers
- **THEN** the probe returns `no_change` and MUST NOT claim that a new work was browsed

#### Scenario: Surface is unsupported or ambiguous
- **WHEN** the probe cannot uniquely classify the page as a supported grid or detail surface
- **THEN** it returns `surface_ambiguous` with structural counts and performs no interaction

### Requirement: Gated one-way like probe
The Douyin like probe SHALL default to shadow mode and SHALL perform at most one real like only after exact profile confirmation, explicit action authorization, login confirmation, unique target confirmation, and readable pre-action state.

#### Scenario: Like probe runs without both action gates
- **WHEN** either `AIDCP_DOUYIN_PROBE_LIKE` is not `1` or `AIDCP_DOUYIN_PROBE_CONFIRM_PROFILE` does not exactly equal the connected profile
- **THEN** the probe returns `shadow_ready` or `gated` and does not click a like control

#### Scenario: Current work is already liked
- **WHEN** the unique current work and unique like control report the liked state before action
- **THEN** the probe returns `already_liked` and MUST NOT click or toggle the control

#### Scenario: Like state has no proven positive and negative mapping
- **WHEN** the like control is unique but its accessible and structural state cannot distinguish liked from unliked using validated fixtures
- **THEN** the probe returns `state_unreadable` and MUST NOT click even when both real-action gates are present

#### Scenario: One real like is UI-confirmed
- **WHEN** both gates are satisfied, the account is logged in, the target is unique and initially unliked, and one click is followed by the same work id in liked state
- **THEN** the probe returns `ui_confirmed` and explicitly marks server persistence as unproven

#### Scenario: Target or state changes ambiguously
- **WHEN** the current work id changes, controls are not unique, or the same work does not become liked after the single click
- **THEN** the probe returns `ambiguous`, performs no second click, and MUST NOT report success

### Requirement: Comment fill has no submit capability
The Douyin comment probe SHALL provide only a fill operation and SHALL structurally exclude comment submission behaviors.

#### Scenario: Unique comment editor is filled and read back
- **WHEN** the account is logged in, the same unique work remains current, exactly one visible comment editor is found, and the input is read back successfully
- **THEN** the probe returns `filled_not_submitted` with `submitted=false`, the input length, and a match boolean without echoing the full text

#### Scenario: Comment editor is absent or ambiguous
- **WHEN** no unique visible comment editor can be proven for the current work
- **THEN** the probe returns `editor_not_found` or `ambiguous` without input

#### Scenario: Only the danmaku input is visible
- **WHEN** the only work-adjacent input is identified by the placeholder `发一条弹幕吧`
- **THEN** the probe excludes it from comment-editor candidates and returns `editor_not_found` without input

#### Scenario: Work changes before comment input
- **WHEN** the stable work id differs between editor discovery and the moment before input
- **THEN** the probe returns `target_changed` without entering text

#### Scenario: Source is statically checked for no-submit behavior
- **WHEN** the focused comment probe tests inspect the implementation
- **THEN** they prove the probe has no send-button lookup, Enter-family dispatch, form submission, submit parameter, or submit environment flag

### Requirement: Read-only publishing surface research
The Douyin publishing probe SHALL inspect the web creator/upload surface without selecting a file, filling publish content, or owning final submission.

#### Scenario: Upload entry or composer structure is observed
- **WHEN** a unique creator or upload route and its structural controls are visible
- **THEN** the probe reports the route, candidate counts, accepted file types, multiple-file mode, and editor metadata with `uploaded=false` and `submitted=false`

#### Scenario: Upload landing page has no pre-upload editor
- **WHEN** `creator.douyin.com/creator-micro/content/upload` exposes one enabled single-file video input but no editor before file selection
- **THEN** the probe reports the input metadata and `editor_not_present_before_upload` without selecting a file

#### Scenario: Publishing page requires login or verification
- **WHEN** the creator or upload surface presents a login requirement, visible challenge, or access restriction
- **THEN** the probe reports the blocker and does not attempt to bypass it

#### Scenario: No web publish submission capability exists in the probe
- **WHEN** the publishing probe implementation and focused tests are inspected
- **THEN** they contain no file selection, publish-text input, final publish-control lookup, Enter-family dispatch, form submission, or enable-submit flag

### Requirement: Gated one-way follow and collection probes
The Douyin probes SHALL treat follow and collection as separate one-way actions with independent authorization gates, a single-action budget, exact work identity, readable pre-action state, and post-action UI confirmation.

#### Scenario: Follow is not independently authorized
- **WHEN** `AIDCP_DOUYIN_PROBE_FOLLOW` is not `1` or the confirmed profile does not exactly match the connected profile
- **THEN** the follow probe returns `shadow_ready` or `gated` without clicking

#### Scenario: Unique un-followed author is followed once
- **WHEN** the detail modal id remains stable, one follow control has proven un-followed semantics, and both follow gates are satisfied
- **THEN** the probe clicks once and returns `ui_confirmed` only after the same modal reports followed state

#### Scenario: Author is already followed or state is unreadable
- **WHEN** the follow control reports followed state or cannot distinguish followed from un-followed
- **THEN** the probe returns `already_followed` or `state_unreadable` and MUST NOT click

#### Scenario: Collection is not independently authorized
- **WHEN** `AIDCP_DOUYIN_PROBE_COLLECT` is not `1` or the confirmed profile does not exactly match the connected profile
- **THEN** the collection probe returns `shadow_ready` or `gated` without clicking

#### Scenario: Unique uncollected work is collected once
- **WHEN** the detail modal id remains stable, validated fixtures prove one collection control is uncollected, and both collection gates are satisfied
- **THEN** the probe clicks once and returns `ui_confirmed` only after the same work reports collected state

#### Scenario: Work is already collected or state is unreadable
- **WHEN** the collection control reports collected state or lacks a validated state mapping
- **THEN** the probe returns `already_collected` or `state_unreadable` and MUST NOT click

### Requirement: Known interaction prompt cannot hide action targets
The Douyin probe SHALL treat the first-interaction tutorial as a separate bounded UI preflight and SHALL NOT count input intercepted by its overlay as a social action.

#### Scenario: Exact known interaction prompt is visible
- **WHEN** exactly one visible `button` has the exact text `我知道了`
- **THEN** the probe clicks it once, confirms it disappears, and rechecks that the intended action coordinate resolves to the intended control before any social action

#### Scenario: Prompt or target hit is ambiguous
- **WHEN** the prompt is not unique, remains visible, or `elementFromPoint` resolves the intended action coordinate to another overlay
- **THEN** the probe returns an honest blocked or ambiguous result and MUST NOT claim or retry the social action as successful

### Requirement: Single bounded direct-message reply
The Douyin direct-message probe SHALL reply to at most one uniquely identified recent inbound conversation, SHALL accept only the allowlisted text `好的` or `ok`, and SHALL keep conversation identities and message bodies out of its report.

#### Scenario: Direct-message reply is gated
- **WHEN** `AIDCP_DOUYIN_PROBE_DM_REPLY` is not `1`, the confirmed profile mismatches, or the text is outside the exact allowlist
- **THEN** the probe returns `gated` or `invalid_text` without opening or sending a reply

#### Scenario: Latest inbound conversation is replied to once
- **WHEN** exactly one selected conversation proves its latest message is inbound, one reply editor is visible, the text is allowlisted, and all gates are satisfied
- **THEN** the probe enters and submits the text once, then reports only structural UI confirmation and text length

#### Scenario: Conversation direction or target is ambiguous
- **WHEN** the probe cannot prove a unique conversation, inbound direction, or reply editor
- **THEN** it returns `conversation_ambiguous`, `inbound_unconfirmed`, or `editor_not_found` without input or submission

### Requirement: Separate bounded live chat and comment reply
The Douyin live probe SHALL keep ordinary live chat and comment-targeted reply as distinct, independently gated single-action capabilities.

#### Scenario: Ordinary live chat sends the authorized text once
- **WHEN** `AIDCP_DOUYIN_PROBE_LIVE_CHAT=1`, the profile confirmation matches, one live room and one ordinary chat editor are uniquely ready, and the text is exactly `1111`
- **THEN** the probe submits the text once and reports `ui_confirmed` only from same-room structural evidence

#### Scenario: Comment-targeted live reply sends the authorized text once
- **WHEN** `AIDCP_DOUYIN_PROBE_LIVE_COMMENT_REPLY=1`, the profile confirmation matches, one non-self live comment has a unique reply entry bound to a reply editor, and the text is exactly `666`
- **THEN** the probe submits the bound reply once and reports `ui_confirmed` only from same-room reply evidence

#### Scenario: Targeted reply is unavailable
- **WHEN** the page exposes only an ordinary live chat editor or cannot prove which comment owns the reply editor
- **THEN** the probe returns `reply_target_unavailable` and MUST NOT send `666` as an ordinary chat message

#### Scenario: Live action text or gates are invalid
- **WHEN** either live action lacks its independent gate, has a profile mismatch, or receives text other than its exact authorized value
- **THEN** that action returns `gated` or `invalid_text` without input or submission

### Requirement: Official API is the preferred production publishing path
The research result SHALL identify the Douyin Open Platform as the preferred future production publishing path and SHALL NOT silently fall back to web submission when official authorization is unavailable.

#### Scenario: Official publishing prerequisites are available
- **WHEN** a future AIDCP integration has an approved application, user OAuth authorization, the required `video.create` permission, and a fresh auditable user approval for the publish operation
- **THEN** the design routes upload and create through the official API and uses the returned item identity plus official list or data queries for follow-up status

#### Scenario: Official publishing prerequisites are unavailable
- **WHEN** the application, permission, OAuth authorization, or per-operation user approval is missing
- **THEN** the system reports `official_api_unavailable` or `approval_required` and MUST NOT downgrade to a CDP final-publish action

### Requirement: Minimal redacted evidence
All Douyin probes SHALL emit bounded structural evidence and SHALL exclude secrets and user content from reports.

#### Scenario: Probe report is produced
- **WHEN** any Douyin probe completes or stops
- **THEN** its report contains only the profile id, host/path, surface, stable work id, structural candidate counts, action-gate state, blocker/result enum, evidence boundary, and timestamp needed for diagnosis

#### Scenario: Sensitive browser state exists
- **WHEN** the page contains cookies, storage entries, OAuth tokens, phone numbers, account identifiers, request bodies, comments, or complete content text
- **THEN** the probe does not read or emit those values

### Requirement: Research probes remain isolated from production runtime
The Douyin research probes SHALL remain manually invoked and SHALL NOT register a production platform or alter production scheduling, protocol, persistence, publishing, or risk state.

#### Scenario: Probe code is added
- **WHEN** the change is implemented in `aidcp-edge`
- **THEN** no production command router, Cloud protocol, platform catalog, publish queue, database schema, or RiskController behavior references the Douyin probe

#### Scenario: Live validation is run without explicit write authorization
- **WHEN** a runner is executed for read-only research and no separate action authorization has been provided
- **THEN** it may navigate and inspect bounded page state but performs no like, comment input, upload, follow, collection, message, or publish action
