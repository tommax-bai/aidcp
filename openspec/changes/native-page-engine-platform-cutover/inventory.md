# Production browser-intelligence inventory

## Baseline

- Control: `095efc0312301819de1acb26866401ddcb27ae9b` on `codex/native-page-engine-platform-cutover`.
- Edge: `2b2d9dd4a439b6e72798b1755ec8e9b6083e11aa` on `codex/native-page-engine-platform-cutover`.
- Edge dependencies: physical worktree-local `node_modules`, installed with `npm ci --prefer-offline`.
- `npm run build:dist`: 109 reachable JavaScript files, 31 unreachable files removed, migrated XHS modules absent, source maps absent.
- Package inputs are `dist/**/*`, Electron CJS/renderer files, `package.json`, and declared `extraResources`; repository `scripts/` and `test/manual/` are not direct inputs.

## Facebook production reachability

`src/main.ts` imports `src/facebook/index.ts`; its wildcard exports make every listed Facebook module production-reachable. All 27 compiled modules below remain under `dist/facebook` at baseline.

### Migrate page intelligence to Native

- Readers and page state: `feed-reader`, `reels-reader`, `inline-reader`, `post-reader`, `identity`, `post-identity`, `cta-labels`, `viewport-scroll`.
- Actions and verification: `like-executor`, `comment-executor`, `join-executor`, `publish-executor`, `consent`, `overlay`.
- Production probes: `probes/editor-probe`, `probes/fingerprint`, `probes/gated-submit`, `probes/page-structure`, `probes/post-composer-probe`, `probes/post-media-probe`, `probes/storage-summary`.
- Mixed orchestration/page access: `facebook-session` currently owns Cloud command sequencing and pacing but also directly reloads/navigates pages; retain selector-free orchestration and move direct page access to Native.

Baseline migrated modules contain `Runtime.evaluate`, `Page.navigate`/reload, `Input.dispatchMouseEvent`/key events, DOM selectors, localization rules, page identity normalization, bounded local recovery, and post-action checks. These are the recoverable core.

### Retain as selector-free TypeScript

- `driver`: platform declaration/start URL/capability assembly, changed only to require Native compatibility.
- `comment-handler` and `join-handler`: Cloud envelope translation and receipt routing, after their executors become Native facades.
- `companion-ui`: user-visible progress/overlay presentation contract, after page-overlay actuation is removed.
- `facebook-session`: Cloud command queue, pacing, ownership, seen-card state, and activity reporting only; all page reads/writes move behind the facade.
- `index`: explicit production exports only; no wildcard probe export.

### Facebook semantic command families

- Session/page: probe, identity, consent, overlay, navigate, reload, surface, scroll metrics/movement.
- Read: feed settle/scan/home state, Reels enter/active/next, inline post, detail post, permalink/identity normalization.
- Interaction: like/follow target/dispatch/verify, comment editor/fill/submit/verify, comment-like.
- Group: group identity, membership, join questions/consent, join dispatch/verification.
- Publish: composer entry, media selection/upload, editor fill, audience/options/schedule, submit, link capture/reconciliation.

## WeChat Channels production reachability

All normal API/auth/runtime modules are production-reachable. Only `browser-sidecar` performs browser inspection:

- Native migration: target attach, `Network.enable`, request-event filtering for exact `channels.weixin.qq.com/.../auth/auth_data`, reload, matching cookie read, and user-agent read.
- Retain TypeScript: provider launch/kill, transient lease ownership, candidate identity validation, encrypted persistence, API clients/descriptors, capability probes, sync/reply state, circuit breakers, and Cloud runtime.
- `probes/black-box-probe` is an API capability probe, not DOM/page understanding, so it remains TypeScript.

The Native result stays limited to the current `WechatSessionMaterial` candidate shape; arbitrary requests/storage/DOM are forbidden.

## Development-only exclusions

Repository probes under `scripts/*probe*`, `scripts/capture-wechat-request-shapes.mjs`, and `test/manual/facebook-phase0-probe.ts` are calibration/diagnostic tools. They remain source-only and must be denied by final-package inspection even though current `build.files` does not include those directories.

## Stable leakage markers

Path checks cover all migrated executor/reader/probe modules above. Representative semantic markers include:

- Facebook targeting tags: `data-aidcp-target`, `data-aidcp-inline`.
- Facebook page selectors/local rules: `multi_permalinks`, `contenteditable="true"][role="textbox"]`, `fbFeedTopCards`, `WRITE_PROBE_GATED`.
- Direct page APIs outside Native: `Runtime.evaluate`, `Input.dispatchMouseEvent`, `Page.navigate`, `Network.getAllCookies`.
- Development probe paths/names: `scripts/*probe*`, `facebook-phase0-probe`, `capture-wechat-request-shapes`.

Markers are checked together with denied paths and positive Native smoke tests; no single minification-sensitive string is treated as sufficient proof.
