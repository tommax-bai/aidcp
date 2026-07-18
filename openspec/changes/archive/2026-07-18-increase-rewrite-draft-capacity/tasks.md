## 1. OpenSpec 与并发门禁

- [x] 1.1 校验 `publish-generation-concurrency` delta：普通稿账号单飞 1、洗稿空闲时并发 3、账号在途默认 20。 <!-- openspec validate increase-rewrite-draft-capacity --strict passed -->
- [x] 1.2 复核 `publish-claim-reject-defer-not-fail` 与 `publish-trigger-and-apply` 无实际 scheduler 写者，并记录本 change 先串行落地。 <!-- 2026-07-18: openspec list + aidcp-cloud worktree/branch audit; no active implementation worktree/branch -->

## 2. aidcp-cloud 容量默认值

- [x] 2.1 将 `PublishScheduler` 的 `pendingCapPerAccount` 缺省值从 3 调为 20、`maxConcurrentRuns` 缺省值从 2 调为 3，并同步注释。 <!-- aidcp-cloud aa8b43e -->
- [x] 2.2 将 `server.ts` 的 `AIDCP_PUBLISH_PENDING_CAP_PER_ACCOUNT` 回落值改为 20、`AIDCP_PUBLISH_MAX_CONCURRENT_RUNS` 回落值改为 3。 <!-- aidcp-cloud aa8b43e -->

## 3. 回归测试

- [x] 3.1 新增默认值回归：三篇不同来源洗稿同时放行、第四篇 `publish_busy`。 <!-- aidcp-cloud aa8b43e; focused scheduler 21/21 -->
- [x] 3.2 新增组合回归：提高全局帽后，同账号普通稿仍单飞；普通稿占槽时洗稿与其共享总帽。 <!-- aidcp-cloud aa8b43e -->
- [x] 3.3 运行聚焦 scheduler 测试、`npm run test:acceptance`、`npm test` 与 `npm run typecheck`。 <!-- focused 21/21; acceptance 56/56; Windows npm glob returned 0 so reran all 275 test files in 7 explicit batches: pass; typecheck pass -->

## 4. 集成与部署

- [x] 4.1 提交 `aidcp-cloud` change 分支并用 `scripts/land-change aidcp-cloud increase-rewrite-draft-capacity --yes` 串行集成、推送默认分支。 <!-- aidcp-cloud a38bcfb on origin/master; land-change acceptance 56/56 + typecheck pass; npm glob limitation covered by prior explicit 275-file run -->
- [x] 4.2 按安全序列部署 dev，确认服务、监听、健康检查、飞书与 PostgreSQL 正常，并记录部署 SHA。 <!-- dev deployed aidcp-cloud a38bcfb; backup /opt/aidcp/cloud.bak.20260718-162421.tar.gz + env backup; active; 8787+8090; panel health ok; PG select 1; Feishu WS onReady -->
- [x] 4.3 更新任务证据，运行 `openspec validate increase-rewrite-draft-capacity --strict`。 <!-- strict validation passed after dev deployment evidence was recorded -->
- [x] 4.4 使用显式 pathspec 提交并推送控制仓 OpenSpec change。 <!-- aidcp 8cb7c95 on origin/main; unrelated untracked files preserved -->
