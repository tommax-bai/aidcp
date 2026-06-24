## ADDED Requirements

### Requirement: 单场会话上限（时长 + 互动预算）可在管理后台按账号配置且运行时每次现读

云端的**单场会话上限**——① 单场时长上限（`max_duration_min`）；② 单场互动预算（`likes` / `collects` / `follows` / `searches` / `comments` / `comment_likes` 六项）——SHALL 为可配置、可在管理后台**按账号**编辑。云端 SHALL 把这些数字落库（新增 `session_config` 表，迁移 `0015`，主键 `account_id`，含 `max_duration_min` 与六个 `budget_*` 列）并维护内存镜像。浏览闭环调度器的时长解析（疲劳乘子用）、会话监测体的到点判定、以及单场互动预算的初始化 / 重置 MUST 经注入的**按账号提供者**（`sessionDurationMsFor(accountId)` / `sessionBudgetFor(accountId)`）**每次现读**当前生效值，使管理后台改完即热加载、MUST NOT 需要重启进程。

绝不 brick（never-brick）：当提供者缺失、账号缺行、或某字段非有限非负整数（时长还需 `>= 1`）时，运行时 MUST 逐项回落代码写死默认（时长 `10` 分钟；互动预算 `likes:10` / `collects:5` / `follows:3` / `searches:5` / `comments:2` / `comment_likes:3`），MUST NOT 抛错、MUST NOT 让浏览闭环崩溃。`session_config` 表为空（如迁移刚跑完）时行为 MUST 与现状逐位一致（严格零回归）。会话内的「已发生计数 = 初始预算 − 当前剩余」比率闸 MUST 以会话开始时的预算快照为 `init`，会话中途的配置改动 MUST NOT 影响本场已在进行的比率闸（新值于下一场会话生效）。

#### Scenario: 后台改某账号单场时长，下一场会话即按新值

- **WHEN** 管理后台把某账号的 `max_duration_min` 从 10 改为 20 并保存成功
- **THEN** 无需重启，该账号下一次会话的时长上限按 20 分钟生效（疲劳乘子与会话监测体到点判定均现读新值）

#### Scenario: 后台改某账号某项互动预算，下一场会话即按新值

- **WHEN** 管理后台把某账号的单场 `likes` 预算从 10 改为 6 并保存成功
- **THEN** 无需重启，该账号下一场会话 reset 后的点赞预算为 6，预算耗尽即不再下发点赞

#### Scenario: 账号缺行 / 非法值回落写死默认、绝不 brick

- **WHEN** 某账号在 `session_config` 缺行，或其某字段为非有限非负整数
- **THEN** 运行时对该账号 / 该字段回落写死默认（时长 10min、预算 `freshBudget` 数字），不抛错，浏览闭环照常驱动

#### Scenario: 配置表为空时与现状逐位一致

- **WHEN** `session_config` 表无任何行（如迁移刚跑完）
- **THEN** 任意账号的单场时长 = 10min、单场互动预算 = `{likes:10,collects:5,follows:3,searches:5,comments:2,comment_likes:3}`，与改造前逐位相同

#### Scenario: 会话中途改预算不动本场比率闸

- **WHEN** 某场会话进行中，管理后台改了该账号的单场 `likes` 预算
- **THEN** 本场会话的「已发生点赞 = 初始预算 − 当前剩余」仍以本场开始时的初始预算为基准计算，不被中途改动扰动；新值于下一场会话生效

### Requirement: 单场会话上限的存储与编辑绝不触碰风控状态单写路径

单场会话上限的存储与编辑 MUST 只写 `session_config` 表，MUST NOT 经由风控状态单写路径（`RiskController.setQuotaLevel` / `applySignal` / 状态机 / `risk_state` 表）。注入的单场上限提供者 MUST 仅作只读读取，MUST NOT 写入或改变账号风控终态（`normal` / `warned` / `restricted` / `frozen`）或档位 `quotaLevel`。账号风控终态 MUST 仍仅由云端 `RiskController` 单写（既有不变量不被本配置通道动摇）。本能力 MUST NOT 经 WebSocket 协议 v2（不动两份 `protocol.ts` / `command-bridge.ts` / `docs/protocol.md`）。

#### Scenario: 改单场上限不改风控状态

- **WHEN** 管理后台保存新的单场时长 / 互动预算
- **THEN** 写操作只落 `session_config` 表，归属账号的 `risk_state`（status 与 quotaLevel）不被改写，`setQuotaLevel` / `applySignal` 不被调用

#### Scenario: 提供者只读、不写状态

- **WHEN** 调度器 / 会话监测体经提供者读取单场上限
- **THEN** 该读取不触发任何状态迁移 / 持久化写、不经协议下发，风控终态单写路径不受影响

### Requirement: 单场会话上限不再来自人设

单场会话上限的运行时来源 SHALL 唯一为安全限额层（`session_config` 表 + 提供者，缺值回落写死默认）。人设（`Soul`）MUST NOT 再承载 `session_limits`——`src/soul/types.ts` 的 `session_limits` 字段、`src/soul/loader.ts` 的 `parseSessionLimits` 校验、`src/soul/soul.yaml` 的对应段 SHALL 被移除。移除 MUST 在确认运行时已无任何 `soul.session_limits` 读取后进行（`grep -rn "session_limits" src/` 仅余历史定义、无运行时读点）。管理后台人设页 MUST NOT 展示或提供 `session_limits` 的编辑入口（消除「能改却无效」的误导）。人设此后只承载身份 / 兴趣 / 行为偏好。

#### Scenario: 时长解析不再读人设

- **WHEN** 浏览闭环调度器与会话监测体解析单场时长上限
- **THEN** 取值来自注入的单场上限提供者（按当前账号），不再读取 `soul.session_limits.max_duration_min`；提供者缺失时回落写死默认 10min

#### Scenario: 人设不再含 session_limits

- **WHEN** 加载任意账号人设
- **THEN** `Soul` 不含 `session_limits` 字段，人设加载器不解析该段，人设页不展示该编辑区，且运行时无任何 `soul.session_limits` 读取

#### Scenario: 删除前无残留读点

- **WHEN** 准备从人设删除 `session_limits`
- **THEN** 全部单场时长读点已迁至提供者，`grep -rn "session_limits" src/` 无运行时读取，删除后浏览闭环不 brick（回落写死默认）
