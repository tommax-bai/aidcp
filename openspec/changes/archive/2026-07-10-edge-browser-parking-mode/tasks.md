## 1. Electron Settings and Environment

- [x] 1.1 Add persisted `browserParkingMode` setting with enum validation and default `edge-strip`. <!-- aidcp-edge 083fdb5: persisted setting normalized in Electron main. -->
- [x] 1.2 Compute parking bounds in Electron main from display geometry, including `parking-display` fallback to `edge-strip`. <!-- aidcp-edge 083fdb5: added display geometry planner and no-secondary fallback. -->
- [x] 1.3 Inject parking mode, effective bounds, and launch-position hint into the spawned edge core process. <!-- aidcp-edge 083fdb5: injected parking env and launch position hints. -->

## 2. Edge Core Browser Parking

- [x] 2.1 Add CDP window utility to apply normal browser bounds, show/reset visible placement, and probe page visibility/viewport. <!-- aidcp-edge 083fdb5: added CDP browser-window utility. -->
- [x] 2.2 Apply parking after `attachToPage` and degrade honestly when verification fails. <!-- aidcp-edge 083fdb5: applies after attach with fallback/error verification. -->
- [x] 2.3 Extend AdsPower/self startup hints where available without changing provider lifecycle ownership. <!-- aidcp-edge 083fdb5: adds window-position hints to AdsPower/self launch only. -->

## 3. Desktop UI and Recovery Controls

- [x] 3.1 Add the three parking mode options to the settings drawer with Chinese labels and concise risk copy. <!-- aidcp-edge 083fdb5: added settings drawer segmented controls. -->
- [x] 3.2 Add IPC/tray or settings actions to show/reset the driven browser window and report honest failure when unavailable. <!-- aidcp-edge 083fdb5: added renderer IPC and tray recovery commands. -->
- [x] 3.3 Keep existing startup, restart, save-failure, and provider-selection behavior compatible. <!-- aidcp-edge 083fdb5: existing renderer smoke/full tests remain green. -->

## 4. Tests and Validation

- [x] 4.1 Add/extend unit tests for settings validation, display-bound computation, env injection, and CDP parking fallback. <!-- aidcp-edge 083fdb5: added Electron parking and CDP parking tests. -->
- [x] 4.2 Add/extend Electron renderer smoke tests for the parking controls. <!-- aidcp-edge 083fdb5: renderer smoke covers default, save, and unavailable recovery. -->
- [x] 4.3 Run `npm run typecheck` and targeted tests in `aidcp-edge`. <!-- aidcp-edge 083fdb5: npm run typecheck; targeted tsx tests; npm test; npm run test:acceptance all pass. -->
- [x] 4.4 Run `openspec validate edge-browser-parking-mode --strict`. <!-- aidcp 2026-07-06: validation passed after edge implementation. -->
