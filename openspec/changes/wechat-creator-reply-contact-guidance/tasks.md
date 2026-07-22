## 1. Cloud reply composition

- [x] 1.1 Make `reply_polisher` use a role-specific generic creator prompt with short, friendly, non-merchant boundaries.
- [x] 1.2 Inject existing account contact info into `{{support_channel}}` only when the published template explicitly uses it.
- [x] 1.3 Protect every rendered support-channel line and fall back to the deterministic template when AI changes one.
- [x] 1.4 Replace merchant-oriented static preview fixtures with generic creator interaction examples.

## 2. Verification

- [x] 2.1 Add focused tests for prompt wording, contact precedence/fallback/no-read behavior, and protected-line fallback.
- [x] 2.2 Run focused Cloud tests, the full Cloud suite, typecheck, and strict OpenSpec validation.

<!-- Implementation: aidcp-cloud master commit 0025f1e; control artifacts landed through 08525f5. Validation: focused reply tests 17/17, reply plus role-preview tests 45/45, post-rebase full Cloud suite 2792 tests (2784 pass, 8 environment-gated skip, 0 fail), npm run typecheck pass, and openspec validate --strict pass. No package or migration changes. -->

## 3. Delivery

- [x] 3.1 Commit the Cloud and control-repo changes with validation evidence, then integrate and push their default branches.
- [x] 3.2 Deploy the clean Cloud `master` revision to `dev` and verify service, health, logs, and unchanged configuration/contact row counts.

<!-- Dev deployment 2026-07-22: deployed aidcp-cloud master 0025f1e from the clean canonical checkout after target preflight. Backup: /opt/aidcp/cloud.bak.20260722-030146Z.tar.gz plus target-local .env backup. The four changed runtime source hashes matched local; aidcp-cloud.service is active with NRestarts=0; 8787/8090/8091 listen; panel and customer-auth health return ok; PostgreSQL SELECT 1 passes; Feishu WSClient reached onReady; isales-api and isales-scheduler remain active. Pre/post counts stayed contact_nonblank=9, reply_scopes=0, published_scopes=0, legacy_reply_configs=0. No real reply/write probe ran, and no template or account contact was changed. -->
