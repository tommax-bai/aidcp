# feishu-command-ingestion Specification

## Purpose
TBD - created by archiving change feishu-message-fast-ack. Update Purpose after archive.
## Requirements
### Requirement: 命令事件受理即回执（fast-ack）

飞书命令消息事件的处理器 SHALL 在**受理该事件后立即返回**（触发 SDK 向飞书回帧），MUST NOT 等待命令执行完成再回执。命令执行与事件回执解耦，使长耗时命令不再因处理器长时间不回帧而被飞书判超时、重推。

#### Scenario: 长耗时命令不再被重推、只执行一次

- **WHEN** 收到一条会触发长耗时执行的命令消息（如 `/publish`，发帖生成流水线实测约 3 分钟）
- **THEN** 处理器受理后立即返回、SDK 及时回帧，飞书 MUST NOT 因超时重推同一条消息
- **AND** 该命令只被执行一次，MUST NOT 因重推而弹出误导性的「发帖未产出／已有一轮在运行中」卡

#### Scenario: 快命令行为不回退

- **WHEN** 收到一条秒级完成的命令消息（如 `/status`）
- **THEN** 处理器同样受理即返回，命令照常执行并回结果卡，行为与时序无可感知回退

### Requirement: 命令结果异步回卡、honest-status 不变、无启动中间卡

命令执行完成后，系统 SHALL 异步发送反映**真实终态**的结果卡，措辞与配色沿用既有 honest-status 判级（触发成功／未产出／失败分色，MUST NOT 把「触发成功」染成「已发布」）。系统 MUST NOT 在终态卡之前插入「任务启动中／已触发」等中间卡。后台执行抛出的意外错误 MUST 被捕获并记录，MUST NOT 中断或重复入口处理。

#### Scenario: 终态卡异步照发、内容不变

- **WHEN** 命令在后台执行完成（成功／未产出／失败）
- **THEN** 系统异步发送与改动前**一字不改**的终态结果卡（含发帖审批卡），只是发送时机从「阻塞后发」变为「执行完异步发」

#### Scenario: 不插入启动中间卡

- **WHEN** 命令被受理并转入后台执行
- **THEN** 在终态卡到达前，系统 MUST NOT 向用户发送任何「任务启动中／已触发」中间卡

#### Scenario: 后台执行异常不外溢

- **WHEN** 后台命令执行抛出意外错误
- **THEN** 错误被捕获并记录日志，入口处理不崩溃、不重复处理该事件

### Requirement: 重复执行由既有并发闸兜底、入口不自建去重

入口 MUST NOT 依赖 fast-ack 单独保证「恰好一次」。当重复的命令仍抵达执行层（如长连接**重连 replay** 触发的重推），已在运行的发帖生成 SHALL 由既有并发闸拦截、跳过第二次，MUST NOT 产出第二篇帖子。本次入口层 MUST NOT 新增 `message_id`/`event_id` 显式去重。

#### Scenario: 重连 replay 重推仍不重复发帖

- **WHEN** 一条重复的 `/publish` 在首轮发帖生成仍在运行时抵达编排器
- **THEN** 该次被并发闸判 skipped、不产出第二篇帖子，即使 fast-ack 已消除超时重推这一主因

### Requirement: 命令结果卡片账号展示必须昵称优先

Feishu 命令结果卡片包含相关账号时，可见账号行 SHALL 使用账号主数据中的 `accounts.nickname` 作为优先展示名；当昵称为空、未知或账号存储不可用时，MUST 诚实回落展示真实 `accountId`。该展示名仅用于结果卡文案，命令解析、调度、发布 / 评论归属、审计和日志 MUST 继续使用真实 `accountId`。

#### Scenario: 参照创作失败结果卡展示昵称

- **WHEN** 精选内容池对账号 `acc-1` 触发参照创作，且账号 `acc-1` 的昵称为 `工程师大白`
- **AND** 参照创作编排失败并发送异步 Feishu 结果卡
- **THEN** 结果卡的账号行 SHALL 展示 `工程师大白`
- **AND** 结果卡标题、红黄绿 honest-status 判级和失败原因 MUST 保持真实终态语义

