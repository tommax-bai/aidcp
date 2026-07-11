## 1. Edge Desktop State

- [x] 1.1 Add an optional persistent abnormal-exit detail field to the Electron companion status state.
  <!-- repo=aidcp-edge commit=a67ed07 added status.edgeFailure as optional renderer-compatible state -->
- [x] 1.2 Capture the concise actionable error line from core stderr/startup failures and attach it to abnormal exit status updates.
  <!-- repo=aidcp-edge commit=a67ed07 captures non-stack failure summaries from core output and local Chrome startup failure -->
- [x] 1.3 Clear stale failure details when a fresh start/restart/pause/intentional stop begins or when the edge reaches running state.
  <!-- repo=aidcp-edge commit=a67ed07 clears edgeFailure on start/restart/pause and successful running updates -->

## 2. Client UI

- [x] 2.1 Render the persistent failure detail in the companion window health/status surface.
  <!-- repo=aidcp-edge commit=a67ed07 added in-window failure banner and health detail summary -->
- [x] 2.2 Keep full raw logs in developer details without duplicating stack traces into the primary UI.
  <!-- repo=aidcp-edge commit=a67ed07 primary UI renders only edgeFailure.summary; developer details keep raw lastMessage log -->

## 3. Verification

- [x] 3.1 Add focused Electron UI/state tests for abnormal exit detail persistence and clearing.
  <!-- repo=aidcp-edge commit=a67ed07 added companion-ui coverage for persistent failure details and clearing -->
- [x] 3.2 Run focused edge tests for the touched Electron modules.
  <!-- repo=aidcp-edge commit=a67ed07 validation: focused Electron tests passed; npm run typecheck passed; npm test passed 615/615 -->
- [x] 3.3 Run `openspec validate show-edge-failure-details --strict`.
  <!-- repo=aidcp validation=openspec validate show-edge-failure-details --strict passed -->
