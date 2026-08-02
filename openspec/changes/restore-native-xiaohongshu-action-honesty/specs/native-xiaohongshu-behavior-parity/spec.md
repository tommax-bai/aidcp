## ADDED Requirements

### Requirement: Native Xiaohongshu comment submits the complete approved text

The Native Xiaohongshu comment command SHALL submit the exact text that human approval saw. When the command carries an approved contact/group code alongside the comment body, the adapter MUST compose one submitted text from both parts and MUST NOT drop, truncate, or reorder either part. Readback verification before submit MUST cover the composed text, not the body alone. If the composed text cannot be established in the editor before submit, the adapter MUST return a not-started result and MUST NOT dispatch the submit. Accepting the field at the process boundary without consuming it in the page rules MUST NOT be treated as support for that field.

#### Scenario: Contact code reaches the platform

- **WHEN** a Xiaohongshu comment command carries a non-empty approved contact/group code
- **THEN** the submitted comment text contains both the approved body and that code verbatim
- **AND** the pre-submit readback is evaluated against the composed text

#### Scenario: Composed text cannot be verified before submit

- **WHEN** the editor readback does not contain the composed body-plus-code text within the bounded pre-submit window
- **THEN** the adapter returns a not-started comment result with a truthful reason
- **AND** no submit control is actuated

#### Scenario: Declared-but-unused field is a parity failure

- **WHEN** the Native command schema declares and validates the contact/group code but the Xiaohongshu page rules read only the comment body
- **THEN** a focused parity test fails before integration

### Requirement: Native Xiaohongshu note open proves a real detail surface before any view is claimed

Opening a Xiaohongshu note SHALL be confirmed only by positive detail evidence: a detail container for the commanded note plus at least one non-empty detail signal among title, body text, and images. A note identifier that is merely parseable from the current address MUST NOT be sufficient, because the platform's blocked-note error page carries the same identifier. This applies equally to the fast path that concludes the note is already open without actuating anything: that path MUST also require positive detail evidence before reporting a detail. When the resulting page exposes a blocked/unavailable-note signal, the adapter MUST return a truthful not-started or ambiguous open result. An unconfirmed open MUST NOT emit a note-detail report, because the detail report is the sole entry point through which the browse loop counts a view and charges quota.

#### Scenario: Blocked-note error page is not a successful open

- **WHEN** the page after the open action exposes a blocked/unavailable-note signal while the address still contains the commanded note identifier
- **THEN** the adapter returns a truthful non-success open result
- **AND** it emits no note-detail report, so no view is counted

#### Scenario: Empty shell detail is not reported

- **WHEN** a detail container is present but title, body text, and images are all empty
- **THEN** the adapter returns an ambiguous open result rather than a confirmed detail
- **AND** it does not report the empty projection as an opened note

#### Scenario: Confirmed open carries detail evidence

- **WHEN** the detail container for the commanded note is present with at least one non-empty title, body, or image signal
- **THEN** the adapter reports the detail once and marks the open confirmed

### Requirement: Native Xiaohongshu image browsing returns a measured action receipt

The Xiaohongshu image-browsing command SHALL terminate with an action receipt that the browse loop can consume. The receipt MUST report the number of images actually advanced through, or an explicit no-target result when no carousel exists. The adapter MUST re-resolve the advance control before every step and MUST verify that the displayed image position actually advanced; a dispatched click that does not advance the position MUST stop the loop and be excluded from the reported count. Returning only a refreshed detail projection MUST NOT be treated as completing this command, because the waiting deep-read stage is released only by the action receipt.

Moving the terminal onto the action receipt MUST NOT drop the image evidence that the refreshed detail projection currently carries: the images observed while advancing SHALL still reach the cloud, because that projection is today the only source that refreshes stored reference images for a note. The mechanism is left to the implementation (carried on the receipt, or a separate observation emitted alongside it), but exactly one of them SHALL be the command's terminal, and silently losing the newly loaded images MUST NOT be accepted as satisfying this requirement.

#### Scenario: No carousel returns an explicit no-target

- **WHEN** the opened note exposes no image carousel
- **THEN** the adapter returns an image-browsing action receipt with an explicit no-target reason
- **AND** the deep-read stage is released rather than left waiting

