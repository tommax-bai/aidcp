## 1. Contract

- [x] 1.1 Update `curated-note-actions` so targeted title search does not send native filter parameters.

## 2. Implementation

- [x] 2.1 Cloud: omit `sort`/`timeWindow` for targeted curated-note comment searches. <!-- aidcp-cloud e6292a0 -->
- [x] 2.2 Edge: treat `comprehensive`/`all` as no-op success in `applySearchFilters`. <!-- aidcp-edge 67069e6 -->

## 3. Validation

- [x] 3.1 Run focused cloud and edge tests. <!-- cloud: npx tsx --test test/comment-agent/comment-scheduler-targeted.test.ts; npx tsx --test test/**/*.test.ts; npm run test:acceptance; npm run typecheck. edge: npm test -- --test-name-pattern=search-handler; npm run test:acceptance; npm run typecheck; npm run build:dist. -->
- [x] 3.2 Run `openspec validate skip-targeted-search-filters --strict`. <!-- valid -->

## 4. Deployment

- [x] 4.1 Deploy `aidcp-cloud` e6292a0 to ECS `121.89.85.150:/opt/aidcp/cloud`. <!-- backup: /opt/aidcp/cloud.bak.20260705-110839.tar.gz and /opt/aidcp/cloud/.env.bak.20260705-110839; health: service active, :8787 listening, Feishu WS ready, PG select 1 ok. -->
