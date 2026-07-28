## 1. Cloud Implementation

- [x] 1.1 Centralize Edge-origin risk-fact dedupe key construction at the Cloud enqueue boundary.
  <!-- repo=aidcp-cloud; commit=a3f3b80; validation=focused/full/typecheck passed; deployment=pending 3.3; deviations=none -->
- [x] 1.2 Bind the key to account ID, Edge environment ID, original envelope timestamp and ID, action, and the existing optional discriminator.
  <!-- repo=aidcp-cloud; commit=a3f3b80; validation=focused key assertions passed; deployment=pending 3.3; deviations=none -->
- [x] 1.3 Route every Edge-origin risk-fact receipt through the scoped key without changing Edge, protocol, schema, worker, or historical rows.
  <!-- repo=aidcp-cloud; commit=a3f3b80; validation=call-site review plus full suite; deployment=pending 3.3; deviations=none -->

## 2. Verification

- [x] 2.1 Add focused tests proving exact replay stability and isolation across accounts, environments, and restarted envelope sequences.
  <!-- repo=aidcp-cloud; commit=a3f3b80; validation=23/23 focused tests; deployment=pending 3.3; deviations=none -->
- [x] 2.2 Run the focused risk-accounting tests, Cloud acceptance suite, full Cloud test suite, and Cloud typecheck.
  <!-- repo=aidcp-cloud; commit=a3f3b80; validation=focused 23/23, acceptance 162/162, full 3757 pass 11 skip 0 fail, typecheck pass; deployment=pending 3.3; deviations=test:pg not run because SQL/schema/transaction code unchanged -->
- [x] 2.3 Run `openspec validate scope-risk-counter-dedupe-key --strict`.
  <!-- repo=aidcp; commit=pending 3.1; validation=strict pass; deployment=not applicable; deviations=none -->

## 3. Integration and DEV Delivery

- [ ] 3.1 Commit the Cloud and control-repo changes with validation evidence recorded in this checklist.
- [ ] 3.2 Rebase and fast-forward the validated commits onto the latest default branches, then push both defaults.
- [ ] 3.3 Deploy the Cloud change to DEV from a clean eligible default checkout and verify service, listener, health, Feishu, and PostgreSQL without initiating an extra real platform action.
