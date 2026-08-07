# facebook-reels-browse Specification

## Purpose
TBD - created by archiving change facebook-empty-feed-reels-fallback. Update Purpose after archive.
## Requirements
### Requirement: Facebook Reels identifies exactly one active video card
Edge SHALL distinguish a keyboard-probeable Reels surface from a reportable or interactable Reel card. An exact `/reel/` or `/reels/` surface with explicit keyboard safety MAY receive one trusted navigation probe without a unique active video or canonical identity. Edge SHALL emit a Reel card or authorize an irreversible interaction only when it freshly resolves exactly one active video and binds that video to a canonical Facebook `/reel/<id>` identity. Missing or ambiguous active video, off-route observations, and identity-changing reads MUST fail closed for reporting and irreversible actions, but active-video structure MUST NOT veto reversible keyboard probing.

#### Scenario: Current Reel wins over preloaded neighbours for reporting
- **WHEN** previous, current, and next videos coexist in the DOM
- **THEN** Edge SHALL report only a uniquely resolved current video with canonical identity
- **AND** failure to make that selection SHALL emit no card without disabling an otherwise safe keyboard probe

#### Scenario: Anonymous or ambiguous landing remains probeable
- **WHEN** an exact `/reel/` surface is explicitly keyboard-safe but canonical identity or unique active-video structure is unavailable
- **THEN** Edge MAY dispatch its one trusted navigation key and SHALL emit no Reel card for the unresolved pre-state

#### Scenario: Route is not a Reel
- **WHEN** the current top-level route is home, login, checkpoint, another Facebook surface, or a non-Facebook URL
- **THEN** Edge SHALL report no Reel target and perform no Reels action

### Requirement: Facebook Reels reads the active video's visible text honestly

For a feed-surface note open, Edge SHALL derive the summary from the active video's bottom-left content overlay, exclude author/follow/audio/action labels, and bind every expansion/read step to the same canonical Reel identity. If an anchored expand control cannot be used without identity drift, Edge SHALL return the real visible snippet or an honest no-target result and MUST NOT claim hidden full text was read.

#### Scenario: Active Reel summary is reported as video detail
- **WHEN** the active Reel has a bottom-left textual summary
- **THEN** Edge reports that text as the note content with `mediaType:video` and the canonical Reel URL as noteId

#### Scenario: Expansion changes identity
- **WHEN** an attempted summary expansion changes the route or active video identity
- **THEN** Edge rejects the expanded result and MUST NOT attribute another Reel's text to the requested note

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

### Requirement: Reels re-entry MUST NOT require a non-empty ordinary feed as its only unlock

An account whose ordinary home feed produces nothing SHALL still be able to be re-authorized onto the Reels surface. Re-authorization MUST NOT depend solely on a non-empty ordinary feed returning, because an account is on Reels precisely when its ordinary feed produced nothing — that unlock can never fire for the accounts that need it.

Cloud MUST NOT use a long-lived `confirmed` flag as evidence of the current page. It SHALL retain only a bounded in-flight Reels redrive attempt and per-session recovery count. Edge SHALL probe the live page for every `facebook.reels.scroll{reason:'resume_redrive'}` and either report the canonical Reel already active or enter Reels through the verified entry path.

Re-entry SHALL be bounded per session. Once the bound is spent, the browse loop MUST reach a terminal state rather than alternating between two surfaces that both yield nothing.

#### Scenario: Reels session returns to an ordinary feed or task page
- **WHEN** a Reels-targeted session is currently on an ordinary feed, group, detail, or other non-Reels page and receives a unified Reels redrive
- **THEN** Edge reconciles the live page to Reels without requiring a non-empty Feed report first
- **AND** Cloud does not consult a past `confirmed` state

#### Scenario: Already on Reels
- **WHEN** Edge receives a unified Reels redrive while a canonical active Reel is already present
- **THEN** Edge reports the current canonical Reel without redundant navigation or input
- **AND** the normal evidence-driven browse loop continues from that fresh card report

#### Scenario: Duplicate evidence during an in-flight entry
- **WHEN** repeated Feed-empty or no-target evidence arrives while one Reels redrive attempt is in flight
- **THEN** Cloud does not issue a parallel entry command
- **AND** a canonical Reel card clears only the transient attempt

#### Scenario: Re-entry is bounded
- **WHEN** Reels redrive recovery has already been used its allowed number of times in one session
- **THEN** further no-target receipts do not create unbounded retries
- **AND** the session reaches a terminal state instead of alternating indefinitely

### Requirement: Configured Reels primary reuses the verified Reels entry path
When a Facebook session pins Reels as its primary surface, Cloud SHALL authorize entry with `facebook.reels.scroll{reason:'facebook_reels_primary'}` and Edge SHALL route that command to the existing Reels entry executor. Edge SHALL first use bounded observation to report a canonical active Reel without input when available. If the observation ends on an exact keyboard-safe Reels surface without a reportable card, Edge SHALL continue the same command through the one-key probe boundary; active-video or axis recognition MUST NOT terminate entry before that probe. Route navigation or input delivery alone MUST NOT count as entry success.

