## Context

视频号回复配置当前由 `ReplyConfigStore` 以 `(platform, account_id, config_version)` 保存，internal API、Console 抽屉和 `ReplyWorkflow.generate()` 都按 `accountId` 读取。`interaction_reply_jobs` 只保存账号内的 `config_version`，账号下线清理也会删除该账号的模板、规则和 profile。另一方面，账号表已经有可运营编辑的 `group_label`，但它只是标签而不是稳定 group entity。

本变更跨 Control、Cloud 与 Console，并涉及版本归属、历史任务引用、迁移和权限边界。Edge 协议不变；策略选择仍由 Cloud 负责，账号最终风险状态仍由 `RiskController` 单写。

## Goals / Non-Goals

**Goals:**

- 一份已发布配置服务一个视频号分组，未分组账号共享一份默认配置。
- 分组选择、配置版本和历史任务引用可审计、可回放，不依赖可变标签解释历史。
- 账号换组或分组发布只影响新任务；已生成任务继续使用原不可变快照。
- 保持账号级 runtime controls、身份、熔断、风控和计数边界。
- 立即退役账号级策略读取、写入和迁移盘点；清理已确认的测试策略数据。

**Non-Goals:**

- 不新增 Edge WS v2 消息或让 Edge 选择策略。
- 不让默认策略覆盖有分组但缺策略的账号，也不保留长期账号级策略 override。
- 不把账号配额计数聚合成分组配额。
- 不把自由文本 `group_label` 立即重构成全系统通用 group 外键；本变更只为回复配置建立稳定 scope identity。

## Decisions

### 1. 使用稳定 scope identity，不直接用标签作为版本主键

新增 `interaction_reply_config_scopes`：

- `scope_id`：稳定 opaque ID；
- `scope_type`：`group | default`；
- `group_label`：group scope 的当前精确标签，default 为 null；
- aggregate version、draft/published head 与审计字段；
- `UNIQUE(platform, scope_type, group_label)`，并以 partial unique index 保证每个平台只有一个 default。

每个 `(scope_id, config_version)` 版本行以 JSONB 子文档原子保存 policy、templates、rules 和 profiles；发布后整行不可变。这样一次 CAS draft mutation 与一次 publish 都只需要锁定 scope head 并写一个完整快照，避免跨四组表复制产生部分版本。旧账号级规范化表不再作为读取源；本次只清空其中的策略数据，物理表暂留以避免共享数据库上的 DROP/RENAME。

选择它而不是“发布时复制到每个账号”，因为复制会产生部分成功、账号新增补拷贝和漂移问题；也不使用幽灵账号承载共享配置，避免破坏账号 FK 和下线语义。

### 2. 解析规则只有 group 或 default 两条路径

Cloud 提供唯一 `resolveEffectiveReplyConfig(accountId)`：

1. 读取账号并校验 `platform='wechat_channels'`；
2. `group_label` 非空时精确查 group scope；没有已发布版本则返回 `group_config_missing`；
3. `group_label` 为空时查 default scope；没有已发布版本则返回 `default_config_missing`；
4. 返回 scope metadata 与不可变 published snapshot。

有分组但缺配置时不回落 default，防止配置错误被静默掩盖。默认策略只覆盖未分组账号。最终 scoped 模式不再读取账号级 override。

### 3. 任务冻结 scope + version

`interaction_reply_jobs` 加性增加 `config_scope_id`；生成成功时同时保存 `config_scope_id` 和 `config_version`。审批、编辑、发送校验按这两个字段重载历史快照，不根据账号当前分组重新解析。已有仅带账号 `config_version` 的历史任务保留审计记录，但不再读取账号旧快照；后续审批/编辑/发送以配置缺失 fail closed。

### 4. 账号安全门禁与共享策略相交，而非被共享策略替代

配置 scope 承载 policy、templates、rules、profiles 和限速参数。账号 `interaction_runtime_controls`、auth/identity/capability、write pause/circuit、幂等和 `RiskController` 继续逐账号检查；限速值可共享，但计数器和最终准入仍以执行账号为主体。

`account_name` 模板变量默认在执行时取已验证账号昵称；profile 可表达统一品牌自称，但不得把一个代表账号的昵称固化为整组事实。