#### Scenario: Reported count equals the observed advances

- **WHEN** five images are requested and the displayed position advances only twice before the advance control stops taking effect
- **THEN** the receipt reports two advances
- **AND** it does not report the requested count or a generic success

#### Scenario: Stale advance control is re-resolved

- **WHEN** the advance control node is replaced after the first advance
- **THEN** the adapter re-resolves it for the next step instead of reusing the detached reference
- **AND** an unresolvable control ends the loop with the count observed so far

#### Scenario: Newly loaded images still reach the cloud

- **WHEN** advancing the carousel loads images that were not present in the original detail report
- **THEN** those images are still delivered to the cloud alongside the measured receipt
- **AND** the command still has exactly one terminal, so the deep-read stage is released once

### Requirement: Native Xiaohongshu list return reports measured navigation truth

The Xiaohongshu navigation-back command SHALL derive its success flag from the observed surface after the action. A hardcoded success flag with a separate, weaker phase field MUST NOT be used, because downstream consumers read the success flag. When the originating list surface is not restored within the bounded window, the adapter MUST report a non-success result with a truthful reason.

#### Scenario: Back does not restore the list surface

- **WHEN** the page after navigation back is neither the feed nor the originating search result surface
- **THEN** the action receipt reports failure with a truthful reason
- **AND** it does not report success with only a degraded phase field

#### Scenario: Back restores the list surface

- **WHEN** the originating list surface is observed after navigation back
- **THEN** the action receipt reports success

### Requirement: Native Xiaohongshu comment scrolling reports measured displacement and observed count

The Xiaohongshu comment-scroll command SHALL derive both its success flag and its reported count from measurement taken after the action. The success flag MUST NOT be hardcoded while the real displacement is recorded only in a weaker side field, because the reading stage consumes the success flag. The reported comment count MUST be the number of comment items actually observed after scrolling; echoing the requested count MUST NOT be used, because the consumer treats the receipt as evidence that comments were read and defaults a missing count to one. When the comment region does not move, the adapter MUST report a non-success result with a truthful reason so the reading stage records zero comments read rather than a fabricated one.

#### Scenario: Comment region does not move

- **WHEN** the comment region's scroll position is unchanged after the scroll action
- **THEN** the action receipt reports failure with a truthful reason
- **AND** no comment count is reported as observed

#### Scenario: Reported count is observed, not requested

- **WHEN** the command requests two scroll steps and three comment items are observable afterwards
- **THEN** the receipt reports the observed count from the page
- **AND** it does not echo the requested step count as the count of comments read

### Requirement: Native Xiaohongshu like, collect, and follow resolve structural controls and wait for a state flip

Xiaohongshu like, collect, and follow SHALL resolve their control structurally inside the note's interaction bar and MUST accept exactly one control that belongs to the commanded note. Selecting an element merely because its visible text contains the action word MUST NOT be used, and a cascading fallback across button, inline, and block elements MUST NOT be used, because inverse controls, aggregate counters, and large containers all match that text. Confirmation MUST poll for a state flip on the same resolved control within a bounded window; a single read after a fixed sleep MUST NOT be the judgement. The presence of a generic completion word anywhere in the control's text MUST NOT by itself be treated as a confirmed state flip. When the control does not flip within the bound, the adapter MUST return an ambiguous state-unchanged result and MUST NOT retry the actuation.

#### Scenario: Inverse or aggregate control is not selected

- **WHEN** the note surface exposes an aggregate reaction counter and an undo-labelled control whose text contains the action word alongside the real interaction-bar control
- **THEN** the adapter resolves only the structural interaction-bar control
- **AND** it returns an honest control-not-found result when that structural control is absent

#### Scenario: Flip arrives after the first sample

- **WHEN** the control flips its state later than the first post-dispatch read but inside the bounded window
- **THEN** the adapter observes the flip through polling and reports success

#### Scenario: Control never flips

- **WHEN** the control keeps its neutral state through the whole bounded window
- **THEN** the adapter returns an ambiguous state-unchanged result
- **AND** a generic completion word found in the control's text does not promote it to success

