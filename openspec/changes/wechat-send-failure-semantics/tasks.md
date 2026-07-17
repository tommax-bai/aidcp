## 1. Edge sending semantics

- [x] 1.1 Update `WechatReplySender` so a trustworthy `requestDispatched=false` is a definitive failed result before category-based platform rejection handling, while unknown or post-dispatch uncertainty keeps bounded verify/ambiguous behavior.
- [x] 1.2 Add focused Edge regression tests proving pre-dispatch schema/local failure returns failed with zero history lookup, and the same post-dispatch uncertainty still verifies and remains confirmed/ambiguous without another platform write.
- [x] 1.3 Preserve existing platform explicit-rejection, durable result, restart/reconcile, exact-ack and no-blind-resend behavior; make no WS payload, message-count or database change.

<!-- Edge implementation: `WechatReplySender.isDefinitiveFailure` now treats trustworthy pre-dispatch evidence as definitive before category checks. `test/wechat-channels/reply-sender.test.ts` adds the pre/post-dispatch `schema_changed` split; focused suite passed 15/15, including durable result outbox, exact ack, restart/reconcile and no-blind-resend coverage. No protocol, payload, message-count or database file changed. -->

## 2. Validation and closeout

- [x] 2.1 Run the focused WeChat reply/API tests and relevant interaction contract tests.
- [x] 2.2 Run Edge acceptance, full tests and typecheck; do not build or publish an installer.
- [x] 2.3 Run `openspec validate wechat-send-failure-semantics --strict`, review scoped diffs/status, and record repo commit/test/deployment plus honest real-write boundaries in this task file.

<!-- Focused validation: `tsx --test test/wechat-channels/reply-sender.test.ts test/wechat-channels/api-client.test.ts test/wechat-channels/contract-and-flags.test.ts test/acceptance/protocol-contract.test.ts` passed 51/51; protocol message count remains 91. -->

<!-- Full Edge validation: acceptance exited 0, full `tsx --test test/**/*.test.ts` exited 0, and `npm run typecheck` exited 0. Dot reporters bounded retained output; no `build:dist`, Electron installer build or publish ran. -->

<!-- Closeout: aidcp-edge commit `6afa18f` contains the complete implementation. Scoped diff is exactly `src/wechat-channels/reply-sender.ts` plus `test/wechat-channels/reply-sender.test.ts`; `openspec validate wechat-send-failure-semantics --strict` passed. No Cloud/Console code, WS payload, database migration, ECS deploy, real-account write, Edge installer build or client publication was performed. The existing true-write acceptance backlog remains open. -->
