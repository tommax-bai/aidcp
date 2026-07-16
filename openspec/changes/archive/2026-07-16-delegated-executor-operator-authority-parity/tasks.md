# Tasks — delegated-executor-operator-authority-parity

## 1. aidcp-cloud — A：精确 /publish 恢复操作员全权

- [x] `triggerDelegated` 加 `operatorOverride` 选择器，置 true 时越风控 status/canDo、保人审 <!-- aidcp-cloud b78a27f publish-scheduler.ts -->
- [x] 执行器仅对精确类（`source=legacy_command && manualSingle`）置 `operatorOverride`；NL/结构化留 governed <!-- aidcp-cloud b78a27f executors.ts + DelegatedPublishPort 类型 -->
- [x] 单测：执行器仅精确类透传 operatorOverride，NL(feishu)/结构化(edge) 均不置 <!-- aidcp-cloud b78a27f executors.test.ts -->

## 2. aidcp-cloud — B：评论起跑前触发闸失败诚实兜底

- [x] `awaitComment` 的 `not_started` 改非重试并携带人类文案（起跑前失败＝永久配置问题） <!-- aidcp-cloud b78a27f executors.ts -->
- [x] `delegatedPublishOutcomeReceipt` → `delegatedTaskFailureReceipt`，放宽为评论族起跑前失败兜底（code `non_retryable_failure` && 0 成功），起跑后失败不补 <!-- aidcp-cloud b78a27f notification.ts -->
- [x] `server.ts` onTaskUpdated 兜底泛化到评论族（卡标签按 actionFamily 取「评论」/「发帖」），沿用 originChatId→团队路由 <!-- aidcp-cloud b78a27f server.ts -->
- [x] 单测：评论起跑前失败→红卡；起跑后失败(max_attempts)→null（不双发） <!-- aidcp-cloud b78a27f notification.test.ts -->

## 3. 回归与验收

- [x] `npm run typecheck` 通过 <!-- aidcp-cloud b78a27f -->
- [x] `npm run test:acceptance` 通过（AC-PUB/AC-RISK 红线绿）54/54 <!-- aidcp-cloud b78a27f -->
- [x] `npm test` 全量通过 2272 pass / 0 fail <!-- aidcp-cloud b78a27f -->
- [x] 部署 dev <!-- 2026-07-16 deployed (cloud 6413a6a) -->
- [ ] 真机验收（受限账号 /publish 仍出草稿+人审卡；人设未绑 /comment 收诚实红卡）→ 簇 86
