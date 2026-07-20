## Context

Cloud 已维护 `client_environments` 全局注册表、环境→账号的最后确认绑定、端用户归属和视频号 offboard 真态，但内部 `/api/client-environments` 只为端用户归属抽屉提供最小字段；Console 账号页以 `accountId` 为主键，没有环境反向可用性。Edge 已通过客户鉴权 HTTP 定时拉取 `/my-environments`，本地 AdsPower 写客户端也已有逐环境 `user/delete`，但非视频号物理删除不会形成 Cloud 生命周期闭环，视频号则必须等待既有 offboard 清密文终态后才可物理删除。

删除属于资源期望状态与本地实际状态的收敛，不是自动化引擎命令。用户明确要求 Edge 主动拉取 Cloud 状态，因此本 change 不新增 Cloud→Edge WS 消息、不触碰 protocol v2 主动命令路由。Cloud 仍是环境生命周期、归属和调度可用性的单写者；AdsPower 是物理 profile 是否存在的事实源；账号风控继续只由 `RiskController` 单写。

## Goals / Non-Goals

**Goals:**

- 提供按环境组织的管理侧资产页，并诚实关联挂载账号、账号风控、分组、端用户归属、Edge 观测和删除生命周期。
- 给账号页提供不含已删除环境的环境摘要，区分无环境、删除中和可执行环境。
- 让管理后台逐环境确认后只写 Cloud `desiredState=deleted`；Edge 经客户鉴权 HTTP pull 获取责任、执行 AdsPower 删除并以 HTTP 幂等回执收敛 Cloud 终态。
- 在 Edge 离线、承载 installation 未定位、AdsPower 拒删、回执丢失和视频号凭证待清理时保留可重试真态，绝不假成功。
- 软删除保留审计与最后挂载账号；Cloud 调度在删除申请成立后立即排除该环境。

**Non-Goals:**

- 不新增或复用 Cloud→Edge WS 删除命令，不改变自动化引擎 command mapping。
- 不批量删除、不自动按过期/离线/本地 ledger 删除，不提供绕过 AdsPower 回执的“强制已删除”。
- 不删除账号、清空账号风控/分组/人设/历史，也不静默改账号运营暂停态。
- 不让 Console 直接访问本机 AdsPower，不让任意同客户客户端领取不属于其 installation 的删除责任。
- 不构建 Edge 安装包；真实 AdsPower profile 的破坏性删除不作为自动化 dev 验证步骤。

## Decisions

### 1. 新建环境资产投影，不把账号或端用户 DTO 当环境真源

Cloud 增加内部 `GET /api/environments`，由环境注册表左连接账号主数据/统一显示名、RiskController 持久投影、端用户归属、installation 观测和删除申请。`/api/client-environments` 继续服务归属抽屉，避免把跨客户资产详情扩散到客户可达接口。

环境 DTO 分开 `environmentName` 与 `account.displayName`。现有混合 `label` 仅作兼容回落；Edge maintenance poll 上报本地 roster 中的 AdsPower 环境名后写 `environment_name`。挂载关系增加 `bindingObservedAt`；Edge/Cloud 无法证明当前在线绑定时显示“上次确认挂载”，不写“当前在线账号”。账号风控字段实时 join，不复制/改写最终 risk state。

### 2. 生命周期采用 desired/actual 状态和独立删除申请

为 `client_environments` 增加 additive `environment_name`、`binding_observed_at`、`lifecycle_state`、`deleted_at` 等投影字段；删除请求使用独立 `environment_deletion_requests` 保存 requestId、envKey、期望版本、操作者、目标用户/installation、状态、claim lease、AdsPower 回执、错误与时间戳。注册表行不硬删。

状态包含 `active | waiting_edge | deleting | delete_failed | deleted`。内部删除 API 在事务内创建/复用未终态请求、立即写入 `waiting_edge`、把环境置为不可调度并返回写后真态；只有匹配 claim 的 Edge 回报 AdsPower `deleted|already_missing` 且所有平台前置清理完成，Cloud 才写 `deleted`。HTTP 接收、claim 或请求派生不等于完成。

### 3. Edge 通过客户鉴权 HTTP poll/claim/result 收敛，不使用 WS

Edge 首次启动客户会话后立即轮询，之后用带 jitter 的短周期有界 HTTP 请求访问 `POST /environment-maintenance/poll`。请求携带持久化随机 `installationId` 和本机 `settings.environments` 的非敏感 roster 摘要；Cloud 只接受当前用户有 active scope 或 durable deletion responsibility 的 envKey，并记录 installation observation。普通 `/my-environments` 仍只决定可见/可运行集合，维护责任即使环境被冻结或撤权仍通过独立端点返回。

