## Why

Facebook 的页面结构、登录态、checkpoint 封控、评论框受控模型和 AdsPower 指纹表现都不能靠小红书经验推断。若没有真机探针先证明登录、身份、页面结构、封控探测和发布校验可行，后续无人审定时评论会把失败误报成成功或把死号反复派活。

## What Changes

- Add Facebook browser environment support behind the platform abstraction from `platform-abstraction-layer`.
- Add Facebook read-only and gated probes for login state, storage summary, page/post structure, comment editor behavior, checkpoint/login URL detection, and AdsPower/CDP fingerprint sanity.
- Add a client-side, one-time Facebook account import path for AdsPower environment creation. The import may pass username/password/2FA key/cookie to AdsPower `user/create`, but aidcp MUST NOT persist those secrets in settings, logs, docs, or local ledgers.
- Implement the Facebook driver identity and overlay/checkpoint detection minimum (`readIdentity`, `detectOverlay`) only after probe evidence confirms the shape.
- Record Phase-0 kill gates: true server-confirmed comment verification feasibility, URL-based checkpoint/login detection, and multi-day AdsPower profile stability.
- Do not implement scheduled commenting or automatic posting in this change.

## Capabilities

### New Capabilities

- `facebook-browser-environment`: Defines Facebook profile startup, login/session probing, storage-safe diagnostics, page structure probes, and Phase-0 gates.

### Modified Capabilities

- `pluggable-browser-provider`: Browser provider startup and tab selection become platform-aware while preserving AdsPower/self provider boundaries.
- `captcha-incident-handling`: Overlay detection adds URL/location-based checkpoint and login-wall classification for Facebook.
- `account-identity-resolution`: Identity reading gains a Facebook implementation that must return a stable platform account id or fail honestly.

## Impact

- Affected repos: `aidcp-edge`, possibly `aidcp-cloud` for platform/account validation and probe reporting.
- Edge areas: Facebook driver skeleton, AdsPower start URL/tab target selection, storage-safe probe scripts, overlay monitor hooks, identity reader.
- Desktop companion areas: AdsPower environment creation UI and Local API profile-create payload construction.
- Cloud areas: optional probe result logging, platform mismatch rejection already introduced by Change 0.
- Security: probes must never print or persist raw cookies, tokens, localStorage values, sessionStorage values, IndexedDB payloads, or credentials.
- Validation gate: Phase-0 must pass before `facebook-scheduled-comment` starts.
