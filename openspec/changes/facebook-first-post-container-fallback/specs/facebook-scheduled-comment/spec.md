## ADDED Requirements

### Requirement: Permalinkless first-post targets remain bound to one live group-post container

For empty-keyword Facebook group comments, Edge SHALL continue to prefer the first eligible post that exposes a canonical same-group permalink. When the first eligible hydrated group-feed post has a uniquely associated comment editor but exposes no canonical permalink, Edge SHALL bind that rendered post container, read its context in place, and return a strict Edge-issued first-post target reference instead of reporting `no_candidates`.

The target reference MUST be deterministic from normalized same-container evidence, MUST NOT be represented as a Facebook permalink or post ID, and MUST NOT be derived from an opaque fragment alone. Context extraction, approval identity, editor focus/fill, pre-commit target recheck, submit, and post-submit acknowledgement SHALL all use the same reference. The reference is valid for actuation only while its original page-local binding and keep-open task lease remain intact.

Canonical-permalink and in-place targets MUST NOT silently fall back to each other after selection. The first-post path MUST NOT switch to keyword search, reselect by document order before submit, or advance to a later post because the selected target is deduped or its binding is lost.

When a uniquely associated comment action must be activated before the editor exists, the page router SHALL return a fresh point target and MUST NOT call DOM `click()` as actuation. Native SHALL dispatch real CDP mouse move/press/release events at most once, then require exactly one eligible editor under the same selected target. Dispatch completion without that editor post-state is not success.

#### Scenario: Visible commentable first post has no canonical permalink
- **WHEN** the group discussion stream hydrates a first eligible post with uniquely bound context and comment editor
- **AND** every rendered story/timestamp link lacks a canonical group-post permalink
- **THEN** Edge returns `note.detail` for that same container with a strict first-post target reference
- **AND** Cloud may compose and approve against that reference without dispatching search or navigating to a fabricated post URL

#### Scenario: Canonical permalink remains the preferred target
- **WHEN** the first eligible group post exposes a canonical same-group permalink
- **THEN** Edge uses the existing permalink detail path
- **AND** it does not replace that canonical identity with an in-place target reference

#### Scenario: Opaque group-root fragment is not promoted to a post identity
- **WHEN** a rendered timestamp link is the group root plus an opaque fragment
- **THEN** Edge does not accept that link as a permalink and does not infer a Facebook post ID from the fragment, text, author, media URL, or feed order
- **AND** any fallback identity remains explicitly typed as an internal first-post target reference

#### Scenario: Context and editor resolve to the same live container
- **WHEN** Cloud returns the approved comment with the Edge-issued first-post target reference
- **THEN** Edge resolves the originally bound container, verifies its normalized evidence is unchanged, and requires exactly one eligible editor inside that boundary before typing
- **AND** it never uses an editor from another post or the document root

#### Scenario: Comment editor requires a trusted pointer activation
- **WHEN** the selected first post has exactly one eligible comment action but no hydrated editor
- **THEN** Edge returns that action's fresh coordinates without invoking DOM `click()`
- **AND** Native dispatches `mouseMoved`, `mousePressed`, and `mouseReleased` through CDP
- **AND** the workflow proceeds only after the same target exposes exactly one eligible editor

#### Scenario: Real click does not hydrate the selected editor
- **WHEN** Native dispatches the bounded pointer activation but the same target does not expose a unique eligible editor
- **THEN** Edge reports an honest non-submit outcome
- **AND** it does not repeat the click, invoke DOM `click()`, or select another post

#### Scenario: Bound container is replaced during approval
- **WHEN** Facebook detaches, recycles, or materially changes the bound post container before submit
- **THEN** Edge reports an honest target-moved or context-mismatch non-submit outcome
- **AND** it does not re-run first-post selection or comment on the new first rendered post

#### Scenario: Duplicate container evidence is ambiguous
- **WHEN** more than one rendered post container produces the same fallback reference or the selected boundary contains multiple peer comment editors
- **THEN** Edge reports an ambiguous target and submits nothing

#### Scenario: In-place acknowledgement remains scoped to the bound post
- **WHEN** Enter is dispatched through an in-place first-post target
- **THEN** server acknowledgement is evaluated only within the bound container using the existing own-account and persistence evidence
- **AND** an optimistic row, editor clearing, or a comment visible under another post does not confirm success

#### Scenario: Cloud rejects opaque references outside first-post selection
- **WHEN** a search candidate, ordinary `openPost`, or unrelated platform flow supplies a non-canonical target reference
- **THEN** Cloud rejects it as an invalid target
- **AND** only the result of the active `first_commentable_group_post` request may introduce the strict first-post reference form

#### Scenario: Deterministic fallback reference preserves dedup
- **WHEN** the same unchanged permalinkless group post is selected on a later run
- **THEN** Edge derives the same first-post target reference from its normalized same-container evidence
- **AND** the existing comment dedup ledger may prevent a repeated comment without pretending the reference is a Facebook post ID
