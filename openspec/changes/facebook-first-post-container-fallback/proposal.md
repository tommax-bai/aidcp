## Why

DEV real-account probes show that Facebook can render a hydrated group-feed post with its own comment editor while exposing no canonical post permalink in DOM links or element metadata. The current empty-keyword first-post path treats the permalink as mandatory, so it reports `no_candidates` even though the first post is visible and commentable.

A packaged DEV follow-up exposed a second failure: some posts expose a uniquely scoped comment action before the editor is hydrated. Calling DOM `element.click()` did not reliably open the editor, and the Native runtime later returned `editor_not_found`. A successful JavaScript method call is not browser input evidence.

## What Changes

- Keep canonical permalink targeting as the preferred first-post path when Facebook exposes one.
- When the first hydrated group post has a uniquely bound comment editor but no canonical permalink, read its context and comment in place through a stable same-container handle.
- Bind context extraction, editor selection, submit, and post-submit verification to the same rendered post container; fail honestly if that boundary is missing, duplicated, or changes before submit.
- Do not synthesize a post ID or permalink from opaque fragments, text, feed order, author identity, or media URLs.
- Preserve keyword-search targeting, existing approval/risk gates, bounded scroll-and-settle behavior, and the rule that first-post mode never substitutes a later post.
- Distinguish “no hydrated post,” “post container not uniquely bindable,” and “comment editor unavailable” from permalink absence; permalink absence alone is no longer a no-candidate outcome.
- Return the uniquely scoped comment action as coordinates, actuate it through Native CDP mouse events, and accept it only when the same target subsequently exposes exactly one eligible editor.
- Record the cross-platform rule that DOM `click()` is not proof for controls that advance a workflow or gate a platform write.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `facebook-scheduled-comment`: Make canonical permalink optional for empty-keyword first-post targeting when Edge can bind the visible post, its context, editor, and verification evidence to one unique group-feed container.

## Impact

- Control: OpenSpec delta and protocol documentation for the first-post target reference.
- Edge: Native Facebook `note.open` first-post selection/read path, real CDP editor activation, comment targeting state, in-place submit verification, and focused tests.
- Cloud: first-post result correlation, approval/dedup target plumbing, and focused scheduler/edge-step tests.
- Protocol: no new command or event type; `note.detail.noteId` and `interaction.comment.noteId` accept a strictly formatted, Edge-issued first-post target reference only for this keep-open flow.
- No database migration, installer build, OL deployment, or real-account write is included in this source change.