#### Scenario: Follow is bound to the commanded author

- **WHEN** a follow command carries an author identity that does not match the author observable on the current surface
- **THEN** the adapter returns a not-started identity-mismatch result without actuating any control

### Requirement: Native Xiaohongshu notification extraction preserves the calibrated row, content, and item-key contract

Xiaohongshu notification extraction SHALL keep the contract established by real-page calibration. Rows MUST be selected by the calibrated list-container structure; bare generic list items and class-substring guesses that also match avatar rows MUST NOT be used. Item content MUST be read from the dedicated content element and MUST be an empty string when that element is absent; the whole row's text MUST NOT be used as a fallback, because it carries the sender name, the action label, and a relative timestamp. The per-item dedupe key MUST be stable per notification item; a per-sender identifier such as the sender's profile link MUST NOT be used, and when no per-item stable identity exists the key MUST be left empty so the consumer can fall back to its own composite key.

#### Scenario: Multiple notifications from one sender stay distinct

- **WHEN** the same sender produced several comment or mention notifications in one sweep
- **THEN** each extracted item carries a distinct per-item key or an empty key
- **AND** no per-sender profile link is emitted as the dedupe key

#### Scenario: Missing content element yields an empty string

- **WHEN** a notification row exposes no dedicated content element
- **THEN** the extracted content is an empty string
- **AND** the row's combined sender, action-label, and timestamp text is not emitted as content

#### Scenario: Avatar-only rows are not emitted as notifications

- **WHEN** the notification list contains avatar rows and generic list items alongside real notification rows
- **THEN** only the calibrated notification rows are emitted
- **AND** no item is emitted with an empty sender name caused by matching an avatar element first

### Requirement: Native Xiaohongshu publish atoms remain bound to the established publish contracts

Moving Xiaohongshu publish execution into the Native engine MUST NOT exempt it from the existing publish contracts. The body-fill atom SHALL satisfy the established humanized incremental text entry, per-newline real Enter with bounded paragraph/prefix/caret confirmation, semantic-similarity readback threshold, and clear-on-abandon behavior that the publish pipeline capability already requires; a single whole-value assignment with synthetic input events and a strict-equality readback MUST NOT be treated as satisfying it. The submit atom SHALL anchor success to a real platform success signal bound to the submitted draft; a page-wide text or address pattern match MUST NOT be used, because unrelated historical toasts, help copy, and list entries satisfy it. A dispatched but unverified submit MUST remain ambiguous with the dispatch recorded.

#### Scenario: Body fill is not a whole-value assignment

- **WHEN** the Xiaohongshu body-fill atom runs on the rich-text editor
- **THEN** it uses the established incremental entry with per-newline real Enter and bounded confirmation
- **AND** its readback uses the established semantic-similarity threshold rather than strict normalized equality

#### Scenario: Page-wide success text is not a submit receipt

- **WHEN** the page contains success wording that does not belong to the submitted draft
- **THEN** the submit atom does not report a confirmed publish
- **AND** an unverified dispatched submit is reported as ambiguous with the dispatch recorded

### Requirement: Native Xiaohongshu scheduled submit remains bound to confirmed platform mode

The Native Xiaohongshu `set_schedule` atom SHALL preserve the established scheduled-publish contract through the irreversible submit. It MUST read the real schedule switch before acting, MUST leave an already-enabled switch untouched, and MUST confirm an initially disabled switch became enabled within a bounded window before writing the target time. An unreadable switch state MUST NOT be treated as disabled or enabled. After writing, success requires the platform surface to keep the switch enabled, expose the exact Beijing target minute, and expose an exact leaf submit control labelled `定时发布`; an hour-only prefix match or the value just assigned without the other platform signals MUST NOT confirm the atom.

The Native session SHALL remember whether the current publish page was confirmed for immediate mode or for one exact scheduled target. That state MUST be derived from a confirmed publish-page navigation and a successful `set_schedule`, not from a cloud assertion or a page-script marker. Immediately before `submit_publish`, the adapter MUST re-read the platform mode and require it to match the remembered state. A scheduled submit MUST also re-read the exact target minute and actuate only the exact `定时发布` submit control; an immediate submit MUST require the switch to be explicitly off and actuate only the exact `发布` submit control. Unknown or mismatched state MUST terminate before dispatch with `submitDispatched=false`.

