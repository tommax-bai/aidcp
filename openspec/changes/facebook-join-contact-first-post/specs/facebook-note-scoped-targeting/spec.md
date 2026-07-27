## ADDED Requirements

### Requirement: Facebook comment context is read from the same canonical target article

After a Facebook comment target permalink is opened, Edge SHALL derive the requested canonical post ID and resolve exactly one target card through the same scoped identity helper used by comment-editor and verification targeting. The post caption, bounded nested-comment sample, and editor readiness MUST be read from that resolved target and its exclusive region only. Background feed cards, an earlier dialog, nested comment articles, or DOM-order first articles MUST NOT contribute composition context.

If the requested target resolves to zero or multiple cards, or content extraction cannot remain bound to the requested identity, Edge MUST return `target_context_mismatch` (or an equivalently explicit non-success) and MUST NOT emit `note.detail`, request approval, focus an editor, or submit.

#### Scenario: Dialog target ignores the background feed's first post
- **WHEN** the requested post is open in a detail dialog while a different background feed post appears earlier in document order
- **THEN** the emitted caption and sampled comments come only from the requested dialog post
- **AND** the background feed post contributes no generation context

#### Scenario: Ambiguous target does not create an approval request
- **WHEN** two same-scope cards resolve to the requested canonical post ID or no card resolves to it
- **THEN** Edge reports an explicit target-context non-success and Cloud does not compose or create an approval request

#### Scenario: Read root and write root remain identical
- **WHEN** a Facebook comment proceeds from target reading through editor lookup and submission
- **THEN** caption/comments, editor, and post-submit verification are all scoped by the same canonical post identity

#### Scenario: Portal editor is uniquely covered by the canonical target card
- **WHEN** Facebook renders the post-level comment editor outside the target card DOM subtree
- **AND** the editor's rendered center is covered by exactly one physical post card whose canonical identity is the requested target
- **THEN** Edge MAY bind that unique editor to the target
- **AND** any overlap with another card, multiple candidate editors, or missing canonical target MUST return an explicit non-success without submitting
