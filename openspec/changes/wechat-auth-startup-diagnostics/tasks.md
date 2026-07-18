## 1. Edge diagnostics

- [x] 1.1 Add safe startup-auth logs for stored-session lookup, validation success, fail-closed outcomes, and API-only browser bypass.
  <!-- repo=aidcp-edge commit=4e4e3e5 validation=wechat auth and module suites pass deviation=none -->
- [x] 1.2 Add a stable reason tag before every auth-driven browser launch without logging credentials or raw identity values.
  <!-- repo=aidcp-edge commit=4e4e3e5 validation=pre-open assertions plus secret-redaction assertions pass deviation=none -->
- [x] 1.3 Add focused tests for valid stored-session bypass, missing/expired session browser launch, and temporary failure no-browser recovery.
  <!-- repo=aidcp-edge commit=4e4e3e5 validation=17 focused auth tests and 70 wechat module tests pass deviation=none -->

## 2. Validation and delivery

- [x] 2.1 Run focused WeChat Channels auth tests and Edge typecheck.
  <!-- repo=aidcp-edge commit=4e4e3e5 validation=70 pass 0 fail; tsc noEmit pass with existing shared dependency runtime and explicit type roots deviation=worktree node_modules lacked dev CLIs, so no install was performed and moduleResolution Node was used for the typecheck -->
- [x] 2.2 Run `openspec validate wechat-auth-startup-diagnostics --strict` and record validation evidence.
  <!-- repo=aidcp validation=openspec strict pass deploy=n/a deviation=none -->
- [x] 2.3 Rebase, fast-forward integrate and push the Edge and control default branches without force. Do not build an installer or deploy a Cloud runtime.
  <!-- repos=aidcp-edge,aidcp commits=4e4e3e5,67d4b97 pushed=origin/master,origin/main deploy=n/a deviation=installer and Cloud deploy intentionally not run -->