#### Scenario: Already-enabled schedule is idempotent

- **WHEN** `set_schedule` reads the real schedule switch as enabled before actuation
- **THEN** it does not click the switch again
- **AND** it proceeds only after the exact target minute and the exact `定时发布` submit control are confirmed

#### Scenario: Minute coercion fails before submit

- **WHEN** the platform keeps the schedule enabled but coerces or rejects the requested minute
- **THEN** `set_schedule` returns a non-success result
- **AND** the publish sequence stops before `submit_publish`

#### Scenario: Scheduled state is lost before submit

- **WHEN** `set_schedule` previously succeeded but the platform switch is off, the exact target minute changed, or only an immediate `发布` control is available at submit time
- **THEN** `submit_publish` does not actuate any submit control
- **AND** it returns a not-started receipt with `submitDispatched=false`

#### Scenario: Immediate submit does not cross an enabled schedule

- **WHEN** the Native session expects immediate mode but the platform schedule switch is enabled
- **THEN** the adapter does not choose a submit control by text order or horizontal position
- **AND** it returns a not-started receipt with `submitDispatched=false`

### Requirement: Native dispatch and receipt truth survive host and transport failures

The Edge host SHALL distinguish a command envelope that was never written to the Native process from one whose bytes were handed to that process. Engine startup, session acquisition, or pre-dispatch cancellation MUST remain `not_started`; entering a runtime method is not dispatch evidence. After the command record is written, a transport timeout, process exit, or unreadable terminal MUST be treated as an unknown effect unless the Native response explicitly proves `not_started`.

For `submit_publish`, an unknown terminal after dispatch MUST preserve the possibility that the irreversible submit occurred by carrying `submitDispatched=true`; it MUST NOT be converted into an ordinary pre-submit failure that an upstream scheduler may safely retry. Conversely, a failure before the command record is written MUST NOT fabricate that flag. A publish submit or identity-capture command MUST produce the typed publish receipt required by its contract; a generic action receipt without `submitDispatched`, identity, or URL evidence MUST NOT be promoted into a successful publish receipt.

The host SHALL also preserve the most specific Native reason available. A non-confirmed action receipt without its own reason MUST fall back to the execution reason, and a non-confirmed publish receipt's concrete error MUST NOT be overwritten by a generic ambiguity label. A search command that returns page cards with a non-confirmed execution MUST NOT be upgraded to a successful `action.completed` receipt merely because an observation payload exists.

#### Scenario: Session acquisition fails before command dispatch

- **WHEN** the Native process cannot start or the session cannot be acquired before the command record is written
- **THEN** the host reports the command as not started with the original stable reason
- **AND** it does not classify the action as dispatched or ambiguous

#### Scenario: Publish terminal is lost after command dispatch

- **WHEN** a `submit_publish` command record was written and the Native process times out or exits without a determinate terminal
- **THEN** the publish result is non-success and carries `submitDispatched=true`
- **AND** the result cannot enter a safe automatic retry path

#### Scenario: Generic receipt cannot confirm a typed publish terminal

- **WHEN** `submit_publish`, `capture_postId`, `capture_scheduled`, or `reconcile_scheduled` returns a generic action receipt
- **THEN** the Native adapter rejects the output as invalid rather than synthesizing a successful publish receipt

#### Scenario: Observation does not upgrade a failed search

- **WHEN** a search execution carries page-card observations but its effect phase is not confirmed
- **THEN** the host may preserve bounded observation evidence but does not emit a successful search completion
- **AND** the failed completion carries the concrete Native reason

### Requirement: Returning from notifications proves the feed surface, not merely an explore-shaped URL

The Native Xiaohongshu `notification_back_home` command SHALL resolve a real home-feed entry and SHALL confirm the exact feed surface after actuation. A note-detail URL under `/explore/<noteId>` MUST NOT be accepted as the home entry or as the post-condition merely because its path contains `/explore`. If the exact feed surface is not confirmed, the command MUST remain non-success.

