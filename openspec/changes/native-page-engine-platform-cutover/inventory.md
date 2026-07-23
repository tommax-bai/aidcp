# Production browser-intelligence inventory

## Baseline

- Control: `095efc0312301819de1acb26866401ddcb27ae9b` on `codex/native-page-engine-platform-cutover`.
- Edge: `2b2d9dd4a439b6e72798b1755ec8e9b6083e11aa` on `codex/native-page-engine-platform-cutover`.
- Edge dependencies: physical worktree-local `node_modules`, installed with `npm ci --prefer-offline`.
- `npm run build:dist`: 109 reachable JavaScript files, 31 unreachable files removed, migrated XHS modules absent, source maps absent.
- Package inputs are `dist/**/*`, Electron CJS/renderer files, `package.json`, and declared `extraResources`; repository `scripts/` and `test/manual/` are not direct inputs.

## Facebook production reachability

`src/main.ts` imports `src/facebook/index.ts`; its wildcard exports make every listed Facebook module production-reachable. All 27 compiled modules below remain under `dist/facebook` at baseline.

### Migrate runtime page intelligence to Native

- Readers and page state: `feed-reader`, `reels-reader`, `inline-reader`, `post-reader`, `identity`, `post-identity`, `cta-labels`, `viewport-scroll`.
- Actions and verification: `like-executor`, `comment-executor`, `join-executor`, `publish-executor`, `consent`, `overlay`.
- Runtime semantic probes: editor state, page structure, post composer/media state, consent/overlay state, and submit postconditions migrate into the fixed Native router.
- Calibration-only probes: `probes/fingerprint`, `probes/gated-submit`, and `probes/storage-summary` do not become runtime commands; they are removed from the production export graph and remain source/test diagnostics only.
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

The cutover also makes the standalone Facebook `probes/*` modules production-unreachable. Their runtime-relevant semantics are implemented inside the Native adapter; fingerprint, storage-summary, and gated-submit calibration surfaces are not exposed as Native production commands.

## Cutover build evidence

- Edge implementation and integration: `4f04e9c10aa4c6dd94639c593d886689fbec2c85` on `master`, pushed without force.
- Native manifest: protocol v2, `multi-platform-v1`, adapters `xiaohongshu-v1`, `facebook-v1`, and `wechat-channels-v1`; capability digest `8ec2b0281599d863e250398c598d41ac8ed233e57764fa61513abb898fc8a8a3`.
- Local release artifact: unsigned `darwin-arm64`, SHA-256 `c96ffb160ed914553bf9a61e111719055a5fb26bd04106dd78ce601d93b569e3`.
- Production build: 77 reachable JavaScript files, 64 removed, only `dist/facebook/driver.js` remains under `dist/facebook`; legacy page-rule markers and source maps are absent.
- Release boundary: no installer was built or released, so final signed ASAR/resource inspection, packaged startup smoke, and disposable-account Facebook/WeChat acceptance remain later release gates.

## Stable leakage markers

Path checks cover all migrated executor/reader/probe modules above. Representative semantic markers include:

- Facebook targeting tags: `data-aidcp-target`, `data-aidcp-inline`.
- Facebook page selectors/local rules: `multi_permalinks`, `contenteditable="true"][role="textbox"]`, `fbFeedTopCards`, `WRITE_PROBE_GATED`.
- Direct page APIs outside Native: `Runtime.evaluate`, `Input.dispatchMouseEvent`, `Page.navigate`, `Network.getAllCookies`.
- Development probe paths/names: `scripts/*probe*`, `facebook-phase0-probe`, `capture-wechat-request-shapes`.

Markers are checked together with denied paths and positive Native smoke tests; no single minification-sensitive string is treated as sufficient proof.
