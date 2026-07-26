## Context

Cloud 目前把管理员撤销 `client_env_scope` 与创建 `interaction_offboards` 放在同一事务。存在精确 `interaction_auth_state` binding 时，这能做到 revoke-first；但管理员分配的存量视频号环境若没有 binding，`setScope()` 和停用端用户都会返回 `offboard_binding_missing` 并回滚，旧 ownership 继续允许 `/my-environments` 与客户 API 访问。客户自助删除已有一个由 completed provisioning intent 限定的“从未绑定”终态分支，但该证明不能泛化到管理员分配的环境。

本变更横跨 Cloud 权威归属事务和 Console 可见真态。现有 `interaction.offboard.*` 已能在 account binding 已知时完成 Edge 清密文、关 sidecar、tombstone 与 purge，因此不需要新增 protocol v2 消息。

## Goals / Non-Goals

**Goals:**

- 管理员移除视频号环境归属或停用端用户时，先原子撤销 customer ownership 和客户读写能力。
- binding 已知时复用现有 durable offboard；binding 缺失时持久记录“撤权已生效、清理未定位”，不伪造 accountId 或清理成功。
- 未完成清理期间阻止 Edge interaction 入站副作用和环境重新分配，并在 binding 后到时自动转入现有 offboard 流程。
- 让内部 API 与 Console 区分正常变更、Edge 待清理和 binding 缺失待处置。

**Non-Goals:**

- 不放宽客户 `DELETE /environments/:envKey` 对非 provisioning-intent 环境的现有规则。
- 不提供跳过清理的人工强制转让，不物理删除 AdsPower 环境，不缩短既有 tombstone/purge 周期。
- 不改变 Edge envelope、capability 或 cleanup 执行顺序。

## Decisions

### 1. Access revocation commits before cleanup can be proven

管理员撤权事务按 envKey 排序并获取与 first-auth 相同的 advisory transaction lock，然后锁定 enabled user、scope、registry 和 binding。无论 binding 是否存在，事务都会写 `client_env_scope_audit` 并删除 active scope；端用户停用还会在同一事务写入 disabled。binding 存在时创建现有 `interaction_offboards`，不存在时写 durable cleanup hold。

选择该方案是因为“保留访问权直到能清理”在安全语义上是 fail open。把缺 binding 当作已经清理同样不诚实，因此不能复用现有 tombstoned terminal offboard，也不能用 envKey 伪造 accountId。

### 2. Missing binding uses an env-scoped durable cleanup hold

Cloud 新增 `client_env_revocation_holds`，仅保存 `revocationId/envKey/userId/reason/revokedBy/requestedAt` 等最小审计字段，不保存消息正文、凭证或虚构 accountId。每个 envKey 最多一个 active hold。数据库级 scope insert/update guard 在 hold 存在时拒绝重新归属，使应用回滚到旧二进制后也不会绕过隔离。

内部 mutation response 分开返回正常 `offboards` 与 `cleanupHolds`；全局环境注册表返回可选 cleanup 摘要。重复提交不得重复建 hold，响应丢失后运营仍可通过注册表读回真态。

备选方案是扩展 `interaction_offboards.account_id` 为 nullable。该表和边云 envelope 都以精确 accountId 为不变量，放宽会把未知 scope 扩散到协议、Edge outbox 和 purge，因此拒绝。

### 3. Late binding materializes the existing offboard lifecycle

周期 reconciliation 在 advisory lock 内选取已有 matching `interaction_auth_state` 的 hold，创建 reason 保持不变的现有 offboard，再删除 hold。之后重分配继续由非 purged offboard 阻断，Edge cleanup、ack、tombstone 和 purge 完全复用现有实现。

在 hold 转换前，Cloud 的 interaction account-scope gate 必须拒绝该 env 的 sync/write；ownership 已删除也使所有 customer-auth 访问即时失败。这样 late auth 只提供清理定位信息，不能恢复客户访问或业务写入。

### 4. Internal API and Console report cleanup truth explicitly

`PATCH /api/client-users/:id` 与 `PUT /api/client-users/:id/scope` 的成功响应增加 cleanup receipts；`GET /api/client-environments` 增加可选 cleanup 摘要。Console 对 `binding_missing` 显示“归属已撤销，清理待定位”，对 offboard pending 显示“归属已撤销，Edge 清理中”，不得统一提示为“已清理”或把成功撤权显示成失败。

该字段为内部 API 的 additive response；唯一行为破坏是原先 `offboard_binding_missing` 导致的整笔失败改为成功撤权加待处置回执。

### 5. Concurrency and dispatch remain single-writer

所有 revocation、late binding 和 hold reconciliation 复用 `interaction-env:<envKey>` advisory lock。Cloud 仍是 ownership/offboard 单写者；reconciliation 只返回新 materialized offboards，由现有 `InteractionOffboardingService` dispatch，不复制 Edge 推送逻辑。

## Risks / Trade-offs

- [binding 永远不出现会使环境长期不可重新分配] → 保留显式 hold 和运营可见状态；本 change 不允许无证据强制清除，后续可单独设计有审计的人工处置流程。
- [Cloud 新旧版本回滚可能绕过应用层 hold 检查] → 用数据库 scope-write guard 保持隔离；回滚时停止新的 ownership mutation，并优先 forward-fix。
- [多环境整批替换的锁顺序可能死锁] → 对 envKey 排序后统一获取 advisory lock，再进行 scope/binding/hold 写入，并以并发 PostgreSQL 测试验证。
- [Console 未同步升级会忽略 additive cleanup 字段] → Cloud API 仍返回真实 scope/user；先部署 Cloud、再部署 Console，旧 Console 不会显示假清理成功以外的额外状态，但 Cloud 权限边界保持安全。

## Migration Plan

1. 在 Cloud schema 初始化中先创建 hold 表、索引和 scope-write guard；用隔离 PostgreSQL 测试验证可重复执行与旧数据兼容。
2. 部署 Cloud 的事务、interaction gate、reconciliation 与内部 API；确认健康检查、无异常重启以及聚焦 offboard/authorization 测试。
3. 部署 Console 的 receipt/badge 展示，验证整批移除与停用的三种真态。
4. 现有 active scope 不自动撤销；只有后续显式管理员动作产生 hold/offboard。

回滚不得删除 hold 表或 guard。若新版本异常，暂停归属写操作并回滚应用；已经撤销的 ownership 不恢复，已有 hold 保持隔离，随后 forward-fix reconciliation/展示。

## Open Questions

无；无 binding hold 的人工解除/转让需要独立的证据和权限设计，不在本 change 内猜测。
