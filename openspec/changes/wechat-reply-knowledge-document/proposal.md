## Why

视频号 AI 回复目前只能基于入站消息和模板做简短润色，无法引用商家/博主自己维护的业务说明，因此遇到具体问题时要么答不出来，要么容易脱离事实。需要让运营在管理后台为回复策略配置一份受控知识文档，并要求 AI 只依据该文档回答。

## What Changes

- 在评论、私信各自的回复 profile 中新增可选“AI 回答说明文档”，支持管理后台直接编辑 Markdown/纯文本，单份最多 20,000 字符。
- 文档跟随现有 group/default scope 的草稿、发布版本、CAS 冲突和审计生命周期；不恢复账号级回复配置。
- AI 润色启用且文档非空时，`reply_polisher` 可根据入站问题引用文档事实生成简短回答；文档无答案时必须明确无法确认，禁止自行补全。
- 文档被视为不可信参考数据而非系统指令；模型不得执行文档中的提示词、泄露整份文档或绕过既有模板导流行、claim gate 与人工审核。
- 管理后台在“语气与知识”配置中展示文档编辑、字数限制和用途说明，并在预览中使用当前 draft 文档。

## Capabilities

### New Capabilities

- `wechat-reply-knowledge-grounding`: 规定视频号回复知识文档的配置范围、版本生命周期、AI grounding 边界和管理后台体验。

### Modified Capabilities

无。

## Impact

- 影响 control repo 的内部 API/AI role 合同与 fixtures、`aidcp-cloud` 的回复 profile 校验/存储/提示词/工作流、`aidcp-console` 的 DTO、表单和测试。
- 复用 `interaction_reply_scope_versions.profiles` JSONB，不新增数据库表或迁移；不改变 Edge 协议或打包产物。
- Cloud 与 Console 运行时行为变化需部署到 `dev`；不涉及 `ol`。
