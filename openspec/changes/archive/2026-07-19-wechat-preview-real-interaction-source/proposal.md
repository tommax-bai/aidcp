## Why

The reply preview currently starts with empty simulated fields, so `video_title` falls back to “这条内容” even when Cloud already stores the real WeChat Channels source title. Operators need a preview path that can use a real inbound interaction context without creating or mutating a reply job.

## What Changes

- Add a preview-only internal API that lists recent inbound interaction contexts for the selected WeChat Channels account.
- Let the Console select a real interaction and automatically populate the simulated channel, message type, user message, user name, and video title.
- Keep manual simulation available and keep preview side-effect free: no Edge command, sync request, reply job, send attempt, or interaction mutation.
- Preserve account scoping and existing preview grants; full DM text remains additionally gated by `interaction.dm.view_full`.

## Capabilities

### New Capabilities

- `wechat-reply-preview-context`: Defines safe selection and use of stored real inbound context in the reply configuration preview.

### Modified Capabilities

None.

## Impact

- `aidcp-cloud`: interaction internal API and read-only interaction-store projection.
- `aidcp-console`: reply preview API/types, source selection UI, and focused tests.
- No Edge, WebSocket protocol, database migration, risk policy, or send-path change.