### 5. API 分离配置作用域与执行账号上下文

新增 internal scope API：

- `GET /api/interaction-reply-config-scopes`
- `GET|POST /api/interaction-reply-config-scopes/:scopeId`
- scope 下的 policy/templates/rules/profile/initialize/publish/audit 路径
- `POST .../:scopeId/preview` 必须携带 `accountId`，并校验该账号当前属于该 group，或在 default scope 下确实未分组。
- `GET /api/accounts/:accountId/effective-reply-config` 返回只读解析状态和非敏感来源。

账号级 `interaction-runtime-controls` 和预览上下文读取保留。其余旧账号 reply-config 读写、预览、发布与审计路径统一返回已退役状态；不会读取已清理数据，也不会把账号请求偷偷改写到整个分组。

权限继续复用 `interaction.config.view/edit/publish/preview` 与 `interaction.audit.view`。审计事件按 `scope_id` 记录，不为每个成员复制；账号有效来源查询只展示 scope 类型、标签、版本和状态。

### 6. Console 以策略目录为主入口

新增“视频号策略”页面，列出默认 scope、账号中出现的 group label 以及已有零成员 scope，展示成员数、草稿/发布版本和缺失状态。策略编辑器以 scope 为上下文；预览真实互动时选择一个合法成员账号。

账号页继续编辑分组和 runtime controls，但不再展示账号策略来源或“查看策略”。账号表不再渲染通用“操作”列：运营状态标签承载暂停/恢复，风控标签承载状态操作，档位标签承载档位选择；视频号“运行控制”使用具名列，Facebook 配置入口附着平台标签。这样动作与所修改的事实列保持一一对应。

### 7. 立即退役账号旧策略

Cloud 固定使用 `scoped` 解析，不再接受环境变量切回 `legacy` 或 `shadow`。账号旧策略 API 和 migration inventory 一并退役。一次性清理只删除 `interaction_reply_configs`、`interaction_reply_config_versions`、`reply_templates`、`reply_rules`、`account_reply_profiles` 的账号策略行，以及对应配置实体审计；不删除账号、runtime controls、互动消息、回复任务、发送尝试、风险或 scoped 数据。

scope 尚未发布时生成/发送按既有 `group_config_missing` / `default_config_missing` fail closed。管理页先创建并发布需要的默认/分组策略，不从旧账号数据自动复制或选择赢家。

## Risks / Trade-offs

- [清理后 scope 尚未发布] → 明确 fail closed，并由“视频号策略”页从零创建；不恢复或自动搬运账号旧策略。
- [账号换组导致策略立即变化] → 账号分组写接口在 scoped 模式返回新 effective source；新任务使用新 scope，历史任务继续冻结旧 scope/version。
- [自由文本标签出现近似重复] → 沿用当前 trim 后精确匹配；Console 显示成员数和零成员 scope，后续可单独引入 group entity/rename 流程。
- [单账号下线误删共享配置] → offboarding 只删账号互动数据和 runtime controls，不删除 scope 配置。
- [清理影响 dev/ol 共享数据库] → 用户已确认旧账号策略均为测试数据；执行前仍需备份并核对精确行数，迁移只 DELETE 指定策略实体，不做 DROP/RENAME，不触碰其它数据域。
- [preview 混淆配置与账号上下文] → API 强制合法代表账号，回包同时标记 scope 与 account，不把预览说成真实发送。

## Migration Plan

1. 部署固定 scoped resolver、退役账号策略 API 和 Console 精简交互。
2. 在共享数据库执行前备份五张旧策略表及相关配置审计，复核行数与账号范围。
3. 执行一次性 DELETE 清理；验证五张旧策略表为 0，runtime controls、回复任务和 scoped 表数量不变。
4. 验证 default/group 缺配置明确 fail closed，并通过“视频号策略”页从零创建新配置。

数据回滚不能依赖运行模式开关；若清理错误，只能从部署前备份恢复被删的精确策略行。物理旧表的 DROP 属于后续独立 schema change。

## Open Questions

- 无。默认策略只覆盖未分组账号、有组缺策略 fail closed、无账号级 override、旧策略数据直接清理和账号表取消通用操作列，均按本次用户确认实施。
