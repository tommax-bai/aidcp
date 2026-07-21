## 1. Facebook stopped-state visibility

- [x] 1.1 Pass the selected environment platform into the pure runtime-guidance view and return no card for Facebook when the normalized automation state is exactly `stopped`.
- [x] 1.2 Keep the existing DOM cleanup and platform-switch rerender path so a visible card from another environment cannot remain after switching to a stopped Facebook environment.

## 2. Regression validation

- [x] 2.1 Add pure-logic and Electron DOM coverage for structured and legacy stopped states, retained cached progress, non-stopped Facebook states, and Facebook/XHS switching.
- [x] 2.2 Run focused UI logic/companion renderer tests and renderer syntax checks.
- [x] 2.3 Run the required Edge full test suite and typecheck, using a focused serial rerun as the deciding gate if shared-machine load causes a timeout.

## 3. Delivery

- [x] 3.1 Record Edge commit and validation evidence, then pass strict OpenSpec validation.
- [ ] 3.2 Replay onto the latest default branches, rerun deciding checks, fast-forward merge and push Edge and control repositories; record that no Cloud deployment or desktop package applies.

<!-- aidcp-edge commit 2fa334c; focused UI/DOM 139/139, renderer syntax checks, full Edge suite 2180/2180 and typecheck passed. OpenSpec strict validation passed. -->
