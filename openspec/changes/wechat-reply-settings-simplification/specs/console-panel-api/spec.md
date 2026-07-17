## ADDED Requirements

### Requirement: 视频号回复设置必须以单一处理方式表达管理员意图

管理后台 SHALL 把 `mode`、`generateDrafts` 与 `sendReplies` 表达为一个账号级“回复处理方式”，只提供“不自动处理，仅收取互动”“只生成回复草稿”“人工审核后发送”“低风险模板自动发送”四种互斥选择。Console MUST 将选择确定性映射到冻结 DTO，MUST NOT 让普通管理员保存互相矛盾的自由组合；Cloud API schema 与硬门禁保持不变。

#### Scenario: 四种处理方式写入规范组合
- **WHEN** 管理员依次选择四种处理方式并保存策略草稿
- **THEN** Console 分别写入 `draft_only/false/false`、`draft_only/true/false`、`review_before_send/true/true`、`auto_safe/true/true` 的 `mode/generateDrafts/sendReplies` 组合

#### Scenario: 历史非规范组合按不扩权规则加载
- **WHEN** Cloud 返回生成关闭、发送关闭或仅草稿但发送开启等历史非规范组合
- **THEN** Console SHALL 显示不扩大当前写权限的处理方式，且未获管理员主动选择更高方式时保存 MUST NOT 把 false 权限静默改为 true

### Requirement: 渠道和规则配置必须只表达参与范围或进一步收紧

评论与私信的 `enabled` SHALL 呈现为“处理该渠道的互动”，并明确它不等于停止收取。渠道自动发送范围 MUST 仅在账号处理方式为低风险自动发送时展示。规则级 `allowAutoSend` SHALL 以“必须人工审核”的收紧语义呈现；启用 AI 润色的规则 MUST 强制人工审核，MUST NOT 向管理员暗示 AI 润色结果可以自动发送。

#### Scenario: 非自动模式不重复询问渠道自动发送
- **WHEN** 账号处理方式为不自动处理、只生成草稿或人工审核后发送
- **THEN** 评论和私信区域不展示“允许低风险自动发送”选择，渠道参与开关仍可独立配置

#### Scenario: 规则人工审核语义不提升权限
- **WHEN** 管理员勾选“此规则必须人工审核”或为规则启用 AI 润色
- **THEN** Console 写入 `allowAutoSend=false`；取消人工审核只恢复继承上层自动化上限，最终自动发送仍受渠道范围与全部 Cloud 硬门禁约束

### Requirement: 版本化策略、即时运行控制与系统硬门禁必须清晰分区

管理后台 SHALL 把需要保存并发布的回复策略、保存后立即生效的 runtime controls、不可关闭的 Cloud 硬门禁分成可辨识区域。账号写总闸、评论回复与私信文本发送 MUST 保留为即时刹车；Cloud RiskController、身份、capability、幂等和待核验门禁 MUST 保持只读且不可由普通管理员关闭。策略保存与原子发布边界 MUST 保留。

#### Scenario: 即时停写不伪装成策略模式
- **WHEN** 管理员关闭账号写总闸或某渠道即时写开关
- **THEN** Console 明确显示这是立即生效的运行控制，读取、草稿和已发布策略保持原语义，真实发送仍被 Cloud 拒绝

#### Scenario: 发布摘要只展示有效用户意图
- **WHEN** 管理员准备发布回复配置
- **THEN** 发布确认 SHALL 展示单一回复处理方式、渠道参与/自动范围和当前即时写状态，MUST NOT 再要求分别理解 `mode` 与“允许发送”重复开关

### Requirement: 模拟预览拒绝必须说明链路未运行

无副作用预览 SHALL 与真实发送设置分离。缺少 `interaction.config.preview` 时，Console MUST 明确说明 Cloud 预览链路未运行；私信预览缺少权限时 MUST 同时说明还需要 `interaction.dm.view_full`。权限拒绝 MUST NOT 被呈现为风险评审结果或发送硬门禁结果。

#### Scenario: 评论预览权限不足
- **WHEN** 评论预览返回 `INTERACTION_PERMISSION_DENIED`
- **THEN** Console 显示当前后台账号缺少模拟预览权限且本次预览未运行，不展示伪造的规则、模板或风险结果

#### Scenario: 私信预览需要额外原文权限
- **WHEN** 私信预览返回 `INTERACTION_PERMISSION_DENIED`
- **THEN** Console 显示私信预览同时需要 `interaction.config.preview` 与 `interaction.dm.view_full`，且本次预览未运行
