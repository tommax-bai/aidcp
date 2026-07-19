# Change: Promote WeChat comment reply to capture-backed write

## Why

The development comment-reply path currently serializes a first-party-bundle candidate shape. A single operator-approved manual reply from the active `tom白` development session was platform-confirmed, and the sanitized observation shows that the accepted request includes a generated `clientId`, the complete bounded target-comment snapshot, and the interaction-comment referer. The existing Edge request omitted those fields and was explicitly rejected by the platform.

## What Changes

- Promote only the WeChat Channels comment-create descriptor from bundle candidate to sanitized, capture-backed evidence.
- Preserve the bounded target-comment fields required by the accepted request in account-local Edge state during comment sync; do not add them to the Cloud protocol or persist arbitrary raw platform objects.
- Require that local context before dispatch, generate a fresh client ID, serialize the observed request shape, and confirm success only from the observed platform acknowledgement.
- Keep comment writes non-retry-safe and preserve existing claimed/executing/completed and ambiguous-result rules.
- Leave the uncaptured direct-message descriptor and production capability/write-probe gates unchanged.

## Impact

- Affected specification: `wechat-channels-real-runtime`
- Affected repository: `aidcp-edge`
- Affected modules: WeChat request descriptors, comment parsing/local state, API client, reply sender, and their fixtures/tests
- No Cloud protocol, database, Console, online deployment, installer, or automatic real-send change
