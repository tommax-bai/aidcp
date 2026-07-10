# Tasks

> Landed to aidcp-edge `master` as `90bcb14` (single commit). Edge-only; no ECS/cloud deploy. Main checkout synced for `electron:dev`.

## 1. aidcp-edge — persona prompt / notice timing grace

- [x] 1.1 Renderer: add grace window to `maybePromptPersonaSetup` (per-env unbound-since, `personaPromptGraceMs` default 6s, re-eval timer) so an account is not prompted before its `personaBound` signal can arrive; overridable via `settings.personaPromptGraceMs` for tests <!-- aidcp-edge 90bcb14 src/electron/renderer/renderer.js -->
- [x] 1.2 Main: add the same grace to the controlled-page reminder (`syncBrowserPersonaNotice` + `personaNoticeReadySince` + recheck timer + `resetPersonaNoticeGrace` at the 3 session-reset points + handle init) <!-- aidcp-edge 90bcb14 src/electron/main.cjs -->
- [x] 1.3 Fix (review): clear `personaUnboundSince` on env removal (avoid stale-since false prompt + leak on re-add of same profile) <!-- aidcp-edge 90bcb14 src/electron/renderer/renderer.js -->
- [x] 1.4 Tests: already-bound account never auto-pops; genuinely-unbound prompts after grace; grace-window suppression <!-- aidcp-edge 90bcb14 test/electron/fleet-console.test.ts -->

## 2. aidcp-edge — primary-screen parking (default) + reliability

- [x] 2.1 `browser-parking.cjs`: add `primary-screen` mode + make default; `primaryScreenBounds` (right-aligned background slot, display-fitted); center `visibleBounds`; `boundsForMode` single-source; parking-display no-secondary falls back to default; fallback bounds = visible/centered <!-- aidcp-edge 90bcb14 src/electron/browser-parking.cjs -->
- [x] 2.2 `browser-window.ts`: accept `primary-screen` (union / VALID_MODES / modeOf default); `showBrowserWindow` raises via `Page.bringToFront` <!-- aidcp-edge 90bcb14 src/cdp/browser-window.ts -->
- [x] 2.3 `main.ts`: wrap `applyBrowserParking` so a parking-apply failure can't skip installing the stdin control listener <!-- aidcp-edge 90bcb14 src/main.ts -->
- [x] 2.4 `main.cjs`: default-mode comment + mode-aware show/re-park hint <!-- aidcp-edge 90bcb14 src/electron/main.cjs -->
- [x] 2.5 Renderer settings: add `主屏停放` button + hint; `PARKING_MODES` / defaults include `primary-screen` <!-- aidcp-edge 90bcb14 src/electron/renderer/{renderer.js,index.html} -->
- [x] 2.6 Tests: primary-screen default + bounds; parking-display fallback consistency; show raises (bringToFront); config accepts primary-screen; renderer default button <!-- aidcp-edge 90bcb14 test/electron/browser-parking.test.ts, test/cdp/browser-window.test.ts, test/electron/renderer-smoke.test.ts -->

## 3. aidcp-edge — environment avatar 3-state toggle + red selection

- [x] 3.1 Renderer: `fleetView.shownEnv`; `onRailRowActivate` (select → showDrivenBrowser → resetBrowserParking); honest-failure never advances phase; reset on env switch; clear stale shown only when core not running (attention/captcha envs keep shown); `shown` in rail sig + phase-aware row title <!-- aidcp-edge 90bcb14 src/electron/renderer/renderer.js -->
- [x] 3.2 CSS: red `.rail-row.selected` + stronger red `.rail-row.shown` (expanded + collapsed), kept distinct from lv-error avatar ring <!-- aidcp-edge 90bcb14 src/electron/renderer/styles.css -->
- [x] 3.3 Fix (review): keyboard Enter/Space on the persona ✦ icon must not trigger the toggle (guard `e.target === row`) <!-- aidcp-edge 90bcb14 src/electron/renderer/renderer.js -->
- [x] 3.4 Tests: avatar three-state (select → show → re-park); attention-env keeps shown + stays re-parkable; keyboard carve-out; phase reset on switch <!-- aidcp-edge 90bcb14 test/electron/fleet-console.test.ts -->

## 4. Validation & landing

- [x] 4.1 `npm run typecheck` + `npm test` (871) + `npm run test:acceptance` (16) green; adversarial multi-agent review, 3 confirmed findings fixed <!-- aidcp-edge 90bcb14 -->
- [x] 4.2 Land branch → edge `master` (`90bcb14`); main checkout synced for `electron:dev` <!-- aidcp-edge 90bcb14 -->
- [ ] 4.3 Real-machine backlog (see docs/real-machine-acceptance-backlog.md): parking actually tucks on the operator machine (single + multi monitor, cascade stacking), avatar toggle summon/re-park + red highlight legibility, and already-set accounts no longer flash the persona prompt/banner
