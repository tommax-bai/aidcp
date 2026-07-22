## Context

Cloud 已有三份 Facebook 群事实：`facebook_group_target` 全局目标目录、`facebook_group_membership` 一群全局唯一归属的成员账本，以及 `facebook_group_join_audit` 结果审计。`FacebookGroupJoinScheduler` 同时服务后台排期和人工 `/comment --join[=<url>]`；后台排期已经挂在每分钟 `ContentScheduler` 动作循环里，但当前只受全局 `AIDCP_FB_GROUP_JOIN_AUTO`、RiskController 日额度和会话额度控制，没有每账号开关/周历/运营上限。候选认领也直接扫描全局目标池。

账号分组当前不是独立实体，而是 `accounts.group_label` 的可空、trim 后最长 64 字符标签。现有 dev 数据包含大量全局群目标，但只有部分 Facebook 账号已分组，因此本变更必须默认关闭且禁止隐式全量映射。

本变更依赖 `platform-aware-account-automation` 提供的平台注册表动作声明和 Console 动态动作容器；两个变更串行集成。Edge 的 `group.join` 命令、观察/判断/点击/验证链和 protocol v2 均不改变。

## Goals / Non-Goals

**Goals:**

- 一个群目标可适用于多个账号分组，账号自动/裸手动认领只在自己当前分组范围内发生。
- 保持全局“一群只归一个账号”的原子锁和现有真实成员账本。
- 为每个 Facebook 账号提供默认关闭的独立自动加群开关、动作时段、运营日上限和最近自动执行结果。
- 继续复用现有调度心跳、单飞、风险、会话额度、全局 kill switch 与真实执行链。
- 提供可批量维护的 Cloud/Console 管理面，并让缺映射、缺分组和失配都 fail-closed。

**Non-Goals:**

- 不把同一群开放给多个账号重复加入；这需要改变全局唯一成员模型和更大风控评审。
- 不把 `accounts.group_label` 规范化成新的账号分组实体，也不自动级联“分组重命名”。
- 不自动把现有目标映射到所有分组，不替运营猜测业务归属。
- 不改变明确指定 URL 的人工覆盖权限、Edge/protocol 或群内评论策略。

## Decisions

### 1. 目标事实保持唯一，新增账号分组映射侧表

新增 `facebook_group_target_scope`：

- `group_url` 外键指向目标目录并级联删除；
- `account_group_label` 保存与 `accounts.group_label` 同口径的非空标签；
- `(group_url, account_group_label)` 为主键，并为 label 建候选查询索引；
- 一个目标可有多行映射，从而适用于多个账号分组。

不在 `facebook_group_target` 放单个 `group_label`，因为那无法表达多归属；也不复制目标行，因为 canonical URL、门槛判断和 enabled 状态必须保持一份事实。范围写入采用“给所选目标替换完整分组集合”的一等存储方法，事务内校验目标存在、标签规范化且当前至少由一个 Facebook 账号使用，写后回读。最后一个账号离开某标签时映射可以暂时休眠，不自动删除；同名标签未来恢复时重新生效，这是当前标签模型的既有语义。

### 2. 导入缺省不清范围，显式分组集合才替换

单条和文件导入界面增加可选“适用账号分组”多选，作为本次提交的公共范围。请求未携带该字段时，既有目标的映射保持不变，新目标保持无映射；显式提交集合（包括空集合）时才替换本次目标的映射。群列表支持账号分组过滤、行内标签展示和勾选行批量替换范围。

相比在 CSV 每一行增加不易校验的自由文本，本期使用导入批次公共多选，直接复用服务端返回的现有 Facebook 账号分组词表，降低拼写漂移。以后如确有逐行范围需求，可在保持“缺字段不清空”契约下增量扩展。

### 3. 候选查询由账号当前分组驱动，继续使用全局唯一锁

自动 `claimNext(accountId)` 和裸人工 `/comment --join` 在同一事务/语句中：

1. 读取账号当前 `group_label` 且确认平台为 Facebook；
2. 只扫描与该 label 有 scope 映射、target enabled、gating 可尝试且全局未被 membership 占用的目标；
3. 仍以 `UNIQUE(group_url)` + `ON CONFLICT DO NOTHING` 原子认领。

未分组、无映射或候选已被其它分组账号抢先占用均返回 `no_targets`，绝不回落全局池。多个分组映射只是多个候选池入口，不放宽一群一账号锁。

明确 `/comment --join=<url>` 继续走 `ensureTarget + claimSpecific` 人工覆盖：新目标仍 `enabled=false`，不会泄漏进自动池；全局唯一归属、平台、kill switch、单飞和边端物理闸保持不变。

### 4. 执行前重验范围，失配只释放未完成分配

账号分组或 scope 可能在“认领后、导航前”变化。因此 scheduler 在任何自动/裸手动的已有未完成 assignment 执行前重新读取账号分组和映射：