#### Scenario: A note link is not a home entry

- **WHEN** the notification page contains note links under `/explore/<noteId>` but no exact `/explore` home entry
- **THEN** `notification_back_home` does not actuate a note link and report success

#### Scenario: Detail navigation is not a confirmed return

- **WHEN** a candidate home actuation lands on `/explore/<noteId>`
- **THEN** the command returns an unconfirmed result rather than page cards for a confirmed feed return

### Requirement: Unmeasured Xiaohongshu compatibility branches are removed rather than left claiming success

Any retained Xiaohongshu command branch that reports a page effect SHALL report it from measured evidence. A scroll step MUST report measured displacement rather than an unconditional confirmation. A compatibility branch that cannot produce such evidence MUST be removed once no live producer of its command exists; leaving it in place with a fabricated confirmation MUST NOT be accepted as harmless because it is believed to be unreachable.

#### Scenario: Legacy plan step no longer fabricates a confirmation

- **WHEN** the Xiaohongshu adapter is asked to execute a legacy ordered-step scroll
- **THEN** it either reports the measured before/after displacement or the branch no longer exists
- **AND** no step result is emitted with a confirmed reason and no measurement

### Requirement: Native Xiaohongshu unread detection is structural, never clears a real unread, and has a single batch sequence source

The Native Xiaohongshu runtime SHALL provide a structural reading of the notification entry's unread badge. The reading MUST traverse both the wide and the narrow entry layouts and evaluate the visible entry, because both entries coexist in the DOM and reading the hidden one reports no unread while unread items exist. Unread MUST be judged as "a visible badge element inside the entry's badge container other than the always-present icon"; an always-present icon with an empty slot MUST NOT be judged as unread, and a dot badge without a number MUST still be judged as unread with the numeric count treated as supplementary only. When the entry or its badge container cannot be read, the reading MUST report an unknown state and MUST NOT report "no unread", because the monitoring contract forbids resetting a known unread to none.

A reading that no live runtime path consumes MUST NOT be treated as satisfying the notification sweep contract: the sweep's only trigger is the unread signal, so an unread judgement that is never invoked leaves the whole notification chain dark and every notification-extraction fix unpowered. Where the periodic invocation and the signal emission live is an assembly concern, but the unpowered state MUST be recorded as an open dependency rather than reported as restored.

The unread batch sequence SHALL have exactly one source: the monotonic value taken when the unread state flips from none to present. Page rules MUST NOT mint a batch sequence of their own on notification list or notification home reports; a wall-clock timestamp per report is not a batch sequence, because every report of the same unread wave then carries a different value.

#### Scenario: Always-present icon alone is not unread

- **WHEN** the notification entry exposes its always-present badge container and icon with no other visible child
- **THEN** the reading reports no unread

#### Scenario: Dot badge without a number is unread

- **WHEN** the badge container holds a visible dot badge that carries no digits
- **THEN** the reading reports unread with the count treated as supplementary
- **AND** a numeric badge reports unread and carries its number

#### Scenario: Narrow layout reads the visible entry

- **WHEN** both a hidden wide-layout entry and a visible narrow-layout entry are present
- **THEN** the reading evaluates the visible entry
- **AND** it does not report "no unread" because the hidden entry carries no badge

#### Scenario: Unreadable entry is unknown, not "no unread"

- **WHEN** the notification entry cannot be located or the read fails
- **THEN** the reading reports an unknown state
- **AND** a previously known unread state is not cleared

#### Scenario: Unconsumed reading is not a restored sweep

- **WHEN** the runtime exposes an unread reading but no live path invokes it and no unread signal is emitted
- **THEN** the notification sweep is treated as not yet restored and the dependency is recorded
- **AND** the notification extraction fixes are not reported as effective in production

#### Scenario: Page rules do not mint a batch sequence

- **WHEN** the adapter reports notification items or notification home counts
- **THEN** the report carries no page-minted wall-clock batch sequence

### Requirement: Native Xiaohongshu notification category viewing terminates with an action receipt

