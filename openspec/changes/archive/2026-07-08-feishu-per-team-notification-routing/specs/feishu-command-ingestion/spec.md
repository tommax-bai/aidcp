## ADDED Requirements

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
