## Context

慢启动入口和 customer-auth API 已经按 `envKey` 工作，但当前写路由会先经 `client_environments.account_id` 解析账号，再写 `accounts.slow_start_since`。`RiskController` 只拿 `accountId`，因此通过 `AccountNurtureProvider.slowStartSinceFor(accountId)` 现读账号表镜像。这个实现让 UI 看似环境级，事实却随账号移动：环境换号会失去设置，离开环境的旧账号仍被 clamp。

运行时仍以账号作为风控单写键，不能为每个环境创建第二个 `RiskController`；与此同时 `effectiveQuotas()` 是同步热路径，不能在每次配额判定中访问 PostgreSQL。现有 `client_environments` 已是环境注册表和当前环境↔账号持久映射，适合承载环境配置并提供同步镜像。

## Goals / Non-Goals

**Goals:**

- 慢启动开关、起点和进度属于 `envKey`，环境换号后设置保留，新账号立即继承、旧账号立即解除。
- 保持 `RiskController` 的账号级单写边界及同步、零 IO 的配额热路径。
- 允许 Facebook 环境在尚未绑定账号时预先配置慢启动，并诚实显示“已配置、当前未生效”。
- 保留已有曲线、上海自然日起点、平台适用性、全局停用闸、投影与 clamp 同源，以及离线可读写行为。
- 对现有已开启状态做一次可重入迁移，不进行破坏性删列。

**Non-Goals:**

- 不改变 7 天曲线数字、风险档位、动作节奏或账号风险状态机。
- 不改变 customer-auth URL、请求体或客户端鉴权协议。
- 不在本变更删除 `accounts.slow_start_since`，也不要求打包或发布 Edge 安装包。
- 不把环境设置复制进账号记录，也不以账号最近一次所在环境作为永久配置。

## Decisions

### 1. `client_environments.slow_start_since` 是唯一的新事实源

为 `client_environments` 增加可空 `slow_start_since TIMESTAMPTZ`：`NULL` 表示该环境关闭，非空值为已对齐上海自然日的开启起点。PUT 在一次数据库语句中同时验证当前客户 ownership 并更新该环境，客户端继续只能提交 `{enabled}`。

选择环境注册表而不是新增账号↔环境配置表，是因为 `env_key` 已是唯一环境主键，平台、归属和当前账号绑定都在这张表上。替代方案“继续写账号表但在换绑时搬运值”仍让配置所有权落在账号上，并会在换绑竞态中把旧账号状态错误带入新环境，拒绝采用。

### 2. 风控仍按账号单写，通过环境绑定镜像适配

`RiskController` 继续只以 `accountId` 建实例。`AccountNurtureProvider.slowStartSinceFor(accountId)` 的签名暂不改变，但实现改为 `ClientUserStore` 的环境绑定镜像：只有当账号当前恰好映射到一个环境时，返回该环境的 `slow_start_since`；没有映射返回 `null`。

`ClientUserStore.init()` 预热环境→账号/起点镜像；环境注册换绑和慢启动 PUT 成功后，在回包前刷新受影响映射。这样缓存 controller 的下一次同步配额计算即可看见新值，无需重启或驱逐。账号的平台和历史 env 全局旁路 `created_at` 仍由 `AccountStore` 提供，服务端组合成一个 provider。

同一账号若被异常登记到多个环境，运行时 MUST NOT 任取一个环境。镜像将其标记为歧义并不返回某个环境起点，同时产生日志/告警；customer-auth 仍按具体 `envKey` 读写自身配置。部署前检查重复绑定并登记清理项，而不是在共享数据库上自动删改绑定。

### 3. env-scoped API 不再以账号绑定作为写入前置

PUT 只需要 enabled user、环境 ownership 和环境注册行即可完成环境配置写入。账号未绑定、账号行悬空或边缘离线都不妨碍保存环境设置，因为写入目标已不再是账号。

GET/PUT 成功后：

- 有唯一有效当前账号绑定时，调用该账号现有 controller 产生 `slowStart` 与 `dayQuotas`，保证投影与实际 clamp 同源。
- 无绑定或悬空绑定时，返回环境配置态：关闭为 `state=off`；开启则携带 `state=active`、`since`、按自然日计算的 `day/totalDays`，同时 `eligible=false`、`ineligibleReason=binding_unknown`，且不返回 `binding` 或 `dayQuotas`。这表达“设置已保存但当前没有执行对象”，不冒充已实际 clamp。
- ownership/数据库失败仍分别返回 403/503；回包永不泄露 `accountId`。