#### Scenario: Configured primary reaches a reportable Reel without input
- **WHEN** Cloud authorizes `facebook_reels_primary` and bounded entry observation verifies one canonical active Reel
- **THEN** Edge SHALL report that Reel through the existing Reels card contract and perform no navigation input

#### Scenario: Reels route is safe but has no reportable card
- **WHEN** bounded entry observation reaches an exact keyboard-safe Reels route but cannot resolve one canonical active Reel
- **THEN** Edge SHALL dispatch exactly one preferred key through the shared navigation actuator
- **AND** it SHALL report a card only if bounded post-observation then verifies canonical progress

#### Scenario: Reels entry remains unresolved after the probe
- **WHEN** the one entry probe is delivered but no canonical active Reel appears within the bounded post-observation window
- **THEN** Edge SHALL return the existing honest ambiguous result and neither Edge nor Cloud SHALL fabricate a view or start content evaluation

### Requirement: Ineffective Reels entry receives one exact-target foreground recovery

For `facebook.reels.scroll{reason:'facebook_reels_primary'}` and `facebook.reels.scroll{reason:'empty_feed_reels_fallback'}`, Edge SHALL keep the first navigation to the Reels route background-first and SHALL prove that the exact bound page reached a ready Reels route/surface before deciding whether entry took effect. If bounded readback proves that the exact bound target remained outside a ready Reels surface, Edge MAY call `Page.bringToFront` on that same target at most once for the command, SHALL re-probe before another write, and MAY issue at most one fresh Reels navigation retry. Reaching the Reels surface MUST suppress foreground activation even when canonical video cards are still hydrating or unavailable; that later card condition SHALL terminate honestly without reclassifying the navigation as ineffective. A late successful entry observed after activation MUST suppress the retry. Target drift, blocker state, or `Page.bringToFront` acknowledgement alone MUST NOT count as entry success.

#### Scenario: First background entry succeeds

- **WHEN** the initial Reels navigation reaches a ready Reels surface
- **THEN** Edge never calls `Page.bringToFront` for that command and separately reports the canonical Reel or an honest hydration/no-target outcome

#### Scenario: Ineffective entry foregrounds and retries once

- **WHEN** the initial navigation completes but bounded same-target readback proves that the eligible Facebook page did not enter a ready Reels surface
- **THEN** Edge calls `Page.bringToFront` once, re-probes the exact target, and issues at most one fresh Reels navigation retry

#### Scenario: Entry completes after activation but before retry

- **WHEN** the post-activation re-probe observes a ready Reels surface
- **THEN** Edge accepts that entry and does not send another `Page.navigate`

#### Scenario: Foreground recovery still cannot confirm entry

- **WHEN** the one foreground recovery and optional fresh navigation retry do not produce a canonical active Reel
- **THEN** Edge returns the existing honest pending, no-target, or ambiguous result and does not fabricate a Reel view

#### Scenario: Blocker or target drift suppresses recovery

- **WHEN** the initial entry readback observes login, challenge, consent, another blocker, or a different target/document context
- **THEN** Edge does not foreground or retry navigation through this recovery path and returns the applicable honest outcome

### Requirement: Anonymous Reels entry receives one bounded local advance

For `facebook_reels_primary` and `empty_feed_reels_fallback`, Edge SHALL preserve one initial 15-second canonical-card hydration window after reaching a ready Reels surface. If that window expires, Edge SHALL invoke the existing bounded Native forward-navigation contract at most once only when fresh active and navigation readbacks bind one unique anonymous `videoKey` and both explicitly prove `inputSafe=true`. The invocation MAY use the existing bounded actuator-discovery order, but it MUST produce at most one active-video transition and MUST stop every later write as soon as any transition is observed. Pre-input same-video hydration MAY complete entry; completion after a transition SHALL require the bound moved-to `videoKey` and exactly one matching canonical-permalink Reel card. The anonymous landing, a content-derived card, input dispatch, or route arrival MUST NOT count as success or a view.

#### Scenario: First Reel hydrates before input commit

- **WHEN** the initially anonymous active video gains a matching canonical Reel card during the hydration window or fresh pre-commit readback
- **THEN** Edge reports that current canonical card and dispatches no keyboard, wheel, pointer, or second route navigation input

#### Scenario: Identity appears at the initial hydration boundary

- **WHEN** the same active video gains canonical identity as the initial 15-second window closes but its card is not yet reportable
- **THEN** Edge performs one immediate card read, dispatches no input, and does not open a second initial hydration window

#### Scenario: Anonymous horizontal landing advances

- **WHEN** the hydration window expires with one safe anonymous active video, fresh structure proves a horizontal layout, and the bounded invocation changes to a different canonically identified Reel
- **THEN** Edge reports exactly the moved-to canonical card, starts with the existing `ArrowRight` actuator, and dispatches no input after the transition

#### Scenario: Anonymous vertical landing advances

- **WHEN** the hydration window expires with one safe anonymous active video, fresh structure proves a vertical layout, and the bounded invocation changes to a different canonically identified Reel
- **THEN** Edge reports exactly the moved-to canonical card, starts with the existing `ArrowDown` actuator, and dispatches no input after the transition

