## Context

Edge 当前将语气、点赞倾向和内容偏好交给 Cloud 的 `persona.generate`，Cloud 生成并持久化账号 soul。`Soul` 没有写作语言；Facebook 通用评论撰写器与定向评论器目前优先跟随目标帖语言，发布正文角色也没有账号级语言合同。Edge 已能按环境识别 Facebook，Cloud 握手后也会校验账号平台，因此平台边界可以两端同时守住。

Facebook 浏览器 UI 固定 `en-US` 是 DOM/动作识别稳定性要求，与本变更的“账号对外写作语言”正交。用户已明确 Facebook 不具备小红书式灵感创作能力，本变更不得借语言功能开放该入口。

## Goals / Non-Goals

**Goals:**

- 为 Facebook 账号提供中文、英文、越南语三选一的结构化写作语言。
- 让帖子和评论从首次产文开始使用该语言，并让去 AI 味/撞车等正文重写保持同一语言。
- 让 Edge 只在 Facebook 人设界面显示并按环境隔离选择，让 Cloud 成为保存与运行时读取的权威。
- 审核前暴露最终文本；审核后发布执行器不翻译、不重写。
- 对缺配置、非法值和明显语言不匹配 fail-closed，并保留可诊断拒因。

**Non-Goals:**

- 不开放 Facebook `publish_from_inspiration`，不增加 Facebook 灵感池或任意 URL 评论能力。
- 不改变 Facebook 浏览器界面 locale、AdsPower 指纹、cookie、代理或时区。
- 不改变小红书/视频号的人设字段、评论语言和发布行为。
- 不在 Edge 引入模型、翻译器或数据库访问；不在提交发布动作前临时翻译已审文本。

## Decisions

### 1. 语言是 soul 的受控顶层字段，不是语气或关键词

Cloud 定义 `WritingLanguage = 'zh-CN' | 'en' | 'vi'`，在 soul YAML 中持久化为 `writing_language`。`PersonaGenerator` 在 LLM 产出通过结构校验后由代码确定性注入该字段；模型不得自行决定或改变它。

备选方案是把 `language:vi` 混进 `keywordSelections`，但这会污染自由关键词、绕过类型校验，并让后续消费者不得不重新解析字符串，故不采用。另一个备选是独立数据库列；当前 `persona_config` 已把完整 soul 作为账号级热加载事实源，新增列会产生双写与漂移，故不采用。

### 2. Edge 只提交一次，运行时角色从账号 soul 读取

`persona.generate` 增加可选类型字段 `writingLanguage` 以保持协议解析兼容；Cloud 对已验证为 Facebook 的会话要求它必须存在且合法，对非 Facebook 会话拒绝该字段。生成后的 soul 保存该值，帖子/评论角色已有 `Soul` 输入，直接读取而不让调度、风险、审批或 Edge 执行消息层层透传。

Cloud 的 UI snapshot 在绑定态同时投影 `personaWritingLanguage`，Edge 以当前环境状态回显；字段缺省表示 Cloud 尚未给出事实，显式 `null` 表示存量人设缺少语言。环境切换必须重新投影，不能复用上一环境的 DOM 选择。

### 3. 文本首次生成即使用目标语言，重写只保持、不转换

Facebook `ContentCreator` 使用平台化正文提示并显式声明账号写作语言；`CommentComposer` 和定向 `facebookCompose` 同样以账号语言为输出要求，即使目标帖是另一语言，也只把它用于理解语境。`CommentDeAiFlavor` 与发布去 AI 味提示要求保持输入语言，避免后续改写漂移。

备选方案是在审批后、提交前统一翻译，虽然减少部分提示改动，但会让审批文本与真实发布文本不一致，并容易产生生硬直译，故不采用。

### 4. 审核前使用轻量三态语言守卫，审核后逐字发布

Cloud 提供无外部依赖的 `checkWritingLanguage`：中文可依 Unicode 汉字判定；越南语以越南语特有变音字符作为强证据；英文排除汉字和越南语特有字符并要求足够拉丁字母。结果为 `match | mismatch | uncertain`。自动公开写入只接受 `match`；`mismatch` 或 `uncertain` 在产文阶段诚实失败/弃权，不把不确定性说成成功。

短文本存在天然不可判定性，宁可进入现有失败/人审分支也不假定正确。语言守卫只检查公开正文，不检查模型解释、标题占位或目标帖原文。

### 5. 存量缺字段可读取但不能继续自动生成 Facebook 公开文本

`writing_language` 在加载器中保持可选，使现有 soul 能继续解析和显示；Edge 对显式 `null` 显示“语言待补充”。新的 Facebook `persona.generate` 必须携带选择。运行时 Facebook 文本角色遇到缺字段返回具名失败或不产草稿，不从语调、昵称、历史文本推断。

小红书和视频号继续允许 soul 无此字段，行为逐位兼容。

## Risks / Trade-offs

- [越南语极短评论可能没有特有变音字符而判为 uncertain] → 维持 fail-closed；提示模型写自然且完整的越南语短句，并用测试覆盖典型输出。
- [旧 Edge 与新 Cloud 的 Facebook 人设更新不兼容] → 字段在协议类型上可选、Cloud 回具名 `writing_language_required`；Edge/Cloud 同批集成并部署 dev，不伪装成通用生成失败。
- [语言字段在环境切换时串号] → Cloud snapshot 按 accountId/edgeId 投影，Edge 状态按 envId 隔离；草稿仍锚定生成时 envId。
- [改写角色把正确语言改错] → 提示明确保持输入语言；重写后再跑守卫，不匹配时回退原文或失败。
- [Facebook 生成 prompt 与既有小红书模板耦合] → 只在 `platform=facebook` 时走窄分支；XHS prompt 和测试保持不变。

## Migration Plan

1. 同步落 Edge/Cloud 协议类型、Cloud soul 兼容解析与 snapshot 字段，先保证旧人设可读。
2. 落 Edge Facebook-only 选择器与 Cloud 生成/评论/发布消费者；新 Facebook 生成请求开始强制选择。
3. 用 dev 的代码级/影子评论验证三种语言 prompt、守卫与无真实写入边界；不以影子结果宣称平台发布成功。
4. 集成默认分支后从 eligible canonical checkout 部署 dev；先盘点存量 Facebook 人设缺语言数量，再由运营逐号显式更新。

回滚时可回滚消费者与 UI；已保存的 `writing_language` 是旧加载器会忽略的额外 YAML 字段，不需要破坏性数据回滚。

## Open Questions

- 无。三种语言、Facebook-only 展示、生成期生效、审核后不转换以及不开放灵感创作均已由用户确认。
