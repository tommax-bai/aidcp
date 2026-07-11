# Tasks: 移除精选页空正文清理入口

## 1. OpenSpec

- [x] 1.1 增加 spec delta，明确精选内容前端不展示空正文清理入口，后端应急接口可保留。 <!-- aidcp remove-curated-empty-cleanup-panel proposal/tasks + panel-curated-content delta -->
- [x] 1.2 `openspec validate remove-curated-empty-cleanup-panel --strict` 通过。 <!-- 2026-07-04 strict valid -->

## 2. aidcp-console

- [x] 2.1 移除 `CuratedContentPage` 中的清理 mutation、预估数和“历史清理”卡片。 <!-- aidcp-console 42119e0 src/pages/CuratedContentPage.tsx; rebased over 55968e7 read-to-write-note-lane and kept write-note actions -->
- [x] 2.2 增加/更新前端测试，断言页面不渲染清理入口且不调用清理接口。 <!-- aidcp-console 42119e0 src/pages/CuratedContentPage.test.tsx -->
- [x] 2.3 运行相关测试、typecheck、build。 <!-- passed after rebase: npx vitest run src/pages/CuratedContentPage.test.tsx (7 pass, existing jsdom getComputedStyle warnings); npm run typecheck; npm run build -> assets/index-zLJqBYQx.js -->

## 3. 发布

- [x] 3.1 推送 control/console 变更。 <!-- aidcp-console 42119e0 pushed to origin/master; aidcp control record pushed with this change -->
- [x] 3.2 部署 console 静态产物并完成线上健康检查。 <!-- 2026-07-04 22:08 CST deployed /tmp/aidcp-console-42119e0-dist.tar to /opt/aidcp/console; backup /opt/aidcp/console.bak.20260704-220806.tar.gz; HTTP 200; index references assets/index-zLJqBYQx.js; cleanup entry strings absent; write-note string present -->
