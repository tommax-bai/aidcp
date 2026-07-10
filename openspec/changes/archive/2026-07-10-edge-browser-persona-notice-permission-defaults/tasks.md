## 1. Persona Client Experience

- [x] 1.1 Automatically open and de-duplicate Electron persona prompts for ready, unbound accounts.
  <!-- aidcp-edge renderer opens once per unresolved selected env/account and emits one desktop notification. -->
- [x] 1.2 Render tone and grouped content-preference panels with recruitment first and per-category custom interests.
  <!-- aidcp-edge renders tone first, recruitment first in content groups, and includes bounded custom interests in keywordSelections. -->
- [x] 1.3 Deny non-allowlisted Electron permission requests and surface throttled notifications honestly.
  <!-- aidcp-edge main installs a fail-closed Electron permission handler with a narrow allowlist and throttled notifications. -->

## 2. Controlled Browser Reminder

- [x] 2.1 Add environment-scoped Electron-to-core routing for `browser.personaNotice` state.
  <!-- aidcp-edge main derives and de-duplicates reminder state on each EnvHandle, then writes only to that handle's child stdin. -->
- [x] 2.2 Inject an idempotent Shadow DOM persona reminder through CDP and remove it when inactive.
  <!-- aidcp-edge browser-window owns the namespaced Shadow DOM host and removes it on inactive state or controller disposal. -->
- [x] 2.3 Reapply unresolved reminders after top-frame navigation and CDP reconnect.
  <!-- BrowserPersonaNoticeController retains desired state and listens to Page.frameNavigated plus cdp.reconnected. -->

## 3. AdsPower Permission Default

- [x] 3.1 Add `location='block'` while retaining `location_switch='1'` in every new profile fingerprint config.
  <!-- aidcp-edge ads-fingerprint adds both fields to the shared template builder used by all new profiles. -->
- [x] 3.2 Add focused tests that assert the final `user/create` fingerprint payload and preserve the proxy-only update boundary.
  <!-- ads-create-flow and ads-fingerprint assert both location fields; ads-write-api regression still asserts user/update has only user_id + user_proxy_config. -->

## 4. Verification And Release

- [x] 4.1 Add focused tests for prompt de-duplication, browser reminder lifecycle/isolation, and custom preferences.
  <!-- Focused suite passed 68/68 across fleet console, persona notice routing, CDP reminder lifecycle, AdsPower fingerprint/create, and write-boundary tests. -->
- [x] 4.2 Run aidcp-edge tests, typecheck, syntax checks, and diff checks.
  <!-- validation: npm test, npm run test:acceptance, npm run typecheck, node --check for touched CJS/renderer files, and git diff --check all passed. -->
- [x] 4.3 Validate the OpenSpec change in strict mode and record implementation evidence.
  <!-- validation: openspec validate edge-browser-persona-notice-permission-defaults --strict passed before release; repeated after release/task evidence update. -->
- [x] 4.4 Commit and push edge/control changes, publish the desktop package to dev, and verify the public download artifacts.
  <!-- aidcp-edge: f138e77 + e5633c4 landed on origin/master after rebasing over 63cd290; aidcp-console: 0ede919 landed on origin/master. Built 0.3.4 from clean master e5633c4 and verified mac x64/arm64 plus Windows app.asar content. Published to dev /opt/aidcp/downloads and deployed console after backup /opt/aidcp/backups/aidcp-console-20260710-114405.tgz. Public 8088 URLs returned 200; sha256: x64 dmg 21b2c9b1e70f1d6a2ec58ac8ea077adb6980090d788c1932a03686dca85c0b99, arm64 dmg e6e8c46649975f3f5abcbcc63b9bfec838af34991d5a15810b82e6a6e023eb5b, Windows exe 8f5f7359d422addaa8b52adb75d32d606cbe38057f5b9e2d02acaac915315413. Console tests 76 passed / 1 skipped, build passed, root and panel API returned 200, and checked isales services remained active. Real AdsPower page acceptance remains a post-install operator check; CDP lifecycle tests and packaged-content checks passed. -->
