# Tasks — delegated-approvalmode-clamp

## 1. aidcp-cloud — 客户端 approvalMode 收口

- [x] 新增 `clampClientApprovalMode(mode)`：undefined→undefined、draft_only→draft_only、其余（含 auto_approve）→review <!-- aidcp-cloud 6413a6a delegated-task/types.ts -->
- [x] 面板建草稿路由 `/api/delegated-tasks/draft` 应用收口 <!-- aidcp-cloud 6413a6a panel/panel-server.ts -->
- [x] 客户端建草稿路由 `/delegated-tasks/draft` 应用收口 <!-- aidcp-cloud 6413a6a client-auth/client-auth-server.ts -->
- [x] 单测：auto_approve/未知→review，保留 review/draft_only，undefined 交默认 <!-- aidcp-cloud 6413a6a delegated-task/types.test.ts -->

## 2. 回归与验收

- [x] `npm run typecheck` 通过 <!-- aidcp-cloud 6413a6a -->
- [x] `npm run test:acceptance` 通过 54/54 <!-- aidcp-cloud 6413a6a -->
- [x] `npm test` 全量通过 2272 pass / 0 fail <!-- aidcp-cloud 6413a6a -->
- [ ] 部署 dev <!-- pending -->
- [ ] 真机验收（结构化 draft 带 auto_approve → 不写审批信号、无免审直发）→ 簇 86
