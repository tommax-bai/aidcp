## Context

Facebook 批量创建在 Edge 本机把账号资料导入 AdsPower，并通过 customer-auth provisioning intent 逐环境建立客户归属；创建阶段不启动环境，也不验证平台登录。真实 `accountId` 只有在环境后续成功登录、Edge 握手并由 Cloud 写入 `client_environments.account_id` 后才成立。现有单账号人设生成绑定于在线 Edge session，客户端必须先知道目标环境并逐账号调用，既不适合批量，也会把本地未知状态误当成“未设置”。

Cloud 已具备四块可复用能力：`client_env_scope` 的客户权威归属、`client_environments` 的持久环境→账号绑定、`persona_config` 的缺失/已绑事实、`PersonaGenerator` + persona facade 的生成校验和热加载写入。当前生成器要求非空关键词，Facebook 还要求显式发言语言；系统没有默认/兜底人设。

## Goals / Non-Goals

**Goals:**

- Edge 只提交“为当前客户快照并补齐 Facebook 缺失人设”的意图，不提交账号 ID、账号状态或敏感导入资料。
- 一次补齐运行覆盖提交时当前客户全部权威归属的 Facebook 环境；已绑定账号立即处理，未绑定环境在后续首次握手后继续处理。
- 只创建缺失人设，使用数据库原子 create-if-missing 防止生成在途时覆盖人工刚写入的人设。
- 运行和目标持久化、请求幂等、Cloud 重启可恢复；失败有界且结果状态真实。
- UI 只增加默认开启的自动补齐开关和整批一次的发言语言选择，不增加弹窗、账号列表、统计或跳转。

**Non-Goals:**

- 不把 Facebook 账号、密码、2FA、cookie、代理或客户端推测的 accountId 上传 Cloud。
- 不自动启动环境、不代替平台登录、不把未绑定环境猜成某个账号。
- 不覆盖、更新或重生成人工/既有的人设；已有人设只记录跳过。
- 不新增客户端任务中心、进度 UI、通知弹窗或全局永久自动补齐开关。
- 不打包 Edge 安装器；本次只交付源码、Cloud dev 部署和协议/规格同步。

## Decisions

### 1. 上传后创建一次 Cloud 运行并快照环境，而非客户端传账号或永久策略

Edge 在 Facebook 批量创建产生至少一个已完成客户归属的环境后，调用 customer-auth `POST /persona-auto-fill/runs`。请求只带 `platform=facebook`、`strategy=facebook_auto_v1`、本批 `writingLanguage`，并用 `Idempotency-Key` 防网络重试重复建运行。

Cloud 在同一事务内以 JWT `userId` 查询 `client_env_scope(source=admin)` 与 `client_environments(platform=facebook)`，把当时所有环境写成运行目标。这样刚建但尚未登录的环境也在目标内，随后登录可继续；以后新建的无关环境不会被一个旧运行悄悄纳入。永久客户策略虽更省表，但缺少关闭入口且会扩大用户当次授权范围，因此不采用。

### 2. 目标解析始终复核当前归属、绑定、平台与争用

处理每个目标时 Cloud 现读：运行所属客户仍拥有该环境、环境平台为 Facebook、绑定账号在 `accounts` 中且平台为 Facebook、同账号不存在跨客户争用。任一条件不成立即等待绑定或 fail-closed，绝不从环境名、导入行、cookie UID 或客户端状态猜账号。

`onEdgeRegistered` 完成 `registerEnvironments(... accountId)` 后触发该 `envKey` 的待运行重检；启动时同时恢复数据库中未终结运行。客户端关闭不影响 Cloud 继续执行。

### 3. 运行/目标两表表达持久状态与幂等

新增：

- `client_persona_auto_fill_runs(run_id, user_id, idempotency_key, platform, strategy, writing_language, state, created_at, updated_at)`，`(user_id,idempotency_key)` 唯一。
- `client_persona_auto_fill_targets(run_id, env_key, account_id, state, attempts, reason, updated_at)`，`(run_id,env_key)` 主键。

运行态为 `running/completed/completed_with_failures`；目标态为 `waiting_binding/pending/running/succeeded/skipped_existing/failed`。Cloud 启动时把陈旧 `running` 目标恢复为 `pending`，每目标最多两次编排尝试；生成器内部仍保留自己的有限模型重试。API 只回运行是否已接受/幂等，不回账号 ID 或敏感目标明细。

### 4. 自动策略是显式生成输入，不是假默认人设

`facebook_auto_v1` 内置一组非敏感、广覆盖的 Facebook 内容方向组合（生活、美食、旅行、健身、宠物、亲子、科技、职场、时尚、娱乐、摄影、汽车等），以稳定账号哈希选择一组，并追加受控语气与 `like_affinity:normal`。发言语言由用户在批量表单为整批选择一次，只允许 `zh-CN/en/vi`。

服务继续调用现有 `PersonaGenerator.generate`，以 `facebook-auto-v1:<accountId>` 作为差异化种子，产物继续走现有 soul 结构校验。此策略仅在用户显式保留勾选并成功提交运行时生效；生成失败不会回落模板或空人设。

### 5. 人设写入增加原子 create-if-missing

现有 `setPersona` 是 upsert，无法满足“生成在途时人工刚写入也绝不覆盖”。`PersonaStore`/facade 增加内部 `setPersonaIfMissing`：先做账号存在与 soul 校验，再以 `INSERT ... ON CONFLICT DO NOTHING RETURNING` 原子创建。返回未创建时目标记为 `skipped_existing`；只有真实插入才触发 `onBound/onChanged`，保持运行时唤醒和 UI 绑定态单写通道不变。

### 6. Edge 创建成功与自动补齐接受态分开

环境创建/归属成功不等于补齐运行已建立。Edge 对 customer-auth 请求做一次有界重试：接受则回 `personaAutoFillScheduled=true`；失败时环境创建仍保持成功，但回执明确“环境已创建，云端自动补齐未启动”，不染绿自动补齐。部分创建已产生环境时也提交一次运行，使已创建且已归属的目标不被遗留。

## Risks / Trade-offs

- [大量账号同时触发 LLM 成本与压力] → Cloud drain 使用小并发、运行/账号去重和目标尝试上限；API 只排队不等待模型。
- [同一账号出现在多个环境或多个运行] → 进程内按 accountId 合并在途，写入再以数据库 create-if-missing 兜底；后来者记录跳过。
- [环境长期未登录导致运行长期 running] → 目标诚实停在 `waiting_binding`；不猜账号、不把运行宣称完成。
- [生成期间客户撤权或环境换号] → 生成前后现读并在原子写前复核目标账号；撤权/冲突 fail-closed。
- [Cloud API 暂不可用] → 不回滚已创建 AdsPower 环境；Edge 明确提示自动补齐未启动，凭据仍不外泄。
- [自动方向与用户预期不一致] → v1 使用明确版本化、非敏感方向池与单批发言语言；既有人设不覆盖，后续策略调整通过新版本而非静默改旧运行。

## Migration Plan

1. Cloud 先加入幂等表、create-if-missing、补齐服务和 customer-auth 端点，运行时未收到新请求即零行为变化。
2. 部署 Cloud 到 dev，验证 customer-auth 健康、表建立和旧 Edge 兼容。
3. Edge 增加批量表单开关/语言选择和新端点调用；不构建安装器。
4. 回滚 Edge 可停止新运行创建；Cloud 已建运行继续按当次授权收敛。若需紧急停止，可先回滚 Cloud 服务代码，表与已有 `persona_config` 保留。

## Open Questions

无。
