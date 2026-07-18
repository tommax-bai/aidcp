## 1. Runtime resource

- [x] 1.1 Reuse and verify the existing branded `build/icon.png` as the supported tray runtime resource. <!-- aidcp-edge b9be0be; PNG signature and non-empty asset contract passed -->
- [x] 1.2 Package the tray PNG as an electron-builder extraResource for installed desktop builds. <!-- aidcp-edge b9be0be; package.json maps build/icon.png to Resources/tray-icon.png -->

## 2. Supervisor behavior

- [x] 2.1 Resolve deterministic development and packaged tray icon paths and load the PNG with `nativeImage.createFromPath`. <!-- aidcp-edge b9be0be -->
- [x] 2.2 Reject missing or empty tray images through the existing honest failure surface and prevent window hiding when no usable tray exists. <!-- aidcp-edge b9be0be -->

## 3. Verification

- [x] 3.1 Add focused Electron contract tests for supported format usage, resource packaging, image validation, and visible-window fallback. <!-- aidcp-edge b9be0be -->
- [x] 3.2 Run focused Electron tests and `npm run typecheck` in the edge worktree. <!-- 12/12 focused tests passed; acceptance 24/24 passed; node --check main/helper passed; typecheck passed. Full npm test: 1750/1751 passed; the sole Windows chmod 0600 mode assertion failure reproduces unchanged on canonical master and is unrelated to this change. -->
- [x] 3.3 Run `openspec validate visible-edge-tray-icon --strict` and record repository commit and validation evidence. <!-- strict validation passed; implementation aidcp-edge b9be0be; no installer build or deployment requested -->
