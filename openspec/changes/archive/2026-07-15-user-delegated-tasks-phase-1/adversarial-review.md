# Adversarial review — user-delegated-tasks-phase-1

Date: 2026-07-15

## Verdict

初稿存在 3 个 BLOCKER 与 4 个 HIGH；均已回写 proposal/design/specs/tasks。修订后无阻塞实施项，可以进入 apply。并行 `lease-strict-preemption` 热点继续列为不可触碰边界。

## Findings and resolutions

1. **BLOCKER — 旧 `/publish`、`/comment` 直跑与“公共写操作先确认”冲突。** 初稿把“兼容”误解成保留副作用路径。修订为：语法/昵称/单次人工语义兼容，但写命令先生成 target=1 确认任务；确认后才调用既有 scheduler。
2. **BLOCKER — PG claim 只能防双 worker，不能防“平台成功后、task 记账前崩溃”的重复提交。** 新增 dispatch 前 attempt ledger 和重启 reconciliation；结果未知禁止同目标自动重试。
3. **BLOCKER — 用户明确要求 Facebook 群组相关任务，但动作目录只写了配置范围评论。** 新增 Facebook 群组任务 adapter/规格/测试，限定既有目标与成员账本，不扩大群发现或全站搜索。
4. **HIGH — waiting_approval 若既占 edge 又无限占 ownership，会阻塞且无法解释。** 修订为不占 edge 租约，但保留同用途草稿/去重 ownership；deadline 不自动批准、删除或提交候选。
5. **HIGH — cloud 先改 curated API、console 后发会让旧 UI 把 task draft 染绿。** 迁移改为兼容响应 + cloud/console 同一 dev 发布窗口切换。
6. **HIGH — “优先执行”可能被误映射为 human，撞正在输入的动作。** 固定异步委托 edge priority=`automatic`；优先只影响 DelegatedTask 队列排序。
7. **HIGH — Facebook 源码存在可能被当作已交付。** 保留 registry beta/runtime gate、真机 backlog 与“Edge 安装端未发布”硬提示；今日灵感和任意 URL 明确 unsupported。

## Lenses exercised

- 安全/诚实：manualOverride、提交未知、平台成功证据、RiskController 单写者。
- 并发/恢复：claim、attempt、重启 reconciliation、scheduler ownership、waiting approval。
- 平台边界：account platform 事实源、XHS 正式、Facebook Beta 与群组范围。
- 入口 UX：Feishu/Edge/console 同一确认模型、旧命令语法兼容、触发态不冒充终态。

## Implementation follow-up

- 初版“今日灵感”只携带来源标签，不能证明素材来自今天。实现评审中补为按 Asia/Shanghai 当日起点过滤精选来源；当日无素材时返回 `today_inspiration_unavailable`，不调用发布编排器。
- 初版自然语言识别会把普通问候误判为委托任务。回归测试发现后收窄 business-goal 入口，`你好` 等继续走既有 help 路径。
- 旧精选内容测试仍断言点击即触发 scheduler。迁移为断言只创建 `awaiting_confirmation` 且零写副作用，避免兼容响应把“已受理”伪装成“已完成”。
