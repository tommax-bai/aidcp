## Context

当前 Electron 主进程在 `ads:createEnv` 内直接取得 AdsPower `user/create` 返回的真实 `userId`，但登录态创建成功后统一覆写为 `requiresAdminAssignment=true`；renderer 因此不入册，`settings:save` 也会按 `/my-environments` 的 `allowedProfileIds` 把它过滤掉。Cloud 的旧 `POST /environments` 已被安全加固为固定 403，active owner 由 `client_env_scope` 的全局唯一索引保护。

Cloud 现有“环境自动登记”只挂在 `onEdgeRegistered`：环境必须先进入花名册、启动并完成边云握手，才会进 `client_environments`；但未归属环境又不能入册，因而客户端内新建路径存在 bootstrap 断点。控制仓基线虽有“登录态新建环境自动归属”要求，后续安全变更又正确禁止了任意客户输入自声明 `envKey`；本设计把两者收敛为一个窄的、可审计的程序化创建例外。

## Goals / Non-Goals

**Goals:**

- 仅允许有效客户会话下、Electron 主进程实际执行的 `user/create` 结果自动归属当前客户。
- Cloud 在一个事务内完成创建意图核验、环境注册、全局唯一 owner 写入和意图完成，写后回真态。
- Edge 只在重新读取 `/my-environments` 确认权威归属后把环境加入本地花名册；加入不等于启动。
- 普通客户仍不能通过已有环境列表、手填 ID 或旧 `POST /environments` 认领/转移环境。
- 单建和 Facebook 批量建号都按环境逐个给出真实归属结果；网络重试不产生第二份 owner。

**Non-Goals:**

- 不提供已有环境自助认领、共享 owner 或客户间转移；这些仍走管理员 revoke/offboard + assign。
- 不引入硬件/OS 远程证明。信任边界仍是官方 Electron 主进程与其私有客户会话；完全控制主机的本地管理员不在本期威胁模型内。
- 不自动启动新环境，不因缺代理阻止创建/归属/入册，不构建桌面安装包。
- 不改边云 WebSocket protocol v2、interaction API、console 管理界面或风险状态机。

## Decisions

### D1. 两段式创建意图，而非恢复通用 attach

Cloud customer-auth 新增两个专用端点：

1. `POST /environment-provisioning/intents`：为当前 `userId` 创建短时、一次性 intent，返回 `intentId + proof + expiresAt`；proof 只在响应中出现一次，数据库只存 SHA-256。
2. `POST /environment-provisioning/complete`：接收 `intentId + proof + user/create` 返回的 `envKey` 及非敏感 label/platform，完成权威写入。

Edge 必须在调用 AdsPower `user/create` **之前**取得 intent；intent/proof 只留在 Electron 主进程闭包中，不经 preload/renderer，不写日志。旧 `POST /environments` 继续固定 403。相比“创建后直接 attach”，预先意图提供短期、单次、按客户绑定和可审计边界，也让 Cloud 能区分“程序化新建完成”与任意已有 ID 输入。

备选“仅靠客户 JWT 直接提交 envKey”被否决：它会重新打开已修复的自认领漏洞。备选“等 Edge 首次 WS 握手再分配”被否决：未归属环境不能入册启动，无法打破 bootstrap 断点。

### D2. Cloud 事务是唯一 owner 写者

新增 `client_env_provisioning_intents` 表，记录 intent 的客户、proof hash、过期时间、完成 envKey 与完成时间。`completeProvisioningIntent()` 在同一事务内：

- 锁定 enabled client user 与 intent，常量时间核 proof，拒绝过期、跨用户、重复用于另一 envKey；
- 要求 envKey 在 `client_environments` 中尚不存在，并依靠其主键插入竞争实现“只认真正新登记”；
- 插入 `client_environments(source='auto')`；
- 插入 `client_env_scope(source='admin', assigned_by='client-provision:<intentId>')`，继续受 `uq_client_env_scope_active_env` 全局唯一 owner 保护；
- 标记 intent completed，提交后回读该客户 scope 真态。

