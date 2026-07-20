## 1. aidcp-cloud — 启动恢复与账本分流

- [x] 1.1 为 PostgreSQL 与内存 DelegatedTaskStore 增加一次性 interrupted-claim 恢复接口，并写稳定恢复事件
- [x] 1.2 在 DelegatedTaskWorker 启动前调用恢复接口，记录恢复数量且禁止运行中重复恢复
- [x] 1.3 对 `prepared` 未派发 attempt 撤销临时账本并归还预算，对 `dispatched` 继续走既有结果未知对账
- [x] 1.4 覆盖普通、暂停、取消与截止任务的恢复状态，保证不残留 ownership 或静默卡死

## 2. aidcp-cloud — 回归测试

- [x] 2.1 Store 测试覆盖 planning/executing 原子恢复、claim 清理、事件与非目标状态不变
- [x] 2.2 Worker 测试覆盖 prepared 安全重排、dispatched 诚实终结、同源新任务随后可起跑
- [x] 2.3 Server 装配测试或等价结构断言覆盖恢复完成后才启动 pump

## 3. aidcp-console — 暂缓原因展示

- [x] 3.1 为稳定 currentStep 增加窄中文映射，未知码不猜测
- [x] 3.2 将 `nextEligibleAt` 文案改为“预计再次检查”，并在排队卡展示等待原因
- [x] 3.3 页面测试覆盖 waiting_ownership、waiting_safe_slot 与未知步骤

## 4. 验证与集成

- [x] 4.1 cloud 运行委托/发布 acceptance、全量测试与 typecheck
  <!-- aidcp-cloud：相关 29/29；acceptance 59/59；rebase 后全量 2651 tests / 0 fail；时间戳类型热修后全量 2652 tests、2644 pass / 8 gated skip / 0 fail；typecheck pass。真实 dev PostgreSQL 用 PREPARE/DEALLOCATE 完成恢复 SQL 解析与类型检查，未执行、未改数据。 -->
- [x] 4.2 console 运行定向测试、全量测试、typecheck 与 build
  <!-- aidcp-console worktree：ContentPage 29/29；FacebookSearchConfig 8/8；最终单 worker 全量 208 pass / 1 skip / 0 fail；typecheck + vite build pass。仓库无 lockfile，依赖隔离安装使用 npm install --prefer-offline --no-package-lock；默认并发全量曾有 3 个既有图片压缩等待测试超时，定向与串行全量复跑全绿。 -->
- [x] 4.3 `openspec validate recover-stale-delegated-executions --strict`
  <!-- strict validation passed 2026-07-20. -->
- [x] 4.4 分别提交 cloud、console 与 control OpenSpec，rebase 最新默认分支后 fast-forward 推送
  <!-- cloud master：92d08a5（恢复实现）+ 1710f9c（timestamptz 热修）；console master：3e35e4d；control main：5fb32b4，均 fast-forward 推送。 -->

## 5. dev 部署与运行态验收

- [x] 5.1 部署前复核 dev 目标与并发部署状态，备份 cloud/env 与 console
  <!-- scripts/deploy-target dev --check 通过；部署前旧任务 8c590fc7/40f75690 的 claim 已于 2026-07-19 过期但仍 executing。备份：dev:/opt/aidcp/cloud.bak.20260720-121747.recover-stale-delegated-executions.tar.gz 与 console.bak.20260720-121747.recover-stale-delegated-executions.tar.gz。 -->
- [x] 5.2 从干净默认分支部署 cloud 与 console，重启仅 `aidcp-cloud.service`
  <!-- 从 clean cloud/console master 部署；首次启动暴露 PostgreSQL CASE timestamptz/text 类型错误，立即从上述备份回滚 3 个运行文件并恢复服务。补 1710f9c、完成真实 PG PREPARE 检查后重新部署成功；仅重启 aidcp-cloud.service。Console 静态资源 index-DiQnHyWH.js 已更新。 -->
- [x] 5.3 验证 service、8787、8090、console、PostgreSQL、Feishu 与 isales 隔离
  <!-- aidcp-cloud active/running；8787、8090、8091 监听；直连 /api/health={"ok":true}，Nginx /api/health={"status":"ok"}；console HTTP 200 且加载新文案；PostgreSQL SELECT 通过；Feishu WSClient onReady；四个 isales service 均保持 active/running。 -->
- [x] 5.4 核对旧僵尸 attempt 诚实终结、两条目标新任务解除 `delegated_ownership_busy`，回写 commit/部署/偏差证据
  <!-- 2026-07-20 12:22:20 启动恢复 2 条 interrupted claim；旧 attempt 2 均结算 submitted_unknown，任务失败且不再占 ownership。12:22:30/12:22:40，3f679cfc 与 acdc965c 分别产生 dispatched attempt 1，并同时处于 executing:publish_post，证明不同参照稿并发恢复。 -->
