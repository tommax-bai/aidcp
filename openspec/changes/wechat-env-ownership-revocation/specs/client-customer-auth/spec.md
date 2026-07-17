## ADDED Requirements

### Requirement: 内部管理员撤销视频号环境归属必须先收回访问权

内部管理员通过整批替换环境归属移除 `wechat_channels` 环境，或通过停用端用户移除其环境时，Cloud SHALL 在同一事务内写撤权审计、删除 active ownership，并在停用场景写入 disabled。访问撤权 MUST NOT 依赖 interaction account binding 是否已经存在；客户下一次 `/my-environments` 或 interaction 请求 MUST 立即失败关闭。

存在精确 `envKey + accountId + platform` binding 时，Cloud SHALL 创建现有 durable offboard。缺少 binding 时，Cloud SHALL 创建不含虚构 accountId 的 durable cleanup hold，并将成功结果明确报告为“ownership revoked, cleanup binding missing”；MUST NOT 返回整笔失败并保留旧 ownership，也 MUST NOT 声称 Edge 密文、sidecar 或 Cloud interaction 数据已经清理。

#### Scenario: 有 binding 的管理员移除继续进入 offboard
- **WHEN** 管理员从端用户归属中移除一个存在精确 interaction account binding 的视频号环境
- **THEN** active ownership 在事务内删除并创建 `admin_revoked` durable offboard，成功响应同时返回撤权后的 scope 与 offboard cleanup receipt

#### Scenario: 缺 binding 的管理员移除仍即时撤权
- **WHEN** 管理员从端用户归属中移除一个缺少 interaction account binding 的视频号环境
- **THEN** active ownership 在事务内删除，客户下一次请求即时不可访问，Cloud 创建 env-scoped `binding_missing` cleanup hold，响应不得包含伪造 accountId 或已清理状态

#### Scenario: 停用端用户混合处理多个环境
- **WHEN** 管理员停用的端用户同时拥有一个已绑定视频号环境和一个缺 binding 视频号环境
- **THEN** 用户 disabled 与全部 active ownership 在一个事务提交，前者创建 offboard、后者创建 cleanup hold，任一数据库写失败时整笔回滚且不得留下半撤权状态

### Requirement: 未完成的撤权清理必须持续隔离并可自动衔接 offboard

Cloud SHALL 为每个 envKey 至多保留一个 active cleanup hold。hold 或非 purged offboard 存在期间，系统 MUST 阻止该环境重新分配给任何客户，并 MUST 拒绝该 env 的 interaction sync/write 副作用。late auth binding MUST NOT 恢复 ownership 或业务能力；Cloud SHALL 在相同 env advisory lock 下把 hold 转换为使用真实 accountId 的现有 durable offboard，再由既有 Edge cleanup 生命周期处理。

#### Scenario: 清理待定位期间拒绝重新分配
- **WHEN** 管理员尝试分配一个存在 `binding_missing` cleanup hold 的环境
- **THEN** 请求返回可识别的 cleanup-in-progress 冲突，active owner 保持为空且不得覆盖 hold

#### Scenario: late binding 只用于定位清理
- **WHEN** cleanup hold 存在后 Edge 上报该 env 的真实 account binding
- **THEN** customer ownership 保持为空、interaction sync/write 仍被拒，Cloud 创建精确 offboard 并移除 hold，后续按既有 pending/dispatched/tombstoned/purged 流程推进

#### Scenario: 重复撤权不重复创建清理责任
- **WHEN** 管理员因响应丢失重试同一归属集合或重复停用已停用用户
- **THEN** Cloud 不创建第二个 active hold 或 offboard，内部读口仍能返回第一笔真实 cleanup 状态

### Requirement: 内部管理面必须展示撤权与清理的不同真态

内部 scope mutation、端用户停用和全局环境注册表响应 SHALL 暴露最小 cleanup receipt，至少区分 `offboard_pending` 与 `binding_missing`，并提供稳定的 revocation/offboard 标识与 envKey。Console SHALL 将两者分别显示为“归属已撤销，Edge 清理中”和“归属已撤销，清理待定位”，不得统一提示“已清理”或把已成功撤权显示成仍有 ownership。

#### Scenario: 保存归属后显示 binding 缺失真态
- **WHEN** 运营保存归属变更且 Cloud 返回 `binding_missing` cleanup receipt
- **THEN** Console 仍刷新并显示环境已从该用户归属移除，同时展示清理待定位警示而非失败回滚或清理完成

#### Scenario: 客户自助删除语义不被放宽
- **WHEN** 客户对非 completed-provisioning-intent 的缺 binding 环境调用 `DELETE /environments/:envKey`
- **THEN** 仍按既有契约返回 `offboard_binding_missing` 并保留 active scope，本 change 的管理员撤权 receipt 不得被客户令牌调用或读取