同一 intent + 同一 envKey 重试返回同一成功结果；同一 intent 换 envKey、envKey 已登记/已归属、proof 错误均拒绝且不部分落库。归属仍由 Cloud 单写方法产生，不让 renderer 或 Edge 本地集合成为真源。

### D3. Edge 先准备归属，再本地建号；归属确认后由主进程入册

客户鉴权启用时，`ads:createEnv` 对每个待创建环境执行：

1. 取得 provisioning intent；失败则在本地建号前停止，避免制造新孤儿。
2. 调用现有 `createEnvironmentWithGroupRecovery`，直接使用其返回 `userId`，renderer 无法替换 envKey。
3. 调 completion；超时/丢响应可用同一 intent 幂等重试。
4. completion 成功后调用 `refreshAllowedEnvironments()`，只有 `allowedProfileIds` 已包含该 userId 才可继续。
5. 主进程把 `{profileId,name,platform}` 去重追加到 `settings.environments`，落盘、`syncEnvHandles()` 并广播 fleet；不 spawn、不自动点“启动”。

本地 `user/create` 已成功但 Cloud 最终未确认时，返回 `createdLocally=true / assignedToCurrentClient=false / requiresAdminAssignment=true`，不加入花名册，文案明确“本机已创建但自动分配失败”。批量创建逐项记录结果，禁止把部分成功描述为整批已加入。

未启用客户鉴权时维持现有内部/运营构建行为；renderer 原有非 gated 自动选择路径保留。gated 成功返回 `rosterJoinedByMain=true`，renderer 不再通过 `settings:save` 重提 envKey。

### D4. 过期、重放与敏感数据

- intent TTL 固定为 10 分钟；创建新 intent 时 opportunistic 清理已过期未完成行，保留 completed 行用于审计与幂等。
- proof 使用 32 字节随机值，数据库只存 hash；HTTP/body 与错误日志不得输出 proof。
- label/platform 为展示元数据；envKey 做长度、字符与空白校验。代理、Cookie、账号密码、2FA、AdsPower API key 均不进入 Cloud 请求。
- customer-auth 的每请求 enabled-user 复核保持不变；停用或令牌失效后 intent 不能完成。

## Risks / Trade-offs

- **[本机在建号后、Cloud 完成前崩溃]** → 环境物理存在但未归属；重开后它仍不会对客户显示，管理员可从 AdsPower/后台登记并分配。本期不持久化 proof，避免新增长期 bearer secret；UI 对失败必须显示管理员兜底。
- **[完全控制客户机的本地管理员伪造官方主进程行为]** → 本期无硬件证明，无法从 Cloud 侧完全证明 AdsPower 创建动作；通过短时 intent、只认未登记 envKey、主进程不暴露 proof、全局唯一 owner 把风险限制在已声明的信任模型。
- **[Cloud 已提交但响应丢失]** → 同 intent + envKey 重试幂等返回成功；Edge 在入册前仍以 `/my-environments` 回读为准。
- **[并发客户提交同一 envKey]** → `client_environments` 主键与 active owner 唯一索引使最多一个事务成功，另一个返回冲突。
- **[批量创建部分失败]** → 每行独立 intent/事务并逐项回报；已成功项保留，失败项不冒充已加入。

## Migration Plan

1. 先部署 Cloud：新增表/单写方法/端点，但旧 Edge 不调用，行为兼容；在 dev 应用迁移并验证旧 `POST /environments` 仍为 403。
2. 再合入 Edge：启用新 intent/complete 流程；不构建安装包，源码与自动化验证完成后停止在 commit/push。
3. dev 验证 Cloud 服务、端口、客户鉴权 health、PostgreSQL 表/约束和旧路由拒绝；无真实账号破坏性建号则明确记录未做真机创建。
4. 回滚 Edge 即恢复管理员分配提示；Cloud 新端点无人调用、表可保留。若回滚 Cloud，必须先回滚 Edge，避免客户端在本地创建前卡在 intent 准备失败。

## Open Questions

- 无阻塞问题。桌面安装包与真实 Windows/AdsPower 建号验收按现有发布红线另行显式执行。
