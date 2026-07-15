# feishu-notification-routing Specification

## Purpose
TBD - created by archiving change feishu-per-team-notification-routing. Update Purpose after archive.
## Requirements
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

账号作用域的出站消息 SHALL 经 `resolveChatIdForAccount` 按其归属账号路由到团队群。账号作用域包含两类：

1. **入站平台通知**——通知巡视产出的「评论 / @」消息（各团队要收的"消息"）；
2. **账号维度的业务结果卡**——该账号的运营结果回执：排期发帖结果卡、评论终态结果卡（含自动排期与人工 `/comment`）、排期评论 / 排期联系评论触发回执、排期评论 / 排期联系评论免审通知卡、参照创作结果卡。这些卡的正文本就渲染了归属账号，其收件人 SHALL 是该账号的团队。

**例外——命令触发的发帖终态结果卡回来源会话**：当发帖终态失败 / 部分完成结果卡属于一个**由飞书命令创建、且持有非空来源会话**的委托任务时，该卡 SHALL 投递到该来源会话（下命令的私聊或群），MUST NOT 走账号→团队群路由。此例外只覆盖**命令触发**的发帖终态卡；自动 / 排期发帖等无来源命令会话的业务结果卡仍按上述第 2 类走账号团队群，逐字不变。（手动 `/comment` 终态结果卡暂不在此例外内，仍走团队群——登记为后续对齐项。）

**面向运营方**的消息 MUST NOT 走账号→群映射，SHALL 维持既有默认（管理）群 / 源群目标不变，具体为：发布 / 评论**审批卡**（需运营点按授权）、**运维 / 配置 / 验证码 / 风控告警**（边缘离线、CDP 不健康、发布熔断、握手 config-error 等）。据此，外部客户群按定义**只收该客户账号自己的入站通知与业务结果，不收审批与运维流量**——客户 MUST NOT 被诱导点按授权，也 MUST NOT 看到内部运维状态。

无归属账号（`accountId` 缺失）的任何消息 SHALL 落默认群，MUST NOT 为其臆造账号作用域。

#### Scenario: 巡视通知走账号团队群

- **WHEN** 账号 `acc-1`（属 `teamA`）的通知巡视产出评论 / @ 通知
- **THEN** 该通知 SHALL 投递到 `teamA` 对应的群

#### Scenario: 排期业务结果卡走账号团队群

- **WHEN** 账号 `acc-1`（属 `teamA`，`group_route` 有 `teamA → oc_team_a_chat`）的排期发帖产出「本槽无新素材」结果卡、或排期评论产出「按需评论未产出」终态卡
- **THEN** 该卡 SHALL 投递到 `oc_team_a_chat`
- **AND** MUST NOT 因「卡片属命令回执类」而被硬绑默认（管理）群

#### Scenario: 命令触发的发帖终态失败卡回来源会话、不走团队群

- **WHEN** 账号 `acc-1`（属 `teamA`，`group_route` 有 `teamA → oc_team_a_chat`）由飞书私聊 `/publish` 命令触发的委托发帖终态失败、其任务持有来源会话 `P`
- **THEN** 该失败结果卡 SHALL 投递到 `P`
- **AND** MUST NOT 投递到 `oc_team_a_chat`

#### Scenario: 未绑定团队的业务结果卡仍落默认群、绝不丢

- **WHEN** 账号 `acc-2` 无 `group_label`，或其团队键在 `group_route` 无匹配行，其排期发帖 / 评论结果卡产出
- **THEN** 该卡 SHALL 投递到默认群链的结果
- **AND** MUST NOT 因未绑定而被静默丢弃

#### Scenario: 审批卡与运维告警不按账号路由

- **WHEN** 系统为账号 `acc-1`（属 `teamA`）发出发布 / 评论审批卡、或该账号相关的 persona / 验证码 / 边缘离线 / CDP 不健康 / 熔断告警
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

### Requirement: 机器人所在群清单取真实群名并优雅降级

`GET /api/bot-chats` SHALL 实时从飞书「获取机器人所在的群列表」接口（`im/v1/chats`，分页取全）解析每个群的**真实群名**返回，使后台以群名展示、而非仅 opaque `chat_id`。当飞书调用失败（缺 `im:chat:readonly` 权限 / 网络 / 限频）时，系统 MUST NOT 返回空列表或抛错致整页失败，SHALL **优雅降级**回本地 `bot_chats` 表（群名可能为空），并在响应中标明数据来源（`source`：`feishu` / `store`），供前端在降级时提示需补权限。为避免频繁打飞书，群名列表 MAY 加进程内短缓存（秒级）。绑定目标仍为 opaque `chat_id`——群名仅用于展示层，MUST NOT 参与路由键或引入枚举。

#### Scenario: 有权限时返回真实群名

- **WHEN** 飞书应用具备 `im:chat:readonly` 权限，运营打开路由配置
- **THEN** `GET /api/bot-chats` SHALL 返回各群的真实 `name` 与 `chatId`，`source` 为 `feishu`
- **AND** 后台 SHALL 以群名为主展示目标群

#### Scenario: 缺权限 / 调用失败时降级不崩

- **WHEN** 飞书群列表调用因缺权限或网络失败
- **THEN** 系统 SHALL 回落本地 `bot_chats` 清单（`name` 可能为空、退回显示 `chatId`），`source` 为 `store`
- **AND** MUST NOT 返回空列表或让路由配置页报错崩溃

### Requirement: 机器人所在群清单标明默认群

`GET /api/bot-chats` 响应 SHALL 标明**默认群** `defaultChatId`（按既有默认解析链：`bot_chats.is_default` → `FEISHU_CHAT_ID`），使后台能一眼看出**未映射账号通知的兜底目的地**。当无任何默认群可解析时，`defaultChatId` SHALL 诚实为 null（而非臆造）。

#### Scenario: 后台展示未映射账号的兜底默认群

- **WHEN** 运营打开路由配置页
- **THEN** 响应 SHALL 带 `defaultChatId`，前端据此展示「未映射的账号 → 默认群：<群名 / id>」
- **AND** 当默认群在群名清单中有名时，SHALL 以群名展示该默认群

### Requirement: 账号级目标解析统一注入，禁止逐处手工装配

云端 SHALL 提供**一处**账号级目标解析入口，内聚注入账号存储、团队路由存储、默认群存储与 `FEISHU_CHAT_ID` 兜底；所有账号作用域的投递点 SHALL 经该入口解析目标群，MUST NOT 在各调用点分别手工装配依赖。

此约束的目的是消除一类静默失败：某调用点漏传团队路由存储时，解析器会**合法地**判定「无团队路由」并回落默认群——投递照常成功、无异常、无 config-gap 日志，运营只看到「配了路由却不生效」，与「未接线」在现象上完全不可区分。统一注入使「漏传依赖」在类型层面不可表达。

#### Scenario: 新增账号作用域投递点无法漏传路由依赖

- **WHEN** 开发者新增一个账号作用域的飞书投递点，调用统一解析入口
- **THEN** 该入口 SHALL 自带全部依赖，调用方只需给出 `accountId`
- **AND** MUST NOT 存在「只传部分依赖即可通过类型检查、运行期静默落默认群」的调用形态

#### Scenario: 路由存储不可用时诚实回落而非伪装命中

- **WHEN** 团队路由存储在启动时初始化失败（依赖不可用）
- **THEN** 统一入口 SHALL 对全体账号回落默认群链，行为与路由表为空逐字一致
- **AND** MUST NOT 让任何投递点因缺依赖而崩溃或静默丢卡

