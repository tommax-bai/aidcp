## 1. Development Boundary

- [x] 1.1 Inject the exact unverified-write token only for unpackaged `wechat_channels` children connected to the named `dev` Cloud environment.
- [x] 1.2 Parse and diagnose the dev override without changing packaged/non-dev defaults.

## 2. Capability and Candidate Requests

- [x] 2.1 Let the dev override bypass comment/DM per-channel Cloud write booleans and write-probe evidence while retaining scoped controls, auth, read, kill, and circuit gates.
- [x] 2.2 Add separately labeled candidate descriptors and strict dev-only serialization for comment create and DM text send.
- [x] 2.3 Align candidate request payloads with the current first-party bundle, resolving DM peer identity before dispatch.
- [x] 2.4 Parse channel-specific platform acknowledgements and retain failed/ambiguous/idempotent result semantics.
- [x] 2.5 Let the existing Cloud global write switch admit the pre-0046 schema only under `AIDCP_DEPLOY_ENV=dev`; for reviewed dev sends bypass login cooldown and quota-only denial without another token, shared quota write, migration 0046, or weaker legacy idempotency uniqueness.
- [x] 2.6 Show Cloud-local rate admission separately from a real WeChat platform rate-limit response.

## 3. Verification and Closeout

- [x] 3.1 Add focused feature-flag, probe, descriptor, API, ack, reply-sender, Electron injection, Cloud schema-capability, and dev-boundary tests.
- [x] 3.2 Run focused tests, Edge acceptance/full tests, typecheck, and distribution build without installing dependencies or building an installer.
- [x] 3.3 Integrate and push Edge and Cloud master, deploy only Cloud dev, restart only the local unpackaged dev client/core as needed, and verify the named account reports both text-write capabilities true from direct Cloud controls.
- [x] 3.4 Record exact commits, validation, runtime evidence, and deviations; run `openspec validate wechat-dev-write-test-override --strict` and push the control change.

## Evidence

- Edge master: `be68b36`, `fc06f3a`, and `ee85739`; Cloud master: `d3b740e` and `8746449`.
- Edge focused workspace test: 41/41; acceptance: 25/25; full: 1824/1824; typecheck passed. Earlier integrated Edge verification also passed distribution build without producing an installer.
- Cloud focused interaction tests: 21/21; acceptance: 57/57; full: 2524 total, 2516 passed, 8 gated skips, 0 failed; typecheck and build passed.
- Cloud dev startup: `schema=legacy_read_only environment=dev configured=true effective=true dev_quota_bypass=true`; migration 0046 remained unapplied and shared idempotency uniqueness remained unchanged.
- Edge runtime received `comment_write=true dm_write=true`; stored auth reported both reply capabilities true.
- Direct customer `send` was invoked once for approved DM job `job_231dffb0-1c16-4b05-8ec8-4f2707af2d1d`. Attempt `attempt_d200bc1d-999b-43b7-8a99-fa569e6bce96` reached `confirmed` with platform server message id `3719969366743649367`; the job reached `sent` without retry.
- Dev backups: `/opt/aidcp/cloud.bak.20260719-005308.wechat-dev-write-test-override.tar.gz` and `/opt/aidcp/cloud.bak.20260719-011112.wechat-dev-write-test-override.tar.gz`, with matching `.env.bak` files. Health passed for service, 8787/8090/8091, PostgreSQL, and Feishu WS.
- Deviation: Windows had no `rsync` or installed WSL. Deployment used a clean canonical `git archive` snapshot, exact two-file staged SCP, pre-install SHA-256 comparison, backup, scoped install, restart, and post-install SHA-256/health verification; no dependency or environment installation was performed.
