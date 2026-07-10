## 1. aidcp-edge — Fingerprint browser permission-prompt suppression

- [x] 1.1 Add `--deny-permission-prompts` to AdsPower launch args (`src/cdp/browser-provider.ts`). <!-- aidcp-edge 381bc4a: flag added to launch_args alongside window-size. -->
- [x] 1.2 Add `--deny-permission-prompts` to self `buildChromeArgs` (`src/cdp/chrome-launcher.ts`). <!-- aidcp-edge 381bc4a: flag added next to --disable-infobars. -->
- [x] 1.3 Add a catch-guarded CDP `Browser.setPermission … denied` backstop (notifications, geolocation, camera, microphone) as an exported helper, called from `reEnableAndInject` so it runs on first attach and on every reconnect (`src/cdp/session.ts`). <!-- aidcp-edge 381bc4a: denyPermissionPrompts() exported + wired into reEnableAndInject; omits origin (all origins); best-effort per-permission catch. -->
- [x] 1.4 Fix the self-mode stealth injector's notifications `permissions.query` remap to faithfully map `Notification.permission` (default→prompt, denied/granted unchanged), so `permissions.query` stays consistent with `Notification.permission` after notifications are denied instead of reporting `prompt` while `Notification.permission` is `denied` (`src/cdp/stealth-injector.ts`). <!-- aidcp-edge 381bc4a: remap changed from denied→prompt to default→prompt; eliminates the mismatch our deny would otherwise create in self mode. -->

## 2. aidcp-edge — Electron companion window notifications

- [x] 2.1 Allow `notifications` in the companion window permission allowlist while keeping device-access permissions denied (`src/electron/main.cjs`). <!-- aidcp-edge 381bc4a: 'notifications' added to BROWSER_PERMISSION_ALLOWLIST; geolocation/camera/mic still denied. -->

## 3. Tests and Validation

- [x] 3.1 Unit tests: both launch-arg builders include `--deny-permission-prompts`; the CDP backstop helper issues `Browser.setPermission` `denied` for each target permission and stays non-fatal when a call rejects. <!-- aidcp-edge 381bc4a: extended chrome-launcher/browser-provider arg tests; new test/cdp/session.test.ts covers ordering, denied+no-origin, and best-effort non-fatal reject. -->
- [x] 3.2 Companion window permission policy grants `notifications` and denies `geolocation`/`camera`/`microphone`. <!-- aidcp-edge 381bc4a: code-complete (Set membership). main.cjs is the Electron entry with no exports and is not required by any test → not cheaply unit-testable; runtime behavior deferred to real-machine backlog per test-restraint. -->
- [x] 3.3 Run `npm run typecheck`, targeted tests, and `npm run test:acceptance` in `aidcp-edge`. <!-- aidcp-edge 381bc4a: typecheck clean; full npm test 914 pass / 0 fail (post-rebase); test:acceptance 16 pass (AC-PUB/AC-* green). -->
- [x] 3.4 Run `openspec validate browser-permission-prompt-defaults --strict`. <!-- aidcp: validation passed (strict). -->

## Real-machine verification (deferred — operator machine)

Deferred to `docs/real-machine-acceptance-backlog.md` 簇 38 (edge-only, no ECS deploy): confirm on the operator machine (AdsPower fingerprint browser, `tom` group) that the "allow notifications" dialog no longer appears and the Electron companion window's own notifications still work. The operator machine must pull `aidcp-edge` master and rebuild the client for the fix to take effect.
