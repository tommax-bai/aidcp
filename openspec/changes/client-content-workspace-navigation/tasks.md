## 1. Cloud customer content boundary

- [x] 1.1 Add account-scoped curated list/detail storage reads with SQL-level creatable filtering, consistent total, limit/offset bounds, and honest null counts.
- [x] 1.2 Add customer-auth curated list/detail routes that recheck `client_env_scope` ownership per request and return a minimum-disclosure DTO.
- [x] 1.3 Add the customer reference-creation route using the server-owned curated snapshot and existing structured delegated-task queue, with stable honest rejection reasons.
- [x] 1.4 Add Cloud storage and customer-auth tests for pagination, DTO disclosure, cross-account isolation, ownership revocation, reference modes, queue receipts, and rejection paths.
  <!-- aidcp-cloud: commit 1daec99 on codex/client-content-workspace-navigation; focused store/client-auth tests 45/45. -->

## 2. Edge authenticated bridge

- [x] 2.1 Add main-process customer API helpers and narrow IPC handlers for curated list, detail, and reference creation using the selected environment.
- [x] 2.2 Expose typed/validated preload methods without exposing customer tokens, arbitrary URLs, or unverified account selectors to the renderer.
- [x] 2.3 Add Edge main/preload tests for request construction, session failure, selected-environment scoping, and honest error propagation.
  <!-- aidcp-edge: renderer receives only named IPC methods; static security tests lock path/method/parameter allowlists and main-owned token/envKey injection. -->

## 3. In-window content workspace

- [x] 3.1 Add the shared content workspace shell and page-stack navigation while preserving titlebar, environment rail, runtime health, close-to-home, and back behavior.
- [x] 3.2 Implement the current-account inspiration library with creatable/all filters, pagination, loading/empty/error states, honest count rendering, and per-account list-state restoration.
- [x] 3.3 Implement inspiration detail and reference-mode confirmation with image availability gating, request busy state, queue receipt, and no false generation/publish success.
- [x] 3.4 Replace the draft preview drawer with a full main-content review page while preserving approve/cancel, non-optimistic image deletion, version CAS, last-image guard, and named failures.
- [x] 3.5 Add stale-response and account-switch invalidation so old list/detail/draft state cannot render under a new account.
- [x] 3.6 Add renderer tests covering navigation restoration, pagination/filtering, reference-mode gating/receipts, draft review safety states, and account switches.
  <!-- aidcp-edge: commit 02268ec on codex/client-content-workspace-navigation; final focused content/companion tests 63/63. -->

## 4. Validation and handoff

- [x] 4.1 Run focused and full Cloud tests plus typecheck; record any unrelated baseline failures without masking them.
  <!-- aidcp-cloud: focused 45/45; npm test exit 0; acceptance 54/54; npm run typecheck pass. No baseline failures observed. -->
- [x] 4.2 Run focused and full Edge tests plus typecheck without invoking Electron packaging; record any unrelated baseline failures without masking them.
  <!-- aidcp-edge: focused 63/63; npm test 1506/1506; acceptance 22/22; npm run typecheck pass; syntax checks pass. No packaging invoked and no baseline failures observed. -->
- [x] 4.3 Run `openspec validate client-content-workspace-navigation --strict`, update this checklist with repo commit SHAs/validation notes, and push only the isolated feature branches without merging or deploying.
  <!-- Strict validation passed. aidcp-cloud 1daec99 and aidcp-edge 02268ec were pushed to codex/client-content-workspace-navigation. The control-repo commit is recorded by this checklist's own history. No default branch merge, deploy, Electron package, or PR was performed. -->
