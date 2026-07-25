## ADDED Requirements

### Requirement: Comment target open confirms the requested canonical Facebook post identity

The Facebook comment path SHALL treat `note.open` as successful only when the hydrated detail derives the same canonical Facebook post identity as the requested target. Equivalent supported permalink forms for one post MUST compare equal. A detail for a different post, a profile/feed article, or an identity-less URL MUST NOT advance composition or create an approval request.

Edge SHALL perform this post-navigation validation inside the existing bounded detail-hydration window and discard transient mismatched details while waiting for the requested target. If the requested identity never appears, Edge SHALL return an honest terminal open failure before Cloud's open-step deadline. Cloud SHALL independently correlate returned detail evidence by canonical identity rather than raw URL equality and SHALL ignore evidence for another target.

#### Scenario: Equivalent permalink forms identify the same opened target

- **WHEN** Cloud requests a post through one supported Facebook permalink form and Edge reports the same post through another supported form
- **THEN** both sides derive the same canonical post identity
- **AND** the comment path may advance to composition and configured approval

#### Scenario: Stale article is discarded while requested detail hydrates

- **WHEN** the first detail sampled after navigation belongs to another post and the requested post appears within the bounded hydration window
- **THEN** Edge does not emit the stale detail as successful target evidence
- **AND** it returns the requested post detail once its identity is confirmed

#### Scenario: Requested target never hydrates

- **WHEN** only mismatched or identity-less detail is observable throughout the bounded hydration window
- **THEN** Edge reports an explicit open failure before Cloud's deadline
- **AND** Cloud records a non-submit outcome without composing a comment or creating an approval card

#### Scenario: Cloud rejects mismatched detail evidence

- **WHEN** Cloud receives detail evidence whose canonical Facebook post identity differs from the requested target
- **THEN** it does not accept the open step or advance the task
- **AND** it MUST NOT reinterpret timeout or mismatch as success
