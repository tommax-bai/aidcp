## ADDED Requirements

### Requirement: 账号级出站目标解析，层叠于默认群兜底之上

系统 SHALL 提供一个账号级飞书目标解析 `resolveChatIdForAccount(accountId?)`，解析顺序为：读该账号的 `accounts.group_label` → 以该团队键查 `group_route` 表得 `chat_id`；命中即返回。命不中时 MUST 落回既有默认群解析链（`bot_chats` 默认群 → `FEISHU_CHAT_ID` → 空串），即 `resolveDefaultChatId` 的现有行为保持不动。**未绑定账号 MUST NOT 被静默丢弃**——一律投递到默认群。当 `group_route` 表为空时，全体账号的投递目标 MUST 与本变更前**逐字一致**（零行为变更）。

#### Scenario: 已绑定账号路由到团队群

- **WHEN** 账号 `acc-1` 的 `group_label` 为 `teamA`，且 `group_route` 存在 `teamA → oc_team_a_chat`
- **THEN** `resolveChatIdForAccount('acc-1')` SHALL 返回 `oc_team_a_chat`
- **AND** 该账号的自主推送投递到 `oc_team_a_chat`，MUST NOT 落默认群

#### Scenario: 未绑定账号落默认群、绝不丢

- **WHEN** 账号 `acc-2` 无 `group_label`，或其 `group_label` 在 `group_route` 无对应行
- **THEN** `resolveChatIdForAccount('acc-2')` SHALL 返回默认群链的结果（默认群 / `FEISHU_CHAT_ID` / 空串）
- **AND** 通知照常尝试投递，MUST NOT 因未绑定而被静默丢弃

#### Scenario: 空表等价于今天行为

- **WHEN** `group_route` 表为空（尚无任何映射）
- **THEN** 所有账号经 `resolveChatIdForAccount` 得到的目标 SHALL 与直接调用 `resolveDefaultChatId` 一致
- **AND** 系统整体投递行为与本变更前逐字一致

### Requirement: 逐层读容错，异常绝不外溢投递闭包

目标解析涉及的每一次读（`getGroupLabel`、`group_route` 查询）MUST 各自被 try/catch 包裹，读失败按「无团队路由」向下一层穿透，MUST NOT 把异常抛入调用方的投递闭包。任一层 SELECT 因数据库抖动 / 连接池耗尽而抛出时，解析 MUST 仍返回默认群链结果，使整批通知照常投递、MUST NOT 因异常而被静默作废（异常路径的静默假成功同样是红线）。

#### Scenario: group_route 查询抛错仍落默认群投递

- **WHEN** `group_route` 查询在解析某账号目标时抛出数据库异常
- **THEN** 解析 SHALL 捕获该异常并回落默认群链，返回一个可用 `chat_id`（或诚实空串）
- **AND** 调用方投递闭包照常执行，该批通知 MUST NOT 因解析异常而被整批作废、MUST NOT 无声无息

#### Scenario: group_label 读失败按无路由处理

- **WHEN** `getGroupLabel(accountId)` 因存储不可用而读失败
- **THEN** 解析 SHALL 视其为「无团队路由」并落默认群，MUST NOT 把该错误上抛为投递失败

### Requirement: 配置漏配可观测（有团队键却落默认）

当某账号持**非空** `group_label` 却在 `group_route` 无匹配行（含大小写 / 首尾空白不一致导致的漏配）而落到默认群时，系统 SHALL 输出一条 config-gap 日志，标明该账号与其未命中的团队键。系统 MUST 仍投递到默认群（绝不丢），该日志仅用于让运营发现漏配 / 拼写错配。

#### Scenario: 团队键拼写不一致时打 config-gap 日志

- **WHEN** 账号 `acc-3` 的 `group_label` 为 `TeamA `（尾随空格），而 `group_route` 只有 `teamA`
- **THEN** 系统 SHALL 投递到默认群
- **AND** SHALL 输出一条 config-gap 日志指出 `acc-3` 的团队键 `TeamA ` 未命中任何路由

### Requirement: 账号入站平台通知按账号路由，面向运营方的卡片 / 告警不按账号路由

账号的**入站平台通知**（通知巡视产出的「评论 / @」消息——即各团队要收的"消息"）SHALL 经 `resolveChatIdForAccount` 按其归属账号路由到团队群。**面向运营方**的消息——发布 / 评论审批卡（需运营点按授权）、运维 / 配置 / 验证码告警、排期编排回执、命令结果卡——MUST NOT 走账号→群映射，SHALL 维持既有默认（管理）群 / 源群目标不变。据此，外部客户群按定义**只收账号入站通知、不收审批与运维流量**，且运营从管理群对某账号下命令的结果不会流向该账号团队群。

