## Why

视频号“互动回复设置”把运行模式、草稿生成、发送许可、渠道自动发送和即时写闸以相同层级重复呈现，管理员需要多次表达同一个意图，并且能够保存“仅草稿但允许发送”“自动发送但禁止发送”等实际无效或误导的组合。需要在不削弱 Cloud 硬门禁的前提下，把普通策略收敛为可直接理解的处理方式。

## What Changes

- 把“运行模式 + 生成草稿 + 允许发送”合并为一个账号级“回复处理方式”：不自动处理、只生成草稿、人工审核后发送、低风险模板自动发送。
- 继续写入冻结的 `mode`、`generateDrafts`、`sendReplies` DTO，但由所选处理方式确定性映射，管理界面不再允许互相矛盾的自由组合。
- 把评论/私信的 `enabled` 表达为“处理该渠道的互动”；只有选择低风险自动发送时才展示渠道自动发送范围。
- 把规则级 `allowAutoSend` 以单调收紧的“必须人工审核”语义呈现；把 AI 润色明确标记为必须人工审核，避免与自动发送形成假承诺。
- 将账号写总闸和评论/私信即时写开关保持在独立的“即时运行控制”区域；Cloud RiskController、身份、capability、幂等和待核验门禁继续只读展示且不可绕过。
- 保留 draft/published、CAS、发布确认、模拟预览和权限语义；不修改 Cloud/Edge 协议、API schema 或发送状态机。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `console-panel-api`: 视频号账号级回复设置 SHALL 用单一、无矛盾的处理方式表达普通管理员意图，并把渠道限制、即时运行控制、不可关闭硬门禁和预览权限清晰分区。

## Impact

- `aidcp-console`: `WechatChannelsReplySettings` 的基本策略、渠道策略、规则编辑文案与测试。
- `aidcp` control repo: 本 change 的设计、规格、任务与验证证据。
- Cloud/Edge/API schema: 无行为或字段变更；现有 fail-closed 门禁保持不变。
- 部署：Console 运行时 UI 变化完成验证后部署到 `dev`；不构建 Edge 安装包，不执行真实视频号写操作。
