## 1. Cloud Implementation

- [x] 1.1 Centralize Edge-origin risk-fact dedupe key construction at the Cloud enqueue boundary.
  <!-- repo=aidcp-cloud; commit=a3f3b80; validation=focused/full/typecheck passed; deployment=dev a3f3b80; deviations=none -->
- [x] 1.2 Bind the key to account ID, Edge environment ID, original envelope timestamp and ID, action, and the existing optional discriminator.
  <!-- repo=aidcp-cloud; commit=a3f3b80; validation=focused key assertions passed; deployment=dev a3f3b80; deviations=none -->
- [x] 1.3 Route every Edge-origin risk-fact receipt through the scoped key without changing Edge, protocol, schema, worker, or historical rows.
  <!-- repo=aidcp-cloud; commit=a3f3b80; validation=call-site review plus full suite; deployment=dev a3f3b80; deviations=none -->

## 2. Verification

- [x] 2.1 Add focused tests proving exact replay stability and isolation across accounts, environments, and restarted envelope sequences.
  <!-- repo=aidcp-cloud; commit=a3f3b80; validation=23/23 focused tests; deployment=dev a3f3b80; deviations=none -->
- [x] 2.2 Run the focused risk-accounting tests, Cloud acceptance suite, full Cloud test suite, and Cloud typecheck.
  <!-- repo=aidcp-cloud; commit=a3f3b80; validation=focused 23/23, acceptance 162/162, full 3757 pass 11 skip 0 fail, typecheck pass; deployment=dev a3f3b80; deviations=test:pg not run because SQL/schema/transaction code unchanged -->
- [x] 2.3 Run `openspec validate scope-risk-counter-dedupe-key --strict`.
  <!-- repo=aidcp; commit=3f7569b; validation=strict pass after final rebase; deployment=not applicable; deviations=none -->

## 3. Integration and DEV Delivery

- [x] 3.1 Commit the Cloud and control-repo changes with validation evidence recorded in this checklist.
  <!-- repos=aidcp-cloud,aidcp; commits=a3f3b80,3f7569b; validation=all required gates recorded above; deployment=dev a3f3b80; deviations=none -->
- [x] 3.2 Rebase and fast-forward the validated commits onto the latest default branches, then push both defaults.
  <!-- repos=aidcp-cloud,aidcp; commits=master a3f3b80,main 3f7569b; validation=remote fast-forward pushes and canonical fast-forward updates; deployment=dev a3f3b80; deviations=first control push raced a new remote commit and was safely rejected, then rebased and strict-validated before retry -->
- [x] 3.3 Deploy the Cloud change to DEV from a clean eligible default checkout and verify service, listener, health, Feishu, and PostgreSQL without initiating an extra real platform action.
  <!-- repo=aidcp-cloud; commit=a3f3b80; deployment=dev backup /opt/aidcp/cloud.bak.20260728-154015.scope-risk-counter-dedupe-key.tar.gz and env backup; package hashes unchanged; migrations content 20/20 automation 52/52 api 60/60 with zero pending; stop-start only aidcp-cloud.service; active NRestarts=0; listeners 8787/8090/8091/8088/5432; panel health ok; three PG probes ok; all schema enforce gates passed; writer lock target=dev; Feishu WS onReady; four isales services remained active; post-start outbox total=0 so no live new-key claim; no real platform write; deviations=none -->
