## 1. Client environment grouping

- [x] 1.1 Split the renderer rail definitions into running, paused, and offline groups while preserving action-needed priority.
  <!-- aidcp-edge: renderer group predicates now use status.session=paused and keep needsAction first. -->
- [x] 1.2 Add focused fleet-console DOM coverage for group titles, ordering, and exclusive row membership.
  <!-- aidcp-edge: fleet-console DOM test covers need-action, running, paused, offline ordering and one-row-one-group membership. -->

## 2. Validation and delivery

- [x] 2.1 Run the focused Electron test and edge typecheck, then validate the OpenSpec change strictly.
  <!-- Validation: fleet-console 42/42 passed; npm run typecheck passed; openspec validate client-environment-status-groups --strict passed. -->
- [x] 2.2 Record repository commits, validation, integration, push, and dev deployment evidence in this checklist.
  <!-- aidcp-edge commit e7a0252 fast-forwarded to master and pushed to origin/master. Post-merge fleet-console 42/42 and typecheck passed. Edge-only renderer source change has no ECS dev runtime deployment; no installer/package was built because packaging was not requested. Control OpenSpec commit is recorded by the enclosing repository history. -->
