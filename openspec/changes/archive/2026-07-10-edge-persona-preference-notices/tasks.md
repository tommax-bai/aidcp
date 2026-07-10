## 1. aidcp-edge Client UX

- [x] 1.1 Add renderer-side auto prompt and de-duplication for ready-but-unbound persona state.
  <!-- aidcp-edge: renderer opens the persona dialog once per ready/unbound env and clears de-dup state after persona binding. -->
- [x] 1.2 Add an Electron IPC/system notification path for persona setup and denied browser permissions.
  <!-- aidcp-edge: preload/main notify IPC sends Electron notifications for persona setup and permission denials. -->
- [x] 1.3 Replace the persona keyword UI with the two-panel tone/content-preference layout and screenshot-derived categories.
  <!-- aidcp-edge: persona setup now renders top tone panel and content preference groups, with recruitment/job seeking placed first. -->
- [x] 1.4 Add per-category custom `+` interests and include them in persona generation keywords.
  <!-- aidcp-edge: each content group has a custom add row; generated keywords include the group title and selected/custom interests. -->

## 2. Browser Permission Handling

- [x] 2.1 Install a main-window permission request handler that denies geolocation and other sensitive permissions by default.
  <!-- aidcp-edge: Electron main-window permission handler deny-lists sensitive prompts by default and allow-lists only benign fullscreen/pointer lock. -->
- [x] 2.2 Surface denied permission requests in the client without pretending authorization succeeded.
  <!-- aidcp-edge: denied permission requests emit a throttled client notification with permission type and origin. -->

## 3. Verification

- [x] 3.1 Update Electron renderer tests for auto prompt, two-panel layout, recruitment category, and custom interests.
  <!-- aidcp-edge: test/electron/fleet-console.test.ts covers auto prompt/notify, two panels, recruitment category, and custom interest generation. -->
- [x] 3.2 Run focused Electron tests and typecheck for aidcp-edge.
  <!-- validation: npm test -- test/electron/fleet-console.test.ts passed 834 tests; npm run typecheck passed. -->
- [x] 3.3 Validate `edge-persona-preference-notices` with OpenSpec strict mode and record implementation notes.
  <!-- validation: openspec validate edge-persona-preference-notices --strict passed. -->
