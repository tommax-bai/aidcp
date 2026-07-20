## Context

视频号回复配置当前由 `ReplyConfigStore` 以 `(platform, account_id, config_version)` 保存，internal API、Console 抽屉和 `ReplyWorkflow.generate()` 都按 `accountId` 读取。`interaction_reply_jobs` 只保存账号内的 `config_version`，账号下线清理也会删除该账号的模板、规则和 profile。另一方面，账号表已经有可运营编辑的 `group_label`，但它只是标签而不是稳定 group entity。

本变更跨 Control、Cloud 与 Console，并涉及版本归属、历史任务引用、迁移和权限边界。Edge 协议不变；策略选择仍由 Cloud 负责，账号最终风险状态仍由 `RiskController` 单写。

## Goals / Non-Goals

**Goals:**

- 一份已发布配置服务一个视频号分组，未分组账号共享一份默认配置。
- 分组选择、配置版本和历史任务引用可审计、可回放，不依赖可变标签解释历史。
- 账号换组或分组发布只影响新任务；已生成任务继续使用原不可变快照。
- 保持账号级 runtime controls、身份、熔断、风控和计数边界。
- 提供无破坏的账号级配置盘点、冲突识别、shadow 对比和显式切换。

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

每个 `(scope_id, config_version)` 版本行以 JSONB 子文档原子保存 policy、templates、rules 和 profiles；发布后整行不可变。这样一次 CAS draft mutation 与一次 publish 都只需要锁定 scope head 并写一个完整快照，避免跨四组表复制产生部分版本。旧账号级规范化表保留为迁移只读源，避免上线 migration 直接重写或删除历史数据。

选择它而不是“发布时复制到每个账号”，因为复制会产生部分成功、账号新增补拷贝和漂移问题；也不使用幽灵账号承载共享配置，避免破坏账号 FK 和下线语义。

### 2. 解析规则只有 group 或 default 两条路径

Cloud 提供唯一 `resolveEffectiveReplyConfig(accountId)`：

1. 读取账号并校验 `platform='wechat_channels'`；
2. `group_label` 非空时精确查 group scope；没有已发布版本则返回 `group_config_missing`；
3. `group_label` 为空时查 default scope；没有已发布版本则返回 `default_config_missing`；
4. 返回 scope metadata 与不可变 published snapshot。

有分组但缺配置时不回落 default，防止配置错误被静默掩盖。默认策略只覆盖未分组账号。最终 scoped 模式不再读取账号级 override。

### 3. 任务冻结 scope + version

`interaction_reply_jobs` 加性增加 `config_scope_id`；生成成功时同时保存 `config_scope_id` 和 `config_version`。审批、编辑、发送校验按这两个字段重载历史快照，不根据账号当前分组重新解析。已有仅带账号 `config_version` 的任务继续走 legacy snapshot 读取，直到自然结束或清理。

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

账号级 `interaction-runtime-controls` 保留。旧账号 reply-config 写路径在迁移期返回显式 deprecated 元数据，scoped cutover 后拒绝新写；不会把账号请求偷偷改写到整个分组。

权限继续复用 `interaction.config.view/edit/publish/preview` 与 `interaction.audit.view`。审计事件按 `scope_id` 记录，不为每个成员复制；账号有效来源查询只展示 scope 类型、标签、版本和状态。

### 6. Console 以策略目录为主入口

新增“视频号策略”页面，列出默认 scope、账号中出现的 group label 以及已有零成员 scope，展示成员数、草稿/发布版本和缺失状态。策略编辑器以 scope 为上下文；预览真实互动时选择一个合法成员账号。

账号页继续编辑分组和 runtime controls，并展示“来自分组 X / 默认策略 / 缺少配置”。不再从账号行直接编辑共享策略，避免用户误以为只影响当前账号。

### 7. 分阶段兼容迁移

Cloud 支持 `legacy | shadow | scoped` 三态解析模式：

- `legacy`：运行时仍使用账号配置；新 scope API 可准备配置；
- `shadow`：仍执行 legacy，但记录 scoped 解析覆盖率和配置 fingerprint 差异，不记录正文；
- `scoped`：按 group/default 执行，缺失 fail closed。

默认保持 `legacy`，只有覆盖报告显示所有活跃视频号账号均有确定的目标 scope 且冲突已处理后，才允许切换 scoped。该模式是迁移门禁，不是长期账号 override。

## Risks / Trade-offs

- [同组现有账号配置不一致] → 迁移工具只输出 fingerprint、版本和差异摘要；不自动选赢家，要求运营显式选择来源或重建策略。
- [账号换组导致策略立即变化] → 账号分组写接口在 scoped 模式返回新 effective source；新任务使用新 scope，历史任务继续冻结旧 scope/version。
- [自由文本标签出现近似重复] → 沿用当前 trim 后精确匹配；Console 显示成员数和零成员 scope，后续可单独引入 group entity/rename 流程。
- [单账号下线误删共享配置] → offboarding 只删账号互动数据、legacy 配置和 runtime controls，不删除 scope 配置。
- [迁移影响 dev/ol 共享数据库] → migration 仅加表/加列，不删旧表；部署前仍必须校验环境数据库边界，任何破坏性清理另行审批。
- [preview 混淆配置与账号上下文] → API 强制合法代表账号，回包同时标记 scope 与 account，不把预览说成真实发送。

## Migration Plan

1. 部署加性 schema、scope store/API、Console 管理页和 `legacy` 模式；旧运行时行为不变。
2. 盘点现有账号级 published 配置，按目标 group/default 计算无正文 fingerprint；一致项可复制到 scope draft，冲突项形成待处理清单。
3. 运营发布所有需要的 group/default scope；运行 `shadow`，确认活跃账号解析覆盖率、版本和预期来源。
4. 在命名环境显式切换 `scoped`，验证生成、审批、发送门禁、客户投影、换组和 offboarding。
5. 观察期后冻结旧账号写 API；旧表和 legacy job 读取保留到数据保留窗结束。删除旧表属于后续独立破坏性 change。

回滚只需把解析模式恢复为 `legacy`；新 scope 数据保留，不需逆向 DDL。已用 scope 生成的任务仍按冻结的 scope/version 完成或人工终止。

## Open Questions

- 无。默认策略只覆盖未分组账号、有组缺策略 fail closed、最终无账号级 override，均按本次用户确认实施。