Viewing the like/collect and new-follower notification categories SHALL terminate with an action receipt under the action name the cloud role waits for, because those roles release the category only on that receipt and the triage loop otherwise stalls until the sweep-wide timeout. When the category tab is not hit, the adapter MUST return an explicit no-target receipt rather than a generic unconfirmed result, so a drifted selector is exposed instead of being reported as viewed. Sender extraction is a read-only side output of clearing the category: an extraction failure MUST NOT block the clearing receipt.

The command still has exactly one terminal. Moving the terminal onto the receipt MUST NOT drop the extracted notification items, because those items are the sole source of the notification contact roster; the mechanism is left to the implementation, but silently losing the items MUST NOT be accepted as satisfying this requirement.

#### Scenario: Category tab is not hit

- **WHEN** the category tab cannot be resolved on the notification page
- **THEN** the adapter returns a non-success action receipt with an explicit no-target reason
- **AND** the waiting category role is released rather than left waiting for the sweep timeout

#### Scenario: Category viewed returns a clearing receipt

- **WHEN** the category tab is hit and the category is viewed
- **THEN** the adapter returns a successful action receipt under the action name the cloud role waits for

#### Scenario: Extraction failure does not block the receipt

- **WHEN** sender extraction fails after the category was viewed
- **THEN** the clearing receipt is still returned
- **AND** the failure is recorded rather than converted into a failed clearing result

#### Scenario: Extracted items still reach the cloud

- **WHEN** the category view extracts sender items
- **THEN** those items still reach the cloud alongside the measured receipt
- **AND** the command still has exactly one terminal

### Requirement: Native Xiaohongshu comment-notification sweep scrolls to the end and honors the commanded scroll budget

Sweeping the comment-and-mention category SHALL keep loading until the list stops growing: the adapter MUST count the rows each round, MUST treat a bounded number of consecutive rounds without growth as reaching the end, and MUST bound the loop with a hard cap. Extracting only what the first screen already rendered MUST NOT be treated as covering the category, because unread items beyond one screen then stay unread and the clear-to-zero premise breaks. The scroll budget carried by the command MUST participate in that bound; accepting and validating the budget at the process boundary while the page rules never read it MUST NOT be treated as support for that parameter.

#### Scenario: Rows beyond the first screen are covered

- **WHEN** the category holds two rows on the first screen and two more load after scrolling
- **THEN** all four rows are extracted and reported

#### Scenario: End of list stops the loop

- **WHEN** the row count does not grow for the bounded number of consecutive rounds
- **THEN** the loop stops and the sweep reports what it collected
- **AND** the loop is also stopped by a hard cap when growth never settles

#### Scenario: Commanded scroll budget is not a dangling parameter

- **WHEN** the command carries a scroll budget
- **THEN** that budget participates in the loop bound
- **AND** a budget that the page rules never read fails a focused parity test

### Requirement: Native Xiaohongshu per-tab unread counts come from the calibrated leaf tab badges

The notification home report SHALL read each category's unread count from a numeric badge inside that category's own leaf tab. A page-wide text scan MUST NOT be used, because any number near an action word elsewhere on the page — a note's like count, a follower total, page chrome — is then counted as unread. Wrapper elements that also carry tab-like class names MUST be excluded, because their concatenated text leaks one category's badge into another. A badge value MUST be accepted only as a plain digit run of at most three digits on a leaf node, and unit-suffixed text such as a ten-thousand marker MUST NOT be converted into an item count. When no such badge is found, the count MUST be reported as zero; treating an unparseable value as one MUST NOT be used, because the cloud's clear-to-zero loop then reads a count that never reaches zero and burns every sweep down to its attempt limit.

#### Scenario: Page chrome numbers are not unread counts

- **WHEN** the page shows an action word followed by a number outside the notification category tabs
- **THEN** that number is not reported as an unread count

#### Scenario: Unit-suffixed text is not an item count

- **WHEN** a badge-like text carries a ten-thousand unit marker
- **THEN** it is not converted into a count of unread items

#### Scenario: No badge means zero

- **WHEN** a category tab exposes no numeric badge
- **THEN** that category is reported as zero unread
- **AND** an unparseable value is not promoted to one

#### Scenario: Wrapper containers do not leak across categories

- **WHEN** a wrapper element whose class name also contains the tab token wraps all three category tabs
- **THEN** its concatenated text is not read as any category's badge

