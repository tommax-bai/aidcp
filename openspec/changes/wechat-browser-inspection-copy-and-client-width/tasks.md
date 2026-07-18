## 1. Contract

- [x] 1.1 Define the shortened manual-inspection copy, wider browser action, and 900px client startup width in the OpenSpec delta.

## 2. Edge implementation

- [x] 2.1 Update the video-channel workspace initial and render-fallback copy.
- [x] 2.2 Increase the desktop browser action width share while preserving the narrow responsive layout.
- [x] 2.3 Set both login and authenticated main BrowserWindow defaults to 900px.

## 3. Validation and delivery

- [x] 3.1 Add focused regression coverage for the copy, layout contract, and both window defaults.
  <!-- Edge focused Electron tests: 40/40 passed; final static layout rerun: 3/3 passed. -->
- [x] 3.2 Run focused tests, typecheck, build, and `openspec validate wechat-browser-inspection-copy-and-client-width --strict`.
  <!-- Edge build and typecheck passed before integration. land-change then passed acceptance 24/24, full suite 1779/1779, and typecheck. OpenSpec strict validation passed before implementation and at closeout. -->
- [ ] 3.3 Commit and push Edge/control changes without building an installer; record validation and SHAs.
