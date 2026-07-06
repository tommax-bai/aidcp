## 1. Contract

- [x] 1.1 Add OpenSpec deltas for direct source-list return and recoverable Xiaohongshu access-limit modals.
- [x] 1.2 Validate `direct-list-return-navigation` with `openspec validate --strict`.

## 2. Edge Implementation

- [x] 2.1 Record the current source list URL before opening a note so search-origin returns can navigate back to the real search result page.
- [x] 2.2 Change `navigation.back` handling to prefer direct `Page.navigate` to the source list, keeping `action.completed{action:'back', ok:true}` unchanged.
- [x] 2.3 Classify Xiaohongshu `access-modal` / `access-limit-app` note access popups as recoverable non-blocking overlays.
<!-- repo: aidcp-edge; commit: ae63fcd7b68a194f2b7a38650d349b88bb526c1d; deviation: none; deployment: not published, desktop edge release target not requested. -->

## 3. Verification

- [x] 3.1 Update focused edge tests for feed direct return, search direct return, and access-limit overlay classification.
- [x] 3.2 Run focused edge tests and typecheck where relevant.
<!-- validation: aidcp-edge npm test 627 pass, gated e2e skipped; aidcp-edge npm run typecheck pass; aidcp openspec validate direct-list-return-navigation --strict pass. -->
