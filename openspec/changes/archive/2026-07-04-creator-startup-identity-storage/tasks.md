# Tasks - creator-startup-identity-storage

> Pure aidcp-edge startup identity hardening. Protocol, cloud, and console are unchanged. Record validation and commit SHA before archive.

## 1. aidcp-edge - Creator Startup Identity

- [x] 1.1 Add a pure creator storage derivation helper that accepts only shape-valid stable ids from known creator storage keys and rejects conflicting valid candidates. <!-- aidcp-edge 7328d56fc3a0e7ca9a5657c1a206c1a7835233d4: deriveCreatorStorageIdentity() reads only USER_INFO_FOR_BIZ.userId + redundant known id keys and rejects conflicts -->
- [x] 1.2 Update `readSelfIdentity()` so a logged-in creator page can establish identity from creator same-origin storage before click-based navigation fallback. <!-- aidcp-edge 7328d56fc3a0e7ca9a5657c1a206c1a7835233d4: creator-app branch returns source=creator-storage before click fallback -->
- [x] 1.3 Short-circuit creator `/login` with an explicit honest failure reason. <!-- aidcp-edge 7328d56fc3a0e7ca9a5657c1a206c1a7835233d4: creator-login returns 当前停在创作平台登录页，登录态已失效 -->
- [x] 1.4 Preserve the existing red lines: nickname is display-only, no guessing, no `default` fallback, no use of malformed ids. <!-- aidcp-edge 7328d56fc3a0e7ca9a5657c1a206c1a7835233d4: malformed/missing/conflicting storage ids fail; nickname/redId never become accountId -->

## 2. Tests

- [x] 2.1 Extend `classifyPageContext` coverage for `creator.xiaohongshu.com/statistics/account/v2`. <!-- aidcp-edge 7328d56fc3a0e7ca9a5657c1a206c1a7835233d4 -->
- [x] 2.2 Add unit coverage for creator storage success, malformed storage, conflicting ids, and creator login page failure. <!-- aidcp-edge 7328d56fc3a0e7ca9a5657c1a206c1a7835233d4: self-identity.test.ts now 21 focused cases -->
- [x] 2.3 Run focused edge tests and typecheck. <!-- focused: .\node_modules\.bin\tsx.cmd --test test/cdp/self-identity.test.ts = 21 pass; npm run typecheck = pass; npm test = 607 pass -->

## 3. OpenSpec

- [x] 3.1 Validate the change with `openspec validate creator-startup-identity-storage --strict`. <!-- strict pass -->
- [x] 3.2 Record implementation commit SHA and validation notes. <!-- edge commit 7328d56fc3a0e7ca9a5657c1a206c1a7835233d4; live read-only AdsPower CDP probe on creator tab returned source=creator-storage for accountId 63e2ff0500000000260049ce / displayName 工程师大白 / redId 5039527968 -->
