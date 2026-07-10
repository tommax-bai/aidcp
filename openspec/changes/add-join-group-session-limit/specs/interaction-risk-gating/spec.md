## MODIFIED Requirements

### Requirement: 单场会话上限为全局配置（时长 + 互动预算），取代按账号维度

云端的**单场会话上限**——① 单场时长上限（`max_duration_min`）；② 单场互动预算（`likes` / `collects` / `follows` / `searches` / `comments` / `comment_likes` / `join_groups` 七项）——SHALL 为可在管理后台编辑的**全局单例配置**：**无账号维度、无 `default`、无按账号覆盖**，一份配置管所有账号（单行表，参照模型配置单行 `id=1 CHECK` 模式）。运行时——浏览闭环时长解析（疲劳乘子用）、会话监测体到点判定、单场互动预算的初始化 / 重置——MUST 经**无账号参数的全局提供者**（`sessionDurationMs()` / `sessionBudget()`）**每次现读**当前生效值，使管理后台改完即热加载、MUST NOT 需要重启进程。

绝不 brick（never-brick）：当全局配置缺失、或某字段非有限非负整数（时长还需 `>= 1`）时，运行时 MUST 逐项回落代码写死默认（时长 `10` 分钟；互动预算 `likes:10` / `collects:5` / `follows:3` / `searches:5` / `comments:2` / `comment_likes:3` / `join_groups:1`），MUST NOT 抛错、MUST NOT 让浏览闭环崩溃。配置表为空（如迁移刚跑完）时行为 MUST 与回落默认逐位一致。会话内的「已发生计数 = 初始预算 − 当前剩余」比率闸 MUST 以会话开始时的预算快照为 `init`，会话中途的配置改动 MUST NOT 影响本场已在进行的比率闸（新值于下一场会话生效）。

Facebook 加群调度在执行真实 `join_group` 前 MUST 同时检查每日/minute/hour 风控配额与单场 `join_groups` 剩余预算；当单场 `join_groups` 剩余为 0 时，MUST 不下发 edge `group.join`，MUST 记录可审计的非成功结果，MUST NOT 写入 membership `joined_at`，MUST NOT 记录 `join_group` 成功风控事件。单场 `join_groups` 只在 judgment-confirmed `joined` 且 edge 执行成功后扣减；`already_member`、`gated`、`pending`、shadow、登录/验证码阻断、导航失败、执行失败或不确定结果 MUST NOT 扣减。

单场会话上限的存储与编辑 MUST 只写自己的单行表、MUST NOT 经由风控状态单写路径（`RiskController.setQuotaLevel` / `applySignal` / 状态机 / `risk_state` 表），MUST 仅作只读读取、MUST NOT 改写账号风控终态或档位。本能力 MUST NOT 经 WebSocket 协议 v2。

**取代说明**：本要求**取代**先前由 `session-limits-to-quota-layer` 引入的「单场会话上限可在管理后台**按账号**配置」要求——账号维度被取消（设计决策 2026-06-24「按账号」→ 2026-06-27「全局通用」翻转）；现有 `account_id='default'` 行的值经前向迁移搬成全局行，已设的 30min 保留生效、零数据丢失。归档协调见本 change 的 design.md。

#### Scenario: 后台改全局单场时长，所有账号下场即按新值

- **WHEN** 管理后台把全局 `max_duration_min` 从 10 改为 30 并保存成功
- **THEN** 无需重启，**所有账号**下一场会话的时长上限按 30 分钟生效（疲劳乘子与会话监测体到点判定均现读新全局值），不再有按账号差异、也不再回落写死 10min

#### Scenario: 后台改全局某项互动预算，所有账号下场即按新值

- **WHEN** 管理后台把全局单场 `likes` 预算从 10 改为 6 并保存成功
- **THEN** 无需重启，**所有账号**下一场会话 reset 后的点赞预算为 6，预算耗尽即不再下发点赞

#### Scenario: 后台改全局加群预算，所有账号下场即按新值

- **WHEN** 管理后台把全局单场 `join_groups` 预算从 1 改为 2 并保存成功
- **THEN** 无需重启，**所有账号**下一场会话 reset 后的加群预算为 2，预算耗尽即不再下发真实加群

#### Scenario: 全局配置缺失 / 非法值回落写死默认、绝不 brick

- **WHEN** 全局单场上限配置缺失（表空），或某字段为非有限非负整数（或时长 < 1）
- **THEN** 运行时逐项回落写死默认（时长 10min、预算 `likes:10/collects:5/follows:3/searches:5/comments:2/comment_likes:3/join_groups:1`），不抛错，浏览闭环照常驱动

#### Scenario: 会话中途改预算不动本场比率闸

- **WHEN** 某场会话进行中，管理后台改了全局单场 `likes` 预算
- **THEN** 本场会话的「已发生点赞 = 初始预算 − 当前剩余」仍以本场开始时的初始预算为基准计算，不被中途改动扰动；新值于下一场会话生效

#### Scenario: 单场加群预算耗尽不下发真实加群

- **WHEN** 某账号当前会话的 `join_groups` 剩余预算为 0，且每日/minute/hour `join_group` 配额仍未耗尽
- **THEN** Facebook 加群调度 MUST 不下发 edge `group.join`，并返回/记录单场预算耗尽的非成功结果

#### Scenario: 只有确认成功加群扣减单场加群预算

- **WHEN** Facebook 加群尝试返回 `joined` 且 edge 执行成功
- **THEN** 当前会话 `join_groups` 剩余预算扣减 1
- **AND** `already_member`、`gated`、`pending`、shadow、失败或不确定结果不扣减该预算

#### Scenario: 改单场上限不改风控状态

- **WHEN** 管理后台保存新的全局单场时长 / 互动预算
- **THEN** 仅写单场上限单行表，账号风控终态（`normal` / `warned` / `restricted` / `frozen`）与档位 `quotaLevel` MUST 不被改变，风控状态仍仅由 `RiskController` 单写