### Requirement: Native Xiaohongshu notification category tab is resolved as a calibrated leaf tab

Selecting a notification category SHALL resolve the calibrated leaf tab element and match its text strictly: the comment-and-mention tab by whole-string match on its label, the like/collect and new-follower tabs by a bounded label length that tolerates an appended badge number. A page-wide search for the first visible element whose text contains the action word MUST NOT be used, and a cascading fallback across button, inline, and block elements MUST NOT be used, because note cards, sidebar entries, and the tab list wrapper all match that text and actuating the wrapper does not switch the category. Whether the category switched MUST be derived from the actuation result on the resolved tab; inferring it from generic active-state class names MUST NOT be the judgement.

#### Scenario: Non-tab elements carrying the action word are not selected

- **WHEN** the page exposes note cards and sidebar entries whose text contains the category word but no calibrated leaf tab
- **THEN** the adapter returns an honest no-target result for the category
- **AND** it does not actuate a wrapper element and report the category as viewed

#### Scenario: Calibrated leaf tab is selected by strict text

- **WHEN** the calibrated leaf tabs are present, one of them labelled with the category name and an appended badge number
- **THEN** the adapter resolves that leaf tab
- **AND** it does not resolve the tab list wrapper that contains all three labels

### Requirement: Native Xiaohongshu notification text fields are truncated on code-point boundaries with field-scoped limits

Notification text fields SHALL be truncated on code-point boundaries and MUST NOT split a surrogate pair, because a split pair reaches the notification card as a replacement character. A truncated field MUST carry a visible ellipsis marker. Limits MUST be field-scoped — content, sender name, and note title each capped at their own size — rather than a single whole-row-sized cap, because a row-sized cap combined with whole-row text turns every notification into an unreadable blob.

#### Scenario: Emoji at the cut boundary is not split

- **WHEN** the character at a field's truncation boundary is an emoji represented by a surrogate pair
- **THEN** the field is cut on the code-point boundary without producing a replacement character
- **AND** the truncated field carries an ellipsis marker

#### Scenario: Field limits are scoped per field

- **WHEN** notification content, sender name, and note title are reported
- **THEN** each is capped at its own field-scoped limit rather than a shared row-sized limit

### Requirement: Native Xiaohongshu publish candidates never self-confirm from command-authored text

`publish_add_with_candidate` SHALL report success only from a platform-produced structural signal that is independent of the text or candidate row used by the command itself. A topic MAY confirm from the calibrated topic-token structure. Until equivalent structures are calibrated for mention, location, and collection, those branches MUST NOT treat the command-authored literal, the candidate's own selected appearance, or an entry-label echo as confirmation. A missing or non-actuated editor, entry, or candidate SHALL remain `not_started` with its specific reason; an actuated candidate without independent acceptance evidence SHALL remain ambiguous.

#### Scenario: Mention literal is not an account binding

- **WHEN** the command writes `@name`, clicks a matching candidate, and the only readable result is the same literal in the editor
- **THEN** the result is `ambiguous` with `publish_candidate_unconfirmed`
- **AND** it is not promoted to a confirmed mention

#### Scenario: Candidate appearance is not location or collection binding

- **WHEN** a location or collection candidate becomes selected or its label is echoed into the entry after the click
- **AND** no calibrated independent binding structure is available
- **THEN** the result remains `ambiguous` rather than confirmed

#### Scenario: Zero-actuation candidate failure keeps its exact phase

- **WHEN** the required editor, entry, or candidate cannot be found or a click cannot be dispatched
- **THEN** the command remains `not_started` with the corresponding specific reason
- **AND** it is not collapsed into post-dispatch ambiguity

### Requirement: Native Xiaohongshu captured publish identity is bound to the current submission

An immediate publish identity SHALL be derived only from a unique note identity exposed by a success-result surface that became new or changed after the current submit actuation. A page-wide first-link scan, a stale result node, the creator page URL, or an arbitrary `id` query parameter MUST NOT be promoted to the published note. The Native session SHALL bind the captured identity to the current publish `recordId`; `capture_postId` MUST NOT recover an unbound identity from whatever note happens to be visible later. A public `postUrl`, when present, MUST be an HTTPS Xiaohongshu detail URL whose path identity equals the captured post id and whose query carries a non-empty `xsec_token`. Missing identity evidence SHALL leave the already-submitted record unconfirmed rather than attaching another note's identity.