Cloud 只有在最近窗口内恰有一个 installation 声明承载 envKey 时才允许 claim；无承载者显示 `waiting_edge`，多个承载者显示定位冲突且不执行。poll 响应返回已 claim 或可 claim 的单环境删除责任。Edge 以 HTTP claim 锁定 requestId/version/installationId，停止本地 handle，满足平台前置清理后调用既有 `deleteProfile()`；结果持久化到本地 outbox，再 `PUT /environment-maintenance/deletions/:requestId/result`。HTTP 2xx 为持久化确认，超时/响应丢失按相同幂等键重试，不设计 result/ack WS 消息。

备选把删除塞进 `/my-environments` 被拒：该端点是正常访问范围真源，撤权后删除责任会随行消失。备选 Cloud push 被拒：它把常规状态收敛混入自动化主动命令并扩大协议热点。

### 4. AdsPower 回执先于 Cloud 删除终态，视频号先完成既有安全清理

小红书/Facebook：Cloud 冻结调度 → Edge claim → 停止本地环境 → AdsPower `user/delete` → HTTP result → Cloud 软删除并移除 active binding/归属投影。

视频号：Cloud 冻结并创建/复用既有 offboard/hold → Edge 只有读到 `tombstoned|purged` 才可 claim 物理删除 → AdsPower `user/delete` → HTTP result → Cloud 软删除。新 HTTP 删除不替代 interaction offboard，也不新增 interaction 消息。

AdsPower 明确 `not found/not exist` 只有来自已 claim、最近确认承载该环境的 installation 才可视作 `already_missing` 成功；其他机器的“不存在”只能返回定位失败。环境打开/运行导致拒删时写 `delete_failed` 和真实原因，可重试但不自动恢复调度。

### 5. 账号页只消费派生摘要，删除环境不改变账号域真态

Panel 账号 DTO additive 返回 `environmentSummary { activeCount, deletingCount, onlineCount }`。账号页显示“未挂载”“一个环境”或“N 个环境”，链接到带 accountId 筛选的环境页。删除申请中的环境仍显示“删除中”，但不计入可执行 `activeCount`；终态删除后从当前数量移除。

删除最后一个环境后账号仍保留，风险、档位、分组、人设、内容、历史和运营暂停态不变；Cloud 调度按环境生命周期 fail closed，Console 显示“无可执行环境”而不是自动写“运营已暂停”。

### 6. Console 删除采用影响预览和精确单环境确认

环境页默认显示未删除环境，可筛选平台、挂载账号、风控、分组、端用户和生命周期，并可切换历史。删除按钮打开影响预览，展示 envKey、环境名、挂载账号、是否为账号最后一个环境、Edge 定位和视频号清理前置；操作者输入完整 envKey 后才可提交。提交成功只显示“删除申请已创建”，页面轮询 Cloud 读模型推进状态。

本地桌面既有两击删除仍保留。远程管理删除是第二个允许触发源，但同样必须逐个、明确确认；任何批量、过期、离线或陈旧 ledger 触发仍禁止。

## Risks / Trade-offs

- [同客户多个客户端都声称同一 envKey] → Cloud 记录 installation observations，存在多个新鲜承载者时阻断 claim 并显示“承载冲突”，不广播执行。
- [删除请求后 Edge 长期离线] → 保留 `waiting_edge`，环境不再调度但仍显示物理状态未知；不提前解除审计记录。
- [AdsPower 已删但 HTTP result 丢失] → Edge 本地 outbox 持久化相同 requestId/idempotency key；重试时 AdsPower `not found` 由同一 claimed installation 证明并收敛。
- [视频号 offboard 未完成] → 删除请求保持清理前置状态；不绕过密文清理、不把 Cloud access revoked 当物理删除。
- [Edge 旧版本不支持 maintenance poll] → Cloud 请求停在等待 Edge，Console 明示“客户端版本不支持或未上线”；不回退 WS 推送。
- [生命周期列与旧代码共存] → additive 字段默认 `active`；旧 Console/Edge 忽略新字段，Cloud 调度闸先部署以保证删除申请后的安全边界。
- [环境名历史来源混杂] → 新 `environment_name` 只由 installation roster observation 更新，旧 `label` 仅标记为兼容回落并显示来源。

## Migration Plan

1. 先部署 Cloud additive schema、环境投影、HTTP maintenance API 和调度排除闸；所有现有环境默认 `active`，不创建删除请求。
2. 部署 Console 环境页和账号摘要；旧 Edge 下环境可读，但删除申请会诚实停在等待 Edge。
3. 合入 Edge HTTP poll/claim/result 和 outbox；重启源码客户端后开始上报 installation observation，不构建安装包。
4. 在 dev 用非破坏性测试夹具验证 request→poll→claim→失败/成功回执状态机、重复回执和账号摘要；不删除真实 AdsPower profile。
5. 回滚顺序为 Edge → Console → Cloud 应用；数据库 additive 表/列和已创建请求保留。回滚期间暂停新删除申请，已冻结环境不自动恢复，forward-fix 后继续收敛。

## Open Questions

无。远程批量删除、无承载 installation 的人工强制清除和真实账号破坏性验收均明确不在本 change 内。
