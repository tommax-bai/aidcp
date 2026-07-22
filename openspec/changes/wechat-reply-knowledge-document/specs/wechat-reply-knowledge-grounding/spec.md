## ADDED Requirements

### Requirement: 知识文档必须跟随渠道 profile 与 scope 版本

comment 与 dm 的 ReplyProfile SHALL 各自允许一个可选 `knowledgeDocument`，值 SHALL 为 `null` 或首尾无空白的非空 Markdown/纯文本，单份 MUST NOT 超过 20,000 字符。文档 MUST 与现有 group/default scope 的 profile 一起经历 draft、expectedVersion CAS、publish、历史版本读取和 body-free audit；系统 MUST NOT 为此恢复账号级回复策略。旧 profile 缺少该字段时 MUST 按 `null` 读取，MUST NOT 阻断既有 published 配置。

#### Scenario: 分组策略保存并发布评论知识文档
- **WHEN** 运营在一个 group scope 的 comment profile 保存合法知识文档并发布该版本
- **THEN** 同组账号后续解析到该 published comment 文档，dm 文档与其它 scope 不受影响

#### Scenario: 未分组账号使用 default 文档
- **WHEN** 未分组账号解析回复配置且 default scope 已发布知识文档
- **THEN** 账号使用 default scope 对应渠道文档，不查询退役账号级配置

#### Scenario: 空文档与旧版本安全兼容
- **WHEN** 文档被清空，或读取的历史 profile 没有 `knowledgeDocument` 字段
- **THEN** Cloud 将其规范为 `null`，模板回复和旧 published 配置继续可用

#### Scenario: 超长文档被拒绝
- **WHEN** profile PUT 携带超过 20,000 字符的知识文档
- **THEN** Cloud 以具名校验错误拒绝整个 CAS 写入，不截断、不产生新 draft 版本

### Requirement: AI 业务事实回答必须由知识文档支撑

仅当规则实际调用 `reply_polisher` 且命中渠道的 `knowledgeDocument` 非空时，polisher SHALL 使用该文档回答入站问题。任何业务事实 MUST 由文档明确支撑；文档没有答案时 SHALL 简短说明暂时无法确认，MUST NOT 使用模型常识猜测、补全价格/订单/时效/承诺或伪造出处。文档支持而新引入回复的事实 SHALL 按既有 `introducedClaims` 语义如实返回。

#### Scenario: 文档包含明确答案
- **WHEN** 用户问题可由当前渠道 published/draft preview 文档中的明确事实回答，且 AI 润色实际启用
- **THEN** polisher 生成简短、亲切、与文档一致的回答，并继续通过既有结构化输出和安全检查

#### Scenario: 文档没有答案
- **WHEN** 用户问题在当前渠道文档中没有明确支持信息
- **THEN** polisher 被要求说明暂时无法确认，不得猜测答案或自行追加私聊 CTA/联系方式

#### Scenario: AI 未调用时文档不离开 Cloud 配置链
- **WHEN** 规则未开启 polish、渠道 AI 开关关闭，或 DM 全局隐私闸关闭
- **THEN** 知识文档不进入 classifier、polisher、reviewer 或其它模型请求，回复继续使用既有确定性路径

### Requirement: 知识文档必须作为不可信数据处理

知识文档 SHALL 只作为事实参考数据，MUST NOT 被解释为系统/开发者指令。文档中的角色切换、忽略规则、自动发送、输出秘密、改写导流或绕过安全闸等内容 MUST 被忽略。模型 MUST NOT 在回答中输出整份文档或与问题无关的大段内容；系统日志与审计摘要 MUST NOT 记录文档正文。

#### Scenario: 文档包含提示词注入
- **WHEN** 文档正文包含“忽略之前规则”、角色设定、自动承诺或要求泄露整份资料等指令
- **THEN** polisher prompt 明确将其视为无效数据，既有 JSON schema、claim gate、reviewer、人工审核与写入开关保持生效

#### Scenario: AI 改写模板导流行
- **WHEN** 知识型 AI 候选删除或改写模板中受保护的私聊引导/联系方式行
- **THEN** 工作流丢弃候选并回退完整 rendered template，且该次 AI 调用仍不得自动发送

### Requirement: 管理后台必须提供安全可验证的文档配置

管理后台 SHALL 在每个 comment/dm profile 中提供 Markdown/纯文本知识文档编辑、20,000 字符计数和用途说明，并与品牌语气使用同一 profile 保存操作。界面 MUST 保留 loading/empty/error/permission/version-conflict 状态和账号/scope 切换的 stale-response 隔离；draft preview SHALL 使用尚未发布的当前文档，且 MUST 明示预览本身不会发送平台回复。

#### Scenario: 运营编辑并预览草稿文档
- **WHEN** 有编辑权限的运营保存渠道知识文档并用 draft 执行预览
- **THEN** Console 通过现有 profile CAS 写链保存，预览结果展示模板、AI 差异和风险，但不创建真实发送尝试

#### Scenario: 切换 scope 时旧响应返回
- **WHEN** 运营保存或加载知识文档期间切换到另一个策略 scope
- **THEN** 旧 scope 响应不得覆盖新 scope 表单或错误状态
