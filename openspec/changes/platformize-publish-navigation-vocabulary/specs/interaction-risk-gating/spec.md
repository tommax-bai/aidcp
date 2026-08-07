## MODIFIED Requirements

### Requirement: 云端必须在下发互动前依 RiskController 判定

云端 SHALL 在下发 `{platform}.note.like` / `xiaohongshu.note.collect` / `{platform}.user.follow` 之前调用 `RiskController.canDo(action)` 判定归属账号是否允许；判定为拒时 MUST NOT 下发该互动指令，并 MUST 以**真实的被拒结果**反映（不伪装成功）。被拒时 MUST NOT 扣减每会话 budget（budget 不得低于实际下发量而漂移）。`{platform}.feed.scroll` / `{platform}.navigation.back` 等推进 / 返回指令 MUST NOT 受该闸拦截，以免浏览循环死锁。

#### Scenario: 允许时正常下发并计数

- **WHEN** 归属账号风控为 `normal` 且未超配额，云端决定点赞
- **THEN** 云端下发 `{platform}.note.like` 并在成功后按账号计数

#### Scenario: 被拒时诚实跳过不假成功

- **WHEN** 归属账号为 `restricted`（或已超配额），云端的角色仍产出一次点赞意图
- **THEN** 云端不下发 `{platform}.note.like`、不扣 budget，并如实记录"被风控拦截"（MUST NOT 上报 / 记录为成功互动）

#### Scenario: 推进指令不被风控闸拦

- **WHEN** 归属账号为 `restricted`
- **THEN** `{platform}.feed.scroll` / `{platform}.navigation.back` 仍正常下发，浏览循环继续（仅互动被拦），不发生死锁

### Requirement: 受限处置策略参与 view 判定

`RiskController.explain('view')` 在账号处于 `restricted` 时 SHALL 按全局受限处置策略判定:`full_pause` 模式下 MUST 拒绝并以 `state:restricted` 为原因、携带剩余等待时长(恢复时刻 − 当前时刻);`browse_only` 模式下 SHALL 保持既有豁免(放行 view)。两种模式下 restricted 对互动动作的拒绝与互动配额归零 SHALL 保持不变。策略模式 SHALL 每次判定现读(热生效),MUST NOT 进程内缓存过陈旧上限。

`full_pause` 的拒绝 SHALL 经既有浏览前闸与会话启动闸生效(不开下一篇、进入浏览休眠);MUST NOT 为此对 `{platform}.feed.scroll` / `{platform}.navigation.back` 等推进 / 返回指令新增拦截(既有反死锁约束不变)。

#### Scenario: full_pause 下不开下一篇

- **WHEN** 全局策略为 `full_pause` 且账号为 `restricted`,浏览角色产出候选
- **THEN** `explain('view')` 拒绝(`state:restricted`,含剩余等待时长),云端 MUST NOT 下发 `open_note`,进入浏览休眠且 MUST NOT 下发 `session.end`

#### Scenario: browse_only 保持现状

- **WHEN** 全局策略为 `browse_only` 且账号为 `restricted`
- **THEN** `explain('view')` 放行,会话内浏览照常,互动仍被拒

#### Scenario: 恢复到警告后放行

- **WHEN** `full_pause` 下账号被扫描器恢复为 `warned`
- **THEN** `explain('view')` 按 `warned` 语义放行,浏览闭环可被重新驱动
