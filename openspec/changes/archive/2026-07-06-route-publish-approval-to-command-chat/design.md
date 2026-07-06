## Context

Manual Feishu `/publish` currently enters `FeishuWsReceiver.handleMessage()`, passes `message.chat_id` only to `CommandRouter.handle()`, and then calls `CommandActions.publish(nickname)` without preserving that source conversation. `PublishScheduler.triggerManual()` and `PublishExecutor.trySendApprovalCard()` therefore have no per-command destination and fall back to `bot_chats.default`.

That fallback is still required for automatic/scheduled publishes, but it is the wrong first choice for a publish explicitly requested from a Feishu private chat or group chat. A bot rotation can also make an old default group unreachable, causing `sendApprovalCard()` to fail with Feishu HTTP 400 while the draft remains pending.

## Goals / Non-Goals

**Goals:**

- Route manual Feishu `/publish` approval cards to the triggering Feishu conversation when a source `chatId` is present.
- Preserve default group routing for publish flows that do not have a source conversation.
- Keep fast-ack behavior: message-event handling must still return immediately while command work and result cards run in the background.
- Make logs and command receipts honest when approval-card delivery fails.

**Non-Goals:**

- No protocol v2 change and no edge change.
- No automatic migration of old `FEISHU_CHAT_ID` or existing `bot_chats` rows.
- No resend UI/tool for already pending drafts in this change.
- No change to `/aidcp bind`; it remains the way to set the default approval group.

## Decisions

1. Add a command execution context for source `chatId`.

   `CommandRouter.handle(text, { chatId })` already receives the incoming conversation. Extend the action interface so `publish` can receive `{ sourceChatId }`. This keeps routing attached to the Feishu command execution path instead of reading global mutable state.

   Alternative considered: store a "last command chat" singleton and let `PublishExecutor` read it. Rejected because concurrent commands from different chats would race and can route cards to the wrong conversation.

2. Carry source chat through scheduler input, not through publish content.

   Add a `manualApprovalChatId` option to `PublishScheduler.triggerManual()` / internal trigger context and pass it to the publish pipeline context. `PublishExecutor` then prefers this value over `bot_chats.default`.

   Alternative considered: make `PublishExecutor` query Feishu command state or `CommandRouter` directly. Rejected because publish roles should remain independent of Feishu command parsing.

3. Preserve fallback only when no source chat exists.

   Manual Feishu commands with a source chat SHALL use that chat first. Scheduled, automatic, panel/reference, mock, and edge-originated flows have no source chat and continue to use the existing default group behavior.

   Alternative considered: always use command chat for every publish trigger. Rejected because non-Feishu triggers have no user-visible source conversation.

4. Return/log card-send truthfully.

   `PublishExecutor.trySendApprovalCard()` should return whether a card was sent and where it attempted to send. The pending-draft log/receipt must not claim "already sent" if `sendApprovalCard()` failed. The draft can still remain `pending_approval` because the approval surface may be provided by console or a later resend, but the send failure must be visible.

## Risks / Trade-offs

- Source chat may be a private chat where the bot can receive events but lacks message/card send permission -> `sendApprovalCard()` fails and is logged. Mitigation: keep honest failure logging and command receipt wording; permission is an app configuration issue.
- A private manual command bypasses the default approval group as an audit channel. Mitigation: this only affects manual commands whose requester is already interacting with the bot; automatic and scheduled flows still go to the default group.
- Existing pending drafts whose cards failed are not automatically repaired. Mitigation: explicitly out of scope; operators can approve via console or rerun/resend separately.
