# accounts-master-data Specification

## Purpose
TBD - created by archiving change aidcp-console-panel-mvp. Update Purpose after archive.
## Requirements
### Requirement: 真账号主表替换单硬编码账号，seed 一个 default 行

系统 SHALL 引入一张真 `accounts` 主表，替换今天唯一硬编码的 `default` 账号。迁移 SHALL **先 seed 恰好一个 `account_id='default'` 行**，与现有字面量对齐，使已按账号 keyed 的表（`risk_state` / `risk_counters` / `risk_interactions`）瞬间获得父行、零行为变化。表 SHALL 至少含：`account_id`（PK）、`label`、`platform`、`persona_ref`（指向版本控制 YAML 的路径）、`quota_level`、`status`（`active`/`paused`）、`paused_at`、`machine_label`（可空）、`group_label`（可空）、`created_at`。`account→machine` 映射 SHALL 放在该表上，MUST NOT 在 MVP/V1 另起 `edge_bindings` 表（近静态，YAGNI）。

#### Scenario: seed default 后运行闭环不变
- **WHEN** 账号表迁移执行并 seed 了一个 `default` 行
- **THEN** 运行中的边缘浏览闭环行为不变，已按账号 keyed 的风控表获得父行，无可见副作用

### Requirement: 运营暂停态持久化，去掉默认 active 回退，暂停跨重启存活

运营暂停态 SHALL 持久进 `accounts.status`/`paused_at`，折叠掉今天非持久的内存 `AccountStateManager`。系统 MUST 去掉「未知账号默认 active」回退——一个无显式 `status` 的账号行 MUST NOT 被默认成 `active`，否则一个被有意暂停的账号会在重启后静默复活。运营暂停态 MUST 与传输层 `pausedEdges`（验证码门控）保持区分（运营意图 vs 验证码门控）。

#### Scenario: 暂停账号重启后仍暂停
- **WHEN** 一个账号被运营暂停，随后 cloud 进程重启
- **THEN** 该账号从 `accounts.status` 读回仍为 `paused`，不静默复活为 active

#### Scenario: 运营暂停不等于验证码硬停
- **WHEN** 一个账号被运营暂停、同时其边缘并未触发验证码
- **THEN** 运营暂停态与 `pausedEdges` 各自独立，互不混淆

### Requirement: RiskControllerRegistry 每账号单写并提供 listStates

系统 SHALL 引入 `RiskControllerRegistry`（`Map<accountId, RiskController>`），从既有风控存储按账号懒加载一个 controller，并提供 `listStates()` 供面板总览。最终风控状态 SHALL 仍**按账号**经该账号的 controller 单写，registry 只做路由、MUST NOT 成为跨账号多路复用的 god-object。`interaction.occurred` SHALL 按事件上的 `accountId` 路由到对应 controller。

#### Scenario: 总览读多账号状态
- **WHEN** 面板请求账号总览且存在多个账号
- **THEN** registry 的 `listStates()` 返回各账号状态，每账号状态仍只由其自身 controller 写

#### Scenario: 事件按账号路由到正确 controller
- **WHEN** 一个带 `accountId` 的 `interaction.occurred` 到达
- **THEN** registry 把它路由到该 `accountId` 的 controller，单写按账号保持

### Requirement: publish_log 与 concepts 增 account_id 隔离列、自动回填

`publish_log` 与 `concepts` 表 SHALL 各增一列 `account_id TEXT NOT NULL DEFAULT 'default'`，为 additive 迁移、经默认值自动回填，使按账号隔离成为可能。概念**查询** SHALL 保持账号无关，直到隔离搜索记忆成为被证实的需求（YAGNI）。

#### Scenario: 增列自动回填
- **WHEN** 对 `publish_log` / `concepts` 执行增 `account_id` 列的迁移
- **THEN** 已有行经 `DEFAULT 'default'` 自动回填，无需手工数据迁移，现有读路径不被破坏