#### Scenario: 昵称缺失时回落账号 ID

- **WHEN** 任何命令或异步任务结果卡关联账号 `acc-2`，但该账号没有可用昵称
- **THEN** 结果卡的账号行 SHALL 展示 `acc-2`
- **AND** 系统 MUST NOT 编造昵称或把缺失昵称显示成成功状态

### Requirement: 账号影响类命令只在管理群受理，外部群纯通知投递

**管理群**由独立显式配置的白名单（env `FEISHU_MANAGEMENT_CHAT_IDS`，逗号分隔）界定。当白名单**非空**时，系统 SHALL 只在白名单会话中受理**任何非帮助类命令**（`/publish`、`/comment`、`/pause`、`/resume`、`/status`、`/bind` 等）；从**外部群**（客户所在的对外共享群）或任何非白名单群下达的此类命令，系统 MUST NOT 执行，SHALL 以诚实回执说明该群无权下达命令。外部客户群按定义**纯做通知投递**：外部成员即便能 @ 机器人，也 MUST NOT 借此驱动任何账号动作。当白名单**为空**（未启用作用域）时，系统 SHALL 放行全部命令（零回归上线 ramp：先零变更部署，待就绪再显式设白名单收紧）。`/help` 在任何群 SHALL 放行。

#### Scenario: 外部群命令被诚实拒绝（作用域已启用）

- **WHEN** 已配置管理群白名单，且某外部客户群里的成员向机器人发送 `/publish <昵称>` 或 `/pause <账号>`
- **THEN** 系统 MUST NOT 执行该命令
- **AND** SHALL 回一条诚实说明「本群无权下达账号命令」的回执，MUST NOT 静默无响应地假装受理

#### Scenario: 管理群命令照常受理

- **WHEN** 在白名单管理群里下达 `/comment <昵称>`
- **THEN** 系统 SHALL 照常解析、执行并回执（结果卡回本管理群）

#### Scenario: 未配置白名单时零回归放行

- **WHEN** `FEISHU_MANAGEMENT_CHAT_IDS` 未配置（白名单为空）
- **THEN** 命令在任何群 SHALL 与本变更前一致地照常受理（零回归），系统 SHALL 记录一条「作用域未启用」日志

### Requirement: /bind 不授予全局默认或管理语义

`/bind` MUST NOT 使任意群获得全局默认群或管理群权限。管理群 / 默认投递群的指定 SHALL 是一项**独立的显式配置**（面板路由或独立标志位），MUST NOT 可被任意用户在自己所在群自助 `/bind` 而获得。据此，任何人在任意群下 `/bind` 都 MUST NOT 借此把 ops / 告警 / 兜底流量或账号命令权引到自己群。

#### Scenario: 自助 /bind 无法提权为管理群

- **WHEN** 某用户在一个未被授权的群里发送 `/bind`
- **THEN** 该群 MUST NOT 因此获得管理群或全局默认群语义
- **AND** 账号影响类命令在该群仍被拒

### Requirement: 作用域闸在命令入口生效，显式 accountId / 短路路径不得绕过

作用域校验 SHALL 在**命令入口**（解析后、派发到任何执行动作前）对**所有**非帮助类命令统一生效，与账号如何指定无关——无论显式 accountId、按昵称、还是单账号 / 空昵称便捷短路。据此，带显式 accountId 的 `/status`、`/pause`、`/resume` 与单账号短路 MUST NOT 因账号已在参数中给出而绕过作用域；非授权群一律诚实拒。入口闸判定 MUST 与账号命令解析解耦（先判权限、后解析账号），杜绝"解析出账号再放行"的漏判。

#### Scenario: 非管理群带显式 accountId 仍被拦

- **WHEN** 从非管理群下达 `/pause acc-1`（显式 accountId）
- **THEN** 系统 SHALL 校验来源群无权管理 `acc-1` 并诚实拒绝
- **AND** MUST NOT 因 accountId 显式给出而绕过作用域执行

#### Scenario: 单账号短路路径也过作用域

- **WHEN** 从非管理群下达无参 `/status`（依赖单账号短路解析）
- **THEN** 该短路解析 MUST 同样受来源群作用域约束，非管理群一律诚实拒

