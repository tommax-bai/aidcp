## 1. Edge sending semantics

- [x] 1.1 Update `WechatChannelsApiClient` to preserve pre-dispatch evidence and promote response-parser failures to dispatched, then make `WechatReplySender` treat a trustworthy `requestDispatched=false` as definitive before category checks while post-dispatch uncertainty keeps bounded verify/ambiguous behavior.
- [x] 1.2 Add focused Edge regression tests proving pre-dispatch schema/local failure returns failed with zero history lookup, and the same post-dispatch uncertainty still verifies and remains confirmed/ambiguous without another platform write.
- [x] 1.3 Preserve existing platform explicit-rejection, durable result, restart/reconcile, exact-ack and no-blind-resend behavior; make no WS payload, message-count or database change.

<!-- Edge implementation: `WechatChannelsApiClient` now separates request errors from response parsing, promotes parser errors to dispatched evidence, and starts the timeout only after request serialization; `WechatReplySender.isDefinitiveFailure` treats trustworthy pre-dispatch evidence as definitive before category checks. API/reply tests cover the pre/post-dispatch `schema_changed` split, including fetch=0 for the unobserved write endpoint, plus durable result outbox, exact ack, restart/reconcile and no-blind-resend. No protocol, payload, message-count or database file changed. -->

## 2. Validation and closeout

- [x] 2.1 Run the focused WeChat reply/API tests and relevant interaction contract tests.
- [x] 2.2 Run Edge acceptance, full tests and typecheck; do not build or publish an installer.
- [x] 2.3 Run `openspec validate wechat-send-failure-semantics --strict`, review scoped diffs/status, and record repo commit/test/deployment plus honest real-write boundaries in this task file.

<!-- Focused validation: `tsx --test test/wechat-channels/reply-sender.test.ts test/wechat-channels/api-client.test.ts test/wechat-channels/contract-and-flags.test.ts test/acceptance/protocol-contract.test.ts` passed 51/51; protocol message count remains 91. -->

<!-- Final Edge validation after the parser-evidence follow-up: full `tsx --test test/**/*.test.ts` exited 0 before the final conflict-free rebase; after rebasing onto Edge `eb1f077`, the focused contract/API/reply suite passed 52/52 with protocol message count 91, acceptance exited 0, and `npm run typecheck` exited 0. Dot reporters bounded retained output; no `build:dist`, Electron installer build or publish ran. -->

<!-- Closeout: aidcp-edge commits `6afa18f` and `29ef51b` contain the complete implementation after rebasing the parser-evidence follow-up onto current `origin/master` (`eb1f077`). Scoped code diff is exactly `src/wechat-channels/api-client.ts`, `src/wechat-channels/reply-sender.ts` and their two focused test files; `openspec validate wechat-send-failure-semantics --strict` passed. No Cloud/Console code, WS payload, database migration, ECS deploy, real-account write, Edge installer build or client publication was performed. The existing true-write acceptance backlog remains open. -->
