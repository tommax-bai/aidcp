## Why

管理员移除视频号环境归属或停用端用户时，Cloud 当前会在缺少 `interaction_auth_state` binding 时以 `offboard_binding_missing` 回滚整个事务，导致本应撤销的 customer ownership 继续有效。访问撤权不应依赖后续 Edge 清理证据；系统需要先 fail closed 地收回访问，再如实保留未完成的清理责任。

## What Changes

- 将内部管理员触发的 env ownership revocation 与 interaction credential/data cleanup 解耦：归属和客户读写能力在同一事务内立即撤销，不因缺 binding 而继续有效。
- 有精确 `envKey + accountId + platform` binding 时继续创建现有 durable offboard；缺 binding 时创建不伪造 `accountId` 的 durable unresolved-cleanup receipt，并阻止该环境重新分配或被宣称已清理。
- 让缺 binding 的撤权真态可由内部 API 和运营界面读到；正常成功、Edge 待清理、缺 binding 待处置必须使用不同状态与文案。
- 为归属整批替换、端用户停用、重复撤权和并发授权补充事务/幂等测试；客户侧自助删除和既有 Edge offboard 协议不在本 change 中放宽。
- **BREAKING**：内部归属变更不再以 `offboard_binding_missing` 保留旧 ownership；调用方必须处理“撤权已生效、清理待处置”的成功真态。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `client-customer-auth`: 修改内部管理员移除视频号环境归属和停用端用户时的撤权、清理回执、重分配阻断与可见真态要求。

## Impact

- `aidcp-cloud`: customer ownership 存储事务、durable cleanup receipt、内部 panel API、审计和聚焦 PostgreSQL 测试。
- `aidcp-console`: 端用户归属保存/停用后的结果提示与未完成清理状态展示。
- OpenSpec `client-customer-auth` 契约；不新增 protocol v2 消息，不改变 Edge 现有 `interaction.offboard.*` envelope。
