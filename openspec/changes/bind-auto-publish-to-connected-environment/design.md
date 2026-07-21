## Context

内容排期由 Cloud 每分钟扫描已完成欢迎握手的在线账号。连接运行时实际已经保存 `accountId` 与 `edgeId=ads-<profileId>`，但调度器只读取去重后的 `accountId[]`；自动发帖触发、候审元数据和下发恢复因而不知道该次在线连接对应哪个浏览器环境，也不知道稿件由 dev 还是 ol 生成。

dev 与 ol 共用业务数据库。当前进程内 `lastFired` 只能阻止单进程在同一小时格重复触发，进程重启或另一 Cloud 实例扫描到相同账号后仍可能再次触发。另一方面，完整队列、跨 Cloud 接管和双在线仲裁的时间与复杂度都不符合本次目标。运营已明确采用人工隔离：同一账号不会同时在线于 dev 和 ol。

## Goals / Non-Goals

**Goals:**

- 自动发帖只从完整、已验证的 `accountId + envKey` 在线身份触发。
- 部署目标只由 Cloud 的 `AIDCP_DEPLOY_ENV` 决定，Edge 不得声明或覆盖 `dev|ol`。
- 用最小数据库占位保证同账号同一发帖小时格在进程重启或同库多 Cloud 下至多启动一次。
- 把 `envKey + executionTarget + hourCell` 固定到发布输入和候审元数据，并在恢复下发时阻止当前 Cloud 消费其它 target 的自动稿件。
- 保持现有直接触发、审批和发布管线，不改变人工发布及其它排期动作。

**Non-Goals:**

- 不增加 Edge 协议字段，不修改 Console 和排期 UI。
- 不检测或仲裁同账号跨环境同时在线，不自动迁移或接管账号。
- 不引入待消费队列、租约续期、跨 Cloud 重试编排或历史占位归档。
- 不把 ol 部署纳入本次 dev 交付。

## Decisions

### 1. 从既有连接身份派生浏览器环境

连接运行时新增只读在线身份投影，为完成欢迎握手的账号返回 `{accountId, envKey}`；只有 `edgeId` 严格符合 `ads-<envKey>` 时 `envKey` 才有值，否则为 `null`。调度器消费该投影，而不是仅消费 `accountId[]`。无效或缺失 `envKey` 的连接只对自动发帖 fail closed，评论、加群、人工操作和其它既有连接能力保持原行为。

不新增 Edge 上报字段：当前握手的 `edgeId` 已绑定实际浏览器环境，重复声明只会制造两份可能漂移的真相。

### 2. 部署目标由服务端严格盖章

Cloud 复用 `AIDCP_DEPLOY_ENV` 的严格解析结果作为 `executionTarget`，只接受 `dev|ol`。值缺失或非法时，不启动自动内容调度器；即使 Edge 伪造输入也不能改变 target。

`executionTarget` 是服务进程归属，`envKey` 是在线浏览器环境归属，两者职责不同，自动发帖必须同时记录。

### 3. 发帖命中后先做最新小时格原子占位

新增一张小型 PostgreSQL 表，以 `(account_id, action)` 为主键，保存最新的 `hour_cell`、`execution_target`、`env_key` 和占位时间。自动发帖所有现有闸通过后，以单条 `INSERT ... ON CONFLICT ... DO UPDATE ... WHERE old.hour_cell <> new.hour_cell RETURNING` 尝试占位；只有拿到返回行的进程才直接启动现有发布管线。

表只保留每账号/动作的最新格，不是任务队列，也不积累历史。占位发生在启动生成前；一旦占位成功，本格即视为已触发。后续生成失败不释放占位，沿用现有“同格不重做、下一格再评估”的成本控制语义。

评论与联系评论继续使用现有进程内幂等，本次持久占位只覆盖自动发帖。

### 4. 执行归属贯穿生成与候审记录

自动发帖触发输入携带不可变的 `scheduleExecution={executionTarget, envKey, hourCell}`。发布执行器先以不可审批的 `needs_review` 安全态建立记录，把归属写入 `PublishMetadata` 成功后才切到 `pending_approval`；任一步失败都不能生成一个无法证明归属的可下发自动稿件。

该字段为可选：人工发布和变更前的历史稿件没有该字段，继续沿用原行为。

### 5. 下发恢复按 target 过滤并二次校验

候审扫描只领取“没有自动排期归属”或“归属当前 `executionTarget`”的记录；按 `recordId` 直接唤醒时，进入 Edge 操作前再次校验 target。解析在线 Edge 后还必须与冻结的 `ads-<envKey>` 精确一致，不能因同账号后来连接到另一浏览器环境而改投。任一不匹配时仅跳过，不改审批和稿件状态，使正确环境仍可继续处理。

这层约束只对已升级的 Cloud 代码生效。由于本次不部署 ol，混合版本期仍依赖用户确认的单账号人工环境隔离，不宣称实现跨版本双在线冲突闭环。

## Risks / Trade-offs

- [占位成功后生成失败会消耗本小时格] → 与现有 `lastFired` 语义一致，避免高成本自动重做；下一活跃格重新评估。
- [无效的旧式 `edgeId` 使自动发帖不触发] → fail closed 并保留日志，人工发布不受影响；现有受管环境均使用 `ads-<profileId>`。
- [共享库上的旧 ol 版本不识别 target 元数据] → 本次 dev 交付不把它描述为混合版本强隔离；由人工保证账号不同时在线，ol 后续升级后获得同样过滤能力。
- [只保留最新占位，不能直接查询完整触发历史] → 稿件元数据与既有发布审计保存实际生成归属；占位表只承担幂等，不承担业务审计。

## Migration Plan

1. Cloud 启动时以 `CREATE TABLE IF NOT EXISTS` 添加占位表；不改现有行，也不要求停机迁移。
2. 在隔离 Cloud worktree 完成聚焦测试、发布安全验收、完整测试与 typecheck。
3. 集成到 `aidcp-cloud/master`，备份 dev Cloud/env 后部署 dev；验证服务、端口、health、数据库连通和目标解析日志。
4. 回滚时恢复上一版 Cloud 代码并重启；新增表保持闲置，无需删除。已带元数据的稿件在旧代码中按历史稿件处理，仍依赖人工环境隔离。

## Open Questions

无。若未来取消“同账号不跨环境同时在线”的人工约束，应另开变更设计连接租约与冲突仲裁，不在本次占位表上叠加隐式接管。
