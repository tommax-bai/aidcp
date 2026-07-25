# Tasks — self-contained-ads-runtime

<!-- Task 1.7: aidcp-edge commit 1f36bb4; validated on Windows with Node 24 via build:ads-runtime, 20 focused runtime tests, typecheck, and strict OpenSpec validation. -->

> All code lands in **aidcp-edge**. Anchor by function name (source line numbers drift). Regression discipline: after any change run `npm run typecheck` + `npm test` + the electron contract tests; before packaging run the built-app asar-absence probe and a **translocated** smoke test (from DMG/Downloads, not a local `.app`).

## 1. aidcp-edge — packaging (edge-desktop-packaging)

- [ ] 1.1 Add `adspower-browser@2.1.0` to **devDependencies** in `package.json`; `npm install --package-lock-only`.
- [x] 1.7 Windows local development: run npm CLI through the current build-time Node executable (no direct `npm.cmd` spawn), resolve the patched `build/ads-runtime` tree before raw `node_modules`, and cover resolution with a focused test. Windows installer packaging remains deferred.
- [ ] 1.2 New `scripts/stage-ads-runtime.mjs`: fresh global-prefix install into `build/ads-prefix` with `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1` + `PLAYWRIGHT_BROWSERS_PATH=0` + `npm_config_ignore_scripts=true`; copy the package dir → `build/ads-runtime/adspower-browser` (POSIX path; leave the single win32 path line as the seam). Ship full all-arch `sqlite/`; do NOT pre-run `ads start`.
- [ ] 1.3 New `resources/ads-runtime.json` = `{ "adsApiKey": "<baked shared key>", "version": 1 }` (data file; NEVER a `.cjs`; not committed with a real secret if repo is shared — inject at build time or keep in a gitignored local — decide per internal-repo policy).
- [ ] 1.4 `package.json > build`: top-level `extraResources` for `build/ads-runtime/adspower-browser → adspower-browser` and `resources/ads-runtime.json → ads-runtime.json`. Add `build:ads-runtime` script; prepend it in `electron:build` / `electron:build:mac` / `electron:build:win`.
- [ ] 1.5 New `scripts/verify-ads-runtime-staged.mjs`: assert on the built `.app` that `adspower-browser` is absent from `app.asar` and present at `Contents/Resources/adspower-browser/{cli,cwd,sqlite,node_modules}`. Wire into the mac build (fail the build on violation).
- [ ] 1.6 `docs/release-desktop.md`: document the staging step and the **translocated** (DMG/Downloads) first-run smoke requirement.

## 2. aidcp-edge — runtime resolution & staging (edge-bundled-ads-runtime)

- [ ] 2.1 `ads-runtime.cjs resolveCliEntry`: add userData candidate #0 (`userDataPath/ads-runtime/adspower-browser/cli/index.js`); keep the sqlite native-module comment (it is correct). Accept `userDataPath` param.
- [ ] 2.2 `main.cjs stageAdsRuntimeIfNeeded()`: idempotent copy `Contents/Resources/adspower-browser` → `userData/ads-runtime/adspower-browser`; write a `{appVersion, adspowerBrowserVersion}` stamp; on mismatch wipe + re-stage; honest error on copy failure; skip in dev.

## 3. aidcp-edge — hard-switch service/kernel ensure (edge-bundled-ads-runtime)

- [ ] 3.1 Split `ensureAdsRuntimeAndKernel` → `ensureAdsServiceOnce()` (single-flight, cleared on settle) + `ensureKernelOnce()` (single-flight, `kernelDownloaded` short-circuit). Remove the `mode:'external'` HTTP-adopt and `mode:'none'` proceed-anyway branches.
- [ ] 3.2 `ensureAdsServiceOnce` step order: reset base → stage → resolveCliEntry (null = honest hard-stop, no core) → `ensureRuntime` (`ads status` reuse / `ads start -k <resolveAdsApiKey()>`) → set `adsServiceBase` from `parseRuntimePort` (never hardcode 50325) → honest failure + `surfaceFailure`.
- [ ] 3.3 Rename `embeddedAdsApiBase` → `adsServiceBase` throughout.

## 4. aidcp-edge — one base authority + ensure-gating (adspower-environment-provisioning)

- [ ] 4.1 `resolveAdsOpts`: `apiBase = form || adsServiceBase || settings.adsApiBase || undefined` (P0-A fix). Unify `buildAdsProviderEnv` to the renamed base.
- [ ] 4.2 `ads:createEnv`: `await ensureAdsServiceOnce()` at top (service only, NO kernel); on `!ok` return `{ok:false,error:'指纹浏览器运行时未就绪：<cause>',retryable:true}`.
- [ ] 4.3 `ads:updateEnvProxy`, `ads:deleteEnv`: `await ensureAdsServiceOnce()` before `resolveAdsOpts` (metadata, no kernel).
- [ ] 4.4 `reconcileRunningProfiles`: run after service-ensure; stays best-effort.
- [ ] 4.5 `ads:status` / `ads:listProfiles` read IPC: **cached-base fast path** — read `adsServiceBase` directly, re-ensure only on `fetch failed` (no subprocess per poll); failure returns honest object, never crashes panel.

## 5. aidcp-edge — baked key + launch/kernel wiring (edge-bundled-ads-runtime)

