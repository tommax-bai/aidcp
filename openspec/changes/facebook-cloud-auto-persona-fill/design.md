## Context

现有 Edge 已有一套账号人设浮层：用户选择语气、点赞倾向、内容偏好以及 Facebook 发言语言，预览完整 `soulYaml` 后确认。此前新增的自动补齐却绕开该人工确认：批量创建后或环境栏点击时只传语言，Cloud 以 `facebook_auto_v1` 为每个账号重新选择方向并调用 PersonaGenerator。这既不能保证账号拿到相同人设，也把 Cloud 从“权威筛选/写入者”扩大成了“替用户决定内容的生成者”。

Cloud 已具备可保留的安全基础：客户环境权威归属、环境→账号绑定、持久运行/目标、原子 `setPersonaIfMissing`、重启恢复和握手续跑。修正重点是替换运行输入与目标处理，不重建账号选择链。

## Goals / Non-Goals

**Goals:**

- 只有用户从 Facebook 环境筛选入口打开人设页面、人工选择并确认后才建立补齐运行。
- 人设页面内完成语言选择；环境栏和批量创建表单不再有独立语言控件。
- 客户端确定性生成一份完整、可预览且可校验的人设；同一次运行所有缺失账号写入逐字相同的 `soulYaml`。
- Cloud 只负责客户范围、平台、绑定、既有人设和跨客户冲突筛选，以及原子 create-if-missing；补齐路径不调用 LLM/PersonaGenerator。
- 保留无账号 ID、无环境 ID、无凭据上传，运行幂等、持久和结果诚实边界。

**Non-Goals:**

- 不改变单账号“账号人设”浮层原有的查看、更新和生成能力；只新增其批量模板模式。
- 不允许批量操作覆盖或更新任何已有 `persona_config`。
- 不把客户端本地环境列表或 `personaBound` 投影当成 Cloud 目标事实。
- 不新增账号列表、数量统计、任务中心或导入后自动操作。
- 不打包 Edge 安装器；Cloud 只部署到 dev。

## Decisions

### 1. 批量设置只从 Facebook 筛选入口进入

环境栏展开且筛选为 Facebook 时显示一个“批量设置人设”按钮。点击打开现有 `persona-pop`，切换为明确的批量模板模式：标题、提示和确认动作说明“仅应用到未设置账号”。其他筛选隐藏入口。

批量创建表单不再展示自动补齐开关或语言，创建 IPC 不携带任何人设字段，也不因创建结果触发补齐请求。这样环境导入/创建只有一个职责，人工人设授权不会被默认勾选代替。

### 2. 批量模式在客户端确定性构建一份人设

批量模式复用现有语气、点赞倾向、内容偏好和 Facebook 发言语言控件，但“生成人设”不再调用单账号 `persona.generate`。可信主进程根据这些受控选择构建 `Soul`：选择内容决定 identity/interests，语气原样进入 tone，点赞倾向映射为 behavior_guidelines，语言写入 `writing_language`；随后确定性序列化为 `soulYaml` 返回预览。

同一组选择总是得到同一份模板。用户可返回修改或重新预览；只有点击“确认批量设置”才提交 Cloud。单账号模式仍走既有按账号生成/确认链，不受影响。

### 3. customer-auth 只接收平台和已确认人设

`POST /persona-auto-fill/runs` 请求体严格为 `{ platform: "facebook", soulYaml }`，并继续要求 Idempotency-Key。账号/环境/客户选择器、`strategy`、独立 `writingLanguage` 及其他字段全部拒绝。Edge 主进程与 Cloud 都限制模板长度；Cloud 使用 `loadSoulFromYaml` 校验结构，并要求模板内存在合法 Facebook `writing_language`。

Cloud 从 JWT 确定客户，响应只回运行受理/幂等状态，不回账号 ID 或目标明细。

### 4. 运行持久化模板，目标只做筛选和原样写入

既有 `persona_auto_fill_runs` 非破坏性新增 `persona_soul_yaml TEXT`，内部策略标识扩展为 `selected_persona_v1`；保留 `writing_language` 仅作为从模板解析出的审计元数据，不再由独立 UI/API 字段提供。新运行在同一事务快照当前客户权威归属的 Facebook 环境。

目标处理仍复核当前归属、真实绑定、Facebook 平台、账号存在和跨客户冲突。已有有效人设直接 `skipped_existing`；缺失人设则把运行里的同一份 `persona_soul_yaml` 交给 `setPersonaIfMissing`。生成器、方向池、差异化种子和模型重试全部退出该路径。

### 5. 历史自动运行停止生成并 fail-closed

部署前已存在的 `facebook_auto_v1` 运行没有已确认模板。恢复时不得再调用模型；当目标进入处理时，以 `selected_persona_required` 记录失败并终结。这样回滚前创建的隐式授权不会在新版本上线后继续生成未知人设。

### 6. 等待绑定仍受原快照边界约束

当前快照内尚未建立真实账号绑定的环境保持 `waiting_binding`；后续首次握手只会把当次已确认模板应用到该环境解析出的缺失账号。运行不会吞入点击之后新增的环境，也不会猜测账号。已有账号在等待期间被人工设置时仍以 create-if-missing 跳过。

## Risks / Trade-offs

- [同一人设用于多个账号，同质化是产品意图] → 界面明确“这些账号将使用同一份人设”，只有人工确认才提交。
- [客户端模板构建不如 LLM 丰富] → 批量功能优先保证用户选择可解释、逐字一致和无额外模型行为；单账号生成能力仍保留。
- [历史运行没有模板] → 明确失败，不恢复隐式模型生成。
- [提交期间人工写入] → 数据库原子 create-if-missing 保住人工设置，批量目标记跳过。
- [客户端或 API 伪造非法 YAML] → Edge 主进程受控构建；Cloud 再做结构、语言、长度校验，非法请求不建运行。

## Migration Plan

1. Cloud 先扩展运行表和 API/服务，部署后旧 Edge 的 `strategy/writingLanguage` 请求被拒绝，且不会再建立自动生成运行。
2. 部署 Cloud 到 dev，验证新列、customer-auth 健康、旧运行 fail-closed 和无 PersonaGenerator 调用。
3. Edge 删除批量创建自动入口，加入 Facebook 筛选的人设浮层批量模式与所选模板请求；不构建安装器。
4. 回滚 Edge 只会失去新入口；已确认的新运行由 Cloud 按原模板继续。回滚 Cloud 前须确认不存在仍需处理的 `selected_persona_v1` 运行。

## Open Questions

无。