#### Scenario: 巡视通知走账号团队群

- **WHEN** 账号 `acc-1`（属 `teamA`）的通知巡视产出评论 / @ 通知
- **THEN** 该通知 SHALL 投递到 `teamA` 对应的群

#### Scenario: 审批卡与运维告警不按账号路由

- **WHEN** 系统为账号 `acc-1`（属 `teamA`）发出发布 / 评论审批卡、或该账号相关的 persona / 验证码 / 排期回执告警
- **THEN** 这些消息 MUST NOT 因 `acc-1` 属 `teamA` 而被投递到 `teamA` 群
- **AND** SHALL 维持既有默认（管理）群目标，供运营方处置

### Requirement: 无归属账号的告警落默认群

无法解析出归属账号的告警（如边缘握手被拒的 config-error 告警、无可解析账号的验证码告警）SHALL 投递到默认群，MUST NOT 被丢弃，MUST NOT 为其臆造 / 保留一个账号作用域。

#### Scenario: config-error 告警落默认群

- **WHEN** 边缘握手因缺账号标识被拒而触发 config-error 告警（按定义无 accountId）
- **THEN** 该告警 SHALL 投递到默认群，MUST NOT 被静默吞掉

### Requirement: 路由只按显式绑定精确生效，绝不模糊匹配

一条路由 SHALL 仅当存在显式存储的 `(group_label, chat_id)` 绑定、且账号 `group_label` 与之**精确相等**时生效。系统 MUST NOT 以名称近似 / 模糊匹配 / 自动猜测的方式选择投递目标。未解析出显式目标时一律回落默认群（安全），MUST NOT 回落到任何被猜测的群。此约束的目的是杜绝**映射错群导致的跨客户 PII 泄漏**（一个账号的第三方互动内容进错团队 / 客户群）。

#### Scenario: 无精确绑定时落默认而非猜测

- **WHEN** 某账号的 `group_label` 与任何已存 `group_route` 行都不精确相等
- **THEN** 系统 SHALL 落默认群，MUST NOT 模糊匹配到某个「名字相近」的群

### Requirement: group_route 自愈式 schema 与单写者存储

`group_route` 表 SHALL 在存储初始化 `init()` 中以 `CREATE TABLE IF NOT EXISTS` 幂等自建，并接入云端启动 init 链，MUST NOT 依赖任何独立 migration 执行器（本仓无）。映射写入 SHALL 走单写者路径并返回**读回为真**的结果，能可区分地表达「已写入 / 目标为空清除 / 无效键拒绝」，并记录审计字段（`updated_by` / `updated_at`）。

#### Scenario: 全新库启动即自建表

- **WHEN** 云端在一个尚无 `group_route` 表的数据库上启动
- **THEN** `init()` SHALL 幂等建出该表，随后路由读写可用，MUST NOT 因缺表报错致投递解析崩溃

#### Scenario: 写入返回读回真值

- **WHEN** 运营把 `teamA` 绑定到 `oc_team_a_chat`
- **THEN** 写入 SHALL 返回该绑定的读回结果，而非乐观假定成功

### Requirement: 路由配置面板 API 与机器人所在群清单

面板 SHALL 暴露 `GET/PUT /api/notification/routes` 读写 `group_label→chat` 映射，以及 `GET /api/bot-chats` 只读列出机器人当前所在的活跃群供选择。绑定目标 SHALL 为 opaque `chat_id`（`TEXT`，非枚举），以结构性避免 cloud→console 枚举漂移导致的整页白屏。当路由存储 / 依赖未注入时，相关写接口 SHALL 返回 503 而非静默无效。运营 SHALL 从 `GET /api/bot-chats` 提供的真实群清单中选择目标，界面 MUST NOT 诱导手贴任意 raw `chat_id`。

#### Scenario: 未注入依赖返回 503

- **WHEN** 路由写存储未注入而收到 `PUT /api/notification/routes`
- **THEN** 接口 SHALL 返回 503，MUST NOT 假成功

#### Scenario: 从机器人所在群清单选择目标

- **WHEN** 运营配置 `teamA` 的投递群
- **THEN** 界面 SHALL 从 `GET /api/bot-chats` 返回的机器人实际所在群中选择
- **AND** 绑定值为该群的 opaque `chat_id`，界面 MUST NOT 依赖任何新增枚举渲染目标
