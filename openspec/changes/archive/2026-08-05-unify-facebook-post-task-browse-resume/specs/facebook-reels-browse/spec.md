## MODIFIED Requirements

### Requirement: Reels re-entry MUST NOT require a non-empty ordinary feed as its only unlock

An account whose ordinary home feed produces nothing SHALL still be able to be re-authorized onto the Reels surface. Re-authorization MUST NOT depend solely on a non-empty ordinary feed returning, because an account is on Reels precisely when its ordinary feed produced nothing — that unlock can never fire for the accounts that need it.

Cloud MUST NOT use a long-lived `confirmed` flag as evidence of the current page. It SHALL retain only a bounded in-flight Reels redrive attempt and per-session recovery count. Edge SHALL probe the live page for every `page.scroll{reason:'resume_redrive',targetSurface:'reels'}` and either report the canonical Reel already active or enter Reels through the verified entry path.

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

When a Facebook session pins Reels as its primary surface, Cloud SHALL authorize active browsing with `page.scroll{reason:'resume_redrive',targetSurface:'reels'}` and Edge SHALL reconcile the current live surface to the existing Reels executor. Route navigation alone MUST NOT count as entry success; browsing SHALL begin only after Edge reports a canonical active Reel through `page.cards{listKind:'reels'}`. Cloud MUST NOT persist that success as a claim about the page after later task navigation.

#### Scenario: Configured primary reaches a reportable Reel

- **WHEN** Cloud sends the unified Reels redrive and Edge verifies one canonical active Reel
- **THEN** Edge reports that Reel through the existing Reels card contract
- **AND** the current persona, slow-start, rule, or consumption path continues without a parallel executor

#### Scenario: Reels route has no reportable card

- **WHEN** navigation reaches a Reels route but no canonical active Reel can yet be reported
- **THEN** Edge returns the existing honest pending or no-target result
- **AND** neither Edge nor Cloud fabricates a Reel view or starts content evaluation

#### Scenario: Group task invalidates prior page truth

- **WHEN** a group/comment task navigates away after a Reel was previously reported
- **THEN** a past Reel report does not suppress the final post-task unified redrive
