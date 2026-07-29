## 1. Native Router Parity

- [x] 1.1 Add focused failing router cases for same-page click-leg reuse, recommendation decoys, ambiguous target regions, fresh React element actuation, and honest no-click outcomes.
  <!-- aidcp-edge: characterization failed 8 focused assertions before implementation, including 30s facade truncation and absent join_click; final router/host/client focused run 57/57 -->
- [x] 1.2 Port the proven current-group scope and candidate classification into the Native Facebook router, retaining bounded out-of-scope evidence.
  <!-- aidcp-edge: attribute-encoded recommendation, symmetric heading ambiguity, member+Join contradiction, pending precedence, login/captcha, and bounded candidate tests pass -->
- [x] 1.3 Add the router-internal fresh `join_click` operation that actuates exactly one enabled in-scope Join element and otherwise fails closed.
  <!-- aidcp-edge: JSDOM React-handler test passes; Rust fake-CDP confirms Runtime.evaluate join_click and no mousePressed/mouseReleased -->

## 2. Native Execution and Timeout Budget

- [x] 2.1 Make Rust reuse an already-open canonical group page only for the click leg, preserve observe-leg navigation, and replace coordinate join actuation with the fresh in-page operation.
  <!-- aidcp-edge: fake-CDP click-leg test confirms zero Page.navigate on the canonical page and no primary coordinate press/release; blocker test confirms navigation remains when page differs -->
- [x] 2.2 Restore the 2-second hydration settle, 1.5-second immediate settle, 45-second durable verification, and honest effect/reason ordering.
  <!-- aidcp-edge: constants and execution ordering restored; loading Join does not end readiness, login/captcha and pending/questionnaire precede structural joined, document-ready guard retained, durable post-click facts win over simultaneous cancellation, and pre/post-actuation cancellation truth is covered -->
- [x] 2.3 Give only Native Facebook `group_join` a 90-second host command budget and allow that ceiling in the Facebook Native session while ordinary commands remain at 30 seconds.
  <!-- aidcp-edge: browse-session/client/protocol tests prove Facebook group_join 90s; non-group commands and non-Facebook sessions remain capped at 30s -->

## 3. Verification and Delivery

- [x] 3.1 Run the focused Native router/session/Rust tests, Cargo tests, and Edge typecheck.
  <!-- aidcp-edge pre-commit: router+browse-session+client 57/57; after rebasing onto the integrated Reels work, focused router/host/client 74/74, cargo lib 55/55, focused group-join fake-CDP 2/2, cargo fmt check, typecheck, protocol acceptance 30/30, and full Edge 2336/2336 all passed. The earlier full fake-CDP aggregate exposed three non-join baseline failures in initial Feed and note-detail hydration fixtures. Strict clippy found two pre-existing collapsible-if warnings outside this change; clippy with only that lint allowed passed. -->
- [x] 3.2 Run `openspec validate restore-native-facebook-group-join-parity --strict` and record exact repositories, commits, validations, deviations, and delivery boundaries in this checklist.
  <!-- aidcp control pre-commit: strict validation pass. Delivery remains source-only feature branches: no package, artifact injection, deployment, or real-account join. Native 18.5s coordinator-visible commit-window parity is explicitly not claimed; pre-click cancellation is not-started and post-click cancellation is clicked=true ambiguous. -->
- [x] 3.3 Commit the Edge implementation and control OpenSpec artifacts on their isolated feature branches without packaging, deployment, artifact injection, or a real join.
  <!-- aidcp-edge was rebased after Reels and fast-forward integrated/pushed as 938767d0f7134d95bf77dcb055efc904d8ff22a1. Control artifacts were rebased as d89df39 and 5e933c5 before this integration evidence update. No package, artifact injection, deployment, or real-account join was performed. The separately specified preserve-native-facebook-capability-boundaries change owns the still-missing coordinator-visible commit-window parity. -->
