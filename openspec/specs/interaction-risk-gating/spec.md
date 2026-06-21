# interaction-risk-gating Specification

## Purpose
TBD - created by archiving change captcha-restrict-and-interaction-gating. Update Purpose after archive.
## Requirements
### Requirement: 云端必须在下发互动前依 RiskController 判定

云端 SHALL 在下发 `interaction.like` / `interaction.collect` / `interaction.follow` 之前调用 `RiskController.canDo(action)` 判定归属账号是否允许；判定为拒时 MUST NOT 下发该互动指令，并 MUST 以**真实的被拒结果**反映（不伪装成功）。被拒时 MUST NOT 扣减每会话 budget（budget 不得低于实际下发量而漂移）。`page.scroll` / `navigation.back` 等推进 / 返回指令 MUST NOT 受该闸拦截，以免浏览循环死锁。

#### Scenario: 允许时正常下发并计数

- **WHEN** 归属账号风控为 `normal` 且未超配额，云端决定点赞
- **THEN** 云端下发 `interaction.like` 并在成功后按账号计数

#### Scenario: 被拒时诚实跳过不假成功

- **WHEN** 归属账号为 `restricted`（或已超配额），云端的角色仍产出一次点赞意图
- **THEN** 云端不下发 `interaction.like`、不扣 budget，并如实记录"被风控拦截"（MUST NOT 上报 / 记录为成功互动）

#### Scenario: 推进指令不被风控闸拦

- **WHEN** 归属账号为 `restricted`
- **THEN** `page.scroll` / `navigation.back` 仍正常下发，浏览循环继续（仅互动被拦），不发生死锁

### Requirement: 互动发生后必须按账号持久计数

云端 SHALL 在收到 `action.completed{action∈{like,collect,follow}, ok:true}` 时驱动 `RiskController.record(action)`（经补发 `interaction.occurred` 或等效路径），使按账号的滑动窗计数真实累加并经 `PgRiskStore` 持久化；计数 MUST 反映真实成功互动，MUST NOT 凭下发即记（下发未必成功）。

#### Scenario: 成功互动累加计数

- **WHEN** 云端收到 `action.completed{action:'like', ok:true}`
- **THEN** 该账号 like 的滑动窗计数 +1 并持久化，可被后续 `canDo` 配额判定读到

#### Scenario: 失败互动不计数

- **WHEN** 云端收到 `action.completed{action:'like', ok:false}`（如 `blocked_by_captcha`）
- **THEN** 该账号 like 计数不增加（只记真实发生的互动）

### Requirement: 风控状态与计数必须持久化跨重启

云端 SHALL 以 `RiskController.create({store: PgRiskStore})` 构造风控控制器，使账号状态与滑动窗计数落库（既有 `risk_state` / `risk_counters` 表）并在启动时回放；MUST NOT 以无 store 的 `new RiskController()` 运行导致状态永远钉在 `normal` 且重启即失忆。

#### Scenario: 重启后保留 restricted

- **WHEN** 某账号被置 `restricted` 后云端进程重启
- **THEN** 启动回放后该账号仍为 `restricted`（状态自库恢复，而非回到 `normal`）

### Requirement: 账号风控终态仅云端单写，边缘不得自挡

账号风控终态 MUST 仅由云端 `RiskController` 单写。边缘 MUST NOT 持有互动前自判 / 自记风控的逻辑：移除 `EdgeClient.canDo` / `recordRiskAction` / `requestSessionBudget` 三个未被调用的死包装。`risk.canDo` / `risk.record` / `session.budget` 协议类型 MAY 保留为 reserved 通道（不接线），但边缘 MUST NOT 在浏览闭环里调用它们替云端做风控决策。

#### Scenario: 边缘不再保留自挡风控入口

- **WHEN** 审查边缘浏览闭环代码（`browse-session` / `edge-client`）
- **THEN** 找不到任何互动前 `risk.canDo` 自判或互动后 `risk.record` 自记的调用（风控判定全在云端）

#### Scenario: 被禁账号的 record 返回 false

- **WHEN** 一个 `frozen` / 超额账号触发 `RiskController.record`
- **THEN** `record` 返回 `false`（绝不自残），符合 `AC-RISK-*`，云端不把它当作成功互动

