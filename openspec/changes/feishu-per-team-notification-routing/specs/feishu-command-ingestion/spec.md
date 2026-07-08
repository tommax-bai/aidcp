## ADDED Requirements

### Requirement: 账号影响类命令只在管理群受理，外部群纯通知投递

系统 SHALL 只在被显式配置为**管理群**的会话中受理会影响账号的命令（`/publish`、`/comment`、`/pause`、`/resume`，以及对指定账号的 `/status`）。从**外部群**（客户所在的对外共享群）或任何非管理群下达的此类命令，系统 MUST NOT 执行，SHALL 以诚实回执说明该群无权下达此命令。外部客户群按定义**纯做通知投递**：外部成员即便能 @ 机器人，也 MUST NOT 借此驱动任何账号动作。

#### Scenario: 外部群命令被诚实拒绝

- **WHEN** 某外部客户群里的成员向机器人发送 `/publish <昵称>` 或 `/pause <账号>`
- **THEN** 系统 MUST NOT 执行该命令
- **AND** SHALL 回一条诚实说明「本群无权下达账号命令」的回执，MUST NOT 静默无响应地假装受理

#### Scenario: 管理群命令照常受理

- **WHEN** 在被显式配置为管理群的会话里下达 `/comment <昵称>`
- **THEN** 系统 SHALL 照常解析、执行并回执（结果卡回本管理群）

### Requirement: /bind 不授予全局默认或管理语义

`/bind` MUST NOT 使任意群获得全局默认群或管理群权限。管理群 / 默认投递群的指定 SHALL 是一项**独立的显式配置**（面板路由或独立标志位），MUST NOT 可被任意用户在自己所在群自助 `/bind` 而获得。据此，任何人在任意群下 `/bind` 都 MUST NOT 借此把 ops / 告警 / 兜底流量或账号命令权引到自己群。

#### Scenario: 自助 /bind 无法提权为管理群

- **WHEN** 某用户在一个未被授权的群里发送 `/bind`
- **THEN** 该群 MUST NOT 因此获得管理群或全局默认群语义
- **AND** 账号影响类命令在该群仍被拒

### Requirement: 显式 accountId 命令必须过来源群作用域校验

带显式 accountId 的 `/status`、`/pause`、`/resume`，以及单账号 / 空昵称的便捷短路路径，MUST 在执行前接收并校验命令的**来源群**是否有权管理目标账号；无权则诚实拒绝，MUST NOT 直接按显式 accountId 越过作用域执行。此校验 SHALL 与出站路由复用同一套来源判定，避免入站 / 出站两半漂移。

#### Scenario: 非管理群带显式 accountId 仍被拦

- **WHEN** 从非管理群下达 `/pause acc-1`（显式 accountId）
- **THEN** 系统 SHALL 校验来源群无权管理 `acc-1` 并诚实拒绝
- **AND** MUST NOT 因 accountId 显式给出而绕过作用域执行

#### Scenario: 单账号短路路径也过作用域

- **WHEN** 从非管理群下达无参 `/status`（依赖单账号短路解析）
- **THEN** 该短路解析 MUST 同样受来源群作用域约束，非管理群一律诚实拒