#### Scenario: Original Reel hydrates after an ineffective actuator

- **WHEN** one entry actuator was dispatched, the active `videoKey` did not change, and that same video's exact canonical Reel card then becomes available
- **THEN** Edge reports the now-canonical current Reel and dispatches no second key, wheel, pointer, or route navigation input

#### Scenario: Anonymous entry target is unavailable

- **WHEN** fresh readback finds no active video, equally eligible videos, `inputSafe=false`, a missing input-safety signal, a blocker, target drift, or no remaining post-input verification budget
- **THEN** Edge dispatches no Reels navigation input and emits no fabricated card or view

#### Scenario: Entry is cancelled around the route boundary

- **WHEN** cancellation is observed immediately before the first `/reels/` route dispatch
- **THEN** Edge dispatches no route and reports `not_started`
- **AND WHEN** cancellation is observed after that route or before a retry route
- **THEN** Edge dispatches no later route or actuator and reports `ambiguous`

#### Scenario: Input leaves the anonymous Reel unchanged

- **WHEN** the one bounded navigation invocation exhausts its permitted methods without changing the active `videoKey`
- **THEN** Edge returns an ambiguous navigation-unconfirmed receipt and does not start a second entry invocation

#### Scenario: Video changes but canonical identity remains pending

- **WHEN** entry input changes the active `videoKey` but no matching canonical Reel card appears within the post-transition hydration window
- **THEN** Edge returns `ambiguous/reels_post_transition_identity_pending`, dispatches no later input, and retains a session-local read-only pending observation

#### Scenario: Later scroll encounters a pending entry transition

- **WHEN** another scroll command arrives while the prior entry transition still awaits canonical identity
- **THEN** Edge performs read-only active-card recovery and dispatches no keyboard, wheel, pointer, or route navigation input
- **AND** it clears the pending observation only after reporting one matching canonical Reel card or leaving the Reels surface

#### Scenario: Pending target drifts a second time

- **WHEN** a pending observation is already bound to one moved-to `videoKey` and either the same hydration window or a later command sees a different active video
- **THEN** Edge reports an ambiguous target-changed receipt, emits no card, and dispatches no input
- **AND** returning to the previously bound `videoKey` later cannot make that drifted observation confirm

#### Scenario: Ordinary Reels transition still awaits identity

- **WHEN** a normal Reels scroll proves one active-video transition but the moved-to video has no matching canonical card within its hydration window
- **THEN** Edge retains the exact moved-to video as a read-only pending observation and a later scroll MUST recover it before attempting another navigation
- **AND** if that video temporarily exposes the previous Reel's canonical ID, Edge MUST NOT report or count it until a distinct canonical Reel ID appears

#### Scenario: Noncanonical Reel card cannot complete entry

- **WHEN** Reels card extraction yields an invalid host or non-Reel URL, anonymous identity, `content_ref`, non-video card, non-ready batch, multiple cards, the previous Reel's stale canonical ID, or a card that does not match the freshly active canonical Reel
- **THEN** Edge does not confirm entry and Cloud receives no Reel view from that batch

### Requirement: Facebook Reels entry allows thirty seconds of document readiness per navigation attempt

For every authorized Facebook Reels entry path, Edge SHALL allow each initial and existing optional retry `Page.navigate` attempt up to 30 seconds to observe an `interactive` or `complete` document on the exact bound page. The 30-second timer SHALL apply separately to each navigation attempt and SHALL remain separate from canonical Reel identity/card hydration. A ready document or route acknowledgement alone MUST NOT count as entry success; success SHALL still require the existing canonical `page.cards{listKind:'reels'}` postcondition. Cancellation, command deadline exhaustion, blocker state, or target/document drift MAY terminate the path earlier and MUST retain their existing fail-closed outcomes.

#### Scenario: Slow Reels landing becomes ready inside thirty seconds

- **WHEN** an authorized Reels entry navigation reaches an `interactive` or `complete` document after the former eight-second boundary but no later than 30 seconds
- **THEN** Edge continues with the existing Reels-surface and canonical-card verification instead of terminating the command at the former readiness boundary
- **AND** it does not count a Reel until canonical card evidence is available

#### Scenario: Optional retry uses the same readiness window

- **WHEN** the existing exact-target foreground recovery authorizes its one optional fresh Reels navigation retry
- **THEN** Edge gives that retry its own bounded 30-second document-readiness window
- **AND** it adds no further navigation retry

#### Scenario: Document remains unready after thirty seconds

- **WHEN** a Reels entry navigation still has no `interactive` or `complete` document at the end of its 30-second window
- **THEN** Edge returns the existing honest failure and does not fabricate route arrival, a Reel card, or a view

#### Scenario: Outer timeout chain remains larger than the entry path

- **WHEN** the two readiness windows and two possible canonical-card hydration windows are combined with explicit probe and receipt margin
- **THEN** the sum remains below the existing 180-second Facebook scroll request, admission, engine, and session ceilings
- **AND** Cloud retains its existing 240-second idle watchdog

