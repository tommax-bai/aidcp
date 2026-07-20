## 1. Batch Close Control

- [x] 1.1 Add the filtered “全部关闭” control and renderer pending / receipt behavior.
- [x] 1.2 Add preload and main-process `fleet:closeAll` routing that scopes envIds against live handles and reuses single-environment close semantics.
- [x] 1.3 Add renderer and main-process regression coverage for filtered batch close, stale targets, and non-completion receipts.

## 2. Browser Window Feedback and Reopen

- [x] 2.1 Remove successful foreground / parking explanatory messages from every client surface while preserving failure feedback.
- [x] 2.2 Make closed-task browser open immediately project a pending state and finish bootstrap / wake asynchronously with cancellation guards.
- [x] 2.3 Add regression coverage for quiet foreground success and responsive closed-task browser reopen.

## 3. Validation and Delivery

- [x] 3.1 Run focused Electron fleet / lifecycle tests and fix any regressions.
  <!-- Edge focused renderer / lifecycle / slot / bootstrap coverage: 107/107 passed after the final stopped-intent correction. -->
- [x] 3.2 Run the Edge acceptance suite, full tests, typecheck, and OpenSpec strict validation.
  <!-- Edge acceptance 27/27 passed (real-machine E2E remained gated), full suite 2056/2056 passed, `npm run typecheck` passed, and `openspec validate client-environment-browser-controls --strict` passed. No installer was built. -->
- [x] 3.3 Record validation evidence and commits in this checklist, commit / push control and Edge branches, then integrate the eligible default branches without building an installer.
  <!-- Edge commit 4a0adc6 was pushed on `codex/client-environment-browser-controls`, fast-forwarded to `origin/master`, and synced to the clean canonical checkout. Control artifact commit fa93a6b was pushed on the matching branch, fast-forwarded to `origin/main`, and synced without touching unrelated canonical `output/` or `tmp/` files. This checklist completion is the final control-only follow-up. No installer was built or published. -->