- `assigned/joining` 失配：以条件写释放该 membership 行并返回 `scope_mismatch`/`no_targets`，不导航、不点击；
- `joined/pending/gated/...` 等已形成平台/判断事实的行不因 scope 变化删除或改成 `left`；scope 只控制未来候选；
- 明确 URL 的人工覆盖不做 scope 重验，但仍不能抢走其它账号已拥有的 group URL。

### 5. 自动加群配置单独持久化并聚合进账号自动化目录

新增 `facebook_group_join_automation_config`，以 `account_id` 为主键，保存 `enabled`（默认 false）、`daily_cap`（默认 0）、可空 168 位 `week_mask`、`updated_at/by`。该领域配置不塞入通用 `account_content_schedule` 动作列；Cloud 在 `GET /api/content-schedule` 聚合后把 Facebook `join_group` 动作状态与 `availableActions` 一并投影给统一页面。

`week_mask=null` 表示跟随账号通用内容自动时段；非空表示额外收窄。自动加群有效时窗为：

`effectiveActiveWeekMask ∩ effectiveContentActiveMask ∩ (joinWeekMask ?? 全 1)`

任一必需公共掩码非法仍沿用 content schedule 的 fail-closed。错峰继续使用 `hash(accountId + localDate + 'join') % 60`，不增加第二个 cron 或固定分钟配置。

写接口只接受 Facebook 账号、boolean、受限非负整数和 null/合法 168 位掩码；写后回读。关闭时保留 cap/mask 便于再开，但 scheduler 必须同时要求账号总开关和 join enabled。

### 6. 多层额度不混淆单位

每日准入为 `joinedToday < min(config.dailyCap, RiskController.effectiveQuotas().day.join_group)`；每次执行仍调用既有 `canDo('join_group')` 与剩余 session `join_groups` 预算。配置 cap 只是运营收窄，不能抬高风控日额度或会话额度。全局 `AIDCP_FB_GROUP_JOIN_AUTO` 继续作为 emergency kill switch；任何一层关闭/为零都不执行。

### 7. 最近结果来自带来源的审计，不从 membership 猜测

`facebook_group_join_audit` 增量增加可空 `trigger_source`（`scheduled`、`manual_pool`、`manual_specific`、`shadow`），所有新执行路径明确写入。目录只查询该账号最新 `scheduled` 行，返回 outcome、reason、groupUrl、createdAt；没有记录返回 null。旧审计行不补猜来源，避免把人工结果伪装成自动结果。

### 8. Console 两处各司其职

- `/facebook-groups`：显示/筛选适用账号分组，导入时可选范围，表格多选后批量替换范围，并警告无范围目标不会被自动认领。
- `/content-schedule` 的 Facebook 单平台视图：按服务端 `availableActions` 渲染“自动加群”的开关、日上限、跟随/自定义周历和最近结果；全部平台仍只显示摘要。

Console 不根据 `group_join` 指标 capability 推断动作；它只消费 Cloud 聚合 DTO。

## Risks / Trade-offs

- [标签不是规范化实体，重命名不会级联] → 只允许选择当前 Facebook 账号真实使用的标签，保留休眠映射并在 UI 显示；规范化分组实体另立变更。
- [现有大量目标无映射，升级后候选骤减] → 每账号 config 默认关闭、无隐式全量映射、群页提供批量映射与无范围计数；dev 先配置少量账号/目标验证。
- [两个分组同时映射同一群产生竞争] → 保留数据库 `UNIQUE(group_url)` 和原子 claim；失败方继续其它候选，不允许双占。
- [范围在执行中变化] → 导航/点击前服务端重验，失配释放未完成 assignment；已 joined 事实永不因配置变化被篡改。
- [最近结果被人工操作污染] → 审计增加 trigger source，只投影 scheduled；旧 null 来源不推断。
- [配置 cap 被误解为平台安全额度] → API/UI同时呈现配置值和当前有效日上限，并明确 RiskController/会话额度仍可进一步收紧。

## Migration Plan

1. 合并 `platform-aware-account-automation`，确认 Cloud/Console 平台动作契约稳定。
2. 部署 Cloud additive schema：scope、per-account config、audit source；不写现有映射、不启用任何账号。
3. 部署 Console 群范围管理和 Facebook 自动加群动作；运营先为少量目标批量映射、为一个 dev Facebook 账号配置低 cap/窄时段。
4. 以 shadow/禁点击和真实低量各验证一次候选范围、审计来源、时窗/额度、全局唯一锁和最近结果。
5. 回滚应用代码时保留新增表/列（旧代码忽略）；若需重新启用旧逻辑必须显式回滚代码，不能靠自动迁移猜测。OL 不在本变更默认部署范围。

## Open Questions

- 无。账号分组标签的实体化和“一群多账号”均明确留待独立变更。
