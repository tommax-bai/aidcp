## 1. Contract

- [x] 1.1 Add OpenSpec deltas for direct source-list return and recoverable Xiaohongshu access-limit modals.
- [x] 1.2 Validate `direct-list-return-navigation` with `openspec validate --strict`.

## 2. Edge Implementation

- [x] 2.1 Record the current source list URL before opening a note so search-origin returns can navigate back to the real search result page.
- [x] 2.2 Change `navigation.back` handling to prefer direct `Page.navigate` to the source list, keeping `action.completed{action:'back', ok:true}` unchanged.
- [x] 2.3 Classify Xiaohongshu `access-modal` / `access-limit-app` note access popups as recoverable non-blocking overlays.
<!-- repo: aidcp-edge; commits: ae63fcd7b68a194f2b7a38650d349b88bb526c1d, be72f235cb7a150f7e943dafcf348d3882f047d9; deviation: be72f23 moves jsdom to runtime dependencies so packaged desktop app includes the DOM parser; deployment: local /Applications/AIDCP.app rebuilt and installed on 2026-07-06, backup at /Applications/AIDCP.app.bak.20260706-150312-pre-jsdom-fix, no public desktop release published. -->

## 3. Verification

- [x] 3.1 Update focused edge tests for feed direct return, search direct return, and access-limit overlay classification.
- [x] 3.2 Run focused edge tests and typecheck where relevant.
<!-- validation: aidcp-edge npm test 627 pass, gated e2e skipped; aidcp-edge npm run typecheck pass; aidcp-edge npm run electron:build:mac -- --publish never pass; installed app.asar contains sourceListUrl/access-limit-app/jsdom and dom-provider import check passes; runtime smoke: launchctl job com.aidcp.edge.manual running for 工程师大白, navigation.back returned to feed and continued browsing; aidcp openspec validate direct-list-return-navigation --strict pass. -->