#### Scenario: Old visible note is not the current publish

- **WHEN** the page contains an older visible note link but the current submit result exposes no bound note identity
- **THEN** `capture_postId` returns a typed non-success receipt
- **AND** it does not return the old link or a creator-page query id

#### Scenario: Fresh unique submit result binds the identity

- **WHEN** the current submit creates or changes a success-result surface that exposes exactly one note identity
- **THEN** that identity is bound to the current `recordId`
- **AND** the following `capture_postId` returns only that bound identity

#### Scenario: Public link requires a token and matching identity

- **WHEN** the bound result exposes a bare detail link, a non-Xiaohongshu link, a tokenless link, or a link for a different note id
- **THEN** it is not returned as `postUrl`
- **AND** no URL is manufactured from the bare id

### Requirement: Native Xiaohongshu scheduled capture and reconciliation use distinct identity states

Capturing a scheduled submission SHALL identify one still-scheduled row by the platform internal id when available, otherwise by the conjunction of frozen title, the complete Asia/Shanghai calendar date and minute, and positive scheduled state. Generic UI `data-id` values MUST NOT be treated as platform note ids. Reconciliation after the target time SHALL distinguish a still-scheduled row from a published row: a still-scheduled match MUST return `scheduled_pending`; a published match SHALL be successful only when one unique row provides both a public post id and a usable tokenized public URL. Missing or multiple matches MUST remain pending or ambiguous rather than selecting the first row.

#### Scenario: Same title and minute on another date is not the scheduled record

- **WHEN** a visible scheduled row shares the frozen title and clock minute but displays another calendar date
- **THEN** it is not captured as the target scheduled record

#### Scenario: Still scheduled is pending, not published

- **WHEN** reconciliation finds the uniquely bound record still in scheduled state
- **THEN** it returns a typed non-success receipt with `scheduled_pending`

#### Scenario: Published reconciliation requires complete public identity

- **WHEN** reconciliation finds one published row with a public post id and a matching HTTPS Xiaohongshu detail URL carrying `xsec_token`
- **THEN** it returns that id and URL as confirmed
- **AND** an id without that URL remains unconfirmed

### Requirement: Native Xiaohongshu parity is protected by behavior-level regression tests

The Edge repository SHALL contain focused Xiaohongshu Native tests derived from the retired TypeScript behavior for comment composition, note-open evidence, image-browsing receipts, navigation-back truth, comment-scroll measurement, interaction control resolution and confirmation, notification extraction, and publish atom contracts. Tests MUST assert externally meaningful outcomes and reason codes rather than only checking that a selector string exists or that a branch returns. Test fixtures MUST NOT globally pin element geometry in a way that makes the adapter's visibility judgement unconditionally true, because that silently disables the guard the tests are meant to protect.

#### Scenario: Regression to a flattened behavior is rejected

- **WHEN** a Xiaohongshu implementation again drops the approved contact code, accepts a parseable identifier as an opened note, returns a refresh-only projection for image browsing, hardcodes a success flag, echoes a requested count as an observed one, or selects an interaction control by visible text alone
- **THEN** a focused parity test fails before integration

#### Scenario: Notification-side regression is rejected

- **WHEN** a Xiaohongshu implementation again extracts only the first screen of a notification category, reads per-category unread counts from page-wide text, resolves a category tab by page-wide text alone, returns notification items without an action receipt for the like/collect or new-follower categories, truncates notification text on UTF-16 boundaries, or mints a wall-clock batch sequence in the page rules
- **THEN** a focused parity test fails before integration

#### Scenario: Visibility guard is exercised rather than pinned

- **WHEN** a Xiaohongshu router test covers a control that the adapter must reject as not visible
- **THEN** the fixture gives that element a non-visible geometry instead of a globally pinned visible rectangle
- **AND** the test asserts the adapter's honest not-found or not-started outcome
