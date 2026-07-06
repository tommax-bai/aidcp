## Why

After rotating to a new Feishu bot, private-message `/publish` commands can reach cloud, but the generated publish approval card still targets the previously bound default approval group. If that group belongs to a different Feishu tenant or bot installation, Feishu rejects the card send and the draft remains pending without an approval surface.

Manual Feishu commands already have a concrete source conversation. Publish approval should use that source conversation first so private commands get their approval card in the private chat and group commands get it in the triggering group.

## What Changes

- Manual Feishu `/publish` carries the source `chatId` from the incoming command event through the publish scheduler into the generated approval-card send path.
- Publish approval cards for manual Feishu commands are sent to the source conversation when one is available.
- Automatic, scheduled, panel/reference, edge-originated, and other non-command publish flows continue to use the configured default approval group (`bot_chats.default`, falling back to `FEISHU_CHAT_ID` where applicable).
- Existing `/aidcp bind` behavior remains the way to set the default approval group for flows without a source conversation.
- No protocol-v2 message shape changes and no edge changes are intended.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `publish-pipeline`: Manual Feishu-triggered publish approval cards prefer the triggering conversation over the default approval group.

## Impact

- Affected code: `aidcp-cloud/src/feishu/commands.ts`, `src/server.ts`, `src/publish-agent/publish-scheduler.ts`, `src/publish-agent/roles/publish-executor.ts`, and focused tests.
- Runtime impact: ECS `aidcp-cloud.service` must be deployed after validation.
- Data impact: none. Existing pending drafts remain pending; this change only routes future approval-card sends unless a resend tool is added separately.
- Security impact: no secrets are stored or logged. Source `chatId` is runtime routing data only.
