## 1. Control Repo Artifacts

- [x] 1.1 Confirm active OpenSpec context and keep the change scoped to `platform-abstraction-layer`.
  <!-- control: implemented on matching codex/platform-abstraction-layer branches/worktrees in aidcp-edge and aidcp-cloud; Facebook probing changes remain separate. -->
- [x] 1.2 Update architecture/protocol docs only where platform abstraction contracts need to be described; do not change protocol counts unless implementation proves a synchronized type-only extension is required.
  <!-- control: docs/protocol.md documents hello.platform as a type-only payload extension; protocol message count remains 57. docs/architecture.md aligned stale count text to 57. -->

## 2. Edge Platform Driver Extraction

- [x] 2.1 Create edge `src/platform/driver.ts` with `PlatformDriver`, capability types, `PlatformId`, and honest unsupported-capability errors.
  <!-- aidcp-edge 49a980a: added platform driver contract, capability guard, platform normalization, and recognized-but-unimplemented facebook failure. -->
- [x] 2.2 Extract existing xhs browse/comment/publish/interact/patrol page-specific logic into `src/xhs/*` while keeping shared CDP, locating, humanize, anti-detection, and browser-provider modules outside the xhs tree.
  <!-- aidcp-edge 49a980a: xhs driver wraps existing identity and overlay implementations; shared CDP/browse modules remain in existing shared folders. -->
- [x] 2.3 Wire `AIDCP_PLATFORM` or equivalent startup config so unset/default selects `xiaohongshu` and unsupported platform values fail honestly.
  <!-- aidcp-edge 49a980a: main.ts selects platform driver from AIDCP_PLATFORM; default/xhs aliases resolve to xiaohongshu; facebook is recognized but rejected until a driver exists. -->
- [x] 2.4 Add edge hello/platform metadata and startup logs without changing xhs behavior.
  <!-- aidcp-edge 49a980a: hello payload includes platform; startup logs selected platform/app/capabilities; xhs app/capability values remain unchanged. -->
- [x] 2.5 Add focused edge tests for driver selection, xhs default behavior, unsupported capability failure, and shared-core non-duplication.
  <!-- aidcp-edge 49a980a: test/platform/driver.test.ts plus hello/startUrl coverage in existing client/provider tests. -->

## 3. Cloud Platform Registry

- [x] 3.1 Add account-store APIs for `getPlatform(accountId)` and `listByPlatform(platform)` with cache behavior aligned to existing account accessors.
  <!-- aidcp-cloud 0c353bb: accounts.platform DDL default xiaohongshu; init prewarms platform cache; getPlatform/listByPlatform added and tested. -->
- [x] 3.2 Upgrade comment platform profile lookup into a keyed registry with xhs defaults matching current prompts and limits.
  <!-- aidcp-cloud 0c353bb: XHS_COMMENT_PROFILE keeps current site/content labels, 50 char limit, search defaults, and targeted search limits. -->
- [x] 3.3 Add cloud `PLATFORM_REGISTRY` skeleton with xhs entry and capability/scheduler metadata, without changing current xhs orchestration.
  <!-- aidcp-cloud 0c353bb: registry contains xiaohongshu entry only; recognized facebook has no registry entry and fails honestly. -->
- [x] 3.4 Inject platform profile into command-style comment roles and scheduler paths while preserving current xhs output.
  <!-- aidcp-cloud 0c353bb: generator/picker/composer/scheduler accept platform profile; default xhs prompt still contains 50 字以内 and 最近一天·最多收藏. -->
- [x] 3.5 Validate edge platform metadata against `accounts.platform` before routing account work to an edge.
  <!-- aidcp-cloud 0c353bb: handshake rejects unsupported platform and platform_mismatch before creating/replacing runtime; mismatch does not evict an existing healthy same-edge connection. -->

## 4. Cross-Repo Validation

- [x] 4.1 Run edge acceptance tests relevant to browse/comment/publish/protocol, then edge `npm test` and `npm run typecheck`.
  <!-- aidcp-edge: npm run typecheck passed; targeted tsx tests passed 50/50; npm run test:acceptance passed 13/13 with gated E2E skipped; npm test passed 636/636. -->
- [x] 4.2 Run cloud acceptance tests relevant to protocol/risk/comment/account routing, then cloud `npm test` and `npm run typecheck`.
  <!-- aidcp-cloud: npm run typecheck passed; targeted tsx tests passed 75/75; npm run test:acceptance passed 44/44 with gated E2E skipped; npm test passed 1387/1387. -->
- [x] 4.3 Verify protocol counts and registered runtime behavior remain unchanged for xhs.
  <!-- edge/cloud protocol acceptance both assert message type count 57; hello.platform is payload metadata only. xhs app/capability/default URL/profile defaults remain unchanged. -->
- [x] 4.4 Review the diff to ensure shared foundations were not copied into platform implementation directories.
  <!-- diff review: edge src/xhs only wraps existing shared self-identity and overlay monitor; cloud platform registry holds metadata only. CDP, locating, browser provider, humanize, risk, and scheduler foundations remain shared. -->

## 5. Closeout

- [x] 5.1 Commit sibling repo work on same-name branches/worktrees and record repo commit SHAs plus validation notes in this `tasks.md`.
  <!-- aidcp-edge codex/platform-abstraction-layer 49a980a; aidcp-cloud codex/platform-abstraction-layer 0c353bb. Validation notes recorded in 4.1/4.2. -->
- [x] 5.2 Run `openspec validate platform-abstraction-layer --strict`.
  <!-- control: openspec validate platform-abstraction-layer --strict passed. -->
- [ ] 5.3 Archive only after xhs zero-regression is proven and tasks contain commit/validation notes.
