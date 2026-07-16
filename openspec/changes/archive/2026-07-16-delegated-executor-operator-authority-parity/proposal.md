## Why

委托任务层现在是所有飞书对外写的唯一前门，`/publish`·`/comment` 精确命令也被解析成任务由 worker 执行器代跑。执行器重新实现了命令语义，且在两处跑偏（审计 change 前的设计稿 `docs/design/delegated-command-two-layer-split.md` 记录）：

- **A：精确 `/publish` 丢了操作员全权**。执行器把所有发帖统一走风控强制路径（`triggerDelegated`，非 normal / 超额即 blocked），而同形的 `/comment` 保住了操作员越权（`legacySingle → manualOverride`）。结果：受限 / 当天已发过的账号，运营 `/publish` 走不通、约两次尝试后静默判失败，`/comment` 却照发——`manual-command-override` spec 明写的操作员越权在发帖侧被回归，且与评论行为不对称。
- **B：评论「起跑前触发闸失败」被静默吞**。人设未绑 / 边端离线（永久）/ 联系方式缺 / 非 FB 带 `--join` / FB 未接线等，在异步评论任务起跑前就早退，评论链的结果卡永不触发；委托层又按 silent 入队、终态兜底只认发帖族 → 运营零反馈（踩「绝不静默失败」红线）。

## What Changes

- **A**：给 `PublishScheduler.triggerDelegated` 加 `operatorOverride` 选择器，置 true 时越过风控 status/canDo 闸（等价老 `triggerManual`），但**发布前飞书人审（AC-PUB）仍强制**——越权只越风控/配额，绝不越人审。执行器仅对**精确单命令类**（`source=legacy_command` 且 `manualSingle`）置该标志；自然语言（`feishu`）与结构化（edge/console/api）发帖一律留 `governed`（不置标志），风控闸不放。与评论分支对称，且不扩散到批量 / 异步委托。
- **B**：评论 `not_started`（起跑前触发闸失败）改为**非重试**并携带人类可读文案；委托层终态兜底从「只发帖族」放宽为**评论族起跑前失败也补一张诚实卡**（判据＝终态码 `non_retryable_failure` 且 0 成功，评论链从未起跑、未发结果卡）。**已起跑再失败的评论仍 MUST NOT 补**（评论链已发结果卡，避免双发）。函数 `delegatedPublishOutcomeReceipt` 更名为 `delegatedTaskFailureReceipt`。

## Impact

- `aidcp-cloud`：`publish-agent/publish-scheduler.ts`（operatorOverride）、`delegated-task/executors.ts`（精确类置标志 + 评论 not_started 非重试）、`delegated-task/notification.ts`（兜底放宽 + 更名）、`server.ts`（onTaskUpdated 兜底泛化到评论族）；单测 `delegated-task/{notification,executors}.test.ts`。
- `aidcp`：本 OpenSpec change 记录 `user-delegated-tasks` 契约收紧。
- 不涉及边云协议、command-bridge 动作映射、RoleName 注册、risk-state-machine（风控只读、RiskController 仍是唯一写者）。
- 真机验收：受限账号 `/publish` 仍出草稿+人审卡、人设未绑 `/comment` 收诚实红卡——归簇 86。
