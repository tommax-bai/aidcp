# Design: Capture-backed WeChat comment reply

## Evidence and boundary

At 2026-07-19 13:11:30 +08, an operator manually sent one reply from the current authorized WeChat Channels page while Edge observed CDP network events. The platform returned HTTP 201, `errCode=0`, and a non-empty `data.comment.commentId`; the reply was then visible on the platform. The sanitized evidence fixes the method, path, query/header names, body keys and value types, referer class, acknowledgement shape, and non-retry-safe classification without retaining cookies, tokens, finder IDs, comment IDs, profile data, or message content.

The earlier programmatic request used the same endpoint and target-ID relationship but omitted `clientId` and the `comment` target snapshot. It received a platform rejection. The implementation therefore adopts the complete observed shape as one unit instead of guessing which omitted field is independently sufficient.

## Local write context

The comment reader already receives the target object required by comment-create. Parsing will copy only the explicitly observed fields into a bounded `WechatCommentWriteContext`. `levelTwoComment` is normalized to an empty array so a reply never embeds an unbounded reply tree. The context is stored only in the account/environment-scoped, owner-restricted Edge runtime state and keyed by the inbound platform comment ID. It is not projected into Cloud messages or `rawMetaSanitized`.

When Cloud later dispatches an approved reply, Edge resolves the context by `inboundMessageExternalId`. A normal comment sync refreshes the local context. For comments synchronized by an older build, Edge may perform a bounded read-only comment lookup before entering the durable executing/write-dispatch state. If no complete target context is found, the reply fails before comment-create `fetch`; Edge does not reconstruct a partial target from Cloud data and does not dispatch a speculative write shape.

## Request and acknowledgement

For `commentCreate`, Edge generates a new UUID `clientId` and serializes the captured keys: reply/root IDs, content, client ID, bounded comment snapshot, export ID, and the existing common interaction fields. The descriptor uses the interaction comment page referer and is marked capture-backed while retaining `retrySafe=false`.

HTTP success alone is insufficient. Confirmation continues to require a successful platform status and a non-empty `data.comment.commentId`. The captured HTTP 201 response is accepted by the existing `response.ok` transport rule. Platform rejection remains failed; loss of a response after dispatch remains ambiguous and is never blindly retried.

## Non-goals

- No second real send is performed as part of implementation or automated verification.
- No direct-message descriptor is promoted; it remains a dev-only bundle candidate.
- No new production write capability or write-probe bypass is introduced.
- Nested-reply target semantics beyond the captured top-level-reply shape are not generalized without separate capture evidence.
