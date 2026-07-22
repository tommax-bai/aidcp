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

#### Scenario: 模型复制或轻改模板而没有回答
- **WHEN** classifier 将入站识别为问题/信息请求类 intent、当前渠道文档非空，且首次合格 polisher 文本与 rendered template 相同，或没有记录任何文档事实且没有明确说明无法确认
- **THEN** Cloud 不得把该文本记为成功知识回答，应在两次调用总预算内纠正一次，要求直接回答并记录文档事实，或明确无法确认

#### Scenario: 纠正后仍没有实际回答
- **WHEN** 第二次候选仍与 rendered template 相同
- **THEN** Cloud 回退模板并记录 `knowledge_answer_missing`，不得发起第三次调用或把模板原文标成 AI 已回答

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

### Requirement: AI 生成与润色必须遵守渠道最大字数

`reply_polisher` 的首次生成提示 MUST 包含当前渠道 profile 的具体 `maxLength`，并 SHALL 要求完整 `polishedText` 在 1 到该上限之间。计数 MUST 包含 AI 自然回答、模板私聊引导、联系方式及其它受保护行，MUST NOT 只限制 AI 新增片段。Cloud MUST 在接受候选前确定性校验长度，MUST NOT 通过字符串截断伪造合规结果。

#### Scenario: 首次生成即遵守最大字数
- **WHEN** 渠道 `maxLength` 为 30 且规则调用 `reply_polisher`
- **THEN** 首次 prompt 明确要求最终完整回复不超过 30 字符，模型返回的合格候选可直接进入既有 claim、reviewer 与人工审核流程

#### Scenario: 首次候选仅因超长而压缩重写
- **WHEN** 首次模型响应通过 JSON/schema 校验但完整 `polishedText` 超过 `maxLength`
- **THEN** Cloud 最多再调用一次同一 polisher，要求在保留知识事实、模板导流与联系方式边界的前提下压缩到具体上限内

#### Scenario: 第二次候选仍不满足限制
- **WHEN** 压缩候选仍为空、超长、结构无效或改写受保护行
- **THEN** Cloud 不进行第三次调用且不截断文本，回退完整 rendered template，并保持 fail-closed、人工审核和不得自动发送

#### Scenario: 模板自身超过最大字数
- **WHEN** rendered template 的受保护内容本身已超过 `maxLength`
- **THEN** 系统不得删除或截断模板行来伪装满足上限，应如实回退并保留可诊断的超限结果，供运营缩短模板或调整上限

#### Scenario: 超长与知识纠正共享重试预算
- **WHEN** 同一 polisher 首次候选同时需要长度或知识回答纠正
- **THEN** Cloud 最多只再调用一次模型，第二次任何不合格结果直接安全回退

### Requirement: 普通知识咨询必须使用明确风险口径

reviewer SHALL 将内容风险与客服措辞分开判断。课程适龄、学习范围、上课方式等普通教育咨询，在候选不含实质 hard-risk 类别、交易信息、个人数据、绝对承诺或未知含义时 SHALL 返回 low；模板中已有的中性私聊引导 MUST NOT 单独导致 unknown。`meaning_changed` 与 `introduced_claim` SHALL 作为强制人审的流程标签，MUST NOT 仅凭自身把内容风险抬成 high。unknown MUST 只用于事实或含义确实无法判断、输入缺失或 AI 调用失败。无论 reviewer 返回 low 与否，知识型 AI 回复 MUST 继续要求人工审核，MUST NOT 因本要求获得自动发送资格。

#### Scenario: 询问课程适龄范围
- **WHEN** 用户询问“适合几岁的孩子”，知识文档回答小学三至六年级，候选没有订单、价格、优惠、退款、医疗、法律、个人数据或绝对承诺
- **THEN** reviewer 与最终内容风险均为 low 且不附加 unknown；工作流可记录 meaning_changed/introduced_claim，但仍因 AI 实际运行而要求人工审核

#### Scenario: 私聊引导不等于未知风险
- **WHEN** 候选逐字保留模板提供的中性私聊引导且没有新增联系方式或敏感承诺
- **THEN** reviewer 不得仅因该引导返回 unknown 或 hard-risk tag

#### Scenario: 模型风险字段与安全理由自相矛盾
- **WHEN** 普通知识问答 intent，或 classifier JSON/schema fallback 但入站命中明确的适龄/年级询问句式，且 polisher/reviewer 调用成功、候选通过确定性门禁并记录文档事实，汇总标签除 unknown/meaning_changed/introduced_claim 外没有任何内容风险
- **THEN** Cloud SHALL 移除该 model-only unknown、不得再由 classifier fallback 单独把最终等级抬回 unknown，并把内容风险显示为 low，同时继续要求人工审核；polisher/reviewer fallback 或任一其它机械条件不满足时 MUST 保留 unknown

### Requirement: 预览必须解释 AI 候选结果

Cloud preview SHALL 返回向后兼容的 `fallbackUsed` 和具名 `fallbackReason`；Console SHALL 用简短中文展示模型异常、输出无效、超长、知识回答缺失或确定性候选拒绝。若 AI 成功运行且文本与模板相同，界面 SHALL 明示“AI 判断无需改写”，MUST NOT 暗示没有运行 AI。

#### Scenario: 知识回答缺失后回退
- **WHEN** 两次 polisher 候选都没有回答问题而最终使用 rendered template
- **THEN** 预览显示“AI 未回答问题，已回退模板”，而不是只展示相同的 before/after

#### Scenario: 候选被确定性门禁拒绝
- **WHEN** AI 候选命中长度、emoji、链接、禁词、声明或受保护行检查
- **THEN** 预览显示候选被安全规则拒绝，且不得展示已被丢弃的候选正文或知识文档正文

### Requirement: 管理后台必须提供安全可验证的文档配置

管理后台 SHALL 在每个 comment/dm profile 中提供 Markdown/纯文本知识文档编辑、20,000 字符计数和用途说明，并与品牌语气使用同一 profile 保存操作。界面 MUST 保留 loading/empty/error/permission/version-conflict 状态和账号/scope 切换的 stale-response 隔离；draft preview SHALL 使用尚未发布的当前文档，且 MUST 明示预览本身不会发送平台回复。

#### Scenario: 运营编辑并预览草稿文档
- **WHEN** 有编辑权限的运营保存渠道知识文档并用 draft 执行预览
- **THEN** Console 通过现有 profile CAS 写链保存，预览结果展示模板、AI 差异和风险，但不创建真实发送尝试

#### Scenario: 切换 scope 时旧响应返回
- **WHEN** 运营保存或加载知识文档期间切换到另一个策略 scope
- **THEN** 旧 scope 响应不得覆盖新 scope 表单或错误状态
