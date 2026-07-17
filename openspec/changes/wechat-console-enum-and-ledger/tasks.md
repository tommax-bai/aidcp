## 1. Console platform enumeration

- [x] 1.1 Add `wechat_channels` to the customer-environment platform metadata and manual registration options while preserving raw-value fallback.
- [x] 1.2 Add focused tests for the Chinese video-channel label, selectable stable value, and unknown-platform fallback.

<!-- Console worktree: platform display/selector implemented in `ClientUsersPage`; focused `ClientUsersPage.test.tsx` passed 10/10. -->

## 2. Reply audit ledger pagination

- [x] 2.1 Extend the reply-audit API client to pass an optional opaque cursor without parsing it and keep response scope validation.
- [x] 2.2 Add account-scoped audit pagination state, load-more/done/retry UI, eventId deduplication, and abort behavior on account refresh/switch/close.
- [x] 2.3 Make unknown audit action/entity values display their raw wire values without blank labels or crashes.
- [x] 2.4 Add focused component tests for multi-page append, end-of-ledger truth, page failure retry, unknown enums, and stale-account abort isolation.

<!-- Console worktree: `WechatChannelsReplySettings.test.tsx` passed 25/25 with one worker; `npm run typecheck` passed. The pagination tests cover opaque cursor encoding, duplicate eventId suppression, retry without clearing loaded rows, unknown action/entity raw display, and stale-account abort. -->

## 3. Validation and delivery

- [x] 3.1 Run focused Console tests, the full Console suite, typecheck and build; run strict OpenSpec validation and record concise evidence.
- [x] 3.2 Rebase and fast-forward the validated Console and control commits onto their latest default branches, push without overwriting unrelated work, and keep the canonical dirty checkout intact.
- [ ] 3.3 Read deployment instructions, run `scripts/deploy-target dev --check`, publish the integrated Console to `dev`, and verify the static app/health without any real WeChat write.

<!-- Validation before integration: `ClientUsersPage.test.tsx` 10/10; `WechatChannelsReplySettings.test.tsx --maxWorkers=1 --minWorkers=1` 25/25; full Console suite 28 files, 155 passed + 1 skipped; `npm run typecheck` passed; production build transformed 3721 modules and completed with the existing chunk-size warning; `openspec validate wechat-console-enum-and-ledger --strict` passed. -->

<!-- Integration: Console `348d503` fast-forwarded `origin/master`; control `c843571` fast-forwarded `origin/main`. Post-rebase focused Console tests passed 35/35 with typecheck green, and strict OpenSpec validation passed. Canonical control checkout's unrelated dirty/archive work was not staged, switched, stashed, cleaned or overwritten. -->