选择允许未绑定时配置，是环境级语义的直接结果，也让“启动新号之前设置慢启动”真正成立。替代方案“仍要求账号绑定才能写”虽然改了列位置，却保留了产品行为对账号的依赖，拒绝采用。

### 4. UI 将配置态与生效态分开

Edge 继续按环境隔离 pending/error/authoritative snapshot。对于 `binding_unknown`：开关不再禁用；若环境配置已开启，保持勾选并说明“已为此环境开启，登录账号后按曲线生效”；若关闭则保持未勾选并说明可先配置。配额、`binding` 和“已压低”文案只在云端返回有当前账号的 controller 投影时显示。

这不是“待下发边缘”状态：环境配置的写入已经成功；只是当前没有账号可被配额机制作用。客户端 MUST 保持这两个事实分离。

### 5. 可重入迁移保留现有开关

部署时增加环境列与一次性 `slow_start_initialized` 标记。DDL 会把升级前历史行标为未初始化，并让此后新建环境默认已初始化；在 `accounts` 已存在后，只对未初始化历史行复制当前绑定账号的旧值并原子标记完成。用户 PUT（包括明确关闭为 NULL）同样标记完成，因此后续重启绝不会把“已关闭”误当“尚未迁移”而重新灌开。已有非空环境值仍优先于旧账号值，迁移可安全重跑。

切换完成后运行时读写只使用环境列。旧账号列暂留，不双写：双写会让账号移动后旧设置继续跟随账号，重新制造本变更要消除的语义。回滚旧版本时旧列仍保留部署前快照，但环境级变更不会自动回写账号列，因此回滚前需明确接受回到部署前慢启动状态或执行人工反向迁移。

## Risks / Trade-offs

- [异常的一账号多环境绑定使账号级 RiskController 无法确定环境] → 镜像拒绝任取、记录可诊断冲突；部署前只读检查重复绑定，人工修复，不自动删除数据。
- [共享 PostgreSQL 中加列与回填同时影响 dev/ol] → 只做向后兼容加列和带一次性初始化标记的可重入迁移；部署前执行目标检查，若 dev/ol 共库则不做破坏性验证，真实换绑验收登记 backlog。
- [未绑定投影自行计算 day 与 controller 计算漂移] → 两者复用同一上海自然日 helper；一旦绑定，立即切换为 controller 的同源投影，未绑定态绝不声称 clamp 已生效。
- [旧二进制回滚看不到新环境设置] → 保留旧账号列和部署前值；一次性初始化标记只服务新版本，不声称无损回滚，回滚步骤明确状态边界。
- [环境换绑与配额调用短暂竞态] → 注册事务提交后、对外确认前刷新同步镜像；旧账号与新账号的下一次调用分别解除/应用设置。

## Migration Plan

1. 在 cloud 默认分支加入环境列自愈、环境慢启动 store/API、同步镜像和组合 provider，保持旧列存在。
2. 服务启动时在 `accounts` 表就绪后运行可重入回填，并输出回填数量；发现重复账号绑定时告警但不猜测、不改数据。
3. 运行 cloud acceptance/full/typecheck 与 Edge 聚焦 UI/acceptance/typecheck，严格校验 OpenSpec。
4. 部署 dev 前按规范确认目标与共享数据库边界，备份并只读检查重复绑定；部署后验证服务、监听、健康、日志和 PostgreSQL。
5. 用非 OL 在跑的 Facebook 测试环境验证：开启后换绑测试账号，确认环境设置保留、新账号受限、旧账号解除且无需重启。若共库或账号排他条件不成立，登记真机 backlog，不宣称完成该项。
6. 回滚代码时保留新增列；如必须恢复旧行为，旧账号列仍保持部署前值。不得把环境列自动覆盖回账号列，除非另行审批迁移范围。

## Open Questions

无。产品归属已由本次需求明确为环境；异常多绑定按现有诚实边界 fail-closed 并交由运维修复。
