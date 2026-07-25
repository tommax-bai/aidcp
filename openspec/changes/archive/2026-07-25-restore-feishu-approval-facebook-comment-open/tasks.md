## 1. Cloud Approval Composition

- [x] 1.1 Inject the shared durable `writeApprovalDecision` authority into every production `FeishuWsReceiver` composition in `aidcp-cloud`.
- [x] 1.2 Add a production-composition regression that fails if the Feishu receiver loses its durable approval write port, while retaining the receiver's existing fail-closed unit coverage.

## 2. Facebook Target Identity

- [x] 2.1 Replace raw Facebook detail-URL equality in the Cloud comment open step with the existing canonical post-identity helper and add equivalent-form/mismatch regressions.
- [x] 2.2 Add canonical Facebook target derivation and bounded requested-detail polling to the Edge Native Page Engine.
- [x] 2.3 Add Native tests proving transient unrelated detail is discarded, equivalent target detail succeeds, and a never-matching target ends in bounded failure without false evidence.

## 3. Validation and Integration

- [x] 3.1 Run focused Cloud approval/comment tests and Edge Native Page Engine tests.
- [x] 3.2 Run the required Cloud acceptance/full-test/typecheck and Edge Native verification/typecheck suites.
- [x] 3.3 Run `openspec validate restore-feishu-approval-facebook-comment-open --strict` and record repository commits, validations, delivery scope, and deviations in this task file.
- [x] 3.4 Rebase, fast-forward integrate, commit, and push the Cloud, Edge, and control changes on their canonical default branches.

## 4. DEV Delivery

- [x] 4.1 Run the DEV deployment prechecks, deploy the clean integrated Cloud default branch, and verify service, listener, health, Feishu, and PostgreSQL evidence without touching unrelated services.
- [x] 4.2 Rebuild and verify the local Edge Native Page Engine from the integrated source, without packaging or releasing an installer.
- [x] 4.3 Report code validation, DEV deployment, local Edge artifact, and any real-account evidence as separate delivery boundaries.

<!--
Implementation evidence (2026-07-25):
- aidcp-cloud master 8a8a7755877c5e657688f7b1015fd5c85bf7c7c7
  - focused Feishu/composition/Facebook-edge steps: 46 pass, 0 fail
  - acceptance: 117 pass, 0 fail
  - full: 3336 total, 3326 pass, 10 gated skip, 0 fail
  - typecheck: pass
- aidcp-edge master 6cb8572bcaffa2984c8b0d8d854f833a86495093
  - acceptance: 30 pass, 0 fail
  - full TypeScript: 2295 pass, 0 fail
  - typecheck: pass
  - Native Rust: 50 unit + 1 contract + 13 fake-CDP + 1 process protocol pass; clippy -D warnings pass
  - transient wrong-detail then equivalent target, and bounded never-matching target, both pass
- OpenSpec strict validation: pass.

Delivery evidence:
- DEV preflight resolved host 121.89.85.150 and aidcp-cloud.service.
- DEV source backup: /opt/aidcp/backups/cloud-20260725-233355
- DEV deployed Cloud SHA: 8a8a7755877c5e657688f7b1015fd5c85bf7c7c7
- Migration status before and after rsync: content/automation/api all checksum-consistent, pending=0.
- Restart was stop-then-start for aidcp-cloud.service only. Service active; 8787/8090/8091 listening;
  PostgreSQL ready; enforce schema gates passed for all three owners; automation writer lock held for dev;
  PublishApprovalStore ready; Feishu WS onReady; bot identity Dev.A; no error-priority startup logs.
- Integrated local Edge arm64 Native artifact verified:
  sha256 87d6fb29d310652efb7b25743b3a0d18da306464c3cf1f6f8326ed685b57f4ec.

Boundaries and deviations:
- No protocol or schema change; no dependency install on ECS was needed.
- No OL deployment and no Edge installer/package/signing/release.
- No real Feishu approval click or real Facebook comment submission was manufactured during deployment.
  Runtime acceptance remains to be observed on the next genuine approval/comment task.
- DEV still runs the documented aidcp-cloud.service monolith. This incident change keeps the approval authority
  as an injected port and does not activate or migrate the three-process service topology.
-->
