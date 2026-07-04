## Why

AdsPower profile can reopen with the active tab already on `https://creator.xiaohongshu.com/...` instead of the consumer feed. In that state the creator page is visibly logged in and shows the account nickname in the top-right user block, but startup identity establishment still uses consumer-side self-profile anchors and then tries a click-based "my profile" fallback. On the creator platform that fallback can miss the entry, so the edge exits before handshake:

`登录态读不出稳定账号 id（跳转兜底未能进入我的主页）`

The existing runtime watcher already treats `creator.xiaohongshu.com` non-`/login` pages as logged-in presence. Startup still needs the stable account id, not just presence or nickname, because account id is the multi-tenant primary key. A live read-only CDP probe on the logged-in creator page showed stable id is available in same-origin storage (`USER_INFO_FOR_BIZ.userId`, with redundant `snsWebPublishCurrentUser`, `USER_INFO.user.value.userId`, and `nps-userId`).

## What Changes

- **aidcp-edge startup identity**: when the in-place consumer self-profile scan cannot find an id and the current page is a real creator platform page (`creator.xiaohongshu.com`, path not containing `/login`), read only the creator page's same-origin user storage for a stable id.
- **Honesty guard**: use only shape-valid stable ids, require storage candidates to agree when more than one valid id is present, and keep the existing hard failure when no stable id can be read.
- **Clear login signal**: if startup is on `creator.xiaohongshu.com/login`, fail with an explicit login-page reason instead of trying consumer click fallbacks.
- **No protocol/cloud change**: the handshake still carries the same `accountId` field after identity is established.

## Capabilities

### Modified Capabilities
- `account-identity-resolution`: startup identity establishment may use creator platform login-state storage as another stable-id source when the browser is already on a logged-in creator page.

## Impact

- **aidcp-edge**
  - `src/cdp/self-identity.ts`: creator storage scan + pure derivation helper + startup branch.
  - `test/cdp/self-identity.test.ts`: creator domain, storage success, conflict, login page, and statistics URL cases.
- **Validation**
  - `npm test -- test/cdp/self-identity.test.ts`
  - `npm run typecheck`
  - `openspec validate creator-startup-identity-storage --strict`

