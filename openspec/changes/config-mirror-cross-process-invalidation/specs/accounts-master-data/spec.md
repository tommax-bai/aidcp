## MODIFIED Requirements

### Requirement: 运营暂停态持久化，去掉默认 active 回退，暂停跨重启存活

运营暂停态 SHALL 持久进 `accounts.status`/`paused_at`，折叠掉今天非持久的内存 `AccountStateManager`。系统 MUST 去掉「未知账号默认 active」回退——一个无显式 `status` 的账号行 MUST NOT 被默认成 `active`，否则一个被有意暂停的账号会在重启后静默复活。运营暂停态 MUST 与传输层 `pausedEdges`（验证码门控）保持区分（运营意图 vs 验证码门控）。

当暂停态由**跨进程本地副本**提供时，读取结果 SHALL 为三态 `paused | active | unknown`：只有副本新鲜且该账号在副本中命中「未暂停」才可判 `active`；副本超过声明的陈旧上限时 MUST 判 `unknown`。`unknown` MUST 走停手路径——不再下发新的平台动作命令——MUST NOT 沿用「副本里查不到即视为 active」的同进程回退。该回退在同进程全量镜像下正确（副本即库），在跨进程副本下等价于「运营点了暂停、后台回写入成功、账号继续对真实平台动作」，属红线「绝不静默假成功」所禁。

#### Scenario: 暂停账号重启后仍暂停
- **WHEN** 一个账号被运营暂停，随后 cloud 进程重启
- **THEN** 该账号从 `accounts.status` 读回仍为 `paused`，不静默复活为 active

#### Scenario: 运营暂停不等于验证码硬停
- **WHEN** 一个账号被运营暂停、同时其边缘并未触发验证码
- **THEN** 运营暂停态与 `pausedEdges` 各自独立，互不混淆

#### Scenario: 副本陈旧时暂停态判未知并停手
- **WHEN** 暂停态副本超过陈旧上限，而库内某账号刚被运营暂停
- **THEN** 读取返回 `unknown`、系统停止下发该账号的新平台动作命令并告警，MUST NOT 因副本未命中而判 `active` 继续执行

### Requirement: 账号人设绑定状态为派生字段

账号是否已绑人设 SHALL 作为一个**派生字段**对外暴露，以**人设存储中是否存在该账号的人设行**为唯一判据。死列 `accounts.persona_ref` MUST NOT 被用作绑定指针（保留不用）。

该派生字段 SHALL 为三态 `bound | unbound | unknown`，MUST NOT 为二值布尔。「人设行不存在」只有在**权威人设存储可读**时才等于 `unbound`；当判据由跨进程本地副本提供且副本超过陈旧上限时，MUST 判 `unknown`。`unknown` MUST 被映射成独立的不可用态，MUST NOT 与 `unbound` 合并——二者的下游后果完全不同：`unbound` 触发人设向导与 `needs_persona_setup` 拒绝，`unknown` 两者都不得触发。

#### Scenario: 绑定状态以人设行存在为准
- **WHEN** 计算某账号的人设绑定状态且权威人设存储可读
- **THEN** 有人设行 → `bound`，无人设行 → `unbound`；不读取/不依赖 `persona_ref` 列

#### Scenario: 副本陈旧时绑定状态为未知
- **WHEN** 人设副本超过陈旧上限，无法确认某账号是否有人设行
- **THEN** 派生字段返回 `unknown`，MUST NOT 返回 `unbound`，MUST NOT 触发任何以「未绑」为前提的下游动作
