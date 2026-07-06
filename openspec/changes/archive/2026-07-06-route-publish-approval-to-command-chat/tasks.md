## 1. Command Context Plumbing

- [x] 1.1 Extend Feishu command publish action types so `/publish` receives the source conversation `chatId` from `CommandRouter.handle(...)`.
  <!-- aidcp-cloud 8b63fe78ca5c4a95f82bdbfd33d33d3944fce16d: CommandRouter passes context.chatId as PublishCommandOptions.sourceChatId. -->
- [x] 1.2 Extend `PublishScheduler.triggerManual(...)` and internal trigger context to carry an optional manual approval chat target without affecting automatic/scheduled flows.
  <!-- aidcp-cloud 8b63fe78ca5c4a95f82bdbfd33d33d3944fce16d: manualApprovalChatId is only set from manual trigger options; automatic and scheduled triggers omit it. -->

## 2. Approval Card Routing

- [x] 2.1 Update `PublishExecutor` to prefer the manual source chat target for approval cards and fall back to `bot_chats.default` only when absent.
  <!-- aidcp-cloud 8b63fe78ca5c4a95f82bdbfd33d33d3944fce16d: PublishExecutor resolveApprovalCardTarget uses manual_source first, then default_chat. -->
- [x] 2.2 Make approval-card delivery logs and command receipts honest when sending fails; do not claim the card was sent after `sendApprovalCard` rejects.
  <!-- aidcp-cloud 8b63fe78ca5c4a95f82bdbfd33d33d3944fce16d: approvalCard result is returned upward; server warns when pending draft exists but card delivery failed. -->

## 3. Validation

- [x] 3.1 Add focused cloud tests proving private/group command source chat routes the publish approval card to that chat.
  <!-- aidcp-cloud 8b63fe78ca5c4a95f82bdbfd33d33d3944fce16d: feishu command, scheduler, and executor focused tests cover source chat propagation. -->
- [x] 3.2 Add focused cloud tests proving non-command/manual-without-source flows still use the default approval group and send failures are observable.
  <!-- aidcp-cloud 8b63fe78ca5c4a95f82bdbfd33d33d3944fce16d: executor tests cover default_chat fallback and sendApprovalCard rejection surface. -->
- [x] 3.3 Run relevant `aidcp-cloud` validation (`npm test -- --runInBand` subset or equivalent focused tests, plus `npm run typecheck` when touched types require it).
  <!-- validation: focused tsx --test feishu-commands + publish-scheduler + publish-executor passed 69/69; npm run test:acceptance passed 44/44 with gated real-e2e skipped; npm test passed 1371/1371; npm run typecheck passed. -->
- [x] 3.4 Run `openspec validate route-publish-approval-to-command-chat --strict`.
  <!-- validation: openspec validate route-publish-approval-to-command-chat --strict passed before deployment; rerun after task update. -->

## 4. Release

- [x] 4.1 Commit and push the control-repo OpenSpec artifacts and cloud implementation commits.
  <!-- aidcp-cloud 8b63fe78ca5c4a95f82bdbfd33d33d3944fce16d committed, fast-forwarded to master, and pushed origin/master; control OpenSpec artifacts are committed with this tasks update. -->
- [x] 4.2 Deploy cloud to ECS from a committed/default-branch-safe snapshot; restart `aidcp-cloud.service`.
  <!-- deployment: ECS 121.89.85.150 updated 20260706-111410 from aidcp-cloud master 8b63fe78ca5c4a95f82bdbfd33d33d3944fce16d; backups /opt/aidcp/backups/aidcp-cloud-20260706-111410.tgz and /opt/aidcp/backups/aidcp-cloud-env-20260706-111410.env; scoped rsync of 5 runtime src files; aidcp-cloud.service restarted. -->
- [x] 4.3 Healthcheck ECS: service active, `:8787`/panel listening, Feishu WS ready, PostgreSQL `select 1`, and no `isales` impact.
  <!-- health: aidcp-cloud active since 2026-07-06 11:14:51 CST; :8787 and 127.0.0.1:8090 listening; panel /api/health ok; PG select 1 ok; Feishu WSClient onReady; remote code anchors verified; isales-scheduler/isales-api active. -->
- [x] 4.4 Record commit SHA, validation, and deployment notes in this `tasks.md`.
  <!-- notes recorded above. -->