- [ ] 5.1 `resolveBakedAdsRuntimeConfig()` (memoized, next to `loadSettings`): read packaged `process.resourcesPath/ads-runtime.json` then dev `appRoot/resources/ads-runtime.json`.
- [ ] 5.2 `resolveAdsApiKey(formKey)`: precedence form > settings > env > baked; route `resolveAdsOpts`, `buildAdsProviderEnv`, `ensureRuntime` through it. Preserve honest-failure when empty.
- [ ] 5.3 `startAdsPowerFlow`: `await ensureAdsServiceOnce()` then `await ensureKernelOnce()` before cancel-gate + `startEdge`; honest bail on either.
- [ ] 5.4 whenReady after `createWindow`: non-blocking `void ensureAdsServiceOnce()` warm-up (swallow failure). Delete dead `openAdsClient` ('open -a AdsPower Global').
- [ ] 5.5 `gracefulStopAllAndQuit`: unchanged core SIGTERM; MUST NOT `ads stop` the daemon (add a comment locking the rationale).

## 6. aidcp-edge — UX & copy (edge-bundled-ads-runtime)

- [ ] 6.1 create-env: static "正在启动指纹浏览器运行时…" line before the ensure `await`, cleared after. **No** `ads:createProgress` IPC channel (cut per review).
- [ ] 6.2 Launch: keep the determinate `kernelPrep` bar (runtime phase no-percent → kernel phase percent). Honest post-ready `/不可达|fetch failed/` remap to "指纹浏览器服务连接中断，请重试" (raw cause to edge log only).
- [ ] 6.3 Copy fixes: API-Key placeholder + probe hint → "留空即用随包默认凭据；仅在需要覆盖时填写".

## 7. aidcp-edge — failure taxonomy (edge-bundled-ads-runtime)

- [~] 7.1 Seat/concurrency: a `browser/start` seat-ceiling rejection inside the core → a **non-crash exit code** that does NOT increment the 5-strike give-up; supervisor classifies it and shows "并发/席位已满：…请错峰或联系管理员扩容". (Not a main.cjs string-matcher.) <!-- 2026-07-25 用户决定砍掉，不实装；spec delta 中对应需求已整条删除，不进权威 spec -->
- [~] 7.2 Kernel download: distinguish stalled/timeout vs errored; disk-full message; partial-file size/sentinel check (don't trust `is_downloaded` blindly) or honest launch-time failure (not a generic core crash). Cancellable download DEFERRED. <!-- 2026-07-25 用户决定砍掉，不实装；spec delta 中对应需求已整条删除，不进权威 spec -->

> **2026-07-25 范围裁决**：第 7 节整节作废（用户决定）。席位/并发上限与内核下载失败分类从未实装，
> 与其把未实装行为写进权威 spec，不如不立此条；若共享密钥席位日后成为真实痛点，另起 change 重新建模。

## 8. aidcp-edge — tests

- [ ] 8.1 `test/electron/lifecycle-contract.test.ts`: add a guard that `runCli` resolves the CLI writable dir from the entry path (not `process.cwd()`) and never inherits a stale cwd. Keep the asar-cwd guard.
- [ ] 8.2 Stub-level unit tests (injectable `run`) for split ensures: service reuse (`alreadyRunning`), base from `parseRuntimePort` (non-50325), create-env triggers service-only (no kernel), honest hard-stop when resolveCliEntry null, seat-ceiling non-crash exit classification.
- [ ] 8.3 `npm run typecheck` + `npm test` + `npm run test:acceptance` green.

## 9. Real-machine acceptance (register to backlog, verify on operator machine)

- [ ] 9.1 Fresh operator mac (no AdsPower client, no CLI): install → create env → launch → kernel downloads once → fingerprint browser opens; zero key input.
- [ ] 9.2 Translocated build (from DMG/Downloads): first-run staging to userData works (no read-only-Resources write failure).
- [ ] 9.3 Machine with a foreign desktop AdsPower on 50325: our CLI takes a fallback port; create/launch hit the bound port (no split-brain, no riding the foreign service).
- [ ] 9.4 Shared-key concurrency: N operators concurrent — seat-ceiling shows the distinct message and does NOT latch the give-up.

## 10. aidcp-edge — V2 browser lifecycle and lost-registry recovery

<!-- Tasks 10.1-10.5: aidcp-edge commit e67fac4; validated after rebase with 82 focused tests, acceptance 24/24, full Edge 1789/1789, typecheck, live read-only V2 reconciliation, and strict OpenSpec validation. -->

- [x] 10.1 Migrate the core AdsPower provider from V1 `browser/start|stop` to V2 per-profile `active|start|stop`, preserving honest CDP-ready/dark confirmation and adding focused request-contract tests.
- [x] 10.2 Migrate Electron manual inspection and startup reconciliation from global V1 `browser/local-active`/`browser/start` to V2 per-profile `active|start` over the known environment roster.
- [x] 10.3 Add bounded profile-cache `DevToolsActivePort` discovery in both lifecycle paths; adopt only when loopback `/json/version` exactly matches the recorded browser websocket path and port.
- [x] 10.4 Cover normal V2-active adoption, V2-inactive validated orphan adoption, rejected stale/spoofed candidates, V2 start fallback, and V2 stop with focused tests.
- [x] 10.5 Run focused tests, `npm run typecheck`, full Edge tests where practical, and strict OpenSpec validation.
