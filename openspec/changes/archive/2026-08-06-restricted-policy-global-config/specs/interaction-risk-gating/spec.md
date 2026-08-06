# interaction-risk-gating Delta

## ADDED Requirements

### Requirement: 受限处置策略参与 view 判定

`RiskController.explain('view')` 在账号处于 `restricted` 时 SHALL 按全局受限处置策略判定:`full_pause` 模式下 MUST 拒绝并以 `state:restricted` 为原因、携带剩余等待时长(恢复时刻 − 当前时刻);`browse_only` 模式下 SHALL 保持既有豁免(放行 view)。两种模式下 restricted 对互动动作的拒绝与互动配额归零 SHALL 保持不变。策略模式 SHALL 每次判定现读(热生效),MUST NOT 进程内缓存过陈旧上限。

`full_pause` 的拒绝 SHALL 经既有浏览前闸与会话启动闸生效(不开下一篇、进入浏览休眠);MUST NOT 为此对 `page.scroll` / `navigation.back` 等推进 / 返回指令新增拦截(既有反死锁约束不变)。

#### Scenario: full_pause 下不开下一篇

- **WHEN** 全局策略为 `full_pause` 且账号为 `restricted`,浏览角色产出候选
- **THEN** `explain('view')` 拒绝(`state:restricted`,含剩余等待时长),云端 MUST NOT 下发 `open_note`,进入浏览休眠且 MUST NOT 下发 `session.end`

#### Scenario: browse_only 保持现状

- **WHEN** 全局策略为 `browse_only` 且账号为 `restricted`
- **THEN** `explain('view')` 放行,会话内浏览照常,互动仍被拒

#### Scenario: 恢复到警告后放行

- **WHEN** `full_pause` 下账号被扫描器恢复为 `warned`
- **THEN** `explain('view')` 按 `warned` 语义放行,浏览闭环可被重新驱动

### Requirement: 受限恢复窗口来自策略配置

风控状态机的 restricted 恢复窗口 SHALL 来自受限处置策略的 `recoveryHours` 现读,MUST NOT 再写死常量;`warned` 窗口维持既有 7 天常量,`frozen` 维持无自动恢复。窗口计时基点遵循 `max(statusSince, lastSignalAt)` 规则。

#### Scenario: 修改恢复时长即刻影响后续判窗

- **WHEN** 运营把 `recoveryHours` 从 72 改为 24 并保存成功
- **THEN** 此后扫描与剩余等待时长计算按 24 小时窗口执行,已受限账号无需重新进入状态
